"""AgentCore Observability — OpenTelemetry tracing and CloudWatch integration."""

from __future__ import annotations

import logging

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

logger = logging.getLogger(__name__)

_initialized = False


def init_tracing(service_name: str = "factor") -> trace.Tracer:
    """Initialize OpenTelemetry tracing.

    Args:
        service_name: Name of the service for trace attribution.

    Returns:
        Configured Tracer instance.
    """
    global _initialized

    if not _initialized:
        provider = TracerProvider()
        processor = SimpleSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        _initialized = True
        logger.info("OpenTelemetry tracing initialized for service: %s", service_name)

    return trace.get_tracer(service_name)


def trace_agent_call(agent_name: str, operation: str):
    """Decorator to trace agent calls with OpenTelemetry.

    Args:
        agent_name: Name of the agent being traced.
        operation: The operation being performed.

    Returns:
        Decorator function.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracer = init_tracing()
            with tracer.start_as_current_span(
                f"{agent_name}.{operation}",
                attributes={
                    "agent.name": agent_name,
                    "agent.operation": operation,
                    "factor.synthetic_data": True,
                },
            ) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("agent.status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("agent.status", "error")
                    span.set_attribute("agent.error", str(e))
                    raise
        return wrapper
    return decorator


class AgentTraceCollector:
    """Collect and structure agent reasoning traces."""

    def __init__(self):
        self.traces: list[dict] = []

    def record(self, agent_name: str, action: str, details: dict | None = None) -> None:
        """Record a trace event.

        Args:
            agent_name: Which agent performed the action.
            action: What action was performed.
            details: Optional additional details.
        """
        import time

        entry = {
            "agent": agent_name,
            "action": action,
            "timestamp": time.time(),
            "details": details or {},
        }
        self.traces.append(entry)

    def get_trace(self) -> list[dict]:
        """Return all collected trace entries."""
        return self.traces

    def clear(self) -> None:
        """Clear all traces."""
        self.traces.clear()
