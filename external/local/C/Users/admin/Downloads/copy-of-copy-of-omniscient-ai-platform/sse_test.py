import requests, sys, time

url = 'http://localhost:8082/api/gcp/gemini/stream?prompt=hello%20world%20smoke%20test'
headers = {'Accept': 'text/event-stream'}

r = requests.get(url, stream=True, timeout=60, headers=headers)
start = time.time()
seen_metrics = False
seen_done = False
seen_duration = False
seen_chunks = False

for i, line in enumerate(r.iter_lines()):
    if not line:
        continue
    s = line.decode('utf-8', errors='ignore')
    print(s)
    sys.stdout.flush()
    if s.startswith(': X-Stream-Duration'):
        seen_duration = True
    if s.startswith(': X-Stream-Chunks'):
        seen_chunks = True
    if s.startswith('event: metrics'):
        seen_metrics = True
    if s.startswith('event: done'):
        seen_done = True
        break
    if i > 400 or time.time() - start > 50:
        break

print('\nSUMMARY: metrics=%s, done=%s, duration_comment=%s, chunks_comment=%s' % (
    seen_metrics, seen_done, seen_duration, seen_chunks
))