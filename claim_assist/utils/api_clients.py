import anthropic
from ..config import Config


def create_anthropic_client(config: Config) -> anthropic.Anthropic:
    """
    Create and configure Anthropic API client

    Args:
        config: Application configuration

    Returns:
        Configured Anthropic client

    Raises:
        ValueError: If API key is not configured
    """
    if not config.anthropic_api_key:
        raise ValueError("Anthropic API key is required")

    return anthropic.Anthropic(api_key=config.anthropic_api_key)
