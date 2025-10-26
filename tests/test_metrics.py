from fastapi.testclient import TestClient
from omni_unified_platform import app


client = TestClient(app)


def parse_metrics(text: str):
    values = {}
    for line in text.splitlines():
        if line.startswith("omni_sse_streams_"):
            parts = line.split()
            if len(parts) == 2:
                # Prometheus values are numbers; cast safely
                try:
                    values[parts[0]] = int(float(parts[1]))
                except ValueError:
                    pass
    return values


def test_metrics_endpoint_plaintext_contains_counters():
    resp = client.get("/metrics")
    assert resp.status_code == 200
    # content-type may include charset, check substring
    assert "text/plain" in resp.headers.get("content-type", "")

    body = resp.text
    # Verify HELP/TYPE and metric names are present
    assert "# HELP omni_sse_streams_started" in body
    assert "# TYPE omni_sse_streams_started counter" in body
    assert "omni_sse_streams_started" in body

    assert "# HELP omni_sse_streams_done" in body
    assert "# TYPE omni_sse_streams_done counter" in body
    assert "omni_sse_streams_done" in body

    assert "# HELP omni_sse_streams_fallback" in body
    assert "# TYPE omni_sse_streams_fallback counter" in body
    assert "omni_sse_streams_fallback" in body

    assert "# HELP omni_sse_streams_errors" in body
    assert "# TYPE omni_sse_streams_errors counter" in body
    assert "omni_sse_streams_errors" in body


def test_metrics_matches_healthz_snapshot():
    health = client.get("/healthz")
    assert health.status_code == 200
    sse = health.json().get("sse_metrics", {})

    metrics_resp = client.get("/metrics")
    assert metrics_resp.status_code == 200
    values = parse_metrics(metrics_resp.text)

    assert values.get("omni_sse_streams_started") == sse.get("started")
    assert values.get("omni_sse_streams_done") == sse.get("done")
    assert values.get("omni_sse_streams_fallback") == sse.get("fallback")
    assert values.get("omni_sse_streams_errors") == sse.get("errors")