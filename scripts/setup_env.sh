#!/bin/bash
# Setup .env file with Ollama configuration

ENV_FILE=".env"

echo "Setting up .env file for Ollama (Llama3)..."
echo ""

# Check if .env already exists
if [ -f "$ENV_FILE" ]; then
    echo "⚠️  .env file already exists."
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted. Existing .env file preserved."
        exit 0
    fi
fi

# Create .env file
cat > "$ENV_FILE" << 'EOF'
# LLM Provider Configuration
# Options: openai, azure, local
LLM_PROVIDER=local

# Local LLM Configuration (Ollama for Llama3)
# Ollama is already running on the system
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3
USE_MOCK_LLM=false

# OpenAI Configuration (uncomment if switching to OpenAI)
# OPENAI_API_KEY=sk-proj-...
# OPENAI_MODEL=gpt-4o-mini

# Azure OpenAI Configuration (uncomment if switching to Azure)
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
# AZURE_OPENAI_KEY=your-key-here
# AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# vLLM Configuration (alternative to Ollama, uncomment if using vLLM)
# VLLM_SERVER_URL=http://localhost:8000/v1
# VLLM_MODEL=meta-llama/Meta-Llama-3-8B-Instruct

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# Storage Configuration
UPLOAD_DIR=./uploads
VERSION_STORE_PATH=./versions
EOF

echo "✅ .env file created successfully!"
echo ""
echo "Configuration:"
echo "  - LLM Provider: local (Ollama)"
echo "  - Ollama URL: http://localhost:11434"
echo "  - Model: llama3"
echo ""
echo "To test the configuration, run:"
echo "  python scripts/test_llm_config.py"
echo ""

