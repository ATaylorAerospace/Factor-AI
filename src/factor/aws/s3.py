"""Amazon S3 integration for document storage."""

from __future__ import annotations

import logging
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from factor.config import settings

logger = logging.getLogger(__name__)


class S3Storage:
    """S3 client for storing and retrieving legal documents."""

    def __init__(self, bucket: str | None = None, region_name: str | None = None):
        self.bucket = bucket or settings.factor_s3_bucket
        self.region_name = region_name or settings.aws_region
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client("s3", region_name=self.region_name)
        return self._client

    def upload_document(
        self,
        file_path: str,
        session_id: str,
        filename: str | None = None,
    ) -> str:
        """Upload a document to S3 with session-scoped key.

        Args:
            file_path: Local path to the document.
            session_id: Session ID for scoping.
            filename: Optional override for the filename.

        Returns:
            S3 key of the uploaded document.
        """
        path = Path(file_path)
        name = filename or path.name
        key = f"sessions/{session_id}/documents/{name}"

        self.client.upload_file(str(path), self.bucket, key)
        logger.info("Uploaded %s to s3://%s/%s", name, self.bucket, key)
        return key

    def download_document(self, key: str, local_path: str) -> str:
        """Download a document from S3.

        Args:
            key: S3 object key.
            local_path: Local path to save the file.

        Returns:
            Local path of the downloaded file.
        """
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        self.client.download_file(self.bucket, key, local_path)
        logger.info("Downloaded s3://%s/%s to %s", self.bucket, key, local_path)
        return local_path

    def list_session_documents(self, session_id: str) -> list[dict]:
        """List all documents for a session.

        Args:
            session_id: Session ID to list documents for.

        Returns:
            List of document metadata dicts.
        """
        prefix = f"sessions/{session_id}/documents/"

        try:
            response = self.client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
        except ClientError:
            return []

        documents = []
        for obj in response.get("Contents", []):
            documents.append({
                "key": obj["Key"],
                "size": obj["Size"],
                "last_modified": obj["LastModified"].isoformat(),
                "filename": obj["Key"].split("/")[-1],
            })

        return documents

    def delete_session_documents(self, session_id: str) -> int:
        """Delete all documents for a session (privacy compliance).

        Args:
            session_id: Session to delete documents for.

        Returns:
            Number of objects deleted.
        """
        documents = self.list_session_documents(session_id)
        if not documents:
            return 0

        objects = [{"Key": doc["key"]} for doc in documents]
        self.client.delete_objects(
            Bucket=self.bucket,
            Delete={"Objects": objects},
        )

        logger.info("Deleted %d documents for session %s", len(objects), session_id)
        return len(objects)

    def generate_presigned_url(self, key: str, expiration: int = 3600) -> str:
        """Generate a presigned URL for document download.

        Args:
            key: S3 object key.
            expiration: URL expiration time in seconds.

        Returns:
            Presigned URL string.
        """
        url = self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expiration,
        )
        return url
