# Backend Architecture Graphs

Below are the architectural diagrams illustrating the core structures and flows of the YouTube Better backend.

## System Overview & Flow

```mermaid
graph TD
    Client[Frontend Application]
    FastAPI[FastAPI Application]
    AuthMiddleware[Auth Middleware / Dependency]
    
    subgraph "API Layer (Routers)"
        RouterRAG[RAG Router]
        RouterNotes[Notes Router]
        RouterSummaries[Summaries Router]
    end
    
    subgraph "Application Layer (Services)"
        ServiceRAG[YouTube RAG Service]
        ServiceNotes[Note Service]
        ServiceSummaries[Summary Service]
    end
    
    subgraph "Infrastructure Layer (Adapters)"
        DB[(PostgreSQL via SQLAlchemy)]
        VectorDB[(ChromaDB)]
        LLM[Ollama / Cloud LLM]
        TranscriptAPI[yt-dlp / YouTube Transcripts]
    end
    
    Client -- "Bearer JWT" --> FastAPI
    FastAPI --> AuthMiddleware
    
    AuthMiddleware -- "Valid User ID" --> RouterRAG
    AuthMiddleware -- "Valid User ID" --> RouterNotes
    AuthMiddleware -- "Valid User ID" --> RouterSummaries
    
    RouterRAG --> ServiceRAG
    RouterNotes --> ServiceNotes
    RouterSummaries --> ServiceSummaries
    
    ServiceRAG --> VectorDB
    ServiceRAG --> LLM
    ServiceRAG --> TranscriptAPI
    
    ServiceNotes --> DB
    ServiceSummaries --> DB
```

## Clean Architecture Boundaries

```mermaid
classDiagram
    class API {
        +routers/rag.py
        +routers/notes.py
        +routers/summaries.py
        +schemas.py
        +app.py
    }
    
    class Application {
        +services.py
        +YouTubeRAGService
        +NoteService
        +SummaryService
    }
    
    class Domain {
        +models.py
        +ports.py
        +Note
        +Summary
        +RAGResult
    }
    
    class Infrastructure {
        +auth/security.py
        +database/db.py
        +database/db_models.py
        +llm/ollama_client.py
        +vectorstores/chroma.py
    }

    Infrastructure ..> Domain : "Implements Ports / Uses Models"
    Application ..> Domain : "Uses Models"
    API ..> Application : "Calls Services"
    API ..> Infrastructure : "Injects Dependencies"
```
