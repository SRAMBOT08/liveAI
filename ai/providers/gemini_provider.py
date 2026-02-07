"""
Google Gemini GenAI Provider
Implements Gemini-based explanation generation
"""
from typing import Optional
import google.generativeai as genai
from .base import BaseGenAIProvider


class GeminiProvider(BaseGenAIProvider):
    """
    Google Gemini provider for risk event explanations
    
    API Documentation: https://ai.google.dev/docs
    """
    
    def _validate_config(self, **kwargs) -> None:
        """Validate Gemini API key and model"""
        self.api_key = kwargs.get("api_key", "")
        self.model_name = kwargs.get("model", "gemini-1.5-pro")
        
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
        self.is_initialized = True
    
    def generate_explanation(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 300
    ) -> Optional[str]:
        """
        Generate explanation using Gemini
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt (prepended to prompt)
            temperature: Sampling temperature
            max_tokens: Maximum response length
        
        Returns:
            Generated text or None if failed
        """
        try:
            # Gemini combines system and user prompts
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Configure generation
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            return response.text.strip()
            
        except Exception as e:
            print(self.format_error_message(e))
            return None
    
    def health_check(self) -> bool:
        """
        Check if Gemini API is accessible
        
        Returns:
            True if operational, False otherwise
        """
        try:
            # Simple test request
            response = self.model.generate_content(
                "test",
                generation_config=genai.types.GenerationConfig(max_output_tokens=5)
            )
            return True
            
        except Exception:
            return False
