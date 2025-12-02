# DAG JSON Format

## Overview

The `dag_complex.json` file in `samples/complex/` is a **sample output file** that demonstrates the structure of a DAG (Directed Acyclic Graph) generated from a workflow.

## Purpose

This file is **NOT meant to be uploaded**. It's a reference example showing:
- How workflow DAGs are structured
- What the DAG builder produces
- The format used for workflow visualization

## File Structure

```json
{
  "workflow_name": "WF_ENTERPRISE_ETL_PIPELINE",
  "nodes": [
    {
      "id": "S_M_LOAD_CUSTOMERS",
      "name": "S_M_LOAD_CUSTOMERS",
      "type": "SESSION",
      "metadata": {
        "mapping": "M_LOAD_CUSTOMERS",
        "enabled": true
      }
    }
  ],
  "edges": [
    {
      "from": "S_M_LOAD_CUSTOMERS",
      "to": "WK_DIMENSIONS_BUILD",
      "type": "SUCCESS"
    }
  ],
  "execution_levels": [
    ["S_M_LOAD_CUSTOMERS", "S_M_LOAD_PRODUCTS", "S_M_LOAD_ORDERS"],
    ["WK_DIMENSIONS_BUILD"]
  ],
  "has_cycles": false,
  "parallel_tasks": 3,
  "total_tasks": 9,
  "total_worklets": 2
}
```

## How to Generate DAGs

To generate a DAG from a workflow:

1. **Upload workflow XML** using File Browser or Upload & Parse
2. **Go to Lineage tab**
3. **Select the workflow file**
4. **Click "Load DAG"**
5. The DAG will be visualized and can be exported

## Export Formats

You can export DAGs in multiple formats:
- **JSON**: Machine-readable format (like `dag_complex.json`)
- **DOT**: Graphviz format
- **Mermaid**: Mermaid diagram format
- **SVG**: Vector image format

## Note

The upload functionality only accepts **XML files** because:
- The system parses Informatica XML files
- DAGs are generated FROM workflows, not uploaded as DAGs
- JSON files are output formats, not input formats

If you need to visualize a pre-built DAG JSON file, you would need to:
1. Use the DAG visualization API directly
2. Or modify the frontend to accept JSON DAG files (future enhancement)

