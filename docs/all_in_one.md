# Informatica Modernization Accelerator — Full Documentation Portal

## 1. Introduction

The **Informatica Modernization Accelerator** is an end-to-end framework to reverse engineer, analyze, and modernize legacy Informatica ETL workloads into a **lakehouse-native** ecosystem (for example, PySpark + Delta + Delta Live Tables on Databricks or Spark).

It is designed for organisations that:

- Have **large Informatica estates** (many workflows, worklets, sessions, mappings)
- Want to **migrate to modern data platforms** on the cloud
- Need **traceability and explainability** of ETL logic
- Want to **reduce migration risk and effort** by using automation and AI

### 1.1 Problems This Accelerator Addresses

1. **Opaque ETL Logic**  
   - Business rules are buried inside complex transformations, expressions, and sessions.  
   - Very little documentation exists; understanding impact requires manual digging.

2. **High Migration Cost & Risk**  
   - Traditional migration is manual, SME-driven, and slow.  
   - It is easy to miss critical rules, edge cases, and data quality logic.

3. **Lack of Lineage & Impact Visibility**  
   - Understanding “where a field comes from” or “what breaks if we change this” is non-trivial.  
   - Cross-cutting lineage across workflows, sessions, mappings is hard to build.

4. **Limited Use of AI**  
   - Most attempts at modernization don’t exploit LLMs to: explain, summarize, detect risk, or auto-fix logic.

### 1.2 What the Accelerator Provides

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

This document is the **single documentation portal** for the accelerator. It is intended to be used alongside `design_spec.md` and the codebase.

---

## 2. High-Level Architecture

### 2.1 Logical Flow

At the highest level, the system can be viewed as:

1. **Input**: Informatica XML files (Workflow, Worklet, Session, Mapping)
2. **Parsing**: Structured extraction of transformations, fields, connectors, and configuration
3. **Canonical Modeling**: Normalization into a technology-neutral representation
4. **Expression Processing**: Building ASTs from Informatica expressions and translating them
5. **Code & Spec Generation**: PySpark/SQL/DLT/specs/reconciliation/tests
6. **AI & LLM Reasoning**: Explanation, summarization, risk analysis, optimization, reconstruction
7. **DAG Construction**: Building workflow-level execution graphs
8. **Delivery**: Through REST API, UI, files, and integration with catalogs/storage/CI

### 2.2 Textual Architecture Diagram

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

## 3. Canonical Model

### 3.1 Purpose

The canonical model serves as a technology-neutral representation of Informatica mappings, transformations, and their relationships. It abstracts away Informatica-specific XML structures into a standardized format that can be used by all downstream components (generators, AI agents, lineage engines).

### 3.2 Structure

The canonical model captures:
- **Mappings**: Sources, targets, transformations, and their connections
- **Transformations**: Types, ports, expressions, and configuration
- **Fields**: Names, data types, expressions, and lineage
- **Connections**: Data flow between transformations
- **Metadata**: Names, descriptions, and annotations

---

## 4. Parsing & Normalization

### 4.1 XML Parsers

The system includes specialized parsers for each Informatica asset type:

- **Mapping Parser**: Extracts transformations, sources, targets, and expressions
- **Workflow Parser**: Extracts tasks, links, and execution order
- **Session Parser**: Extracts session configuration and mapping references
- **Worklet Parser**: Extracts worklet structure and embedded tasks

### 4.2 Normalization

The normalization layer converts parsed XML structures into the canonical model format, ensuring:
- Consistent naming conventions
- Standardized data types
- Unified transformation representations
- Normalized expression formats

### 4.3 Lineage

The canonical model captures:

- **Column-level lineage**: which source columns feed each derived field
- **Transformation-level lineage**: how data flows through SQ → EXP → LKUP → AGG → TARGET
- **Workflow/session-level lineage**: which mappings feed which targets in the workflow DAG

This lineage is used by:

- Impact analysis agents
- Documentation generators
- UI lineage views
- Governance integration (catalogs)

### 4.4 SCD & Incremental Logic Detection

Heuristics (and optionally AI hints) detect:

- **SCD2 patterns**:
  - EFFECTIVE_FROM, EFFECTIVE_TO columns
  - UPDATE STRATEGY usage
  - Historical tracking flags
- **Incremental Load**:
  - Filters on LAST_UPDATED_DATE or similar columns
  - CDC-like conditions in Source Qualifier or Filter transformations

These annotations influence code generation, especially for DLT and PySpark.

---

## 5. Expression AST Engine

### 5.1 Role

Informatica expressions are complex and tool-specific. The AST engine:

1. Parses these expressions into a structured AST
2. Translates them to PySpark and SQL
3. Provides inputs for AI-based explanations and risk analysis

### 5.2 Stages

1. **Tokenization**
   - Splits expression into tokens: identifiers, functions, literals, operators.

2. **Parsing into AST**
   - Applies a grammar to build a tree:
     - binary operations (+, -, *, /, <, >, =…)
     - function calls (IIF, NVL, DECODE, TO_CHAR, etc.)
     - conditionals (nested IIF)

3. **AST Normalization**
   - Aligns function semantics with target platforms.

4. **Translation**
   - AST → PySpark expression string
   - AST → SQL expression string

### 5.3 Example

**Informatica Expression**
```
IIF(AGE < 30, 'YOUNG', 'OTHER')
```

**PySpark Translation**
```python
F.when(F.col("AGE") < 30, F.lit("YOUNG")).otherwise("OTHER")
```

**SQL Translation**
```sql
CASE WHEN AGE < 30 THEN 'YOUNG' ELSE 'OTHER' END
```

The AST engine ensures a single source of truth for these semantics, which reduces drift between SQL and PySpark.

---

## 6. Code Generators

### 6.1 Overview

The code generators turn the canonical model + AST expressions into executable artifacts suitable for lakehouse platforms.

### 6.2 Types of Generators

1. **PySpark Generator**
   - Builds DataFrame pipelines:
     - Reads from sources (tables/files)
     - Applies column derivations using AST expressions
     - Implements joins, lookups, filters, aggregations
     - Writes to Delta tables

2. **Delta Live Tables Generator**
   - Generates DLT pipelines with:
     - `@dlt.table` functions
     - incremental load semantics
     - dependencies between tables expressed via `spark.table()` or `dlt.read()`

3. **SQL Generator**
   - Generates equivalent SQL:
     - SELECT statements
     - WITH clauses
     - target views or CTAS-style statements

4. **Spec / Documentation Generator**
   - Produces Markdown mapping specifications:
     - sources, targets
     - column-level mapping
     - expressions (original + PySpark/SQL form)
     - business-level descriptions (optionally AI-generated)

5. **Reconciliation Generator**
   - Builds queries to:
     - compare row counts
     - compare aggregates
     - validate distribution of key metrics

6. **Test Suite Generator**
   - Creates pytest-based tests:
     - structural tests (schema, presence of fields)
     - golden-row tests (small synthetic datasets)
     - expression evaluation validations

### 6.3 Design Considerations

- Generated code should be:
  - Readable and idiomatic
  - Organized in modular functions/modules
  - Structured for future manual refinement
- All generators rely only on the canonical model so that regeneration is straightforward.

---

## 7. Workflow DAG Engine

### 7.1 Purpose

While mappings describe intra-table logic, workflows and worklets describe orchestration and execution order. The DAG engine:

- Reconstructs the execution graph from workflow/worklet connectors
- Validates that there are no cycles (unless explicitly allowed)
- Provides a DAG representation for:
  - UI visualization
  - AI workflow simulation
  - Migration of orchestration (e.g., to Airflow / jobs / tasks)

### 7.2 Input

- Workflow XML
- Worklet XML
- Session XML
- The mapping-to-session relationships

### 7.3 Output (Conceptual)

```json
{
  "nodes": [
    { "id": "S_M_LOAD_CUSTOMER", "type": "SESSION" },
    { "id": "WK_BUILD_DIMS", "type": "WORKLET" },
    { "id": "S_M_LOAD_FACT", "type": "SESSION" }
  ],
  "edges": [
    { "from": "S_M_LOAD_CUSTOMER", "to": "WK_BUILD_DIMS" },
    { "from": "WK_BUILD_DIMS", "to": "S_M_LOAD_FACT" }
  ]
}
```

This structure is later used by both the UI and workflow-related AI agents.

---

## 8. AI & LLM Agents

### 8.1 Purpose

The AI layer is designed to augment human understanding and decision-making, not to replace deterministic parsing and generation.

It answers questions like:

- "What does this mapping actually do?"
- "Which transformations are risky or brittle?"
- "What is a simpler way to express this logic?"
- "What is the impact of changing this column?"
- "Given partial clues, what might the original mapping have been?"

### 8.2 LLM Layer

The LLM Manager abstracts away providers:

- OpenAI (standard GPT models)
- Azure OpenAI
- Local LLM (llama.cpp, vLLM, etc.)

Selection is controlled by configuration (e.g., an environment variable `LLM_PROVIDER`).

Prompt templates are centralized so that:

- Expression explanation
- Mapping summarization
- Risk analysis
- Suggestion generation
- Code fixing
- Reconstruction

…all follow consistent patterns.

### 8.3 Core AI Agents

1. **Rule Explainer Agent**
   - Input:
     - field name
     - original Informatica expression
     - AST / canonical context
   - Output:
     - human-readable explanation of the rule
   - Example:
     - "AGE_BUCKET classifies customers as 'YOUNG' when AGE is less than 30, and 'OTHER' otherwise."

2. **Mapping Summary Agent**
   - Input:
     - canonical mapping model
   - Output:
     - narrative summary of what the mapping does, which tables it reads from, and what outputs it produces.

3. **Risk Detection Agent**
   - Scans expressions and transformation patterns to identify:
     - risky casts
     - suspicious default values
     - potential data loss
     - complex nested logic that might be fragile

4. **Suggestion Agent**
   - Offers optimization ideas:
     - simplification of expressions
     - more idiomatic use of Spark functions
     - splitting very complex transformations

### 8.4 Advanced AI Agents

1. **Code Fix Agent**
   - Input:
     - generated PySpark code + error hints (optional)
   - Output:
     - corrected version of the code, preserving semantics where possible

2. **Mapping Reconstruction Agent**
   - Input:
     - partial XML
     - log fragments
     - lineage clues
     - target table definitions
   - Output:
     - a hypothesized canonical mapping model or at least a structured description

3. **Impact Analysis Agent**
   - Given:
     - a mapping, column, or transformation
   - Produces:
     - descriptions of which downstream elements depend on it
     - prioritization of what must be regression-tested

4. **Workflow Simulation Agent**
   - Uses:
     - DAG model
     - metadata about tasks
   - To:
     - simulate expected run sequences
     - highlight bottlenecks or single points of failure

---

## 9. Backend API & Frontend UI

### 9.1 Backend API (FastAPI)

The backend offers endpoints such as:

- **POST /parse**
  - Input: one or more XML files
  - Output: canonical model + lineage + basic stats
- **POST /generate/pyspark**
  - Input: canonical mapping name or model
  - Output: PySpark code
- **POST /generate/spec**
  - Input: canonical mapping model
  - Output: mapping specification (Markdown/text)
- **POST /ai/explain**
  - Input: mapping + scope
  - Output: AI-generated explanations, summaries, risk notes
- **POST /dag/build**
  - Input: workflow/worklet/session data
  - Output: DAG JSON
- **GET /health**
  - Basic health probe

### 9.2 Frontend UI (React + Vite)

Key screens:

1. **Upload Screen**
   - Upload XML(s)
   - Trigger parsing and canonical model creation

2. **Mapping Explorer**
   - List mappings
   - View details
   - Drill into sources, targets, transformations

3. **Spec Viewer**
   - Render mapping_spec.md for a mapping

4. **Code Viewer**
   - Show generated PySpark, SQL, or DLT code
   - Allow copy/export

5. **Lineage & DAG Viewer**
   - Visualize mapping-level lineage
   - Visualize workflow DAGs

6. **AI Insights Panel**
   - Show rule explanations
   - Mapping summaries
   - Risk & optimization suggestions

---

## 10. Deployment & Enterprise Integrations

### 10.1 Deployment

The platform is designed to be deployed with:

- **Docker images**:
  - Backend (FastAPI + Uvicorn)
  - Frontend (built React assets served via Node or a static server)
- **Docker Compose**:
  - Ties together API + UI
  - Handles basic networking
- **CI/CD** (e.g., GitHub Actions):
  - Run tests on push
  - Build images on tag
  - Publish to a registry (if configured)

Kubernetes / Helm–based deployments can be added on top of this, but are not strictly required.

### 10.2 Enterprise Extensions

To fit into enterprise platforms, the accelerator can integrate with:

- **Storage**:
  - S3
  - ADLS
  - GCS
- **Catalogs**:
  - Glue
  - Purview
  - Dataplex
- **Version Store**:
  - JSON snapshots of:
    - canonical mappings
    - generated code
    - AI insight outputs
- **Notifications**:
  - Slack/Teams webhooks for:
    - migration progress
    - risk alerts
    - job completion reports

---

## 11. Testing Strategy

### 11.1 Types of Tests

1. **Parser Tests**
   - Use sample XMLs (like workflow_complex.xml, mapping_complex.xml)
   - Assert:
     - correct number of transformations
     - correct connector wiring
     - correct field extraction

2. **Canonical Model Tests**
   - Validate:
     - transformation normalization
     - lineage correctness for key columns
     - SCD detection behavior on known cases

3. **Expression Engine Tests**
   - Golden set of expressions with expected:
     - AST shape
     - PySpark translation
     - SQL translation

4. **Generator Tests**
   - Confirm structure and key contents of:
     - PySpark pipelines
     - DLT flows
     - SQL scripts
     - Specs

5. **DAG Tests**
   - Validate that the DAG from a workflow:
     - matches expected ordering
     - identifies error if cycles appear unexpectedly

6. **AI-Agent Tests** (non-deterministic but structured)
   - Validate:
     - schema/shape of responses
     - that simple prompts return non-empty results
   - Avoid strict string matching for LLM outputs.

---

## 12. Extensibility & Regeneration

### 12.1 Extensibility

Areas you can extend:

- **Transformations**:
  - Support additional Informatica transformation types
  - Add new canonical types or subtypes
- **Target Technologies**:
  - Add generators for:
    - dbt models
    - native Snowflake SQL
    - other orchestration frameworks
- **AI Agents**:
  - Define new prompt templates
  - Implement new agent classes for specialized analyses
- **LLM Providers**:
  - Implement wrappers for other hosted or on-prem LLMs
  - Plug them into the LLM Manager interface

### 12.2 Regeneration Using Design Specs

Two main documents act as source-of-truth:

- `design_spec.md` — formal architectural & component-centric design
- `infa_modernizer_full_portal.md` — this portal (conceptual + narrative)

With these, you can instruct Cursor (or any AI coding assistant) to:

- Regenerate a specific module (e.g., PySpark generator) based on updated design
- Refactor AST rules to add new functions
- Introduce new transformation patterns while keeping tests aligned

A typical regeneration workflow:

1. Update `design_spec.md` to reflect new design decisions.
2. Use a prompt like:
   "Based on design_spec.md section 'Expression Engine' and 'Code Generators', regenerate expression_engine/translator_pyspark.py to support the additional DATE_DIFF function and ensure tests are updated accordingly."
3. Run test suite.
4. Commit updated modules and version snapshots.

---

## 13. Conclusion

The Informatica Modernization Accelerator is a modular, AI-augmented, regeneration-friendly framework that:

- Makes legacy ETL transparent and explainable
- Reduces modernization effort through automation
- Adds AI reasoning to help engineers understand, validate, and improve logic
- Provides a clear path from Informatica to lakehouse-native pipelines

This documentation portal, together with `design_spec.md` and your codebase, should give you:

- A strong architectural foundation
- A shared conceptual model across the team
- A stable base for future evolution and new capabilities

---

## Next Steps

You can now:

1. Use this document as the single source of truth for the accelerator
2. Reference it alongside `design_spec.md` for implementation details
3. Extend it as new features are added

If you'd like, next steps could include:

- Generate a **Developer Onboarding Guide** (`developers_guide.md`)
- Or a **Regeneration Playbook** (`regeneration_instructions.md`) with concrete Cursor prompts tied to this design.
