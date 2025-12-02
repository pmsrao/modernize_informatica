# Workflow DAG Engine

## Purpose

While mappings describe intra-table logic, workflows and worklets describe orchestration and execution order. The DAG engine:

- Reconstructs the execution graph from workflow/worklet connectors
- Validates that there are no cycles (unless explicitly allowed)
- Provides a DAG representation for:
  - UI visualization
  - AI workflow simulation
  - Migration of orchestration (e.g., to Airflow / jobs / tasks)

---

## Input

- Workflow XML
- Worklet XML
- Session XML
- The mapping-to-session relationships

---

## Output

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
  ],
  "execution_levels": [
    ["S_M_LOAD_CUSTOMER"],
    ["WK_BUILD_DIMS"],
    ["S_M_LOAD_FACT"]
  ]
}
```

This structure is later used by both the UI and workflow-related AI agents.

---

## Features

- **Topological Sorting**: Determines execution order
- **Cycle Detection**: Identifies circular dependencies
- **Execution Levels**: Groups tasks that can run in parallel
- **Visualization**: Multiple format support (DOT, JSON, Mermaid, SVG)

---

**Next**: Learn about [AI & LLM Agents](ai_agents.md) for intelligent analysis.

