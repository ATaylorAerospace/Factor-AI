"""Phoenix OTLP telemetry — exports OpenTelemetry traces to Arize Phoenix."""

from __future__ import annotations

import logging

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, ReadableSpan
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
    ConsoleSpanExporter,
)

from factor.config import settings

logger = logging.getLogger(__name__)

_initialized = False


class GuardrailSpanProcessor(SimpleSpanProcessor):
    """SpanProcessor that extracts token usage from OTel spans and feeds
    it to the active circuit breaker for the session.

    Works with both OpenInference and OpenTelemetry GenAI semantic
    conventions for token count attributes.
    """

    # Attribute names used by different instrumentation libraries
    TOKEN_ATTR_MAPS = [
        # OpenTelemetry GenAI semantic conventions
        ("gen_ai.usage.input_tokens", "gen_ai.usage.output_tokens"),
        # OpenInference / Phoenix conventions
        ("llm.token_count.prompt", "llm.token_count.completion"),
        # Strands-specific (if present)
        ("strands.input_tokens", "strands.output_tokens"),
    ]

    def __init__(self, exporter: SpanExporter):
        super().__init__(exporter)
        self._guardrail = None

    def set_guardrail(self, guardrail) -> None:
        self._guardrail = guardrail

    def on_end(self, span: ReadableSpan) -> None:
        super().on_end(span)

        if self._guardrail is None:
            return

        attrs = span.attributes or {}
        input_tokens = 0
        output_tokens = 0

        for input_key, output_key in self.TOKEN_ATTR_MAPS:
            inp = attrs.get(input_key, 0)
            out = attrs.get(output_key, 0)
            if inp or out:
                input_tokens = int(inp)
                output_tokens = int(out)
                break

        if input_tokens or output_tokens:
            session_id = attrs.get("session.id") or attrs.get("factor.session_id")
            action = span.name or "unknown"
            self._guardrail.record_from_span(
                session_id=session_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                action=action,
            )


def init_phoenix_tracing(service_name: str = "factor") -> tuple[trace.Tracer, GuardrailSpanProcessor | None]:
    """Initialize OpenTelemetry with Phoenix OTLP exporter.

    Falls back to ConsoleSpanExporter when Phoenix deps are unavailable
    or the endpoint is not configured.

    Returns:
        Tuple of (tracer, guardrail_processor).  The processor is None
        when Phoenix is not available.
    """
    global _initialized

    if _initialized:
        return trace.get_tracer(service_name), None

    provider = TracerProvider()
    guardrail_processor = None

    if settings.phoenix_enabled and settings.phoenix_otlp_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

            phoenix_exporter = OTLPSpanExporter(
                endpoint=settings.phoenix_otlp_endpoint,
            )
            guardrail_processor = GuardrailSpanProcessor(phoenix_exporter)
            provider.add_span_processor(guardrail_processor)
            logger.info("Phoenix OTLP exporter configured: %s", settings.phoenix_otlp_endpoint)
        except ImportError:
            logger.warning("opentelemetry-exporter-otlp not installed, falling back to console")
            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    else:
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        logger.info("Phoenix disabled or endpoint not set, using console exporter")

    trace.set_tracer_provider(provider)
    _initialized = True

    return trace.get_tracer(service_name), guardrail_processor
