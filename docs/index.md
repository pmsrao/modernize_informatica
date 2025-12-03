# Documentation Index

## Overview

Welcome to the Informatica Modernization Accelerator documentation. This index helps you navigate to the information you need.

## Documentation Structure

```
docs/
├── getting-started/     # Quick start guides
├── architecture/         # Architecture documentation
├── modules/             # Module-specific docs
├── guides/              # User guides
├── api/                 # API documentation
├── ai/                  # AI/LLM documentation
├── deployment/          # Deployment guides
├── development/         # Development docs
├── testing/            # Testing documentation
├── reference/          # Reference materials
└── archive/            # Legacy/archived docs
```

---

## 🚀 Getting Started

- **[Introduction](getting-started/introduction.md)** - Overview, problems addressed, and what the accelerator provides
- **[Setup Neo4j](getting-started/setup_neo4j.md)** - Neo4j installation and configuration guide

---

## 📚 Core Documentation

### [Architecture](architecture/system_architecture.md)
High-level architecture, logical flow, and system design overview.

### [Canonical Model](modules/canonical_model.md)
Technology-neutral representation of Informatica mappings, transformations, and lineage.

### [Parsing & Normalization](modules/parsing.md)
XML parsers, normalization process, and lineage capture.

### [Expression Engine](modules/expression_engine.md)
AST engine for parsing and translating Informatica expressions to PySpark/SQL.

### [Code Generators](modules/code_generators.md)
PySpark, DLT, SQL, spec, reconciliation, and test suite generators.

### [DAG Engine](modules/dag_engine.md)
Workflow DAG construction, visualization, and execution flow.

### [AI & LLM Agents](ai/ai_agents.md)
AI agents for explanation, summarization, risk analysis, and optimization.

### [API & Frontend](api/api_frontend.md)
Backend API endpoints and frontend UI components.

### [Deployment](deployment/deployment.md)
Docker deployment, enterprise integrations, and CI/CD.

### [Extensibility](deployment/extensibility.md)
How to extend the accelerator with new transformations, generators, and agents.

---

## 🧪 Testing

### [Testing Guide](testing/TESTING.md)
Main testing documentation with links to detailed guides.

**Detailed Testing Docs:**
- [Test Flow Guide](testing/test_flow_guide.md) - Comprehensive testing instructions
- [Phase 1 & 2 Testing](testing/phase1_phase2_testing_guide.md) - Phase testing guide
- [End-to-End Testing](testing/test_end_to_end.md) - Complete flow validation
- [Test Results](testing/frontend.md) - Frontend testing guide
- [Troubleshooting](testing/troubleshooting.md) - Common issues and solutions

---

## 📖 User Guides

- **[AI Agents Usage](guides/ai_agents_usage.md)** - How to use AI agents
- **[LLM Configuration](guides/llm_configuration.md)** - LLM setup and configuration
- **[LLM Quick Reference](guides/llm_quick_reference.md)** - Quick LLM reference
- **[Analysis Report](guides/analysis_report.md)** - Analysis of implementation status
- **[CLI Usage Guide](guides/cli_usage_guide.md)** - Command-line interface usage
- **[Testing and Validation](guides/testing_validation.md)** - Testing and validation guide
- **[Error Handling](guides/error_handling.md)** - Error categorization and recovery guide

---

## 🏗️ Architecture Diagrams

- [Architecture Diagram](architecture/architecture_diagram.drawio) - System architecture diagram
- [Architecture Mermaid](architecture/architecture_diagram.mermaid) - Architecture in Mermaid format
- [System Architecture](architecture/system_architecture.md) - Detailed system architecture

---

## 📚 Reference Materials

- **[Roadmap](reference/roadmap.md)** - Implementation status and next steps
- **[Lakebridge Comparison](reference/lakebridge_comparison.md)** - Comparison with Databricks Lakebridge
- **[Canonical Model Review](reference/canonical_model_review_gpt.md)** - External review of canonical model design

---

## 🔧 Development

- **[Solution Overview](development/solution.md)** - Complete solution architecture with detailed process documentation
- **[Code Generation Fixes](development/code_generation_fixes_summary.md)** - Code generation fixes
- **[Code Generation Issues](development/code_generation_issues_fixes.md)** - Code generation issues and fixes
- **[Neo4j Persistence Fix](development/neo4j_persistence_fix.md)** - Neo4j persistence fixes

---

## 🗄️ Archive

Legacy and archived documentation:
- [Graph Explorer Guide](archive/graph_explorer_guide.md)
- [DAG JSON Format](archive/dag_json_format.md)
- [Neo4j Persistence Explanation](archive/neo4j_persistence_explanation.md)
- [UI Enhancement Plans](archive/ui_enhancement_plan.md)

---

## 🚀 Quick Links

- **Getting Started**: See [Introduction](getting-started/introduction.md) and [Setup Neo4j](getting-started/setup_neo4j.md)
- **Testing**: See [Testing Guide](testing/TESTING.md)
- **Development**: See [Roadmap](reference/roadmap.md)
- **Architecture**: See [System Architecture](architecture/system_architecture.md) and [Solution Overview](development/solution.md)

---

**Last Updated**: December 2, 2025
