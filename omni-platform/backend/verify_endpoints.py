import json
import urllib.request
import urllib.error

BASE = "http://localhost:8004/api/v1"
API_KEY = "d405a71f7bee4f358497640f31deac0e"
TENANT = "finops-demo"
HEADERS = {
    "x-api-key": API_KEY,
    "tenant_id": TENANT,
    "Content-Type": "application/json",
}


def request(method: str, path: str, data: dict | None = None):
    url = f"{BASE}{path}"
    body = None
    headers = dict(HEADERS)
    if data is not None:
        body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req) as resp:
            txt = resp.read().decode("utf-8")
            try:
                return json.loads(txt)
            except json.JSONDecodeError:
                return {"raw": txt}
    except urllib.error.HTTPError as e:
        return {"error": True, "status": e.code, "body": e.read().decode("utf-8")}
    except Exception as e:
        return {"error": True, "exception": str(e)}


def main():
    print("Checking revenue status...")
    print(request("GET", "/policy/revenue/status"))

    print("Enabling revenue policy...")
    enable_body = {
        "tenant_id": TENANT,
        "feature_name": "auto-generated-api",
        "rollout": 100,
        "notes": "initial enable via script",
    }
    print(request("POST", "/policy/revenue/enable", enable_body))

    print("Listing billing catalog before add...")
    print(request("GET", "/billing/catalog"))

    print("Adding billing catalog item...")
    item = {
        "name": "Starter API Plan",
        "sku": "api-starter",
        "price": 19.99,
        "currency": "USD",
        "features": ["100k requests", "basic support"],
    }
    print(request("POST", "/billing/catalog/add", item))

    print("Listing billing catalog after add...")
    print(request("GET", "/billing/catalog"))


if __name__ == "__main__":
    main()