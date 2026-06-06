"""GuardedBedrockModel — wraps Strands BedrockModel with circuit breaker checks."""

from __future__ import annotations

import logging

from strands.models.bedrock import BedrockModel

from factor.config import settings
from factor.harness.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class GuardedBedrockModel:
    """Proxy around `BedrockModel` that enforces financial guardrails.

    Before every model invocation the circuit breaker is checked.  If it
    has already tripped (budget exceeded or reasoning loop) the call is
    blocked immediately without consuming additional tokens.

    All other attribute access is delegated transparently to the
    underlying `BedrockModel` so Strands sees a duck-type-compatible
    model object.
    """

    def __init__(self, model: BedrockModel, breaker: CircuitBreaker):
        # Store on the instance dict directly to avoid __getattr__ recursion
        object.__setattr__(self, "_model", model)
        object.__setattr__(self, "_breaker", breaker)

    def __getattr__(self, name: str):
        return getattr(self._model, name)

    def __setattr__(self, name: str, value):
        if name.startswith("_"):
            object.__setattr__(self, name, value)
        else:
            setattr(self._model, name, value)

    def __call__(self, *args, **kwargs):
        """Intercept the model call to enforce guardrails."""
        self._breaker.check()
        return self._model(*args, **kwargs)

    def converse(self, *args, **kwargs):
        self._breaker.check()
        return self._model.converse(*args, **kwargs)

    def invoke(self, *args, **kwargs):
        self._breaker.check()
        return self._model.invoke(*args, **kwargs)

    def update_config(self, *args, **kwargs):
        self._breaker.check()
        return self._model.update_config(*args, **kwargs)

    def format_request(self, *args, **kwargs):
        return self._model.format_request(*args, **kwargs)

    def format_chunk(self, *args, **kwargs):
        return self._model.format_chunk(*args, **kwargs)


def guarded_model(breaker: CircuitBreaker) -> GuardedBedrockModel:
    """Create a GuardedBedrockModel with the standard config.

    Args:
        breaker: The circuit breaker instance for this session.

    Returns:
        A model proxy that halts on budget / loop violations.
    """
    model = BedrockModel(
        model_id=settings.bedrock_model_id,
        region_name=settings.aws_region,
    )
    return GuardedBedrockModel(model, breaker)
