# YouTube RAG Backend

A FastAPI-based application that provides a robust, multi-user backend for the YouTube Better project. Built using **Clean Architecture**, it offers a Retrieval-Augmented Generation (RAG) system for YouTube videos, storing transcripts in a vector database (ChromaDB) and answering questions using **OpenAI**. It also supports personalized user notes and video summaries, fully backed by **Supabase Auth** and **PostgreSQL**.

## Features

- **Multi-User Authentication**: Protected endpoints using Supabase JWT verification.
- **Video Ingestion**: Fetches and splits YouTube video transcripts (`POST /rag/ingest`).
- **Q&A**: Ask questions about the video content (`POST /rag/query`).
- **Notes & Summaries Generation**: Use OpenAI models to generate notes (`POST /rag/generate-notes`) and summaries (`POST /rag/generate-summary`).
- **Personalized Storage**: Full CRUD endpoints for users to manage their own notes (`/notes`) and summaries (`/summaries`) backed by SQLAlchemy.
- **Model Selection**: Choose between OpenAI models (e.g. `gpt-5.4-mini`, `gpt-5-mini`) per request or use the server default.
- **Local Embeddings**: Uses Ollama's `qwen3-embedding:0.6b` model locally for fast, free vector embeddings via ChromaDB.
- **Rate Limiting**: Protects all endpoints from abuse using `slowapi`.

> [!NOTE] 
> **Vector Database**: This project currently uses **ChromaDB** running locally for storing vector embeddings. The architecture is modular, and you can substitute it with a cloud-based service like Pinecone or Weaviate by updating the `VideoKnowledgeBase` adapter.

## Architecture

The app is organized around strict **Clean Architecture** boundaries:

```text
src/
  api/              FastAPI app initialization, endpoint routers, schemas
  application/      Use cases orchestrating logic (RAG, Notes, Summaries)
  domain/           Core data models and dependency interfaces
  infrastructure/   Adapters for DB (SQLAlchemy), Auth (PyJWT/Supabase), LLM (OpenAI), Vector DB (ChromaDB)
  bootstrap.py      Dependency wiring
```

For detailed architectural graphs and diagrams, please refer to the `mermaid.md` file.

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) running locally (required for the `qwen3-embedding:0.6b` embedding model only).
- An **OpenAI API key**.
- **Supabase** Project (For PostgreSQL Database and Authentication).
- `uv` (recommended) or `pip` for dependency management.

## Installation

1.  **Clone the repository** and navigate to the `backend` directory.

2.  **Install dependencies**:

    ```bash
    # Using uv (recommended)
    uv sync
    ```

3.  **Pull the embedding model** (one-time setup):

    ```bash
    ollama pull qwen3-embedding:0.6b
    ```

4.  **Environment Setup**:
    Create a `.env` file in the `backend/` directory:
    ```env
    DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres
    SUPABASE_URL=https://your-project-ref.supabase.co
    SUPABASE_KEY=your-supabase-publishable-or-anon-key
    SUPABASE_JWT_SECRET=your-supabase-jwt-secret
    OPENAI_API_KEY=your-openai-api-key
    MODEL_NAME=gpt-5.4-mini
    APP_LOG_FILE=logs/app.log
    CHROMA_PERSIST_DIRECTORY=db
    PORT=8080
    ```

## Running the Application

Start the FastAPI server:

```bash
# Using uv
uv run main.py
```

Interactive documentation (Swagger UI) is available at `http://localhost:8080/docs`.

### Configuration

| Environment Variable | Description | Default |
|---|---|---|
| `OPENAI_API_KEY` | Your OpenAI API key | *(required)* |
| `MODEL_NAME` | Default OpenAI model | `gpt-5.4-mini` |
| `DATABASE_URL` | PostgreSQL connection string | *(required)* |
| `SUPABASE_URL` | Supabase project URL | *(required)* |
| `SUPABASE_KEY` | Supabase publishable/anon key | *(required)* |
| `SUPABASE_JWT_SECRET` | Supabase JWT secret for token verification | *(required)* |
| `CHROMA_PERSIST_DIRECTORY` | ChromaDB storage path | `db` |
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
