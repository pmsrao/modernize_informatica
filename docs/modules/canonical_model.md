# Canonical Model

## Table of Contents
1. [Overview](#overview)
2. [Purpose and Benefits](#purpose-and-benefits)
3. [Platform-Agnostic Design](#platform-agnostic-design)
4. [Model Components](#model-components)
5. [JSON Structure](#json-structure)
6. [Neo4j Graph Representation](#neo4j-graph-representation)
7. [Storage and Persistence](#storage-and-persistence)
8. [Usage](#usage)
9. [Examples](#examples)

---

## Overview

### What is a Canonical Model?

The **Canonical Model** is a **platform-agnostic, standardized representation** of ETL logic. It serves as the **single source of truth** that abstracts away platform-specific structures (Informatica, DataStage, Talend, etc.) into a uniform format that all downstream components can use.

The model uses generic terminology (Transformations, Pipelines, Tasks) while preserving source platform information via `source_component_type` properties. This enables support for multiple ETL platforms while maintaining traceability to the original source.

### Key Principles

1. **Platform Independence**: The model is not tied to Informatica or any target platform
2. **Completeness**: Captures all essential ETL logic and metadata
3. **Extensibility**: Easy to add new transformation types or metadata
4. **Regeneration**: Code can be regenerated without re-parsing source files
5. **Traceability**: Source platform information preserved via `source_component_type`

### Terminology Mapping

The canonical model uses generic, platform-agnostic terminology:

| Informatica Term | Generic Term | Neo4j Label | source_component_type |
|-----------------|--------------|-------------|----------------------|
| Mapping | Transformation | `:Transformation` | `'mapping'` |
| Mapplet | ReusableTransformation | `:ReusableTransformation` | `'mapplet'` |
| Workflow | Pipeline | `:Pipeline` | `'workflow'` |
| Session | Task | `:Task` | `'session'` |
| Worklet | SubPipeline | `:SubPipeline` | `'worklet'` |

---

## Purpose and Benefits

### Purpose

The canonical model serves as a technology-neutral representation of ETL logic, transformations, and their relationships. It abstracts away platform-specific XML structures into a standardized format that can be used by all downstream components (generators, AI agents, lineage engines).

### Key Benefits

1. **Single Source of Truth**: All generators and agents work from the same model
2. **Technology Independence**: Model is not tied to any specific source or target platform
3. **Regeneration**: Code can be regenerated without re-parsing source files
4. **Extensibility**: Easy to add new transformation types or metadata
5. **Cross-Platform Support**: Enables migration from Informatica to DataStage, Talend, etc.
6. **Traceability**: Source platform information preserved for audit and lineage

---

## Platform-Agnostic Design

### Design Philosophy

The canonical model uses **generic terminology** throughout, with `source_component_type` properties to track the origin platform. This approach:

- **Enables Multi-Platform Support**: Can represent ETL logic from Informatica, DataStage, Talend, etc.
- **Maintains Traceability**: Always know which platform a component came from
- **Simplifies Migration**: Generic terms make it easier to migrate between platforms
- **Future-Proof**: New platforms can be added without changing core model structure

### Source Component Type

Every component includes a `source_component_type` property that identifies the original platform:

- `'mapping'` - Informatica Mapping
- `'mapplet'` - Informatica Mapplet
- `'workflow'` - Informatica Workflow
- `'session'` - Informatica Session
- `'worklet'` - Informatica Worklet

This property is used throughout the system to:
- Filter queries by source platform
- Display platform-specific information in UI
- Generate platform-aware documentation
- Maintain lineage to original source

---

## Model Components

### 1. Transformations (`Transformation`)

A **Transformation** (generic term for Informatica Mapping) represents a complete ETL transformation flow. It contains:

- Sources (input tables/files)
- Targets (output tables/files)
- Transformations (processing logic - nested transformations)
- Connectors (data flow between components)

**Key Properties:**
- `transformation_name`: Unique identifier
- `source_component_type`: Source platform component type (e.g., 'mapping' for Informatica mappings)
- `sources`: List of source definitions
- `targets`: List of target definitions (preserves `table.name` for metrics display)
- `transformations`: List of nested transformation objects
- `connectors`: List of data flow connections
- `lineage`: Column-level and transformation-level lineage
- `scd_type`: Slowly Changing Dimension type (SCD1, SCD2, NONE)
- `incremental_keys`: Keys for incremental loading

**Enhancement Metadata** (optional, added by AI):
- `_optimization_hint`: Performance optimization suggestions
- `_data_quality_rules`: Data quality constraints
- `_performance_metadata`: Performance characteristics
- `_provenance`: Tracking of enhancements applied

### 2. Reusable Transformations (`ReusableTransformation`)

A **Reusable Transformation** (generic term for Informatica Mapplet) is a reusable transformation component that can be used across multiple transformations. Unlike main transformations, reusable transformations:

- Have **input ports** and **output ports** (not sources/targets)
- Contain transformations that process the input ports
- Are "inlined" into transformations when used (their transformations are inserted into the transformation's flow)

**Key Properties:**
- `name`: Reusable transformation identifier
- `source_component_type`: Source platform component type (e.g., 'mapplet' for Informatica mapplets)
- `type`: Always "REUSABLE_TRANSFORMATION"
- `input_ports`: List of input port definitions
- `output_ports`: List of output port definitions
- `transformations`: List of transformation objects within the reusable transformation

### 3. Pipelines (`Pipeline`)

A **Pipeline** (generic term for Informatica Workflow) represents the orchestration structure. It contains:

- Tasks (execution tasks - generic term for Informatica Sessions)
- SubPipelines (reusable pipeline components - generic term for Informatica Worklets)
- Control flow (links between tasks)

**Key Properties:**
- `name`: Pipeline identifier
- `source_component_type`: Source platform component type (e.g., 'workflow' for Informatica workflows)
- `type`: "PIPELINE"
- `tasks`: List of tasks and sub pipelines
- `links`: Control flow between tasks

### 4. Tasks (`Task`)

A **Task** (generic term for Informatica Session) is an execution task within a pipeline. It:

- Executes a transformation
- Contains task-specific configuration (commit intervals, error handling, etc.)

**Key Properties:**
- `name`: Task identifier
- `source_component_type`: Source platform component type (e.g., 'session' for Informatica sessions)
- `type`: "TASK"
- `transformation_name`: Name of the transformation this task executes
- `config`: Task configuration (commit intervals, error handling, etc.)

### 5. SubPipelines (`SubPipeline`)

A **SubPipeline** (generic term for Informatica Worklet) is a reusable pipeline component that contains:

- Multiple tasks
- Control flow logic
- Can be used in multiple pipelines

**Key Properties:**
- `name`: SubPipeline identifier
- `source_component_type`: Source platform component type (e.g., 'worklet' for Informatica worklets)
- `type`: "SUB_PIPELINE"
- `tasks`: List of tasks within the sub pipeline

### 6. Nested Transformations (`Transformation`)

A **Nested Transformation** represents a processing unit within a transformation or reusable transformation. Types include:

- **EXPRESSION**: Calculated fields and expressions
- **LOOKUP**: Lookup operations (connected/unconnected)
- **AGGREGATOR**: Aggregation operations (SUM, AVG, COUNT, etc.)
- **JOINER**: Join operations between multiple sources
- **FILTER**: Filtering logic
- **ROUTER**: Conditional routing
- **SORTER**: Sorting operations
- **RANKER**: Ranking operations
- **NORMALIZER**: Normalization operations
- **MAPPLET_INSTANCE**: Instance of a reusable transformation used in a transformation

**Key Properties:**
- `name`: Transformation identifier
- `type`: Transformation type
- `transformation`: Name of the parent transformation (for nested transformations)
- `reusable_transformation_ref`: Reference to reusable transformation (for MAPPLET_INSTANCE types)
- `ports`: Input and output ports
- Type-specific attributes (e.g., `lookup_type`, `group_by_ports`, `aggregate_functions`)

### 7. Sources (`Source`)

A **Source** represents an input data source (table, file, etc.).

**Key Properties:**
- `name`: Source identifier
- `table`: Table name
- `database`: Database name
- `fields`: List of field definitions (name, data_type, etc.)

### 8. Targets (`Target`)

A **Target** represents an output data destination (table, file, etc.).

**Key Properties:**
- `name`: Target identifier
- `table`: Table name (preserved for metrics display)
- `database`: Database name
- `fields`: List of field definitions
- `load_type`: Load type (INSERT, UPDATE, DELETE, UPSERT)

### 9. Connectors (`CONNECTS_TO`)

A **Connector** represents data flow between components:
- Source → Transformation
- Transformation → Transformation
- Transformation → Target

**Key Properties:**
- `from_transformation`: Source component name
- `to_transformation`: Target component name
- `from_port`: Source port name
- `to_port`: Target port name

### 10. Tables (`Table`)

A **Table** represents a physical database table referenced by sources or targets.

**Key Properties:**
- `name`: Table name
- `database`: Database name
- `platform`: Database platform (Oracle, SQL Server, etc.)

---

## JSON Structure

### Memory Representation

**Current Implementation**: Python Dictionary (nested JSON structure)

```python
# In-memory representation
canonical_model: Dict[str, Any] = {
    "transformation_name": "M_LOAD_CUSTOMER",
    "source_component_type": "mapping",
    "sources": [...],
    "targets": [...],
    "transformations": [...],
    "connectors": [...],
    "lineage": {...},
    "scd_type": "SCD2",
    "incremental_keys": [...],
    # AI enhancements (optional)
    "_optimization_hint": {...},
    "_data_quality_rules": [...],
    "_performance_metadata": {...},
    "_provenance": {...}
}
```

**Storage Format**: JSON files (via `VersionStore`)
- Serialized: `json.dumps(model, indent=2)`
- Stored in: `versions/{transformation_name}.json`
- Loaded: `json.load(file)`

### Complete Structure

#### 1. Top-Level Structure

```json
{
  "transformation_name": "M_LOAD_CUSTOMER",
  "source_component_type": "mapping",
  "sources": [...],           // List of source definitions
  "targets": [...],           // List of target definitions
  "transformations": [...],   // List of transformation objects
  "connectors": [...],        // List of data flow connections
  "lineage": {...},           // Lineage information
  "scd_type": "SCD2",        // Slowly Changing Dimension type
  "incremental_keys": [...]   // Keys for incremental loading
}
```

#### 2. Sources Structure

```json
{
  "name": "SQ_CUSTOMER",
  "table": "CUSTOMER_SRC",
  "database": "source_db",
  "fields": [
    {
      "name": "CUSTOMER_ID",
      "data_type": "STRING",
      "nullable": true
    },
    {
      "name": "FIRST_NAME",
      "data_type": "STRING"
    },
    {
      "name": "ORDER_DATE",
      "data_type": "TIMESTAMP"
    }
  ]
}
```

#### 3. Targets Structure

```json
{
  "name": "TGT_CUSTOMER",
  "table": "DIM_CUSTOMER",
  "database": "lakehouse_db",
  "fields": [
    {
      "name": "CUSTOMER_ID",
      "data_type": "STRING"
    },
    {
      "name": "FULL_NAME",
      "data_type": "STRING"
    }
  ]
}
```

**Note**: The `table` property preserves the table name for canonical model view metrics display.

#### 4. Transformations Structure

**Base Structure:**
```json
{
  "name": "EXP_DERIVE",
  "type": "EXPRESSION",
  "ports": [
    {
      "name": "FULL_NAME",
      "port_type": "OUTPUT",
      "expression": "FIRST_NAME || ' ' || LAST_NAME",
      "data_type": "STRING"
    }
  ],
  "_optimization_hint": "consider_splitting",
  "_optimization_reason": "Large number of output ports"
}
```

**Type-Specific Attributes:**

- **LOOKUP**:
```json
{
  "name": "LK_REGION",
  "type": "LOOKUP",
  "lookup_type": "connected",
  "cache_type": "none",
  "table_name": "REGION_DIM",
  "condition": "REGION_ID = :LKP.REGION_ID",
  "_optimization_hint": "broadcast_join"
}
```

- **AGGREGATOR**:
```json
{
  "name": "AGG_SALES",
  "type": "AGGREGATOR",
  "group_by_ports": ["CUSTOMER_ID"],
  "aggregate_functions": [
    {
      "port": "TOTAL_SALES",
      "expression": "SUM(SALES_AMT)"
    }
  ],
  "_optimization_hint": "partition_by_group_by"
}
```

- **JOINER**:
```json
{
  "name": "JNR_ORDERS",
  "type": "JOINER",
  "join_type": "INNER",
  "conditions": [
    {
      "left": "CUSTOMER_ID",
      "right": "CUSTOMER_ID",
      "operator": "="
    }
  ]
}
```

- **FILTER**:
```json
{
  "name": "FILTER_ACTIVE",
  "type": "FILTER",
  "filter_condition": "STATUS = 'ACTIVE'",
  "_optimization_hint": "filter_pushdown"
}
```

#### 5. Connectors Structure

```json
{
  "from_transformation": "SQ_CUSTOMER",
  "to_transformation": "EXP_DERIVE",
  "from_port": "*",
  "to_port": "*"
}
```

#### 6. Lineage Structure

```json
{
  "column_level": {
    "FULL_NAME": ["FIRST_NAME", "LAST_NAME"],
    "TOTAL_SALES": ["SALES_AMT", "CUSTOMER_ID"]
  },
  "transformation_level": [
    {
      "from": "SQ_CUSTOMER",
      "to": "EXP_DERIVE",
      "from_port": "*",
      "to_port": "*"
    }
  ],
  "workflow_level": {
    "transformation_name": "M_LOAD_CUSTOMER",
    "sources": ["SQ_CUSTOMER"],
    "targets": ["TGT_CUSTOMER"]
  }
}
```

#### 7. Enhancement Metadata (Optional)

```json
{
  "_optimization_hints": {
    "LK_REGION": "broadcast_join",
    "AGG_SALES": "partition_by_group_by"
  },
  "_data_quality_rules": [
    {
      "type": "NOT_NULL",
      "field": "CUSTOMER_ID",
      "severity": "ERROR",
      "description": "CUSTOMER_ID should not be null"
    }
  ],
  "_performance_metadata": {
    "complexity": "MEDIUM",
    "estimated_runtime": "MEDIUM",
    "transformation_count": 4
  },
  "_provenance": {
    "original_model_hash": "abc123...",
    "enhanced_model_hash": "def456...",
    "enhanced_at": "2024-11-28T08:00:00",
    "enhancement_agent": "ModelEnhancementAgent",
    "llm_used": false,
    "model_changed": true,
    "enhancements_applied": [
      "Inferred data type for ORDER_DATE",
      "Added broadcast_join hint to LK_REGION",
      "Added partition hint to AGG_SALES"
    ]
  }
}
```

#### 8. Reusable Transformation Instance

When a reusable transformation is used in a transformation, it appears as a `MAPPLET_INSTANCE` transformation:

```json
{
  "type": "MAPPLET_INSTANCE",
  "name": "MPL_TOTALS_INST",
  "reusable_transformation_ref": "MPL_CALCULATE_TOTALS",
  "input_port_mappings": {
    "UNIT_PRICE": {
      "from_transformation": "JNR_ORDERS_ITEMS",
      "from_port": "ITEM_PRICE"
    },
    "QUANTITY": {
      "from_transformation": "JNR_ORDERS_ITEMS",
      "from_port": "QUANTITY"
    }
  },
  "output_port_mappings": {
    "GRAND_TOTAL": {
      "to_transformation": "AGG_ORDER_SUMMARY",
      "to_port": "GRAND_TOTAL"
    }
  },
  "requires_resolution": true,
  "resolution_strategy": "inline"
}
```

### Memory Characteristics

**Size**: 
- Small transformation: ~10-50 KB (JSON)
- Medium transformation: ~50-200 KB
- Large transformation: ~200 KB - 2 MB
- Enterprise (1000s of transformations): Could be GBs

**Structure**:
- **Hierarchical**: Nested dictionaries and lists
- **Referential**: Connectors reference transformations by name
- **Graph-like**: Transformations connected via connectors (implicit graph)
- **Currently Flat**: Each transformation is a separate JSON file

---

## Neo4j Graph Representation

### Why Graph Database?

For **large-scale enterprise migrations** with **thousands of transformations**, a graph database provides:

1. **Relationship Queries**: Natural representation of data flow
2. **Cross-Transformation Lineage**: Trace dependencies across entire platform
3. **Pattern Discovery**: Find similar transformations, shared patterns
4. **Impact Analysis**: "What breaks if I change this table?"
5. **Knowledge Graph**: Build enterprise-wide data lineage
6. **Efficient Traversals**: Graph algorithms for dependency analysis

### Schema Management

The Neo4j schema uses platform-agnostic terminology. To recreate the schema:

```bash
python scripts/schema/create_neo4j_schema.py
```

This script will:
1. Drop all existing nodes and relationships
2. Create indexes with generic labels (`:Transformation`, `:Pipeline`, `:Task`, `:SubPipeline`, `:ReusableTransformation`)
3. Set up indexes for performance

**Note**: This will delete all existing data. Use only during development or when you want a clean slate.

### Node Types

#### 1. Transformation Node

```cypher
(:Transformation {
  name: "M_LOAD_CUSTOMER",
  transformation_name: "M_LOAD_CUSTOMER",
  source_component_type: "mapping",
  scd_type: "SCD2",
  incremental_keys: ["customer_id"]
})
```

**Properties:**
- `name`: Unique identifier (same as transformation_name)
- `transformation_name`: Transformation name
- `source_component_type`: Source platform component type (e.g., 'mapping', 'mapplet')
- `scd_type`: Slowly Changing Dimension type
- `incremental_keys`: Array of incremental key field names

#### 2. Reusable Transformation Node

```cypher
(:ReusableTransformation {
  name: "MPL_CALCULATE_TOTALS",
  source_component_type: "mapplet",
  type: "REUSABLE_TRANSFORMATION"
})
```

**Properties:**
- `name`: Unique identifier
- `source_component_type`: Source platform component type (e.g., 'mapplet' for Informatica mapplets)
- `type`: Always "REUSABLE_TRANSFORMATION"
- Additional properties stored as JSON strings for complex objects

#### 3. Nested Transformation Node

```cypher
(:Transformation {
  name: "EXP_CALCULATIONS",
  type: "EXPRESSION",
  transformation: "M_LOAD_CUSTOMER"
})
```

**Properties:**
- `name`: Transformation identifier
- `type`: Transformation type (EXPRESSION, LOOKUP, AGGREGATOR, etc.)
- `transformation`: Name of the parent transformation this nested transformation belongs to
- `reusable_transformation_ref`: Reference to reusable transformation (for MAPPLET_INSTANCE types)
- Complex objects (ports, connectors) stored as JSON strings with `_json` suffix

#### 4. Source Node

```cypher
(:Source {
  name: "SQ_CUSTOMER",
  transformation: "M_LOAD_CUSTOMER",
  table: "CUSTOMER",
  database: "ORACLE_DB"
})
```

**Properties:**
- `name`: Source identifier
- `transformation`: Name of the transformation this source belongs to
- `table`: Table name
- `database`: Database name

#### 5. Target Node

```cypher
(:Target {
  name: "TGT_CUSTOMER",
  transformation: "M_LOAD_CUSTOMER",
  table: "DIM_CUSTOMER",
  database: "DATA_WAREHOUSE",
  load_type: "INSERT"
})
```

**Properties:**
- `name`: Target identifier
- `transformation`: Name of the transformation this target belongs to
- `table`: Table name (preserved for metrics display)
- `database`: Database name
- `load_type`: Load type (INSERT, UPDATE, DELETE, UPSERT)

#### 6. Table Node

```cypher
(:Table {
  name: "CUSTOMER",
  database: "ORACLE_DB",
  platform: "Oracle"
})
```

**Properties:**
- `name`: Table name
- `database`: Database name
- `platform`: Database platform

#### 7. Pipeline Node

```cypher
(:Pipeline {
  name: "WF_CUSTOMER_ETL",
  source_component_type: "workflow",
  type: "PIPELINE"
})
```

**Properties:**
- `name`: Pipeline identifier
- `source_component_type`: Source platform component type (e.g., 'workflow' for Informatica workflows)
- `type`: Always "PIPELINE"

#### 8. Task Node

```cypher
(:Task {
  name: "S_M_LOAD_CUSTOMER",
  source_component_type: "session",
  type: "TASK",
  transformation_name: "M_LOAD_CUSTOMER"
})
```

**Properties:**
- `name`: Task identifier
- `source_component_type`: Source platform component type (e.g., 'session' for Informatica sessions)
- `type`: Always "TASK"
- `transformation_name`: Name of the transformation this task executes

#### 9. SubPipeline Node

```cypher
(:SubPipeline {
  name: "WL_CUSTOMER_PROCESSING",
  source_component_type: "worklet",
  type: "SUB_PIPELINE"
})
```

**Properties:**
- `name`: SubPipeline identifier
- `source_component_type`: Source platform component type (e.g., 'worklet' for Informatica worklets)
- `type`: Always "SUB_PIPELINE"

#### 10. SourceFile Node

```cypher
(:SourceFile {
  filename: "mapping_load_customer.xml",
  file_path: "test_log/staging/mapping_load_customer.xml",
  file_type: "mapping",
  file_size: 10240,
  parsed_at: "2025-12-03T10:00:00"
})
```

**Properties:**
- `filename`: Original filename
- `file_path`: Full file path
- `file_type`: Component type (mapping, workflow, session, worklet, mapplet)
- `file_size`: File size in bytes
- `parsed_at`: Timestamp when parsed

#### 11. GeneratedCode Node

```cypher
(:GeneratedCode {
  file_path: "test_log/generated/workflows/customer_etl/tasks/load_customer/transformations/m_load_customer/m_load_customer_pyspark.py",
  code_type: "pyspark",
  language: "python",
  quality_score: 85,
  transformation_name: "M_LOAD_CUSTOMER",
  generated_at: "2025-12-03T10:30:00"
})
```

**Properties:**
- `file_path`: Path to generated code file
- `code_type`: Code type (pyspark, dlt, sql)
- `language`: Programming language
- `quality_score`: Code quality score (0-100)
- `transformation_name`: Name of transformation this code was generated for
- `generated_at`: Timestamp when generated

### Relationships

#### Transformation Relationships

```cypher
// Transformation has sources
(:Transformation)-[:HAS_SOURCE]->(:Source)

// Transformation has targets
(:Transformation)-[:HAS_TARGET]->(:Target)

// Transformation has nested transformations
(:Transformation)-[:HAS_TRANSFORMATION]->(:Transformation)

// Transformation uses reusable transformation
(:Transformation)-[:USES_REUSABLE_TRANSFORMATION]->(:ReusableTransformation)
```

#### Data Flow Relationships

```cypher
// Source connects to transformation
(:Source)-[:CONNECTS_TO {from_port: "field1", to_port: "input1"}]->(:Transformation)

// Transformation connects to transformation
(:Transformation)-[:CONNECTS_TO {from_port: "output1", to_port: "input2"}]->(:Transformation)

// Transformation connects to target
(:Transformation)-[:CONNECTS_TO {from_port: "output1", to_port: "field1"}]->(:Target)
```

#### Table Relationships

```cypher
// Source reads from table
(:Source)-[:READS_TABLE]->(:Table)

// Target writes to table
(:Target)-[:WRITES_TABLE]->(:Table)
```

#### Pipeline Relationships

```cypher
// Pipeline contains task
(:Pipeline)-[:CONTAINS]->(:Task)

// Pipeline contains sub pipeline
(:Pipeline)-[:CONTAINS]->(:SubPipeline)

// SubPipeline contains task
(:SubPipeline)-[:CONTAINS]->(:Task)

// Task executes transformation
(:Task)-[:EXECUTES]->(:Transformation)
```

#### File Metadata Relationships

```cypher
// Component loaded from file
(:Transformation)-[:LOADED_FROM]->(:SourceFile)
(:Pipeline)-[:LOADED_FROM]->(:SourceFile)
(:Task)-[:LOADED_FROM]->(:SourceFile)
(:SubPipeline)-[:LOADED_FROM]->(:SourceFile)
(:ReusableTransformation)-[:LOADED_FROM]->(:SourceFile)
```

### Example Graph Queries

#### 1. Impact Analysis

```cypher
// What transformations will break if CUSTOMER_SRC table changes?
MATCH (tab:Table {name: "CUSTOMER_SRC"})<-[:READS_TABLE]-(s:Source)<-[:HAS_SOURCE]-(t:Transformation)
WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
RETURN t.name, t.transformation_name
```

#### 2. Dependency Chain

```cypher
// Find all transformations that depend on M_LOAD_CUSTOMER
MATCH path = (t:Transformation {name: "M_LOAD_CUSTOMER", source_component_type: 'mapping'})<-[:DEPENDS_ON*]-(dependent:Transformation)
WHERE dependent.source_component_type = 'mapping' OR dependent.source_component_type IS NULL
RETURN dependent.name, dependent.transformation_name, length(path) as depth
ORDER BY depth
```

#### 3. Pattern Discovery

```cypher
// Find all transformations with similar transformation patterns
MATCH (t1:Transformation {type: "LOOKUP"})-[:HAS_TRANSFORMATION]->(main1:Transformation),
      (t2:Transformation {type: "LOOKUP"})-[:HAS_TRANSFORMATION]->(main2:Transformation)
WHERE t1.table_name = t2.table_name AND main1 <> main2
RETURN main1.name, main2.name, t1.table_name
```

#### 4. Cross-Transformation Lineage

```cypher
// Trace data flow from source table to final target across transformations
MATCH path = (src:Table {name: "CUSTOMER_SRC"})
            <-[:READS_TABLE]-(s:Source)
            <-[:HAS_SOURCE]-(t1:Transformation)
            WHERE t1.source_component_type = 'mapping' OR t1.source_component_type IS NULL
            -[:HAS_TARGET]->(tgt1:Target)
            -[:WRITES_TABLE]->(intermediate:Table)
            <-[:READS_TABLE]-(s2:Source)
            <-[:HAS_SOURCE]-(t2:Transformation)
            WHERE t2.source_component_type = 'mapping' OR t2.source_component_type IS NULL
            -[:HAS_TARGET]->(tgt2:Target)
            -[:WRITES_TABLE]->(tgt:Table {name: "CUSTOMER_FINAL"})
RETURN path
```

#### 5. Migration Planning

```cypher
// Find transformations that can be migrated in parallel (no dependencies)
MATCH (t:Transformation)
WHERE (t.source_component_type = 'mapping' OR t.source_component_type IS NULL)
AND NOT (t)-[:DEPENDS_ON]->()
RETURN t.name, t.transformation_name, t.complexity
ORDER BY t.complexity
```

### Benefits for Large-Scale Migrations

1. **Enterprise-Wide Lineage**: See data flow across entire platform
2. **Impact Analysis**: Understand change impact across transformations
3. **Pattern Reuse**: Find and reuse similar transformation patterns
4. **Migration Planning**: Identify dependencies and migration order
5. **Knowledge Graph**: Build AI-enhanced knowledge base
6. **Query Performance**: Fast relationship queries vs. scanning files
7. **Scalability**: Handle millions of nodes and relationships

---

## Storage and Persistence

### Storage Formats

The canonical model is stored in multiple formats:

1. **JSON Files**: 
   - Location: `test_log/parsed/` and `test_log/parse_ai/` directories
   - Format: Complete canonical model JSON files
   - Purpose: Code generation, versioning, human-readable

2. **Neo4j Graph Database**: 
   - Format: Nodes and relationships
   - Purpose: Querying, analysis, relationship traversal
   - Benefits: Fast queries, cross-transformation analysis, lineage

3. **Version Store**: 
   - Location: `versions/` directory
   - Format: JSON files
   - Purpose: Versioning and history tracking

### Dual Storage Approach

**JSON Files**:
- Complete canonical model representation
- Easy to version control
- Fast to load for code generation
- Human-readable

**Neo4j Graph**:
- Enables complex relationship queries
- Supports workflow-level analysis
- Provides lineage traversal
- Enables impact analysis

This dual-storage approach provides the best of both worlds: complete fidelity for code generation and powerful querying capabilities for analysis and exploration.

### Design Decisions

#### Why Store Complex Objects as JSON Strings?

Neo4j has limitations on storing complex nested objects. Properties like `ports`, `connectors`, and `input_port_mappings` are stored as JSON strings with a `_json` suffix (e.g., `ports_json`, `connectors_json`).

**Benefits:**
- Preserves complete structure
- Allows querying by simple properties
- Enables reconstruction of full canonical model

**Trade-offs:**
- Cannot directly query nested properties in Cypher
- Requires JSON parsing when loading full model

#### Why Separate Transformation and Nested Transformation Nodes?

Nested transformations are stored as separate nodes rather than nested within transformation nodes because:
- Enables efficient querying of transformation types across all transformations
- Supports relationship queries (which transformations connect to which)
- Allows analysis of transformation patterns
- Maintains referential integrity

---

## Usage

The canonical model is used by:

- **Code Generators**: Generate PySpark, DLT, SQL from the model
- **AI Agents**: Analyze and explain based on model structure
- **Lineage Engine**: Build lineage graphs from model connections
- **Documentation Generators**: Create specs from model metadata
- **Assessment Tools**: Analyze complexity, dependencies, migration readiness
- **UI Components**: Display transformations, metrics, relationships

---

## Examples

### Example 1: Simple Transformation Structure

**Transformation:** `M_LOAD_CUSTOMER`

**JSON:**
```json
{
  "transformation_name": "M_LOAD_CUSTOMER",
  "source_component_type": "mapping",
  "sources": [
    {
      "name": "SQ_CUSTOMER",
      "table": "CUSTOMER",
      "database": "ORACLE_DB",
      "fields": [
        {"name": "customer_id", "data_type": "number"},
        {"name": "first_name", "data_type": "string"}
      ]
    }
  ],
  "targets": [
    {
      "name": "TGT_CUSTOMER",
      "table": "DIM_CUSTOMER",
      "database": "DATA_WAREHOUSE",
      "fields": [
        {"name": "customer_id", "data_type": "number"},
        {"name": "full_name", "data_type": "string"}
      ]
    }
  ],
  "transformations": [
    {
      "name": "EXP_CALCULATIONS",
      "type": "EXPRESSION",
      "ports": [
        {
          "name": "full_name",
          "port_type": "OUTPUT",
          "expression": "FIRST_NAME || ' ' || LAST_NAME"
        }
      ]
    }
  ],
  "connectors": [
    {
      "from_transformation": "SQ_CUSTOMER",
      "to_transformation": "EXP_CALCULATIONS",
      "from_port": "first_name",
      "to_port": "first_name"
    }
  ],
  "scd_type": "SCD2",
  "incremental_keys": ["customer_id"]
}
```

**Neo4j Graph:**
```cypher
// Create transformation
CREATE (t:Transformation {
  name: "M_LOAD_CUSTOMER",
  transformation_name: "M_LOAD_CUSTOMER",
  source_component_type: "mapping",
  scd_type: "SCD2"
})

// Create source
CREATE (s:Source {
  name: "SQ_CUSTOMER",
  transformation: "M_LOAD_CUSTOMER",
  table: "CUSTOMER",
  database: "ORACLE_DB"
})
CREATE (tab:Table {name: "CUSTOMER", database: "ORACLE_DB", platform: "Oracle"})

// Create nested transformation
CREATE (trans:Transformation {
  name: "EXP_CALCULATIONS",
  type: "EXPRESSION",
  transformation: "M_LOAD_CUSTOMER"
})

// Create target
CREATE (tgt:Target {
  name: "TGT_CUSTOMER",
  transformation: "M_LOAD_CUSTOMER",
  table: "DIM_CUSTOMER",
  database: "DATA_WAREHOUSE"
})

// Create relationships
CREATE (t)-[:HAS_SOURCE]->(s)
CREATE (t)-[:HAS_TRANSFORMATION]->(trans)
CREATE (t)-[:HAS_TARGET]->(tgt)
CREATE (s)-[:READS_TABLE]->(tab)
CREATE (s)-[:CONNECTS_TO {from_port: "first_name", to_port: "first_name"}]->(trans)
CREATE (trans)-[:CONNECTS_TO {from_port: "full_name", to_port: "full_name"}]->(tgt)
```

### Example 2: Transformation with Reusable Transformation

**Transformation:** `M_PROCESS_ORDERS` uses reusable transformation `MPL_CALCULATE_TOTALS`

**JSON:**
```json
{
  "transformation_name": "M_PROCESS_ORDERS",
  "source_component_type": "mapping",
  "transformations": [
    {
      "type": "MAPPLET_INSTANCE",
      "name": "MPL_TOTALS_INST",
      "reusable_transformation_ref": "MPL_CALCULATE_TOTALS",
      "input_port_mappings": {
        "UNIT_PRICE": {
          "from_transformation": "JNR_ORDERS_ITEMS",
          "from_port": "ITEM_PRICE"
        }
      }
    }
  ]
}
```

**Neo4j Graph:**
```cypher
// Create transformation
CREATE (t:Transformation {
  name: "M_PROCESS_ORDERS",
  transformation_name: "M_PROCESS_ORDERS",
  source_component_type: "mapping"
})

// Create reusable transformation
CREATE (rt:ReusableTransformation {
  name: "MPL_CALCULATE_TOTALS",
  source_component_type: "mapplet",
  type: "REUSABLE_TRANSFORMATION"
})

// Create reusable transformation instance
CREATE (mpl_inst:Transformation {
  name: "MPL_TOTALS_INST",
  type: "MAPPLET_INSTANCE",
  transformation: "M_PROCESS_ORDERS",
  reusable_transformation_ref: "MPL_CALCULATE_TOTALS"
})

// Create relationships
CREATE (t)-[:USES_REUSABLE_TRANSFORMATION]->(rt)
CREATE (t)-[:HAS_TRANSFORMATION]->(mpl_inst)
```

### Example 3: Pipeline Structure

**Pipeline:** `WF_CUSTOMER_ETL`

**Neo4j Graph:**
```cypher
// Create pipeline
CREATE (p:Pipeline {
  name: "WF_CUSTOMER_ETL",
  source_component_type: "workflow",
  type: "PIPELINE"
})

// Create task
CREATE (task:Task {
  name: "S_M_LOAD_CUSTOMER",
  source_component_type: "session",
  type: "TASK",
  transformation_name: "M_LOAD_CUSTOMER"
})

// Create transformation
CREATE (t:Transformation {
  name: "M_LOAD_CUSTOMER",
  transformation_name: "M_LOAD_CUSTOMER",
  source_component_type: "mapping"
})

// Create relationships
CREATE (p)-[:CONTAINS]->(task)
CREATE (task)-[:EXECUTES]->(t)
```

---

## Summary

The Canonical Model provides a standardized, platform-agnostic representation of ETL logic. It is stored in two complementary formats:

1. **JSON Files**: Complete, versioned representation for code generation
2. **Neo4j Graph**: Queryable graph structure for analysis and exploration

The model uses generic terminology (Transformations, Pipelines, Tasks) while preserving source platform information through `source_component_type` properties. This enables support for multiple ETL platforms (Informatica, DataStage, Talend, etc.) while maintaining traceability to the original source.

The Neo4j representation uses nodes for components (Transformations, Pipelines, Tasks, etc.) and relationships to represent data flow, containment, and execution. Complex nested structures are stored as JSON strings to preserve completeness while maintaining queryability.

This dual-storage approach provides the best of both worlds: complete fidelity for code generation and powerful querying capabilities for analysis and exploration.
