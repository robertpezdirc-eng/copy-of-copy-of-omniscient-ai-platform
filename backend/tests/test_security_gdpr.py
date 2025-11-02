import pytest

from backend.services.security.encryption import get_encryption_service
from backend.services.security.gdpr import get_gdpr_service


def test_encryption_roundtrip():
    svc = get_encryption_service()
    token = svc.encrypt("hello", associated_data=b"aad")
    out = svc.decrypt(token, associated_data=b"aad").decode("utf-8")
    assert out == "hello"


@pytest.mark.asyncio
async def test_gdpr_consent_export_erase_flow():
    gdpr = get_gdpr_service()
    uid = "user-123"
    await gdpr.record_consent(uid, {"marketing": True, "tos": "v2"})
    got = await gdpr.get_consent(uid)
    assert got["ok"] is True
    assert got["consent"]["marketing"]

    export = await gdpr.export_user_data(uid)
    assert export["user_id"] == uid
    assert "consent" in export

    erased = await gdpr.erase_user_data(uid)
    assert erased["user_id"] == uid
