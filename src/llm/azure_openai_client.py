"""Azure OpenAI Client Wrapper — Production Style"""
import os
import time
from typing import Optional
from openai import AzureOpenAI
from openai import APIError, APIConnectionError, APITimeoutError
from utils.exceptions import ModernizationError
from utils.logger import get_logger
from config import settings

logger = get_logger(__name__)


class AzureOpenAIClient:
    """Azure OpenAI client with retry logic and error handling."""
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        deployment: Optional[str] = None,
        api_version: str = "2024-02-01"
    ):
        """Initialize Azure OpenAI client.
        
        Args:
            endpoint: Azure OpenAI endpoint URL
            api_key: Azure OpenAI API key
            deployment: Deployment name (model deployment)
            api_version: API version to use
        """
        endpoint = endpoint or settings.azure_openai_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = api_key or settings.azure_openai_key or os.getenv("AZURE_OPENAI_KEY")
        deployment = deployment or settings.azure_openai_deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
        
        if not endpoint:
            raise ModernizationError(
                "Azure OpenAI endpoint not found. Set AZURE_OPENAI_ENDPOINT environment variable or configure in settings."
            )
        if not api_key:
            raise ModernizationError(
                "Azure OpenAI API key not found. Set AZURE_OPENAI_KEY environment variable or configure in settings."
            )
        
        try:
            self.client = AzureOpenAI(
                api_key=api_key,
                azure_endpoint=endpoint,
                api_version=api_version
            )
            self.deployment = deployment
            self.api_version = api_version
            logger.info(f"Azure OpenAI client initialized with deployment: {deployment}")
        except Exception as e:
            raise ModernizationError(f"Failed to initialize Azure OpenAI client: {str(e)}") from e

    def ask(self, prompt: str, max_retries: int = 3, initial_delay: float = 1.0) -> str:
        """Send prompt to Azure OpenAI and return response with retry logic.
        
        Args:
            prompt: The prompt to send
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay before retry (seconds)
            
        Returns:
            Response text from the model
            
        Raises:
            ModernizationError: If API call fails after retries
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.deployment,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=2000
                )
                logger.debug(f"Azure OpenAI API call successful (attempt {attempt + 1})")
                return response.choices[0].message.content
                
            except APITimeoutError as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = initial_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Azure OpenAI API timeout (attempt {attempt + 1}/{max_retries}), retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"Azure OpenAI API timeout after {max_retries} attempts")
                    
            except APIConnectionError as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = initial_delay * (2 ** attempt)
                    logger.warning(f"Azure OpenAI connection error (attempt {attempt + 1}/{max_retries}), retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"Azure OpenAI connection error after {max_retries} attempts")
                    
            except APIError as e:
                # Don't retry on API errors (authentication, rate limits, etc.)
                logger.error(f"Azure OpenAI API error: {str(e)}")
                raise ModernizationError(f"Azure OpenAI API error: {str(e)}") from e
                
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = initial_delay * (2 ** attempt)
                    logger.warning(f"Azure OpenAI unexpected error (attempt {attempt + 1}/{max_retries}), retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"Azure OpenAI unexpected error after {max_retries} attempts")
        
        # If we get here, all retries failed
        raise ModernizationError(
            f"Azure OpenAI API call failed after {max_retries} attempts: {str(last_exception)}"
        ) from last_exception
