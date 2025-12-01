"""
API clients for both local inference and legacy cloud APIs
"""

from typing import Optional, Union
from ..config import Config
from .local_inference import InferenceClientFactory, LocalInferenceClient


def create_inference_client(config: Config) -> LocalInferenceClient:
    """
    Create an inference client based on configuration
    
    Args:
        config: Application configuration
        
    Returns:
        LocalInferenceClient instance
        
    Raises:
        ValueError: If configuration is invalid or backend is unavailable
    """
    # Handle Anthropic API
    if config.inference_backend == "anthropic":
        return _create_anthropic_wrapper(config)
    
    # Handle llamacpp_python (local GGUF model)
    elif config.inference_backend == "llamacpp_python":
        return InferenceClientFactory.create_client(
            backend_type="llamacpp_python",
            model_name=config.model_name,
            model_path=config.model_path,
            n_gpu_layers=config.n_gpu_layers,
            n_ctx=config.n_ctx
        )
    
    else:
        raise ValueError(f"Unsupported backend: {config.inference_backend}")


def create_anthropic_client(config: Config):
    """
    Legacy function for backward compatibility
    Creates Anthropic client wrapped in our interface
    """
    return _create_anthropic_wrapper(config)


def _create_anthropic_wrapper(config: Config) -> LocalInferenceClient:
    """Create a wrapper around Anthropic API to match our interface"""
    try:
        import anthropic
    except ImportError:
        raise ValueError("Anthropic library not installed. Install with: pip install anthropic")
    
    if not config.anthropic_api_key:
        raise ValueError("Anthropic API key is required")
    
    client = anthropic.Anthropic(api_key=config.anthropic_api_key)
    return AnthropicWrapper(client)


class AnthropicWrapper(LocalInferenceClient):
    """Wrapper to make Anthropic API compatible with LocalInferenceClient interface"""
    
    def __init__(self, anthropic_client, model: str = "claude-3-5-haiku-20241022"):
        self.client = anthropic_client
        self.model = model
        self._model_name = model  # Store for compatibility
    
    def generate(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.1):
        """Generate response using Anthropic API"""
        from .local_inference import InferenceResponse
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = ""
            for block in message.content:
                if hasattr(block, 'text'):
                    content += block.text
            
            return InferenceResponse(
                content=content,
                model=self.model,
                tokens_used=getattr(message.usage, 'total_tokens', None) if hasattr(message, 'usage') else None,
                success=True
            )
            
        except Exception as e:
            return InferenceResponse(
                content="",
                model=self.model,
                success=False,
                error=str(e)
            )
    
    def is_available(self) -> bool:
        """Check if Anthropic API is available"""
        try:
            # Try a minimal API call to check availability
            self.client.messages.create(
                model=self.model,
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except:
            return False
