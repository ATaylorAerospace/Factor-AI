"""Circuit breaker exceptions — raised to hard-halt agent execution."""

from __future__ import annotations


class CircuitBreakerTripped(Exception):
    """Base exception for all circuit breaker halts."""

    def __init__(self, status: dict):
        self.status = status
        super().__init__(self._format(status))

    @staticmethod
    def _format(status: dict) -> str:
        reason = status.get("reason", "unknown")
        cost = status.get("total_cost_usd", 0)
        steps = status.get("total_steps", 0)
        return (
            f"Circuit breaker tripped: {reason} "
            f"(cost=${cost:.4f}, steps={steps})"
        )


class BudgetExceededError(CircuitBreakerTripped):
    """Session token spend exceeded the configured budget."""


class ReasoningLoopError(CircuitBreakerTripped):
    """Agent is stuck in a repetitive high-cost reasoning loop."""
