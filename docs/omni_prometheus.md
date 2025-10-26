# OMNI Unified Platform Prometheus Metrics

This platform exposes a Prometheus-compatible endpoint at `/metrics` with SSE streaming counters.

## Exposed metrics

- omni_sse_streams_started (counter)
- omni_sse_streams_done (counter)
- omni_sse_streams_fallback (counter)
- omni_sse_streams_errors (counter)

Each metric includes `# HELP` and `# TYPE` headers per Prometheus exposition format.

## Quick check

- PowerShell:
  - `Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8082/metrics | Select-Object -ExpandProperty Content`
- Linux/macOS:
  - `curl -s http://127.0.0.1:8082/metrics`

Note: If your local firewall restricts binding to `0.0.0.0`, use `127.0.0.1` on an allowed port (e.g., 8091).

## Prometheus scrape example

prometheus.yml:

```
scrape_configs:
  - job_name: 'omni_sse'
    metrics_path: '/metrics'
    scheme: 'http'
    static_configs:
      - targets: ['127.0.0.1:8082']
```

Replace the target and port according to your deployment environment (Docker, Cloud Run, VM, etc.).

## Grafana dashboard tips

- Counters (instant):
  - `omni_sse_streams_started`
  - `omni_sse_streams_done`
  - `omni_sse_streams_fallback`
  - `omni_sse_streams_errors`
- Rates (per minute or per second):
  - `rate(omni_sse_streams_started[5m])`
  - `rate(omni_sse_streams_errors[5m])`
- Health snapshot alignment:
  - `/healthz` returns a JSON `sse_metrics` snapshot; values should match the current counters exposed by `/metrics`.

## Production notes

- Ensure the app is reachable from Prometheus (network/port/firewall).
- When running behind a reverse proxy (nginx), forward `/metrics` without modification.
- Configure alerts on `omni_sse_streams_errors` spikes and `omni_sse_streams_fallback` sustained increases.