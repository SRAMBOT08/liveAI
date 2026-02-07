"""
Grok (xAI) GenAI Provider
Implements Grok-based explanation generation
"""
from typing import Optional
import requests
from .base import BaseGenAIProvider


class GrokProvider(BaseGenAIProvider):
    """
    xAI Grok provider for risk event explanations
    
    API Documentation: https://docs.x.ai/
    """
    
    def _validate_config(self, **kwargs) -> None:
        """Validate Grok API key and endpoint"""
        self.api_key = kwargs.get("api_key", "")
        self.api_base = kwargs.get("api_base", "https://api.x.ai/v1")
        self.model = kwargs.get("model", "grok-beta")
        
        if not self.api_key:
            raise ValueError("Grok API key is required")
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
        self.is_initialized = True
    
    def generate_explanation(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 300
    ) -> Optional[str]:
        """
        Generate explanation using Grok
        
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
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = self.session.post(
                f"{self.api_base}/chat/completions",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                print(f"Grok API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(self.format_error_message(e))
            return None
    
    def health_check(self) -> bool:
        """
        Check if Grok API is accessible
        
        Returns:
            True if operational, False otherwise
        """
        try:
            # Simple test request
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 5
            }
            
            response = self.session.post(
                f"{self.api_base}/chat/completions",
                json=payload,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception:
            return False
