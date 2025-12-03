# Informatica Modernization Accelerator — End-to-End Architecture & Design Specification

## 1. Purpose & Problem Statement
Legacy Informatica ETL + traditional DW stacks create issues such as:
- Vendor lock-in, operational complexity, slow change velocity
- Poor visibility into business rules encoded in mappings
- Difficulty onboarding new teams
- High migration effort for Lakehouse modernization

This platform provides an **AI-augmented modernization accelerator** that:
1. Reverse-engineers Informatica assets (workflow, worklet, session, mapping XMLs)
2. Converts everything into a normalized, technology-neutral canonical data model
3. Builds complete lineage graphs
4. Generates modern code (PySpark, Delta Live Tables, SQL, specs, tests)
5. Provides deep AI reasoning (summaries, risks, optimizations, code-fix, reconstruction)
6. Enables a near‑zero‑touch migration to Lakehouse architectures

---

## 2. High‑Level Architecture Overview

```
Informatica XMLs
   ↓
XML Parsers  →  Canonical Model  →  Lineage Engine
   ↓                     ↓                  ↓
Expression AST Engine → Code Generators → Spec/Test/DAG
   ↓
AI Reasoning Layer (LLM + Agents)
   ↓
Modernized ETL Pipelines & Insights
```

The system is fully modular. Any enhancement to one component does not break others.

---

## 3. Components & Responsibilities

### 3.1 XML Parsers
Location: `src/parser/`

Components:
- `mapping_parser.py`: Parses Mapping XML files
- `workflow_parser.py`: Parses Workflow XML files
- `session_parser.py`: Parses Session XML files
- `worklet_parser.py`: Parses Worklet XML files
- `mapplet_parser.py`: Parses Mapplet XML files
- `reference_resolver.py`: Resolves references between objects
- `xml_utils.py`: XML utility functions

Responsibilities:
- Read Informatica Workflow, Worklet, Session, Mapping, Mapplet XMLs
- Extract transformations, attributes, expressions, lookup metadata, connectors
- Resolve references between objects
- Produce a structured Python dictionary as raw parsed output

---

### 3.2 Canonical Model Layer
Location: `src/normalizer/`

Components:
- `mapping_normalizer.py`: Main normalizer orchestrator
- `lineage_engine.py`: Builds data lineage graphs
- `scd_detector.py`: Detects Slowly Changing Dimension patterns
- `model_serializer.py`: Serializes canonical models
- `complexity_calculator.py`: Calculates mapping complexity
- `semantic_tag_detector.py`: Detects semantic patterns
- `runtime_config_normalizer.py`: Normalizes runtime configurations

Responsibilities:
- Transform raw parsed XML into a **technology-neutral canonical model**
- Normalize all transformation types:
  - Source
  - Expression
  - Lookup
  - Aggregator
  - Join
  - Router/Filter
  - Union
- Extract business rules and mapping relationships
- Build full mapping → session → workflow lineage
- Detect SCD patterns, incremental keys, CDC logic
- Calculate complexity metrics
- Store in Version Store (file-based or graph-based)

Output:
- `mapping_model.json` used by all downstream code generators and AI agents
- Optionally stored in Neo4j graph (if `ENABLE_GRAPH_STORE=true`)

---

### 3.3 Expression AST Engine
Location: `src/translator/`

Components:
- `parser_engine.py`: Parses Informatica expressions into AST
- `tokenizer.py`: Tokenizes expression strings
- `ast_nodes.py`: Defines AST node types
- `pyspark_translator.py`: Translates AST to PySpark code
- `sql_translator.py`: Translates AST to SQL
- `function_registry.py`: Maps Informatica functions to target platform functions

Responsibilities:
- Tokenize Informatica expressions
- Build an abstract syntax tree (AST)
- Normalize functions and operators
- Generate equivalent:
  - PySpark expressions
  - SQL expressions
  - Human-readable descriptions (for AI agents)

The AST engine is critical for correct transformation logic during migration.

---

### 3.4 Code Generators
Location: `src/generators/`

Components:
- `pyspark_generator.py`: Generates PySpark DataFrame code
- `dlt_generator.py`: Generates Delta Live Tables pipelines
- `sql_generator.py`: Generates SQL scripts
- `spec_generator.py`: Generates mapping specifications
- `tests_generator.py`: Generates unit tests
- `recon_generator.py`: Generates reconciliation scripts
- `orchestration_generator.py`: Generates orchestration code
- `code_quality_checker.py`: Checks code quality

Responsibilities:
- Convert canonical model + AST into modern execution-ready code
- Ensure code readability and maintainability
- Support modular and extensible output formats
- Generate idiomatic code for target platforms

---

### 3.5 Workflow & DAG Engine
Location: `src/dag/`

Components:
- `dag_builder.py`: Main DAG construction logic
- `dag_models.py`: DAG data structures
- `dag_visualizer.py`: Visualization utilities (Mermaid, DOT, JSON)

Responsibilities:
- Construct an execution DAG from Workflow, Worklet, and Session definitions
- Validate ordering and dependencies
- Detect cycles or broken links
- Perform topological sorting
- Produce DAG as JSON/Mermaid/DOT for:
  - UI visualization
  - Workflow simulation AI agent
  - Orchestration in Lakehouse jobs

---

### 3.6 AI Reasoning Layer
Location: `ai_agents/`

Core Agents:
- `rule_explainer_agent.py`: Explains Informatica expressions in business terms
- `mapping_summary_agent.py`: Generates comprehensive narrative summaries
- `risk_detection_agent.py`: Identifies potential issues and risks
- `transformation_suggestion_agent.py`: Suggests optimizations and modernizations

Advanced Agents:
- `code_fix_agent.py`: Automatically fixes errors in generated code
- `impact_analysis_agent.py`: Analyzes downstream impact of changes
- `mapping_reconstruction_agent.py`: Reconstructs mappings from partial information
- `workflow_simulation_agent.py`: Simulates execution and identifies bottlenecks
- `code_review_agent.py`: Reviews and improves generated code
- `model_enhancement_agent.py`: Enhances canonical models with AI insights
- `model_validation_agent.py`: Validates canonical models

Orchestration:
- `agent_orchestrator.py`: Coordinates multiple agents with error handling and caching

Capabilities:
- Explain expressions in natural language
- Summarize mappings
- Detect transformation risks
- Suggest optimization opportunities
- Reconstruct missing mappings from partial clues
- Perform impact analysis
- Simulate workflow execution paths
- Auto-correct and optimize PySpark code

This layer enhances developer productivity and dramatically reduces migration risk.

---

### 3.7 LLM Layer
Location: `src/llm/`

Components:
- `llm_manager.py`: Main manager with intelligent fallback logic
- `openai_client.py`: OpenAI API client
- `azure_openai_client.py`: Azure OpenAI client
- `local_llm_client.py`: Local LLM client (Ollama, vLLM, mock)
- `prompt_templates.py`: Centralized prompt templates

Responsibilities:
- Provide uniform `.ask(prompt)` interface to:
  - OpenAI GPT models
  - Azure OpenAI deployments
  - Local LLMs (Ollama, vLLM, mock)
- Manage prompt templates
- Provide intelligent fallback mechanisms:
  - OpenAI → Local LLM (if OpenAI fails)
  - Local LLM → OpenAI (if Local fails)
  - Azure → OpenAI (if Azure fails)
- Enable response caching for performance
- Support multiple local LLM backends:
  - Ollama (default: `http://localhost:11434`, model: `llama3`)
  - vLLM server
  - Mock mode for testing

Configuration:
- Set `LLM_PROVIDER` in `.env`: `openai`, `azure`, or `local`
- For local: `OLLAMA_URL`, `OLLAMA_MODEL` environment variables
- For OpenAI: `OPENAI_API_KEY` environment variable
- For Azure: `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_KEY`, `AZURE_OPENAI_DEPLOYMENT`

---

### 3.8 Graph Store
Location: `src/graph/`

Components:
- `graph_store.py`: Neo4j integration for storing canonical models
- `graph_queries.py`: High-level query interface
- `graph_sync.py`: Synchronization between JSON and graph storage

Responsibilities:
- Store canonical models as graph nodes and relationships
- Build and maintain data lineage graphs
- Enable graph-first architecture (optional)
- Support complex queries (migration order, readiness, patterns)
- Provide graph-based assessment capabilities

Configuration:
- Set `ENABLE_GRAPH_STORE=true` in `.env` to enable
- Configure Neo4j: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- Set `GRAPH_FIRST=true` to prefer graph over file storage
- See `docs/getting-started/setup_neo4j.md` for setup

Requirements:
- Neo4j 5.15+ (Community or Enterprise)
- Docker (recommended) or local Neo4j installation
- Neo4j Python driver (`pip install neo4j`)

---

### 3.9 Backend API
Location: `src/api/`

Components:
- `app.py`: FastAPI application setup
- `routes.py`: Comprehensive API endpoint definitions
- `file_manager.py`: File upload and management
- `models.py`: Request/response Pydantic models
- `hierarchy_builder.py`: Component hierarchy construction

Responsibilities:
- REST endpoints for parsing, generation, AI insights, and DAG building
- Graph store endpoints (when enabled)
- Acts as the orchestration hub for the entire platform
- Handles file uploads, storage, and retrieval
- Provides error handling and validation
- Supports versioning and caching

---

### 3.10 Assessment Components
Location: `src/assessment/`

Components:
- `profiler.py`: Profiles mappings and transformations
- `analyzer.py`: Analyzes patterns and migration blockers
- `wave_planner.py`: Plans migration waves
- `report_generator.py`: Generates assessment reports
- `tco_calculator.py`: Calculates total cost of ownership

Responsibilities:
- Analyze migration complexity and readiness
- Identify migration blockers and risks
- Plan migration waves based on dependencies
- Generate comprehensive assessment reports
- Calculate TCO and effort estimates

Requirements: Requires graph store to be enabled

---

### 3.11 Frontend UI
Location: `frontend/`

Responsibilities:
- Upload Informatica XMLs
- Render mapping specifications
- Display lineage graphs and DAGs
- View AI insights (risks, summaries, optimizations)
- View generated code (PySpark, DLT)
- Explore graph store (when enabled)

---

### 3.12 Deployment Layer
Location: `deployment/`

Includes:
- Dockerfiles for backend and frontend
- Docker Compose for local orchestration
- GitHub Actions CI/CD workflows

---

### 3.13 Enterprise Integrations
Location: `src/connectors/` and `src/catalog/`

Components:
- `s3_connector.py`, `adls_connector.py`, `gcs_connector.py`: Storage connectors
- `glue_catalog.py`, `purview_catalog.py`, `dataplex_catalog.py`: Catalog integrations
- `slack_notifier.py`, `teams_notifier.py`: Notification modules

Responsibilities:
- Storage connectors: S3, ADLS, GCS
- Catalog integrations: Glue, Purview, Dataplex
- Versioning store for all generated artifacts
- Slack/Teams notification modules

---

## 4. Internal Canonical Model Contract

This is the **single source of truth** for all downstream engines.

```json
{
  "mapping_name": "M_LOAD_CUSTOMER",
  "sources": [...],
  "targets": [...],
  "transformations": [...],
  "connectors": [...],
  "lineage": {...},
  "scd_type": "SCD2",
  "incremental_keys": ["LAST_UPDATED_DT"]
}
```

---

## 5. End-to-End Modernization Flow

1. User uploads Informatica XMLs  
2. Parsers extract structured metadata  
3. Canonical Model Builder normalizes all objects  
4. **Optional**: Store canonical model in Neo4j graph (if `ENABLE_GRAPH_STORE=true`)
5. AST Engine converts Informatica expressions  
6. Code Generators produce PySpark, DLT, SQL, specs, tests  
7. AI Agents enrich with explanations, risks, optimizations (with LLM fallback)
8. DAG Engine produces execution graph  
9. **Optional**: Assessment components analyze migration readiness (requires graph store)
10. Enterprise adapters register outputs  
11. Developer reviews and deploys

**Configuration Requirements**:
- **Basic operation**: No external dependencies required (works with file-based storage)
- **LLM features**: Set `LLM_PROVIDER=local` (Ollama) or `LLM_PROVIDER=openai` (with API key)
- **Graph features**: Set `ENABLE_GRAPH_STORE=true` and configure Neo4j (see `docs/getting-started/setup_neo4j.md`)

---

## 6. Design Principles

- **Idempotency** — any output can be regenerated from canonical model  
- **Extensibility** — every layer is plugin-based  
- **Separation of concerns** — parsing, modeling, generation, AI reasoning kept separate  
- **LLM-optional** — platform works even without LLM, enhances with LLM
  - Intelligent fallback: OpenAI → Local LLM → Error
  - Local LLM support via Ollama (default) or vLLM
- **Graph-optional** — platform works without Neo4j, but graph enables advanced features
  - Assessment, wave planning, and complex queries require graph store
  - Can operate in file-based mode for basic functionality
- **Reproducible outputs** — tests ensure transformation correctness
- **Import path consistency** — uses `from module import ...` pattern (not `from src.module`) when `src` is in PYTHONPATH  

---

## 7. Regeneration Approach

This spec is meant to serve as the **source of truth**:
- Cursor can regenerate code from it
- Any improvements flow into all layers
- Provides blueprint for onboarding new developers

---

## 8. Supported Informatica Transformations

- SourceQualifier  
- Expression  
- Lookup  
- Aggregator  
- Router  
- Filter  
- Joiner  
- Union  
- Normalizer  
- Update Strategy  
- Custom transformations (extensible)

---

## 9. Appendix: Future Enhancements

- ML-based expression pattern mining  
- Migration wave planner  
- Databricks Jobs orchestration generator  
- Full reconciler & data quality suite  
