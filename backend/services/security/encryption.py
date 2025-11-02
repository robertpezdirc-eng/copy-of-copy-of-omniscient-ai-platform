from __future__ import annotations

import base64
import os
import secrets
from dataclasses import dataclass
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore

try:  # Optional dependency; available in requirements, but handle gracefully
    from google.cloud import secretmanager  # type: ignore
except Exception:  # pragma: no cover - optional
    secretmanager = None  # type: ignore


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    pad = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


@dataclass
class EncryptionConfig:
    master_key: bytes


class EncryptionService:
    """AES-GCM encryption with a static 256-bit key.

    In production, use a KMS for envelope encryption. Here we use a single
    application-level key for simplicity. Nonce is 96-bit random per message.
    """

    def __init__(self, config: EncryptionConfig) -> None:
        if len(config.master_key) not in (16, 24, 32):
            raise ValueError("master_key must be 128/192/256 bits")
        self._key = config.master_key

    def encrypt(self, plaintext: bytes | str, associated_data: Optional[bytes] = None) -> str:
        if isinstance(plaintext, str):
            plaintext = plaintext.encode("utf-8")
        nonce = secrets.token_bytes(12)  # 96-bit nonce
        aead = AESGCM(self._key)
        ct = aead.encrypt(nonce, plaintext, associated_data)
        return _b64url_encode(nonce + ct)

    def decrypt(self, token: str, associated_data: Optional[bytes] = None) -> bytes:
        raw = _b64url_decode(token)
        nonce, ct = raw[:12], raw[12:]
        aead = AESGCM(self._key)
        return aead.decrypt(nonce, ct, associated_data)


_encryption_singleton: Optional[EncryptionService] = None


def _load_master_key_from_env() -> Optional[bytes]:
    b64 = os.getenv("OMNI_ENCRYPTION_KEY")
    if not b64:
        return None
    try:
        key = _b64url_decode(b64)
        return key
    except Exception:
        return None


def _load_master_key_from_gcp() -> Optional[bytes]:  # pragma: no cover - env specific
    secret_name = os.getenv("GCP_SECRET_ENCRYPTION_KEY")  # e.g., projects/..../secrets/OMNI_KEY/versions/latest
    if not secret_name or not secretmanager:
        return None
    try:
        client = secretmanager.SecretManagerServiceClient()
        resp = client.access_secret_version(name=secret_name)
        key_b64 = resp.payload.data.decode("utf-8").strip()
        return _b64url_decode(key_b64)
    except Exception:
        return None


def get_encryption_service() -> EncryptionService:
    global _encryption_singleton
    if _encryption_singleton:
        return _encryption_singleton

    key = _load_master_key_from_env() or _load_master_key_from_gcp()
    if not key:
        # Fallback to ephemeral key (use only for local/dev).
        key = AESGCM.generate_key(bit_length=256)

    _encryption_singleton = EncryptionService(EncryptionConfig(master_key=key))
    return _encryption_singleton
