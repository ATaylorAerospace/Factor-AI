"""Amazon Bedrock integration — model invocation with retry logic."""

from __future__ import annotations

import json
import logging
import time

import boto3
from botocore.exceptions import ClientError

from factor.config import settings

logger = logging.getLogger(__name__)


class BedrockClient:
    """Client for Amazon Bedrock foundation model invocations."""

    def __init__(
        self,
        model_id: str | None = None,
        region_name: str | None = None,
        max_retries: int = 4,
    ):
        self.model_id = model_id or settings.bedrock_model_id
        self.region_name = region_name or settings.aws_region
        self.max_retries = max_retries
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client(
                "bedrock-runtime",
                region_name=self.region_name,
            )
        return self._client

    def invoke(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        system: str | None = None,
    ) -> dict:
        """Invoke a Bedrock model with exponential backoff retry.

        Args:
            prompt: The user prompt.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.
            system: Optional system prompt.

        Returns:
            Model response dictionary.
        """
        messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        if system:
            body["system"] = system

        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(body),
                    contentType="application/json",
                    accept="application/json",
                )

                result = json.loads(response["body"].read())
                return {
                    "content": result.get("content", [{}])[0].get("text", ""),
                    "model": self.model_id,
                    "usage": result.get("usage", {}),
                    "stop_reason": result.get("stop_reason", ""),
                }

            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                if error_code == "ThrottlingException" and attempt < self.max_retries:
                    wait_time = 2 ** (attempt + 1)
                    logger.warning(
                        "Bedrock throttled (attempt %d/%d), retrying in %ds",
                        attempt + 1, self.max_retries, wait_time,
                    )
                    time.sleep(wait_time)
                    continue
                raise

        return {"content": "", "error": "Max retries exceeded"}

    def invoke_streaming(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        system: str | None = None,
    ):
        """Invoke with streaming response.

        Yields:
            Text chunks from the model response.
        """
        messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        if system:
            body["system"] = system

        response = self.client.invoke_model_with_response_stream(
            modelId=self.model_id,
            body=json.dumps(body),
            contentType="application/json",
        )

        for event in response["body"]:
            chunk = json.loads(event["chunk"]["bytes"])
            if chunk.get("type") == "content_block_delta":
                delta = chunk.get("delta", {})
                if delta.get("type") == "text_delta":
                    yield delta.get("text", "")
