# Parsing & Normalization

## XML Parsers

The system includes specialized parsers for each Informatica asset type:

- **Mapping Parser**: Extracts transformations, sources, targets, and expressions
- **Workflow Parser**: Extracts tasks, links, and execution order
- **Session Parser**: Extracts session configuration and mapping references
- **Worklet Parser**: Extracts worklet structure and embedded tasks

---

## Normalization

The normalization layer converts parsed XML structures into the canonical model format, ensuring:

- Consistent naming conventions
- Standardized data types
- Unified transformation representations
- Normalized expression formats

---

## Lineage

The canonical model captures:

- **Column-level lineage**: which source columns feed each derived field
- **Transformation-level lineage**: how data flows through SQ → EXP → LKUP → AGG → TARGET
- **Workflow/session-level lineage**: which mappings feed which targets in the workflow DAG

This lineage is used by:

- Impact analysis agents
- Documentation generators
- UI lineage views
- Governance integration (catalogs)

---

## SCD & Incremental Logic Detection

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

**Next**: Learn about the [Expression Engine](expression_engine.md) that processes Informatica expressions.

