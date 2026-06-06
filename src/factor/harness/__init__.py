"""Financial-Guardrail & Telemetry Harness for Factor agents.

Wraps Bedrock AgentCore execution to audit token I/O at every reasoning
step, enforce per-session budgets, and halt agents stuck in repetitive
high-cost reasoning loops.  Traces are exported to Arize Phoenix via OTLP.
"""

from factor.harness.exceptions import (
    CircuitBreakerTripped,
    BudgetExceededError,
    ReasoningLoopError,
)
from factor.harness.budget import SessionBudget
from factor.harness.loop_detector import LoopDetector
from factor.harness.circuit_breaker import CircuitBreaker
from factor.harness.guardrail import FinancialGuardrail, get_guardrail

__all__ = [
    "CircuitBreakerTripped",
    "BudgetExceededError",
    "ReasoningLoopError",
    "SessionBudget",
    "LoopDetector",
    "CircuitBreaker",
    "FinancialGuardrail",
    "get_guardrail",
]


def guarded_model(breaker):
    """Lazy import to avoid requiring strands at import time."""
    from factor.harness.model_wrapper import guarded_model as _guarded_model
    return _guarded_model(breaker)
