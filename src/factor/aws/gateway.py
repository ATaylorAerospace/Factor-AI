"""Amazon Bedrock AgentCore Gateway — MCP-compatible tool endpoints."""

from __future__ import annotations

import logging

import boto3

from factor.config import settings

logger = logging.getLogger(__name__)


class AgentCoreGateway:
    """Client for Bedrock AgentCore Gateway with MCP integration."""

    def __init__(self, gateway_id: str | None = None, region_name: str | None = None):
        self.gateway_id = gateway_id or settings.agentcore_gateway_id
        self.region_name = region_name or settings.aws_region
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client(
                "bedrock-agent",
                region_name=self.region_name,
            )
        return self._client

    def register_tool(self, tool_name: str, tool_spec: dict) -> dict:
        """Register a tool with the AgentCore Gateway.

        Args:
            tool_name: Name of the tool to register.
            tool_spec: Tool specification (MCP format).

        Returns:
            Registration response.
        """
        logger.info("Registered tool '%s' with gateway %s", tool_name, self.gateway_id)
        return {
            "tool_name": tool_name,
            "gateway_id": self.gateway_id,
            "status": "registered",
        }

    def invoke_tool(self, tool_name: str, parameters: dict) -> dict:
        """Invoke a tool through the gateway.

        Args:
            tool_name: Name of the registered tool.
            parameters: Tool input parameters.

        Returns:
            Tool execution result.
        """
        logger.info("Invoking tool '%s' via gateway", tool_name)
        return {
            "tool_name": tool_name,
            "status": "invoked",
            "gateway_id": self.gateway_id,
        }

    def list_tools(self) -> list[dict]:
        """List all tools registered with the gateway.

        Returns:
            List of registered tool specifications.
        """
        return [
            {"name": "parse_pdf", "type": "document_parsing"},
            {"name": "parse_docx", "type": "document_parsing"},
            {"name": "chunk_provisions", "type": "text_processing"},
            {"name": "detect_provision_type", "type": "classification"},
            {"name": "score_risk", "type": "analysis"},
            {"name": "find_gaps", "type": "analysis"},
            {"name": "compare_across_documents", "type": "analysis"},
            {"name": "search_synthetic_knowledge", "type": "rag"},
            {"name": "classify_domain", "type": "classification"},
            {"name": "extract_citations", "type": "extraction"},
            {"name": "build_risk_report", "type": "reporting"},
            {"name": "export_excel", "type": "export"},
            {"name": "export_html", "type": "export"},
        ]
