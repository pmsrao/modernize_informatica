#!/usr/bin/env python3
"""Test LLM configuration and connectivity."""
import sys
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

from llm.llm_manager import LLMManager
from utils.logger import get_logger

logger = get_logger(__name__)


def test_llm_configuration():
    """Test LLM configuration and connectivity."""
    print("=" * 80)
    print("LLM Configuration Test")
    print("=" * 80)
    print()
    
    try:
        # Initialize LLM Manager
        print("1. Initializing LLM Manager...")
        llm = LLMManager()
        provider_name = llm.client.__class__.__name__
        print(f"   ✅ LLM Manager initialized")
        print(f"   Provider: {provider_name}")
        print()
        
        # Test simple prompt
        print("2. Testing LLM with simple prompt...")
        test_prompt = "Say 'Hello, LLM is working!' in exactly one sentence. Do not add any explanation."
        print(f"   Prompt: {test_prompt}")
        print("   Sending request...")
        
        response = llm.ask(test_prompt)
        
        print(f"   ✅ LLM responded successfully!")
        print(f"   Response: {response}")
        print()
        
        # Test with a more complex prompt (expression explanation)
        print("3. Testing expression explanation...")
        expr_prompt = "Explain this Informatica expression in simple terms: IIF(AGE < 30, 'YOUNG', 'OTHER')"
        print(f"   Prompt: {expr_prompt[:60]}...")
        
        expr_response = llm.ask(expr_prompt)
        print(f"   ✅ Expression explanation received")
        print(f"   Response: {expr_response[:200]}...")
        print()
        
        print("=" * 80)
        print("✅ All tests passed! LLM is configured correctly.")
        print("=" * 80)
        return True
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ Test failed!")
        print("=" * 80)
        print(f"Error: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check your environment variables:")
        print("   - For OpenAI: export OPENAI_API_KEY=sk-...")
        print("   - For Azure: export AZURE_OPENAI_ENDPOINT=...")
        print("   - For Local: export OLLAMA_URL=http://localhost:11434")
        print()
        print("2. Verify LLM service is running:")
        print("   - OpenAI: Check API key is valid")
        print("   - Azure: Check endpoint and key")
        print("   - Ollama: Run 'ollama serve' and 'ollama pull llama3'")
        print()
        print("3. See detailed configuration guide:")
        print("   docs/guides/llm_configuration.md")
        print()
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_llm_configuration()
    sys.exit(0 if success else 1)

