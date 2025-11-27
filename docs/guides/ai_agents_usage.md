# AI Agents Usage Guide

Complete guide for using AI agents in the Informatica Modernization Accelerator.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Configuration](#configuration)
3. [Using Agents Programmatically](#using-agents-programmatically)
4. [Using Agents via API](#using-agents-via-api)
5. [Examples](#examples)
6. [Error Handling](#error-handling)
7. [Performance Tips](#performance-tips)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Configure LLM Provider

```bash
# Option 1: OpenAI (default)
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-...

# Option 2: Azure OpenAI
export LLM_PROVIDER=azure
export AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
export AZURE_OPENAI_KEY=your_key_here
export AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# Option 3: Local Llama3 (Ollama)
export LLM_PROVIDER=local
export OLLAMA_URL=http://localhost:11434
export OLLAMA_MODEL=llama3
export USE_MOCK_LLM=false

# Option 4: Mock (for testing without LLM)
export LLM_PROVIDER=local
export USE_MOCK_LLM=true
```

### 2. Start API Server

```bash
./start_api.sh
```

### 3. Test an Agent

```bash
# Parse a mapping first
curl -X POST http://localhost:8000/api/v1/parse/mapping \
  -F "file=@samples/complex/mapping_complex.xml"

# Get summary
curl -X POST http://localhost:8000/api/v1/analyze/summary \
  -H "Content-Type: application/json" \
  -d '{"file_id": "your_file_id"}'
```

---

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LLM_PROVIDER` | Provider: `openai`, `azure`, or `local` | `openai` | No |
| `OPENAI_API_KEY` | OpenAI API key | - | Yes (if using OpenAI) |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | - | Yes (if using Azure) |
| `AZURE_OPENAI_KEY` | Azure OpenAI API key | - | Yes (if using Azure) |
| `AZURE_OPENAI_DEPLOYMENT` | Azure deployment name | `gpt-4o-mini` | No |
| `LOCAL_LLM_PATH` | Path to local model file | - | No |
| `OLLAMA_URL` | Ollama server URL | `http://localhost:11434` | No (for Ollama) |
| `OLLAMA_MODEL` | Ollama model name | `llama3` | No (for Ollama) |
| `VLLM_SERVER_URL` | vLLM server URL | - | No (for vLLM) |
| `VLLM_MODEL` | vLLM model name | `default` | No (for vLLM) |
| `USE_MOCK_LLM` | Use mock responses | `false` | No |

### Configuration File

Create a `.env` file in the project root:

```bash
# .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

---

## Using Agents Programmatically

### Basic Usage

```python
import sys
from pathlib import Path

# Add paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

from parser import MappingParser
from normalizer import MappingNormalizer
from ai_agents.mapping_summary_agent import MappingSummaryAgent
from ai_agents.risk_detection_agent import RiskDetectionAgent

# Parse and normalize mapping
parser = MappingParser("samples/complex/mapping_complex.xml")
raw_mapping = parser.parse()
normalizer = MappingNormalizer()
canonical_model = normalizer.normalize(raw_mapping)

# Use agents
summary_agent = MappingSummaryAgent()
summary = summary_agent.summarize(canonical_model)
print(summary["summary"])

risk_agent = RiskDetectionAgent()
risks = risk_agent.detect_risks(canonical_model)
for risk in risks:
    print(f"{risk['severity']}: {risk['risk']}")
```

### Using Orchestrator

```python
from ai_agents.agent_orchestrator import AgentOrchestrator

orchestrator = AgentOrchestrator(enable_parallel=True)
results = orchestrator.run_all(canonical_model)

# Access results
print("Summary:", results["summary"])
print("Explanations:", len(results["explanations"]))
print("Risks:", len(results["risks"]))
print("Suggestions:", len(results["suggestions"]))
```

---

## Using Agents via API

### 1. Expression Explanation

**Endpoint**: `POST /api/v1/analyze/explain`

**Request**:
```json
{
  "expression": "IIF(AGE < 30, 'YOUNG', 'OTHER')",
  "context": {
    "field_name": "age_bucket",
    "transformation": "EXP_CALCULATIONS"
  }
}
```

**Response**:
```json
{
  "success": true,
  "result": {
    "expression": "IIF(AGE < 30, 'YOUNG', 'OTHER')",
    "field_name": "age_bucket",
    "explanation": "This field classifies customers into age groups...",
    "context": {...}
  },
  "message": "Expression explanation generated"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/analyze/explain \
  -H "Content-Type: application/json" \
  -d '{
    "expression": "IIF(AGE < 30, \"YOUNG\", \"OTHER\")",
    "context": {"field_name": "age_bucket"}
  }'
```

### 2. Mapping Summary

**Endpoint**: `POST /api/v1/analyze/summary`

**Request**:
```json
{
  "canonical_model": {...},
  "mapping_id": "optional_mapping_id",
  "file_id": "optional_file_id"
}
```

**Response**:
```json
{
  "success": true,
  "result": {
    "summary": {
      "mapping": "M_SALES_ANALYTICS",
      "summary": "This mapping processes customer order data...",
      "sources": ["CUSTOMER_SRC", "ORDER_SRC"],
      "targets": ["SALES_FACT"],
      "transformation_types": ["EXPRESSION", "LOOKUP"],
      "key_business_rules": [...]
    }
  },
  "message": "Summary generated successfully"
}
```

**Example**:
```bash
# Using file_id (after parsing)
curl -X POST http://localhost:8000/api/v1/analyze/summary \
  -H "Content-Type: application/json" \
  -d '{"file_id": "your_file_id"}'
```

### 3. Risk Detection

**Endpoint**: `POST /api/v1/analyze/risks`

**Request**: Same as summary endpoint

**Response**:
```json
{
  "success": true,
  "result": {
    "risks": [
      {
        "category": "Data Quality",
        "severity": "High",
        "location": "EXP_CALCULATIONS/age_bucket",
        "risk": "Missing null handling",
        "impact": "NULL values may cause issues",
        "recommendation": "Add null check"
      }
    ]
  },
  "message": "Risk analysis completed successfully"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/analyze/risks \
  -H "Content-Type: application/json" \
  -d '{"file_id": "your_file_id"}'
```

### 4. Transformation Suggestions

**Endpoint**: `POST /api/v1/analyze/suggestions`

**Request**: Same as summary endpoint

**Response**:
```json
{
  "success": true,
  "result": {
    "suggestions": [
      {
        "transformation": "EXP_CALCULATIONS",
        "field": "full_name",
        "current_pattern": "String concatenation",
        "suggestion": "Use concat_ws for better null handling",
        "benefits": ["Handles nulls gracefully", "More readable"],
        "improved_code": "F.concat_ws(' ', F.col('FIRST_NAME'), F.col('LAST_NAME'))",
        "priority": "Medium"
      }
    ]
  },
  "message": "Suggestions generated successfully"
}
```

---

## Examples

### Example 1: Complete Analysis Workflow

```python
from parser import MappingParser
from normalizer import MappingNormalizer
from ai_agents.agent_orchestrator import AgentOrchestrator

# Parse mapping
parser = MappingParser("mapping.xml")
raw = parser.parse()
normalizer = MappingNormalizer()
model = normalizer.normalize(raw)

# Run all analyses
orchestrator = AgentOrchestrator()
results = orchestrator.run_all(model)

# Print summary
print("=" * 80)
print("MAPPING SUMMARY")
print("=" * 80)
print(results["summary"]["summary"])

# Print risks
print("\n" + "=" * 80)
print("RISKS DETECTED")
print("=" * 80)
for risk in results["risks"]:
    print(f"\n[{risk['severity']}] {risk['location']}")
    print(f"  Risk: {risk['risk']}")
    print(f"  Recommendation: {risk['recommendation']}")

# Print suggestions
print("\n" + "=" * 80)
print("OPTIMIZATION SUGGESTIONS")
print("=" * 80)
for suggestion in results["suggestions"]:
    print(f"\n[{suggestion['priority']}] {suggestion['transformation']}/{suggestion.get('field', 'N/A')}")
    print(f"  Current: {suggestion['current_pattern']}")
    print(f"  Suggestion: {suggestion['suggestion']}")
    print(f"  Improved: {suggestion['improved_code']}")
```

### Example 2: Explain Specific Expression

```python
from ai_agents.rule_explainer_agent import RuleExplainerAgent

agent = RuleExplainerAgent()

expression = "IIF(INSTR(EMAIL, '@') > 0 AND INSTR(EMAIL, '.') > INSTR(EMAIL, '@'), 1, 0)"
explanation = agent.explain_expression(expression, "is_valid_email")

print(f"Expression: {expression}")
print(f"Explanation: {explanation}")
```

### Example 3: Fix PySpark Code

```python
from ai_agents.code_fix_agent import CodeFixAgent

agent = CodeFixAgent()

broken_code = """
from pyspark.sql import SparkSession
df = spark.table("customers")
result = df.select(F.col("name"))
"""

result = agent.fix(
    broken_code,
    error_message="NameError: name 'F' is not defined"
)

print("Fixed Code:")
print(result["fixed_code"])
print("\nChanges:")
for change in result["changes"]:
    print(f"  - {change}")
```

---

## Error Handling

### Common Errors

1. **Missing API Key**
   ```
   Error: OpenAI API key not found
   Solution: Set OPENAI_API_KEY environment variable
   ```

2. **LLM Provider Error**
   ```
   Error: Azure OpenAI connection failed
   Solution: Check endpoint and key configuration
   ```

3. **Invalid Canonical Model**
   ```
   Error: Missing required field 'mapping_name'
   Solution: Ensure canonical model is properly normalized
   ```

### Error Handling in Code

```python
from ai_agents.mapping_summary_agent import MappingSummaryAgent
from utils.exceptions import ModernizationError

try:
    agent = MappingSummaryAgent()
    summary = agent.summarize(canonical_model)
except ModernizationError as e:
    print(f"Error: {e}")
    # Handle error gracefully
except Exception as e:
    print(f"Unexpected error: {e}")
```

### API Error Responses

All API endpoints return consistent error format:

```json
{
  "success": false,
  "result": {},
  "message": "Analysis failed: error message",
  "errors": ["error1", "error2"]
}
```

---

## Performance Tips

### 1. Use Caching

Caching is enabled by default. To clear cache:

```python
from llm.llm_manager import LLMManager

llm = LLMManager()
llm.clear_cache()
```

### 2. Parallel Execution

Use orchestrator with parallel execution:

```python
orchestrator = AgentOrchestrator(enable_parallel=True)
results = orchestrator.run_all(model)  # Faster
```

### 3. Mock Mode for Testing

Use mock LLM for testing without API costs:

```bash
export USE_MOCK_LLM=true
export LLM_PROVIDER=local
```

### 4. Batch Processing

Process multiple mappings efficiently:

```python
for mapping_file in mapping_files:
    model = parse_and_normalize(mapping_file)
    results = orchestrator.run_all(model)
    # Process results
```

---

## Troubleshooting

### Issue: "Module not found" errors

**Solution**: Ensure Python paths are set correctly:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
```

### Issue: LLM responses are empty or invalid

**Solution**: 
- Check API key is valid
- Verify network connectivity
- Check LLM provider configuration
- Review error logs

### Issue: Agents return fallback responses

**Solution**:
- Check LLM provider is configured correctly
- Verify API keys are set
- Check error logs for LLM failures
- Fallback responses are normal when LLM is unavailable

### Issue: Slow response times

**Solution**:
- Enable parallel execution
- Use caching (enabled by default)
- Consider using faster models
- Check network latency

---

## Best Practices

1. **Always validate canonical model** before passing to agents
2. **Use mock mode** for development and testing
3. **Enable caching** to reduce API costs
4. **Handle errors gracefully** - agents provide fallbacks
5. **Use orchestrator** for multiple analyses
6. **Monitor API usage** to control costs
7. **Test with sample files** before production use

---

## Additional Resources

- [AI Agents Documentation](../ai_agents.md)
- [API Documentation](../api_frontend.md)
- [Next Steps](../next_steps_ai_agents.md)
- [Testing Guide](../../TESTING.md)

---

**Last Updated**: After AI Agents Implementation

