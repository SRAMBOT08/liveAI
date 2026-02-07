"""
LiveAI Standalone Demo
Demonstrates core functionality without Kafka/Pathway dependencies
"""
import sys
from datetime import datetime
import time

# Add current directory to path
sys.path.insert(0, '.')

try:
    from config.instruments import get_instrument_info, DEFAULT_FUTURES, DEFAULT_OPTION
    from pathway_pipeline.greeks import calculate_option_greeks
    from pathway_pipeline.risk import compute_risk_score, determine_risk_regime, compute_shock_scenarios
    from pathway_pipeline.events import RiskEventDetector
    
    print("=" * 70)
    print("  LiveAI Real-Time Market Risk Intelligence Platform")
    print("  Standalone Demo (No Kafka/Pathway Required)")
    print("=" * 70)
    print()
    
    # Show instrument configuration
    info = get_instrument_info()
    print("📈 Instrument Configuration:")
    print(f"  Futures: {info['futures']['name']} ({info['futures']['symbol']})")
    print(f"  Price: ${info['futures']['current_price']:.2f}")
    print(f"  Option: {info['option']['type'].upper()} @ ${info['option']['strike']:.2f}")
    print(f"  Expiration: {info['option']['tte_days']} days")
    print()
    
    # Initialize event detector
    detector = RiskEventDetector()
    
    # Simulate price movements
    print("🔄 Simulating Market Data Stream...")
    print("-" * 70)
    print()
    
    base_price = DEFAULT_FUTURES.current_price
    volatility = 0.20  # 20% IV
    
    # Price scenarios
    price_changes = [0, 10, -5, 15, -20, 25, -10, 5, 30, -15]
    
    for i, change in enumerate(price_changes):
        current_price = base_price + change
        timestamp = datetime.now().isoformat()
        
        print(f"⏰ Update {i+1}/10 - Price: ${current_price:.2f} (Change: ${change:+.2f})")
        
        # Calculate Greeks
        greeks = calculate_option_greeks(current_price, volatility=volatility)
        
        print(f"  Greeks:")
        print(f"    Delta: {greeks['delta']:>8.4f}  Gamma: {greeks['gamma']:>10.6f}")
        print(f"    Theta: {greeks['theta']:>8.4f}  Vega:  {greeks['vega']:>10.4f}")
        
        # Calculate risk metrics
        risk_score = compute_risk_score(greeks)
        risk_regime = determine_risk_regime(risk_score)
        
        print(f"  Risk Score: {risk_score:.1f}/100")
        print(f"  Risk Regime: {risk_regime}")
        
        # Build metrics dict
        current_metrics = {
            'timestamp': timestamp,
            'underlying_price': current_price,
            'option_price': greeks['option_price'],
            'delta': greeks['delta'],
            'gamma': greeks['gamma'],
            'theta': greeks['theta'],
            'vega': greeks['vega'],
            'rho': greeks['rho'],
            'risk_score': risk_score,
            'risk_regime': risk_regime
        }
        
        # Detect events
        events = detector.detect_events(current_metrics)
        
        if events:
            for event in events:
                severity_icon = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}.get(event.severity, "⚪")
                print(f"  {severity_icon} RISK EVENT: {event.event_type} (Severity: {event.severity})")
                print(f"     {event.description}")
                print(f"     Change: {event.change_pct:+.2f}%")
        
        print()
        time.sleep(0.5)  # Pause for readability
    
    print("=" * 70)
    print("✅ Demo Complete!")
    print()
    print("📊 Summary:")
    print(f"  - Total Events Detected: {len(detector.event_history)}")
    print(f"  - Event Types: {set(e.event_type for e in detector.event_history)}")
    print()
    print("🚀 To run the full system with Kafka, Pathway, and GenAI:")
    print("  1. Start Docker Desktop")
    print("  2. Run: docker run -d --name kafka -p 9092:9092 apache/kafka:latest")
    print("  3. Install: pip install -r requirements.txt")
    print("  4. Configure: Copy .env.example to .env and add API keys")
    print("  5. Run: python app.py")
    print("=" * 70)

except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print()
    print("Please install required packages:")
    print("  pip install numpy scipy pandas")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
