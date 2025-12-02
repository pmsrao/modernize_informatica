# AI & LLM Agents

## Purpose

The AI layer is designed to augment human understanding and decision-making, not to replace deterministic parsing and generation.

It answers questions like:

- "What does this mapping actually do?"
- "Which transformations are risky or brittle?"
- "What is a simpler way to express this logic?"
- "What is the impact of changing this column?"
- "Given partial clues, what might the original mapping have been?"

---

## LLM Layer

The LLM Manager abstracts away providers:

- **OpenAI** (standard GPT models) - Default provider
- **Azure OpenAI** - Enterprise deployments
- **Local LLM** (llama.cpp, vLLM, mock) - Testing and privacy

Selection is controlled by configuration (environment variable `LLM_PROVIDER`).

### Configuration

Set the following environment variables:

```bash
# For OpenAI (default)
export LLM_PROVIDER=openai
export OPENAI_API_KEY=your_key_here

# For Azure OpenAI
export LLM_PROVIDER=azure
export AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
export AZURE_OPENAI_KEY=your_key_here
export AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# For Local Llama3 (Ollama)
export LLM_PROVIDER=local
export OLLAMA_URL=http://localhost:11434
export OLLAMA_MODEL=llama3
export USE_MOCK_LLM=false

# For Mock (testing without LLM)
export LLM_PROVIDER=local
export USE_MOCK_LLM=true
```

### Features

- **Retry Logic**: Automatic retry with exponential backoff
- **Response Caching**: Cache responses to reduce API costs
- **Error Handling**: Graceful degradation with fallback responses
- **Unified Interface**: Same API for all providers

Prompt templates are centralized so that:

- Expression explanation
- Mapping summarization
- Risk analysis
- Suggestion generation
- Code fixing
- Reconstruction
- Impact analysis
- Workflow simulation

…all follow consistent patterns with few-shot examples.

---

## Core AI Agents

### 1. Rule Explainer Agent

**Purpose**: Explains Informatica expressions in simple business terms.

**Input**: 
- Field name
- Original Informatica expression
- Optional context (transformation, mapping, field type)

**Output**: Human-readable explanation of the rule

**Example**:
- Expression: `IIF(AGE < 30, 'YOUNG', 'OTHER')`
- Explanation: "This field classifies customers into age groups. If the customer's age is less than 30, they are classified as 'YOUNG', otherwise they are classified as 'OTHER'."

**Usage**:
```python
from ai_agents.rule_explainer_agent import RuleExplainerAgent

agent = RuleExplainerAgent()
explanations = agent.explain(canonical_model)
# Or explain a single expression:
explanation = agent.explain_expression("IIF(AGE < 30, 'YOUNG', 'OTHER')", "age_bucket")
```

**API Endpoint**: `POST /api/v1/analyze/explain`

### 2. Mapping Summary Agent

**Purpose**: Generates comprehensive narrative summaries of mapping logic.

**Input**: Canonical mapping model

**Output**: Structured summary with:
- Narrative description
- Source and target tables
- Key transformations
- Business rules identified
- SCD type and incremental load info

**Example Output**:
```json
{
  "mapping": "M_SALES_ANALYTICS",
  "summary": "This mapping processes customer order data...",
  "sources": ["CUSTOMER_SRC", "ORDER_SRC"],
  "targets": ["SALES_FACT", "CUSTOMER_DIM"],
  "transformation_types": ["EXPRESSION", "LOOKUP", "AGGREGATOR"],
  "key_business_rules": ["Customer segmentation logic", "Order classification"]
}
```

**Usage**:
```python
from ai_agents.mapping_summary_agent import MappingSummaryAgent

agent = MappingSummaryAgent()
summary = agent.summarize(canonical_model)
```

**API Endpoint**: `POST /api/v1/analyze/summary`

### 3. Risk Detection Agent

**Purpose**: Identifies potential risks and issues in mappings.

**Input**: Canonical mapping model

**Output**: List of risks with:
- Category (Data Quality, Performance, Maintainability, Migration)
- Severity (High, Medium, Low)
- Location (transformation/field)
- Risk description
- Impact assessment
- Mitigation recommendations

**Detects**:
- Missing null handling
- Risky type casts
- Division without zero checks
- Deeply nested IIF statements
- Missing filters
- Performance issues
- Complex patterns that may break during migration

**Example**:
```json
[
  {
    "category": "Data Quality",
    "severity": "High",
    "location": "EXP_CALCULATIONS/age_bucket",
    "risk": "Expression does not handle NULL values",
    "impact": "NULL ages will cause unexpected results",
    "recommendation": "Add null check: IIF(ISNULL(AGE), 'UNKNOWN', ...)"
  }
]
```

**Usage**:
```python
from ai_agents.risk_detection_agent import RiskDetectionAgent

agent = RiskDetectionAgent()
risks = agent.detect_risks(canonical_model)
```

**API Endpoint**: `POST /api/v1/analyze/risks`

### 4. Transformation Suggestion Agent

**Purpose**: Suggests optimizations and modernizations for transformations.

**Input**: Canonical mapping model, target platform (default: PySpark)

**Output**: List of suggestions with:
- Transformation and field
- Current pattern
- Suggested improvement
- Benefits
- Improved code example
- Priority

**Suggests**:
- Using `concat_ws` instead of `||` for string concatenation
- Using `when/otherwise` instead of nested `IIF`
- Using `coalesce` instead of `NVL`
- Splitting complex transformations
- Performance optimizations

**Example**:
```json
[
  {
    "transformation": "EXP_CALCULATIONS",
    "field": "full_name",
    "current_pattern": "String concatenation using ||",
    "suggestion": "Use PySpark concat_ws for better null handling",
    "benefits": ["Handles nulls gracefully", "More readable"],
    "improved_code": "F.concat_ws(' ', F.col('FIRST_NAME'), F.col('LAST_NAME'))",
    "priority": "Medium"
  }
]
```

**Usage**:
```python
from ai_agents.transformation_suggestion_agent import TransformationSuggestionAgent

agent = TransformationSuggestionAgent(target_platform="PySpark")
suggestions = agent.suggest(canonical_model)
```

**API Endpoint**: `POST /api/v1/analyze/suggestions`

---

## Advanced AI Agents

### 1. Code Fix Agent

**Purpose**: Automatically fixes errors in generated PySpark code.

**Input**: 
- PySpark code with errors
- Optional error message
- Optional error type

**Output**: 
- Fixed code
- Explanation of changes
- List of changes made

**Features**:
- Preserves business logic
- Fixes syntax errors
- Adds missing imports
- Handles type mismatches
- Provides explanations

**Usage**:
```python
from ai_agents.code_fix_agent import CodeFixAgent

agent = CodeFixAgent()
result = agent.fix(pyspark_code, error_message="NameError: name 'F' is not defined")
print(result["fixed_code"])
```

### 2. Mapping Reconstruction Agent

**Purpose**: Reconstructs mappings from partial information.

**Input**: Clues dictionary with:
- `partial_xml`: Partial Informatica XML
- `log_fragments`: Log file fragments
- `lineage`: Lineage information
- `target_definitions`: Target table structures
- `source_definitions`: Source table structures

**Output**: Reconstructed canonical mapping model with confidence level

**Usage**:
```python
from ai_agents.mapping_reconstruction_agent import MappingReconstructionAgent

agent = MappingReconstructionAgent()
clues = {
    "target_definitions": [{"name": "TGT1", "fields": [...]}],
    "lineage": {...}
}
reconstructed = agent.reconstruct(clues)
```

### 3. Impact Analysis Agent

**Purpose**: Analyzes downstream impact of proposed changes.

**Input**:
- Canonical mapping model
- Change target (e.g., "EXP_CALCULATIONS/age_bucket")
- Change description

**Output**: Impact analysis with:
- Direct dependencies
- Indirect dependencies
- Affected targets
- Data quality concerns
- Testing priorities
- Overall risk level

**Usage**:
```python
from ai_agents.impact_analysis_agent import ImpactAnalysisAgent

agent = ImpactAnalysisAgent()
impact = agent.analyze(
    canonical_model,
    "EXP_CALCULATIONS/age_bucket",
    "Change age bucket logic to include more categories"
)
```

### 4. Workflow Simulation Agent

**Purpose**: Simulates workflow execution to identify bottlenecks.

**Input**: DAG model with nodes, edges, execution levels

**Output**: Simulation results with:
- Execution sequence
- Critical path
- Bottlenecks
- Single points of failure
- Resource requirements
- Optimization suggestions

**Usage**:
```python
from ai_agents.workflow_simulation_agent import WorkflowSimulationAgent

agent = WorkflowSimulationAgent()
simulation = agent.simulate(dag_model)
```

---

## Agent Orchestrator

The `AgentOrchestrator` coordinates multiple agents:

**Features**:
- Runs all core agents in parallel (optional)
- Aggregates results
- Handles errors gracefully
- Provides unified interface

**Usage**:
```python
from ai_agents.agent_orchestrator import AgentOrchestrator

orchestrator = AgentOrchestrator(enable_parallel=True)
results = orchestrator.run_all(canonical_model)

# Access individual results
summary = results["summary"]
explanations = results["explanations"]
risks = results["risks"]
suggestions = results["suggestions"]
```

---

## Error Handling & Fallbacks

All agents include:

1. **Pattern-Based Detection**: Deterministic pattern matching for common cases
2. **LLM Integration**: AI-powered analysis for complex cases
3. **Fallback Responses**: Graceful degradation when LLM fails
4. **Error Logging**: Comprehensive error tracking

This ensures agents always return useful results, even when LLM services are unavailable.

---

## Performance Considerations

- **Caching**: Responses are cached to reduce API costs
- **Parallel Execution**: Independent agents run in parallel
- **Retry Logic**: Automatic retries with exponential backoff
- **Mock Mode**: Use `USE_MOCK_LLM=true` for testing without API keys

---

## Testing

### Unit Tests
```bash
pytest tests/unit/test_ai_agents.py -v
```

### Integration Tests
```bash
# With mock LLM (always runs)
pytest tests/integration/test_ai_agents_integration.py -v

# With real LLM (requires API keys)
USE_MOCK_LLM=false pytest tests/integration/test_ai_agents_integration.py -v
```

---

## API Usage

All agents are accessible via REST API:

```bash
# Get mapping summary
curl -X POST http://localhost:8000/api/v1/analyze/summary \
  -H "Content-Type: application/json" \
  -d '{"canonical_model": {...}}'

# Detect risks
curl -X POST http://localhost:8000/api/v1/analyze/risks \
  -H "Content-Type: application/json" \
  -d '{"canonical_model": {...}}'

# Get suggestions
curl -X POST http://localhost:8000/api/v1/analyze/suggestions \
  -H "Content-Type: application/json" \
  -d '{"canonical_model": {...}}'

# Explain expression
curl -X POST http://localhost:8000/api/v1/analyze/explain \
  -H "Content-Type: application/json" \
  -d '{"expression": "IIF(AGE < 30, \"YOUNG\", \"OTHER\")", "context": {...}}'
```

See [API Usage Guide](guides/ai_agents_usage.md) for detailed examples.

---

**Next**: Learn about [API & Frontend](api_frontend.md) for user interaction.
