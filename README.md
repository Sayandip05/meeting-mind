# Meeting Intelligence System

**Why do meetings waste 4 hours daily instead of summaries?**

Corporate employees spend half their workday in back-to-back status meetings, planning discussions, and review calls that could be replaced by brief written updates if they had AI-powered real-time meeting transcription and summarization tools optimized to understand Indian accents and business context.

---

## Vision

Transform meetings from time-wasters into searchable knowledge. This is a production-grade AI application that converts meeting recordings into structured insights, replacing endless status meetings with intelligent summaries and on-demand Q&A.

---

## Architecture Overview

### Target Architecture: Modular Monolith (Layered)

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Landing Page │  │  Auth Pages  │  │   React Dashboard    │   │
│  │   (Next.js)  │  │ (SignUp/In)  │  │  (TypeScript/React)  │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                         API GATEWAY LAYER                        │
│                    FastAPI - Modular Routers                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │  Auth    │ │ Meetings │ │  Chat    │ │ Highlights│ │ Admin  │ │
│  │  Router  │ │  Router  │ │  Router  │ │  Router   │ │ Router │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                        SERVICE LAYER                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │Auth Service  │  │Meeting Svc   │  │  AI Agent Service    │   │
│  │(JWT/SQLite)  │  │(Orchestration)│  │ (LangGraph + LangSmith)│  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      REPOSITORY LAYER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  User Repo   │  │ Meeting Repo │  │   Vector Store Repo  │   │
│  │  (SQLite)    │  │  (SQLite)    │  │    (Qdrant Docker)   │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                     INFRASTRUCTURE LAYER                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │   Whisper    │  │SentenceTrans │  │     Groq LLM         │   │
│  │(Indian Accent│  │  (Embeddings)│  │  (via LangChain)     │   │
│  │  Optimized)  │  │              │  │                      │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Backend (Python)
| Component | Technology |
|-----------|------------|
| Framework | FastAPI |
| Database | SQLite (dev) → PostgreSQL (prod) |
| Vector DB | Qdrant (Docker) |
| AI Orchestration | LangGraph |
| Tracing | LangSmith |
| Auth | JWT + bcrypt |
| Testing | pytest |
| Transcription | OpenAI Whisper (Indian accent optimized) |
| Embeddings | SentenceTransformers |
| LLM | Groq (via LangChain) |

### Frontend
| Component | Technology |
|-----------|------------|
| Landing Page | Next.js / React |
| Dashboard | React + TypeScript |
| Styling | Tailwind CSS |
| State Management | React Query / Zustand |
| Auth | JWT stored in httpOnly cookies |

### DevOps
| Component | Technology |
|-----------|------------|
| Containerization | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| Monitoring | LangSmith tracing |

---

## Project Structure (Target)

```
Meeting_Intelligence_System/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry
│   │   ├── config.py               # Settings & env vars
│   │   │
│   │   ├── api/                    # API Layer (Routers)
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # Auth endpoints
│   │   │   ├── meetings.py         # Meeting CRUD
│   │   │   ├── chat.py             # Chat endpoints
│   │   │   ├── highlights.py       # Highlights endpoints
│   │   │   └── admin.py            # Super admin endpoints
│   │   │
│   │   ├── core/                   # Core Layer
│   │   │   ├── __init__.py
│   │   │   ├── security.py         # JWT, password hashing
│   │   │   └── exceptions.py       # Custom exceptions
│   │   │
│   │   ├── services/               # Service Layer
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── meeting_service.py
│   │   │   └── ai_agent_service.py # LangGraph agents
│   │   │
│   │   ├── repositories/           # Repository Layer
│   │   │   ├── __init__.py
│   │   │   ├── user_repository.py
│   │   │   ├── meeting_repository.py
│   │   │   └── vector_repository.py
│   │   │
│   │   ├── models/                 # Database Models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   └── meeting.py
│   │   │
│   │   ├── schemas/                # Pydantic Schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── meeting.py
│   │   │   └── chat.py
│   │   │
│   │   └── agents/                 # LangGraph Agents
│   │       ├── __init__.py
│   │       ├── transcription_agent.py
│   │       ├── summarization_agent.py
│   │       ├── highlights_agent.py
│   │       └── chat_agent.py
│   │
│   ├── tests/                      # pytest tests
│   │   ├── __init__.py
│   │   ├── test_auth.py
│   │   ├── test_meetings.py
│   │   └── conftest.py
│   │
│   ├── alembic/                    # Database migrations
│   ├── uploads/                    # Meeting uploads
│   ├── data/                       # SQLite data
│   ├── requirements.txt
│   └── pytest.ini
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── auth/               # Login, Signup forms
│   │   │   ├── dashboard/          # Main dashboard
│   │   │   ├── meeting/            # Meeting view
│   │   │   └── admin/              # Super admin dashboard
│   │   ├── pages/
│   │   │   ├── landing.tsx
│   │   │   ├── login.tsx
│   │   │   ├── signup.tsx
│   │   │   ├── dashboard.tsx
│   │   │   └── admin.tsx
│   │   ├── hooks/
│   │   ├── services/               # API clients
│   │   ├── store/                  # State management
│   │   └── types/                  # TypeScript types
│   ├── package.json
│   └── tsconfig.json
│
├── qdrant_data/                    # Qdrant persistence
├── .env.example
├── .gitignore
└── README.md
```

---

## User Flows

### 1. Landing → Authentication → Dashboard

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Landing   │────▶│   Sign Up   │────▶│   Sign In   │────▶│  Dashboard  │
│    Page     │     │   (Form)    │     │   (Form)    │     │  (React UI) │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### 2. Meeting Lifecycle

```
Upload/Record ──▶ Transcribe ──▶ Chunk & Embed ──▶ Store in Qdrant
                                              │
                                              ▼
Ask Questions ◀── Chat Agent ◀── Retrieve ◀───┘
                                              │
Generate Summary ◀── Highlights Agent ◀───────┘
```

### 3. Super Admin Flow

```
Admin Dashboard:
├── View all users
├── View all meetings
├── System analytics
├── Manage settings
└── View LangSmith traces
```

---

## Database Schema (SQLite → PostgreSQL)

### Users Table
```sql
users:
- id (PK)
- email (unique)
- hashed_password
- full_name
- is_active
- is_superadmin
- created_at
- updated_at
```

### Meetings Table
```sql
meetings:
- id (PK)
- user_id (FK)
- name
- original_filename
- audio_path
- transcript_path
- status (uploaded/processing/completed/failed)
- created_at
- updated_at
```

### Qdrant Collections
```
meetings_{meeting_id}  # Per-meeting vector collection
```

---

## AI Agent Architecture (LangGraph)

```
┌─────────────────────────────────────────────────────────────┐
│                    TRANSCRIPTION AGENT                       │
│  Input: Audio → Whisper (Indian accent optimized) → Text    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    CHUNKING AGENT                            │
│  Input: Text → Semantic chunking → Chunks                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    EMBEDDING AGENT                           │
│  Input: Chunks → SentenceTransformers → Embeddings          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    STORAGE AGENT                             │
│  Input: Embeddings → Qdrant (per-meeting collection)        │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────────┐
│   HIGHLIGHTS AGENT      │     │      CHAT AGENT             │
│  (LangGraph Workflow)   │     │   (LangGraph + Memory)      │
│                         │     │                             │
│  1. Multi-query retrieval│     │  1. Receive question        │
│  2. Deduplicate chunks   │     │  2. Retrieve context        │
│  3. Groq summarization   │     │  3. Groq generate answer    │
│  4. Format highlights    │     │  4. Update memory           │
└─────────────────────────┘     └─────────────────────────────┘
```

---

## Key Features

### Phase 1: Foundation
- [ ] Modular monolith architecture (layered)
- [ ] User authentication (JWT, SQLite)
- [ ] Landing page + Auth pages
- [ ] React TypeScript dashboard
- [ ] File upload/record meetings

### Phase 2: AI Pipeline
- [ ] Whisper transcription (Indian accent optimization)
- [ ] Semantic chunking
- [ ] Qdrant vector storage (Docker)
- [ ] LangGraph agent orchestration
- [ ] LangSmith tracing

### Phase 3: Intelligence
- [ ] Highlights generation agent
- [ ] Conversational Q&A with memory
- [ ] Real-time transcription streaming
- [ ] Speaker diarization

### Phase 4: Production
- [ ] Docker + Docker Compose
- [ ] pytest test suite
- [ ] Super admin dashboard
- [ ] PostgreSQL migration path
- [ ] CI/CD pipeline

---

## Environment Variables

```bash
# Backend
DATABASE_URL=sqlite:///./data/app.db
QDRANT_HOST=localhost
QDRANT_PORT=6333
GROQ_API_KEY=your_key_here
LANGSMITH_API_KEY=your_key_here
LANGSMITH_PROJECT=meeting-intelligence
JWT_SECRET=your_secret_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Running with Docker

```bash
# Start all services
docker-compose up -d

# Services:
# - Backend: http://localhost:8000
# - Frontend: http://localhost:3000
# - Qdrant: http://localhost:6333
```

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_auth.py -v
```

---

## Indian Accent Optimization Strategy

1. **Whisper Fine-tuning**: Use Whisper models with Indian English training data
2. **Post-processing**: Domain-specific vocabulary correction
3. **Context Enhancement**: Business terminology injection
4. **Fallback**: Manual transcript editing capability

---

## Migration from Current State

### Current → Target

| Current | Target |
|---------|--------|
| Flat structure | Layered modular monolith |
| Vanilla JS frontend | React + TypeScript |
| No auth | JWT-based auth |
| Chroma DB | Qdrant (Docker) |
| LangChain | LangGraph + LangSmith |
| No tests | pytest suite |
| No Docker | Full containerization |

---

## Resume Description (Updated)

> Architected and built a production-grade Meeting Intelligence System using modular monolith architecture, featuring LangGraph-powered AI agents, Qdrant vector database, React TypeScript frontend, and Docker containerization. Reduced corporate meeting overhead by transforming recordings into searchable knowledge with Indian accent-optimized transcription and intelligent summarization.

