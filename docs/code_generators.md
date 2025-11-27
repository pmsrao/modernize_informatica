# Code Generators

## Overview

The code generators turn the canonical model + AST expressions into executable artifacts suitable for lakehouse platforms.

---

## Types of Generators

### 1. PySpark Generator
Builds DataFrame pipelines:
- Reads from sources (tables/files)
- Applies column derivations using AST expressions
- Implements joins, lookups, filters, aggregations
- Writes to Delta tables

### 2. Delta Live Tables Generator
Generates DLT pipelines with:
- `@dlt.table` functions
- incremental load semantics
- dependencies between tables expressed via `spark.table()` or `dlt.read()`

### 3. SQL Generator
Generates equivalent SQL:
- SELECT statements
- WITH clauses
- target views or CTAS-style statements

### 4. Spec / Documentation Generator
Produces Markdown mapping specifications:
- sources, targets
- column-level mapping
- expressions (original + PySpark/SQL form)
- business-level descriptions (optionally AI-generated)

### 5. Reconciliation Generator
Builds queries to:
- compare row counts
- compare aggregates
- validate distribution of key metrics

### 6. Test Suite Generator
Creates pytest-based tests:
- structural tests (schema, presence of fields)
- golden-row tests (small synthetic datasets)
- expression evaluation validations

---

## Design Considerations

- Generated code should be:
  - Readable and idiomatic
  - Organized in modular functions/modules
  - Structured for future manual refinement
- All generators rely only on the canonical model so that regeneration is straightforward.

---

**Next**: Learn about the [DAG Engine](dag_engine.md) for workflow orchestration.

