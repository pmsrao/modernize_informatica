# Solution Process & Steps - Detailed Documentation

This document provides comprehensive answers to questions about the Informatica Modernization Accelerator's solution, process, and implementation steps.

---

## a) Parse & Enhance Step - File Processing Details

### What Files Are Parsed?

The **Parse & Enhance** step processes **all Informatica component types**, not just mappings:

#### Supported Component Types:

1. **Mappings** (`mapping`)
   - **Purpose**: Extract transformation logic, sources, targets, expressions
   - **Output**: Creates canonical model (technology-neutral representation)
   - **Enhancement**: AI enhancement adds metadata, optimization hints, data quality rules
   - **Storage**: Saved to Neo4j graph database

2. **Workflows** (`workflow`)
   - **Purpose**: Extract task execution order, dependencies, scheduling
   - **Output**: Creates workflow DAG (Directed Acyclic Graph) structure
   - **Enhancement**: Workflow-level analysis and optimization suggestions
   - **Storage**: Stored separately from canonical model (workflow orchestration data)

3. **Sessions** (`session`)
   - **Purpose**: Extract session configuration, mapping references, connection details
   - **Output**: Session configuration and metadata
   - **Enhancement**: Configuration optimization suggestions
   - **Storage**: Linked to workflows and mappings in graph

4. **Worklets** (`worklet`)
   - **Purpose**: Extract reusable workflow components and embedded tasks
   - **Output**: Worklet structure and relationships
   - **Enhancement**: Reusability analysis and pattern detection
   - **Storage**: Linked to workflows in graph

### Processing Flow

```
Upload XML File
    ↓
File Type Detection (mapping/workflow/session/worklet)
    ↓
┌─────────────────────────────────────────┐
│  Type-Specific Parser                   │
├─────────────────────────────────────────┤
│  • Mapping → MappingParser              │
│  • Workflow → WorkflowParser            │
│  • Session → SessionParser              │
│  • Worklet → WorkletParser              │
└─────────────────────────────────────────┘
    ↓
Raw Parsed Data (Python Dictionary)
    ↓
┌─────────────────────────────────────────┐
│  For Mappings Only:                     │
│  Normalization → Canonical Model         │
│  ↓                                       │
│  AI Enhancement (optional)               │
│  ↓                                       │
│  Save to Neo4j                          │
├─────────────────────────────────────────┤
│  For Other Types:                       │
│  Store as hierarchy/orchestration data  │
│  Link to mappings in graph              │
└─────────────────────────────────────────┘
```

### Key Implementation Details

**Code Reference**: `frontend/src/pages/ModernizationJourneyPage.jsx` (lines 113-159)

```javascript
const handleParseAndEnhance = async (fileId) => {
  // Determine file type
  const fileInfo = await apiClient.getFileInfo(fileId);
  const fileType = fileInfo.file_type;

  let result;
  if (fileType === 'mapping') {
    result = await apiClient.parseMapping(fileId, true); // enhance_model = true
  } else if (fileType === 'workflow') {
    result = await apiClient.parseWorkflow(fileId);
  } else if (fileType === 'session') {
    result = await apiClient.parseSession(fileId);
  } else if (fileType === 'worklet') {
    result = await apiClient.parseWorklet(fileId);
  }
  // ... processing continues
}
```

**Important Notes**:
- ✅ **All component types are parsed** (mapping, workflow, session, worklet)
- ✅ **Only mappings create canonical models** (technology-neutral representation)
- ✅ **Workflows/sessions/worklets create orchestration structures** (DAGs, configs)
- ✅ **All components are stored in Neo4j** with appropriate relationships
- ✅ **AI enhancement is primarily applied to mappings** (canonical models)

---

## b) Canonical Model - Components and Neo4j Schema

### What Is Included in the Canonical Model?

The canonical model is a **technology-neutral, standardized JSON representation** that serves as the single source of truth for all downstream processing.

#### Components Included:

1. **Mapping Structure**
   - Mapping name and metadata
   - Source definitions (tables, files, connections)
   - Target definitions (tables, files, write strategies)
   - Transformation list (all transformation objects)
   - Connection graph (data flow between transformations)

2. **Transformation Details**
   - Transformation type (EXPRESSION, LOOKUP, AGGREGATOR, JOINER, ROUTER, FILTER, UNION, etc.)
   - Input ports (field definitions, data types)
   - Output ports (derived fields, expressions)
   - Expressions and formulas (Informatica syntax)
   - Configuration parameters (lookup conditions, join keys, etc.)

3. **Lineage Information**
   - Column-level lineage (which source columns feed each derived field)
   - Transformation-level lineage (data flow: SQ → EXP → LKUP → AGG → TARGET)
   - Field-to-field relationships (derived_from, flows_to)

4. **Metadata**
   - Names, descriptions, annotations
   - SCD type detection (Type 1, Type 2, Type 3)
   - Incremental load keys
   - Business rules and constraints

5. **AI Enhancement Metadata** (optional, added during enhancement)
   - `_optimization_hint`: Performance optimization suggestions
   - `_data_quality_rules`: Data quality constraints
   - `_performance_metadata`: Performance characteristics
   - `_provenance`: Tracking of enhancements applied

### What Components Are Modeled in Neo4j?

**All Informatica components are modeled in Neo4j**, but with different purposes:

#### Primary Components (Mappings - Canonical Model):

- **Mapping**: Core ETL logic representation
- **Transformation**: Individual transformation objects
- **Source**: Source table/file definitions
- **Target**: Target table/file definitions
- **Field**: Column/field definitions with lineage
- **Connector**: Data flow connections between transformations

#### Orchestration Components (Workflows/Sessions/Worklets):

- **Workflow**: Workflow execution structure
- **Session**: Session configuration and mapping references
- **Worklet**: Reusable workflow components
- **Table**: Physical table definitions
- **Database**: Database/platform definitions

### Neo4j Data Model/Schema

The Neo4j schema supports **all components** with a comprehensive relationship model:

#### Node Types:

```
Mapping
├── name: "M_LOAD_CUSTOMER"
├── type: "MAPPING"
├── mapping_name: "M_LOAD_CUSTOMER"
└── properties: {metadata, scd_type, ...}

Transformation
├── name: "EXP_CALCULATE_TOTAL"
├── type: "EXPRESSION"
├── mapping: "M_LOAD_CUSTOMER"
└── properties: {optimization_hint, ...}

Source
├── name: "SQ_CUSTOMER"
├── type: "SOURCE"
├── table: "CUSTOMER_SRC"
└── database: "source_db"

Target
├── name: "TGT_CUSTOMER"
├── type: "TARGET"
├── table: "CUSTOMER_TGT"
└── database: "lakehouse_db"

Field
├── name: "CUSTOMER_ID"
├── type: "FIELD"
├── data_type: "STRING"
└── parent: "SQ_CUSTOMER"

Workflow
├── name: "WF_CUSTOMER_DAILY"
├── type: "WORKFLOW"
└── schedule: {...}

Session
├── name: "S_M_LOAD_CUSTOMER"
├── type: "SESSION"
├── mapping: "M_LOAD_CUSTOMER"
└── workflow: "WF_CUSTOMER_DAILY"

Table
├── name: "CUSTOMER_SRC"
├── type: "TABLE"
├── database: "source_db"
└── schema: {...}

Database
├── name: "source_db"
├── type: "DATABASE"
└── platform: "Oracle"
```

#### Relationship Types:

```
(Mapping)-[:HAS_TRANSFORMATION]->(Transformation)
(Mapping)-[:HAS_SOURCE]->(Source)
(Mapping)-[:HAS_TARGET]->(Target)
(Transformation)-[:CONNECTS_TO]->(Transformation)
(Transformation)-[:READS_FROM]->(Source)
(Transformation)-[:WRITES_TO]->(Target)
(Field)-[:FLOWS_TO]->(Field)
(Field)-[:DERIVED_FROM]->(Field)
(Mapping)-[:USES_TABLE]->(Table)
(Source)-[:READS_TABLE]->(Table)
(Target)-[:WRITES_TABLE]->(Table)
(Workflow)-[:CONTAINS]->(Session)
(Session)-[:EXECUTES]->(Mapping)
(Mapping)-[:DEPENDS_ON]->(Mapping)
(Transformation)-[:SIMILAR_TO]->(Transformation)
(Table)-[:FEEDS_INTO]->(Table)
```

### Neo4j Schema Capabilities

✅ **All components are modeled**: Mappings, workflows, sessions, worklets, tables, databases
✅ **Comprehensive relationships**: Full lineage, dependencies, and orchestration links
✅ **Cross-mapping queries**: Find all mappings using a table, trace dependencies
✅ **Impact analysis**: Understand downstream effects of changes
✅ **Pattern discovery**: Discover reusable patterns across mappings

**Reference Documentation**: 
- `canonical_model_deep_dive.md` (lines 300-364)
- `docs/canonical_model.md`
- `docs/setup_neo4j.md`

---

## c) Code Generation - Process and Dependencies

### What Does Code Generation Use?

Code generation **primarily uses the canonical model** as the single source of truth, with **no dependency on source mapping XML files** after parsing.

#### Primary Input: Canonical Model

```
Canonical Model (from Neo4j or JSON)
    ↓
Expression Translation (Informatica → PySpark/SQL)
    ↓
Code Generator (PySpark/DLT/SQL)
    ↓
Generated Code Files
```

#### Code Generation Process:

1. **Load Canonical Model**
   - Load from Neo4j graph database (primary)
   - Or load from JSON file (backup/compatibility)
   - **No access to original XML files needed**

2. **Expression Translation**
   - Parse Informatica expressions into AST (Abstract Syntax Tree)
   - Translate AST to target platform syntax (PySpark/SQL)
   - Map 100+ Informatica functions to PySpark/SQL equivalents
   - **Uses only canonical model expressions**

3. **Code Generation**
   - Generate source table reads
   - Generate transformation logic (joins, lookups, aggregations, expressions)
   - Generate target table writes
   - Generate complete executable pipelines
   - **Uses only canonical model structure**

### Code Generation Details

#### What Gets Generated:

**For each mapping, code generation produces:**

1. **Complete PySpark Code**
   - SparkSession initialization
   - Source table reads (`spark.table()` or `spark.read()`)
   - Transformation DataFrame operations
   - Target table writes (`df.write.format('delta').saveAsTable()`)
   - All expressions translated to PySpark syntax

2. **Delta Live Tables (DLT) Code**
   - `@dlt.table` function definitions
   - Incremental load semantics (if SCD detected)
   - Dependencies between tables (`spark.table()` or `dlt.read()`)
   - Complete DLT pipeline

3. **SQL Code**
   - SELECT statements with transformations
   - WITH clauses for intermediate results
   - Target views or CTAS-style statements
   - Complete SQL scripts

#### Code Generation Implementation:

**Code Reference**: `src/generators/pyspark_generator.py`, `src/api/routes.py` (lines 597-658)

```python
# Code generation flow
def generate_pyspark(mapping_name: str):
    # 1. Load canonical model (from Neo4j or JSON)
    canonical_model = load_canonical_model(mapping_name)
    
    # 2. Translate expressions (Informatica → PySpark)
    translated_expressions = translate_expressions(canonical_model)
    
    # 3. Generate code (uses only canonical model)
    code = pyspark_generator.generate(canonical_model, translated_expressions)
    
    return code
```

**Key Points**:
- ✅ **Uses only canonical model** - no XML files needed
- ✅ **Regeneration is straightforward** - just reload model and regenerate
- ✅ **Technology independence** - model is not tied to Informatica or target platforms
- ✅ **Single source of truth** - all generators work from the same model

### Does Code Generation Detect Reusable Code/Libraries?

**Current Implementation**: Code generation produces **mapping-specific code** for each mapping. Reusability detection is handled separately by AI agents and graph analysis.

#### Reusability Detection Mechanisms:

1. **Pattern Detection** (via Graph Analysis)
   - Neo4j queries identify similar transformations across mappings
   - Pattern matching: `(Transformation)-[:SIMILAR_TO]->(Transformation)`
   - Identifies reusable transformation patterns

2. **AI Agent Analysis** (via TransformationSuggestionAgent)
   - Analyzes canonical models for common patterns
   - Suggests extraction of reusable functions
   - Identifies library candidates

3. **Manual Post-Processing** (Future Enhancement)
   - Generated code can be refactored to extract common functions
   - Shared libraries can be created from detected patterns
   - Code review agents can suggest refactoring opportunities

#### Current Code Generation Approach:

**Per-Mapping Generation**:
- Each mapping generates **standalone code**
- Code is **self-contained** and **executable**
- **No automatic library extraction** (by design for clarity)

**Reusability via Graph**:
- Graph queries identify similar patterns
- AI agents suggest refactoring opportunities
- Manual extraction of common code into libraries

**Reference Documentation**:
- `docs/code_generators.md` (line 57: "All generators rely only on the canonical model")
- `solution.md` (lines 245-252: Code Generation Stage)
- `system_architecture.md` (lines 304-320: Code Generation Stage)

---

## Summary

### a) Parse & Enhance
- ✅ **Parses all component types**: mappings, workflows, sessions, worklets
- ✅ **Only mappings create canonical models**: Other types create orchestration structures
- ✅ **All components stored in Neo4j**: With appropriate relationships

### b) Canonical Model
- ✅ **Includes**: Mappings, transformations, sources, targets, fields, lineage, metadata
- ✅ **All components modeled in Neo4j**: Mappings (canonical), workflows/sessions/worklets (orchestration)
- ✅ **Comprehensive Neo4j schema**: Supports all components with full relationship model

### c) Code Generation
- ✅ **Uses only canonical model**: No dependency on source XML files
- ✅ **Complete code generation**: Full PySpark/DLT/SQL pipelines
- ✅ **Reusability detection**: Via graph analysis and AI agents (not automatic in generated code)

---

## Related Documentation

- **Architecture**: `solution.md`, `system_architecture.md`
- **Canonical Model**: `docs/canonical_model.md`, `canonical_model_deep_dive.md`
- **Code Generation**: `docs/code_generators.md`
- **Parsing**: `docs/parsing.md`
- **Neo4j Setup**: `docs/setup_neo4j.md`
- **Graph Explorer**: `docs/graph_explorer_guide.md`

