"""FinancialGuardrail — manages per-session circuit breakers."""

from __future__ import annotations

import logging
import threading

from factor.config import settings
from factor.harness.circuit_breaker import CircuitBreaker
from factor.harness.exceptions import CircuitBreakerTripped

logger = logging.getLogger(__name__)

_instance: FinancialGuardrail | None = None
_instance_lock = threading.Lock()


class FinancialGuardrail:
    """Central registry of per-session circuit breakers.

    One instance is shared across the application.  Each analysis session
    gets its own `CircuitBreaker` with independent budget and loop state.
    """

    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()

    def register_session(self, session_id: str) -> CircuitBreaker:
        """Create and register a circuit breaker for a new session."""
        breaker = CircuitBreaker(
            session_id=session_id,
            max_budget_usd=settings.guardrail_session_budget_usd,
            input_cost_per_1m=settings.guardrail_input_cost_per_1m,
            output_cost_per_1m=settings.guardrail_output_cost_per_1m,
            max_steps=settings.guardrail_max_steps,
            loop_window=settings.guardrail_loop_window,
            loop_threshold=settings.guardrail_loop_threshold,
        )
        with self._lock:
            self._breakers[session_id] = breaker
        logger.info(
            "Registered circuit breaker for session %s (budget=$%.2f, max_steps=%d)",
            session_id, settings.guardrail_session_budget_usd, settings.guardrail_max_steps,
        )
        return breaker

    def get_breaker(self, session_id: str) -> CircuitBreaker | None:
        with self._lock:
            return self._breakers.get(session_id)

    def remove_session(self, session_id: str) -> None:
        with self._lock:
            self._breakers.pop(session_id, None)

    def record_from_span(
        self,
        session_id: str | None,
        input_tokens: int,
        output_tokens: int,
        action: str,
    ) -> None:
        """Called by `GuardrailSpanProcessor` when a span with token data ends.

        Silently ignores unknown session IDs (spans from background work).
        """
        if session_id is None:
            return
        breaker = self.get_breaker(session_id)
        if breaker is None:
            return
        try:
            breaker.record_step(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                action=action,
            )
        except CircuitBreakerTripped:
            # Let it propagate up the call stack to halt the agent
            raise

    def session_status(self, session_id: str) -> dict | None:
        breaker = self.get_breaker(session_id)
        if breaker is None:
            return None
        return breaker.status()

    def all_sessions(self) -> list[dict]:
        with self._lock:
            return [b.status() for b in self._breakers.values()]


def get_guardrail() -> FinancialGuardrail:
    """Return the singleton FinancialGuardrail instance."""
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = FinancialGuardrail()
    return _instance
