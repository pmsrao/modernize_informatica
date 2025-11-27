
# Sample Files — Option D (Comprehensive Test Set)

This folder contains **realistic, complex Informatica XML assets** and a DAG JSON to fully test the modernization platform.

## Contents

### 1. workflow_complex.xml
A workflow with:
- 2 sessions
- 1 worklet
- Directed flow with success links
- Tests workflow parser + lineage engine

### 2. worklet_complex.xml
A multi-session worklet used inside the workflow.

Tests:
- Nested structure
- TaskInstances
- Connector flow

### 3. mapping_complex.xml
A complex mapping including:
- Source Qualifier
- Expression transformation
- Lookup
- Aggregator
- Connectors across transformations

Covers:
- Expression parsing
- Lookup modeling
- Aggregator grouping
- Full graph lineage reconstruction

### 4. session_complex.xml
Session environment configuration:
- Connection details
- Tracing level
- Commit interval

Tests:
- Session parser
- Task → Mapping linkage

### 5. dag_complex.json
Synthetic DAG representing:
- Node-level workflow
- Relationships among tasks

Useful for:
- DAG builder
- Workflow simulation agent (Batch 15)

---

This dataset provides **full coverage** across:
- Workflow parsing
- Worklet parsing
- Mapping parsing
- Expression & Lookup modeling
- Aggregator handling
- Session config extraction
- DAG simulation
- All AI/LLM agents (Batch 11, 14, 15)

