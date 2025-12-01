#!/usr/bin/env python3
"""
Test script to verify both local llama.cpp and Anthropic API modes work correctly

This script checks for common configuration issues and validates the setup.
"""

import os
import sys


def check_local_llamacpp():
    """Test local llama-cpp-python configuration"""
    print("\n" + "="*60)
    print("TESTING LOCAL LLAMA-CPP-PYTHON MODE")
    print("="*60)
    
    # Check environment variables
    backend = os.getenv("INFERENCE_BACKEND", "llamacpp_python")
    model_name = os.getenv("MODEL_NAME", "llama-3.1-8b-instruct")
    model_path = os.getenv("MODEL_PATH")
    n_gpu_layers = os.getenv("N_GPU_LAYERS", "50")
    
    print(f"Backend: {backend}")
    print(f"Model: {model_name}")
    
    if backend == "llamacpp_python":
        print("\n✓ Configured for llama-cpp-python mode")
        print(f"  Model path: {model_path}")
        print(f"  GPU layers: {n_gpu_layers}")
        
        if not model_path:
            print("  ✗ MODEL_PATH not set!")
            print("  Set with: set MODEL_PATH=path/to/model.gguf")
        elif not os.path.exists(model_path):
            print(f"  ✗ Model file not found: {model_path}")
        else:
            print(f"  ✓ Model file exists")
            
        # Test import
        try:
            import llama_cpp
            print("  ✓ llama-cpp-python is installed")
        except ImportError:
            print("  ✗ llama-cpp-python not installed")
            print("  Install with: pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124")
    else:
        print(f"\n○ Backend is '{backend}' (not llamacpp_python)")


def check_anthropic():
    """Test Anthropic API configuration"""
    print("\n" + "="*60)
    print("TESTING ANTHROPIC API MODE")
    print("="*60)
    
    backend = os.getenv("INFERENCE_BACKEND")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if backend == "anthropic":
        print("✓ Backend set to 'anthropic'")
    else:
        print(f"Backend: {backend} (set INFERENCE_BACKEND=anthropic to use Anthropic)")
    
    if api_key:
        # Mask the key for security
        masked_key = api_key[:10] + "..." + api_key[-4:] if len(api_key) > 14 else "***"
        print(f"✓ API key set: {masked_key}")
        
        # Test import
        try:
            import anthropic
            print("✓ anthropic library is installed")
            
            # Test API call
            print("\nTesting API connection...")
            client = anthropic.Anthropic(api_key=api_key)
            try:
                response = client.messages.create(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=10,
                    messages=[{"role": "user", "content": "Hi"}]
                )
                print("✓ API is working! Response:", response.content[0].text[:50])
            except Exception as e:
                print(f"✗ API call failed: {e}")
                
        except ImportError:
            print("✗ anthropic library not installed")
            print("  Install with: pip install anthropic")
    else:
        print("✗ ANTHROPIC_API_KEY not set")
        print("  Set with: set ANTHROPIC_API_KEY=sk-ant-...")


def check_dependencies():
    """Check required dependencies"""
    print("\n" + "="*60)
    print("CHECKING DEPENDENCIES")
    print("="*60)
    
    required = {
        "pandas": "Data processing",
        "beautifulsoup4": "Web scraping",
        "requests": "HTTP requests",
        "tqdm": "Progress bars"
    }
    
    for package, purpose in required.items():
        try:
            __import__(package if package != "beautifulsoup4" else "bs4")
            print(f"✓ {package:20s} - {purpose}")
        except ImportError:
            print(f"✗ {package:20s} - {purpose} (MISSING)")
    
    optional = {
        "anthropic": "Anthropic API (for cloud mode)",
        "llama_cpp": "llama-cpp-python (for local mode)",
        "selenium": "Selenium scraping (Facebook/Mercari)"
    }
    
    print("\nOptional:")
    for package, purpose in optional.items():
        try:
            __import__(package.replace("-", "_"))
            print(f"✓ {package:20s} - {purpose}")
        except ImportError:
            print(f"○ {package:20s} - {purpose} (optional)")


def check_config():
    """Check configuration"""
    print("\n" + "="*60)
    print("CURRENT CONFIGURATION")
    print("="*60)
    
    try:
        from claim_assist.config import Config
        config = Config.from_env()
        
        print(f"Backend:              {config.inference_backend}")
        print(f"Model:                {config.model_name}")
        
        if config.inference_backend == "llamacpp_python":
            print(f"Model path:           {config.model_path}")
            print(f"GPU layers:           {config.n_gpu_layers}")
            print(f"Context size:         {config.n_ctx}")
        elif config.inference_backend == "anthropic":
            print(f"API key set:          {'Yes' if config.anthropic_api_key else 'No'}")
        
        print(f"\nWeb Scraping:")
        print(f"  Delay:              {config.scraping_delay}s")
        print(f"  Max results:        {config.max_results_per_source}")
        print(f"  Selenium enabled:   {config.enable_selenium_scraping}")
        
        print(f"\nProcessing:")
        print(f"  Value threshold:    ${config.value_threshold}")
        print(f"  Cache enabled:      {config.enable_cache}")
        
        # Try to validate
        try:
            config.validate()
            print("\n✓ Configuration is valid!")
        except ValueError as e:
            print(f"\n✗ Configuration error: {e}")
            
    except Exception as e:
        print(f"✗ Error loading config: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all checks"""
    print("\n" + "🔍 CLAIM-ASSIST CONFIGURATION CHECKER")
    print("="*60)
    
    check_dependencies()
    check_config()
    check_local_llamacpp()
    check_anthropic()
    
    print("\n" + "="*60)
    print("SETUP RECOMMENDATIONS")
    print("="*60)
    
    backend = os.getenv("INFERENCE_BACKEND", "llamacpp_python")
    
    if backend == "llamacpp_python":
        print("""
For llama-cpp-python mode (Recommended):
1. Install: pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124
2. Download model from HuggingFace
3. Set MODEL_PATH: set MODEL_PATH=path/to/model.gguf
4. Set GPU layers: set N_GPU_LAYERS=50 (or -1 for all layers)
5. Run: python -m claim_assist.main example_claims.csv

See COLAB_QUICKSTART.md for detailed instructions.
""")
    
    elif backend == "anthropic":
        print("""
For Anthropic API mode:
1. Get API key from https://console.anthropic.com/
2. Install: pip install anthropic
3. Set key: set ANTHROPIC_API_KEY=sk-ant-...
4. Run: python -m claim_assist.main example_claims.csv --inference-backend anthropic
""")
    
    print("\n✅ Checker complete!\n")


if __name__ == "__main__":
    main()
