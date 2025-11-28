# Informatica Modernization Accelerator

An AI-augmented framework to reverse engineer, analyze, and modernize legacy Informatica ETL workloads into lakehouse-native architectures (PySpark + Delta + Delta Live Tables on Databricks/Spark).

---

## Features

### Core Capabilities

- **XML Parsing**: Parse Informatica Workflow, Worklet, Session, and Mapping XMLs
- **Canonical Model**: Technology-neutral representation of ETL logic
- **Code Generation**: Generate PySpark, Delta Live Tables, SQL, specs, and tests
- **Expression Translation**: Translate 100+ Informatica functions to PySpark/SQL
- **Lineage Engine**: Build complete data lineage graphs
- **DAG Builder**: Construct workflow execution graphs with dependency analysis

### AI & LLM Agents

- **Rule Explainer**: Explain Informatica expressions in business terms
- **Mapping Summary**: Generate comprehensive narrative summaries
- **Risk Detection**: Identify potential issues and risks
- **Transformation Suggestions**: Suggest optimizations and modernizations
- **Code Fix Agent**: Automatically fix errors in generated code
- **Impact Analysis**: Analyze downstream impact of changes
- **Mapping Reconstruction**: Reconstruct mappings from partial information
- **Workflow Simulation**: Simulate execution and identify bottlenecks

### LLM Provider Support

- **OpenAI** (default): Standard GPT models
- **Azure OpenAI**: Enterprise deployments
- **Local LLM**: Mock mode for testing, vLLM server support

---

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone <repository-url>
cd modernize_informatica

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file or set environment variables:

```bash
# For OpenAI (default)
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-...

# For Azure OpenAI
export LLM_PROVIDER=azure
export AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
export AZURE_OPENAI_KEY=your_key_here

# For local Llama3 (Ollama)
export LLM_PROVIDER=local
export OLLAMA_URL=http://localhost:11434
export OLLAMA_MODEL=llama3
export USE_MOCK_LLM=false

# For testing (mock mode)
export LLM_PROVIDER=local
export USE_MOCK_LLM=true
```

### 3. Start API Server

```bash
./start_api.sh
```

API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### 4. Test with Sample Files

```bash
# Parse a mapping
curl -X POST http://localhost:8000/api/v1/parse/mapping \
  -F "file=@samples/complex/mapping_complex.xml"

# Get AI analysis
curl -X POST http://localhost:8000/api/v1/analyze/summary \
  -H "Content-Type: application/json" \
  -d '{"file_id": "your_file_id"}'
```

---

## Usage Examples

### Parse and Analyze Mapping

```python
from parser import MappingParser
from normalizer import MappingNormalizer
from ai_agents.agent_orchestrator import AgentOrchestrator

# Parse mapping
parser = MappingParser("mapping.xml")
raw = parser.parse()
normalizer = MappingNormalizer()
model = normalizer.normalize(raw)

# Run AI analysis
orchestrator = AgentOrchestrator()
results = orchestrator.run_all(model)

# Access results
print("Summary:", results["summary"]["summary"])
print("Risks:", len(results["risks"]))
print("Suggestions:", len(results["suggestions"]))
```

### Generate PySpark Code

```python
from generators import PySparkGenerator

generator = PySparkGenerator()
pyspark_code = generator.generate(model)
print(pyspark_code)
```

### Explain Expression

```python
from ai_agents.rule_explainer_agent import RuleExplainerAgent

agent = RuleExplainerAgent()
explanation = agent.explain_expression(
    "IIF(AGE < 30, 'YOUNG', 'OTHER')",
    "age_bucket"
)
print(explanation)
```

---

## Project Structure

```
modernize_informatica/
├── src/                    # Source code
│   ├── parser/            # XML parsers
│   ├── normalizer/        # Canonical model normalization
│   ├── translator/        # Expression translation
│   ├── generators/        # Code generators
│   ├── llm/              # LLM client implementations
│   ├── api/              # FastAPI endpoints
│   └── dag/              # DAG builder
├── ai_agents/            # AI agent implementations
├── tests/                # Test suite
├── samples/              # Sample XML files
├── docs/                 # Documentation
└── frontend/             # Web UI
```

---

## Documentation

- [Solution Overview](solution.md) - Complete solution architecture and design
- [Roadmap](roadmap.md) - Implementation status and next steps
- [End-to-End Testing Guide](test_end_to_end.md) - Comprehensive testing instructions
- [System Architecture](system_architecture.md) - Detailed component architecture
- [AI Agents Guide](docs/ai_agents.md)
- [API Usage Guide](docs/guides/ai_agents_usage.md)
- [Canonical Model](docs/canonical_model.md)
- [Testing Guide](TESTING.md)

---

## Testing

### Run Unit Tests

```bash
pytest tests/unit/ -v
```

### Run Integration Tests

```bash
# With mock LLM (always runs)
pytest tests/integration/ -v

# With real LLM (requires API keys)
USE_MOCK_LLM=false pytest tests/integration/ -v
```

### Test Sample Files

```bash
python scripts/test_samples.py
```

---

## API Endpoints

### Parsing
- `POST /api/v1/parse/mapping` - Parse mapping XML
- `POST /api/v1/parse/workflow` - Parse workflow XML
- `POST /api/v1/parse/session` - Parse session XML
- `POST /api/v1/parse/worklet` - Parse worklet XML

### Code Generation
- `POST /api/v1/generate/pyspark` - Generate PySpark code
- `POST /api/v1/generate/dlt` - Generate DLT pipeline
- `POST /api/v1/generate/sql` - Generate SQL
- `POST /api/v1/generate/spec` - Generate mapping spec

### AI Analysis
- `POST /api/v1/analyze/summary` - Get mapping summary
- `POST /api/v1/analyze/risks` - Detect risks
- `POST /api/v1/analyze/suggestions` - Get optimization suggestions
- `POST /api/v1/analyze/explain` - Explain expression

### DAG
- `POST /api/v1/dag/build` - Build workflow DAG

See [API Documentation](http://localhost:8000/docs) for detailed request/response formats.

---

## Key Components

### Parsers
- Support for Workflow, Worklet, Session, and Mapping XMLs
- Reference resolution
- Transformation extraction

### Canonical Model
- Technology-neutral representation
- Supports all transformation types
- Complete lineage information

### Code Generators
- **PySpark**: Production-ready Spark code
- **Delta Live Tables**: DLT pipeline definitions
- **SQL**: Standard SQL queries
- **Specs**: Markdown documentation
- **Tests**: Auto-generated test suites

### AI Agents
- **LLM Integration**: Support for OpenAI, Azure, Local
- **Caching**: Reduce API costs
- **Error Handling**: Graceful fallbacks
- **Parallel Execution**: Fast analysis

---

## Requirements

- Python 3.8+
- See `requirements.txt` for dependencies

### Optional (for LLM features)
- OpenAI API key (for OpenAI provider)
- Azure OpenAI credentials (for Azure provider)
- vLLM server (for local LLM)

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## License

[Add your license here]

---

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Last Updated**: After AI Agents Implementation
