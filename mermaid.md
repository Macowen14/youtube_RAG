# Backend Architecture Graphs

This document describes the current backend architecture for YouTube Better, including the main modules, how requests flow from the frontend to external systems, and the clean architecture boundaries that separate concerns.

## High-Level Architecture

```mermaid
graph TD
    Frontend[Frontend App]
    FastAPI[FastAPI App]
    SupabaseAuth[Supabase Auth / JWT Verification]

    subgraph "API Layer"
        RagRouter[/src/api/routers/rag.py/]
        NotesRouter[/src/api/routers/notes.py/]
        SummariesRouter[/src/api/routers/summaries.py/]
        Schemas[/src/api/schemas.py/]
        Dependencies[/src/api/dependencies.py/]
    end

    subgraph "Application Layer"
        RAGService[YouTubeRAGService]
        NoteService[NoteService]
        SummaryService[SummaryService]
    end

    subgraph "Domain Layer"
        Ports[ports.py]
        Models[models.py]
    end

    subgraph "Infrastructure Layer"
        Auth[auth/security.py]
        DB[database/db.py]
        DBModels[database/db_models.py]
        Transcript[YtDlpTranscriptProvider]
        Chunker[LangChainTextChunker]
        KnowledgeBase[PineconeVideoKnowledgeBase]
        LLM[OpenAIRAGGenerator]
        Config[config.py]
    end

    Frontend -- "Authorization: Bearer <JWT>" --> FastAPI
    FastAPI --> SupabaseAuth
    SupabaseAuth -->|user_id| RagRouter
    SupabaseAuth -->|user_id| NotesRouter
    SupabaseAuth -->|user_id| SummariesRouter

    RagRouter --> Dependencies
    NotesRouter --> NoteService
    SummariesRouter --> SummaryService

    Dependencies --> RAGService
    RAGService --> Transcript
    RAGService --> Chunker
    RAGService --> KnowledgeBase
    RAGService --> LLM

    NoteService --> DB
    SummaryService --> DB
    NoteService --> DBModels
    SummaryService --> DBModels
    NotesRouter --> DB
    SummariesRouter --> DB

    Frontend -->|Supabase Auth token| SupabaseAuth
    RAGService -->|embedded video chunks| KnowledgeBase
    RAGService -->|AI prompt & response| LLM
    Transcript -->|YouTube subtitles| Frontend
```

## How the Backend Works

### 1. Application startup
- `main.py` configures the environment and starts the FastAPI server.
- `src/api/app.py` creates the FastAPI app, configures CORS and rate limiting, registers routers, and runs Alembic migrations on startup.
- `src/bootstrap.py` wires concrete infrastructure adapters into the `YouTubeRAGService` using the protocol abstractions in `src/domain/ports.py`.

### 2. Authentication
- Every protected endpoint depends on `src.infrastructure.auth.security.get_current_user`.
- JWT validation is done against Supabase using:
  - JWKS verification for `ES256`/`RS256`, or
  - HS256 verification using `SUPABASE_JWT_SECRET`, or
  - Supabase Auth `/auth/v1/user` endpoint fallback.
- The authenticated Supabase `user_id` is passed into route handlers.

### 3. RAG ingestion and query flow
- `POST /rag/ingest` calls `YouTubeRAGService.ingest_video(video_id)`.
- Transcript provider (`YtDlpTranscriptProvider`) fetches YouTube subtitles via `yt-dlp` and HTTP.
- `LangChainTextChunker` splits transcript text into overlapping chunks.
- `PineconeVideoKnowledgeBase` embeds chunks locally with Ollama and upserts them to Pinecone under the video namespace.

### 4. Question answering and generation flow
- `POST /rag/query` and `POST /rag/generate-notes` / `POST /rag/generate-summary` all use the same service pipeline.
- The knowledge base searches for relevant chunks for `video_id` and query/topic.
- Selected chunks are combined into a context string.
- `OpenAIRAGGenerator` sends a structured prompt to OpenAI using `ChatOpenAI`.
- The response is returned as `RAGResult(answer, source)`.

### 5. Notes and summaries persistence
- `NoteService` and `SummaryService` both use `src.infrastructure.database.db.get_db()`.
- Persistent storage is managed through SQLAlchemy and PostgreSQL.
- `DBNote` and `DBSummary` tables store `user_id`, `video_id`, `content`, and `created_at`.

## Sequence Diagram: Request to Response

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant API as FastAPI
    participant Auth as Supabase Auth
    participant RAG as YouTubeRAGService
    participant KB as Pinecone KB
    participant LLM as OpenAI
    participant DB as PostgreSQL

    FE->>API: POST /rag/query
    API->>Auth: verify JWT
    Auth-->>API: return user_id
    API->>RAG: ask_question(video_id, question)
    RAG->>KB: search(video_id, query)
    KB-->>RAG: relevant chunks
    RAG->>LLM: answer_question(context, question)
    LLM-->>RAG: structured answer
    RAG-->>API: RAGResult
    API-->>FE: ResponseModel(answer, source)

    FE->>API: POST /notes/
    API->>Auth: verify JWT
    API->>DB: create note
    DB-->>API: saved note
    API-->>FE: NoteResponse
```

## Clean Architecture Map

```mermaid
classDiagram
    class FastAPI_App {
        +create_app()
        +CORS
        +rate limiting
        +startup migrations
    }
    class RouterRAG {
        +ingest_video()
        +query_video()
        +generate_notes()
        +generate_summary()
    }
    class RouterNotes {
        +create_note()
        +get_notes()
        +get_note()
    }
    class RouterSummaries {
        +create_summary()
        +get_summaries()
        +get_summary()
    }
    class YouTubeRAGService {
        +ingest_video()
        +ask_question()
        +generate_notes()
        +generate_summary()
    }
    class NoteService {
        +create_note()
        +get_notes()
        +get_note_by_id()
    }
    class SummaryService {
        +create_summary()
        +get_summaries()
        +get_summary_by_id()
    }
    class DomainPorts {
        +TranscriptProvider
        +TextChunker
        +VideoKnowledgeBase
        +RAGGenerator
    }
    class DB {
        +SessionLocal
        +get_db()
    }
    class PineconeKB {
        +has_video()
        +add_video_chunks()
        +search()
    }
    class OpenAI_Generator {
        +answer_question()
        +generate_notes()
    }
    class TranscriptProvider {
        +fetch_transcript()
    }

    FastAPI_App --> RouterRAG
    FastAPI_App --> RouterNotes
    FastAPI_App --> RouterSummaries
    RouterRAG --> YouTubeRAGService
    RouterNotes --> NoteService
    RouterSummaries --> SummaryService
    YouTubeRAGService --> DomainPorts
    YouTubeRAGService --> PineconeKB
    YouTubeRAGService --> OpenAI_Generator
    YouTubeRAGService --> TranscriptProvider
    NoteService --> DB
    SummaryService --> DB
    PineconeKB --> DB
```

## Notes
- The backend uses a dependency inversion strategy: concrete adapters are assembled in `src/bootstrap.py`, while the rest of the code depends on protocols in `src/domain/ports.py`.
- Supabase Auth is used for authentication only; user data persists in PostgreSQL via SQLAlchemy.
- The RAG pipeline combines transcript retrieval, local embedding, vector search, and OpenAI structured generation.
