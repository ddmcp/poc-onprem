# PDF Text Searcher Microservice

A semantic search microservice that allows users to find information across processed PDF documents using vector embeddings and natural language queries.

## 🚀 Features

- **Semantic Search**: Find relevant text chunks even if keywords don't match exactly.
- **FastAPI Core**: High-performance API with automatic interactive documentation.
- **Qdrant Integration**: Efficient vector search powered by Qdrant.
- **LLM Embeddings**: Uses `sentence-transformers` (default: `all-MiniLM-L6-v2`) locally.

## 🛠 Setup & Running

The service is integrated into the main `docker-compose.yml`.

### Start the Service
```bash
docker-compose up -d text-searcher-microservice
```

### Access Documentation
- **Swagger UI**: [http://localhost:8003/docs](http://localhost:8003/docs)
- **Health Check**: [http://localhost:8003/health](http://localhost:8003/health)

## 📖 API Usage

### Search for Text
**Endpoint**: `POST /search`

**Request Body**:
```json
{
  "query": "machine learning",
  "limit": 3
}
```

**Example Request**:
```bash
curl -X POST "http://localhost:8003/search" \
     -H "Content-Type: application/json" \
     -d '{"query": "machine learning", "limit": 3}'
```

**Example Response**:
```json
[
  {
    "score": 0.852,
    "pdf_id": "uuid-123",
    "pdf_name": "ai_trends.pdf",
    "page_number": 5,
    "chunk_index": 12,
    "text_snippet": "Machine learning is a subset of AI that focuses on...",
    "chunk_id": "chunk-uuid-abc"
  }
]
```

## ⚙️ Configuration

The service uses environment variables defined in `.env.dev`.

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Name of the service | `text-searcher-microservice` |
| `EMBEDDING_MODEL` | HuggingFace model name | `all-MiniLM-L6-v2` |
| `QDRANT_HOST` | Qdrant host address | `qdrant-pdf-vector-db` |
| `QDRANT_PORT` | Qdrant HTTP port | `6333` |

## LLM Provider Configuration

The chat-docs-service supports multiple LLM providers through a flexible abstraction layer.

### Supported Providers

#### 1. Ollama (Default)
Uses a local Ollama instance for LLM inference.

**Configuration:**
```bash
LLM_PROVIDER=ollama  # or leave unset (default)
OLLAMA_CHAT_URL=http://ollama-llm-chat:11434
OLLAMA_CHAT_MODEL=gemma:2b
```

#### 2. OpenAI-Compatible Endpoints (vLLM Recommended)
Supports any OpenAI-compatible endpoint. **vLLM is the recommended option** for on-premises deployments, providing high-performance inference with the `ibm/granite-3-3-8b-instruct` model.

**Configuration:**
```bash
LLM_PROVIDER=openai-compatible
OPENAI_API_KEY=your-api-key-here
OPENAI_API_BASE_URL=http://your-vllm-endpoint:8000/v1  # vLLM endpoint
OPENAI_MODEL=ibm/granite-3-3-8b-instruct  # Default recommended model
OPENAI_TEMPERATURE=0
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_PROVIDER` | No | `ollama` | LLM provider: `ollama` or `openai-compatible` |
| `OLLAMA_CHAT_URL` | No | `http://ollama-llm-chat:11434` | Ollama service URL |
| `OLLAMA_CHAT_MODEL` | No | `gemma:2b` | Ollama model name |
| `OPENAI_API_KEY` | Yes* | - | API key for OpenAI-compatible endpoint (*required for openai-compatible) |
| `OPENAI_API_BASE_URL` | No | `http://your-vllm-endpoint:8000/v1` | Base URL for OpenAI-compatible API (vLLM recommended) |
| `OPENAI_MODEL` | No | `ibm/granite-3-3-8b-instruct` | Model name (vLLM with granite recommended) |
| `OPENAI_TEMPERATURE` | No | `0` | Temperature for response generation |

### Switching Providers

**Development (.env files):**
```bash
# For Ollama
LLM_PROVIDER=ollama

# For OpenAI-compatible (vLLM recommended)
LLM_PROVIDER=openai-compatible
OPENAI_API_KEY=your-api-key-here
OPENAI_API_BASE_URL=http://your-vllm-endpoint:8000/v1
OPENAI_MODEL=ibm/granite-3-3-8b-instruct
```

**Production (OpenShift):**
See the [OpenShift deployment documentation](../../openshift/README.md#llm-provider-configuration) for instructions on configuring providers in Kubernetes/OpenShift.

### Architecture

The service uses an abstract `LLMChatClient` interface with provider-specific implementations:
- `OllamaLLMClient`: Uses `langchain-ollama` (ChatOllama) for Ollama integration
- `OpenAICompatibleClient`: Uses `langchain-openai` (ChatOpenAI) for OpenAI-compatible endpoints

Both implementations use LangChain's unified interface for consistency. The factory pattern (`create_llm_client()`) instantiates the appropriate client based on the `LLM_PROVIDER` environment variable.

## 📂 Project Structure

```text
text-searcher-microservice/
├── main.py              # FastAPI application & endpoints
├── search_service.py    # Vector search logic
├── logger_config.py     # Logging configuration
├── requirements.txt     # Python dependencies
├── .env.dev             # Development configuration
└── Dockerfile           # Container definition
```
