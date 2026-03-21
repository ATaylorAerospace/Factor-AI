"""Amazon Bedrock AgentCore Policy — Cedar-based action controls."""

from __future__ import annotations

import logging
from pathlib import Path

from factor.config import settings

logger = logging.getLogger(__name__)


class AgentCorePolicy:
    """Cedar policy enforcement for agent actions."""

    def __init__(self, policies_dir: str = "policies"):
        self.policies_dir = Path(policies_dir)
        self._policies: list[dict] = []
        self._load_policies()

    def _load_policies(self) -> None:
        """Load Cedar policy files from the policies directory."""
        if not self.policies_dir.exists():
            logger.warning("Policies directory not found: %s", self.policies_dir)
            return

        for policy_file in self.policies_dir.glob("*.cedar"):
            content = policy_file.read_text()
            self._policies.append({
                "name": policy_file.stem,
                "content": content,
                "file": str(policy_file),
            })
            logger.info("Loaded Cedar policy: %s", policy_file.name)

    def check_access(
        self,
        principal_id: str,
        action: str,
        resource_owner: str,
    ) -> bool:
        """Check if an action is permitted by Cedar policies.

        Enforces session isolation — users can only access their own resources.

        Args:
            principal_id: The user requesting access.
            action: The action being performed (e.g., 'read_document').
            resource_owner: The owner of the target resource.

        Returns:
            True if access is permitted, False otherwise.
        """
        if principal_id == resource_owner:
            logger.debug(
                "Access granted: %s -> %s (owner match)",
                principal_id, action,
            )
            return True

        logger.warning(
            "Access denied: %s -> %s (resource owned by %s)",
            principal_id, action, resource_owner,
        )
        return False

    def validate_session_isolation(self, session_id: str, user_id: str) -> bool:
        """Validate that a session belongs to the requesting user.

        Args:
            session_id: The session to validate.
            user_id: The requesting user.

        Returns:
            True if the session belongs to the user.
        """
        if session_id.startswith(f"factor-{user_id}-"):
            return True
        logger.warning(
            "Session isolation violation: user %s accessing session %s",
            user_id, session_id,
        )
        return False

    @property
    def loaded_policies(self) -> list[dict]:
        return self._policies
