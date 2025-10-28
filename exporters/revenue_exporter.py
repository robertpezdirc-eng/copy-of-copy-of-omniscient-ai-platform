import os
import json
import time
from threading import Thread
from datetime import datetime
from flask import Flask, Response
from prometheus_client import CollectorRegistry, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)
registry = CollectorRegistry()

# KPI metrics
revenue_eur = Gauge('omni_revenue_eur', 'Total revenue in EUR', registry=registry)
active_users = Gauge('omni_active_users', 'Active users count', registry=registry)
conversion_rate = Gauge('omni_conversion_rate', 'Conversion rate (0..1)', registry=registry)

# Config
KPI_FILE = os.environ.get('KPI_FILE', '/data/business_kpis.json')
POLL_SECONDS = float(os.environ.get('POLL_SECONDS', '10'))
INITIAL_REVENUE = float(os.environ.get('INITIAL_REVENUE_EUR', '0'))
INITIAL_USERS = float(os.environ.get('INITIAL_ACTIVE_USERS', '0'))
INITIAL_CONVERSION = float(os.environ.get('INITIAL_CONVERSION_RATE', '0.0'))

# Initialize
revenue_eur.set(INITIAL_REVENUE)
active_users.set(INITIAL_USERS)
conversion_rate.set(INITIAL_CONVERSION)


def log(msg: str):
    print(f"[{datetime.utcnow().isoformat(timespec='seconds')}Z] {msg}")


def update_from_file():
    while True:
        try:
            if os.path.exists(KPI_FILE):
                with open(KPI_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if 'revenue_eur' in data:
                    revenue_eur.set(float(data['revenue_eur']))
                if 'active_users' in data:
                    active_users.set(float(data['active_users']))
                if 'conversion_rate' in data:
                    conversion_rate.set(float(data['conversion_rate']))
                log(f"KPI updated from file: revenue={data.get('revenue_eur')} users={data.get('active_users')} conv={data.get('conversion_rate')}")
            else:
                log(f"KPI file not found: {KPI_FILE}; using initial values")
        except Exception as e:
            log(f"Error updating KPI: {e}")
        time.sleep(POLL_SECONDS)


@app.route('/metrics')
def metrics():
    return Response(generate_latest(registry), mimetype=CONTENT_TYPE_LATEST)


def start_worker():
    t = Thread(target=update_from_file, daemon=True)
    t.start()


if __name__ == '__main__':
    start_worker()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', '9101')))