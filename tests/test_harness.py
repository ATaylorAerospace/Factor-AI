"""Tests for the Financial-Guardrail & Telemetry Harness."""

from __future__ import annotations

import pytest

from factor.harness.budget import SessionBudget
from factor.harness.loop_detector import LoopDetector
from factor.harness.circuit_breaker import CircuitBreaker
from factor.harness.exceptions import (
    BudgetExceededError,
    ReasoningLoopError,
    CircuitBreakerTripped,
)
from factor.harness.guardrail import FinancialGuardrail


# ---------------------------------------------------------------------------
# SessionBudget
# ---------------------------------------------------------------------------

class TestSessionBudget:
    def test_initial_state(self):
        budget = SessionBudget(max_budget_usd=5.0)
        status = budget.status()
        assert status["input_tokens"] == 0
        assert status["output_tokens"] == 0
        assert status["total_cost_usd"] == 0
        assert status["budget_limit_usd"] == 5.0
        assert not budget.is_over_budget

    def test_cost_calculation(self):
        budget = SessionBudget(
            max_budget_usd=10.0,
            input_cost_per_1m=3.0,
            output_cost_per_1m=15.0,
        )
        budget.record(1_000_000, 0)
        assert budget.total_cost_usd == pytest.approx(3.0)

        budget.record(0, 1_000_000)
        assert budget.total_cost_usd == pytest.approx(18.0)

    def test_over_budget(self):
        budget = SessionBudget(max_budget_usd=0.01, input_cost_per_1m=3.0)
        budget.record(100_000, 0)
        assert budget.is_over_budget

    def test_step_limit(self):
        budget = SessionBudget(max_budget_usd=100.0, max_steps=3)
        budget.record(10, 10)
        budget.record(10, 10)
        assert not budget.is_over_step_limit
        budget.record(10, 10)
        assert budget.is_over_step_limit

    def test_history(self):
        budget = SessionBudget(max_budget_usd=10.0)
        budget.record(100, 200, {"tool": "detect"})
        budget.record(300, 400, {"tool": "score"})
        assert len(budget.history) == 2
        assert budget.history[0]["input_tokens"] == 100
        assert budget.history[1]["meta"]["tool"] == "score"

    def test_utilization_percentage(self):
        budget = SessionBudget(max_budget_usd=10.0, input_cost_per_1m=10.0)
        budget.record(500_000, 0)
        status = budget.status()
        assert status["budget_utilization_pct"] == pytest.approx(50.0)


# ---------------------------------------------------------------------------
# LoopDetector
# ---------------------------------------------------------------------------

class TestLoopDetector:
    def test_no_loop_initially(self):
        detector = LoopDetector(window_size=10, threshold=5)
        assert not detector.is_looping

    def test_detects_repetitive_actions(self):
        detector = LoopDetector(window_size=10, threshold=3)
        detector.record("tool_a")
        detector.record("tool_a")
        assert not detector.is_looping
        detector.record("tool_a")
        assert detector.is_looping
        assert detector.status()["loop_signature"] == "tool_a"

    def test_mixed_actions_no_loop(self):
        detector = LoopDetector(window_size=10, threshold=5)
        for i in range(10):
            detector.record(f"tool_{i}")
        assert not detector.is_looping

    def test_reset_clears_state(self):
        detector = LoopDetector(window_size=5, threshold=3)
        for _ in range(3):
            detector.record("stuck")
        assert detector.is_looping
        detector.reset()
        assert not detector.is_looping
        assert detector.status()["loop_signature"] is None

    def test_window_rotation(self):
        detector = LoopDetector(window_size=5, threshold=4)
        for _ in range(3):
            detector.record("tool_a")
        for _ in range(5):
            detector.record("tool_b")
        status = detector.status()
        assert len(status["window"]) == 5
        assert all(a == "tool_b" for a in status["window"])


# ---------------------------------------------------------------------------
# CircuitBreaker
# ---------------------------------------------------------------------------

class TestCircuitBreaker:
    def test_normal_operation(self):
        breaker = CircuitBreaker(
            session_id="test-session",
            max_budget_usd=10.0,
            max_steps=100,
        )
        breaker.record_step(input_tokens=100, output_tokens=50, action="analyze")
        assert not breaker.is_tripped

    def test_budget_trip(self):
        breaker = CircuitBreaker(
            session_id="test-session",
            max_budget_usd=0.001,
            input_cost_per_1m=3.0,
        )
        with pytest.raises(BudgetExceededError) as exc_info:
            breaker.record_step(input_tokens=1_000_000, output_tokens=0, action="big_call")
        assert breaker.is_tripped
        assert exc_info.value.status["reason"] == "budget_exceeded"

    def test_step_limit_trip(self):
        breaker = CircuitBreaker(
            session_id="test-session",
            max_budget_usd=1000.0,
            max_steps=3,
        )
        breaker.record_step(input_tokens=10, output_tokens=10, action="a")
        breaker.record_step(input_tokens=10, output_tokens=10, action="b")
        with pytest.raises(BudgetExceededError) as exc_info:
            breaker.record_step(input_tokens=10, output_tokens=10, action="c")
        assert exc_info.value.status["reason"] == "step_limit_exceeded"

    def test_loop_trip(self):
        breaker = CircuitBreaker(
            session_id="test-session",
            max_budget_usd=1000.0,
            max_steps=1000,
            loop_window=10,
            loop_threshold=3,
        )
        with pytest.raises(ReasoningLoopError) as exc_info:
            for _ in range(5):
                breaker.record_step(input_tokens=10, output_tokens=10, action="stuck_tool")
        assert breaker.is_tripped
        assert exc_info.value.status["reason"] == "reasoning_loop"
        assert exc_info.value.status["loop_signature"] == "stuck_tool"

    def test_distinct_meta_does_not_trip_loop(self):
        """Repeating the same action over distinct items is not a loop."""
        breaker = CircuitBreaker(
            session_id="test-session",
            max_budget_usd=1000.0,
            max_steps=1000,
            loop_window=10,
            loop_threshold=5,
        )
        for i in range(20):
            breaker.record_step(
                action="score_risk",
                meta={"doc_id": "doc-1", "provision_index": i},
            )
        assert not breaker.is_tripped

    def test_identical_meta_still_trips_loop(self):
        breaker = CircuitBreaker(
            session_id="test-session",
            max_budget_usd=1000.0,
            max_steps=1000,
            loop_window=10,
            loop_threshold=3,
        )
        with pytest.raises(ReasoningLoopError):
            for _ in range(5):
                breaker.record_step(
                    action="score_risk",
                    meta={"doc_id": "doc-1", "provision_index": 0},
                )
        assert breaker.is_tripped

    def test_status_report(self):
        breaker = CircuitBreaker(session_id="test-session", max_budget_usd=5.0)
        breaker.record_step(input_tokens=1000, output_tokens=500, action="analyze")
        status = breaker.status()
        assert status["session_id"] == "test-session"
        assert status["tripped"] is False
        assert status["input_tokens"] == 1000
        assert status["output_tokens"] == 500
        assert status["steps"] == 1
        assert "total_cost_usd" in status


# ---------------------------------------------------------------------------
# FinancialGuardrail
# ---------------------------------------------------------------------------

class TestFinancialGuardrail:
    def test_register_and_retrieve(self):
        guardrail = FinancialGuardrail()
        breaker = guardrail.register_session("session-1")
        assert breaker is not None
        assert guardrail.get_breaker("session-1") is breaker

    def test_session_status(self):
        guardrail = FinancialGuardrail()
        guardrail.register_session("session-1")
        status = guardrail.session_status("session-1")
        assert status is not None
        assert status["session_id"] == "session-1"

    def test_unknown_session_returns_none(self):
        guardrail = FinancialGuardrail()
        assert guardrail.session_status("nonexistent") is None
        assert guardrail.get_breaker("nonexistent") is None

    def test_remove_session(self):
        guardrail = FinancialGuardrail()
        guardrail.register_session("session-1")
        guardrail.remove_session("session-1")
        assert guardrail.get_breaker("session-1") is None

    def test_record_from_span(self):
        guardrail = FinancialGuardrail()
        guardrail.register_session("session-1")
        guardrail.record_from_span(
            session_id="session-1",
            input_tokens=100,
            output_tokens=50,
            action="model_call",
        )
        status = guardrail.session_status("session-1")
        assert status["input_tokens"] == 100
        assert status["steps"] == 1

    def test_record_from_span_unknown_session_is_silent(self):
        guardrail = FinancialGuardrail()
        guardrail.record_from_span(
            session_id="unknown",
            input_tokens=100,
            output_tokens=50,
            action="model_call",
        )

    def test_all_sessions(self):
        guardrail = FinancialGuardrail()
        guardrail.register_session("s1")
        guardrail.register_session("s2")
        sessions = guardrail.all_sessions()
        assert len(sessions) == 2
        ids = {s["session_id"] for s in sessions}
        assert ids == {"s1", "s2"}


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class TestExceptions:
    def test_circuit_breaker_tripped_hierarchy(self):
        assert issubclass(BudgetExceededError, CircuitBreakerTripped)
        assert issubclass(ReasoningLoopError, CircuitBreakerTripped)

    def test_exception_carries_status(self):
        status = {"reason": "budget_exceeded", "total_cost_usd": 5.01, "total_steps": 42}
        exc = BudgetExceededError(status)
        assert exc.status is status
        assert "budget_exceeded" in str(exc)
        assert "5.01" in str(exc)
