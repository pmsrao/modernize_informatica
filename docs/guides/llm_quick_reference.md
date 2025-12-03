# LLM Configuration Quick Reference

Quick reference for configuring LLM providers.

---

## OpenAI (Cloud)

```bash
# Set environment variables
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-proj-...

# Or in .env file
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini
```

**Get API Key**: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

---

## Azure OpenAI (Enterprise)

```bash
# Set environment variables
export LLM_PROVIDER=azure
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
export AZURE_OPENAI_KEY=your-key-here
export AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# Or in .env file
LLM_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_KEY=your-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
```

---

## Local Llama3 (Ollama) - Recommended

### Setup

```bash
# 1. Install Ollama
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.com/install.sh | sh
# Windows: Download from https://ollama.com/download

# 2. Start Ollama
ollama serve

# 3. Pull Llama3 (in another terminal)
ollama pull llama3
```

### Configuration

```bash
# Set environment variables
export LLM_PROVIDER=local
export OLLAMA_URL=http://localhost:11434
export OLLAMA_MODEL=llama3
export USE_MOCK_LLM=false

# Or in .env file
LLM_PROVIDER=local
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3
USE_MOCK_LLM=false
```

### Verify Ollama is Running

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Test with a prompt
curl http://localhost:11434/api/generate -d '{
  "model": "llama3",
  "prompt": "Say hello",
  "stream": false
}'
```

---

## Local Llama3 (vLLM)

### Setup

```bash
# 1. Install vLLM
pip install vllm

# 2. Start vLLM server (requires GPU)
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Meta-Llama-3-8B-Instruct \
  --port 8000
```

### Configuration

```bash
# Set environment variables
export LLM_PROVIDER=local
export VLLM_SERVER_URL=http://localhost:8000/v1
export VLLM_MODEL=meta-llama/Meta-Llama-3-8B-Instruct
export USE_MOCK_LLM=false

# Or in .env file
LLM_PROVIDER=local
VLLM_SERVER_URL=http://localhost:8000/v1
VLLM_MODEL=meta-llama/Meta-Llama-3-8B-Instruct
USE_MOCK_LLM=false
```

---

## Test Configuration

```bash
# Quick test
python -c "
from llm.llm_manager import LLMManager
llm = LLMManager()
print('Provider:', llm.client.__class__.__name__)
response = llm.ask('Say hello in one sentence')
print('Response:', response)
"
```

---

## Common Issues

### "Connection refused" (Ollama)
- **Fix**: Start Ollama: `ollama serve`

### "Model not found" (Ollama)
- **Fix**: Pull model: `ollama pull llama3`

### "API key not found" (OpenAI)
- **Fix**: Set `OPENAI_API_KEY` environment variable

### "Falling back to mock"
- **Fix**: Check provider configuration and service status

---

## Switching Providers

Just change `LLM_PROVIDER`:

```bash
# Switch to OpenAI
export LLM_PROVIDER=openai

# Switch to Local (Llama3)
export LLM_PROVIDER=local
```

Restart the application after changing providers.

---

For detailed configuration, see [LLM Configuration Guide](llm_configuration.md).

