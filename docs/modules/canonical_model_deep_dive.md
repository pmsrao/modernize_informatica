# Canonical Model Deep Dive & Graph Database Analysis

## a) What is the Canonical Model?

### Definition

The **Canonical Model** is a **technology-neutral, standardized JSON representation** of Informatica ETL logic. It serves as the **single source of truth** that abstracts away Informatica-specific XML structures into a uniform format that all downstream components can use.

### Memory Representation

**Current Implementation**: Python Dictionary (nested JSON structure)

```python
# In-memory representation
canonical_model: Dict[str, Any] = {
    "mapping_name": "M_LOAD_CUSTOMER",
    "sources": [...],
    "targets": [...],
    "transformations": [...],
    "connectors": [...],
    "lineage": {...},
    "scd_type": "SCD2",
    "incremental_keys": [...],
    # Phase 1 enhancements (optional)
    "_optimization_hint": {...},
    "_data_quality_rules": [...],
    "_performance_metadata": {...},
    "_provenance": {...}
}
```

**Storage Format**: JSON files (via `VersionStore`)
- Serialized: `json.dumps(model, indent=2)`
- Stored in: `versions/{mapping_name}.json`
- Loaded: `json.load(file)`

### Complete Structure

#### 1. **Top-Level Structure**

```json
{
  "mapping_name": "M_LOAD_CUSTOMER",
  "sources": [...],           // List of source definitions
  "targets": [...],           // List of target definitions
  "transformations": [...],   // List of transformation objects
  "connectors": [...],        // List of data flow connections
  "lineage": {...},           // Lineage information
  "scd_type": "SCD2",        // Slowly Changing Dimension type
  "incremental_keys": [...]   // Keys for incremental loading
}
```

#### 2. **Sources Structure**

```json
{
  "name": "SQ_CUSTOMER",
  "table": "CUSTOMER_SRC",
  "database": "source_db",
  "fields": [
    {
      "name": "CUSTOMER_ID",
      "data_type": "STRING",      // Inferred by enhancement agent
      "nullable": true
    },
    {
      "name": "FIRST_NAME",
      "data_type": "STRING"
    },
    {
      "name": "ORDER_DATE",
      "data_type": "TIMESTAMP"    // Inferred from name pattern
    }
  ]
}
```

#### 3. **Targets Structure**

```json
{
  "name": "TGT_CUSTOMER",
  "table": "CUSTOMER_TGT",
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

#### 4. **Transformations Structure**

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
  // Phase 1 enhancements
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

#### 5. **Connectors Structure**

```json
{
  "from_transformation": "SQ_CUSTOMER",
  "to_transformation": "EXP_DERIVE",
  "from_port": "*",
  "to_port": "*"
}
```

#### 6. **Lineage Structure**

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
    "mapping_name": "M_LOAD_CUSTOMER",
    "sources": ["SQ_CUSTOMER"],
    "targets": ["TGT_CUSTOMER"]
  }
}
```

#### 7. **Enhancement Metadata (Phase 1)**

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

### Memory Characteristics

**Size**: 
- Small mapping: ~10-50 KB (JSON)
- Medium mapping: ~50-200 KB
- Large mapping: ~200 KB - 2 MB
- Enterprise (1000s of mappings): Could be GBs

**Structure**:
- **Hierarchical**: Nested dictionaries and lists
- **Referential**: Connectors reference transformations by name
- **Graph-like**: Transformations connected via connectors (implicit graph)
- **Currently Flat**: Each mapping is a separate JSON file

### Current Limitations for Large-Scale

1. **No Cross-Mapping Relationships**: Each mapping is isolated
2. **No Global Lineage**: Can't trace data flow across mappings
3. **No Shared Knowledge**: Patterns learned from one mapping don't help others
4. **No Efficient Queries**: "Find all mappings using CUSTOMER table" requires scanning all files
5. **No Relationship Queries**: "What mappings depend on this mapping?"
6. **Memory Inefficient**: Loading all mappings into memory is expensive

---

## b) Graph Database Analysis for Large-Scale Migrations

### Why Graph Database?

For **large-scale enterprise migrations** with **thousands of mappings**, a graph database provides:

1. **Relationship Queries**: Natural representation of data flow
2. **Cross-Mapping Lineage**: Trace dependencies across entire platform
3. **Pattern Discovery**: Find similar mappings, shared transformations
4. **Impact Analysis**: "What breaks if I change this table?"
5. **Knowledge Graph**: Build enterprise-wide data lineage
6. **Efficient Traversals**: Graph algorithms for dependency analysis

### Graph Model Design

#### Node Types

```
Mapping
├── name: "M_LOAD_CUSTOMER"
├── type: "MAPPING"
├── metadata: {...}
└── properties: {scd_type, incremental_keys, ...}

Transformation
├── name: "EXP_DERIVE"
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

#### Relationship Types

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

### Graph Database Options

#### Option 1: **Neo4j** (Recommended for Enterprise)

**Pros**:
- Mature, production-ready
- Excellent query language (Cypher)
- Strong community and tooling
- Good Python integration (`neo4j` driver)
- Handles billions of nodes/relationships
- Built-in graph algorithms
- **Open source Community Edition** available
- Enterprise features available when needed

**Cons**:
- Requires separate infrastructure
- Learning curve for Cypher
- Enterprise licensing costs (but open source is free)

**Example Cypher Query**:
```cypher
// Find all mappings that use CUSTOMER_SRC table
MATCH (m:Mapping)-[:HAS_SOURCE]->(s:Source)-[:READS_TABLE]->(t:Table {name: "CUSTOMER_SRC"})
RETURN m.name, m.mapping_name

// Find dependency chain
MATCH path = (m1:Mapping)-[:DEPENDS_ON*]->(m2:Mapping)
WHERE m1.name = "M_LOAD_CUSTOMER"
RETURN path

// Find similar transformations
MATCH (t1:Transformation)-[:HAS_PATTERN]->(p:Pattern)<-[:HAS_PATTERN]-(t2:Transformation)
WHERE t1 <> t2
RETURN t1.name, t2.name, p.pattern_type
```

#### Option 2: **Amazon Neptune** (Cloud-Native)

**Pros**:
- Fully managed (AWS)
- Scales automatically
- Gremlin and SPARQL support
- Good for cloud-native architectures

**Cons**:
- AWS lock-in
- Cost at scale
- Less flexible than self-hosted

#### Option 3: **ArangoDB** (Multi-Model)

**Pros**:
- Supports graphs, documents, key-value
- Single database for multiple use cases
- Good performance
- Open source

**Cons**:
- Less specialized for pure graph use cases
- Smaller community than Neo4j

#### Option 4: **In-Memory Graph** (Python Libraries)

**Pros**:
- No infrastructure needed
- Fast for small-medium graphs
- Easy integration

**Cons**:
- Doesn't scale to enterprise
- Memory limitations
- No persistence

**Libraries**:
- `networkx`: Python graph library
- `igraph`: Fast graph library
- `graph-tool`: High-performance

### Hybrid Approach (Recommended)

**For Phase 1-2**: Keep current JSON-based storage
**For Phase 3+**: Add graph database layer

```
JSON Files (Current)
    ↓
Graph Database (Future)
    ↓
Knowledge Graph (AI-Enhanced)
```

**Architecture**:
1. **JSON as Source of Truth**: Keep canonical models as JSON
2. **Graph as Index**: Build graph index for queries
3. **Sync Mechanism**: Keep graph in sync with JSON
4. **Query Layer**: Use graph for queries, JSON for details

### Implementation Strategy

#### Phase 1: Current (JSON-based)
- ✅ Simple, works for small-medium scale
- ✅ No infrastructure needed
- ❌ Doesn't scale to thousands of mappings

#### Phase 2: Add Graph Index (Hybrid)
- Keep JSON as source of truth
- Build graph index for queries
- Use graph for relationship queries
- Use JSON for full model details

#### Phase 3: Full Graph Database
- Migrate to graph-first architecture
- Use graph for storage and queries
- JSON export for compatibility

### Graph Model Schema

```python
# Node Labels
NODE_LABELS = {
    "Mapping", "Transformation", "Source", "Target", 
    "Field", "Workflow", "Session", "Table", "Database",
    "Pattern", "Rule", "Enhancement", "Expression"
}

# Relationship Types
RELATIONSHIP_TYPES = {
    "HAS_TRANSFORMATION", "HAS_SOURCE", "HAS_TARGET",
    "CONNECTS_TO", "READS_FROM", "WRITES_TO",
    "FLOWS_TO", "DERIVED_FROM", "USES_TABLE",
    "READS_TABLE", "WRITES_TABLE", "CONTAINS", 
    "EXECUTES", "DEPENDS_ON", "SIMILAR_TO", 
    "USES_PATTERN", "HAS_ENHANCEMENT", "FEEDS_INTO"
}
```

### Example Graph Queries for Large-Scale

#### 1. **Impact Analysis**
```cypher
// What mappings will break if CUSTOMER_SRC table changes?
MATCH (t:Table {name: "CUSTOMER_SRC"})<-[:READS_TABLE]-(s:Source)<-[:HAS_SOURCE]-(m:Mapping)
RETURN m.name, m.mapping_name
```

#### 2. **Dependency Chain**
```cypher
// Find all mappings that depend on M_LOAD_CUSTOMER
MATCH path = (dependent:Mapping)-[:DEPENDS_ON*]->(m:Mapping {name: "M_LOAD_CUSTOMER"})
RETURN dependent.name, length(path) as depth
ORDER BY depth
```

#### 3. **Pattern Discovery**
```cypher
// Find all mappings with similar transformation patterns
MATCH (m1:Mapping)-[:HAS_TRANSFORMATION]->(t1:Transformation {type: "LOOKUP"}),
      (m2:Mapping)-[:HAS_TRANSFORMATION]->(t2:Transformation {type: "LOOKUP"})
WHERE t1.table_name = t2.table_name AND m1 <> m2
RETURN m1.name, m2.name, t1.table_name
```

#### 4. **Cross-Mapping Lineage**
```cypher
// Trace data flow from source table to final target across mappings
MATCH path = (src:Table {name: "CUSTOMER_SRC"})
            <-[:READS_TABLE]-(s:Source)
            <-[:HAS_SOURCE]-(m1:Mapping)
            -[:HAS_TARGET]->(t1:Target)
            -[:WRITES_TABLE]->(intermediate:Table)
            <-[:READS_TABLE]-(s2:Source)
            <-[:HAS_SOURCE]-(m2:Mapping)
            -[:HAS_TARGET]->(t2:Target {table: "CUSTOMER_FINAL"})
RETURN path
```

#### 5. **Knowledge Extraction**
```cypher
// Find all mappings using a specific business rule pattern
MATCH (t:Transformation)-[:HAS_EXPRESSION]->(e:Expression)
WHERE e.expression CONTAINS "IIF(AGE < 30"
RETURN t.name, t.mapping, e.expression
```

#### 6. **Migration Planning**
```cypher
// Find mappings that can be migrated in parallel (no dependencies)
MATCH (m:Mapping)
WHERE NOT (m)-[:DEPENDS_ON]->()
RETURN m.name, m.mapping_name
ORDER BY m.complexity
```

#### 7. **Shared Resources**
```cypher
// Find tables used by multiple mappings (shared resources)
MATCH (t:Table)<-[:READS_TABLE]-(s:Source)<-[:HAS_SOURCE]-(m:Mapping)
WITH t, collect(m.name) as mappings
WHERE size(mappings) > 1
RETURN t.name, t.database, mappings, size(mappings) as usage_count
ORDER BY usage_count DESC
```

### Benefits for Large-Scale Migrations

1. **Enterprise-Wide Lineage**: See data flow across entire platform
2. **Impact Analysis**: Understand change impact across mappings
3. **Pattern Reuse**: Find and reuse similar transformation patterns
4. **Migration Planning**: Identify dependencies and migration order
5. **Knowledge Graph**: Build AI-enhanced knowledge base
6. **Query Performance**: Fast relationship queries vs. scanning files
7. **Scalability**: Handle millions of nodes and relationships

### Migration Path

#### Step 1: Add Graph Index Layer (Non-Breaking)

```python
class GraphIndex:
    """Graph index for canonical models."""
    
    def index_model(self, canonical_model: Dict[str, Any]):
        """Index canonical model in graph database."""
        # Create nodes
        mapping_node = self.create_mapping_node(canonical_model)
        
        # Create transformation nodes
        for trans in canonical_model.get("transformations", []):
            trans_node = self.create_transformation_node(trans)
            self.create_relationship(mapping_node, "HAS_TRANSFORMATION", trans_node)
        
        # Create connectors as relationships
        for conn in canonical_model.get("connectors", []):
            from_node = self.get_node(conn["from_transformation"])
            to_node = self.get_node(conn["to_transformation"])
            self.create_relationship(from_node, "CONNECTS_TO", to_node)
    
    def query_dependencies(self, mapping_name: str) -> List[str]:
        """Find all mappings that depend on this mapping."""
        # Graph query
        pass
```

#### Step 2: Dual Storage (JSON + Graph)

- Write to both JSON and graph
- Use graph for queries
- Use JSON for full model details
- Keep in sync

#### Step 3: Graph-First (Future)

- Store in graph database
- Export to JSON when needed
- Graph becomes source of truth

### Recommendation

**For Large-Scale Enterprise Migrations:**

✅ **Use Graph Database** (Neo4j recommended)

**Reasons**:
1. **Relationship Queries**: Natural fit for ETL dependencies
2. **Cross-Mapping Analysis**: Essential for enterprise scale
3. **Pattern Discovery**: Find reusable patterns across codebase
4. **Impact Analysis**: Critical for safe migrations
5. **Knowledge Graph**: Build AI-enhanced knowledge base
6. **Scalability**: Handle thousands of mappings efficiently

**Implementation Approach**:
1. **Phase 1-2**: Keep JSON, add graph index layer
2. **Phase 3**: Full graph database integration
3. **Hybrid**: JSON for details, graph for queries

### Example: Graph vs. JSON Query Performance

**JSON Approach** (Current):
```python
# Find all mappings using CUSTOMER_SRC
mappings = []
for file in version_store.list_all():
    model = version_store.load(file)
    for source in model.get("sources", []):
        if source.get("table") == "CUSTOMER_SRC":
            mappings.append(model["mapping_name"])
# Time: O(n) where n = number of mappings (slow for 1000s)
```

**Graph Approach** (Future):
```cypher
MATCH (m:Mapping)-[:HAS_SOURCE]->(s:Source)-[:READS_TABLE]->(t:Table {name: "CUSTOMER_SRC"})
RETURN m.name
// Time: O(log n) with indexes (fast even for millions)
```

---

## Summary

### Canonical Model

- **What**: Technology-neutral JSON representation of ETL logic
- **Structure**: Nested Python dictionaries (JSON)
- **Storage**: JSON files in `versions/` directory
- **Size**: 10 KB - 2 MB per mapping
- **Current**: Flat structure, one file per mapping

### Graph Database Recommendation

**For Large-Scale**: ✅ **Highly Recommended**

**Benefits**:
- Relationship queries (dependencies, lineage)
- Cross-mapping analysis
- Pattern discovery
- Impact analysis
- Scalability (millions of nodes)

**Implementation**:
- **Phase 1-2**: Add graph index layer (non-breaking)
- **Phase 3**: Full graph database integration
- **Hybrid**: JSON for details, graph for queries

**Technology**: Neo4j (recommended) - Open source Community Edition available

The graph database would be a **game-changer** for large-scale enterprise migrations, enabling enterprise-wide lineage, impact analysis, and pattern discovery that's impossible with flat JSON files.

