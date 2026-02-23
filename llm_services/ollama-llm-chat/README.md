# Ollama Chat Microservice

This directory contains the configuration for a local Ollama service dedicated to chat and text generation.

## 🚀 Getting Started

### 1. Start the Service
This service is part of the root `docker-compose.yml`.
```bash
docker-compose up -d ollama-llm-chat
```

### 2. Verify Readiness
The container automatically pulls the **tinyllama** model on its first launch.
```bash
# Follow logs to see download progress
docker-compose logs -f ollama-llm-chat
```

## 🔌 API Usage

To chat with the model, use the `/api/chat` endpoint.

### Example Request (Port 11436)
Default model: `tinyllama`

```bash
curl http://localhost:11436/api/chat -d '{
  "model": "tinyllama",
  "messages": [{"role": "user", "content": "Hi! Explain quantum computing to a 5 year old."}],
  "stream": false
}'
```

### Response Format
The response will be a JSON object containing the interaction:
```json
{
  "model": "tinyllama",
  "created_at": "...",
  "message": {
    "role": "assistant",
    "content": "..."
  },
  "done": true
}
```

## 📂 Data & Persistence
Model data is stored in the `./ollama-llm-chat/data` directory on the host machine. This ensures that models are not re-downloaded when the container is restarted or recreated.
