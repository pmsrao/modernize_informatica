#!/bin/bash
# Neo4j Setup Script for Informatica Modernization Accelerator
# This script helps set up Neo4j using Docker

set -e

echo "=========================================="
echo "Neo4j Setup for Modernization Accelerator"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✅ Docker is installed"
echo ""

# Check if Neo4j container already exists
if docker ps -a --format '{{.Names}}' | grep -q "^neo4j-modernize$"; then
    echo "⚠️  Neo4j container 'neo4j-modernize' already exists"
    read -p "Do you want to remove it and create a new one? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Stopping and removing existing container..."
        docker stop neo4j-modernize 2>/dev/null || true
        docker rm neo4j-modernize 2>/dev/null || true
    else
        echo "Starting existing container..."
        docker start neo4j-modernize
        echo ""
        echo "✅ Neo4j is running"
        echo "   Browser: http://localhost:7474"
        echo "   Bolt: bolt://localhost:7687"
        exit 0
    fi
fi

# Default values
NEO4J_PASSWORD="${NEO4J_PASSWORD:-password}"
NEO4J_VERSION="${NEO4J_VERSION:-5.15-community}"

echo "Configuration:"
echo "  Neo4j Version: $NEO4J_VERSION"
echo "  Password: $NEO4J_PASSWORD"
echo ""

read -p "Press Enter to continue or Ctrl+C to cancel..."

echo ""
echo "Starting Neo4j container..."
docker run -d \
    --name neo4j-modernize \
    -p 7474:7474 \
    -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/$NEO4J_PASSWORD \
    -e NEO4J_PLUGINS='["apoc"]' \
    -e NEO4J_dbms_memory_heap_initial__size=512m \
    -e NEO4J_dbms_memory_heap_max__size=2G \
    -v neo4j-modernize-data:/data \
    -v neo4j-modernize-logs:/logs \
    neo4j:$NEO4J_VERSION

echo ""
echo "⏳ Waiting for Neo4j to start (this may take 30-60 seconds)..."
sleep 5

# Wait for Neo4j to be ready
MAX_WAIT=60
WAIT_COUNT=0
while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    if docker exec neo4j-modernize cypher-shell -u neo4j -p $NEO4J_PASSWORD "RETURN 1" > /dev/null 2>&1; then
        echo "✅ Neo4j is ready!"
        break
    fi
    echo -n "."
    sleep 2
    WAIT_COUNT=$((WAIT_COUNT + 2))
done

if [ $WAIT_COUNT -ge $MAX_WAIT ]; then
    echo ""
    echo "❌ Neo4j did not start within $MAX_WAIT seconds"
    echo "   Check logs: docker logs neo4j-modernize"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Neo4j Setup Complete!"
echo "=========================================="
echo ""
echo "Access Neo4j:"
echo "  Browser: http://localhost:7474"
echo "  Username: neo4j"
echo "  Password: $NEO4J_PASSWORD"
echo "  Bolt URI: bolt://localhost:7687"
echo ""
echo "Next Steps:"
echo "  1. Update .env file with Neo4j credentials"
echo "  2. Run: python scripts/test_graph_store.py"
echo "  3. Test connection: python -c \"from src.graph.graph_store import GraphStore; GraphStore()\""
echo ""
echo "Useful Commands:"
echo "  Stop: docker stop neo4j-modernize"
echo "  Start: docker start neo4j-modernize"
echo "  Logs: docker logs neo4j-modernize"
echo "  Remove: docker stop neo4j-modernize && docker rm neo4j-modernize"
echo ""

