"""Per-session token cost accounting."""

from __future__ import annotations

import threading
import time


class SessionBudget:
    """Accumulates token costs for a single agent session.

    Pricing defaults match Anthropic Claude Sonnet on Bedrock
    ($3 / 1M input tokens, $15 / 1M output tokens).
    """

    def __init__(
        self,
        max_budget_usd: float,
        input_cost_per_1m: float = 3.0,
        output_cost_per_1m: float = 15.0,
        max_steps: int = 200,
    ):
        self.max_budget_usd = max_budget_usd
        self.input_cost_per_1m = input_cost_per_1m
        self.output_cost_per_1m = output_cost_per_1m
        self.max_steps = max_steps

        self._lock = threading.Lock()
        self._input_tokens = 0
        self._output_tokens = 0
        self._steps = 0
        self._history: list[dict] = []
        self._created_at = time.time()

    def record(self, input_tokens: int, output_tokens: int, meta: dict | None = None) -> None:
        with self._lock:
            self._input_tokens += input_tokens
            self._output_tokens += output_tokens
            self._steps += 1
            self._history.append({
                "step": self._steps,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cumulative_cost_usd": self._cost_unlocked(),
                "timestamp": time.time(),
                "meta": meta or {},
            })

    @property
    def total_cost_usd(self) -> float:
        with self._lock:
            return self._cost_unlocked()

    def _cost_unlocked(self) -> float:
        input_cost = (self._input_tokens / 1_000_000) * self.input_cost_per_1m
        output_cost = (self._output_tokens / 1_000_000) * self.output_cost_per_1m
        return input_cost + output_cost

    @property
    def is_over_budget(self) -> bool:
        with self._lock:
            return self._cost_unlocked() >= self.max_budget_usd

    @property
    def is_over_step_limit(self) -> bool:
        with self._lock:
            return self._steps >= self.max_steps

    def status(self) -> dict:
        with self._lock:
            cost = self._cost_unlocked()
            return {
                "input_tokens": self._input_tokens,
                "output_tokens": self._output_tokens,
                "total_tokens": self._input_tokens + self._output_tokens,
                "total_cost_usd": round(cost, 6),
                "budget_limit_usd": self.max_budget_usd,
                "budget_remaining_usd": round(max(0, self.max_budget_usd - cost), 6),
                "budget_utilization_pct": round((cost / self.max_budget_usd) * 100, 2) if self.max_budget_usd > 0 else 0,
                "steps": self._steps,
                "max_steps": self.max_steps,
                "elapsed_seconds": round(time.time() - self._created_at, 2),
            }

    @property
    def history(self) -> list[dict]:
        with self._lock:
            return list(self._history)
