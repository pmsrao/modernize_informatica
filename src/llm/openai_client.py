"""OpenAI Client Wrapper — Production Style
Uses current OpenAI API (not deprecated).
"""
import os
from typing import Optional
from openai import OpenAI
from utils.exceptions import ModernizationError


class OpenAIClient:
    """OpenAI client using current API."""
    
    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None):
        """Initialize OpenAI client.
        
        Args:
            model: Model name to use (default: gpt-4o-mini)
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ModernizationError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def ask(self, prompt: str) -> str:
        """Send prompt to OpenAI and return response.
        
        Args:
            prompt: The prompt to send
            
        Returns:
            Response text from the model
            
        Raises:
            ModernizationError: If API call fails
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            raise ModernizationError(f"OpenAI API call failed: {str(e)}") from e
