# Code Generation

## Table of Contents
1. [Overview](#overview)
2. [Types of Generators](#types-of-generators)
3. [Code Generation Workflow](#code-generation-workflow)
4. [Workflow-Aware Generation](#workflow-aware-generation)
5. [Repository Structure](#repository-structure)
6. [Implementation Details](#implementation-details)
7. [Usage and Configuration](#usage-and-configuration)

---

## Overview

The code generators turn the canonical model + AST expressions into executable artifacts suitable for lakehouse platforms. All generators rely only on the canonical model so that regeneration is straightforward.

### Key Principles

- **Readable and Idiomatic**: Generated code should be readable and follow platform best practices
- **Modular Organization**: Code organized in modular functions/modules
- **Structured for Refinement**: Code is structured for future manual refinement
- **Canonical Model Driven**: All generators use only the canonical model as input

---

## Types of Generators

### 1. PySpark Generator

Builds DataFrame pipelines:
- Reads from sources (tables/files)
- Applies column derivations using AST expressions
- Implements joins, lookups, filters, aggregations
- Writes to Delta tables

**Output**: Python files with PySpark DataFrame operations

### 2. Delta Live Tables Generator

Generates DLT pipelines with:
- `@dlt.table` functions
- Incremental load semantics
- Dependencies between tables expressed via `spark.table()` or `dlt.read()`

**Output**: Python files with DLT pipeline definitions

### 3. SQL Generator

Generates equivalent SQL:
- SELECT statements
- WITH clauses
- Target views or CTAS-style statements

**Output**: SQL files with equivalent SQL queries

### 4. Spec / Documentation Generator

Produces Markdown mapping specifications:
- Sources, targets
- Column-level mapping
- Expressions (original + PySpark/SQL form)
- Business-level descriptions (optionally AI-generated)

**Output**: Markdown specification files

### 5. Reconciliation Generator

Builds queries to:
- Compare row counts
- Compare aggregates
- Validate distribution of key metrics

**Output**: Reconciliation query files

### 6. Test Suite Generator

Creates pytest-based tests:
- Structural tests (schema, presence of fields)
- Golden-row tests (small synthetic datasets)
- Expression evaluation validations

**Output**: Python test files

### 7. Orchestration Generator

Generates workflow orchestration code:
- Airflow DAGs
- Databricks Workflows
- Prefect flows

**Output**: Orchestration code files (Python/YAML)

---

## Code Generation Workflow

### CLI Workflow: Upload → Parse → Enhance → Code → Review

```
1. Upload Files
   ↓
2. Parse (all components: transformations, pipelines, tasks, sub pipelines)
   ↓
3. Enhance (transformations only - creates canonical models)
   ↓
4. Code Generation (transformations only - uses canonical models)
   ↓
5. Review (generated code)
```

### Step-by-Step Process

#### Step 1: Upload Files
**Input**: Platform XML files (transformations, pipelines, tasks, sub pipelines)
**Output**: Files stored in staging directory
**Trigger**: `make upload` or `python scripts/test_flow.py upload`

```bash
# Example
make upload FILES="samples/super_complex/*.xml"
```

#### Step 2: Parse
**Input**: Uploaded XML files
**Output**: 
- **Transformations**: Raw parsed data (not yet canonical model)
- **Pipelines/Tasks/SubPipelines**: Parsed structure (DAGs, configs)
**Trigger**: `make parse` or `python scripts/test_flow.py parse`

**What Happens**:
- All component types are parsed (transformation, pipeline, task, sub pipeline)
- Parsed data stored in `test_log/parsed/` directory
- **Only transformations proceed to normalization** (other types stored separately)

#### Step 3: Enhance
**Input**: Parsed transformation data
**Output**: Enhanced canonical models (JSON files)
**Trigger**: `make enhance` or `python scripts/test_flow.py enhance`

**What Happens**:
- **Only transformations are enhanced** (pipelines/tasks/sub pipelines are not)
- Normalization creates canonical model
- AI enhancement adds metadata, optimization hints
- Enhanced models saved to `test_log/parse_ai/` and Neo4j

#### Step 4: Code Generation
**Input**: Enhanced canonical models (from JSON files or Neo4j)
**Output**: Generated code files (PySpark, DLT, SQL)
**Trigger**: `make code` or `python scripts/test_flow.py code`

**What Happens**:
- Finds all canonical model files (`*.json` in `test_log/parse_ai/` or `test_log/parsed/`)
- For each transformation's canonical model:
  - Generates PySpark code
  - Generates DLT code (if enabled)
  - Generates SQL code (if enabled)
- Saves code to `test_log/generated/{transformation_name}/`

#### Step 5: Review
**Input**: Generated code files
**Output**: Reviewed and fixed code
**Trigger**: `make review` or `python scripts/test_flow.py review`

---

## Code Generation Trigger/Input

### Current Implementation

**Trigger**: Command-line execution of `make code` or `python scripts/test_flow.py code`

**Input Sources** (in priority order):

1. **Enhanced Canonical Models** (Primary)
   - Location: `test_log/parse_ai/*.json`
   - Format: Enhanced canonical model JSON files
   - Contains: Full transformation structure with AI enhancements

2. **Parsed Canonical Models** (Fallback)
   - Location: `test_log/parsed/*.json`
   - Format: Basic canonical model JSON files
   - Contains: Transformation structure without AI enhancements

3. **Neo4j Graph Database** (Workflow-Aware Mode)
   - Query: Load canonical model by transformation name
   - Format: Graph nodes and relationships
   - Contains: Full transformation structure with relationships

### Code Generation Process Flow

```
Code Generation Trigger
    ↓
Check Graph Store Enabled?
    ├── Yes → Workflow-Aware Generation
    │   ├── Query Neo4j for pipelines
    │   ├── Get pipeline structure (tasks, transformations)
    │   └── Generate code organized by pipeline
    └── No → File-Based Generation
        ├── Search: test_log/parse_ai/*.json (enhanced)
        └── Search: test_log/parsed/*.json (basic)
    ↓
For Each Transformation's Canonical Model:
    ├── Load JSON file or query Neo4j
    ├── Extract transformation_name
    ├── Create output directory
    └── Generate Code:
        ├── PySpark → {transformation_name}_pyspark.py
        ├── DLT → {transformation_name}_dlt.py (if enabled)
        └── SQL → {transformation_name}_sql.sql (if enabled)
    ↓
Save Generated Code Files
    ↓
Generate Summary: generation_summary.json
```

---

## Workflow-Aware Generation

### Overview

Workflow-aware code generation organizes code by pipeline structure, making it easier to migrate Informatica workloads to modern platforms. It uses Neo4j to query pipeline → task → transformation relationships and generates code in a hierarchical structure.

### Key Features

1. **Pipeline-Based Repository Structure**: Code organized to reflect original platform hierarchy
2. **Descriptive File Naming**: Code files use transformation names (e.g., `load_customer_pyspark.py`)
3. **Neo4j Integration**: Queries Neo4j for pipeline structure and relationships
4. **Shared/Reusable Code**: Common utilities extracted to `shared/` directory
5. **Automatic Orchestration**: Generates workflow orchestration code

### How It Works

1. **Checks for Neo4j**: If graph store is enabled, uses workflow-aware generation
2. **Queries Pipelines**: Gets all pipelines from Neo4j
3. **For Each Pipeline**:
   - Gets pipeline structure (tasks, transformations)
   - Creates pipeline directory structure
   - Generates pipeline README
4. **For Each Task**:
   - Creates task directory
   - Generates task configuration
5. **For Each Transformation**:
   - Loads canonical model (from Neo4j or JSON files)
   - Generates PySpark, DLT, SQL code
   - Saves with descriptive filenames
   - Generates transformation specification
6. **Generates Shared Code**:
   - Common utilities
   - Configuration files
7. **Generates Pipeline Orchestration**:
   - Pipeline DAG JSON
   - Execution dependencies
   - Orchestration code (Airflow, Databricks Workflows, etc.)

### Fallback Behavior

If Neo4j is not available or no pipelines are found, the system falls back to file-based generation:
- Searches for canonical model JSON files
- Generates code in flat per-transformation structure
- Uses descriptive filenames

---

## Repository Structure

### Current Structure (Per-Transformation)

```
generated_code/
├── load_customer/
│   ├── load_customer_pyspark.py
│   ├── load_customer_dlt.py
│   └── load_customer_sql.sql
├── load_orders/
│   ├── load_orders_pyspark.py
│   ├── load_orders_dlt.py
│   └── load_orders_sql.sql
└── generation_summary.json
```

### Workflow-Based Repository Structure

For migration scenarios, code is organized by **pipeline** to reflect the original platform structure:

```
generated_code/
├── workflows/
│   ├── customer_orders_etl/
│   │   ├── README.md                    # Pipeline documentation
│   │   ├── workflow_dag.json            # Pipeline DAG structure
│   │   ├── workflow_dag.mermaid         # Pipeline visualization
│   │   ├── sessions/
│   │   │   ├── load_customer/
│   │   │   │   ├── README.md            # Task config
│   │   │   │   ├── session_config.json
│   │   │   │   └── transformations/
│   │   │   │       ├── load_customer/
│   │   │   │       │   ├── load_customer_pyspark.py
│   │   │   │       │   ├── load_customer_dlt.py
│   │   │   │       │   ├── load_customer_sql.sql
│   │   │   │       │   └── transformation_spec.md
│   │   │   │       └── ingest_customers/
│   │   │   │           ├── ingest_customers_pyspark.py
│   │   │   │           └── ...
│   │   │   └── load_orders/
│   │   │       └── transformations/
│   │   │           └── load_order_fact/
│   │   │               ├── load_order_fact_pyspark.py
│   │   │               └── ...
│   │   └── orchestration/
│   │       ├── workflow_orchestrator.py  # Pipeline-level orchestration
│   │       └── dependencies.json         # Execution dependencies
│   └── daily_batch/
│       └── ...
├── shared/
│   ├── common_utils.py                  # Reusable functions
│   ├── utilities.py                     # Shared utilities
│   └── config/
│       ├── database_config.py
│       └── spark_config.py
└── generation_summary.json
```

### Benefits of Workflow-Based Structure

1. **Better Organization**: Code structure matches original platform hierarchy
2. **Easier Migration**: Clear mapping from source to target structure
3. **Reusable Code**: Common patterns extracted to shared directory
4. **Documentation**: Auto-generated READMEs and specifications
5. **Scalability**: Supports large migrations with many pipelines
6. **Orchestration**: Automatic generation of workflow orchestration code

---

## Implementation Details

### Code Generation Process

#### Workflow-Aware Generation

```python
def generate_code_workflow_aware(self, output_dir: str):
    """Generate code organized by pipeline structure.
    
    Args:
        output_dir: Base output directory
    """
    # 1. Query Neo4j for all pipelines
    pipelines = graph_queries.list_pipelines()
    
    # 2. For each pipeline
    for pipeline in pipelines:
        pipeline_name = pipeline.get("name")
        
        # 3. Get pipeline structure
        structure = graph_queries.get_workflow_structure(pipeline_name)
        
        # 4. Create pipeline directory
        pipeline_dir = os.path.join(output_dir, "workflows", pipeline_name)
        
        # 5. For each task in pipeline
        for task in structure.get("tasks", []):
            task_name = task.get("name")
            
            # 6. Create task directory
            task_dir = os.path.join(pipeline_dir, "sessions", task_name)
            
            # 7. For each transformation in task
            for transformation in task.get("transformations", []):
                transformation_name = transformation.get("transformation_name")
                
                # 8. Load canonical model
                canonical_model = load_canonical_model(transformation_name)
                
                # 9. Create transformation directory
                trans_dir = os.path.join(task_dir, "transformations", transformation_name)
                
                # 10. Generate code
                generate_transformation_code(canonical_model, trans_dir)
        
        # 11. Generate pipeline orchestration
        generate_pipeline_orchestration(structure, pipeline_dir)
    
    # 12. Generate shared code
    generate_shared_code(output_dir)
```

#### File-Based Generation

```python
def generate_code_file_based(self, output_dir: str):
    """Generate code from JSON files (fallback).
    
    Args:
        output_dir: Base output directory
    """
    # 1. Find canonical model files
    parse_ai_dir = os.path.join(project_root, "test_log", "parse_ai")
    parsed_dir = os.path.join(project_root, "test_log", "parsed")
    
    model_files = []
    for dir_path in [parse_ai_dir, parsed_dir]:
        if os.path.exists(dir_path):
            found_files = glob.glob(os.path.join(dir_path, "*.json"))
            model_files.extend(found_files)
    
    # 2. For each canonical model file
    for model_file in model_files:
        with open(model_file, 'r') as f:
            canonical_model = json.load(f)
        
        # 3. Skip non-transformation files
        if not canonical_model.get("transformation_name"):
            continue
        
        transformation_name = canonical_model.get("transformation_name")
        transformation_dir = os.path.join(output_dir, transformation_name.lower().replace("m_", ""))
        
        # 4. Generate code
        generate_transformation_code(canonical_model, transformation_dir)
```

### Generator Implementation

Each generator implements a `generate()` method that takes a canonical model and returns generated code:

```python
class PySparkGenerator:
    def generate(self, model: Dict[str, Any]) -> str:
        """Generate PySpark code from canonical model.
        
        Args:
            model: Canonical model dictionary
            
        Returns:
            Complete PySpark code as string
        """
        lines = []
        
        # Extract transformation name
        transformation_name = model.get("transformation_name", model.get("mapping_name", "Unknown"))
        
        # Generate imports
        lines.append("from pyspark.sql import SparkSession, functions as F")
        lines.append("from pyspark.sql.types import *")
        lines.append("")
        
        # Generate Spark session
        lines.append(f"spark = SparkSession.builder.appName('{transformation_name}').getOrCreate()")
        lines.append("")
        
        # Generate source reads
        for source in model.get("sources", []):
            # ... generate source reading code
        
        # Generate transformations
        for transformation in model.get("transformations", []):
            # ... generate transformation code
        
        # Generate target writes
        for target in model.get("targets", []):
            # ... generate target writing code
        
        return "\n".join(lines)
```

### Descriptive File Naming

Code files use descriptive names based on transformation names:
- `load_customer_pyspark.py` (instead of `pyspark_code.py`)
- `load_customer_dlt.py` (instead of `dlt_pipeline.py`)
- `load_customer_sql.sql` (instead of `sql_queries.sql`)

This makes it easier to identify which transformation a code file belongs to.

---

## Usage and Configuration

### Basic Usage

```bash
# Generate code with workflow-aware organization (default if Neo4j enabled)
make code

# Or using Python directly
python scripts/test_flow.py code --output-dir test_log/generated
```

### Configuration

#### Enable Graph Store

In your `.env` file:

```bash
ENABLE_GRAPH_STORE=true
GRAPH_FIRST=true
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

#### Disable Workflow-Aware Generation

To use flat structure even with Neo4j:

```python
flow.generate_code(output_dir, workflow_aware=False)
```

#### Enable/Disable Generator Types

By default, only PySpark generation is enabled. To enable DLT or SQL:

```python
# In scripts/test_flow.py
generators = {
    "pyspark": PySparkGenerator(),
    "dlt": DLTGenerator(),      # Uncomment to enable
    "sql": SQLGenerator()       # Uncomment to enable
}
```

### Example Output

After running `make code`, you'll see:

```
STEP G: Generate Code
============================================================
✅ Graph store enabled - using workflow-aware generation

📋 Found 2 pipeline(s) in graph

🔄 Processing pipeline: WF_CUSTOMER_ORDERS_ETL
   ⚙️  Processing task: S_LOAD_CUSTOMER
      📋 Generating code for transformation: M_LOAD_CUSTOMER
         ✅ Generated PYSPARK: load_customer_pyspark.py
         ✅ Generated DLT: load_customer_dlt.py
         ✅ Generated SQL: load_customer_sql.sql
      📋 Generating code for transformation: M_INGEST_CUSTOMERS
         ✅ Generated PYSPARK: ingest_customers_pyspark.py
         ...

📦 Generating shared/reusable code...
   ✅ Generated shared code in: generated_code/shared

📊 Summary:
   Pipelines: 2
   Generated files: 12
   Failed: 0
   Shared code files: 3
```

---

## Related Documentation

- **Canonical Model**: `docs/modules/canonical_model.md`
- **Solution Process**: `docs/development/solution.md` (includes detailed process documentation)
- **Test Flow Guide**: `docs/test_flow_guide.md`
- **Neo4j Setup**: `docs/setup_neo4j.md`

