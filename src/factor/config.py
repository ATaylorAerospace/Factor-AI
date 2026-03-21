"""Application configuration using pydantic-settings."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Factor application settings loaded from environment variables."""

    model_config = {"env_prefix": "", "env_file": ".env", "extra": "ignore"}

    # AWS
    aws_region: str = "us-west-2"
    aws_profile: str = "default"
    bedrock_model_id: str = "us.anthropic.claude-sonnet-4-20250514-v1:0"

    # AgentCore
    agentcore_runtime_arn: str = ""
    agentcore_memory_store_id: str = "factor-memory"
    agentcore_gateway_id: str = "factor-gateway"

    # Application
    factor_env: Literal["development", "staging", "production"] = "development"
    factor_knowledge_path: str = "./data/chroma"
    factor_max_upload_mb: int = 50
    factor_max_batch_size: int = 100
    factor_log_level: str = "INFO"
    factor_s3_bucket: str = "factor-documents"

    # Cognito
    factor_cognito_user_pool_id: str = ""
    factor_cognito_client_id: str = ""

    @property
    def knowledge_dir(self) -> Path:
        return Path(self.factor_knowledge_path)

    @property
    def max_upload_bytes(self) -> int:
        return self.factor_max_upload_mb * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.factor_env == "production"


settings = Settings()
