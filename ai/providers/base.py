"""
Base GenAI Provider Interface
All GenAI providers must implement this interface
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict


class BaseGenAIProvider(ABC):
    """
    Abstract base class for all GenAI providers
    
    Design principles:
    1. All providers implement the same interface
    2. Providers handle their own authentication
    3. Providers handle their own error recovery
    4. Providers never store state (stateless)
    """
    
    def __init__(self, **kwargs):
        """
        Initialize provider
        
        Args:
            **kwargs: Provider-specific configuration
        """
        self.is_initialized = False
        self._validate_config(**kwargs)
    
    @abstractmethod
    def _validate_config(self, **kwargs) -> None:
        """
        Validate provider-specific configuration
        Raise ValueError if configuration is invalid
        """
        pass
    
    @abstractmethod
    def generate_explanation(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 300
    ) -> Optional[str]:
        """
        Generate explanation from prompt
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 = deterministic)
            max_tokens: Maximum response length
        
        Returns:
            Generated text or None if failed
        """
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if provider is operational
        
        Returns:
            True if operational, False otherwise
        """
        pass
    
    def get_provider_info(self) -> Dict:
        """
        Return provider metadata
        
        Returns:
            Dictionary with provider information
        """
        return {
            "provider": self.__class__.__name__,
            "initialized": self.is_initialized
        }
    
    def format_error_message(self, error: Exception) -> str:
        """
        Format error message for logging
        
        Args:
            error: Exception that occurred
        
        Returns:
            Formatted error string
        """
        return f"{self.__class__.__name__} error: {str(error)}"
