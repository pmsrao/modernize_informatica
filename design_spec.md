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
Location: `parsers/`

Responsibilities:
- Read Informatica Workflow, Worklet, Session, Mapping XMLs
- Extract transformations, attributes, expressions, lookup metadata, connectors
- Resolve references between objects
- Produce a structured Python dictionary as raw parsed output

---

### 3.2 Canonical Model Layer
Location: `canonical/`

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

Output:
- `mapping_model.json` used by all downstream code generators and AI agents

---

### 3.3 Expression AST Engine
Location: `expression_engine/`

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
Location: `generators/`

Includes:
- PySpark pipeline generator
- Delta Live Tables generator
- SQL generator
- Mapping specification generator
- Reconciliation SQL generator
- Test case generator

Responsibilities:
- Convert canonical model + AST into modern execution-ready code
- Ensure code readability and maintainability
- Support modular and extensible output formats

---

### 3.5 Workflow & DAG Engine
Location: `dag/`

Responsibilities:
- Construct an execution DAG from Workflow, Worklet, and Session definitions
- Validate ordering and dependencies
- Detect cycles or broken links
- Produce DAG as JSON for:
  - UI visualization
  - Workflow simulation AI agent
  - Orchestration in Lakehouse jobs

---

### 3.6 AI Reasoning Layer
Location: `ai_agents/` and `advanced_ai/`

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
Location: `llm/`

Responsibilities:
- Provide uniform `.ask(prompt)` interface to:
  - OpenAI GPT models
  - Azure OpenAI deployments
  - Local LLMs (llama.cpp, vLLM)
- Manage prompt templates
- Provide future extensibility (new models, new prompts)

---

### 3.8 Backend API
Location: `src/api/`

Responsibilities:
- REST endpoints for parsing, generation, AI insights, and DAG building
- Acts as the orchestration hub for the entire platform

---

### 3.9 Frontend UI
Location: `frontend/`

Responsibilities:
- Upload Informatica XMLs
- Render mapping specifications
- Display lineage graphs and DAGs
- View AI insights (risks, summaries, optimizations)
- View generated code (PySpark, DLT)

---

### 3.10 Deployment Layer
Location: `deployment/`

Includes:
- Dockerfiles for backend and frontend
- Docker Compose for local orchestration
- GitHub Actions CI/CD workflows

---

### 3.11 Enterprise Integrations
Location: `connectors/` and `catalog/`

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
4. AST Engine converts Informatica expressions  
5. Code Generators produce PySpark, DLT, SQL, specs, tests  
6. AI Agents enrich with explanations, risks, optimizations  
7. DAG Engine produces execution graph  
8. Enterprise adapters register outputs  
9. Developer reviews and deploys

---

## 6. Design Principles

- **Idempotency** — any output can be regenerated from canonical model  
- **Extensibility** — every layer is plugin-based  
- **Separation of concerns** — parsing, modeling, generation, AI reasoning kept separate  
- **LLM-optional** — platform works even without LLM, enhances with LLM  
- **Reproducible outputs** — tests ensure transformation correctness  

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
