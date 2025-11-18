import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class Config:
    """Configuration for Claim Assist application"""

    # API Keys
    anthropic_api_key: str
    perplexity_api_key: Optional[str] = None

    # Model selection
    routing_model: str = "claude-3-5-haiku-latest"
    simple_research_model: str = "claude-3-5-haiku-latest"
    complex_research_model: str = "claude-sonnet-4-5-20250929"

    # Processing thresholds
    value_threshold: int = 100  # Threshold for deep research vs simple pricing
    low_confidence_threshold: int = 3  # Min comparables for medium confidence
    high_confidence_threshold: int = 5  # Min comparables for high confidence

    # Pricing validation
    percentile_value: float = 0.75  # Use 75th percentile for fair replacement
    outlier_threshold: float = 0.5  # Flag if >50% deviation from median

    # Cache settings
    enable_cache: bool = True
    cache_ttl: int = 86400  # 24 hours in seconds

    # Output settings
    export_csv: bool = True
    export_json: bool = False

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables"""
        # Helper to parse env vars and strip comments
        def parse_env_value(key: str, default: str) -> str:
            value = os.getenv(key, default)
            # Strip inline comments (everything after #)
            if isinstance(value, str) and '#' in value:
                value = value.split('#')[0].strip()
            return value

        return cls(
            anthropic_api_key=parse_env_value("ANTHROPIC_API_KEY", ""),
            perplexity_api_key=parse_env_value("PERPLEXITY_API_KEY", ""),
            value_threshold=int(parse_env_value("VALUE_THRESHOLD", "100")),
            enable_cache=parse_env_value("ENABLE_CACHE", "true").lower() == "true"
        )

    def validate(self) -> None:
        """Validate required configuration"""
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")


# Default configuration
DEFAULT_CONFIG = Config(
    anthropic_api_key=""  # Must be set by user
)
