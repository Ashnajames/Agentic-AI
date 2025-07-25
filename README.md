
#  Enterprise-Grade ITSM RAG System

**Agentic-AI** is a powerful, production-ready Retrieval-Augmented Generation (RAG) system tailored for IT Service Management (ITSM). It combines the latest in semantic search, real-time scraping, and local AI generation to deliver accurate, contextual responses based on the top 10 ITSM tools outlined in [Zenduty's 2025 ITSM report](https://zenduty.com/blog/top-itsm-tools/).

---

## 🔧 Architecture Overview

```
app/
├── main.py              # Application entry point
├── api/                 # API layer with proper routing
├── core/                # Configuration and environment settings
├── db/                  # Database connections and models
├── services/            # Business logic layer
├── schemas/             # Pydantic data validation
└── utils/               # Helper utilities
```

### 🛠 Technology Stack
- **Weaviate**: High-performance vector database for semantic search
- **HuggingFace Transformers**: Local AI model for generation (no OpenAI dependency)
- **FastAPI**: Modern async web framework
- **Docker Compose**: Container orchestration for deployment

---

## 🚀 Key Features

### ✅ Advanced RAG Pipeline
- Real-time web scraping with retry logic
- Intelligent content chunking and HTML-aware preprocessing
- Sentence transformer embeddings for vector search
- Local HuggingFace model for response generation
- Source attribution and confidence scoring

### ✅ Production-Ready Features
- Health monitoring endpoints
- Automatic data refresh & change detection
- Comprehensive logging and error handling
- Pydantic-based validation
- Async-first design throughout
- Dockerized for easy deployment

### ✅ Smart Architecture
- Dependency injection for clean service management
- Modular, scalable service design
- Environment-based configuration management

---

## ⚙️ Quick Start

### 1. Setup

```bash
uv pip install -r requirements.txt 
```

### 2. Start Weaviate

```bash
docker-compose up -d weaviate
```

### 3. Run the Application

```bash
python -m app.main
```

### 4. Access the API

Visit: [http://localhost:8000](http://localhost:8000)

---

## 💡 Technical Highlights

### 🔍 Weaviate Integration
- Custom ITSM schema definition
- Optimized vector search with filters
- Automatic schema creation and batching

### 🧠 HuggingFace Local Model
- Efficient on-device inference (CPU/GPU)
- Quantized model support
- Caching and fallback handling

### 📄 Smart Content Processing
- Clean HTML extraction with `unstructured`
- Title-aware and overlap-based chunking
- Tool-specific metadata preservation

---

## 🎯 Advanced Capabilities

### 🔄 Real-Time Knowledge Refresh
- Periodic scraping for updated ITSM content
- Change detection and diff-based updates
- Manual refresh endpoints

### 📈 User Experience & Monitoring
- Confidence scoring per response
- Source attribution with citation
- Response time logging
- Real-time system health endpoints

### 📊 Monitoring & Analytics
- Application health and performance metrics
- Structured, centralized logging
- Error trace tracking
- System resource monitoring and alerts

---

## 📦 Deployment

This system is:

- ✅ **Scalable**: Handles high concurrency via async operations and connection pooling
- ✅ **Maintainable**: Clean architecture and modular services
- ✅ **Extensible**: Add new models, tools, or scrapers easily
- ✅ **Production-Ready**: Error handling, metrics, monitoring, and CI/CD compatible

---

## 📚 Domain Focus

> This AI agent is exclusively focused on ITSM tools as documented in the Zenduty 2025 report. It will not respond to unrelated or out-of-domain queries.

---

## 🧠 Knowledge Base

The system includes detailed, context-rich knowledge about the following ITSM tools:

1. **Xurrent** (Top pick, AI-first platform)
2. ServiceNow
3. BMC Helix
4. Freshservice
5. Jira Service Management
6. Ivanti Neurons
7. SolarWinds
8. ManageEngine
9. SysAid
10. Microsoft Dynamics 365 for Customer Service


## 🔑 Authentication: HuggingFace Token

To use HuggingFace models (for embedding or generation), set your HuggingFace token in the environment variables:

```bash
export HUGGINGFACEHUB_API_TOKEN=your_hf_token_here
```

Alternatively, update your `.env` file if you are using `python-dotenv`:

```env
HUGGINGFACEHUB_API_TOKEN=your_hf_token_here
```

Make sure the token has the necessary access to download private or gated models if required.
