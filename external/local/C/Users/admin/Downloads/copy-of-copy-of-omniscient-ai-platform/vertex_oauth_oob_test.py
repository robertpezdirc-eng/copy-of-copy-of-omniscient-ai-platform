#!/usr/bin/env python3
import subprocess, requests, json, os, sys

def log(msg):
    print(msg, flush=True)

def get_access_token():
    try:
        r = subprocess.run([
            "gcloud","auth","application-default","print-access-token"
        ], capture_output=True, text=True, timeout=20)
        if r.returncode != 0:
            return None, f"gcloud returned {r.returncode}: {r.stderr.strip()[:200]}"
        token = r.stdout.strip()
        return token, None
    except Exception as e:
        return None, str(e)

def vertex_oauth_test(project="refined-graph-471712-n9", region="us-central1", model="gemini-2.0-pro"):
    token, err = get_access_token()
    if not token:
        return {"ok": False, "error": f"No access token: {err}"}
    url = f"https://{region}-aiplatform.googleapis.com/v1/projects/{project}/locations/{region}/publishers/google/models/{model}:generateContent"
    payload = {
        "contents": [{
            "role": "user",
            "parts": [{"text": "Pozdravljen, Gemini! To je neinteraktivni OAuth test iz Vertex AI."}]
        }],
        "generation_config": {
            "max_output_tokens": 128,
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40
        }
    }
    try:
        r = requests.post(url, headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }, json=payload, timeout=15)
        out_path = os.path.join(os.getcwd(), "vertex_oauth_vertex.json")
        with open(out_path, "wb") as f:
            f.write(r.content)
        if r.status_code == 200:
            data = r.json()
            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text")
            snippet = (text or "")[:160]
            return {"ok": True, "status": 200, "snippet": snippet, "path": out_path}
        else:
            return {"ok": False, "status": r.status_code, "path": out_path, "error": r.text[:300]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

if __name__ == "__main__":
    res = vertex_oauth_test()
    log(json.dumps(res, ensure_ascii=False))