# 🏎️ Pagani Zonda R – Enterprise Intelligence

> A full-stack AI-powered enterprise system featuring RAG (Retrieval-Augmented Generation), role-based access control, and a cinematic car showcase experience.

[![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Gemini](https://img.shields.io/badge/Gemini-AI-4285F4?logo=google)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🤖 **RAG-Powered Chat** | AI assistant with hybrid search (semantic + keyword), streaming responses, and agentic query routing |
| 🔐 **JWT Authentication** | Secure login with access/refresh token rotation and role-based access (Admin, Engineer, Viewer) |
| 🎬 **Cinematic Ignition** | Video-based intro experience with Framer Motion animations |
| 📊 **Admin Dashboard** | Executive-style dashboard with system metrics and AI query interface |
| 🔧 **Engineer Dashboard** | Technical console with engineering-focused data access |
| 🎯 **Role-Based Data** | Documents filtered by user role — admins see financials, engineers see technical specs |
| 💾 **Database Persistence** | SQLAlchemy ORM with PostgreSQL/SQLite for users, chat history, system logs, and analytics |
| 🛡️ **Security Hardening** | Security headers, rate limiting, request size limits, input sanitization, CORS |
| 📝 **Structured Logging** | Rotating file logs + DB persistence for all system events |
| 📈 **Analytics Tracking** | Non-invasive usage analytics for chat, login, and system events |
| 🐳 **Docker Ready** | docker-compose with frontend, backend, and PostgreSQL services |

---

## 🏗️ Architecture

```mermaid
graph TB
    subgraph Frontend["Next.js Frontend"]
        A[Ignition Experience] --> B[Auth Pages]
        B --> C[Dashboards]
        C --> D[Chat Assistant]
        D --> E["lib/api.ts<br/>Fetch + Auth + Sanitize"]
    end

    subgraph Backend["FastAPI Backend"]
        F[Auth Endpoints] --> G[JWT + bcrypt]
        H[Chat Endpoints] --> I[Agentic Router]
        I --> J[FAISS Hybrid Search]
        J --> K[Gemini LLM]
        L[Health Monitor]
    end

    subgraph Data["Data Layer"]
        M[(PostgreSQL/SQLite)]
        N[(FAISS Vector Index)]
        O[Gemini API]
    end

    E -->|HTTP/SSE| F
    E -->|HTTP/SSE| H
    E -->|HTTP| L
    G --> M
    H --> M
    J --> N
    K --> O
    L --> M
```

---

## 🔄 System Workflow

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant API as FastAPI
    participant DB as Database
    participant VS as Vector Store
    participant LLM as Gemini

    U->>FE: Enter question
    FE->>FE: sanitizeInput()
    FE->>API: POST /api/chat/stream
    API->>API: Verify JWT token
    API->>LLM: Agentic Router (needs search?)
    LLM-->>API: {needs_search, search_query}
    API->>VS: Hybrid search (FAISS + keyword)
    VS-->>API: Relevant documents
    API->>LLM: Generate with context
    LLM-->>API: Stream tokens
    API-->>FE: SSE stream
    FE-->>U: Render markdown
    API->>DB: Persist chat history
    API->>DB: Track analytics
```

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+, Python 3.11+, Git

### Setup

```bash
# Clone
git clone https://github.com/Nischal-S143/EnterpriseRAG.git
cd EnterpriseRAG

# Frontend
npm install

# Backend
cd backend
pip install -r requirements.txt
# Configure backend/.env (see .env.example)
```

### Run

```bash
# Terminal 1: Backend
cd backend && python main.py

# Terminal 2: Frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

> See [docs/Setup.md](docs/Setup.md) for detailed setup instructions including Docker.

---

## 🧪 Testing

```bash
# Backend tests
cd backend && python -m pytest tests/ -v

# Frontend tests (when configured)
npm test
```

---

## 📁 Project Structure

```
├── app/                    # Next.js pages
│   ├── dashboard/          # Admin & Engineer dashboards
│   ├── login/              # Login page
│   ├── register/           # Registration page
│   └── page.tsx            # Home (Ignition + Scroll experience)
├── components/             # React components
│   ├── ChatAssistant.tsx   # AI chat with streaming + markdown
│   ├── IgnitionExperience.tsx
│   ├── Navbar.tsx
│   └── Zonda*.tsx          # Scroll animation components
├── lib/                    # Frontend utilities
│   ├── api.ts              # API client + input sanitization
│   ├── auth.ts             # Auth functions
│   └── logger.ts           # Debug logger
├── backend/                # FastAPI backend
│   ├── main.py             # API endpoints + middleware
│   ├── auth.py             # JWT auth + user management
│   ├── rag_pipeline.py     # RAG with Gemini + memory
│   ├── vector_store.py     # FAISS + hybrid search
│   ├── database.py         # SQLAlchemy config
│   ├── models.py           # DB models
│   ├── middleware.py        # Security middleware
│   ├── logging_config.py   # Structured logging
│   └── tests/              # pytest test suite
├── docs/                   # Documentation
│   ├── Architecture.md
│   ├── Setup.md
│   └── API.md
├── docker-compose.yml      # Docker multi-service config
└── .env.example            # Environment template
```

---

## 📚 Documentation

- [Architecture](docs/Architecture.md) – System design, data flow, component overview
- [Setup Guide](docs/Setup.md) – Local setup, Docker, environment variables
- [API Reference](docs/API.md) – All endpoint documentation

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 🔒 Security

See [SECURITY.md](SECURITY.md) for our security policy and reporting vulnerabilities.

## 📜 Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
