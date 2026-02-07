# LiveAI Real-Time Market Risk Intelligence Platform

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

**Production-grade streaming financial risk intelligence system for derivatives markets**

---

## 🎯 Executive Summary

LiveAI is a **real-time market risk intelligence platform** that continuously monitors option Greeks, detects risk events, and generates human-readable explanations using GenAI. Built for financial risk managers who need **streaming analytics**, not batch reports.

### Core Capabilities
- ✅ **Streaming-first architecture** using Apache Kafka + Pathway
- ✅ **Deterministic Black-76 Greeks** computation (Delta, Gamma, Theta, Vega, Rho)
- ✅ **Stateful risk tracking** with regime classification
- ✅ **Event-driven AI explanations** (not continuous chatbots)
- ✅ **Multi-provider design** for data and AI (swap without code changes)
- ✅ **Demo-safe** with historical replay mode

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MARKET DATA LAYER                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Polygon  │  │ Intrinio │  │ 12Data   │  │Historical│   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       └────────────┬┴────────────┬┴────────────┬┘          │
│                    │  Unified Schema  │                     │
└────────────────────┼──────────────────┼─────────────────────┘
                     │                  │
                     ▼                  ▼
            ┌─────────────────────────────────┐
            │        KAFKA (Event Bus)        │
            │     Topic: market_data_events   │
            └────────────┬────────────────────┘
                         │
                         ▼
            ┌─────────────────────────────────┐
            │      PATHWAY (Core Engine)      │
            │  • Stateful Ingestion           │
            │  • Black-76 Computation         │
            │  • Greeks Calculation           │
            │  • Risk Scoring                 │
            │  • Event Detection              │
            └────────────┬────────────────────┘
                         │
                         ▼
            ┌─────────────────────────────────┐
            │       GENAI LAYER (RAG)         │
            │  ┌─────────┐  ┌─────────┐       │
            │  │ OpenAI  │  │ Gemini  │       │
            │  └─────────┘  └─────────┘       │
            │  ┌─────────┐                    │
            │  │  Grok   │  Event-Triggered   │
            │  └─────────┘                    │
            └────────────┬────────────────────┘
                         │
                         ▼
            ┌─────────────────────────────────┐
            │    STREAMLIT DASHBOARD (UI)     │
            │  • Real-time Greeks             │
            │  • Risk Regime Monitor          │
            │  • AI Explanations              │
            │  • Provider Switching           │
            └─────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.10+**
2. **Apache Kafka** (or Docker Compose)
3. **API Keys** (at least one market data + one GenAI provider)

### Installation

```bash
# Clone repository
git clone <your-repo-url>
cd liveAI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Running the System

**Step 1: Start Kafka**

```bash
# Using Docker (recommended)
docker run -d --name kafka -p 9092:9092 \
  apache/kafka:latest

# Or use local Kafka installation
bin/kafka-server-start.sh config/server.properties
```

**Step 2: Start Market Data Producer**

```python
# In one terminal
python -c "
from kafka.producer_manager import producer_manager
producer_manager.initialize()
producer_manager.start_streaming()
input('Press Enter to stop...')
"
```

**Step 3: Start Pathway Engine**

```bash
# In another terminal
python app.py
```

**Step 4: Launch Dashboard**

```bash
# In a third terminal
streamlit run dashboard/app.py
```

**Access Dashboard:** http://localhost:8501

---

## 📊 Features Deep Dive

### 1. Multi-Provider Market Data

**Supported Providers:**
- **Polygon.io** - CME futures and options
- **Intrinio** - Financial market data
- **Twelve Data** - Real-time and historical
- **Historical CSV** - Replay mode for demos

**Provider Switching:**
```python
from config.settings import update_market_data_provider, MarketDataProvider
update_market_data_provider(MarketDataProvider.POLYGON)
```

All providers implement the same `BaseMarketDataProvider` interface with unified output schema.

### 2. Black-76 Greeks Calculation

```python
from pathway_pipeline.greeks import calculate_option_greeks

greeks = calculate_option_greeks(
    underlying_price=2050.0,
    volatility=0.20
)
# Returns: {delta, gamma, theta, vega, rho, option_price}
```

**Deterministic computation** - no ML, no external APIs.

### 3. Risk Health Score (0-100)

```
Score Range    │ Regime      │ Interpretation
───────────────┼─────────────┼────────────────────────
0 - 30         │ STABLE      │ Low risk, stable Greeks
30 - 65        │ SENSITIVE   │ Moderate risk, monitor
65 - 100       │ FRAGILE     │ High risk, rapid changes
```

### 4. Event-Driven AI Explanations

**AI triggers ONLY when:**
- Delta changes > 5%
- Gamma changes > 10%
- Risk regime transitions
- Significant Greek movements

**AI does NOT:**
- Run continuously
- Make predictions
- Recommend trades
- Compute Greeks

### 5. Context-Grounded RAG

Simple in-memory RAG without vector databases:
```python
# Explainer maintains recent metrics history
risk_explainer.add_context(current_metrics)

# AI receives last 10 metrics as context
explanation = risk_explainer.explain_event(event, current_metrics)
```

---

## 🔧 Configuration

### System Configuration (`config/settings.py`)

```python
from config.settings import config

# Mode selection
config.mode = Mode.HISTORICAL  # or Mode.LIVE

# Provider selection
config.market_data_provider = MarketDataProvider.HISTORICAL
config.genai_provider = GenAIProvider.OPENAI

# Risk thresholds
config.risk_thresholds.delta_change_threshold = 0.05  # 5%
```

### Instrument Configuration (`config/instruments.py`)

```python
# Define your futures contract
GOLD_FUTURES = FuturesContract(
    symbol="GC",
    name="Gold Futures",
    exchange="COMEX",
    current_price=2050.0
)

# Define your option
GOLD_CALL_OPTION = OptionContract(
    symbol="GC_C_2100",
    underlying="GC",
    option_type="call",
    strike=2100.0,
    expiration=datetime.now() + timedelta(days=90),
    risk_free_rate=0.045
)
```

---

## 🔄 Provider Failover Strategy

### Market Data Failover

```python
# Automatic failover logic
providers_priority = [
    MarketDataProvider.POLYGON,
    MarketDataProvider.INTRINIO,
    MarketDataProvider.HISTORICAL  # Fallback
]

for provider in providers_priority:
    if producer_manager.switch_provider(provider):
        break
```

### GenAI Failover

```python
# Try providers in order
genai_priority = [
    GenAIProvider.OPENAI,
    GenAIProvider.GEMINI,
    GenAIProvider.GROK
]

for provider in genai_priority:
    if risk_explainer.switch_provider(provider):
        break
```

---

## 📈 Demo Flow

### Historical Replay Mode (Demo Safe)

1. **Select Mode:** Historical in dashboard
2. **Load CSV:** Automatically uses `data/historical_prices.csv`
3. **Control Speed:** Adjust replay multiplier (1.0 = real-time)
4. **Observe:**
   - Greeks update as prices change
   - Risk events detected
   - AI generates explanations

### Live Mode (Production)

1. **Configure API Keys** in `.env`
2. **Select Provider:** Polygon/Intrinio/Twelve Data
3. **Start Streaming:** Click "Start" in dashboard
4. **Monitor:**
   - Real-time Greeks
   - Live risk regime
   - Event-triggered AI insights

---

## 🛠️ Development

### Project Structure

```
liveAI/
├── app.py                      # Pathway entry point
├── requirements.txt            # Dependencies
├── config/
│   ├── settings.py             # Global config
│   └── instruments.py          # Financial instruments
├── kafka/
│   ├── kafka_utils.py          # Kafka helpers
│   └── producer_manager.py     # Provider orchestration
├── market_data/
│   └── providers/              # Data provider implementations
├── pathway_pipeline/
│   ├── schemas.py              # Pathway schemas
│   ├── ingest.py               # Kafka → Pathway
│   ├── greeks.py               # Black-76 computation
│   ├── risk.py                 # Risk scoring
│   └── events.py               # Event detection
├── ai/
│   ├── prompts.py              # Prompt templates
│   ├── explainer.py            # AI orchestration
│   └── providers/              # GenAI implementations
├── dashboard/
│   └── app.py                  # Streamlit UI
└── data/
    └── historical_prices.csv   # Sample data
```

### Testing

```bash
# Test market data provider
python -c "
from market_data.providers import HistoricalProvider
provider = HistoricalProvider('GC', data_path='data/historical_prices.csv')
provider.connect()
print(provider.get_latest_price())
"

# Test Greeks calculation
python -c "
from pathway_pipeline.greeks import calculate_option_greeks
greeks = calculate_option_greeks(2050.0)
print(greeks)
"
```

---

## 🐳 Docker Deployment

```dockerfile
# Build image
docker build -t liveai -f docker/Dockerfile .

# Run with Kafka
docker-compose up
```

---

## 📚 Key Design Decisions

### Why Kafka?
- **Decoupled architecture** - producers/consumers independent
- **Replay capability** - reprocess historical events
- **Scalability** - handle high-frequency data

### Why Pathway?
- **Streaming-first** - not batch with delays
- **Stateful computation** - track changes over time
- **Python-native** - integrate with scientific stack

### Why NOT Kafka for Analytics?
- Kafka is **transport**, not **computation**
- No built-in state management
- No complex window operations
- Pathway is the **analytical engine**

### Why Event-Driven AI?
- **Cost-effective** - only trigger when needed
- **Relevant** - AI explains actual events
- **Production-ready** - no continuous load

---

## 🎓 For Hackathon Judges

### Innovation Highlights

1. **True Streaming Architecture**: Not polling, not batch - real streaming with Pathway
2. **Provider Abstraction**: Swap data/AI providers without code changes
3. **Deterministic Finance**: Black-76 math, not ML black boxes
4. **Event-Driven AI**: AI reacts to events, doesn't run idle
5. **Production Patterns**: Clean architecture, type hints, error handling

### Technical Depth

- **Stateful streaming** with Pathway reducers
- **Financial mathematics** (Black-76, Greeks computation)
- **Multi-provider design patterns**
- **Context-grounded RAG** without vector databases
- **Real-time event detection** with configurable thresholds

### Demo Reliability

- **Historical replay mode** - deterministic demos
- **Provider failover** - graceful degradation
- **Error handling** - won't crash on API failures

---

## 🤝 Contributing

This is a hackathon project demonstrating production-grade architecture patterns for financial risk systems.

---

## 📄 License

MIT License - See LICENSE file

---

## 🙏 Acknowledgments

- **Pathway** - Streaming data processing
- **Apache Kafka** - Event backbone
- **OpenAI/Google/xAI** - GenAI capabilities
- **CME Group** - Options market inspiration

---

## 📞 Contact

Built with ❤️ for financial risk professionals who need **real-time intelligence**, not yesterday's reports.

**Project:** LiveAI Real-Time Market Risk Intelligence Platform  
**Version:** 1.0.0  
**Status:** Production-Ready Architecture Demo
