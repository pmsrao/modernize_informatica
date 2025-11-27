# High-Level Architecture

## Logical Flow

At the highest level, the system can be viewed as:

1. **Input**: Informatica XML files (Workflow, Worklet, Session, Mapping)
2. **Parsing**: Structured extraction of transformations, fields, connectors, and configuration
3. **Canonical Modeling**: Normalization into a technology-neutral representation
4. **Expression Processing**: Building ASTs from Informatica expressions and translating them
5. **Code & Spec Generation**: PySpark/SQL/DLT/specs/reconciliation/tests
6. **AI & LLM Reasoning**: Explanation, summarization, risk analysis, optimization, reconstruction
7. **DAG Construction**: Building workflow-level execution graphs
8. **Delivery**: Through REST API, UI, files, and integration with catalogs/storage/CI

---

## Textual Architecture Diagram

```text
Informatica XMLs
  (Workflow / Worklet / Session / Mapping)
                 |
                 v
          [ XML Parsers ]
                 |
                 v
      [ Canonical Model + Lineage ]
                 |
                 v
      [ Expression AST Engine ]
                 |
                 v
      [ Code Generators ]
   (PySpark / SQL / DLT / Specs / Tests)
                 |
                 v
      [ AI & LLM Agents Layer ]
                 |
                 v
        [ Workflow DAG Engine ]
                 |
                 v
     [ API + UI + Deployment Layer ]
```

---

## Component Overview

### Input Layer
- **XML Files**: Workflow, Worklet, Session, Mapping XML files from Informatica

### Processing Layer
- **XML Parsers**: Extract structured data from XML
- **Canonical Model**: Technology-neutral representation
- **Expression Engine**: Parse and translate expressions
- **Code Generators**: Generate target platform code

### Intelligence Layer
- **AI Agents**: LLM-powered analysis and reasoning
- **DAG Engine**: Workflow execution graph construction

### Delivery Layer
- **Backend API**: RESTful API for programmatic access
- **Frontend UI**: Interactive web interface
- **Deployment**: Docker, Kubernetes, CI/CD integration

---

## Data Flow

1. **XML → Parsed Data**: XML parsers extract structured information
2. **Parsed Data → Canonical Model**: Normalization ensures consistency
3. **Canonical Model → Code**: Generators produce executable artifacts
4. **Canonical Model → AI Insights**: Agents provide analysis and recommendations
5. **Workflow XML → DAG**: DAG engine constructs execution graphs
6. **All → API/UI**: Results delivered through interfaces

---

## Key Design Principles

1. **Modularity**: Each component is independent and replaceable
2. **Canonical Model**: Single source of truth for all downstream processing
3. **Extensibility**: Easy to add new parsers, generators, or agents
4. **AI-Augmented**: LLMs enhance but don't replace deterministic logic
5. **Regeneration-Friendly**: Code can be regenerated from design specs

---

**Next**: Learn about the [Canonical Model](canonical_model.md) that powers the system.

