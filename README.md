# FinSight AI

**Financial Document Intelligence & Credit Risk Advisory Platform**

A production-grade, multi-tenant SaaS platform that automates financial document analysis and credit risk assessment using fine-tuned LLMs, classical ML, and a hybrid RAG system.

---

## What It Does

Upload a company's financial PDF (annual report, credit agreement, earnings call transcript) and receive in under 5 minutes:

- **Extracted Financial Ratios** — DSCR, leverage, interest coverage, current ratio, net profit margin (fine-tuned LLaMA 3.1 8B)
- **Sentiment Analysis** — overall financial sentiment with flagged negative sections (fine-tuned FinBERT)
- **Covenant Breach Detection** — identifies potential covenant violations with clause references (fine-tuned FinBERT)
- **ML Credit Risk Score** — XGBoost risk classification with SHAP explainability
- **Executive Risk Report** — GPT-4 synthesized narrative combining all findings
- **RAG Chat Interface** — ask follow-up questions grounded in the actual document

---

## Architecture Overview

- **AI Pipeline:** 6-agent LangGraph orchestration (parse → extract → sentiment + breach + risk in parallel → report)
- **RAG System:** HyDE + hybrid dense/sparse Qdrant search + RRF fusion + cross-encoder reranking
- **Backend:** FastAPI + Celery + Redis (async processing)
- **Frontend:** React + Vite + TailwindCSS + Framer Motion
- **Databases:** PostgreSQL (18 tables) · Redis (5 logical DBs) · Qdrant (vector store) · MinIO (object storage)
- **Infrastructure:** Docker (10 containers) · Nginx · Kubernetes (Minikube) · GitHub Actions CI/CD
- **Monitoring:** Prometheus + Grafana · LangSmith (dev) · RAGAS (RAG quality)
- **Security:** JWT + RBAC (4 roles) · Multi-tenant isolation · Rate limiting

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| LLM Fine-tuning | LLaMA 3.1 8B (QLoRA), FinBERT (full fine-tune) |
| Classical ML | XGBoost, SHAP, scikit-learn |
| Orchestration | LangGraph, Celery |
| RAG | HyDE, Qdrant (dense + sparse), RRF, cross-encoder |
| Backend | FastAPI, SQLAlchemy, Alembic, Pydantic |
| Frontend | React 18, Vite, TailwindCSS, Framer Motion, Recharts |
| Databases | PostgreSQL 16, Redis 7, Qdrant 1.9, MinIO |
| Infrastructure | Docker, Nginx, Minikube/Kubernetes, GitHub Actions |
| Monitoring | Prometheus, Grafana, LangSmith, RAGAS |

---

## Getting Started

### Prerequisites
- Python 3.11
- Docker Desktop
- Node.js 18+
- Git

### Quick Start
```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/finsight-ai.git
cd finsight-ai

# Set up environment
cp .env.example .env
# Edit .env with your actual values

# Start database containers
docker-compose -f docker-compose.dev.yml up -d

# Set up Python environment
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the backend
uvicorn backend.app.main:app --reload

# In a new terminal — start the frontend
cd frontend
npm install
npm run dev
```

---

## Project Status

🚧 **Under Active Development**

- [x] Phase 1 — Project Setup
- [ ] Phase 2 — Database Infrastructure
- [ ] Phase 3 — XGBoost Credit Risk Model
- [ ] Phase 4 — LLM Fine-Tuning (Colab)
- [ ] Phase 5 — FastAPI Backend
- [ ] Phase 6 — Celery Async Tasks
- [ ] Phase 7 — LangGraph Pipeline
- [ ] Phase 8 — Hybrid RAG System
- [ ] Phase 9 — Monitoring
- [ ] Phase 10 — Superadmin Features
- [ ] Phase 11 — React Frontend
- [ ] Phase 12 — Full Dockerization
- [ ] Phase 13 — Kubernetes Manifests
- [ ] Phase 14 — CI/CD Pipeline
- [ ] Phase 15 — AWS Deployment
- [ ] Phase 16 — Documentation & Demo

---

## License

This project is a portfolio demonstration and is not licensed for commercial use.

---

## Author

**Sahad** — AI/ML Engineer & Data Scientist