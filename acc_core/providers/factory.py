"""Provider factory — creates the right provider based on configuration."""

import os
from acc_core.config import get
from acc_core.providers.base import BaseProvider


PROVIDER_REGISTRY: dict[str, type[BaseProvider]] = {}


def register_provider(name: str):
    """Decorator to register a provider class."""
    def decorator(cls):
        PROVIDER_REGISTRY[name] = cls
        return cls
    return decorator


def create_provider(
    provider: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
) -> BaseProvider:
    """Create a provider instance based on configuration or explicit arguments.

    Priority: explicit args > environment variables > config defaults.
    Provider detection: explicit provider > ACC_PROVIDER env > auto-detect from available keys.
    """
    provider = provider or os.environ.get("ACC_PROVIDER") or get("provider")

    # Auto-detect provider from available API keys
    if not provider or provider == "auto":
        if os.environ.get("ANTHROPIC_API_KEY"):
            provider = "anthropic"
        elif os.environ.get("DEEPSEEK_API_KEY"):
            provider = "deepseek"
        else:
            provider = "anthropic"  # default

    if provider not in PROVIDER_REGISTRY:
        raise ValueError(
            f"Unknown provider: {provider}. Available: {list(PROVIDER_REGISTRY.keys())}"
        )

    # Resolve API key
    if not api_key:
        key_env_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
        }
        env_var = key_env_map.get(provider, "ANTHROPIC_API_KEY")
        api_key = os.environ.get(env_var, "")

    if not api_key:
        raise ValueError(
            f"No API key found for provider '{provider}'. "
            f"Set {key_env_map.get(provider, 'API_KEY')} environment variable."
        )

    # Resolve model
    if not model:
        model = os.environ.get("ACC_MODEL")
    if not model:
        model_defaults = {
            "anthropic": "claude-sonnet-4-5-20250929",
            "deepseek": "deepseek-chat",
        }
        model = model_defaults.get(provider, "deepseek-chat")

    provider_cls = PROVIDER_REGISTRY[provider]
    return provider_cls(api_key=api_key, model=model)


def get_available_providers() -> list[str]:
    """List registered provider names."""
    return list(PROVIDER_REGISTRY.keys())


# Import provider modules at the bottom to trigger their @register_provider decorators
# and populate PROVIDER_REGISTRY, avoiding circular dependency issues.
import acc_core.providers.anthropic
import acc_core.providers.deepseek
