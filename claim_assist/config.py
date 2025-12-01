import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class Config:
    """Configuration for Claim Assist application"""

    # Local Inference Configuration
    inference_backend: str = "ollama"  # ollama, openai_compatible, transformers
    model_name: str = "llama3.1:8b"
    inference_base_url: str = "http://localhost:11434"
    inference_api_key: Optional[str] = None  # For OpenAI-compatible APIs
    
    # Legacy API Keys (deprecated, for backward compatibility)
    anthropic_api_key: Optional[str] = None
    perplexity_api_key: Optional[str] = None

    # Model selection (now using local models)
    routing_model: str = "llama3.1:8b"
    simple_research_model: str = "llama3.1:8b"
    complex_research_model: str = "llama3.1:8b"  # Can be a larger model for complex items

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

    # Web Scraping Configuration
    scraping_delay: float = 1.0  # Delay between requests (seconds)
    max_results_per_source: int = 10
    enable_alternative_sources: bool = True  # Craigslist as alternative to Facebook
    craigslist_location: str = "sfbay"  # Default Craigslist location

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
            # Local inference settings
            inference_backend=parse_env_value("INFERENCE_BACKEND", "ollama"),
            model_name=parse_env_value("MODEL_NAME", "llama3.1:8b"),
            inference_base_url=parse_env_value("INFERENCE_BASE_URL", "http://localhost:11434"),
            inference_api_key=parse_env_value("INFERENCE_API_KEY", ""),
            
            # Legacy settings (for backward compatibility)
            anthropic_api_key=parse_env_value("ANTHROPIC_API_KEY", ""),
            perplexity_api_key=parse_env_value("PERPLEXITY_API_KEY", ""),
            
            # Processing settings
            value_threshold=int(parse_env_value("VALUE_THRESHOLD", "100")),
            enable_cache=parse_env_value("ENABLE_CACHE", "true").lower() == "true",
            
            # Web scraping settings
            scraping_delay=float(parse_env_value("SCRAPING_DELAY", "1.0")),
            max_results_per_source=int(parse_env_value("MAX_RESULTS_PER_SOURCE", "10")),
            enable_alternative_sources=parse_env_value("ENABLE_ALT_SOURCES", "true").lower() == "true",
            craigslist_location=parse_env_value("CRAIGSLIST_LOCATION", "sfbay")
        )

    def validate(self) -> None:
        """Validate required configuration"""
        # Check that we have either local inference setup or legacy API key
        if self.inference_backend == "anthropic" and not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when using anthropic backend")
        
        if self.inference_backend == "openai_compatible" and not self.inference_api_key:
            raise ValueError("INFERENCE_API_KEY is required when using openai_compatible backend")
        
        # Validate backend type
        valid_backends = ["ollama", "openai_compatible", "transformers", "anthropic"]
        if self.inference_backend not in valid_backends:
            raise ValueError(f"Invalid inference backend: {self.inference_backend}. Must be one of: {valid_backends}")


# Default configuration
DEFAULT_CONFIG = Config(
    inference_backend="ollama",
    model_name="llama3.1:8b"
)
