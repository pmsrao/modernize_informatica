# LLM Configuration Guide

Complete guide for configuring OpenAI, Azure OpenAI, and local LLM (Llama3) providers.

---

## Table of Contents

1. [OpenAI Configuration](#openai-configuration)
2. [Azure OpenAI Configuration](#azure-openai-configuration)
3. [Local LLM Configuration (Llama3)](#local-llm-configuration-llama3)
4. [Environment Variables](#environment-variables)
5. [Configuration File](#configuration-file)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

---

## OpenAI Configuration

### Step 1: Get OpenAI API Key

1. **Sign up or log in** to your OpenAI account:
   - Go to [https://platform.openai.com](https://platform.openai.com)
   - Create an account or sign in

2. **Navigate to API Keys**:
   - Click on your profile icon (top right)
   - Select "API keys" from the menu
   - Or go directly to: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

3. **Create a new API key**:
   - Click "Create new secret key"
   - Give it a name (e.g., "Informatica Modernization")
   - **Copy the key immediately** - it won't be shown again!
   - Store it securely

### Step 2: Set Environment Variable

#### Option A: Export in Terminal (Temporary)

**Linux/macOS:**
```bash
export OPENAI_API_KEY="sk-proj-..."
export LLM_PROVIDER=openai
```

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="sk-proj-..."
$env:LLM_PROVIDER="openai"
```

**Windows (Command Prompt):**
```cmd
set OPENAI_API_KEY=sk-proj-...
set LLM_PROVIDER=openai
```

#### Option B: Add to `.env` File (Recommended)

Create a `.env` file in the project root:

```bash
# .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini
```

**Note**: Add `.env` to `.gitignore` to keep your API key secure!

### Step 3: Verify Configuration

```bash
# Start the API server
./start_api.sh

# In another terminal, test the configuration
python -c "
from llm.llm_manager import LLMManager
llm = LLMManager()
response = llm.ask('Say hello')
print('✅ OpenAI configured correctly!')
print(f'Response: {response[:50]}...')
"
```

### OpenAI API Key Format

- Starts with `sk-` (for standard keys) or `sk-proj-` (for project keys)
- Example: `sk-proj-abc123def456ghi789...`
- Keep it secret and never commit to version control

### OpenAI Models Available

- `gpt-4o-mini` (default) - Fast and cost-effective
- `gpt-4o` - More capable, higher cost
- `gpt-4-turbo` - High performance
- `gpt-3.5-turbo` - Legacy model

Change model via:
```bash
export OPENAI_MODEL=gpt-4o
```

---

## Azure OpenAI Configuration

### Step 1: Get Azure OpenAI Credentials

1. **Create Azure OpenAI Resource**:
   - Go to [Azure Portal](https://portal.azure.com)
   - Create a new "Azure OpenAI" resource
   - Note the endpoint URL (e.g., `https://your-resource.openai.azure.com`)

2. **Get API Key**:
   - In Azure Portal, go to your OpenAI resource
   - Navigate to "Keys and Endpoint"
   - Copy **Key 1** or **Key 2**

3. **Create Model Deployment**:
   - Go to "Model deployments" in Azure Portal
   - Create a new deployment (e.g., `gpt-4o-mini`)
   - Note the deployment name

### Step 2: Set Environment Variables

#### Option A: Export in Terminal

```bash
export LLM_PROVIDER=azure
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
export AZURE_OPENAI_KEY=your-key-here
export AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
```

#### Option B: Add to `.env` File

```bash
# .env
LLM_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_KEY=your-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
```

### Step 3: Verify Configuration

```bash
python -c "
from llm.llm_manager import LLMManager
llm = LLMManager()
response = llm.ask('Say hello')
print('✅ Azure OpenAI configured correctly!')
"
```

---

## Local LLM Configuration (Llama3)

### Option 1: Using Ollama (Recommended for Llama3)

Ollama is the easiest way to run Llama3 locally.

#### Step 1: Install Ollama

**macOS:**
```bash
brew install ollama
# Or download from https://ollama.com/download
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
- Download from [https://ollama.com/download](https://ollama.com/download)
- Run the installer

#### Step 2: Start Ollama and Pull Llama3

```bash
# Start Ollama service (runs on http://localhost:11434 by default)
ollama serve

# In another terminal, pull Llama3 model
ollama pull llama3

# Or for larger model:
ollama pull llama3:70b
```

#### Step 3: Verify Ollama is Running

```bash
# Test Ollama API
curl http://localhost:11434/api/generate -d '{
  "model": "llama3",
  "prompt": "Say hello",
  "stream": false
}'
```

#### Step 4: Configure Application

**Set Environment Variables:**

```bash
export LLM_PROVIDER=local
export OLLAMA_URL=http://localhost:11434
export OLLAMA_MODEL=llama3
export USE_MOCK_LLM=false
```

**Or add to `.env` file:**

```bash
# .env
LLM_PROVIDER=local
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3
USE_MOCK_LLM=false
```

#### Step 5: Verify Configuration

```bash
python -c "
from llm.llm_manager import LLMManager
llm = LLMManager()
response = llm.ask('Say hello')
print('✅ Ollama/Llama3 configured correctly!')
print(f'Response: {response[:50]}...')
"
```

### Option 2: Using vLLM Server

vLLM provides high-performance inference for local models.

#### Step 1: Install vLLM

```bash
pip install vllm
```

#### Step 2: Start vLLM Server with Llama3

```bash
# Start vLLM server (requires GPU)
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Meta-Llama-3-8B-Instruct \
  --port 8000

# Or if you have the model locally:
python -m vllm.entrypoints.openai.api_server \
  --model /path/to/llama3 \
  --port 8000
```

#### Step 3: Configure Application

```bash
export LLM_PROVIDER=local
export VLLM_SERVER_URL=http://localhost:8000/v1
export USE_MOCK_LLM=false
```

**Or in `.env`:**

```bash
# .env
LLM_PROVIDER=local
VLLM_SERVER_URL=http://localhost:8000/v1
USE_MOCK_LLM=false
```

### Llama3 Model Variants

- `llama3` - 8B parameter model (default, good balance)
- `llama3:70b` - 70B parameter model (more capable, requires more RAM)
- `llama3:8b-instruct` - Instruction-tuned version
- `llama3:70b-instruct` - Larger instruction-tuned version

Change model via:
```bash
export OLLAMA_MODEL=llama3:70b
```

---

## Environment Variables

### Complete List

| Variable | Description | Default | Required For |
|----------|-------------|---------|--------------|
| `LLM_PROVIDER` | Provider: `openai`, `azure`, or `local` | `openai` | All |
| `OPENAI_API_KEY` | OpenAI API key | - | OpenAI |
| `OPENAI_MODEL` | OpenAI model name | `gpt-4o-mini` | OpenAI |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | - | Azure |
| `AZURE_OPENAI_KEY` | Azure OpenAI API key | - | Azure |
| `AZURE_OPENAI_DEPLOYMENT` | Azure deployment name | `gpt-4o-mini` | Azure |
| `OLLAMA_URL` | Ollama server URL | `http://localhost:11434` | Local (Ollama) |
| `OLLAMA_MODEL` | Ollama model name | `llama3` | Local (Ollama) |
| `VLLM_SERVER_URL` | vLLM server URL | - | Local (vLLM) |
| `USE_MOCK_LLM` | Use mock responses | `false` | Testing |

---

## Configuration File

### Create `.env` File

Create a `.env` file in the project root:

```bash
# .env

# LLM Provider Selection
LLM_PROVIDER=local  # or 'openai' or 'azure'

# OpenAI Configuration (if using OpenAI)
# OPENAI_API_KEY=sk-proj-...
# OPENAI_MODEL=gpt-4o-mini

# Azure OpenAI Configuration (if using Azure)
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
# AZURE_OPENAI_KEY=your-key-here
# AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# Local LLM Configuration (if using local)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3
USE_MOCK_LLM=false

# Or for vLLM:
# VLLM_SERVER_URL=http://localhost:8000/v1
```

### Security Note

**Always add `.env` to `.gitignore`:**

```bash
# .gitignore
.env
*.env
.env.local
```

---

## Verification

### Quick Test Script

Create `test_llm_config.py`:

```python
#!/usr/bin/env python3
"""Test LLM configuration."""
import sys
from pathlib import Path

# Add paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

from llm.llm_manager import LLMManager

def test_llm():
    """Test LLM configuration."""
    try:
        print("Testing LLM configuration...")
        llm = LLMManager()
        
        print(f"✅ LLM Manager initialized")
        print(f"   Provider: {llm.client.__class__.__name__}")
        
        print("\nSending test prompt...")
        response = llm.ask("Say 'Hello, LLM is working!' in one sentence.")
        
        print(f"✅ LLM responded successfully!")
        print(f"   Response: {response}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_llm()
    sys.exit(0 if success else 1)
```

Run it:
```bash
python test_llm_config.py
```

---

## Troubleshooting

### OpenAI Issues

**Error: "OpenAI API key not found"**
- Solution: Set `OPENAI_API_KEY` environment variable
- Check: `echo $OPENAI_API_KEY` (should show your key)

**Error: "OpenAI API call failed: Invalid API key"**
- Solution: Verify your API key is correct
- Check: Key starts with `sk-` or `sk-proj-`
- Regenerate key if needed

**Error: "Rate limit exceeded"**
- Solution: Wait a few minutes or upgrade your OpenAI plan
- Check: Your API usage at [platform.openai.com/usage](https://platform.openai.com/usage)

### Azure OpenAI Issues

**Error: "Azure OpenAI endpoint not found"**
- Solution: Set `AZURE_OPENAI_ENDPOINT` environment variable
- Format: `https://your-resource.openai.azure.com`

**Error: "Authentication failed"**
- Solution: Verify `AZURE_OPENAI_KEY` is correct
- Check: Use Key 1 or Key 2 from Azure Portal

**Error: "Deployment not found"**
- Solution: Verify deployment name matches `AZURE_OPENAI_DEPLOYMENT`
- Check: Create deployment in Azure Portal if missing

### Local LLM (Llama3) Issues

**Error: "Ollama server request failed: Connection refused"**
- Solution: Start Ollama server: `ollama serve`
- Check: `curl http://localhost:11434/api/tags` should return model list

**Error: "Model 'llama3' not found"**
- Solution: Pull the model: `ollama pull llama3`
- Check: `ollama list` should show llama3

**Error: "vLLM server request failed"**
- Solution: Start vLLM server on correct port
- Check: `curl http://localhost:8000/health` should return status

**Slow responses from local LLM**
- Solution: Use smaller model (llama3:8b) or better hardware
- Consider: Using GPU for faster inference

**Out of memory errors**
- Solution: Use smaller model or increase system RAM
- For Ollama: `OLLAMA_NUM_GPU=0` to use CPU only

### General Issues

**Error: "LLM provider not configured"**
- Solution: Set `LLM_PROVIDER` environment variable
- Options: `openai`, `azure`, or `local`

**Falling back to mock responses**
- Check: Verify your provider configuration
- Check: Ensure service is running (for local LLM)
- Check: API keys are valid (for cloud providers)

---

## Switching Between Providers

### Quick Switch

```bash
# Switch to OpenAI
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-...

# Switch to Azure
export LLM_PROVIDER=azure
export AZURE_OPENAI_ENDPOINT=https://...

# Switch to Local (Llama3)
export LLM_PROVIDER=local
export OLLAMA_URL=http://localhost:11434
export OLLAMA_MODEL=llama3
```

### Using .env File

Just change `LLM_PROVIDER` in `.env` and restart the application.

---

## Best Practices

1. **Never commit API keys** - Always use `.env` and `.gitignore`
2. **Use environment variables** - More secure than hardcoding
3. **Test configuration** - Use test script before running production
4. **Monitor usage** - Track API costs for cloud providers
5. **Use local LLM for development** - Save costs during testing
6. **Keep keys secure** - Rotate keys periodically

---

## Additional Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Azure OpenAI Documentation](https://learn.microsoft.com/azure/ai-services/openai/)
- [Ollama Documentation](https://ollama.com/docs)
- [vLLM Documentation](https://docs.vllm.ai/)

---

**Last Updated**: After Llama3 Integration

