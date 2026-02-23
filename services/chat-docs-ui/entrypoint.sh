#!/bin/sh

# Default value if not set
: "${CHAT_API_URL:=http://localhost:8003/ask_llm_model}"

echo "🔧 Injecting API URL: $CHAT_API_URL"

# Replace the placeholder in the JS file
# We use a temporary file to avoid issues with busy files
sed -i "s|__CHAT_API_URL__|$CHAT_API_URL|g" /usr/share/nginx/html/script.js

echo "🚀 Starting Nginx..."
exec "$@"
