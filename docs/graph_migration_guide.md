# Graph Migration Guide

## Overview

This guide explains how to migrate from JSON-based storage to a **graph-first architecture** using Neo4j Community Edition.

## Prerequisites

1. **Neo4j Community Edition** installed and running
2. **Python dependencies** installed: `pip install -r requirements.txt`
3. **Environment variables** configured (see Configuration section)

## Installation

### Option 1: Docker (Recommended)

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

Access Neo4j Browser at: http://localhost:7474

### Option 2: Local Installation

1. Download Neo4j Community Edition from https://neo4j.com/download/
2. Extract and run:
   ```bash
   ./bin/neo4j start
   ```

### Option 3: Neo4j Desktop

1. Download Neo4j Desktop
2. Create new project
3. Install Community Edition
4. Enable APOC plugin

## Configuration

### Environment Variables

Create or update `.env` file:

```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Enable graph store (Phase 2: Hybrid mode)
ENABLE_GRAPH_STORE=true

# Graph-first mode (Phase 3: Graph becomes primary)
GRAPH_FIRST=false  # Set to true after migration
```

### Verify Configuration

```bash
# Check Neo4j connection
python -c "from src.graph.graph_store import GraphStore; GraphStore()"
```

## Migration Steps

### Phase 2: Hybrid Mode (Dual-Write)

**Purpose**: Keep JSON as source of truth, sync to graph for queries.

1. **Enable Graph Store**:
   ```bash
   export ENABLE_GRAPH_STORE=true
   ```

2. **Migrate Existing Data**:
   ```bash
   python scripts/migrate_to_graph.py
   ```

3. **Validate Migration**:
   ```bash
   python scripts/validate_graph_migration.py
   ```

4. **Verify Sync**:
   - All mappings should be in sync
   - Check for any errors

### Phase 3: Graph-First Mode

**Purpose**: Graph becomes primary storage, JSON is export-only.

1. **Complete Phase 2 Migration**:
   - Ensure all mappings are synced
   - Validate no errors

2. **Enable Graph-First Mode**:
   ```bash
   export GRAPH_FIRST=true
   ```

3. **Restart API**:
   ```bash
   ./start_api.sh
   ```

4. **Verify Graph-First**:
   - New mappings saved to graph first
   - JSON export still available
   - Queries use graph

## Usage

### API Endpoints

#### 1. Find Mappings Using a Table

```bash
curl "http://localhost:8000/api/v1/graph/mappings/using-table/CUSTOMER_SRC?database=source_db"
```

#### 2. Get Dependencies

```bash
curl "http://localhost:8000/api/v1/graph/mappings/M_LOAD_CUSTOMER/dependencies"
```

#### 3. Trace Lineage

```bash
curl "http://localhost:8000/api/v1/graph/lineage/trace?source_table=CUSTOMER_SRC&target_table=CUSTOMER_TGT"
```

#### 4. Get Migration Order

```bash
curl "http://localhost:8000/api/v1/graph/migration/order"
```

#### 5. Get Statistics

```bash
curl "http://localhost:8000/api/v1/graph/statistics"
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

# Query mappings using a table
mappings = queries.find_mappings_using_table("CUSTOMER_SRC")

# Get dependencies
deps = queries.find_dependent_mappings("M_LOAD_CUSTOMER")

# Trace lineage
lineage = queries.trace_lineage("CUSTOMER_SRC", "CUSTOMER_TGT")

# Get migration order
order = queries.get_migration_order()
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

#### Transformation Statistics

```cypher
MATCH (t:Transformation)
RETURN t.type, count(t) as count
ORDER BY count DESC
```

## Troubleshooting

### Connection Issues

**Error**: `Neo4j connection failed`

**Solutions**:
1. Verify Neo4j is running: `docker ps` or `./bin/neo4j status`
2. Check connection URI: `bolt://localhost:7687`
3. Verify credentials in `.env`
4. Check firewall/network settings

### Migration Errors

**Error**: `Failed to sync mapping`

**Solutions**:
1. Check mapping JSON is valid
2. Verify Neo4j is accessible
3. Check logs for detailed error
4. Re-run migration for failed mappings

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

## Rollback

### From Graph-First to Hybrid

1. Set `GRAPH_FIRST=false` in `.env`
2. Restart API
3. JSON becomes primary again

### From Hybrid to JSON-Only

1. Set `ENABLE_GRAPH_STORE=false` in `.env`
2. Restart API
3. Graph store disabled, JSON-only mode

### Data Recovery

JSON files remain as backup:
- Location: `./versions/*.json`
- Can be re-imported anytime
- Graph can be rebuilt from JSON

## Best Practices

1. **Backup Regularly**: Export JSON files regularly
2. **Monitor Sync**: Run validation script periodically
3. **Index Optimization**: Ensure indexes are created
4. **Query Optimization**: Use specific filters in queries
5. **Error Handling**: Monitor logs for sync errors

## Next Steps

- **Phase 2 Complete**: Hybrid mode with dual-write
- **Phase 3 Complete**: Graph-first mode
- **Future**: AI-enhanced knowledge graph, pattern discovery

## Support

For issues or questions:
1. Check logs: `tail -f logs/app.log`
2. Validate migration: `python scripts/validate_graph_migration.py`
3. Check Neo4j Browser: http://localhost:7474

