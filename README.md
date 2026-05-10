# YouTube RAG Backend

A FastAPI-based application that provides a robust, multi-user backend for the YouTube Better project. Built using **Clean Architecture**, it offers a Retrieval-Augmented Generation (RAG) system for YouTube videos, storing transcript embeddings in **Pinecone** and answering questions using **OpenAI**. It also supports personalized user notes and video summaries, fully backed by **Supabase Auth** and **Neon PostgreSQL**.

## Features

- **Multi-User Authentication**: Protected endpoints using Supabase JWT verification.
- **Video Ingestion**: Fetches and splits YouTube video transcripts (`POST /rag/ingest`).
- **Q&A**: Ask questions about the video content (`POST /rag/query`).
- **Notes & Summaries Generation**: Use OpenAI models to generate notes (`POST /rag/generate-notes`) and summaries (`POST /rag/generate-summary`).
- **Personalized Storage**: Full CRUD endpoints for users to manage their own notes (`/notes`) and summaries (`/summaries`) backed by SQLAlchemy + Neon PostgreSQL.
- **Model Selection**: Choose between OpenAI models (e.g. `gpt-5.4-mini`, `gpt-5-mini`) per request or use the server default.
- **Local Embeddings**: Uses Ollama's `qwen3-embedding:0.6b` model locally for fast, free 1024-dim vector embeddings.
- **Serverless Vector Search**: Pinecone serverless with cosine similarity for transcript chunk retrieval.
- **Automated Migrations**: Alembic runs automatically on startup via `start.sh`.
- **Rate Limiting**: Protects all endpoints from abuse using `slowapi`.

## Architecture

The app is organized around strict **Clean Architecture** boundaries with a **split-provider** strategy:

```text
src/
  api/              FastAPI app factory, endpoint routers, Pydantic schemas
  application/      Use cases orchestrating logic (RAG, Notes, Summaries)
  domain/           Core data models and dependency port interfaces
  infrastructure/
    auth/           JWT verification via Supabase Auth (HTTPS)
    database/       SQLAlchemy ORM + Neon PostgreSQL
    llm/            OpenAI RAG generator
    vectorstores/   Pinecone + Ollama embeddings
    transcripts/    YouTube transcript fetcher (yt-dlp)
  bootstrap.py      Composition root — wires adapters to ports
```

### Provider Responsibilities

| Provider | Role | Protocol |
|---|---|---|
| **Supabase Auth** | JWT issuance & verification | HTTPS (no DB dependency) |
| **Neon PostgreSQL** | Relational data (notes, summaries, migrations) | TCP/SSL |
| **Pinecone** | Vector storage & similarity search | HTTPS |
| **Ollama** | Local embedding generation (`qwen3-embedding:0.6b`) | Local HTTP |
| **OpenAI** | LLM inference (Q&A, note generation) | HTTPS |

> [!NOTE]
> Auth and database are fully decoupled. Supabase provides user identity
> (JWT → `user_id`), which is stored as a plain string column in Neon
> PostgreSQL. Swapping either provider requires no changes to the other.

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) running locally (for the `qwen3-embedding:0.6b` embedding model).
- An **OpenAI API key**.
- A **Pinecone** account with a serverless index (1024-dim, cosine metric).
- A **Neon** PostgreSQL database.
- A **Supabase** project (for authentication only).
- `uv` (recommended) or `pip` for dependency management.

## Installation

1.  **Clone the repository** and navigate to the `backend` directory.

2.  **Install dependencies**:

    ```bash
    uv sync
    ```

3.  **Pull the embedding model** (one-time setup):

    ```bash
    ollama pull qwen3-embedding:0.6b
    ```

4.  **Environment Setup**:
    Copy the example and fill in your credentials:

    ```bash
    cp .env.example .env
    ```

    ```env
    # External API Keys
    PINECONE_API_KEY=your-pinecone-api-key
    PINECONE_INDEX_NAME=youtuberag
    OPENAI_API_KEY=your-openai-api-key

    # Database (Neon PostgreSQL)
    DATABASE_URL=postgresql://user:pass@ep-xxx.region.aws.neon.tech/neondb?sslmode=require

    # Authentication (Supabase Auth — HTTPS only, no DB dependency)
    SUPABASE_URL=https://your-project-ref.supabase.co
    SUPABASE_JWT_SECRET=your-supabase-jwt-secret
    SUPABASE_KEY=your-supabase-publishable-key

    # LLM Configuration
    MODEL_NAME=gpt-5.4-mini
    APP_LOG_FILE=logs/app.log
    PORT=8080
    ```

## Running the Application

The recommended way to start is via the bootstrap script, which runs Alembic migrations before launching the server:

```bash
bash start.sh
```

Or run directly (skipping the migration step):

```bash
uv run main.py
```

Interactive documentation (Swagger UI) is available at `http://localhost:8080/docs`.

### Configuration

| Environment Variable | Description | Default |
|---|---|---|
| `OPENAI_API_KEY` | Your OpenAI API key | *(required)* |
| `MODEL_NAME` | Default OpenAI model | `gpt-5.4-mini` |
| `PINECONE_API_KEY` | Pinecone API key | *(required)* |
| `PINECONE_INDEX_NAME` | Pinecone serverless index name | `youtuberag` |
| `DATABASE_URL` | Neon PostgreSQL connection string | *(required)* |
| `SUPABASE_URL` | Supabase project URL (auth only) | *(required)* |
| `SUPABASE_KEY` | Supabase publishable/anon key | *(required)* |
| `SUPABASE_JWT_SECRET` | Supabase JWT secret for token verification | *(required)* |
| `APP_LOG_FILE` | Log file path | `logs/app.log` |
| `PORT` | Server port | `8080` |

## API Endpoints

### 1. RAG Operations (Protected & Rate Limited)
- **POST** `/rag/ingest` - Ingests a YouTube video
- **POST** `/rag/query` - Ask the LLM a question about the video
- **POST** `/rag/generate-notes` - Generate comprehensive notes
- **POST** `/rag/generate-summary` - Generate a quick summary

RAG request bodies accept an optional `model_name` field to override the server default:

```json
{
  "video_id": "VIDEO_ID",
  "question": "What is the main point?",
  "model_name": "gpt-5-mini"
}
```

### 2. User Notes (Protected)
- **POST** `/notes/` - Save a generated note
- **GET** `/notes/` - Get all notes for the authenticated user (optional `?video_id=...`)
- **GET** `/notes/{note_id}` - Get a specific note

### 3. User Summaries (Protected)
- **POST** `/summaries/` - Save a generated summary
- **GET** `/summaries/` - Get all summaries for the authenticated user (optional `?video_id=...`)
- **GET** `/summaries/{summary_id}` - Get a specific summary
