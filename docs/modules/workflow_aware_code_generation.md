# Workflow-Aware Code Generation - Implementation Guide

## Overview

The code generation process has been enhanced to support **workflow-aware generation** that organizes code by workflow structure, making it easier to migrate Informatica workloads to modern platforms.

## Key Features

### 1. Workflow-Based Repository Structure

Code is now organized to reflect the original Informatica hierarchy:

```
generated_code/
├── workflows/
│   ├── customer_orders_etl/
│   │   ├── README.md                    # Workflow documentation
│   │   ├── sessions/
│   │   │   ├── load_customer/
│   │   │   │   ├── session_config.json  # Session configuration
│   │   │   │   └── mappings/
│   │   │   │       ├── load_customer/
│   │   │   │       │   ├── load_customer_pyspark.py
│   │   │   │       │   ├── load_customer_dlt.py
│   │   │   │       │   ├── load_customer_sql.sql
│   │   │   │       │   └── mapping_spec.md
│   │   │   │       └── ingest_customers/
│   │   │   │           ├── ingest_customers_pyspark.py
│   │   │   │           └── ...
│   │   │   └── load_orders/
│   │   │       └── mappings/
│   │   │           └── load_order_fact/
│   │   │               └── ...
│   │   └── orchestration/
│   │       └── workflow_dag.json        # Workflow DAG structure
│   └── daily_batch/
│       └── ...
├── shared/
│   ├── common_utils.py                  # Reusable functions
│   └── config/
│       ├── database_config.py
│       └── spark_config.py
└── generation_summary.json
```

### 2. Descriptive File Naming

Code files now use descriptive names based on mapping names:
- `load_customer_pyspark.py` (instead of `pyspark_code.py`)
- `load_customer_dlt.py` (instead of `dlt_pipeline.py`)
- `load_customer_sql.sql` (instead of `sql_queries.sql`)

### 3. Neo4j Integration

Code generation now queries Neo4j to:
- Get all workflows
- Get workflow structure (sessions, mappings)
- Load canonical models from graph or JSON files
- Organize code by workflow hierarchy

### 4. Shared/Reusable Code

Common utilities and configuration files are generated outside the workflow structure in the `shared/` directory:
- `common_utils.py`: Reusable transformation patterns
- `config/database_config.py`: Database connection configuration
- `config/spark_config.py`: Spark session configuration

## Usage

### Basic Usage

```bash
# Generate code with workflow-aware organization (default)
make code

# Or using Python directly
python scripts/test_flow.py code --output-dir test_log/generated
```

### How It Works

1. **Checks for Neo4j**: If graph store is enabled, uses workflow-aware generation
2. **Queries Workflows**: Gets all workflows from Neo4j
3. **For Each Workflow**:
   - Gets workflow structure (sessions, mappings)
   - Creates workflow directory structure
   - Generates workflow README
4. **For Each Session**:
   - Creates session directory
   - Generates session configuration
5. **For Each Mapping**:
   - Loads canonical model (from Neo4j or JSON files)
   - Generates PySpark, DLT, SQL code
   - Saves with descriptive filenames
   - Generates mapping specification
6. **Generates Shared Code**:
   - Common utilities
   - Configuration files
7. **Generates Workflow Orchestration**:
   - Workflow DAG JSON
   - Execution dependencies

### Fallback Behavior

If Neo4j is not available or no workflows are found, the system falls back to file-based generation:
- Searches for canonical model JSON files
- Generates code in flat per-mapping structure
- Uses descriptive filenames

## Configuration

### Enable Graph Store

In your `.env` file:

```bash
ENABLE_GRAPH_STORE=true
GRAPH_FIRST=true
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

### Disable Workflow-Aware Generation

To use flat structure even with Neo4j:

```python
flow.generate_code(output_dir, workflow_aware=False)
```

## Implementation Details

### New Graph Queries

Added to `src/graph/graph_queries.py`:

- `list_workflows()`: List all workflows in graph
- `get_workflow_structure(workflow_name)`: Get complete workflow structure
- `get_mappings_in_workflow(workflow_name)`: Get all mappings in workflow
- `get_sessions_in_workflow(workflow_name)`: Get all sessions in workflow

### Enhanced Code Generation

Updated `scripts/test_flow.py`:

- `generate_code()`: Main entry point with workflow-aware support
- `_generate_code_workflow_aware()`: Workflow-aware generation logic
- `_generate_code_file_based()`: Fallback file-based generation
- `_load_canonical_model_from_files()`: Load models from JSON files
- `_generate_workflow_readme()`: Generate workflow documentation
- `_generate_session_config()`: Generate session configuration
- `_generate_mapping_spec()`: Generate mapping specifications
- `_generate_workflow_orchestration()`: Generate workflow DAG
- `_generate_shared_code()`: Generate reusable code

## Benefits

1. **Better Organization**: Code structure matches original Informatica hierarchy
2. **Easier Migration**: Clear mapping from source to target structure
3. **Reusable Code**: Common patterns extracted to shared directory
4. **Documentation**: Auto-generated READMEs and specifications
5. **Scalability**: Supports large migrations with many workflows

## Migration Path

For existing projects:

1. **Parse and enhance** all mappings (creates canonical models in Neo4j)
2. **Run code generation** with workflow-aware mode
3. **Review generated structure** in `generated_code/workflows/`
4. **Customize shared code** in `generated_code/shared/`
5. **Use generated code** as starting point for migration

## Example Output

After running `make code`, you'll see:

```
STEP G: Generate Code
============================================================
✅ Graph store enabled - using workflow-aware generation

📋 Found 2 workflow(s) in graph

🔄 Processing workflow: WF_CUSTOMER_ORDERS_ETL
   ⚙️  Processing session: S_LOAD_CUSTOMER
      📋 Generating code for mapping: M_LOAD_CUSTOMER
         ✅ Generated PYSPARK: load_customer_pyspark.py
         ✅ Generated DLT: load_customer_dlt.py
         ✅ Generated SQL: load_customer_sql.sql
      📋 Generating code for mapping: M_INGEST_CUSTOMERS
         ✅ Generated PYSPARK: ingest_customers_pyspark.py
         ...

📦 Generating shared/reusable code...
   ✅ Generated shared code in: generated_code/shared

📊 Summary:
   Workflows: 2
   Generated files: 12
   Failed: 0
   Shared code files: 3
```

## Related Documentation

- **Code Generation Workflow**: `docs/code_generation_workflow.md`
- **Solution Process**: `docs/solution_process_details.md`
- **Neo4j Setup**: `docs/setup_neo4j.md`

