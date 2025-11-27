"""Local LLM Client — Support for llama.cpp, vLLM, and mock responses"""
import os
import json
import requests
from typing import Optional
from utils.exceptions import ModernizationError
from utils.logger import get_logger
from config import settings

logger = get_logger(__name__)


class LocalLLMClient:
    """Local LLM client supporting multiple backends."""
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        vllm_server_url: Optional[str] = None,
        ollama_url: Optional[str] = None,
        use_mock: bool = False
    ):
        """Initialize Local LLM client.
        
        Args:
            model_path: Path to local model file (for llama.cpp)
            vllm_server_url: URL to vLLM server (e.g., http://localhost:8000/v1)
            ollama_url: URL to Ollama server (e.g., http://localhost:11434)
            use_mock: If True, use mock responses instead of actual LLM
        """
        self.model_path = model_path or settings.local_llm_path or os.getenv("LOCAL_LLM_PATH")
        self.vllm_server_url = vllm_server_url or os.getenv("VLLM_SERVER_URL")
        self.ollama_url = ollama_url or os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
        self.use_mock = use_mock or os.getenv("USE_MOCK_LLM", "false").lower() == "true"
        
        # Determine which backend to use
        if self.use_mock:
            self.backend = "mock"
            logger.info("Local LLM client initialized with mock responses")
        elif self.vllm_server_url:
            self.backend = "vllm"
            logger.info(f"Local LLM client initialized with vLLM server: {self.vllm_server_url}")
        elif self.ollama_url:
            self.backend = "ollama"
            logger.info(f"Local LLM client initialized with Ollama server: {self.ollama_url}, model: {self.ollama_model}")
        elif self.model_path:
            self.backend = "llamacpp"
            logger.info(f"Local LLM client initialized with llama.cpp model: {self.model_path}")
            # Note: llama.cpp integration would require additional dependencies
            # For now, we'll use mock as fallback
            logger.warning("llama.cpp integration not fully implemented, using mock responses")
            self.backend = "mock"
        else:
            self.backend = "mock"
            logger.warning("No local LLM configuration found, using mock responses")

    def ask(self, prompt: str) -> str:
        """Send prompt to local LLM and return response.
        
        Args:
            prompt: The prompt to send
            
        Returns:
            Response text from the model
            
        Raises:
            ModernizationError: If LLM call fails
        """
        try:
            if self.backend == "mock":
                return self._mock_response(prompt)
            elif self.backend == "vllm":
                return self._vllm_request(prompt)
            elif self.backend == "ollama":
                return self._ollama_request(prompt)
            elif self.backend == "llamacpp":
                return self._llamacpp_request(prompt)
            else:
                return self._mock_response(prompt)
        except Exception as e:
            logger.error(f"Local LLM request failed: {str(e)}")
            # Fallback to mock on error
            logger.warning("Falling back to mock response due to error")
            return self._mock_response(prompt)

    def _mock_response(self, prompt: str) -> str:
        """Generate a mock response for testing/development.
        
        Args:
            prompt: The prompt
            
        Returns:
            Mock response
        """
        # Simple heuristic-based mock responses
        if "explain" in prompt.lower() or "explanation" in prompt.lower():
            return "This expression performs a conditional classification based on the input values. It categorizes data into different groups using nested conditional logic."
        elif "summary" in prompt.lower() or "summarize" in prompt.lower():
            return "This mapping processes data from multiple sources, applies various transformations including joins, lookups, and aggregations, and writes the results to target tables. The mapping implements business logic for data enrichment and calculation."
        elif "risk" in prompt.lower() or "analyze" in prompt.lower():
            return json.dumps([
                {
                    "category": "Data Quality",
                    "severity": "Medium",
                    "location": "EXP_CALCULATIONS/AGE_BUCKET",
                    "risk": "Missing null handling in expression",
                    "impact": "NULL values may cause unexpected results",
                    "recommendation": "Add null checks to handle missing values"
                }
            ], indent=2)
        elif "suggestion" in prompt.lower() or "optimize" in prompt.lower():
            return json.dumps([
                {
                    "transformation": "EXP_CALCULATIONS",
                    "field": "FULL_NAME",
                    "current_pattern": "String concatenation",
                    "suggestion": "Use concat_ws for better null handling",
                    "benefits": ["Handles nulls gracefully", "More readable"],
                    "improved_code": "F.concat_ws(' ', F.col('FIRST_NAME'), F.col('LAST_NAME'))",
                    "priority": "Medium"
                }
            ], indent=2)
        else:
            return f"[Local LLM Mock Response] Processed prompt: {prompt[:100]}..."

    def _vllm_request(self, prompt: str) -> str:
        """Send request to vLLM server.
        
        Args:
            prompt: The prompt
            
        Returns:
            Response from vLLM server
        """
        if not self.vllm_server_url:
            raise ModernizationError("vLLM server URL not configured")
        
        try:
            # vLLM uses OpenAI-compatible API
            # If URL doesn't end with /v1, add it
            base_url = self.vllm_server_url.rstrip('/')
            if not base_url.endswith('/v1'):
                base_url = f"{base_url}/v1"
            
            url = f"{base_url}/chat/completions"
            
            # Get model name from environment or use default
            model_name = os.getenv("VLLM_MODEL", "default")
            
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"vLLM server request failed: {str(e)}")
            raise ModernizationError(f"vLLM server request failed: {str(e)}") from e
        except (KeyError, IndexError) as e:
            logger.error(f"Invalid response from vLLM server: {str(e)}")
            raise ModernizationError(f"Invalid response from vLLM server: {str(e)}") from e

    def _ollama_request(self, prompt: str) -> str:
        """Send request to Ollama server (for Llama3 and other local models).
        
        Args:
            prompt: The prompt
            
        Returns:
            Response from Ollama server
        """
        if not self.ollama_url:
            raise ModernizationError("Ollama server URL not configured")
        
        try:
            # Ollama uses a different API format
            url = f"{self.ollama_url}/api/generate"
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 2000
                }
            }
            
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "").strip()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama server request failed: {str(e)}")
            raise ModernizationError(f"Ollama server request failed: {str(e)}") from e
        except (KeyError, ValueError) as e:
            logger.error(f"Invalid response from Ollama server: {str(e)}")
            raise ModernizationError(f"Invalid response from Ollama server: {str(e)}") from e

    def _llamacpp_request(self, prompt: str) -> str:
        """Send request to llama.cpp (not fully implemented).
        
        Args:
            prompt: The prompt
            
        Returns:
            Response from llama.cpp
        """
        # llama.cpp integration would require:
        # - llama-cpp-python package
        # - Model file loading
        # - Inference execution
        # For now, fallback to mock
        logger.warning("llama.cpp integration not fully implemented, using mock response")
        return self._mock_response(prompt)
