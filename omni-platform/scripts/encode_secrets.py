import base64
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
# Load OpenAI key from file
openai_key_file = root / 'openai key.txt'
openai_key = openai_key_file.read_text(encoding='utf-8').strip() if openai_key_file.exists() else ''

# Fixed/known values from repo
jwt_secret = "77fdc36c8e21b8fa50f2ad7c9be0173e89ca274bfbc8543f6d3260a1fa3c56e2"
jwt_refresh_secret = "30b1e2f3c4d5a6b7c8d9e0f1a23b45c67d8901e2f3c4a5b6d7e8f9a0b1c2d3e4"
redis_pass = "omni_redis_secure_pass"
mongo_user = "omni_root"
mongo_pass = "omni_root_pass_2024"
google_api_key = "AIzaSyAyKCIUE1b8SQF9g-Ok2WDB_zvtkCkYC8M"
ibm_api_key = "not_set"
# Use Google key for Gemini if separate not provided
gemini_key = google_api_key

values = {
  'MONGO_USER': mongo_user,
  'MONGO_PASS': mongo_pass,
  'REDIS_PASS': redis_pass,
  'JWT_SECRET': jwt_secret,
  'JWT_REFRESH_SECRET': jwt_refresh_secret,
  'OPENAI_API_KEY': openai_key,
  'IBM_API_KEY': ibm_api_key,
  'GEMINI_KEY': gemini_key,
  'GOOGLE_API_KEY': google_api_key,
}

encoded = {k: base64.b64encode(v.encode('utf-8')).decode('ascii') for k, v in values.items()}

out_path = root / 'encoded_secrets.json'
out_path.write_text(json.dumps(encoded, indent=2), encoding='utf-8')
print(f"Wrote base64 secrets to {out_path}")