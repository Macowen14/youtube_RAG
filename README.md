# YouTube RAG Backend

A FastAPI-based application that provides a robust, multi-user backend for the YouTube Better project. Built using **Clean Architecture**, it offers a Retrieval-Augmented Generation (RAG) system for YouTube videos, storing transcripts in a vector database (ChromaDB) and answering questions using Ollama. It also supports personalized user notes and video summaries, fully backed by **Supabase Auth** and **PostgreSQL**.

## Features

- **Multi-User Authentication**: Protected endpoints using Supabase JWT verification.
- **Video Ingestion**: Fetches and splits YouTube video transcripts (`POST /rag/ingest`).
- **Q&A**: Ask questions about the video content (`POST /rag/query`).
- **Notes & Summaries Generation**: Use LLMs to generate notes (`POST /rag/generate-notes`) and summaries (`POST /rag/generate-summary`).
- **Personalized Storage**: Full CRUD endpoints for users to manage their own notes (`/notes`) and summaries (`/summaries`) backed by SQLAlchemy.
- **Dynamic LLM Host**: Automatically switches between local (`localhost`) and cloud (`ollama.com`) Ollama hosts based on the model name.
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
  infrastructure/   Adapters for DB (SQLAlchemy), Auth (PyJWT/Supabase), LLMs, Vector DBs
  bootstrap.py      Dependency wiring
```

For detailed architectural graphs and diagrams, please refer to the `mermaid.md` file.

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) running locally (for local models).
- **Supabase** Project (For PostgreSQL Database and Authentication).
- `uv` (recommended) or `pip` for dependency management.

## Installation

1.  **Clone the repository** and navigate to the `backend` directory.

2.  **Install dependencies**:

    ```bash
    # Using uv (recommended)
    uv sync
    ```

3.  **Environment Setup**:
    Create a `.env` file in the `backend/` directory:
    ```env
    DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres
    SUPABASE_JWT_SECRET=your-supabase-jwt-secret
    OLLAMA_HOST=http://localhost:11434
    ```

## Running the Application

Start the FastAPI server:

```bash
# Using uv and uvicorn
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8060
```

### Production Deployment

For production, use the provided `start.sh` script which utilizes **Gunicorn** with Uvicorn workers for better performance and concurrency:

```bash
./start.sh
```

Interactive documentation (Swagger UI) is available at `http://localhost:8060/docs`.

## API Endpoints

### 1. RAG Operations (Protected & Rate Limited)
- **POST** `/rag/ingest` - Ingests a YouTube video
- **POST** `/rag/query` - Ask the LLM a question about the video
- **POST** `/rag/generate-notes` - Generate comprehensive notes
- **POST** `/rag/generate-summary` - Generate a quick summary

### 2. User Notes (Protected)
- **POST** `/notes/` - Save a generated note
- **GET** `/notes/` - Get all notes for the authenticated user (optional `?video_id=...`)
- **GET** `/notes/{note_id}` - Get a specific note

### 3. User Summaries (Protected)
- **POST** `/summaries/` - Save a generated summary
- **GET** `/summaries/` - Get all summaries for the authenticated user (optional `?video_id=...`)
- **GET** `/summaries/{summary_id}` - Get a specific summary

### 4. Admin
- **GET** `/logs/download` - Downloads the server logs as a `.zip` file.
