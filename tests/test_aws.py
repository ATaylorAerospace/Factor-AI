"""Tests for AWS integration helpers (Cognito, S3, Observability)."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from factor.aws.cognito import CognitoAuth
from factor.aws.observability import trace_agent_call
from factor.aws.s3 import S3Storage
from factor.config import settings


def test_cognito_rejects_empty_token():
    auth = CognitoAuth(user_pool_id="")
    assert auth.verify_token("") is None
    assert auth.verify_token("   ") is None


def test_cognito_fails_closed_in_production_when_unconfigured(monkeypatch):
    monkeypatch.setattr(settings, "factor_env", "production")
    auth = CognitoAuth(user_pool_id="")
    assert auth.verify_token("valid-looking-token") is None


def test_cognito_allows_dev_fallback_in_development(monkeypatch):
    monkeypatch.setattr(settings, "factor_env", "development")
    auth = CognitoAuth(user_pool_id="")
    user = auth.verify_token("dev-token")
    assert user is not None
    assert user["sub"] == "dev-user"


def test_s3_list_session_documents_paginates():
    storage = S3Storage(bucket="test-bucket")
    mock_client = MagicMock()
    now = datetime.now(timezone.utc)
    mock_client.list_objects_v2.side_effect = [
        {
            "Contents": [
                {"Key": "sessions/s1/documents/a.pdf", "Size": 10, "LastModified": now}
            ],
            "IsTruncated": True,
            "NextContinuationToken": "tok-2",
        },
        {
            "Contents": [
                {"Key": "sessions/s1/documents/b.pdf", "Size": 20, "LastModified": now}
            ],
            "IsTruncated": False,
        },
    ]
    storage._client = mock_client

    docs = storage.list_session_documents("s1")
    assert [d["filename"] for d in docs] == ["a.pdf", "b.pdf"]
    assert mock_client.list_objects_v2.call_count == 2


def test_s3_delete_session_documents_batches_over_1000_keys():
    storage = S3Storage(bucket="test-bucket")
    mock_client = MagicMock()
    storage._client = mock_client
    storage.list_session_documents = MagicMock(  # type: ignore[method-assign]
        return_value=[
            {"key": f"sessions/s1/documents/doc_{i}.pdf"} for i in range(1250)
        ]
    )

    deleted = storage.delete_session_documents("s1")
    assert deleted == 1250
    assert mock_client.delete_objects.call_count == 2
    first_batch = mock_client.delete_objects.call_args_list[0].kwargs["Delete"]["Objects"]
    second_batch = mock_client.delete_objects.call_args_list[1].kwargs["Delete"]["Objects"]
    assert len(first_batch) == 1000
    assert len(second_batch) == 250


def test_s3_upload_and_download_reject_invalid_filenames(tmp_path):
    storage = S3Storage(bucket="test-bucket")
    storage._client = MagicMock()
    dummy = tmp_path / "file.txt"
    dummy.write_text("hello", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid document filename"):
        storage.upload_document(str(dummy), "s1", filename="..")

    with pytest.raises(ValueError, match="Invalid local download path"):
        storage.download_document("sessions/s1/documents/file.txt", "..")


def test_trace_agent_call_preserves_function_metadata():
    @trace_agent_call("coordinator", "analyze")
    def sample_func(x: int) -> int:
        """Sample docstring."""
        return x + 1

    assert sample_func.__name__ == "sample_func"
    assert sample_func.__doc__ == "Sample docstring."
