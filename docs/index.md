# Documentation Index

## Overview

Welcome to the Informatica Modernization Accelerator documentation. This index helps you navigate to the information you need.

---

## 📚 Core Documentation

### [Introduction](introduction.md)
Overview, problems addressed, and what the accelerator provides.

### [Architecture](architecture.md)
High-level architecture, logical flow, and system design overview.

### [Canonical Model](canonical_model.md)
Technology-neutral representation of Informatica mappings, transformations, and lineage.

### [Parsing & Normalization](parsing.md)
XML parsers, normalization process, and lineage capture.

### [Expression Engine](expression_engine.md)
AST engine for parsing and translating Informatica expressions to PySpark/SQL.

### [Code Generators](code_generators.md)
PySpark, DLT, SQL, spec, reconciliation, and test suite generators.

### [DAG Engine](dag_engine.md)
Workflow DAG construction, visualization, and execution flow.

### [AI & LLM Agents](ai_agents.md)
AI agents for explanation, summarization, risk analysis, and optimization.

### [API & Frontend](api_frontend.md)
Backend API endpoints and frontend UI components.

### [Deployment](deployment.md)
Docker deployment, enterprise integrations, and CI/CD.

### [Extensibility](extensibility.md)
How to extend the accelerator with new transformations, generators, and agents.

---

## 🧪 Testing

### [Testing Guide](../TESTING.md)
Main testing documentation with links to detailed guides.

**Detailed Testing Docs:**
- [Testing Guide](test/guide.md) - Comprehensive testing instructions
- [Test Results](test/results.md) - Test results and validation
- [Troubleshooting](test/troubleshooting.md) - Common issues and solutions
- [Frontend Testing](test/frontend.md) - Frontend testing guide

---

## 📖 Guides

### [Design Specification](design_spec.md)
Formal architectural and component-centric design specification.

### [Solution Overview](../solution.md)
Complete solution architecture including graph-first design and two-part architecture.

### [Roadmap](../roadmap.md)
Implementation status, completed items, and next steps.

### [End-to-End Testing](../test_end_to_end.md)
Comprehensive testing guide for complete flow validation.

### [Analysis Report](guides/analysis_report.md)
Analysis of current implementation status and gaps.

---

## 🏗️ Architecture Diagrams

- [Architecture Diagram](architecture/architecture_diagram.drawio) - System architecture diagram

---

## 🚀 Quick Links

- **Getting Started**: See [Solution Overview](../solution.md) and [Architecture](architecture.md)
- **Testing**: See [End-to-End Testing Guide](../test_end_to_end.md)
- **Development**: See [Roadmap](../roadmap.md)
- **Design**: See [Design Specification](../design_spec.md)

---

## 📝 Document Structure

```
docs/
├── index.md (this file)
├── architecture.md
├── canonical_model.md
├── parsing.md
├── expression_engine.md
├── code_generators.md
├── dag_engine.md
├── ai_agents.md
├── api_frontend.md
├── deployment.md
├── extensibility.md
├── architecture/
│   └── architecture_diagram.drawio
├── guides/
│   ├── next_steps.md
│   └── analysis_report.md
└── test/
    ├── guide.md
    ├── results.md
    ├── troubleshooting.md
    └── frontend.md
```

---

**Last Updated**: November 27, 2025

