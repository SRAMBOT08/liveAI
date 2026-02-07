# LiveAI Real-Time Market Risk Intelligence Platform

A production-grade streaming financial risk intelligence system built for hackathon demonstration.

## Quick Links

- **Full Documentation**: See [README.md](README.md)
- **Architecture**: Kafka + Pathway + Multi-GenAI
- **Features**: Real-time Greeks, Risk Regimes, Event-driven AI

## Super Quick Start

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure (copy and edit)
cp .env.example .env

# 3. Start Kafka
docker run -d --name kafka -p 9092:9092 apache/kafka:latest

# 4. Run (3 separate terminals)
# Terminal 1: Producer
python -c "from streaming.producer_manager import producer_manager; producer_manager.initialize(); producer_manager.start_streaming(); input('Running...')"

# Terminal 2: Pathway Engine  
python app.py

# Terminal 3: Dashboard
streamlit run dashboard/app.py
```

## What This System Does

1. **Ingests** market data from multiple providers (Polygon, Intrinio, Twelve Data, CSV)
2. **Computes** Black-76 option Greeks in real-time (Delta, Gamma, Theta, Vega, Rho)
3. **Detects** risk events (regime changes, Greek spikes)
4. **Explains** events using GenAI (OpenAI, Gemini, Grok)
5. **Visualizes** everything in a Streamlit dashboard

## Core Files

- `app.py` - Pathway streaming engine
- `dashboard/app.py` - Streamlit UI
- `config/` - System configuration
- `kafka/` - Producer manager
- `pathway_pipeline/` - Core computation
- `ai/` - GenAI explainers
- `market_data/providers/` - Data source plugins

## Tech Stack

- **Streaming**: Pathway + Kafka
- **Math**: NumPy + SciPy (Black-76)
- **AI**: OpenAI + Gemini + Grok
- **UI**: Streamlit + Plotly

Built for financial risk professionals who need **real-time intelligence**, not batch reports.
