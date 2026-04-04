<div align="center">

# 🏦 FinSight AI

### Financial Document Intelligence & Credit Risk Advisory Platform

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org)
[![Docker](https://img.shields.io/badge/Docker-10_Containers-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-6_Agents-FF6F00?style=for-the-badge)](https://langchain-ai.github.io/langgraph/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-KEDA_HPA-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)](https://kubernetes.io)
[![AWS](https://img.shields.io/badge/AWS-EC2_Deployed-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)](https://aws.amazon.com)

**A production-grade, multi-tenant SaaS platform that transforms financial document analysis from a 4–6 hour manual process into an automated 5-minute AI-powered pipeline.**

[🌐 Live Demo](http://65.0.114.221) · [📖 API Docs](http://65.0.114.221/api/docs) 

```
Note: The deployed application may not always be accessible, as compute resources are managed dynamically to optimize costs.

If you would like to access the live system, please feel free to reach out via the contact details provided below, and I will be happy to enable access.
```
---

<img src="https://img.shields.io/badge/⚡_Status-Live_on_AWS-success?style=for-the-badge" alt="Live Status"/>

</div>

---

## 📑 Table of Contents

| Section | Description |
|---------|-------------|
| [🎯 The Business Problem](#-the-business-problem) | Why this platform exists |
| [💡 The Solution](#-the-solution) | How FinSight AI solves it |
| [🏗️ System Architecture](#️-system-architecture) | High-level architecture diagram |
| [🤖 AI/ML Pipeline](#-aiml-pipeline--6-agent-langgraph-orchestration) | 6-agent LangGraph pipeline |
| [🔍 Hybrid RAG System](#-hybrid-rag-chat-system) | 5-step retrieval-augmented generation |
| [🧠 Fine-Tuned Models](#-fine-tuned-models) | LLaMA 3.1, FinBERT sentiment, FinBERT breach |
| [📊 XGBoost Risk Model](#-xgboost-credit-risk-model) | ML risk scoring with SHAP explainability |
| [🛡️ Auth & Multi-Tenancy](#️-authentication-rbac--multi-tenancy) | JWT, RBAC, tenant isolation |
| [🗄️ Database Architecture](#️-database-architecture) | 18 PostgreSQL tables, Redis, Qdrant, MinIO |
| [🐳 Docker Infrastructure](#-docker-infrastructure--10-containers) | 10-container production stack |
| [☸️ Kubernetes & Autoscaling](#️-kubernetes--autoscaling) | KEDA-driven HPA manifests |
| [📈 Monitoring & Observability](#-monitoring--observability) | Prometheus, Grafana, LangSmith |
| [⚡ Async Processing](#-async-processing--celery--redis) | Celery, Redis, dead letter queue |
| [🎨 Frontend](#-frontend) | React, TailwindCSS, Framer Motion |
| [🛠️ Tech Stack](#️-complete-technology-stack) | Full technology reference |
| [🚀 Deployment](#-deployment) | AWS EC2 deployment guide |
| [📂 Project Structure](#-project-structure) | Complete folder layout |
| [🧪 Testing](#-testing) | pytest test suite |
| [🔮 Future Enhancements](#-future-enhancements) | Roadmap |

---

## 🎯 The Business Problem

> **Credit analysts and risk officers at banks, investment firms, and financial institutions spend 4–6 hours manually analyzing a single company's financial report.**

Every day, financial professionals across UAE institutions — ADGM-regulated banks, DIFC-based investment firms, sovereign wealth funds, and retail banks — face the same tedious, error-prone workflow:

| Manual Task | Time Spent | Error Risk |
|-------------|-----------|------------|
| Reading 80–150 pages of dense financial text | 1–2 hours | Missed critical clauses |
| Manually extracting key financial ratios (DSCR, leverage, interest coverage) | 30–60 min | Calculation errors |
| Identifying covenant breaches buried in legal language | 45–90 min | Overlooked violations |
| Assessing overall financial sentiment and tone | 30–45 min | Subjective bias |
| Producing a structured credit risk advisory report | 1–2 hours | Inconsistent formatting |
| **Total** | **4–6 hours** | **High** |

### **Why This Matters in the UAE Financial Sector**

- 🏛️ **Regulatory compliance** (ADGM, DIFC, Central Bank of UAE) requires documented, auditable risk assessments
- 📊 **Explainability requirements** — regulators demand to know *why* a risk decision was made, not just the score
- 🔒 **Data sovereignty** — sensitive financial documents cannot be sent to third-party cloud AI services
- ⚡ **Competitive pressure** — institutions processing reports faster gain a significant market advantage

---

## 💡 The Solution

### **FinSight AI reduces credit risk analysis from 4–6 hours to under 5 minutes.**

```
📄 Upload PDF → 🤖 6 AI Agents Process → 📊 Complete Risk Report → 💬 Ask Questions via RAG Chat
```

The platform automates the entire credit analysis workflow:

| What FinSight AI Does | How It Does It | Time |
|----------------------|---------------|------|
| Extract financial ratios from any document | Fine-tuned LLaMA 3.1 8B with QLoRA adapter | ~3 min |
| Classify financial sentiment across all pages | Fine-tuned FinBERT (95.37% accuracy) | ~30 sec |
| Detect covenant breaches in legal language | Fine-tuned FinBERT breach classifier | ~30 sec |
| Score credit risk with full explainability | XGBoost + SHAP feature importance | < 1 sec |
| Write a professional risk advisory report | GPT-4 with structured context | ~10 sec |
| Answer any question about the document | Hybrid RAG with HyDE + cross-encoder | ~5 sec |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          NGINX REVERSE PROXY                            │
│                    (SSL · Load Balancing · Static Files)                 │
├──────────────────┬──────────────────────────────────────────────────────┤
│                  │                                                      │
│   React Frontend │              FastAPI Backend                         │
│   (Vite + Tailwind)            (JWT · RBAC · Multi-tenant)             │
│                  │                    │                                  │
│                  │         ┌──────────┴──────────┐                      │
│                  │         │                     │                      │
│                  │    Celery Worker          RAG Service                │
│                  │    (Async Pipeline)       (HyDE · RRF · Rerank)     │
│                  │         │                     │                      │
│                  │    LangGraph 6-Agent          │                      │
│                  │    Orchestration              │                      │
│                  │    ┌─────────────┐            │                      │
│                  │    │ Agent 1: Parser           │                      │
│                  │    │ Agent 2: LLaMA Extractor  │                      │
│                  │    │ Agent 3: FinBERT Sentiment │                     │
│                  │    │ Agent 4: FinBERT Breach    │                     │
│                  │    │ Agent 5: XGBoost Risk      │                     │
│                  │    │ Agent 6: GPT-4 Report      │                     │
│                  │    └─────────────┘            │                      │
├──────────────────┴──────────────────────────────────────────────────────┤
│                         DATA LAYER                                      │
│  ┌──────────┐  ┌───────┐  ┌────────┐  ┌───────┐  ┌──────────────────┐ │
│  │PostgreSQL│  │ Redis │  │ Qdrant │  │ MinIO │  │Prometheus+Grafana│ │
│  │18 Tables │  │ 5 DBs │  │Vectors │  │  PDFs │  │  4 Dashboards   │ │
│  └──────────┘  └───────┘  └────────┘  └───────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### Architecture Decision Records

| Decision | Choice | Rationale |
|----------|--------|-----------|
| LLM inference | GGUF + llama-cpp-python (CPU) | Self-hosted for data sovereignty; no GPU required |
| Agent orchestration | LangGraph (not CrewAI/AutoGen) | Deterministic graph with conditional edges; production-ready |
| Vector database | Qdrant (not Pinecone/Weaviate) | Self-hosted; supports hybrid dense+sparse search natively |
| Task queue | Celery + Redis (not RQ/Dramatiq) | Industry standard; supports dead letter queue; Flower monitoring |
| Risk model | XGBoost (not neural network) | Regulatory requirement for SHAP explainability in financial services |
| RAG strategy | Hybrid + HyDE + RRF + Cross-encoder | 4-layer retrieval eliminates single-strategy failure modes |
| Frontend state | Zustand (not Redux) | Minimal boilerplate; sufficient for this application's complexity |

---

## 🤖 AI/ML Pipeline — 6-Agent LangGraph Orchestration

The document processing pipeline is orchestrated by **LangGraph** — a directed acyclic graph where each node is a specialized AI agent.

```
                    ┌──────────────┐
                    │   Agent 1    │
                    │  Doc Parser  │
                    │  & Indexer   │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
       ┌──────────┐ ┌──────────┐ ┌──────────┐
       │ Agent 2  │ │ Agent 3  │ │ Agent 4  │
       │  LLaMA   │ │ FinBERT  │ │ FinBERT  │
       │ Extractor│ │Sentiment │ │ Breach   │
       └────┬─────┘ └────┬─────┘ └────┬─────┘
            │             │            │
            ▼             │            │
       ┌──────────┐      │            │
       │ Agent 5  │      │            │
       │ XGBoost  │      │            │
       │Risk Score│      │            │
       └────┬─────┘      │            │
            │             │            │
            └─────────────┼────────────┘
                          │
                   ┌──────▼───────┐
                   │   Agent 6    │
                   │   GPT-4     │
                   │Report Writer │
                   └──────────────┘
```

**Parallel execution:** Agents 2, 3, and 4 run simultaneously after Agent 1 completes — they are completely independent and each read from Qdrant directly. Agent 5 depends on Agent 2 (needs extracted ratios). Agent 6 waits for all prior agents.

### Agent Details

| Agent | Model | Input | Output | Latency (CPU) |
|-------|-------|-------|--------|---------------|
| 1 — Document Parser | PyMuPDF + spaCy + BGE + fastembed | Raw PDF | Qdrant vectors + PostgreSQL chunks | 1–3 min |
| 2 — Ratio Extractor | **Fine-tuned LLaMA 3.1 8B** (GGUF Q4_K_M + LoRA) | All chunk texts | 5 financial ratios (DSCR, leverage, interest coverage, current ratio, net profit margin) | 3–8 min |
| 3 — Sentiment Analyst | **Fine-tuned FinBERT** (95.37% accuracy) | All chunk texts | Overall sentiment + flagged negative sentences | 30–60 sec |
| 4 — Breach Detector | **Fine-tuned FinBERT** (2-class) | All chunk texts | Covenant breach flags with clause references | 30–60 sec |
| 5 — Risk Scorer | **XGBoost** + SHAP | Extracted ratios | Risk score (0–1) + tier + SHAP values | < 1 sec |
| 6 — Report Writer | **GPT-4** | All agent outputs | Professional risk advisory narrative | 5–10 sec |

---

## 🔍 Hybrid RAG Chat System

The RAG (Retrieval-Augmented Generation) chat enables analysts to ask any question about the uploaded document and receive grounded, cited answers.

### 5-Step Pipeline (runs on every chat query)

```
User Question
     │
     ▼
┌─────────────────┐
│  Step 1: HyDE   │  GPT-3.5-turbo generates a hypothetical answer
│  (Hypothetical   │  → Embedded with BGE to create query vector
│   Document       │  → Solves the "question ≠ answer" embedding gap
│   Embeddings)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Step 2: Hybrid  │  Dense search (cosine similarity, top-20)
│  Qdrant Search   │  + Sparse BM25 search (keyword matching, top-20)
│                  │  → Both filtered by tenant_id AND document_id
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Step 3: RRF     │  Reciprocal Rank Fusion merges both lists
│  Fusion          │  → Score = 1/(60+rank_dense) + 1/(60+rank_sparse)
│                  │  → Up to 40 unique candidates
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Step 4: Cross-  │  cross-encoder/ms-marco-MiniLM-L-6-v2 (22M params)
│  Encoder Rerank  │  → Scores each (question, chunk) pair jointly
│                  │  → Keeps top 5 by relevance score
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Step 5: Answer  │  GPT-3.5-turbo generates grounded answer
│  Generation      │  → Uses ONLY the top 5 chunks as context
│                  │  → Cites page numbers for source attribution
└─────────────────┘
```

### RAG Quality Monitoring (RAGAS)

Every chat response is evaluated asynchronously using the RAGAS framework:

| Metric | Target | Description |
|--------|--------|-------------|
| Faithfulness | > 0.85 | Does the answer contain only information from retrieved chunks? |
| Answer Relevancy | > 0.80 | Does the answer actually address the question? |
| Context Recall | > 0.75 | Did retrieval surface the right chunks? |

---

## 🧠 Fine-Tuned Models

### 1. LLaMA 3.1 8B — Financial Ratio Extraction

| Property | Value |
|----------|-------|
| **Base Model** | `NousResearch/Meta-Llama-3.1-8B-Instruct` |
| **Method** | QLoRA (4-bit NF4 quantization + Low-Rank Adaptation) |
| **LoRA Config** | rank=16, alpha=32, target_modules=[q_proj, v_proj, k_proj, o_proj], dropout=0.05 |
| **Training Data** | FinanceBench (PatronusAI) — financial QA pairs from real 10-K/10-Q filings |
| **Training** | 3 epochs, lr=2e-4, effective batch size=16, cosine scheduler |
| **Training Time** | ~14 minutes on T4 GPU (Google Colab) |
| **Training Loss** | 1.2108 |
| **Inference Format** | GGUF Q4_K_M (~4.9GB) + GGUF-LoRA adapter (~27MB) via llama-cpp-python |
| **Inference Hardware** | CPU-only (no GPU required) |

**Why QLoRA?** Full fine-tuning of an 8B parameter model requires ~64GB GPU memory. QLoRA reduces this to ~5GB by quantizing the base model to 4-bit and training only small adapter matrices (~130K trainable params per layer vs 16.7M for the full matrix). The adapter weights are only 54MB — not the full 16GB model.

### 2. FinBERT Sentiment — Financial Sentiment Classification

| Property | Value |
|----------|-------|
| **Base Model** | `ProsusAI/finbert` (110M parameters) |
| **Task** | 3-class classification (positive / neutral / negative) |
| **Training Data** | Financial PhraseBank — 4,840 human-labeled financial sentences |
| **Accuracy** | **95.37%** on held-out test set |
| **Training** | 5 epochs, lr=2e-5, batch size=16 |
| **Inference** | Standard PyTorch CPU (no quantization needed — only 418MB) |

### 3. FinBERT Breach — Covenant Breach Detection

| Property | Value |
|----------|-------|
| **Base Model** | `ProsusAI/finbert` (110M parameters) |
| **Task** | 2-class classification (breach / no-breach) |
| **Training Data** | Labeled covenant clauses from SEC EDGAR 10-K filings |
| **Inference** | Standard PyTorch CPU (418MB) |

---

## 📊 XGBoost Credit Risk Model

| Property | Value |
|----------|-------|
| **Algorithm** | XGBoost Gradient Boosted Trees |
| **Training Data** | LendingClub Loan Dataset (2M+ real loan records with actual default outcomes) |
| **Features** | 5 financial ratios: DSCR, Leverage Ratio, Interest Coverage, Current Ratio, Net Profit Margin |
| **Target** | Binary classification — probability of debt default (0.0–1.0) |
| **Explainability** | SHAP (SHapley Additive exPlanations) — per-feature contribution values |
| **Hyperparameters** | n_estimators=300, max_depth=6, learning_rate=0.05, scale_pos_weight for class imbalance |

### Risk Tier Mapping

| Score Range | Tier | Color |
|-------------|------|-------|
| 0.00 – 0.30 | 🟢 Low Risk | Green |
| 0.30 – 0.55 | 🟡 Medium Risk | Amber |
| 0.55 – 0.75 | 🔴 High Risk | Red |
| 0.75 – 1.00 | ⛔ Distress | Dark Red |

### Missing Value Handling

When LLaMA cannot extract a ratio from the document (e.g., DSCR not mentioned), the XGBoost model uses **median imputation** — the training set median for that feature is substituted. The imputed features are recorded in the `imputed_features` JSONB column and displayed on the frontend so analysts know which values are real vs. estimated.

---

## 🛡️ Authentication, RBAC & Multi-Tenancy

### JWT Authentication Flow

```
Login → bcrypt verify → Issue Access Token (15 min) + Refresh Token (7 days)
                              │
                              ▼
                   Every API Request:
                   Authorization: Bearer {access_token}
                              │
                              ▼
                   Validate JWT signature
                   + Check Redis blacklist (DB 3)
                   + Extract tenant_id
                              │
                              ▼
                   Filter ALL queries by tenant_id
```

- **Access token:** 15-minute TTL, stored in frontend memory (not localStorage — prevents XSS)
- **Refresh token:** 7-day TTL, stored in httpOnly cookie (prevents JavaScript access — CSRF protection)
- **Logout:** Access token JTI added to Redis blacklist with TTL = remaining lifetime
- **Password reset:** Cryptographic token via email, SHA256 hashed in DB, 15-minute expiry, single-use

### 4-Role RBAC Hierarchy

| Role | Scope | Capabilities |
|------|-------|-------------|
| **Superadmin** | Platform-wide | View all tenants, suspend/restore companies, manage LLM configs, view all usage/billing |
| **Tenant Admin** | Company-level | Manage users, view all company documents/reports, view company billing |
| **Analyst** | Company-level | Upload documents, trigger AI pipeline, view reports, use RAG chat |
| **Viewer** | Company-level | View reports and use RAG chat only (read-only) |

### Multi-Tenant Isolation

Every database query is filtered by `tenant_id`. A user from Company A can never see, access, or even know about Company B's data. This isolation is enforced at the ORM level — not just the API level.

---

## 🗄️ Database Architecture

### PostgreSQL — 18 Tables (7 Groups)

```
┌─────────────────────────────────────────────────────┐
│              GROUP 1: IDENTITY & ACCESS              │
│  superadmins · tenants · users · refresh_tokens     │
│  audit_logs · password_reset_tokens                  │
├─────────────────────────────────────────────────────┤
│              GROUP 2: DOCUMENT PIPELINE              │
│  documents · processing_jobs · document_chunks       │
├─────────────────────────────────────────────────────┤
│              GROUP 3: AGENT OUTPUTS                  │
│  extracted_ratios · sentiment_results                │
│  breach_results · risk_scores                        │
├─────────────────────────────────────────────────────┤
│              GROUP 4: FINAL OUTPUT                   │
│  reports                                             │
├─────────────────────────────────────────────────────┤
│              GROUP 5: RAG CHAT                       │
│  chat_sessions · chat_messages                       │
├─────────────────────────────────────────────────────┤
│              GROUP 6: TOKEN USAGE & BILLING          │
│  token_usage_events · monthly_usage_summaries        │
├─────────────────────────────────────────────────────┤
│              GROUP 7: SYSTEM CONFIG                  │
│  llm_configurations                                  │
└─────────────────────────────────────────────────────┘
```

All primary keys are UUID. All timestamps are TIMESTAMPTZ (timezone-aware). Alembic manages all schema migrations with versioned, reversible scripts.

### Redis — 5 Logical Databases

| DB | Purpose | Key Pattern | TTL |
|----|---------|-------------|-----|
| 0 | Celery task queue | Managed by Celery | None |
| 1 | Dead letter queue | `dlq:{job_id}` | 30 days |
| 2 | Application cache | `cache:{endpoint}:{hash}` | 5 min |
| 3 | JWT blacklist | `blacklist:{jti}` | Token remaining lifetime |
| 4 | Rate limiting | `rate:{user_id}:{endpoint}` | 1 hour sliding window |

### Qdrant — Vector Database

- **Collection per tenant** for strict data isolation
- **Dual vectors per chunk:** Dense (768-dim BGE financial) + Sparse (BM25)
- **Payload:** document_id, tenant_id, chunk_index, page_number, section, has_table, raw text

### MinIO — Object Storage

- S3-compatible, self-hosted
- Bucket: `finsight-documents`
- Key pattern: `{tenant_id}/{document_id}/{filename}.pdf`

---

## 🐳 Docker Infrastructure — 10 Containers

| # | Container | Image | Purpose |
|---|-----------|-------|---------|
| 1 | Nginx | `nginx:alpine` | Reverse proxy, load balancer, SSL termination, static file server |
| 2 | FastAPI | Custom `Dockerfile.api` | API server (1 Gunicorn worker + Uvicorn) |
| 3 | Celery Worker | Custom `Dockerfile.worker` | Async document processing with LangGraph pipeline |
| 4 | Redis | `redis:7-alpine` | Queue broker, cache, JWT blacklist, rate limiter |
| 5 | PostgreSQL | `postgres:16-alpine` | Relational database (18 tables) |
| 6 | Qdrant | `qdrant/qdrant:v1.9.1` | Vector database (dense + sparse) |
| 7 | MinIO | `minio/minio:latest` | PDF object storage |
| 8 | Prometheus | `prom/prometheus:v2.51.0` | Metrics collection (15-second scrape interval) |
| 9 | Grafana | `grafana/grafana:10.4.0` | Monitoring dashboards |
| 10 | Flower | `mher/flower:2.0.1` | Celery task monitoring UI |

All containers communicate on a shared Docker network (`finsight_network`). Database containers use named volumes for data persistence. Health checks ensure dependent services wait for databases to be ready before starting.

---

## ☸️ Kubernetes & Autoscaling

Kubernetes manifests are validated on Minikube and ready for AWS EKS production deployment.

### KEDA-Driven Autoscaling

```yaml
# When Redis queue depth > 5, KEDA adds more Celery worker pods
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
spec:
  scaleTargetRef:
    name: celery-worker
  minReplicaCount: 1
  maxReplicaCount: 10
  triggers:
  - type: redis
    metadata:
      listName: celery
      listLength: "5"
```

### Manifest Files

| File | Purpose |
|------|---------|
| `k8s/deployment-api.yaml` | FastAPI with 2 replicas, resource limits, liveness/readiness probes |
| `k8s/deployment-worker.yaml` | Celery worker with 2 initial replicas |
| `k8s/deployment-nginx.yaml` | Nginx with 1 replica |
| `k8s/service-api.yaml` | ClusterIP service for FastAPI |
| `k8s/service-nginx.yaml` | LoadBalancer service for external traffic |
| `k8s/hpa-worker.yaml` | KEDA ScaledObject for auto-scaling workers |
| `k8s/configmap.yaml` | Non-sensitive environment variables |
| `k8s/secret.yaml` | Passwords and API keys (base64) |

---

## 📈 Monitoring & Observability

### Prometheus Custom Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `finsight_document_processing_duration_seconds` | Histogram | Total pipeline time per document |
| `finsight_agent_duration_seconds{agent}` | Histogram | Per-agent processing time |
| `finsight_rag_faithfulness_score` | Gauge | RAGAS faithfulness per chat query |
| `finsight_queue_depth` | Gauge | Waiting jobs in Redis queue |
| `finsight_llm_tokens_total{model}` | Counter | Running token counter per model |
| `finsight_risk_tier_distribution{tier}` | Counter | Count of each risk tier predicted |

### Grafana Dashboards (4)

1. **Pipeline Health** — processing latency, success/failure rates, queue depth
2. **RAG Quality** — faithfulness, relevancy, context recall over time
3. **Token Usage & Cost** — per-tenant and per-model breakdown
4. **Business Metrics** — risk tier distribution, documents processed per day

### LangSmith (Development)

LangSmith tracing is enabled during development — shows every LangGraph agent step, exact prompts, responses, token counts, and latency. Disabled in production where Prometheus + Grafana take over.

---

## ⚡ Async Processing — Celery & Redis

### Why Async is Required

PDF processing takes 4–8 minutes. HTTP connections timeout after 30–120 seconds. Celery solves this by decoupling the upload request from the processing pipeline.

### The Flow

```
User Upload → FastAPI stores PDF in MinIO
            → Creates processing_jobs row (status: queued)
            → Enqueues Celery task to Redis DB 0
            → Returns HTTP 202 {job_id, status: "queued"} immediately
            
Frontend polls GET /jobs/{job_id}/status every 5 seconds

Celery Worker picks up task → Runs LangGraph pipeline
                            → Updates current_agent field at each step
                            → Frontend shows real-time progress

On completion → status: "completed" → Frontend loads report
On failure (3 retries) → Dead letter queue (Redis DB 1) → Alert
```

### Dead Letter Queue

After 3 failed retries (exponential backoff: 30s → 60s → 120s), jobs route to Redis DB 1 with 30-day retention. A Prometheus alert fires. The user sees "Processing failed. Please try uploading again."

---

## 🎨 Frontend

Built with **React 18 + Vite + TailwindCSS + Framer Motion + Recharts + Zustand**.

### Design Philosophy

Modern dark-first financial analytics platform. Primary color: deep crimson `#C62828`. Full of purposeful animations using Framer Motion.

### Key Pages

| Page | Highlights |
|------|-----------|
| **Login / Register** | Glassmorphism cards on animated particle background |
| **Dashboard** | Real-time job status cards, risk tier donut chart, recent reports |
| **Document Upload** | Drag-and-drop with live upload progress ring |
| **Processing View** | Animated 6-agent pipeline timeline with live status updates |
| **Report View** | Animated risk gauge, ratio cards, sentiment bar chart, breach alerts, SHAP chart, GPT-4 summary |
| **RAG Chat** | Floating panel with streaming answers and source page citations |
| **Admin Panel** | User management, usage analytics |
| **Superadmin Portal** | Cross-tenant management, per-company token usage breakdown |

### Color System

| Token | Value | Usage |
|-------|-------|-------|
| Primary | `#C62828` | Deep Crimson — buttons, accents |
| Accent | `#1565C0` | Electric Blue — positive indicators |
| Background | `#0A0A0B` | Near-black |
| Surface | `#141416` | Card backgrounds |
| Success | `#2E7D32` | Low risk |
| Warning | `#F57F17` | Medium risk |
| Danger | `#C62828` | High risk |
| Distress | `#880E4F` | Critical risk |

---

## 🛠️ Complete Technology Stack

### Backend

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| Web Framework | FastAPI | 0.111.0 | Async API server |
| ASGI Server | Uvicorn + Gunicorn | 0.29.0 + 22.0.0 | Production server |
| ORM | SQLAlchemy | 2.0.29 | PostgreSQL ORM |
| Migrations | Alembic | 1.13.1 | Schema versioning |
| Task Queue | Celery | 5.3.6 | Async processing |
| Agent Framework | LangGraph | 0.0.55 | Multi-agent orchestration |
| LLM Framework | LangChain | 0.2.0 | LLM integrations |
| LLM Inference | llama-cpp-python | 0.3.20 | CPU-optimized GGUF inference |
| PDF Parsing | PyMuPDF | 1.24.2 | Text + table extraction |
| Text Splitting | spaCy | 3.8.3 | Sentence-aware chunking |
| Dense Embeddings | BAAI/bge-base-financial | via sentence-transformers | 768-dim vectors |
| Sparse Embeddings | fastembed | 0.3.6 | BM25 vectors |
| Re-ranking | cross-encoder/ms-marco-MiniLM | via sentence-transformers | 22M param cross-encoder |
| ML Model | XGBoost | 2.0.3 | Credit risk classification |
| Explainability | SHAP | 0.45.0 | Feature importance |
| RAG Evaluation | RAGAS | 0.1.9 | Faithfulness, relevancy scores |

### Frontend

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| Framework | React | 18.x | UI framework |
| Build Tool | Vite | 5.x | Fast dev server + build |
| Styling | TailwindCSS | 3.x | Utility CSS |
| Animations | Framer Motion | 11.x | Page and component animations |
| Charts | Recharts | 2.x | Risk gauges, sentiment charts |
| State | Zustand | 4.x | Frontend state management |

### Infrastructure

| Category | Technology | Purpose |
|----------|-----------|---------|
| Containerization | Docker + Compose | 10-container production stack |
| Reverse Proxy | Nginx | SSL, load balancing, static files |
| Orchestration | Kubernetes (Minikube) | HPA manifests with KEDA autoscaling |
| CI/CD | GitHub Actions | Automated test → build → deploy |
| Cloud | AWS EC2 (t3.xlarge) | 16GB RAM, 4 vCPUs, production host |
| Monitoring | Prometheus + Grafana | Metrics collection + dashboards |
| Tracing | LangSmith | Development-only agent tracing |

### Databases

| Database | Technology | Purpose |
|----------|-----------|---------|
| Relational | PostgreSQL 16 | 18 tables, multi-tenant, RBAC |
| Cache/Queue | Redis 7 | 5 logical DBs (queue, DLQ, cache, blacklist, rate limit) |
| Vector | Qdrant 1.9.1 | Dense + sparse hybrid search |
| Object Storage | MinIO | PDF file storage (S3-compatible) |

---

## 🚀 Deployment

### Live Instance

| Property | Value |
|----------|-------|
| **URL** | [http://65.0.114.221](http://65.0.114.221) |
| **API Docs** | [http://65.0.114.221/api/docs](http://65.0.114.221/api/docs) |
| **Instance** | AWS EC2 t3.xlarge (16GB RAM, 4 vCPUs) |
| **Region** | Asia Pacific (Mumbai) ap-south-1 |
| **OS** | Ubuntu 24.04 LTS |
| **Storage** | 50GB gp3 SSD |

### Quick Deploy (Single Command)

```bash
# Clone the repository
git clone https://github.com/mohamedsahadm786/finsight-ai.git
cd finsight-ai

# Configure environment
cp .env.example .env
# Edit .env with your values

# Start all 10 containers
docker-compose up -d

# Run database migrations
docker exec finsight-api alembic -c backend/alembic.ini upgrade head

# Seed initial data
docker exec finsight-api python scripts/seed_llm_config.py
docker exec finsight-api python scripts/create_superadmin.py
```

### Model Files (Not in Git — Too Large)

The following model files must be copied to the `models/` directory:

| File | Size | Source |
|------|------|--------|
| `Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf` | 4.9 GB | [HuggingFace (bartowski)](https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF) |
| `finsight-lora-adapter.gguf` | 27 MB | Fine-tuned in Google Colab, converted with llama.cpp |
| `finbert-sentiment/` | 418 MB | Fine-tuned in Google Colab |
| `finbert-breach/` | 418 MB | Fine-tuned in Google Colab |
| `credit_risk_model.pkl` | 1.4 MB | Trained locally with XGBoost |

---

## 📂 Project Structure

```
finsight-ai/
├── .github/workflows/ci-cd.yml          # GitHub Actions CI/CD
├── backend/
│   ├── app/
│   │   ├── main.py                       # FastAPI application
│   │   ├── config.py                     # Pydantic settings
│   │   ├── api/                          # Route handlers
│   │   │   ├── auth.py                   # Login, register, refresh, logout
│   │   │   ├── documents.py              # Upload, list, status
│   │   │   ├── jobs.py                   # Processing job polling
│   │   │   ├── reports.py                # Report retrieval
│   │   │   ├── chat.py                   # RAG chat endpoint
│   │   │   ├── admin.py                  # Tenant admin routes
│   │   │   └── superadmin.py             # Platform admin routes
│   │   ├── models/                       # SQLAlchemy ORM models (18 tables)
│   │   ├── schemas/                      # Pydantic request/response schemas
│   │   ├── services/                     # Business logic layer
│   │   ├── dependencies/                 # FastAPI dependency injection
│   │   ├── database/                     # DB connection modules
│   │   ├── core/                         # Security, exceptions, metrics
│   │   └── middleware/                   # Tenant isolation middleware
│   ├── agents/                           # LangGraph 6-agent pipeline
│   │   ├── graph.py                      # LangGraph wiring
│   │   ├── agent_1_parser.py             # Document parser + Qdrant indexer
│   │   ├── agent_2_extractor.py          # LLaMA ratio extraction
│   │   ├── agent_3_sentiment.py          # FinBERT sentiment classification
│   │   ├── agent_4_breach.py             # FinBERT breach detection
│   │   ├── agent_5_risk_scorer.py        # XGBoost + SHAP scoring
│   │   └── agent_6_report_writer.py      # GPT-4 report generation
│   ├── rag/                              # Hybrid RAG pipeline
│   │   ├── hyde.py                       # HyDE implementation
│   │   ├── retriever.py                  # Hybrid Qdrant search
│   │   ├── fusion.py                     # Reciprocal Rank Fusion
│   │   ├── reranker.py                   # Cross-encoder re-ranking
│   │   ├── generator.py                  # Answer generation
│   │   └── evaluator.py                  # RAGAS evaluation
│   ├── tasks/                            # Celery async tasks
│   ├── tests/                            # pytest test suite
│   ├── migrations/                       # Alembic migrations
│   ├── Dockerfile.api                    # FastAPI container
│   └── Dockerfile.worker                 # Celery worker container
├── frontend/                             # React + Vite + TailwindCSS
│   ├── src/
│   │   ├── pages/                        # 10 page components
│   │   ├── components/                   # Reusable UI components
│   │   ├── store/                        # Zustand state management
│   │   └── api/                          # API client modules
├── models/                               # AI model artifacts (not in git)
├── docker/                               # Nginx, Prometheus, Grafana configs
├── k8s/                                  # Kubernetes manifests
├── scripts/                              # Admin scripts
├── docker-compose.yml                    # Production 10-container stack
├── docker-compose.dev.yml                # Development (databases only)
├── requirements.txt                      # Local Python dependencies
└── requirements.ec2.txt                  # EC2/production dependencies
```

---

## 🧪 Testing

```bash
# Run all tests
pytest backend/tests/ -v

# Run with coverage
pytest backend/tests/ --cov=backend --cov-report=html

# Run specific test module
pytest backend/tests/test_auth.py -v
```

Tests cover: authentication flows, RBAC enforcement, multi-tenant isolation, document upload, job status polling, report retrieval, RAG chat, and agent outputs.

---

## 🔮 Future Enhancements

- [ ] GPU-accelerated inference (AWS g4dn.xlarge with T4 GPU) for 10x faster LLaMA processing
- [ ] SSL/HTTPS with Let's Encrypt certbot
- [ ] Custom domain (e.g., finsight-ai.com)
- [ ] Real-time WebSocket updates (replace polling)
- [ ] PDF annotation overlay — highlight source passages directly on the PDF
- [ ] Multi-document comparison — compare risk profiles across companies
- [ ] Email notification when processing completes
- [ ] Export reports as PDF with charts and branding
- [ ] AWS EKS production Kubernetes deployment
- [ ] A/B testing of model versions via LLM configuration management

---

## 👤 Author

**Mohamed Sahad M**

- 🎓 MSc & BSc in Statistics
- 🔧 AI/ML Engineer specializing in NLP, LLMs, and production ML systems
- 📧 mohamedsahadm786@gmail.com
- 💼 [LinkedIn](https://www.linkedin.com/in/mohamed-sahad-m/)
- 💻 [Portfolio](https://d5qb6gsuemmzn.cloudfront.net/)

---

## 📄 License

This project represents a complete end-to-end AI system, covering LLaMA fine-tuning, system design, and containerized deployment using Docker.

---

<div align="center">

**Designed and implemented by Mohamed Sahad M with a strong focus on scalability, modular architecture, and real-world applicability.**

*AI-assisted development tools were leveraged to enhance development efficiency, debugging, and optimization workflows.*

</div>
