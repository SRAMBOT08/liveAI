"""
LiveAI Real-Time Market Risk Intelligence Platform
Main Pathway Application Entry Point

This is the core streaming engine that:
1. Ingests market data from Kafka
2. Computes Greeks and risk metrics in real-time
3. Detects risk events
4. Triggers GenAI explanations
"""
import pathway as pw
import time
import signal
import sys
from datetime import datetime

from config.settings import config
from config.instruments import DEFAULT_FUTURES, get_instrument_info
from pathway_pipeline.ingest import create_kafka_input
from pathway_pipeline.state import compute_price_state
from pathway_pipeline.risk import compute_full_risk_metrics
from pathway_pipeline.events import risk_event_detector
from ai.explainer import risk_explainer


class LiveAIEngine:
    """
    Main streaming engine orchestrating all components
    """
    
    def __init__(self):
        self.is_running = False
        self.current_metrics = None
        self.latest_explanation = None
    
    def initialize(self) -> bool:
        """
        Initialize all system components
        
        Returns:
            True if successful, False otherwise
        """
        print("=" * 60)
        print("LiveAI Real-Time Market Risk Intelligence Platform")
        print("=" * 60)
        
        # Print instrument info
        instrument_info = get_instrument_info()
        print(f"\nInstrument Configuration:")
        print(f"  Futures: {instrument_info['futures']['name']} ({instrument_info['futures']['symbol']})")
        print(f"  Option: {instrument_info['option']['type'].upper()} @ {instrument_info['option']['strike']}")
        print(f"  Expiration: {instrument_info['option']['tte_days']} days")
        
        # Initialize GenAI explainer
        print(f"\nInitializing GenAI provider: {config.genai_provider.value}")
        if not risk_explainer.initialize():
            print("WARNING: GenAI provider failed to initialize")
            return False
        
        print(f"Mode: {config.mode.value}")
        print(f"Market Data Provider: {config.market_data_provider.value}")
        print("=" * 60)
        
        return True
    
    def create_pipeline(self):
        """
        Create the Pathway streaming pipeline
        
        Returns:
            Configured pipeline
        """
        print("\nCreating Pathway streaming pipeline...")
        
        # Step 1: Ingest from Kafka
        market_events = create_kafka_input()
        
        # Step 2: Compute price state
        price_state = compute_price_state(market_events)
        
        # Step 3: Define UDF to compute risk metrics
        @pw.udf
        def compute_risk_metrics_udf(timestamp: str, instrument_id: str, price: float) -> pw.Json:
            """Compute full risk metrics for each price update"""
            metrics = compute_full_risk_metrics(
                underlying_price=price,
                timestamp=timestamp,
                instrument_id=instrument_id,
                volatility=0.20  # 20% implied volatility
            )
            self.current_metrics = metrics
            
            # Add to explainer context
            risk_explainer.add_context(metrics)
            
            return pw.Json(metrics)
        
        # Step 4: Apply risk computation
        risk_metrics = price_state.select(
            risk_data=compute_risk_metrics_udf(
                pw.this.timestamp,
                pw.this.instrument_id,
                pw.this.price
            )
        )
        
        # Step 5: Define UDF for event detection and explanation
        @pw.udf
        def detect_and_explain_events(risk_json: pw.Json) -> pw.Json:
            """Detect risk events and generate explanations"""
            risk_dict = risk_json.as_dict()
            
            # Detect events
            events = risk_event_detector.detect_events(risk_dict)
            
            explanations = []
            
            # Generate explanation for each event
            for event in events:
                print(f"\n🚨 RISK EVENT: {event.event_type} (Severity: {event.severity})")
                print(f"   {event.description}")
                
                explanation = risk_explainer.explain_event(event.to_dict(), risk_dict)
                
                if explanation:
                    print(f"   💡 AI Explanation: {explanation}")
                    explanations.append({
                        "event": event.to_dict(),
                        "explanation": explanation
                    })
                    self.latest_explanation = explanation
            
            return pw.Json({
                "events": [e.to_dict() for e in events],
                "explanations": explanations
            })
        
        # Step 6: Apply event detection
        events_with_explanations = risk_metrics.select(
            event_data=detect_and_explain_events(pw.this.risk_data)
        )
        
        # Step 7: Output to debug (console)
        pw.io.null.write(events_with_explanations)
        
        print("Pipeline created successfully")
        
        return events_with_explanations
    
    def run(self):
        """
        Run the Pathway streaming engine
        """
        try:
            print("\n" + "=" * 60)
            print("Starting Pathway streaming engine...")
            print("Waiting for market data from Kafka...")
            print("=" * 60 + "\n")
            
            self.is_running = True
            
            # Create and run pipeline
            pipeline = self.create_pipeline()
            
            # Run Pathway
            pw.run()
            
        except KeyboardInterrupt:
            print("\n\nShutdown signal received...")
            self.shutdown()
        except Exception as e:
            print(f"\n\nEngine error: {e}")
            self.shutdown()
    
    def shutdown(self):
        """Graceful shutdown"""
        print("\nShutting down LiveAI engine...")
        self.is_running = False
        print("Shutdown complete")
    
    def get_current_metrics(self):
        """Get latest computed metrics"""
        return self.current_metrics
    
    def get_latest_explanation(self):
        """Get latest AI explanation"""
        return self.latest_explanation


# Global engine instance
engine = LiveAIEngine()


def signal_handler(sig, frame):
    """Handle shutdown signals"""
    print("\n\nReceived interrupt signal")
    engine.shutdown()
    sys.exit(0)


def main():
    """
    Main entry point
    """
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize
    if not engine.initialize():
        print("Failed to initialize engine")
        sys.exit(1)
    
    # Run
    engine.run()


if __name__ == "__main__":
    main()
