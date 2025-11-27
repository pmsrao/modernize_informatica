# Introduction

## Overview

The **Informatica Modernization Accelerator** is an end-to-end framework to reverse engineer, analyze, and modernize legacy Informatica ETL workloads into a **lakehouse-native** ecosystem (for example, PySpark + Delta + Delta Live Tables on Databricks or Spark).

It is designed for organisations that:

- Have **large Informatica estates** (many workflows, worklets, sessions, mappings)
- Want to **migrate to modern data platforms** on the cloud
- Need **traceability and explainability** of ETL logic
- Want to **reduce migration risk and effort** by using automation and AI

---

## Problems This Accelerator Addresses

1. **Opaque ETL Logic**  
   - Business rules are buried inside complex transformations, expressions, and sessions.  
   - Very little documentation exists; understanding impact requires manual digging.

2. **High Migration Cost & Risk**  
   - Traditional migration is manual, SME-driven, and slow.  
   - It is easy to miss critical rules, edge cases, and data quality logic.

3. **Lack of Lineage & Impact Visibility**  
   - Understanding "where a field comes from" or "what breaks if we change this" is non-trivial.  
   - Cross-cutting lineage across workflows, sessions, mappings is hard to build.

4. **Limited Use of AI**  
   - Most attempts at modernization don't exploit LLMs to: explain, summarize, detect risk, or auto-fix logic.

---

## What the Accelerator Provides

- Automated **parsing** of Informatica XML assets (workflow, worklet, session, mapping)
- A technology-neutral **Canonical Model** for mappings, transformations, and lineage
- An **Expression AST Engine** to interpret Informatica expressions and translate them to PySpark/SQL
- **Code Generators** for:
  - PySpark pipelines
  - Delta Live Tables pipelines
  - SQL
  - Mapping specifications (Markdown)
  - Reconciliation queries
  - Test suites
- **AI & LLM Agents** that:
  - Explain rules in natural language
  - Summarize mappings and workflows
  - Highlight risks and anti-patterns
  - Suggest optimizations
  - Simulate workflow behavior
  - Attempt reconstruction from partial information
- A **Workflow DAG Engine** that reconstructs end-to-end ETL execution flow
- **Backend API** and **Frontend UI** for interactive usage
- **Deployment & Enterprise Extensions** for integration into a broader data platform

---

## Documentation Structure

This documentation is organized into focused topics:

- **[Architecture](architecture.md)** - System design and logical flow
- **[Canonical Model](canonical_model.md)** - Technology-neutral representation
- **[Parsing](parsing.md)** - XML parsing and normalization
- **[Expression Engine](expression_engine.md)** - AST and translation
- **[Code Generators](code_generators.md)** - Code generation
- **[DAG Engine](dag_engine.md)** - Workflow DAG construction
- **[AI Agents](ai_agents.md)** - AI and LLM integration
- **[API & Frontend](api_frontend.md)** - User interfaces
- **[Deployment](deployment.md)** - Deployment and enterprise integration
- **[Extensibility](extensibility.md)** - How to extend the accelerator

See [Documentation Index](index.md) for complete navigation.

---

**Next**: Read [Architecture](architecture.md) to understand the system design.

