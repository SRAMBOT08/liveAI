"""
OpenAI GenAI Provider
Implements GPT-based explanation generation
"""
from typing import Optional
import openai
from .base import BaseGenAIProvider


class OpenAIProvider(BaseGenAIProvider):
    """
    OpenAI GPT provider for risk event explanations
    
    API Documentation: https://platform.openai.com/docs/api-reference
    """
    
    def _validate_config(self, **kwargs) -> None:
        """Validate OpenAI API key and model"""
        self.api_key = kwargs.get("api_key", "")
        self.model = kwargs.get("model", "gpt-4")
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # Initialize OpenAI client
        openai.api_key = self.api_key
        self.is_initialized = True
    
    def generate_explanation(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 300
    ) -> Optional[str]:
        """
        Generate explanation using GPT
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum response length
        
        Returns:
            Generated text or None if failed
        """
        try:
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(self.format_error_message(e))
            return None
    
    def health_check(self) -> bool:
        """
        Check if OpenAI API is accessible
        
        Returns:
            True if operational, False otherwise
        """
        try:
            # Simple test request
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return True
            
        except Exception:
            return False
