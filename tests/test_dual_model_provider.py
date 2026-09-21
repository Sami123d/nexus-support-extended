from unittest.mock import MagicMock

import pytest

from customer_support_agent import DualModelProvider


def test_invoke_uses_primary_when_healthy(monkeypatch):
    monkeypatch.setenv("FALLBACK_API_KEY", "test-fallback-key")
    provider = DualModelProvider()
    provider.primary = MagicMock()
    provider.secondary = MagicMock()
    provider.primary.invoke.return_value = "primary response"

    result = provider.invoke("hello")

    assert result == "primary response"
    provider.secondary.invoke.assert_not_called()


def test_invoke_falls_back_to_secondary_on_primary_failure(monkeypatch):
    monkeypatch.setenv("FALLBACK_API_KEY", "test-fallback-key")
    provider = DualModelProvider()
    provider.primary = MagicMock()
    provider.secondary = MagicMock()
    provider.primary.invoke.side_effect = RuntimeError("DeepSeek is down")
    provider.secondary.invoke.return_value = "secondary response"

    result = provider.invoke("hello")

    assert result == "secondary response"


def test_invoke_reraises_when_no_fallback_configured(monkeypatch):
    monkeypatch.delenv("FALLBACK_API_KEY", raising=False)
    provider = DualModelProvider()
    assert provider.secondary is None
    provider.primary = MagicMock()
    provider.primary.invoke.side_effect = RuntimeError("DeepSeek is down")

    with pytest.raises(RuntimeError, match="DeepSeek is down"):
        provider.invoke("hello")


def test_with_structured_output_falls_back(monkeypatch):
    monkeypatch.setenv("FALLBACK_API_KEY", "test-fallback-key")
    provider = DualModelProvider()

    primary_chain = MagicMock()
    primary_chain.invoke.side_effect = RuntimeError("primary structured call failed")
    secondary_chain = MagicMock()
    secondary_chain.invoke.return_value = {"ok": True}

    provider.primary = MagicMock()
    provider.primary.with_structured_output.return_value = primary_chain
    provider.secondary = MagicMock()
    provider.secondary.with_structured_output.return_value = secondary_chain

    chain = provider.with_structured_output(schema=dict)
    result = chain.invoke("hello")

    assert result == {"ok": True}
