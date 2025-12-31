# YouTube RAG Backend

A FastAPI-based application that creates a Retrieval-Augmented Generation (RAG) system for YouTube videos. It fetches transcripts, stores them in a vector database (ChromaDB), and allows users to ask questions or generate notes based on the video content using Ollama.

## Features

- **Video Ingestion**: Fetches and splits YouTube video transcripts (`POST /ingest`).
- **Q&A**: Ask questions about the video content (`POST /query`).
- **Note Generation**: Generate comprehensive notes on specific topics (`POST /notes`).
- **Dynamic LLM Host**: Automatically switches between local (`localhost`) and cloud (`ollama.com`) Ollama hosts based on the model name.
- **Log Management**: Download application logs as a zip file (`GET /logs/download`).

> [!NOTE] > **Vector Database**: This project currently uses **ChromaDB** running locally for storing vector embeddings. However, the architecture is modular (via LangChain), and you can easily substitute it with a cloud-based service like **Pinecone**, **Weaviate**, or **Milvus** by updating the vector store initialization in `rag_service.py`.

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) running locally (for local models).
- `uv` or `pip` for dependency management.

## Installation

1.  **Clone the repository** and navigate to the `youtube_RAG` directory.

2.  **Install dependencies**:

    ```bash
    # Using uv (recommended)
    uv sync

    # OR using pip
    pip install -r requirements.txt
    ```

    _Note: If `requirements.txt` is missing, dependencies are defined in `pyproject.toml`._

3.  **Environment Setup**:
    Create a `.env` file (optional if using defaults):
    ```env
    OLLAMA_HOST=http://localhost:11434
    ```

## Running the Application

Start the FastAPI server:

```bash
# Direct python execution
python main.py

# OR using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.
Interactive documentation (Swagger UI) is available at `http://localhost:8000/docs`.

## API Endpoints

### 1. Ingest Video

**POST** `/ingest`

```json
{
	"video_id": "dQw4w9WgXcQ"
}
```

### 2. Query Video

**POST** `/query`

```json
{
	"video_id": "dQw4w9WgXcQ",
	"question": "What is the main message?",
	"model_name": "mistral-large-3:675b-cloud"
}
```

_Note: If `model_name` contains "cloud", the system connects to `https://ollama.com/`._

### 3. Generate Notes

**POST** `/notes`

```json
{
	"video_id": "dQw4w9WgXcQ",
	"topic": "Key Takeaways",
	"model_name": "llama3"
}
```

### 4. Download Logs

**GET** `/logs/download`
Downloads the server logs as a `.zip` file.
