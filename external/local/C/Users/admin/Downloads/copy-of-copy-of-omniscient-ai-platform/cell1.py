# === V ta niz prilepite CELOTEN JSON ključ ===
KEY_JSON = r"""
{
  "type": "service_account",
  "project_id": "refined-graph-471712-n9",
  "private_key_id": "00039a357d32497fd3696b5fe2a3bab407a91709",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCw6WkHsuYw8QQw\nUxX7ZRmAbetsV90i8fOya3+vdmCLY5QqRPnMy7y20FywjvZDm1j3S9lUxgmuQVzX\nKNsvgKcvy7BjwkmOBNzPidkvDXPwls6OfybGp+5etplEeP1ONtq6Ir0vlVhmph7G\n4m53I1zpuYGB10YfqTxTYXvNpnXccI+xAGQNcGSrEIF45oPUpDsgBPBtp9HzKPxA\neYMbpln0XMPv3q0aB6nSSrfx/uMGAt3tOD6L77sc/ThvvM3JB+LmVXQAgm/FxsrS\nyEK3bjlD//ZqecwVyFUhfSJP2/uyz9RihQrtNyQLEDbx1GlvJfE53X3GuNyB5BjU\nAjYJuv1NAgMBAAECggEAD3xjDAA6O6sBT5yaRj8HkDEvBDUdv58X0rSrwOd3FISD\nNf8DMczcyFDtaCwffPQGgeEzFUNfmhARKSljpGEZ4WpuVpEtgJ/G12js6Lw/+52r\n15fkREvzZvmLaY3AuJ2/ID+FuXpUemnMtGKiQk4HZlMtdbjrI77b772PCYWqeAEC\nDTLNWUslLMniZbJBopBLo1+tHC4OSVB0PugZW0W4hwYRr0kMu3hD+LGCTqkZYDip\nygrWxW4lZxhQf3guyAHG98+WuIwlVZt9qbQtDbrZqnnfNnWu1AyW39ABGpFLmhMl\nHdVUan7fAWpMyJCD7FqWp3Vy/cTbRBKa3P82r/L4kQKBgQDkaPyaWp0wB6s2lYjS\n00TdHahQs9MKRk4657JqijDPYtxOfWxb+ACkjufUQEdLNn1WGSPT2eXt4492NxvS\njSPjZDx/RfGuMwj3xk6a/DW5WnKQgPlogT9H4QqSQXsVkGcl1iG4vkyFOkNtzz4n\n1JdgEknIWhSJwKCX8Aa1LRVfvQKBgQDGR/ct6O69icood8TwGfPeaKwDAsYWvp2S\ngiP1iFGdxLFp7ePUc3TJ2PJHgCpuxnMtogzFoNmxUr5V2VMzYrBm6/ShUcJq2zsS\n0diBH8Z6NUdOiU6HzhUZJgkBzQ16F8ywJ+VVsa/n0d5TT1q3ax7Wf8L9myXBWVPi\nMJxMvopk0QKBgQDVsvRDZewS99nUY+tzdH7Fce38M4KL5mNi8UwYKdqo7ZG5TdeH\n5GyVia6VAt6xG/YAC91dZEyfWXzr2XuKbsrZAPspCMOpe840I7F/h+Cr3le5ozG1\n+Na/5WkClYkXD9exqro6IrFtJKnZn0BD+770/6dQcBcvGq4l+UgNUnTg8QKBgFTy\nTe5IRcfD+Wze6utmYvkc5NyhWpYx8bXrtVYiobyyoMNeHGZPVHCJVjrVqNgugvfA\n3jHo2HrElTCYW7G/DQ369qIKMf2vkJ5ecp/XKiP/IV5/Krq5yoYsql0wKR7uhU3O\nucy9xDvPyKzuaVH9PYft0m7uAf3UtEBKTRv/4bCRAoGBANSsoRIgddTg4Anl+FTk\nikJdbM5XSraEX32lgn/49Sp2HTorxmbkaPkoSZXnmnk2preLyoVS/JEEM6jb3+4F\n3PQGn0nuicvUQ6T5gayMuyckqBuIFd7C9L806NLLAAxYC2airHcLd5Omeie6Dg/C\n/yS1Qv+X7aATF+On9PDXwxdv\n-----END PRIVATE KEY-----\n",
  "client_email": "omni-runner@refined-graph-471712-n9.iam.gserviceaccount.com",
  "client_id": "111224118950203567247",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/omni-runner%40refined-graph-471712-n9.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
"""

import os, json, tempfile, subprocess, shlex, sys

def run(cmd):
    print("> ", cmd)
    p = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
    if p.stdout.strip(): print(p.stdout)
    if p.stderr.strip(): print(p.stderr)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed ({p.returncode}): {cmd}\n{p.stderr}")
    return p.stdout.strip()

# Zapiši ključ v začasno datoteko in aktiviraj SA
try:
    key = json.loads(KEY_JSON)
except Exception as e:
    print("JSON ključ ni veljaven:", e); sys.exit(1)

key_path = os.path.join(tempfile.gettempdir(), "service-account.json")
with open(key_path, "w", encoding="utf-8") as f:
    f.write(KEY_JSON.strip())
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
print("GOOGLE_APPLICATION_CREDENTIALS =", key_path)

project_id = key.get("project_id")
sa_email = key.get("client_email")
if not project_id or not sa_email:
    print("Manjka project_id ali client_email v JSON ključu"); sys.exit(1)

run(f"gcloud auth activate-service-account --key-file={key_path}")
run(f"gcloud config set project {project_id}")

# Poskusi omogočiti API-je (zahteva serviceusage.serviceUsageAdmin ali owner)
try:
    run("gcloud services enable cloudbuild.googleapis.com run.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com")
    print("✅ API-ji uspešno omogočeni.")
except Exception as e:
    print("⚠️ API-jev ni bilo mogoče omogočiti (manjkajo pravice). Dodeli vloge in ponovno zaženi to celico.")