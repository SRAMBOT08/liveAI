"""
LiveAI Streamlit Dashboard
Real-time risk intelligence visualization and control panel
"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import time
from datetime import datetime
import json
import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from config.settings import (
    config,
    Mode,
    MarketDataProvider,
    GenAIProvider,
    update_mode,
    update_market_data_provider,
    update_genai_provider
)
from config.instruments import get_instrument_info
from streaming.producer_manager import producer_manager
from ai.explainer import risk_explainer


# Page configuration
st.set_page_config(
    page_title="LiveAI Risk Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
    st.session_state.metrics_history = []
    st.session_state.events_history = []
    st.session_state.explanations_history = []
    st.session_state.last_update = None


def initialize_system():
    """Initialize all system components"""
    if not st.session_state.initialized:
        with st.spinner("Initializing LiveAI system..."):
            # Initialize producer manager
            if producer_manager.initialize():
                st.success("✅ Kafka producer initialized")
            else:
                st.error("❌ Failed to initialize Kafka producer")
                return False
            
            # Initialize GenAI explainer
            if risk_explainer.initialize():
                st.success(f"✅ GenAI provider initialized ({config.genai_provider.value})")
            else:
                st.error("❌ Failed to initialize GenAI provider")
                return False
            
            st.session_state.initialized = True
            return True
    return True


def render_sidebar():
    """Render control sidebar"""
    st.sidebar.title("⚙️ Control Panel")
    
    # System status
    st.sidebar.subheader("System Status")
    
    if st.session_state.initialized:
        st.sidebar.success("🟢 System Online")
    else:
        st.sidebar.warning("🟡 System Offline")
    
    st.sidebar.divider()
    
    # Mode selection
    st.sidebar.subheader("Operating Mode")
    current_mode = st.sidebar.radio(
        "Select Mode:",
        options=[Mode.HISTORICAL.value, Mode.LIVE.value],
        index=0 if config.mode == Mode.HISTORICAL else 1,
        format_func=lambda x: "📜 Historical Replay" if x == "historical" else "🔴 Live Market"
    )
    
    if current_mode != config.mode.value:
        update_mode(Mode(current_mode))
        st.sidebar.info(f"Mode switched to: {current_mode}")
    
    st.sidebar.divider()
    
    # Market data provider selection
    st.sidebar.subheader("Market Data Provider")
    provider_options = [p.value for p in MarketDataProvider]
    current_provider_idx = provider_options.index(config.market_data_provider.value)
    
    selected_provider = st.sidebar.selectbox(
        "Select Provider:",
        options=provider_options,
        index=current_provider_idx,
        format_func=lambda x: {
            "polygon": "📡 Polygon.io",
            "intrinio": "📡 Intrinio",
            "twelve_data": "📡 Twelve Data",
            "historical": "📁 Historical CSV"
        }.get(x, x)
    )
    
    if selected_provider != config.market_data_provider.value:
        update_market_data_provider(MarketDataProvider(selected_provider))
        if st.session_state.initialized:
            with st.spinner("Switching provider..."):
                producer_manager.switch_provider(MarketDataProvider(selected_provider))
            st.sidebar.success(f"Switched to {selected_provider}")
    
    st.sidebar.divider()
    
    # GenAI provider selection
    st.sidebar.subheader("GenAI Provider")
    genai_options = [p.value for p in GenAIProvider]
    current_genai_idx = genai_options.index(config.genai_provider.value)
    
    selected_genai = st.sidebar.selectbox(
        "Select Provider:",
        options=genai_options,
        index=current_genai_idx,
        format_func=lambda x: {
            "openai": "🤖 OpenAI GPT",
            "gemini": "🤖 Google Gemini",
            "grok": "🤖 xAI Grok"
        }.get(x, x)
    )
    
    if selected_genai != config.genai_provider.value:
        update_genai_provider(GenAIProvider(selected_genai))
        if st.session_state.initialized:
            with st.spinner("Switching GenAI provider..."):
                risk_explainer.switch_provider(GenAIProvider(selected_genai))
            st.sidebar.success(f"Switched to {selected_genai}")
    
    st.sidebar.divider()
    
    # Streaming controls
    st.sidebar.subheader("Data Stream Control")
    
    producer_status = producer_manager.get_status()
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("▶️ Start", use_container_width=True):
            if producer_manager.start_streaming():
                st.sidebar.success("Stream started")
            else:
                st.sidebar.error("Failed to start")
    
    with col2:
        if st.button("⏸️ Stop", use_container_width=True):
            producer_manager.stop_streaming()
            st.sidebar.info("Stream stopped")
    
    # Producer stats
    st.sidebar.metric("Events Published", producer_status.get("events_published", 0))
    st.sidebar.metric("Errors", producer_status.get("errors", 0))


def render_instrument_info():
    """Render instrument information"""
    st.subheader("📈 Instrument Configuration")
    
    info = get_instrument_info()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Futures Contract",
            info['futures']['symbol'],
            info['futures']['name']
        )
    
    with col2:
        st.metric(
            "Current Price",
            f"${info['futures']['current_price']:.2f}"
        )
    
    with col3:
        st.metric(
            "Option Type",
            info['option']['type'].upper(),
            f"Strike: ${info['option']['strike']:.2f}"
        )
    
    with col4:
        st.metric(
            "Time to Expiration",
            f"{info['option']['tte_days']} days",
            info['option']['expiration'][:10]
        )


def render_greeks_dashboard(metrics):
    """Render Greeks metrics"""
    st.subheader("🎯 Option Greeks")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Delta", f"{metrics.get('delta', 0):.4f}")
    
    with col2:
        st.metric("Gamma", f"{metrics.get('gamma', 0):.6f}")
    
    with col3:
        st.metric("Theta", f"{metrics.get('theta', 0):.4f}")
    
    with col4:
        st.metric("Vega", f"{metrics.get('vega', 0):.4f}")
    
    with col5:
        st.metric("Rho", f"{metrics.get('rho', 0):.4f}")


def render_risk_dashboard(metrics):
    """Render risk metrics"""
    st.subheader("⚠️ Risk Assessment")
    
    risk_score = metrics.get('risk_score', 0)
    risk_regime = metrics.get('risk_regime', 'UNKNOWN')
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Risk score gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=risk_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Risk Score"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkred" if risk_score > 65 else ("orange" if risk_score > 30 else "green")},
                'steps': [
                    {'range': [0, 30], 'color': "lightgreen"},
                    {'range': [30, 65], 'color': "lightyellow"},
                    {'range': [65, 100], 'color': "lightcoral"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': risk_score
                }
            }
        ))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Risk Regime")
        
        regime_color = {
            "STABLE": "🟢",
            "SENSITIVE": "🟡",
            "FRAGILE": "🔴"
        }.get(risk_regime, "⚪")
        
        st.markdown(f"## {regime_color} {risk_regime}")
        
        st.markdown("### Shock Scenarios")
        st.metric("Shock +1%", f"{metrics.get('shock_up_1pct', 0):.4f}")
        st.metric("Shock -1%", f"{metrics.get('shock_down_1pct', 0):.4f}")
        st.metric("Shock +5%", f"{metrics.get('shock_up_5pct', 0):.4f}")
        st.metric("Shock -5%", f"{metrics.get('shock_down_5pct', 0):.4f}")


def render_ai_explanations():
    """Render AI explanations"""
    st.subheader("🤖 AI Risk Intelligence")
    
    if st.session_state.explanations_history:
        latest = st.session_state.explanations_history[-1]
        
        st.info(f"**Latest Explanation** ({latest['timestamp']})\n\n{latest['text']}")
        
        with st.expander("📜 Explanation History"):
            for exp in reversed(st.session_state.explanations_history[-10:]):
                st.markdown(f"**{exp['timestamp']}**")
                st.markdown(exp['text'])
                st.divider()
    else:
        st.info("Waiting for risk events to generate explanations...")


def main():
    """Main dashboard application"""
    
    # Header
    st.title("📊 LiveAI Real-Time Market Risk Intelligence Platform")
    st.caption("Production-grade streaming risk analytics with event-driven AI")
    
    # Render sidebar
    render_sidebar()
    
    # Initialize system
    if not initialize_system():
        st.error("Failed to initialize system. Please check configuration.")
        return
    
    st.divider()
    
    # Render instrument info
    render_instrument_info()
    
    st.divider()
    
    # Placeholder for real-time data
    # In production, this would connect to Pathway output or a shared state
    # For now, show static example
    
    example_metrics = {
        'timestamp': datetime.now().isoformat(),
        'underlying_price': 2050.0,
        'option_price': 12.45,
        'delta': 0.4521,
        'gamma': 0.00123,
        'theta': -0.0345,
        'vega': 0.1234,
        'rho': 0.0567,
        'risk_score': 42.3,
        'risk_regime': 'SENSITIVE',
        'shock_up_1pct': 0.4623,
        'shock_down_1pct': 0.4419,
        'shock_up_5pct': 0.5234,
        'shock_down_5pct': 0.3808
    }
    
    # Render Greeks
    render_greeks_dashboard(example_metrics)
    
    st.divider()
    
    # Render risk metrics
    render_risk_dashboard(example_metrics)
    
    st.divider()
    
    # Render AI explanations
    render_ai_explanations()
    
    # Footer
    st.divider()
    st.caption("LiveAI Risk Intelligence Platform | Powered by Pathway, Kafka, and GenAI")
    
    # Auto-refresh
    time.sleep(2)
    st.rerun()


if __name__ == "__main__":
    main()
