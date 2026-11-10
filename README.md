# AI-Powered News Translation from Kannada to English

An end-to-end, verified **Translate-Then-Summarize** news intelligence system designed specifically for Kannada language news feeds, user-submitted articles, and research evaluation.

---

## 📌 Project Overview

This project implements a verified machine translation and summarization pipeline:
1. **Ingest & Extract**: RSS feed ingestion & user-submitted Kannada text with Unicode NFC normalization and Indic-aware sentence boundary detection.
2. **Translate First**: Kannada-to-English translation powered by **IndicTrans2** (with pluggable Sarvam, LLM, and offline Mock baselines).
3. **Translation Guards**: Multi-check context preservation (Number consistency, Named Entities, Date/Month normalization, and Length ratios).
4. **Structured Summarization**: Abstractive summary generation producing strict JSON with citations linking claims directly to source sentence IDs.
5. **Faithfulness Verification**: 7-layer verification guarding against hallucinations with claim entailment, entity cross-matching against the Kannada original, and extractive fallback.
6. **Dual Presentation**: Interactive Next.js web application offering side-by-side sentence-aligned reader, flagged discrepancy inspection, reading history, and analytics.

---

## 🏛️ System Architecture

```text
Browser (Next.js UI)
    |  HTTPS, REST / SSE
    v
FastAPI Backend (/api/v1) <================> PostgreSQL 16 (JSONB + FTS)
    | (Enqueues job into pipeline_jobs)             ^
    v                                               | (Writes processed data)
AI Worker (Background loop) ========================+
    |--> ML: IndicTrans2 / Mock Translator
    |--> Guards: Numbers, Entities, Alignment
    |--> LLM: Gemini / Local / Extractive Fallback
    +--> Categorizer & NER
```

---

## 📁 Repository Structure

```text
kannada-news-ai/
├── docker-compose.yml           # Complete container stack (db, api, worker, web)
├── .env.example                 # Environment configuration template
├── Makefile                     # Developer lifecycle commands
├── README.md                    # Project documentation
├── docs/                        # Architecture, ethics, and eval documentation
│   ├── architecture.md
│   ├── ethics.md
│   └── eval-protocol.md
├── apps/
│   ├── web/                     # Next.js (App Router, Tailwind CSS, shadcn/ui)
│   └── api/                     # FastAPI backend application
├── services/
│   ├── worker/                  # Background worker & pipeline stages
│   ├── ml/                      # Kannada NLP, Translation & LLM connectors
│   └── collector/               # News fetcher, RSS parser & crawler politeness
├── scripts/
│   ├── demo_articles.json       # Fixed test Kannada news articles
│   ├── seed.py                  # Database seed utility
│   └── bench_translation.py     # Evaluation benchmark script
└── eval/                        # Benchmarks, datasets, and human evaluation tools
```

---

## 🚀 Quickstart

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ or Docker & Docker Compose

### 1. Configure Environment
```bash
cp .env.example .env
```

### 2. Using Docker Compose
```bash
docker compose up -d
```

### 3. Local Development (Without Docker)
1. **Start PostgreSQL** and ensure `DATABASE_URL` is set in `.env`.
2. **Setup Backend & Worker**:
   ```bash
   cd apps/api
   pip install -r requirements.txt
   alembic upgrade head
   uvicorn app.main:app --reload --port 8000
   ```
3. **Run AI Worker**:
   ```bash
   cd services/worker
   python worker.py
   ```
4. **Setup Web Frontend**:
   ```bash
   cd apps/web
   npm install
   npm run dev
   ```

---

## 📊 Milestone Roadmap

| Milestone | Description | Status |
|---|---|---|
| **M0** | Repository setup, Docker Compose, workspace configs | In Progress |
| **M1** | Database schema, SQLAlchemy models, Alembic migrations | Next |
| **M2** | Frontend layout, design system & mock data rendering | Planned |
| **M3** | RSS news collection, crawler politeness & article extraction | Planned |
| **M4** | IndicTrans2 translation integration with quality guards | Planned |
| **M5** | Grounded JSON summarization & multi-layer faithfulness check | Planned |
| **M6** | Background worker orchestration with DB queue | Planned |
| **M7** | Named entity recognition, category classification & search | Planned |
| **M8** | KannadaNews-Eval dataset & research evaluation harness | Planned |
| **M9** | Comprehensive test suite & error hardening | Planned |
| **M10** | Production deployment setup | Planned |
| **M11** | Research paper experiments, demo presentation | Planned |
