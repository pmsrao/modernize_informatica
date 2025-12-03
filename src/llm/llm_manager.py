"""LLM Manager — Selects between OpenAI, Azure, or Local fallback with retry and caching"""
import os
import hashlib
import json
from functools import lru_cache
from typing import Optional, Dict
from llm.openai_client import OpenAIClient
from llm.azure_openai_client import AzureOpenAIClient
from llm.local_llm_client import LocalLLMClient
from utils.logger import get_logger
from config import settings

logger = get_logger(__name__)


class LLMManager:
    """Manages LLM client selection and provides unified interface with caching."""
    
    def __init__(self, provider: Optional[str] = None, enable_cache: bool = True):
        """Initialize LLM Manager.
        
        Args:
            provider: LLM provider to use (openai, azure, local). Defaults to settings.
            enable_cache: Whether to enable response caching
        """
        provider = provider or settings.llm_provider or os.getenv("LLM_PROVIDER", "openai")
        self.enable_cache = enable_cache
        self._cache: Dict[str, str] = {}
        
        logger.info(f"Initializing LLM Manager with provider: {provider}")
        
        if provider == "azure":
            try:
                self.client = AzureOpenAIClient()
                logger.info("Azure OpenAI client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Azure OpenAI client: {str(e)}, falling back to OpenAI")
                self.client = OpenAIClient()
        elif provider == "local":
            try:
                self.client = LocalLLMClient()
                logger.info("Local LLM client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Local LLM client: {str(e)}, falling back to OpenAI")
                try:
                    self.client = OpenAIClient()
                    logger.info("OpenAI client initialized successfully (fallback)")
                except Exception as e2:
                    logger.error(f"Failed to initialize OpenAI client (fallback): {str(e2)}")
                    raise
        else:
            # Default: try OpenAI first, fall back to local if it fails
            try:
                self.client = OpenAIClient()
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {str(e)}, falling back to local LLM")
                try:
                    self.client = LocalLLMClient()
                    logger.info("Local LLM client initialized successfully (fallback)")
                except Exception as e2:
                    logger.error(f"Failed to initialize Local LLM client (fallback): {str(e2)}")
                    raise

    def ask(self, prompt: str, use_cache: bool = True) -> str:
        """Send prompt to LLM and return response with optional caching.
        
        Args:
            prompt: The prompt to send
            use_cache: Whether to use cache for this request
            
        Returns:
            Response text from the model
        """
        # Check cache if enabled
        if self.enable_cache and use_cache:
            cache_key = self._get_cache_key(prompt)
            if cache_key in self._cache:
                logger.debug("Returning cached LLM response")
                return self._cache[cache_key]
        
        # Call LLM
        try:
            logger.debug("Sending prompt to LLM")
            response = self.client.ask(prompt)
            
            # Cache response if enabled
            if self.enable_cache and use_cache:
                cache_key = self._get_cache_key(prompt)
                self._cache[cache_key] = response
                logger.debug("Cached LLM response")
            
            return response
            
        except Exception as e:
            logger.error(f"LLM request failed: {str(e)}")
            raise

    def generate(self, prompt: str, max_tokens: Optional[int] = None, use_cache: bool = True) -> str:
        """Generate response from LLM (alias for ask with max_tokens parameter).
        
        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens (ignored for now, kept for API compatibility)
            use_cache: Whether to use cache for this request
            
        Returns:
            Response text from the model
        """
        # max_tokens is ignored for now as it's provider-specific
        # In the future, this could be passed to the client if needed
        return self.ask(prompt, use_cache=use_cache)

    def _get_cache_key(self, prompt: str) -> str:
        """Generate cache key for prompt.
        
        Args:
            prompt: The prompt
            
        Returns:
            Cache key (hash of prompt)
        """
        return hashlib.md5(prompt.encode()).hexdigest()

    def clear_cache(self):
        """Clear the response cache."""
        self._cache.clear()
        logger.info("LLM response cache cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            "cached_responses": len(self._cache),
            "cache_enabled": self.enable_cache
        }
