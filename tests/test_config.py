"""Tests for settings derived properties."""

from __future__ import annotations

from factor.config import Settings


def test_wildcard_origins_allowed_in_development():
    s = Settings(factor_env="development", factor_allowed_origins="*")
    assert s.cors_origins == ["*"]
    assert s.cors_allow_credentials is False


def test_wildcard_origins_dropped_in_production():
    """A production deployment without explicit origins must not get '*'."""
    s = Settings(factor_env="production", factor_allowed_origins="*")
    assert s.cors_origins == []


def test_explicit_origins_parsed_and_allow_credentials():
    s = Settings(
        factor_env="production",
        factor_allowed_origins="https://a.example, https://b.example ,",
    )
    assert s.cors_origins == ["https://a.example", "https://b.example"]
    assert s.cors_allow_credentials is True
