import requests
import time

BASE = "http://127.0.0.1:8082"
STREAM = f"{BASE}/api/gcp/gemini/stream"


def read_sse(url: str, timeout: int = 30, max_lines: int = 1000):
    lines = []
    with requests.get(url, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        for raw in r.iter_lines(decode_unicode=True):
            if raw is None:
                continue
            line = raw.strip()
            if not line:
                continue
            lines.append(line)
            # stop early if we see done
            if line.startswith("event: done"):
                break
            if len(lines) >= max_lines:
                break
    return lines


def metrics_snapshot():
    try:
        h = requests.get(f"{BASE}/healthz", timeout=5)
        h.raise_for_status()
        return h.json().get("sse_metrics", {})
    except Exception as e:
        print(f"[WARN] healthz fetch failed: {e}")
        return {}


def simulate_success(n: int = 3):
    print(f"[SIM] Success streams x{n}")
    for i in range(n):
        url = f"{STREAM}?source=sim&prompt=Success%20stream%20{i}&chunk_size=24&delay_ms=10"
        lines = read_sse(url, timeout=20, max_lines=500)
        print(f"  • run {i+1}: events={sum(1 for l in lines if l.startswith('event:'))} done={any(l.startswith('event: done') for l in lines)}")
        time.sleep(0.5)


def simulate_fallback_error(n: int = 2):
    print(f"[SIM] Fallback/error streams x{n}")
    for i in range(n):
        # Use a non-existent model to trigger fallback+error handling
        url = f"{STREAM}?prompt=Error%20probe%20{i}&model=gemini-nonexistent-model-xyz&chunk_size=32&delay_ms=1"
        lines = read_sse(url, timeout=25, max_lines=800)
        fallback = any(l.startswith('event: fallback') for l in lines)
        done = any(l.startswith('event: done') for l in lines)
        print(f"  • run {i+1}: fallback={fallback} done={done}")
        time.sleep(0.5)


if __name__ == "__main__":
    m1 = metrics_snapshot()
    print("[BEFORE]", m1)
    simulate_success(3)
    simulate_fallback_error(2)
    m2 = metrics_snapshot()
    print("[AFTER]", m2)
    print("[DELTA]", {k: m2.get(k.split('_', 2)[-1], 0) - m1.get(k.split('_', 2)[-1], 0) for k in ['sse_streams_started','sse_streams_done','sse_streams_fallback','sse_streams_errors']})