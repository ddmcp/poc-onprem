# Ollama Embedding Microservice

This directory contains the configuration for a local Ollama service dedicated to generating text embeddings.

## 🚀 Getting Started

### 1. Start the Service
This service is part of the root `docker-compose.yml`.
```bash
docker-compose up -d ollama-llm-embedding
```

### 2. Verify Readiness
The container automatically pulls the **nomic-embed-text** model on its first launch.
```bash
# Follow logs to see download progress
docker-compose logs -f ollama-llm-embedding
```

## 🔌 API Usage

To convert text into a numerical vector (embedding), use the `/api/embeddings` endpoint.

### Example Request (Port 11434)
Default model: `nomic-embed-text`

```bash
curl http://localhost:11434/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "The sky is blue because of Rayleigh scattering."
}'
```

### Response Format
The response will be a JSON object containing the `embedding` array:
```json
{
  "embedding": [
    0.0123,
    -0.0456,
    0.0789,
    ...
  ]
}
```

## 📂 Data & Persistence
Model data is stored in the `./ollama-llm-embedding/data` directory on the host machine. This ensures that models are not re-downloaded when the container is restarted or recreated.
