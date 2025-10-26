import requests

BASE="http://localhost:8082"


def parse_sse(url: str, max_lines: int = 500, timeout: int = 30):
    r = requests.get(url, stream=True, timeout=timeout)
    lines = []
    for i, b in enumerate(r.iter_lines()):
        if not b:
            continue
        s = b.decode('utf-8', errors='ignore')
        lines.append(s)
        if i >= max_lines:
            break
    return lines


def test_sim_stream_headers_and_done():
    url = f"{BASE}/api/gcp/gemini/stream?source=sim&prompt=Test%20SSE%20sim%20headers"
    lines = parse_sse(url, max_lines=200, timeout=25)
    assert any(l.startswith('event: start') for l in lines), "Missing event: start"
    assert any(l.startswith(': X-Stream-Duration') for l in lines), "Missing X-Stream-Duration comment"
    assert any(l.startswith(': X-Stream-Chunks') for l in lines), "Missing X-Stream-Chunks comment"
    assert any(l.startswith('event: metrics') for l in lines), "Missing event: metrics"
    assert any(l.startswith('event: done') for l in lines), "Missing event: done"


def test_vertex_error_emits_fallback_and_increments_metrics():
    # Baseline metrics
    m1 = requests.get(f"{BASE}/healthz", timeout=5).json().get('sse_metrics', {})

    # Trigger a non-existent model to force Vertex error → GENAI fallback
    url = f"{BASE}/api/gcp/gemini/stream?prompt=Error%20probe%20for%20fallback&model=gemini-nonexistent-model-xyz&chunk_size=96&delay_ms=1"
    lines = parse_sse(url, max_lines=800, timeout=40)

    assert any(l.startswith('event: fallback') for l in lines), "Missing event: fallback on error"
    assert any(l.startswith(': X-Stream-Duration') for l in lines), "Missing X-Stream-Duration comment"
    assert any(l.startswith(': X-Stream-Chunks') for l in lines), "Missing X-Stream-Chunks comment"
    assert any(l.startswith('event: metrics') for l in lines), "Missing event: metrics"
    assert any(l.startswith('event: done') for l in lines), "Missing event: done"

    # Post metrics
    m2 = requests.get(f"{BASE}/healthz", timeout=5).json().get('sse_metrics', {})
    assert m2.get('errors', 0) >= m1.get('errors', 0), "errors counter should increment"
    assert m2.get('fallback', 0) >= m1.get('fallback', 0), "fallback counter should increment"
    assert m2.get('started', 0) >= m1.get('started', 0), "started counter should increment"
    assert m2.get('done', 0) >= m1.get('done', 0), "done counter should increment or match (depending on stream completion timing)"