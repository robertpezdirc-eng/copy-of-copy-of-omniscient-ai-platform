import json
import os
import time
from datetime import datetime, timedelta, timezone

# Optional imports; guarded so container can run without them when not configured
try:
    import psycopg2  # type: ignore
except Exception:
    psycopg2 = None

try:
    import stripe  # type: ignore
except Exception:
    stripe = None

import requests

OUTPUT_PATH = os.environ.get("KPI_OUTPUT_PATH", \
    os.path.join(os.path.dirname(__file__), "..", "backend", "data", "business_kpis.json"))


def log(msg: str):
    print(f"[kpi_ingest] {datetime.now(timezone.utc).isoformat()} - {msg}")


def ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def fetch_db_metrics():
    dsn = os.environ.get("DB_DSN")
    if not dsn or psycopg2 is None:
        return {"revenue_db": 0.0, "active_users_db": 0}
    revenue_24h = 0.0
    active_users_24h = 0
    try:
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()
        # Example queries; adapt to your schema
        cur.execute("SELECT COALESCE(SUM(amount),0) FROM revenue WHERE ts > NOW() - INTERVAL '24 hours';")
        row = cur.fetchone()
        revenue_24h = float(row[0] or 0.0)
        cur.execute("SELECT COUNT(*) FROM users WHERE last_active > NOW() - INTERVAL '24 hours';")
        row = cur.fetchone()
        active_users_24h = int(row[0] or 0)
    except Exception as e:
        log(f"DB fetch error: {e}")
    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass
    return {"revenue_db": revenue_24h, "active_users_db": active_users_24h}


def fetch_stripe_metrics():
    api_key = os.environ.get("STRIPE_API_KEY")
    if not api_key or stripe is None:
        return {"revenue_stripe": 0.0}
    stripe.api_key = api_key
    revenue_24h = 0.0
    try:
        # Sum captured charges in the last 24h
        since = int((datetime.now(timezone.utc) - timedelta(hours=24)).timestamp())
        charges = stripe.Charge.list(created={"gte": since}, limit=100)
        for ch in charges.auto_paging_iter():
            if ch.get("paid") and not ch.get("refunded"):
                revenue_24h += (ch.get("amount", 0) or 0) / 100.0  # amount in cents
    except Exception as e:
        log(f"Stripe fetch error: {e}")
    return {"revenue_stripe": revenue_24h}


def fetch_analytics_metrics():
    endpoint = os.environ.get("ANALYTICS_ENDPOINT")
    token = os.environ.get("ANALYTICS_TOKEN")
    if not endpoint:
        return {"conversion_rate": None}
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = requests.get(endpoint, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        # Expect JSON like { "conversion_rate": 0.034 } or nested structure
        cr = data.get("conversion_rate")
        if cr is None and "metrics" in data:
            cr = data["metrics"].get("conversion_rate")
        return {"conversion_rate": cr}
    except Exception as e:
        log(f"Analytics fetch error: {e}")
        return {"conversion_rate": None}


def write_kpis(kpis: dict):
    ensure_dir(OUTPUT_PATH)
    try:
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(kpis, f, indent=2)
        log(f"Wrote KPIs to {OUTPUT_PATH}")
    except Exception as e:
        log(f"Write error: {e}")


def compute_and_store():
    db = fetch_db_metrics()
    stripe_m = fetch_stripe_metrics()
    analytics = fetch_analytics_metrics()

    revenue_total_24h = float(db.get("revenue_db", 0.0)) + float(stripe_m.get("revenue_stripe", 0.0))
    active_users_24h = int(db.get("active_users_db", 0))
    conversion_rate = analytics.get("conversion_rate")

    kpis = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "revenue": revenue_total_24h,
        "active_users": active_users_24h,
        "conversion_rate": conversion_rate if conversion_rate is not None else 0.0,
        "sources": {
            "db": db,
            "stripe": stripe_m,
            "analytics": analytics,
        },
    }
    write_kpis(kpis)


if __name__ == "__main__":
    # One-shot execution; compose command will loop hourly
    compute_and_store()