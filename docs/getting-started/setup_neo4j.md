# Neo4j Setup Guide

This guide helps you set up Neo4j for the Informatica Modernization Accelerator.

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Run the setup script
./scripts/setup_neo4j.sh
```

The script will:
- Check Docker installation
- Create Neo4j container
- Wait for Neo4j to be ready
- Provide connection details

### Option 2: Manual Docker Setup

```bash
docker run -d \
    --name neo4j-modernize \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/password \
    -e NEO4J_PLUGINS='["apoc"]' \
    -v neo4j-modernize-data:/data \
    -v neo4j-modernize-logs:/logs \
    neo4j:5.15-community
```

### Option 3: Local Installation

1. Download Neo4j Community Edition from https://neo4j.com/download/
2. Extract and run:
   ```bash
   ./bin/neo4j start
   ```

## Configuration

### 1. Update Environment Variables

Create or update `.env` file:

```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Graph Store Configuration
ENABLE_GRAPH_STORE=true
GRAPH_FIRST=true
```

Or copy from example:
```bash
cp .env.example .env
# Edit .env with your Neo4j credentials
```

### 2. Verify Configuration

```bash
# Test connection
python -c "from graph.graph_store import GraphStore; GraphStore()"
```

### 3. Run Tests

```bash
# Run GraphStore tests
python scripts/test_graph_store.py
```

## Access Neo4j

### Neo4j Browser

Open in your browser: http://localhost:7474

- **Username**: neo4j
- **Password**: (your password from .env)

### Useful Cypher Queries

```cypher
// List all mappings
MATCH (m:Mapping)
RETURN m.name, m.mapping_name, m.complexity
ORDER BY m.name

// Find mappings using a table
MATCH (t:Table {name: "CUSTOMER_SRC"})<-[:READS_TABLE]-(s:Source)<-[:HAS_SOURCE]-(m:Mapping)
RETURN m.name, m.mapping_name

// Count nodes by type
MATCH (n)
RETURN labels(n)[0] as type, count(n) as count
ORDER BY count DESC
```

## Troubleshooting

### Connection Issues

**Error**: `Neo4j connection failed`

**Solutions**:
1. Check if Neo4j is running:
   ```bash
   docker ps | grep neo4j
   # or
   ./bin/neo4j status
   ```

2. Check Neo4j logs:
   ```bash
   docker logs neo4j-modernize
   ```

3. Verify credentials in `.env` file

4. Test connection manually:
   ```bash
   docker exec neo4j-modernize cypher-shell -u neo4j -p password "RETURN 1"
   ```

### Port Conflicts

If ports 7474 or 7687 are already in use:

```bash
# Use different ports
docker run -d \
    --name neo4j-modernize \
    -p 7475:7474 -p 7688:7687 \
    ...
```

Update `.env`:
```bash
NEO4J_URI=bolt://localhost:7688
```

### Memory Issues

If Neo4j runs out of memory:

```bash
# Increase memory limits
docker run -d \
    --name neo4j-modernize \
    -e NEO4J_dbms_memory_heap_initial__size=1G \
    -e NEO4J_dbms_memory_heap_max__size=4G \
    ...
```

## Next Steps

After Neo4j is set up:

1. ✅ Run connection test: `python scripts/test_graph_store.py`
2. ✅ Test Part 1 flow: Parse a mapping and verify it's saved to graph
3. ✅ Test Part 2 flow: Generate code and verify it loads from graph
4. ✅ Explore graph in Neo4j Browser

## Useful Commands

```bash
# Start Neo4j
docker start neo4j-modernize

# Stop Neo4j
docker stop neo4j-modernize

# View logs
docker logs neo4j-modernize

# Remove container (data preserved in volume)
docker stop neo4j-modernize
docker rm neo4j-modernize

# Remove everything (including data)
docker stop neo4j-modernize
docker rm neo4j-modernize
docker volume rm neo4j-modernize-data neo4j-modernize-logs
```

## Data Persistence

Neo4j data is stored in Docker volumes:
- `neo4j-modernize-data`: Database files
- `neo4j-modernize-logs`: Log files

Data persists even if you remove the container. To remove data:
```bash
docker volume rm neo4j-modernize-data
```

