"""
Risk Event Explainer
Event-driven GenAI explanation generation
"""
from typing import Optional, List, Dict
from datetime import datetime

from config.settings import config, GenAIProvider
from .prompts import SYSTEM_PROMPT, create_risk_event_prompt, create_risk_summary_prompt
from .providers import (
    BaseGenAIProvider,
    OpenAIProvider,
    GeminiProvider,
    GrokProvider
)


class RiskExplainer:
    """
    Manages GenAI provider selection and explanation generation
    
    Responsibilities:
    1. Instantiate correct GenAI provider
    2. Handle provider failover
    3. Generate event-driven explanations
    4. Implement context-grounded RAG (no vector DB needed)
    
    Design: Event-driven, not continuous
    """
    
    def __init__(self):
        self.provider: Optional[BaseGenAIProvider] = None
        self.explanation_count = 0
        self.error_count = 0
        
        # In-memory context store (simple RAG)
        self.metrics_history: List[Dict] = []
        self.max_history_size = 50
    
    def initialize(self) -> bool:
        """
        Initialize GenAI provider
        
        Returns:
            True if successful, False otherwise
        """
        try:
            success = self._initialize_provider(config.genai_provider)
            
            if success:
                print(f"RiskExplainer initialized with {config.genai_provider.value} provider")
            
            return success
            
        except Exception as e:
            print(f"RiskExplainer initialization error: {e}")
            return False
    
    def _initialize_provider(self, provider_type: GenAIProvider) -> bool:
        """
        Initialize specific GenAI provider
        
        Args:
            provider_type: Provider to initialize
        
        Returns:
            True if successful, False otherwise
        """
        try:
            genai_config = config.genai_providers
            
            if provider_type == GenAIProvider.OPENAI:
                self.provider = OpenAIProvider(
                    api_key=genai_config.openai_api_key,
                    model=genai_config.openai_model
                )
            
            elif provider_type == GenAIProvider.GEMINI:
                self.provider = GeminiProvider(
                    api_key=genai_config.gemini_api_key,
                    model=genai_config.gemini_model
                )
            
            elif provider_type == GenAIProvider.GROK:
                self.provider = GrokProvider(
                    api_key=genai_config.grok_api_key,
                    api_base=genai_config.grok_api_base,
                    model=genai_config.grok_model
                )
            
            else:
                print(f"Unknown GenAI provider: {provider_type}")
                return False
            
            return self.provider.is_initialized
            
        except Exception as e:
            print(f"GenAI provider initialization error: {e}")
            return False
    
    def switch_provider(self, new_provider: GenAIProvider) -> bool:
        """
        Switch to a different GenAI provider
        
        Args:
            new_provider: New provider to use
        
        Returns:
            True if successful, False otherwise
        """
        success = self._initialize_provider(new_provider)
        
        if success:
            print(f"Switched to {new_provider.value} provider")
        
        return success
    
    def add_context(self, metrics: Dict) -> None:
        """
        Add current metrics to context history (RAG store)
        
        Args:
            metrics: Current risk metrics
        """
        self.metrics_history.append(metrics)
        
        # Trim history
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size:]
    
    def explain_event(self, event: Dict, current_metrics: Dict) -> Optional[str]:
        """
        Generate explanation for a risk event
        
        Args:
            event: Risk event dictionary
            current_metrics: Current risk metrics
        
        Returns:
            Explanation text or None if failed
        """
        if not self.provider:
            print("GenAI provider not initialized")
            return None
        
        try:
            # Get recent context for RAG
            recent_context = self.metrics_history[-10:]  # Last 10 metrics
            
            # Create prompt
            prompt = create_risk_event_prompt(event, current_metrics, recent_context)
            
            # Generate explanation
            explanation = self.provider.generate_explanation(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=config.genai_providers.temperature,
                max_tokens=config.genai_providers.max_tokens
            )
            
            if explanation:
                self.explanation_count += 1
                return explanation
            else:
                self.error_count += 1
                return None
                
        except Exception as e:
            print(f"Event explanation error: {e}")
            self.error_count += 1
            return None
    
    def generate_risk_summary(self, current_metrics: Dict) -> Optional[str]:
        """
        Generate overall risk summary
        
        Args:
            current_metrics: Current risk metrics
        
        Returns:
            Summary text or None if failed
        """
        if not self.provider:
            print("GenAI provider not initialized")
            return None
        
        try:
            # Create prompt
            prompt = create_risk_summary_prompt(current_metrics)
            
            # Generate summary
            summary = self.provider.generate_explanation(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=config.genai_providers.temperature,
                max_tokens=config.genai_providers.max_tokens
            )
            
            if summary:
                self.explanation_count += 1
                return summary
            else:
                self.error_count += 1
                return None
                
        except Exception as e:
            print(f"Risk summary error: {e}")
            self.error_count += 1
            return None
    
    def get_status(self) -> Dict:
        """
        Get current explainer status
        
        Returns:
            Status dictionary
        """
        return {
            "provider": config.genai_provider.value,
            "provider_initialized": self.provider.is_initialized if self.provider else False,
            "explanations_generated": self.explanation_count,
            "errors": self.error_count,
            "context_size": len(self.metrics_history)
        }
    
    def clear_context(self) -> None:
        """Clear context history"""
        self.metrics_history.clear()


# Global explainer instance
risk_explainer = RiskExplainer()
