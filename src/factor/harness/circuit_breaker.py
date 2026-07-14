"""Circuit breaker — combines budget enforcement and loop detection."""

from __future__ import annotations

import logging

from factor.harness.budget import SessionBudget
from factor.harness.loop_detector import LoopDetector
from factor.harness.exceptions import BudgetExceededError, ReasoningLoopError

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Financial circuit breaker for a single agent session.

    Enforces two independent trip conditions:
    1. Token spend exceeds the session budget.
    2. Agent enters a repetitive reasoning loop.

    When either condition fires, `check()` raises the corresponding
    exception, hard-halting agent execution.
    """

    def __init__(
        self,
        session_id: str,
        max_budget_usd: float = 5.0,
        input_cost_per_1m: float = 3.0,
        output_cost_per_1m: float = 15.0,
        max_steps: int = 200,
        loop_window: int = 10,
        loop_threshold: int = 5,
    ):
        self.session_id = session_id
        self.budget = SessionBudget(
            max_budget_usd=max_budget_usd,
            input_cost_per_1m=input_cost_per_1m,
            output_cost_per_1m=output_cost_per_1m,
            max_steps=max_steps,
        )
        self.loop_detector = LoopDetector(
            window_size=loop_window,
            threshold=loop_threshold,
        )
        self._tripped = False
        self._trip_reason: str | None = None

    def record_step(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        action: str = "model_call",
        meta: dict | None = None,
    ) -> None:
        """Record a reasoning step and check trip conditions."""
        self.budget.record(input_tokens, output_tokens, meta)
        signature = action
        if meta:
            signature = f"{action}:{sorted(meta.items())!r}"
        self.loop_detector.record(signature)

        logger.debug(
            "Session %s step: action=%s in=%d out=%d cost=$%.4f",
            self.session_id, action, input_tokens, output_tokens,
            self.budget.total_cost_usd,
        )

        self.check()

    def check(self) -> None:
        """Raise if any trip condition is met."""
        if self.budget.is_over_budget:
            self._tripped = True
            self._trip_reason = "budget_exceeded"
            status = self.status()
            logger.warning("CIRCUIT BREAKER: budget exceeded for session %s — $%.4f / $%.2f",
                           self.session_id, status["total_cost_usd"], status["budget_limit_usd"])
            raise BudgetExceededError(status)

        if self.budget.is_over_step_limit:
            self._tripped = True
            self._trip_reason = "step_limit_exceeded"
            status = self.status()
            logger.warning("CIRCUIT BREAKER: step limit exceeded for session %s — %d / %d",
                           self.session_id, status["steps"], status["max_steps"])
            raise BudgetExceededError(status)

        if self.loop_detector.is_looping:
            self._tripped = True
            self._trip_reason = "reasoning_loop"
            status = self.status()
            logger.warning("CIRCUIT BREAKER: reasoning loop detected for session %s — %s",
                           self.session_id, status.get("loop_signature"))
            raise ReasoningLoopError(status)

    @property
    def is_tripped(self) -> bool:
        return self._tripped

    def status(self) -> dict:
        budget_status = self.budget.status()
        loop_status = self.loop_detector.status()
        return {
            "session_id": self.session_id,
            "tripped": self._tripped,
            "reason": self._trip_reason,
            **budget_status,
            "loop_signature": loop_status["loop_signature"],
            "is_looping": loop_status["is_looping"],
        }
