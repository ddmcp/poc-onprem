#!/usr/bin/env bash

# Use nomic-embed-text by default if not specified
MODEL_NAME=${OLLAMA_MODEL:-nomic-embed-text}

echo "🚀 Starting Ollama..."
/bin/ollama serve &
pid=$!

# Wait for server to be responsive
echo "⏳ Waiting for server to be ready..."
until ollama list >/dev/null 2>&1; do
  sleep 1
done

# Check if model exists
if ! ollama list | grep -q "$MODEL_NAME"; then
  echo "🔽 Downloading model '$MODEL_NAME'..."
  ollama pull "$MODEL_NAME"
fi

# Run a quick verification if it's not a known pure embedding model
# Embedding models can still respond to 'run' but let's make it brief
echo "🧪 Running verification query for '$MODEL_NAME'..."
ollama run "$MODEL_NAME" "hi" --verbose false

echo "✅ Ollama is ready and model '$MODEL_NAME' is active."

# Keep the process running
wait $pid
