# Code Generation Workflow - CLI Process & Repository Structure

This document explains how code generation works in the CLI workflow, the trigger/input mechanism, and how code can be organized in a repository structure.

---

## CLI Workflow: Upload → Parse → Enhance → Code → Review

### Current Workflow Steps

```
1. Upload Files
   ↓
2. Parse (all components: mappings, workflows, sessions, worklets)
   ↓
3. Enhance (mappings only - creates canonical models)
   ↓
4. Code Generation (mappings only - uses canonical models)
   ↓
5. Review (generated code)
```

### Step-by-Step Process

#### Step 1: Upload Files
**Input**: Informatica XML files (mappings, workflows, sessions, worklets)
**Output**: Files stored in staging directory
**Trigger**: `make upload` or `python scripts/test_flow.py upload`

```bash
# Example
make upload FILES="samples/super_complex/*.xml"
```

#### Step 2: Parse
**Input**: Uploaded XML files
**Output**: 
- **Mappings**: Raw parsed data (not yet canonical model)
- **Workflows/Sessions/Worklets**: Parsed structure (DAGs, configs)
**Trigger**: `make parse` or `python scripts/test_flow.py parse`

**What Happens**:
- All component types are parsed (mapping, workflow, session, worklet)
- Parsed data stored in `test_log/parsed/` directory
- **Only mappings proceed to normalization** (other types stored separately)

#### Step 3: Enhance
**Input**: Parsed mapping data
**Output**: Enhanced canonical models (JSON files)
**Trigger**: `make enhance` or `python scripts/test_flow.py enhance`

**What Happens**:
- **Only mappings are enhanced** (workflows/sessions/worklets are not)
- Normalization creates canonical model
- AI enhancement adds metadata, optimization hints
- Enhanced models saved to `test_log/parse_ai/` and Neo4j

#### Step 4: Code Generation
**Input**: Enhanced canonical models (from JSON files or Neo4j)
**Output**: Generated code files (PySpark, DLT, SQL)
**Trigger**: `make code` or `python scripts/test_flow.py code`

**What Happens**:
- Finds all canonical model files (`*.json` in `test_log/parse_ai/` or `test_log/parsed/`)
- For each mapping's canonical model:
  - Generates PySpark code
  - Generates DLT code
  - Generates SQL code
- Saves code to `test_log/generated/{mapping_name}/`

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
   - Contains: Full mapping structure with AI enhancements

2. **Parsed Canonical Models** (Fallback)
   - Location: `test_log/parsed/*.json`
   - Format: Basic canonical model JSON files
   - Contains: Mapping structure without AI enhancements

3. **Neo4j Graph Database** (Future/Alternative)
   - Query: Load canonical model by mapping name
   - Format: Graph nodes and relationships
   - Contains: Full mapping structure with relationships

### Code Generation Process Flow

```
Code Generation Trigger
    ↓
Find Canonical Model Files
    ├── Search: test_log/parse_ai/*.json (enhanced)
    └── Search: test_log/parsed/*.json (basic)
    ↓
For Each Mapping's Canonical Model:
    ├── Load JSON file
    ├── Extract mapping_name
    ├── Create output directory: generated/{mapping_name}/
    └── Generate Code:
        ├── PySpark → pyspark_code.py
        ├── DLT → dlt_pipeline.py
        └── SQL → sql_queries.sql
    ↓
Save Generated Code Files
    ↓
Generate Summary: generation_summary.json
```

### Code Reference

**File**: `scripts/test_flow.py` (lines 701-803)

```python
def generate_code(self, output_dir: str) -> Dict[str, Any]:
    """Generate code (PySpark/DLT/SQL).
    
    Args:
        output_dir: Directory to save generated code
        
    Returns:
        Dictionary with generation results
    """
    # Find enhanced or parsed models
    parse_ai_dir = os.path.join(project_root, "test_log", "parse_ai")
    parsed_dir = os.path.join(project_root, "test_log", "parsed")
    
    model_files = []
    for dir_path in [parse_ai_dir, parsed_dir]:
        if os.path.exists(dir_path):
            found_files = glob.glob(os.path.join(dir_path, "*.json"))
            model_files.extend(found_files)
    
    # For each canonical model file
    for model_file in model_files:
        with open(model_file, 'r') as f:
            canonical_model = json.load(f)
        
        mapping_name = canonical_model.get("mapping_name")
        mapping_dir = os.path.join(output_dir, mapping_name.lower().replace("m_", ""))
        
        # Generate PySpark, DLT, SQL
        for code_type, generator in generators.items():
            code = generator.generate(canonical_model)
            # Save to mapping_dir
```

---

## How Code Generation Works with Neo4j

### The Architecture

**Key Point**: Canonical model only contains **mappings**, but Neo4j contains **all components** (mappings, workflows, sessions, worklets) with relationships.

### Current Code Generation Flow

```
┌─────────────────────────────────────────────────┐
│  Neo4j Graph Database                           │
│  ┌───────────────────────────────────────────┐ │
│  │ All Components:                            │ │
│  │ • Mappings (with canonical model data)     │ │
│  │ • Workflows                                 │ │
│  │ • Sessions                                  │ │
│  │ • Worklets                                  │ │
│  │ • Relationships:                            │ │
│  │   (Workflow)-[:CONTAINS]->(Session)        │ │
│  │   (Session)-[:EXECUTES]->(Mapping)         │ │
│  └───────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
                    ↓
        Query: Get Mapping by Name
                    ↓
┌─────────────────────────────────────────────────┐
│  Canonical Model (Mapping Only)                 │
│  • Sources                                      │
│  • Targets                                      │
│  • Transformations                              │
│  • Connections                                  │
│  • Lineage                                      │
└─────────────────────────────────────────────────┘
                    ↓
        Code Generator
                    ↓
┌─────────────────────────────────────────────────┐
│  Generated Code (Per Mapping)                   │
│  • pyspark_code.py                              │
│  • dlt_pipeline.py                              │
│  • sql_queries.sql                              │
└─────────────────────────────────────────────────┘
```

### How It Works

1. **Code Generation Trigger**: 
   - Currently uses JSON files from `test_log/parse_ai/` or `test_log/parsed/`
   - **Future**: Can query Neo4j directly by mapping name

2. **Neo4j Role**:
   - Stores all components and relationships
   - Enables workflow-level queries (e.g., "Get all mappings in workflow X")
   - Provides cross-mapping analysis and lineage
   - **Not currently used as primary input for code generation** (uses JSON files)

3. **Canonical Model Role**:
   - Contains only mapping-level data (sources, targets, transformations)
   - **This is what code generators use** (mapping-specific logic)
   - Workflow/session/worklet data is not needed for code generation

4. **Code Generation Scope**:
   - **Per-Mapping**: Each mapping generates its own code files
   - **Standalone**: Code is self-contained and executable
   - **No Workflow Context**: Current implementation doesn't generate workflow-level orchestration code

---

## Repository Structure for Generated Code

### Current Structure (Per-Mapping)

```
generated_code/
├── load_customer/
│   ├── pyspark_code.py
│   ├── dlt_pipeline.py
│   └── sql_queries.sql
├── load_orders/
│   ├── pyspark_code.py
│   ├── dlt_pipeline.py
│   └── sql_queries.sql
└── generation_summary.json
```

### Proposed Workflow-Based Repository Structure

For migration scenarios, code should be organized by **workflow** to reflect the original Informatica structure:

```
generated_code/
├── workflows/
│   ├── wf_customer_orders_etl/
│   │   ├── README.md                    # Workflow documentation
│   │   ├── workflow_dag.json            # Workflow DAG structure
│   │   ├── workflow_dag.mermaid         # Workflow visualization
│   │   ├── sessions/
│   │   │   ├── s_load_customer/
│   │   │   │   ├── README.md            # Session config
│   │   │   │   ├── mappings/
│   │   │   │   │   ├── m_load_customer/
│   │   │   │   │   │   ├── pyspark_code.py
│   │   │   │   │   │   ├── dlt_pipeline.py
│   │   │   │   │   │   ├── sql_queries.sql
│   │   │   │   │   │   └── mapping_spec.md
│   │   │   │   │   └── m_ingest_customers/
│   │   │   │   │       ├── pyspark_code.py
│   │   │   │   │       ├── dlt_pipeline.py
│   │   │   │   │       └── sql_queries.sql
│   │   │   │   └── session_config.json
│   │   │   └── s_load_orders/
│   │   │       └── mappings/
│   │   │           └── m_load_order_fact/
│   │   │               ├── pyspark_code.py
│   │   │               └── ...
│   │   └── orchestration/
│   │       ├── workflow_orchestrator.py  # Workflow-level orchestration
│   │       └── dependencies.json         # Execution dependencies
│   └── wf_daily_batch/
│       └── ...
├── shared/
│   ├── common_functions.py              # Reusable functions
│   ├── utilities.py                     # Shared utilities
│   └── config/
│       ├── database_config.py
│       └── spark_config.py
└── tests/
    ├── unit/
    │   └── test_mappings/
    └── integration/
        └── test_workflows/
```

### Implementation Approach

#### Option 1: Workflow-Aware Code Generation (Recommended)

**Enhancement to Current Flow**:

```python
def generate_code_workflow_aware(self, workflow_name: str, output_dir: str):
    """Generate code organized by workflow structure.
    
    Args:
        workflow_name: Name of workflow to generate code for
        output_dir: Base output directory
    """
    # 1. Query Neo4j for workflow structure
    workflow = graph_queries.get_workflow(workflow_name)
    
    # 2. Get all sessions in workflow
    sessions = graph_queries.get_sessions_in_workflow(workflow_name)
    
    # 3. For each session, get mappings
    for session in sessions:
        mappings = graph_queries.get_mappings_in_session(session.name)
        
        # 4. Create directory structure
        workflow_dir = os.path.join(output_dir, "workflows", workflow_name)
        session_dir = os.path.join(workflow_dir, "sessions", session.name)
        
        # 5. Generate code for each mapping
        for mapping in mappings:
            canonical_model = load_canonical_model(mapping.name)  # From Neo4j or JSON
            mapping_dir = os.path.join(session_dir, "mappings", mapping.name)
            
            # Generate code (same as current)
            generate_mapping_code(canonical_model, mapping_dir)
        
        # 6. Generate session-level files
        generate_session_config(session, session_dir)
    
    # 7. Generate workflow-level orchestration
    generate_workflow_orchestration(workflow, workflow_dir)
```

#### Option 2: Post-Processing Organization

**After code generation, reorganize by workflow**:

```python
def reorganize_by_workflow(self, generated_dir: str, output_dir: str):
    """Reorganize generated code by workflow structure.
    
    Args:
        generated_dir: Current per-mapping structure
        output_dir: New workflow-based structure
    """
    # 1. Query Neo4j for all workflows
    workflows = graph_queries.list_workflows()
    
    # 2. For each workflow, organize mappings
    for workflow in workflows:
        # Get mappings via sessions
        mappings = graph_queries.get_mappings_in_workflow(workflow.name)
        
        # Move/copy code files to workflow structure
        organize_mappings_into_workflow(mappings, workflow, output_dir)
```

---

## How Code Generation Proceeds

### Current Flow (Per-Mapping)

```
Start: make code
    ↓
1. Find Canonical Model Files
   ├── Search: test_log/parse_ai/*.json
   └── Search: test_log/parsed/*.json
    ↓
2. For Each Mapping:
   ├── Load canonical model (JSON)
   ├── Create directory: generated/{mapping_name}/
   └── Generate Code:
       ├── PySpark Generator → pyspark_code.py
       ├── DLT Generator → dlt_pipeline.py
       └── SQL Generator → sql_queries.sql
    ↓
3. Save Files
   └── Write code files to mapping directory
    ↓
4. Generate Summary
   └── generation_summary.json
    ↓
End
```

### Proposed Flow (Workflow-Aware)

```
Start: make code --workflow WF_CUSTOMER_ORDERS
    ↓
1. Query Neo4j for Workflow
   └── Get workflow structure and relationships
    ↓
2. Get Workflow Components
   ├── Sessions in workflow
   ├── Mappings in each session
   └── Dependencies between sessions
    ↓
3. Create Repository Structure
   └── workflows/{workflow_name}/sessions/{session_name}/mappings/{mapping_name}/
    ↓
4. For Each Mapping:
   ├── Load canonical model (from Neo4j or JSON)
   ├── Generate code (PySpark/DLT/SQL)
   └── Save to workflow-based structure
    ↓
5. Generate Workflow-Level Files
   ├── Workflow DAG (JSON/Mermaid)
   ├── Orchestration code (if needed)
   └── Dependencies file
    ↓
6. Generate Session-Level Files
   ├── Session configuration
   └── Session documentation
    ↓
7. Generate Summary
   └── workflow_generation_summary.json
    ↓
End
```

---

## Answering Your Questions

### Q1: What is the trigger/input for code generation (CLI way)?

**Answer**:
- **Trigger**: `make code` command or `python scripts/test_flow.py code`
- **Input**: Canonical model JSON files from `test_log/parse_ai/` or `test_log/parsed/`
- **Process**: Finds all canonical model files, generates code for each mapping
- **Output**: Code files in `test_log/generated/{mapping_name}/`

### Q2: How will code be generated, where it starts and how it proceeds?

**Answer**:
- **Starts**: From canonical model files (JSON) or Neo4j queries
- **Proceeds**: 
  1. Load canonical model for each mapping
  2. Generate PySpark, DLT, SQL code
  3. Save to per-mapping directories
- **Current**: Per-mapping generation (standalone code)
- **Future**: Workflow-aware generation (organized by workflow structure)

### Q3: Can code be generated in repo structure?

**Answer**: **Yes, with enhancements**

**Current State**:
- Code is generated per-mapping: `generated_code/{mapping_name}/`
- Flat structure, no workflow organization

**Proposed Enhancement**:
- **Workflow-based structure**: `workflows/{workflow}/sessions/{session}/mappings/{mapping}/`
- **Benefits**:
  - Reflects original Informatica structure
  - Easier migration and understanding
  - Supports workflow-level orchestration
  - Better organization for large migrations

**Implementation**:
- Use Neo4j to query workflow → session → mapping relationships
- Organize code generation output by workflow hierarchy
- Generate workflow-level orchestration files
- Create session-level configuration files

---

## Implementation Recommendations

### Phase 1: Enhance Code Generation (Current)

1. **Add Workflow Query Support**
   ```python
   def generate_code_for_workflow(self, workflow_name: str):
       # Query Neo4j for workflow structure
       # Get all mappings in workflow
       # Generate code organized by workflow
   ```

2. **Add Repository Structure Option**
   ```python
   def generate_code(self, output_dir: str, organize_by_workflow: bool = False):
       if organize_by_workflow:
           # Use workflow-based structure
       else:
           # Use current per-mapping structure
   ```

### Phase 2: Workflow-Level Generation

1. **Generate Workflow Orchestration**
   - Create workflow DAG files
   - Generate orchestration code (Airflow, Databricks Workflows, etc.)
   - Document execution dependencies

2. **Generate Session Configuration**
   - Session-level configuration files
   - Connection details
   - Execution parameters

### Phase 3: Shared Code Extraction

1. **Pattern Detection**
   - Use Neo4j to find similar transformations
   - Identify reusable code patterns

2. **Library Generation**
   - Extract common functions
   - Create shared utilities
   - Generate reusable modules

---

## Summary

- **Current**: Code generation is **per-mapping**, triggered by finding canonical model JSON files
- **Input**: Canonical model files (JSON) from parse/enhance steps
- **Neo4j Role**: Stores all components and relationships, but not currently primary input for code generation
- **Future**: Can be enhanced to generate code in **workflow-based repository structure** using Neo4j queries
- **Repository Structure**: Yes, code can be organized by workflow/session/mapping hierarchy for better migration support

---

## Related Documentation

- **Solution Process**: `docs/solution_process_details.md`
- **Code Generators**: `docs/code_generators.md`
- **Test Flow Guide**: `docs/test_flow_guide.md`
- **Neo4j Setup**: `docs/setup_neo4j.md`

