# Testing AI Agents Guide

This guide explains how to test the AI agents and understand their contributions to the Informatica modernization process.

## Overview

The system includes multiple AI agents that provide intelligent analysis and assistance:

1. **Core Analysis Agents** (Most Used):
   - `RuleExplainerAgent` - Explains Informatica expressions in human-readable terms
   - `MappingSummaryAgent` - Generates comprehensive summaries of mapping logic
   - `RiskDetectionAgent` - Identifies potential risks and issues
   - `TransformationSuggestionAgent` - Suggests optimizations and modernizations

2. **Advanced Agents**:
   - `CodeFixAgent` - Fixes code errors and issues
   - `ImpactAnalysisAgent` - Analyzes impact of changes
   - `MappingReconstructionAgent` - Reconstructs mappings from partial data
   - `WorkflowSimulationAgent` - Simulates workflow execution

3. **Orchestrator**:
   - `AgentOrchestrator` - Coordinates multiple agents for comprehensive analysis

## Prerequisites

### 1. API Server Running

Start the API server:

```bash
# Option 1: Using the startup script
./start_api.sh

# Option 2: Manual start
cd src
uvicorn api.app:app --reload --port 8000
```

The API should be accessible at `http://localhost:8000`

### 2. LLM Configuration

Configure your LLM provider in `.env` or environment variables:

```bash
# For OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=your_api_key_here

# For Azure OpenAI
LLM_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name

# For Local LLM (optional)
LLM_PROVIDER=local
LOCAL_LLM_URL=http://localhost:8000/v1
```

### 3. Sample Files

Ensure you have sample mapping files in the `samples/` directory:
- `samples/simple/mapping_simple.xml`
- `samples/complex/mapping_complex.xml`

## Testing Methods

### Method 1: Using API Endpoints (Recommended)

#### Step 1: Upload a Mapping File

```bash
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@samples/simple/mapping_simple.xml"
```

Response:
```json
{
  "file_id": "abc123...",
  "filename": "mapping_simple.xml",
  "file_size": 1234,
  "file_type": "mapping",
  "uploaded_at": "2024-01-01T00:00:00",
  "message": "File uploaded successfully"
}
```

Save the `file_id` for subsequent requests.

#### Step 2: Parse the Mapping

```bash
curl -X POST "http://localhost:8000/api/v1/parse/mapping" \
  -H "Content-Type: application/json" \
  -d '{"file_id": "YOUR_FILE_ID"}'
```

#### Step 3: Test AI Agents

##### A. Get Mapping Summary

```bash
curl -X POST "http://localhost:8000/api/v1/analyze/summary" \
  -H "Content-Type: application/json" \
  -d '{
    "mapping_id": "YOUR_FILE_ID"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "result": {
    "summary": "This mapping loads customer data from CUSTOMER_SRC...",
    "sources": ["CUSTOMER_SRC"],
    "targets": ["CUSTOMER_TGT"],
    "transformations": ["EXP_DERIVE", "LK_REGION", "AGG_SALES"],
    "business_logic": "Derives full name, looks up region, aggregates sales..."
  },
  "message": "Mapping summary generated successfully"
}
```

**What to Validate:**
- ✅ Summary is human-readable and comprehensive
- ✅ All sources and targets are identified
- ✅ Transformations are listed
- ✅ Business logic is explained clearly

##### B. Detect Risks

```bash
curl -X POST "http://localhost:8000/api/v1/analyze/risks" \
  -H "Content-Type: application/json" \
  -d '{
    "mapping_id": "YOUR_FILE_ID"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "result": {
    "risks": [
      {
        "type": "DATA_LOSS",
        "severity": "MEDIUM",
        "description": "Potential data loss in type conversion...",
        "location": "EXP_DERIVE.FULL_NAME",
        "recommendation": "Add validation before conversion"
      }
    ],
    "risk_count": 1,
    "high_risk_count": 0,
    "medium_risk_count": 1,
    "low_risk_count": 0
  },
  "message": "Risk analysis completed successfully"
}
```

**What to Validate:**
- ✅ Risks are categorized by type and severity
- ✅ Each risk has clear description and location
- ✅ Recommendations are actionable
- ✅ Risk counts are accurate

##### C. Get Transformation Suggestions

```bash
curl -X POST "http://localhost:8000/api/v1/analyze/suggestions" \
  -H "Content-Type: application/json" \
  -d '{
    "mapping_id": "YOUR_FILE_ID"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "result": {
    "suggestions": [
      {
        "type": "PERFORMANCE",
        "priority": "HIGH",
        "description": "Use broadcast join for small lookup table",
        "transformation": "LK_REGION",
        "current_approach": "Regular join",
        "suggested_approach": "Broadcast join",
        "expected_benefit": "50% faster execution"
      }
    ],
    "suggestion_count": 1
  },
  "message": "Suggestions generated successfully"
}
```

**What to Validate:**
- ✅ Suggestions are prioritized
- ✅ Current and suggested approaches are clear
- ✅ Expected benefits are quantified
- ✅ Suggestions are actionable

##### D. Explain Expression

```bash
curl -X POST "http://localhost:8000/api/v1/analyze/explain" \
  -H "Content-Type: application/json" \
  -d '{
    "expression": "IIF(AGE < 30, '\''YOUNG'\'', '\''OTHER'\'')",
    "context": {
      "field_name": "AGE_BUCKET",
      "transformation": "EXP_DERIVE"
    }
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "result": {
    "expression": "IIF(AGE < 30, 'YOUNG', 'OTHER')",
    "field_name": "AGE_BUCKET",
    "explanation": "This expression categorizes customers into age buckets. If the age is less than 30, it returns 'YOUNG', otherwise it returns 'OTHER'.",
    "context": {
      "field_name": "AGE_BUCKET",
      "transformation": "EXP_DERIVE"
    }
  },
  "message": "Expression explanation generated"
}
```

**What to Validate:**
- ✅ Explanation is clear and human-readable
- ✅ Logic is correctly interpreted
- ✅ Context is considered

### Method 2: Using Python Scripts

Create a test script `scripts/test_ai_agents.py`:

```python
#!/usr/bin/env python3
"""Test AI agents directly."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from parser import MappingParser
from normalizer import MappingNormalizer
from ai_agents.rule_explainer_agent import RuleExplainerAgent
from ai_agents.mapping_summary_agent import MappingSummaryAgent
from ai_agents.risk_detection_agent import RiskDetectionAgent
from ai_agents.transformation_suggestion_agent import TransformationSuggestionAgent

def test_ai_agents():
    """Test all AI agents."""
    
    # Parse and normalize a mapping
    print("=" * 80)
    print("STEP 1: Parse and Normalize Mapping")
    print("=" * 80)
    
    parser = MappingParser("samples/simple/mapping_simple.xml")
    mapping_data = parser.parse()
    
    normalizer = MappingNormalizer()
    canonical_model = normalizer.normalize(mapping_data)
    
    print(f"✅ Mapping parsed: {canonical_model.get('mapping_name')}")
    print(f"   Sources: {len(canonical_model.get('sources', []))}")
    print(f"   Targets: {len(canonical_model.get('targets', []))}")
    print(f"   Transformations: {len(canonical_model.get('transformations', []))}")
    
    # Test Rule Explainer Agent
    print("\n" + "=" * 80)
    print("STEP 2: Test Rule Explainer Agent")
    print("=" * 80)
    
    explainer = RuleExplainerAgent()
    expression = "IIF(AGE < 30, 'YOUNG', 'OTHER')"
    explanation = explainer.explain_expression(expression, "AGE_BUCKET", {})
    
    print(f"Expression: {expression}")
    print(f"Explanation: {explanation}")
    print(f"✅ Rule Explainer Agent working")
    
    # Test Mapping Summary Agent
    print("\n" + "=" * 80)
    print("STEP 3: Test Mapping Summary Agent")
    print("=" * 80)
    
    summary_agent = MappingSummaryAgent()
    summary = summary_agent.summarize(canonical_model)
    
    print(f"Summary: {summary.get('summary', 'N/A')[:200]}...")
    print(f"✅ Mapping Summary Agent working")
    
    # Test Risk Detection Agent
    print("\n" + "=" * 80)
    print("STEP 4: Test Risk Detection Agent")
    print("=" * 80)
    
    risk_agent = RiskDetectionAgent()
    risks = risk_agent.detect_risks(canonical_model)
    
    print(f"Risks detected: {len(risks.get('risks', []))}")
    for risk in risks.get('risks', [])[:3]:
        print(f"  - {risk.get('type')}: {risk.get('description', '')[:100]}")
    print(f"✅ Risk Detection Agent working")
    
    # Test Transformation Suggestion Agent
    print("\n" + "=" * 80)
    print("STEP 5: Test Transformation Suggestion Agent")
    print("=" * 80)
    
    suggestion_agent = TransformationSuggestionAgent()
    suggestions = suggestion_agent.suggest(canonical_model)
    
    print(f"Suggestions: {len(suggestions.get('suggestions', []))}")
    for suggestion in suggestions.get('suggestions', [])[:3]:
        print(f"  - {suggestion.get('type')}: {suggestion.get('description', '')[:100]}")
    print(f"✅ Transformation Suggestion Agent working")
    
    print("\n" + "=" * 80)
    print("ALL AI AGENTS TESTED SUCCESSFULLY")
    print("=" * 80)

if __name__ == "__main__":
    test_ai_agents()
```

Run the script:

```bash
python scripts/test_ai_agents.py
```

### Method 3: Using Agent Orchestrator

Test all agents at once using the orchestrator:

```python
from ai_agents.agent_orchestrator import AgentOrchestrator
from parser import MappingParser
from normalizer import MappingNormalizer

# Parse and normalize
parser = MappingParser("samples/simple/mapping_simple.xml")
mapping_data = parser.parse()
normalizer = MappingNormalizer()
canonical_model = normalizer.normalize(mapping_data)

# Run all agents
orchestrator = AgentOrchestrator()
results = orchestrator.run_all(canonical_model)

print("Summary:", results.get('summary', {}))
print("Risks:", results.get('risks', {}))
print("Suggestions:", results.get('suggestions', {}))
```

## Understanding Agent Contributions

### 1. Rule Explainer Agent

**Purpose:** Makes complex Informatica expressions understandable

**Contribution:**
- Translates technical expressions to business language
- Explains conditional logic, functions, and operators
- Helps non-technical stakeholders understand data transformations

**Example:**
- Input: `IIF(REGION_ID IN (1,2,3), 'PREMIUM', IIF(REGION_ID IN (4,5), 'STANDARD', 'BASIC'))`
- Output: "This expression categorizes regions into three tiers: PREMIUM for regions 1-3, STANDARD for regions 4-5, and BASIC for all other regions."

### 2. Mapping Summary Agent

**Purpose:** Provides comprehensive overview of mapping logic

**Contribution:**
- Generates human-readable summaries
- Identifies data flow and transformations
- Explains business logic in narrative form
- Helps with documentation and knowledge transfer

**Example Output:**
```
This mapping processes customer sales data from the CUSTOMER_SRC source table.
It derives a full name field by concatenating first and last names, categorizes
customers by age, looks up region information, and aggregates total sales by
customer. The final output is written to CUSTOMER_TGT.
```

### 3. Risk Detection Agent

**Purpose:** Identifies potential issues before migration

**Contribution:**
- Detects data loss risks (type conversions, truncations)
- Identifies performance issues (large joins, no indexes)
- Flags data quality concerns (null handling, default values)
- Prioritizes risks by severity
- Provides actionable recommendations

**Example Risks:**
- **Data Loss:** Converting VARCHAR(100) to VARCHAR(50) may truncate data
- **Performance:** Large table join without proper partitioning
- **Data Quality:** Missing null checks in expressions

### 4. Transformation Suggestion Agent

**Purpose:** Suggests optimizations and modernizations

**Contribution:**
- Recommends performance improvements
- Suggests modern PySpark/Spark SQL patterns
- Identifies optimization opportunities
- Provides migration guidance

**Example Suggestions:**
- Use broadcast join for small lookup tables
- Replace Informatica-specific functions with Spark equivalents
- Split complex transformations for better maintainability
- Use Delta Lake features for SCD2 implementations

## Validation Checklist

After testing, verify:

- [ ] **LLM Connection:** Agents can connect to configured LLM provider
- [ ] **Response Quality:** AI responses are relevant and accurate
- [ ] **Error Handling:** Agents handle errors gracefully
- [ ] **Performance:** Responses are generated in reasonable time (< 30s)
- [ ] **Consistency:** Same input produces similar quality output
- [ ] **Coverage:** All transformation types are analyzed
- [ ] **Actionability:** Suggestions and recommendations are implementable

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'ai_agents'"

**Solution:**
```bash
# Ensure you're in the project root
cd /path/to/modernize_informatica

# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: "LLM API Error" or "Connection Failed"

**Solution:**
1. Check LLM configuration in `.env` or environment variables
2. Verify API keys are correct
3. Test LLM connection:
   ```python
   from src.llm.llm_manager import LLMManager
   llm = LLMManager()
   response = llm.ask("Test prompt")
   print(response)
   ```

### Issue: "Empty or Generic Responses"

**Solution:**
1. Ensure canonical model is properly normalized
2. Check that transformations have expressions/ports
3. Verify LLM provider is working (test with simple prompt)
4. Check logs for errors: `tail -f logs/app.log`

### Issue: "Slow Response Times"

**Solution:**
1. Use a faster LLM model (e.g., GPT-3.5-turbo instead of GPT-4)
2. Enable caching if available
3. Reduce prompt complexity
4. Use parallel execution for multiple agents

## Next Steps

1. **Integrate into Workflow:** Add AI agent calls to your modernization pipeline
2. **Customize Prompts:** Adjust prompt templates for your specific use cases
3. **Add Metrics:** Track agent performance and response quality
4. **Extend Agents:** Create custom agents for domain-specific analysis

## Additional Resources

- API Documentation: `http://localhost:8000/docs` (when API is running)
- Agent Implementation: See `ai_agents/` directory
- Prompt Templates: See `src/llm/prompt_templates.py`
- Configuration: See `src/config.py`

