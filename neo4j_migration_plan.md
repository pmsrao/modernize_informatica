# Neo4j Graph-First Implementation Plan

## Overview

This document outlines the implementation plan for a **graph-first architecture** using **Neo4j Community Edition** (open source) as the primary storage for canonical models. Since we're in the early stages of building the accelerator, we'll implement graph-first from the start rather than migrating from JSON.

---

## Architecture Vision

### Two-Part Architecture

**PART 1: Source to Canonical Form**
```
Informatica XML
    ↓
Parser → Python Dict
    ↓
Normalizer → Canonical Model (Python Dict)
    ↓
AI Enhancement Agents → Enhanced Canonical Model
    ↓
Graph Store (Neo4j) ← PRIMARY STORAGE
```

**PART 2: Canonical Form to Target Stack**
```
Graph Store (Neo4j) → Load Enhanced Model
    ↓
Translators → Translate Expressions
    ↓
Code Generators → Generate Target Code (Databricks today, extensible tomorrow)
    ↓
AI Review Agents → Review & Fix Code
    ↓
Final Code → Target Platform
```

### Graph Store as Central Hub

The **Graph Store (Neo4j)** serves as the **central repository** for canonical models, positioned between:
- **Part 1**: Where canonical models are created and enhanced
- **Part 2**: Where canonical models are consumed for code generation

**Benefits**:
- ✅ Single source of truth for canonical models
- ✅ Cross-mapping lineage and relationships
- ✅ Impact analysis across mappings
- ✅ Pattern discovery and reuse
- ✅ Extensible to future target platforms

---

## Implementation Strategy: Graph-First from Start

### Phase 1: Foundation Setup (Week 1-2)

**Goal**: Set up Neo4j and basic graph infrastructure

#### 1.1 Neo4j Installation

**Option A: Docker (Recommended for Development)**
```bash
docker run \
    --name neo4j-modernize \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/password \
    -e NEO4J_PLUGINS='["apoc"]' \
    -v neo4j-data:/data \
    -v neo4j-logs:/logs \
    neo4j:5.15-community
```

**Option B: Local Installation**
```bash
# Download Neo4j Community Edition
wget https://neo4j.com/artifact.php?name=neo4j-community-5.15.0-unix.tar.gz
tar -xzf neo4j-community-5.15.0-unix.tar.gz
cd neo4j-community-5.15.0
./bin/neo4j start
```

**Option C: Neo4j Desktop (Development)**
- Download Neo4j Desktop
- Create new project
- Install Community Edition
- Enable APOC plugin

#### 1.2 Python Driver Setup

```bash
pip install neo4j
```

#### 1.3 Graph Model Schema Design

**Node Labels**:
- `Mapping`: ETL mappings
- `Transformation`: Transformations within mappings
- `Source`: Source definitions
- `Target`: Target definitions
- `Field`: Fields/columns
- `Workflow`: Workflow definitions
- `Session`: Session definitions
- `Table`: Database tables
- `Database`: Database instances
- `Expression`: Expression AST nodes
- `Pattern`: Reusable patterns
- `Enhancement`: AI enhancements

**Relationship Types**:
- `HAS_TRANSFORMATION`, `HAS_SOURCE`, `HAS_TARGET`, `HAS_FIELD`
- `CONNECTS_TO`, `FLOWS_TO`, `DERIVED_FROM`, `READS_FROM`, `WRITES_TO`
- `READS_TABLE`, `WRITES_TABLE`, `USES_TABLE`, `FEEDS_INTO`
- `DEPENDS_ON`, `SIMILAR_TO`, `USES_PATTERN`, `HAS_ENHANCEMENT`

### Phase 2: Graph Store Implementation (Week 2-3)

**Goal**: Implement GraphStore class and integrate into Part 1 flow

#### 2.1 Create GraphStore Class

**File**: `src/graph/graph_store.py` ✅ (Already implemented)

**Key Methods**:
- `save_mapping()`: Save canonical model to Neo4j
- `load_mapping()`: Load canonical model from Neo4j
- `query_dependencies()`: Find dependent mappings
- `query_mappings_using_table()`: Find mappings using a table
- `list_all_mappings()`: List all mappings

#### 2.2 Integrate into Part 1 Flow

**Update**: `src/api/routes.py` (Already done)

After AI Enhancement Agents enhance the canonical model:
```python
# Save enhanced model to graph (primary storage)
graph_store.save_mapping(enhanced_model)

# Optional: Export to JSON for backup/compatibility
version_store.save(name, enhanced_model)
```

#### 2.3 Configuration

**File**: `src/config.py` ✅ (Already implemented)

```python
# Neo4j Configuration
neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
neo4j_password: str = os.getenv("NEO4J_PASSWORD", "password")
enable_graph_store: bool = os.getenv("ENABLE_GRAPH_STORE", "true").lower() == "true"
graph_first: bool = os.getenv("GRAPH_FIRST", "true").lower() == "true"
```

**Note**: `graph_first=true` by default since we're starting fresh.

### Phase 3: Part 2 Integration (Week 3-4)

**Goal**: Update Part 2 components to read from graph

#### 3.1 Update Code Generators

**File**: `src/generators/*.py`

Code generators already use `VersionStore`, which now supports graph-first mode. No changes needed! ✅

When `graph_first=True`:
- `version_store.load()` reads from Neo4j
- Falls back to JSON if graph unavailable

#### 3.2 Update AI Agents

**File**: `ai_agents/*.py`

AI agents also use `VersionStore`, so they automatically read from graph. ✅

#### 3.3 Graph Query Endpoints

**File**: `src/api/routes.py` ✅ (Already implemented)

Endpoints for:
- Finding mappings using a table
- Dependency analysis
- Lineage tracing
- Migration order
- Statistics

### Phase 4: JSON Export (Optional, Week 4)

**Goal**: Add JSON export capability for backup/compatibility

#### 4.1 Export on Demand

**File**: `src/graph/graph_store.py`

```python
def export_to_json(self, mapping_name: str) -> Dict[str, Any]:
    """Export canonical model from graph to JSON format."""
    model = self.load_mapping(mapping_name)
    if model:
        # Save to JSON via VersionStore
        version_store.save(mapping_name, model)
    return model
```

#### 4.2 Batch Export

**File**: `scripts/export_graph_to_json.py`

```python
#!/usr/bin/env python3
"""Export all graph models to JSON."""
from src.graph.graph_store import GraphStore
from src.versioning.version_store import VersionStore

graph_store = GraphStore()
version_store = VersionStore()

for mapping_name in graph_store.list_all_mappings():
    model = graph_store.load_mapping(mapping_name)
    if model:
        version_store.save(mapping_name, model)
        print(f"Exported: {mapping_name}")
```

---

## Configuration

### Environment Variables

```bash
# Neo4j Configuration (Required)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Graph Store Configuration
ENABLE_GRAPH_STORE=true
GRAPH_FIRST=true  # Graph is primary storage
```

### Docker Compose (Optional)

**File**: `deployment/docker-compose-neo4j.yaml`

```yaml
version: '3.8'
services:
  neo4j:
    image: neo4j:5.15-community
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    environment:
      - NEO4J_AUTH=neo4j/password
      - NEO4J_PLUGINS=["apoc"]
    volumes:
      - neo4j-data:/data
      - neo4j-logs:/logs
    healthcheck:
      test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "password", "RETURN 1"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  neo4j-data:
  neo4j-logs:
```

---

## Usage

### API Endpoints

#### 1. Save Canonical Model (Part 1)

```bash
# After parsing and enhancement, model is automatically saved to graph
POST /api/v1/parse/mapping
# Enhanced model saved to Neo4j automatically
```

#### 2. Load Canonical Model (Part 2)

```bash
# Code generators automatically load from graph
POST /api/v1/generate/pyspark
# Model loaded from Neo4j automatically
```

#### 3. Graph Queries

```bash
# Find mappings using a table
GET /api/v1/graph/mappings/using-table/CUSTOMER_SRC

# Get dependencies
GET /api/v1/graph/mappings/M_LOAD_CUSTOMER/dependencies

# Trace lineage
GET /api/v1/graph/lineage/trace?source_table=CUSTOMER_SRC&target_table=CUSTOMER_TGT

# Get migration order
GET /api/v1/graph/migration/order

# Get statistics
GET /api/v1/graph/statistics
```

### Python API

```python
from src.graph.graph_store import GraphStore
from src.graph.graph_queries import GraphQueries

# Initialize
graph_store = GraphStore(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password"
)
queries = GraphQueries(graph_store)

# Save model (Part 1)
graph_store.save_mapping(canonical_model)

# Load model (Part 2)
model = graph_store.load_mapping("M_LOAD_CUSTOMER")

# Query mappings
mappings = queries.find_mappings_using_table("CUSTOMER_SRC")
deps = queries.find_dependent_mappings("M_LOAD_CUSTOMER")
lineage = queries.trace_lineage("CUSTOMER_SRC", "CUSTOMER_TGT")
```

### Cypher Queries (Neo4j Browser)

Access Neo4j Browser at http://localhost:7474

#### Find All Mappings

```cypher
MATCH (m:Mapping)
RETURN m.name, m.mapping_name, m.complexity
ORDER BY m.name
```

#### Find Mappings Using Table

```cypher
MATCH (t:Table {name: "CUSTOMER_SRC"})<-[:READS_TABLE]-(s:Source)<-[:HAS_SOURCE]-(m:Mapping)
RETURN m.name, m.mapping_name
```

#### Dependency Chain

```cypher
MATCH path = (m1:Mapping {name: "M_LOAD_CUSTOMER"})<-[:DEPENDS_ON*]-(m2:Mapping)
RETURN m2.name, length(path) as depth
ORDER BY depth
```

---

## Benefits of Graph-First Approach

### 1. **Single Source of Truth**
- Canonical models stored in Neo4j
- No sync issues between JSON and graph
- Consistent data across all components

### 2. **Cross-Mapping Capabilities**
- Find all mappings using a table
- Trace dependencies across mappings
- Impact analysis for changes

### 3. **Extensibility**
- Easy to add new target platforms
- Canonical model remains platform-agnostic
- Graph queries work for any target

### 4. **Performance**
- Fast relationship queries (O(log n))
- Efficient traversal of dependencies
- Scales to thousands of mappings

### 5. **Knowledge Graph**
- Build enterprise-wide lineage
- Pattern discovery across mappings
- AI-enhanced insights

---

## Implementation Checklist

### Phase 1: Foundation Setup
- [x] Neo4j installation guide
- [x] Python driver setup
- [x] Graph model schema design
- [x] Configuration setup

### Phase 2: Graph Store Implementation
- [x] GraphStore class implementation
- [x] Save/load methods
- [x] Query methods
- [x] Integration into Part 1 flow
- [x] API endpoints

### Phase 3: Part 2 Integration
- [x] Code generators read from graph (via VersionStore)
- [x] AI agents read from graph (via VersionStore)
- [x] Graph query endpoints
- [x] Testing

### Phase 4: JSON Export (Optional)
- [ ] Export on demand
- [ ] Batch export script
- [ ] Documentation

---

## Troubleshooting

### Connection Issues

**Error**: `Neo4j connection failed`

**Solutions**:
1. Verify Neo4j is running: `docker ps` or `./bin/neo4j status`
2. Check connection URI: `bolt://localhost:7687`
3. Verify credentials in `.env`
4. Check firewall/network settings

### Performance Issues

**Slow Queries**:

1. **Create Indexes** (automatic on startup):
   ```cypher
   CREATE INDEX mapping_name IF NOT EXISTS FOR (m:Mapping) ON (m.name)
   ```

2. **Check Query Plans**:
   ```cypher
   EXPLAIN MATCH (m:Mapping) RETURN m
   ```

3. **Optimize Queries**: Use specific filters, limit results

---

## Next Steps

1. **Set Up Neo4j**: Install and configure Neo4j
2. **Configure Environment**: Set `ENABLE_GRAPH_STORE=true` and `GRAPH_FIRST=true`
3. **Test Integration**: Verify Part 1 saves to graph, Part 2 reads from graph
4. **Add Graph Queries**: Use graph query endpoints for analysis
5. **Extend to New Targets**: Add new target platform generators (they'll automatically use graph)

---

## Summary

Since we're in the **early stages** of building the accelerator, we're implementing **graph-first from the start**:

- ✅ **No migration needed**: We're not migrating from JSON, we're starting with graph
- ✅ **Graph is primary**: Neo4j is the main storage for canonical models
- ✅ **JSON is optional**: JSON export available for backup/compatibility
- ✅ **Two-part architecture**: Graph sits in the middle, connecting Part 1 (source → canonical) and Part 2 (canonical → target)
- ✅ **Extensible**: Easy to add new target platforms without changing storage

This approach is **simpler** and **cleaner** than migrating from JSON, and sets us up for success as the accelerator grows.
