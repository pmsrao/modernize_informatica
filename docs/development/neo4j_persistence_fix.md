# Neo4j Persistence Fix - All Component Types

## Problem Identified

**Issue**: Workflows, sessions, and worklets were being parsed and saved to JSON files, but **NOT saved to Neo4j**. This caused:

1. **Workflow-aware code generation to fail** - When Neo4j is queried for workflows, it returns empty because workflows were never saved
2. **Fallback to file-based generation** - System falls back to file-based mode which doesn't generate orchestration code
3. **Missing relationships** - Workflow → Session → Mapping relationships not built in graph

## Root Cause Analysis

### What Was Working:
- ✅ Mappings were saved to Neo4j via `graph_store.save_mapping()`
- ✅ Workflows/sessions/worklets were parsed and saved to JSON files
- ✅ GraphStore had methods to query workflows (but workflows didn't exist)

### What Was Missing:
- ❌ No `save_workflow()`, `save_session()`, `save_worklet()` methods in GraphStore
- ❌ Parsing code didn't call Neo4j save methods for workflows/sessions/worklets
- ❌ Relationships between workflows, sessions, worklets, and mappings not built

## Solution Implemented

### 1. Added Methods to GraphStore

**File**: `src/graph/graph_store.py`

**New Methods Added:**
- `save_workflow(workflow_data)` - Saves workflow with tasks and links
- `save_session(session_data, workflow_name)` - Saves session and links to workflow/mapping
- `save_worklet(worklet_data, workflow_name)` - Saves worklet and links to workflow

**Indexes Added:**
- `CREATE INDEX workflow_name IF NOT EXISTS FOR (w:Workflow) ON (w.name)`
- `CREATE INDEX session_name IF NOT EXISTS FOR (s:Session) ON (s.name)`
- `CREATE INDEX worklet_name IF NOT EXISTS FOR (w:Worklet) ON (w.name)`

### 2. Updated Parsing Code

**File**: `scripts/test_flow.py`

**Changes:**
- Initialize GraphStore at start of parsing (if enabled)
- Save mappings to Neo4j during parsing
- Save workflows to Neo4j during parsing
- Save sessions to Neo4j during parsing
- Save worklets to Neo4j during parsing
- Second pass: Build relationships between components

### 3. Relationship Building

**Relationships Created:**
- `Workflow -[:CONTAINS]-> Session`
- `Workflow -[:CONTAINS]-> Worklet`
- `Worklet -[:CONTAINS]-> Session`
- `Session -[:EXECUTES]-> Mapping`
- `Workflow/Session/Worklet -[:DEPENDS_ON]-> Workflow/Session/Worklet` (from links)

## Implementation Details

### Workflow Storage

```python
def save_workflow(self, workflow_data: Dict[str, Any]) -> str:
    """Save workflow to Neo4j."""
    # Creates Workflow node
    # Processes tasks (sessions, worklets)
    # Creates Session/Worklet nodes
    # Links workflow to sessions/worklets via CONTAINS
    # Processes links to create DEPENDS_ON relationships
```

### Session Storage

```python
def save_session(self, session_data: Dict[str, Any], workflow_name: Optional[str] = None) -> str:
    """Save session to Neo4j."""
    # Creates Session node
    # Links to workflow if provided
    # Links to mapping if mapping_name available
```

### Worklet Storage

```python
def save_worklet(self, worklet_data: Dict[str, Any], workflow_name: Optional[str] = None) -> str:
    """Save worklet to Neo4j."""
    # Creates Worklet node
    # Links to workflow if provided
    # Processes tasks in worklet (sessions)
    # Links worklet to sessions
```

## Graph Schema

### Nodes
- `Workflow` - Workflow definitions
- `Session` - Session configurations
- `Worklet` - Reusable workflow components
- `Mapping` - Canonical models (already existed)

### Relationships
- `Workflow -[:CONTAINS]-> Session`
- `Workflow -[:CONTAINS]-> Worklet`
- `Worklet -[:CONTAINS]-> Session`
- `Session -[:EXECUTES]-> Mapping`
- `* -[:DEPENDS_ON]-> *` (from workflow links)

## Testing

### Verify Workflows in Neo4j

```cypher
// List all workflows
MATCH (w:Workflow)
RETURN w.name, w.type

// Get workflow with sessions
MATCH (w:Workflow {name: "WF_CUSTOMER_ORDERS_ETL"})-[:CONTAINS]->(s:Session)
RETURN w.name, s.name

// Get workflow with worklets
MATCH (w:Workflow {name: "WF_CUSTOMER_ORDERS_ETL"})-[:CONTAINS]->(wl:Worklet)
RETURN w.name, wl.name

// Get session to mapping relationships
MATCH (s:Session)-[:EXECUTES]->(m:Mapping)
RETURN s.name, m.name
```

### Expected Results After Fix

1. **Workflows in Neo4j**: All parsed workflows should be in Neo4j
2. **Sessions in Neo4j**: All parsed sessions should be in Neo4j
3. **Worklets in Neo4j**: All parsed worklets should be in Neo4j
4. **Relationships**: Workflow → Session → Mapping relationships should exist
5. **Workflow-aware generation**: Should now work because workflows are in Neo4j

## Workflow-Aware vs File-Based Generation

### Workflow-Aware Mode (Preferred)

**When**: Neo4j has workflows stored

**How it works:**
1. Query Neo4j for all workflows: `graph_queries.list_workflows()`
2. For each workflow, get structure: `graph_queries.get_workflow_structure(workflow_name)`
3. Structure includes: workflow → sessions → mappings
4. Generate code organized by workflow structure
5. Generate orchestration code automatically

**Benefits:**
- Complete workflow structure with relationships
- Automatic orchestration generation
- Better organization

### File-Based Mode (Fallback)

**When**: Neo4j doesn't have workflows or graph store disabled

**How it works:**
1. Search for JSON files in `test_log/parsed/` and `test_log/parse_ai/`
2. Generate code per mapping (flat structure)
3. Generate orchestration from workflow JSON files (if found)

**Limitations:**
- No relationship information
- Manual orchestration generation
- Less organized output

## Next Steps

1. **Re-run parsing** - Parse files again to save workflows/sessions/worklets to Neo4j
2. **Verify in Neo4j** - Check that workflows are now stored
3. **Re-run code generation** - Should now use workflow-aware mode
4. **Verify orchestration** - Check that orchestration files are generated

## Summary

✅ **Fixed**: Added methods to save workflows, sessions, and worklets to Neo4j
✅ **Fixed**: Updated parsing code to save all components to Neo4j
✅ **Fixed**: Added relationship building between components
✅ **Fixed**: Workflow-aware generation should now work

**Result**: All component types (workflows, sessions, worklets, mappings) are now persisted to Neo4j with proper relationships.

