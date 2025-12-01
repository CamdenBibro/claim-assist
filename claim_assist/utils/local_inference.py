"""
Local inference client for various local LLM backends
Supports llama.cpp, vLLM, Transformers, and OpenAI-compatible APIs
"""

import json
import requests
from typing import Dict, List, Optional, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class InferenceResponse:
    """Response from local inference"""
    content: str
    model: str
    tokens_used: Optional[int] = None
    success: bool = True
    error: Optional[str] = None


class LocalInferenceClient(ABC):
    """Abstract base class for local inference clients"""
    
    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.1) -> InferenceResponse:
        """Generate response from local model"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the inference backend is available"""
        pass


class LlamaCppClient(LocalInferenceClient):
    """Client for llama.cpp server (OpenAI-compatible API with better AMD GPU support)"""
    
    def __init__(self, model_name: str = "llama-3.1-8b", base_url: str = "http://localhost:8080/v1", api_key: str = "dummy"):
        self.model_name = model_name
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def generate(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.1) -> InferenceResponse:
        """Generate response using llama.cpp server"""
        try:
            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            tokens_used = result.get("usage", {}).get("total_tokens")
            
            return InferenceResponse(
                content=content,
                model=self.model_name,
                tokens_used=tokens_used,
                success=True
            )
            
        except Exception as e:
            return InferenceResponse(
                content="",
                model=self.model_name,
                success=False,
                error=str(e)
            )
    
    def is_available(self) -> bool:
        """Check if llama.cpp server is available"""
        try:
            # Try the health endpoint first
            response = requests.get(f"{self.base_url.replace('/v1', '')}/health", timeout=5)
            if response.status_code == 200:
                return True
            # Fallback to models endpoint
            response = requests.get(f"{self.base_url}/models", headers=self.headers, timeout=5)
            return response.status_code == 200
        except:
            return False


class OpenAICompatibleClient(LocalInferenceClient):
    """Client for OpenAI-compatible APIs (vLLM, LocalAI, etc.)"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", base_url: str = "http://localhost:8000/v1", api_key: str = "dummy"):
        self.model_name = model_name
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def generate(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.1) -> InferenceResponse:
        """Generate response using OpenAI-compatible API"""
        try:
            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            tokens_used = result.get("usage", {}).get("total_tokens")
            
            return InferenceResponse(
                content=content,
                model=self.model_name,
                tokens_used=tokens_used,
                success=True
            )
            
        except Exception as e:
            return InferenceResponse(
                content="",
                model=self.model_name,
                success=False,
                error=str(e)
            )
    
    def is_available(self) -> bool:
        """Check if the API is available"""
        try:
            response = requests.get(f"{self.base_url}/models", headers=self.headers, timeout=5)
            return response.status_code == 200
        except:
            return False


class LlamaCppClient(LocalInferenceClient):
    """Client for llama.cpp server (OpenAI-compatible API with better AMD GPU support)"""
    
    def __init__(self, model_name: str = "llama-3.1-8b", base_url: str = "http://localhost:8080/v1", api_key: str = "dummy"):
        self.model_name = model_name
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def generate(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.1) -> InferenceResponse:
        """Generate response using llama.cpp server"""
        try:
            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            tokens_used = result.get("usage", {}).get("total_tokens")
            
            return InferenceResponse(
                content=content,
                model=self.model_name,
                tokens_used=tokens_used,
                success=True
            )
            
        except Exception as e:
            return InferenceResponse(
                content="",
                model=self.model_name,
                success=False,
                error=str(e)
            )
    
    def is_available(self) -> bool:
        """Check if llama.cpp server is available"""
        try:
            # Try the health endpoint first
            response = requests.get(f"{self.base_url.replace('/v1', '')}/health", timeout=5)
            if response.status_code == 200:
                return True
            # Fallback to models endpoint
            response = requests.get(f"{self.base_url}/models", headers=self.headers, timeout=5)
            return response.status_code == 200
        except:
            return False


class LlamaCppPythonClient(LocalInferenceClient):
    """Client for llama-cpp-python library (Python bindings, no server needed)"""
    
    def __init__(self, model_path: str, n_gpu_layers: int = 50, n_ctx: int = 4096):
        """
        Initialize llama-cpp-python client
        
        Args:
            model_path: Path to the GGUF model file
            n_gpu_layers: Number of layers to offload to GPU (-1 for all)
            n_ctx: Context window size
        """
        self.model_path = model_path
        self.n_gpu_layers = n_gpu_layers
        self.n_ctx = n_ctx
        self._llm = None
        self._load_model()
    
    def _load_model(self):
        """Load the model using llama-cpp-python"""
        try:
            from llama_cpp import Llama
            self._llm = Llama(
                model_path=self.model_path,
                n_gpu_layers=self.n_gpu_layers,
                n_ctx=self.n_ctx,
                verbose=False
            )
        except Exception as e:
            print(f"Failed to load model from {self.model_path}: {e}")
    
    def generate(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.1) -> InferenceResponse:
        """Generate response using llama-cpp-python"""
        if not self._llm:
            return InferenceResponse(
                content="",
                model=self.model_path,
                success=False,
                error="Model not loaded"
            )
        
        try:
            result = self._llm.create_chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            content = result["choices"][0]["message"]["content"]
            tokens_used = result.get("usage", {}).get("total_tokens")
            
            return InferenceResponse(
                content=content,
                model=self.model_path,
                tokens_used=tokens_used,
                success=True
            )
            
        except Exception as e:
            return InferenceResponse(
                content="",
                model=self.model_path,
                success=False,
                error=str(e)
            )
    
    def is_available(self) -> bool:
        """Check if the model is loaded"""
        return self._llm is not None


class TransformersClient(LocalInferenceClient):
    """Client for Hugging Face Transformers local inference"""
    
    def __init__(self, model_name: str = "microsoft/DialoGPT-medium"):
        self.model_name = model_name
        self._pipeline = None
        self._load_model()
    
    def _load_model(self):
        """Load the transformers model"""
        try:
            from transformers import pipeline
            self._pipeline = pipeline(
                "text-generation",
                model=self.model_name,
                device_map="auto" if self._has_gpu() else "cpu"
            )
        except Exception as e:
            print(f"Failed to load model {self.model_name}: {e}")
    
    def _has_gpu(self) -> bool:
        """Check if GPU is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except:
            return False
    
    def generate(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.1) -> InferenceResponse:
        """Generate response using Transformers"""
        if not self._pipeline:
            return InferenceResponse(
                content="",
                model=self.model_name,
                success=False,
                error="Model not loaded"
            )
        
        try:
            result = self._pipeline(
                prompt,
                max_length=len(prompt.split()) + max_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                pad_token_id=self._pipeline.tokenizer.eos_token_id
            )
            
            content = result[0]["generated_text"][len(prompt):].strip()
            
            return InferenceResponse(
                content=content,
                model=self.model_name,
                success=True
            )
            
        except Exception as e:
            return InferenceResponse(
                content="",
                model=self.model_name,
                success=False,
                error=str(e)
            )
    
    def is_available(self) -> bool:
        """Check if the model is loaded"""
        return self._pipeline is not None


class InferenceClientFactory:
    """Factory for creating local inference clients"""
    
    @staticmethod
    def create_client(
        backend_type: str,
        model_name: str,
        **kwargs
    ) -> LocalInferenceClient:
        """
        Create a local inference client
        
        Args:
            backend_type: Type of backend ('llamacpp', 'llamacpp_python', 'openai_compatible', 'transformers')
            model_name: Name of the model to use
            **kwargs: Additional arguments for the specific client
        
        Returns:
            LocalInferenceClient instance
        """
        if backend_type == "llamacpp":
            return LlamaCppClient(
                model_name=model_name,
                base_url=kwargs.get("base_url", "http://localhost:8080/v1"),
                api_key=kwargs.get("api_key", "dummy")
            )
        elif backend_type == "llamacpp_python":
            return LlamaCppPythonClient(
                model_path=kwargs.get("model_path", model_name),
                n_gpu_layers=kwargs.get("n_gpu_layers", 50),
                n_ctx=kwargs.get("n_ctx", 4096)
            )
        elif backend_type == "openai_compatible":
            return OpenAICompatibleClient(
                model_name=model_name,
                base_url=kwargs.get("base_url", "http://localhost:8000/v1"),
                api_key=kwargs.get("api_key", "dummy")
            )
        elif backend_type == "transformers":
            return TransformersClient(model_name=model_name)
        else:
            raise ValueError(f"Unsupported backend type: {backend_type}")
    
    @staticmethod
    def auto_detect_available() -> Optional[LocalInferenceClient]:
        """Auto-detect and return the first available local inference client"""
        
        # Try llama.cpp server first (best for AMD GPUs)
        llamacpp_client = LlamaCppClient()
        if llamacpp_client.is_available():
            return llamacpp_client
        
        # Try vLLM/LocalAI (OpenAI-compatible)
        openai_client = OpenAICompatibleClient()
        if openai_client.is_available():
            return openai_client
        
        # Fall back to transformers (always available if installed)
        try:
            transformers_client = TransformersClient()
            if transformers_client.is_available():
                return transformers_client
        except:
            pass
        
        return None