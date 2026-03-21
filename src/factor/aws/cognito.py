"""Amazon Cognito integration for user authentication."""

from __future__ import annotations

import logging

import boto3
from botocore.exceptions import ClientError

from factor.config import settings

logger = logging.getLogger(__name__)


class CognitoAuth:
    """Cognito client for user authentication and authorization."""

    def __init__(
        self,
        user_pool_id: str | None = None,
        client_id: str | None = None,
        region_name: str | None = None,
    ):
        self.user_pool_id = user_pool_id or settings.factor_cognito_user_pool_id
        self.client_id = client_id or settings.factor_cognito_client_id
        self.region_name = region_name or settings.aws_region
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client(
                "cognito-idp",
                region_name=self.region_name,
            )
        return self._client

    def verify_token(self, token: str) -> dict | None:
        """Verify a Cognito access token.

        Args:
            token: The access token to verify.

        Returns:
            User info dict if valid, None if invalid.
        """
        if not self.user_pool_id:
            logger.warning("Cognito not configured, skipping token verification")
            return {"sub": "dev-user", "email": "dev@factor.local"}

        try:
            response = self.client.get_user(AccessToken=token)
            user_attrs = {
                attr["Name"]: attr["Value"]
                for attr in response.get("UserAttributes", [])
            }
            return {
                "sub": user_attrs.get("sub", ""),
                "email": user_attrs.get("email", ""),
                "username": response.get("Username", ""),
            }
        except ClientError as e:
            logger.warning("Token verification failed: %s", e)
            return None

    def get_user_id(self, token: str) -> str | None:
        """Extract user ID from a token.

        Args:
            token: The access token.

        Returns:
            User ID string or None.
        """
        user = self.verify_token(token)
        return user.get("sub") if user else None
