import os
from google.oauth2 import service_account
from vertexai import init as vertex_init
from vertexai.preview.generative_models import GenerativeModel

KEY_PATH = r"C:\Users\admin\Downloads\copy-of-copy-of-omniscient-ai-platform\service_account.omni-deployer.json"
PROJECT = "refined-graph-471712-n9"
REGION = "us-central1"
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

print("Using SA key:", KEY_PATH)
creds = service_account.Credentials.from_service_account_file(KEY_PATH)
vertex_init(project=PROJECT, location=REGION, credentials=creds)
model = GenerativeModel(MODEL)
print("Initialized Vertex AI for:", PROJECT, REGION, "model:", MODEL)
try:
    resp = model.generate_content("Test respond in one sentence.")
    print("RESULT_TEXT:", getattr(resp, "text", None))
except Exception as e:
    print("GEN_ERROR:", e)