# Neo4j Graph-First Migration Plan

## Overview

This document outlines a detailed plan to migrate from JSON-based canonical model storage to a **graph-first architecture** using **Neo4j Community Edition** (open source). The migration will enable enterprise-scale capabilities including cross-mapping lineage, impact analysis, and pattern discovery.

---

## Current State Analysis

### Current Architecture (JSON-Based)

```
Informatica XML
    ↓
Parser → Python Dict
    ↓
Normalizer → Canonical Model (Python Dict)
    ↓
VersionStore → JSON File (versions/{name}.json)
    ↓
Code Generators / AI Agents (read from JSON)
```

**Characteristics**:
- ✅ Simple, no infrastructure needed
- ✅ Human-readable (JSON)
- ✅ Easy to version control
- ❌ No cross-mapping relationships
- ❌ Slow queries (O(n) file scanning)
- ❌ Doesn't scale to thousands of mappings
- ❌ No global lineage

### Target Architecture (Graph-First)

```
Informatica XML
    ↓
Parser → Python Dict
    ↓
Normalizer → Canonical Model (Python Dict)
    ↓
GraphStore → Neo4j Database
    ↓
Code Generators / AI Agents (read from Neo4j)
    ↓
JSON Export (on-demand for compatibility)
```

**Characteristics**:
- ✅ Fast relationship queries (O(log n))
- ✅ Cross-mapping lineage
- ✅ Pattern discovery
- ✅ Impact analysis
- ✅ Scales to millions of nodes
- ✅ Enterprise-wide knowledge graph

---

## Migration Strategy: Phased Approach

### Phase 1: Foundation (Current)
**Status**: ✅ Complete
- JSON-based storage
- VersionStore implementation
- Basic canonical model structure

### Phase 2: Hybrid (Graph Index Layer)
**Timeline**: Weeks 1-4
- Add Neo4j alongside JSON
- Build graph index for queries
- Keep JSON as source of truth
- Dual-write mechanism

### Phase 3: Graph-First (Target)
**Timeline**: Weeks 5-12
- Neo4j becomes primary storage
- JSON export for compatibility
- Graph-first queries
- Migration tools

---

## Phase 2: Hybrid Implementation (Weeks 1-4)

### Week 1: Neo4j Setup & Graph Model Design

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
```python
NODE_LABELS = {
    "Mapping",           # ETL mappings
    "Transformation",   # Transformations within mappings
    "Source",           # Source definitions
    "Target",           # Target definitions
    "Field",            # Fields/columns
    "Workflow",         # Workflow definitions
    "Session",          # Session definitions
    "Table",            # Database tables
    "Database",         # Database instances
    "Expression",       # Expression AST nodes
    "Pattern",          # Reusable patterns
    "Enhancement"       # AI enhancements
}
```

**Relationship Types**:
```python
RELATIONSHIP_TYPES = {
    # Structural relationships
    "HAS_TRANSFORMATION",
    "HAS_SOURCE",
    "HAS_TARGET",
    "HAS_FIELD",
    "CONTAINS",
    "EXECUTES",
    
    # Data flow relationships
    "CONNECTS_TO",
    "FLOWS_TO",
    "DERIVED_FROM",
    "READS_FROM",
    "WRITES_TO",
    
    # Table relationships
    "READS_TABLE",
    "WRITES_TABLE",
    "USES_TABLE",
    "FEEDS_INTO",
    
    # Dependency relationships
    "DEPENDS_ON",
    "SIMILAR_TO",
    "USES_PATTERN",
    "HAS_ENHANCEMENT"
}
```

**Node Properties Schema**:

```python
# Mapping Node
{
    "name": str,                    # "M_LOAD_CUSTOMER"
    "mapping_name": str,            # "M_LOAD_CUSTOMER"
    "scd_type": str,                # "SCD2", "SCD1", "NONE"
    "incremental_keys": List[str],  # ["LAST_UPDATED_DT"]
    "complexity": str,              # "LOW", "MEDIUM", "HIGH"
    "created_at": str,              # ISO timestamp
    "updated_at": str,              # ISO timestamp
    "version": int                  # Version number
}

# Transformation Node
{
    "name": str,                    # "EXP_DERIVE"
    "type": str,                    # "EXPRESSION", "LOOKUP", etc.
    "mapping": str,                 # "M_LOAD_CUSTOMER"
    "optimization_hint": str,       # "broadcast_join", etc.
    "properties": Dict              # Type-specific properties
}

# Source/Target Node
{
    "name": str,                    # "SQ_CUSTOMER"
    "table": str,                   # "CUSTOMER_SRC"
    "database": str,                # "source_db"
    "mapping": str                  # "M_LOAD_CUSTOMER"
}

# Table Node
{
    "name": str,                    # "CUSTOMER_SRC"
    "database": str,                # "source_db"
    "schema": str,                  # Optional schema name
    "platform": str                 # "Oracle", "SQL Server", etc.
}
```

### Week 2: Graph Store Implementation

#### 2.1 Create GraphStore Class

**File**: `src/graph/graph_store.py`

```python
"""Graph Store — Neo4j implementation for canonical models."""
from typing import Dict, Any, List, Optional
from neo4j import GraphDatabase
from utils.logger import get_logger
from utils.exceptions import ModernizationError

logger = get_logger(__name__)


class GraphStore:
    """Neo4j-based storage for canonical models."""
    
    def __init__(self, uri: str = "bolt://localhost:7687", 
                 user: str = "neo4j", 
                 password: str = "password"):
        """Initialize Neo4j connection.
        
        Args:
            uri: Neo4j connection URI
            user: Neo4j username
            password: Neo4j password
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self._verify_connectivity()
        self._create_indexes()
        logger.info(f"GraphStore initialized: {uri}")
    
    def _verify_connectivity(self):
        """Verify Neo4j connection."""
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("Neo4j connection verified")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
            raise ModernizationError(f"Neo4j connection failed: {str(e)}")
    
    def _create_indexes(self):
        """Create indexes for performance."""
        indexes = [
            "CREATE INDEX mapping_name IF NOT EXISTS FOR (m:Mapping) ON (m.name)",
            "CREATE INDEX transformation_name IF NOT EXISTS FOR (t:Transformation) ON (t.name)",
            "CREATE INDEX table_name IF NOT EXISTS FOR (t:Table) ON (t.name)",
            "CREATE INDEX source_name IF NOT EXISTS FOR (s:Source) ON (s.name)",
            "CREATE INDEX target_name IF NOT EXISTS FOR (t:Target) ON (t.name)"
        ]
        
        with self.driver.session() as session:
            for index_query in indexes:
                try:
                    session.run(index_query)
                except Exception as e:
                    logger.warning(f"Index creation warning: {str(e)}")
    
    def save_mapping(self, canonical_model: Dict[str, Any]) -> str:
        """Save canonical model to Neo4j.
        
        Args:
            canonical_model: Canonical model dictionary
            
        Returns:
            Mapping name
        """
        mapping_name = canonical_model.get("mapping_name", "unknown")
        logger.info(f"Saving mapping to graph: {mapping_name}")
        
        with self.driver.session() as session:
            # Use transaction for atomicity
            session.write_transaction(self._create_mapping_tx, canonical_model)
        
        logger.info(f"Successfully saved mapping to graph: {mapping_name}")
        return mapping_name
    
    @staticmethod
    def _create_mapping_tx(tx, model: Dict[str, Any]):
        """Transaction function to create mapping in graph."""
        mapping_name = model.get("mapping_name", "unknown")
        
        # 1. Create Mapping node
        mapping_props = {
            "name": mapping_name,
            "mapping_name": mapping_name,
            "scd_type": model.get("scd_type", "NONE"),
            "incremental_keys": model.get("incremental_keys", []),
            "complexity": model.get("_performance_metadata", {}).get("complexity", "UNKNOWN"),
            "created_at": model.get("_provenance", {}).get("enhanced_at", ""),
            "version": 1
        }
        
        tx.run("""
            MERGE (m:Mapping {name: $name})
            SET m += $props
        """, name=mapping_name, props=mapping_props)
        
        # 2. Create Source nodes
        for source in model.get("sources", []):
            source_name = source.get("name", "")
            table_name = source.get("table", "")
            database = source.get("database", "")
            
            # Create Source node
            tx.run("""
                MERGE (s:Source {name: $name, mapping: $mapping})
                SET s.table = $table, s.database = $database
                WITH s
                MERGE (m:Mapping {name: $mapping})
                MERGE (m)-[:HAS_SOURCE]->(s)
            """, name=source_name, mapping=mapping_name, 
                  table=table_name, database=database)
            
            # Create Table node and link
            if table_name:
                tx.run("""
                    MERGE (t:Table {name: $table, database: $database})
                    SET t.platform = $platform
                    WITH t
                    MERGE (s:Source {name: $source, mapping: $mapping})
                    MERGE (s)-[:READS_TABLE]->(t)
                """, table=table_name, database=database, platform="Unknown",
                      source=source_name, mapping=mapping_name)
            
            # Create Field nodes
            for field in source.get("fields", []):
                field_name = field.get("name", "")
                tx.run("""
                    MERGE (f:Field {name: $field, parent: $parent})
                    SET f.data_type = $data_type, f.nullable = $nullable
                    WITH f
                    MERGE (s:Source {name: $parent, mapping: $mapping})
                    MERGE (s)-[:HAS_FIELD]->(f)
                """, field=field_name, parent=source_name, mapping=mapping_name,
                      data_type=field.get("data_type"), 
                      nullable=field.get("nullable", True))
        
        # 3. Create Target nodes
        for target in model.get("targets", []):
            target_name = target.get("name", "")
            table_name = target.get("table", "")
            database = target.get("database", "")
            
            tx.run("""
                MERGE (t:Target {name: $name, mapping: $mapping})
                SET t.table = $table, t.database = $database
                WITH t
                MERGE (m:Mapping {name: $mapping})
                MERGE (m)-[:HAS_TARGET]->(t)
            """, name=target_name, mapping=mapping_name,
                  table=table_name, database=database)
            
            if table_name:
                tx.run("""
                    MERGE (tab:Table {name: $table, database: $database})
                    WITH tab
                    MERGE (t:Target {name: $target, mapping: $mapping})
                    MERGE (t)-[:WRITES_TABLE]->(tab)
                """, table=table_name, database=database,
                      target=target_name, mapping=mapping_name)
        
        # 4. Create Transformation nodes
        for trans in model.get("transformations", []):
            trans_name = trans.get("name", "")
            trans_type = trans.get("type", "")
            
            trans_props = {
                "name": trans_name,
                "type": trans_type,
                "mapping": mapping_name,
                "optimization_hint": trans.get("_optimization_hint"),
                "properties": {k: v for k, v in trans.items() 
                              if not k.startswith("_") or k == "_optimization_hint"}
            }
            
            tx.run("""
                MERGE (t:Transformation {name: $name, mapping: $mapping})
                SET t += $props
                WITH t
                MERGE (m:Mapping {name: $mapping})
                MERGE (m)-[:HAS_TRANSFORMATION]->(t)
            """, name=trans_name, mapping=mapping_name, props=trans_props)
        
        # 5. Create Connector relationships
        for conn in model.get("connectors", []):
            from_trans = conn.get("from_transformation", "")
            to_trans = conn.get("to_transformation", "")
            
            if from_trans and to_trans:
                tx.run("""
                    MATCH (t1:Transformation {name: $from, mapping: $mapping})
                    MATCH (t2:Transformation {name: $to, mapping: $mapping})
                    MERGE (t1)-[r:CONNECTS_TO {from_port: $from_port, to_port: $to_port}]->(t2)
                """, from=from_trans, to=to_trans, mapping=mapping_name,
                      from_port=conn.get("from_port", ""),
                      to_port=conn.get("to_port", ""))
        
        # 6. Create cross-mapping dependencies (if targets feed into other mappings)
        # This would be populated when multiple mappings are loaded
        pass
    
    def load_mapping(self, mapping_name: str) -> Optional[Dict[str, Any]]:
        """Load canonical model from Neo4j.
        
        Args:
            mapping_name: Name of mapping to load
            
        Returns:
            Canonical model dictionary or None
        """
        logger.info(f"Loading mapping from graph: {mapping_name}")
        
        with self.driver.session() as session:
            result = session.read_transaction(self._load_mapping_tx, mapping_name)
        
        if result:
            logger.info(f"Successfully loaded mapping from graph: {mapping_name}")
        else:
            logger.warning(f"Mapping not found in graph: {mapping_name}")
        
        return result
    
    @staticmethod
    def _load_mapping_tx(tx, mapping_name: str) -> Optional[Dict[str, Any]]:
        """Transaction function to load mapping from graph."""
        # Load mapping node
        mapping_result = tx.run("""
            MATCH (m:Mapping {name: $name})
            RETURN m
        """, name=mapping_name).single()
        
        if not mapping_result:
            return None
        
        mapping_node = mapping_result["m"]
        model = {
            "mapping_name": mapping_node.get("mapping_name", mapping_name),
            "scd_type": mapping_node.get("scd_type", "NONE"),
            "incremental_keys": mapping_node.get("incremental_keys", []),
            "sources": [],
            "targets": [],
            "transformations": [],
            "connectors": []
        }
        
        # Load sources
        sources_result = tx.run("""
            MATCH (m:Mapping {name: $name})-[:HAS_SOURCE]->(s:Source)
            RETURN s
        """, name=mapping_name)
        
        for record in sources_result:
            source = record["s"]
            model["sources"].append({
                "name": source.get("name"),
                "table": source.get("table"),
                "database": source.get("database"),
                "fields": []  # Load fields separately
            })
        
        # Load targets
        targets_result = tx.run("""
            MATCH (m:Mapping {name: $name})-[:HAS_TARGET]->(t:Target)
            RETURN t
        """, name=mapping_name)
        
        for record in targets_result:
            target = record["t"]
            model["targets"].append({
                "name": target.get("name"),
                "table": target.get("table"),
                "database": target.get("database"),
                "fields": []
            })
        
        # Load transformations
        trans_result = tx.run("""
            MATCH (m:Mapping {name: $name})-[:HAS_TRANSFORMATION]->(t:Transformation)
            RETURN t
        """, name=mapping_name)
        
        for record in trans_result:
            trans = record["t"]
            trans_dict = {
                "name": trans.get("name"),
                "type": trans.get("type"),
                "ports": []
            }
            # Merge properties
            props = trans.get("properties", {})
            trans_dict.update(props)
            model["transformations"].append(trans_dict)
        
        # Load connectors
        connectors_result = tx.run("""
            MATCH (t1:Transformation {mapping: $name})-[r:CONNECTS_TO]->(t2:Transformation {mapping: $name})
            RETURN t1.name as from, t2.name as to, r.from_port as from_port, r.to_port as to_port
        """, name=mapping_name)
        
        for record in connectors_result:
            model["connectors"].append({
                "from_transformation": record["from"],
                "to_transformation": record["to"],
                "from_port": record.get("from_port", ""),
                "to_port": record.get("to_port", "")
            })
        
        return model
    
    def query_dependencies(self, mapping_name: str) -> List[str]:
        """Find all mappings that depend on this mapping.
        
        Args:
            mapping_name: Mapping name
            
        Returns:
            List of dependent mapping names
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (m:Mapping {name: $name})<-[:DEPENDS_ON*]-(dependent:Mapping)
                RETURN DISTINCT dependent.name as name
            """, name=mapping_name)
            
            return [record["name"] for record in result]
    
    def query_mappings_using_table(self, table_name: str, database: str = None) -> List[str]:
        """Find all mappings using a specific table.
        
        Args:
            table_name: Table name
            database: Optional database name
            
        Returns:
            List of mapping names
        """
        with self.driver.session() as session:
            if database:
                result = session.run("""
                    MATCH (t:Table {name: $table, database: $database})<-[:READS_TABLE]-(s:Source)<-[:HAS_SOURCE]-(m:Mapping)
                    RETURN DISTINCT m.name as name
                """, table=table_name, database=database)
            else:
                result = session.run("""
                    MATCH (t:Table {name: $table})<-[:READS_TABLE]-(s:Source)<-[:HAS_SOURCE]-(m:Mapping)
                    RETURN DISTINCT m.name as name
                """, table=table_name)
            
            return [record["name"] for record in result]
    
    def close(self):
        """Close Neo4j connection."""
        self.driver.close()
        logger.info("GraphStore connection closed")
```

#### 2.2 Create Configuration

**File**: `src/config.py` (add to existing)

```python
# Neo4j Configuration
neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
neo4j_password: str = os.getenv("NEO4J_PASSWORD", "password")
enable_graph_store: bool = os.getenv("ENABLE_GRAPH_STORE", "false").lower() == "true"
```

### Week 3: Dual-Write Implementation

#### 3.1 Update VersionStore to Support Graph

**File**: `src/versioning/version_store.py` (modify)

```python
class VersionStore:
    def __init__(self, path: str = "./versions", graph_store: Optional[GraphStore] = None):
        """Initialize version store with optional graph store.
        
        Args:
            path: Directory path for JSON storage
            graph_store: Optional GraphStore instance for graph storage
        """
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.graph_store = graph_store
        logger.info(f"Version store initialized at: {self.path}")
        if self.graph_store:
            logger.info("Graph store enabled")
    
    def save(self, name: str, model: Dict[str, Any]) -> str:
        """Save model to both JSON and graph (if enabled).
        
        Args:
            name: Model name/identifier
            model: Model data to save
            
        Returns:
            Path to saved file
        """
        # Save to JSON (always)
        json_path = self._save_json(name, model)
        
        # Save to graph (if enabled)
        if self.graph_store:
            try:
                self.graph_store.save_mapping(model)
                logger.debug(f"Model saved to graph: {name}")
            except Exception as e:
                logger.warning(f"Failed to save to graph: {str(e)}")
        
        return json_path
    
    def _save_json(self, name: str, model: Dict[str, Any]) -> str:
        """Save model to JSON file."""
        safe_name = name.replace("/", "_").replace("\\", "_")
        file_path = self.path / f"{safe_name}.json"
        
        with open(file_path, "w") as f:
            json.dump(model, f, indent=2)
        
        return str(file_path)
    
    def load(self, name: str, use_graph: bool = False) -> Optional[Dict[str, Any]]:
        """Load model from JSON or graph.
        
        Args:
            name: Model name/identifier
            use_graph: Whether to load from graph (default: False for backward compatibility)
            
        Returns:
            Model data or None if not found
        """
        # Try graph first if enabled and requested
        if use_graph and self.graph_store:
            model = self.graph_store.load_mapping(name)
            if model:
                return model
        
        # Fall back to JSON
        return self._load_json(name)
    
    def _load_json(self, name: str) -> Optional[Dict[str, Any]]:
        """Load model from JSON file."""
        safe_name = name.replace("/", "_").replace("\\", "_")
        file_path = self.path / f"{safe_name}.json"
        
        if not file_path.exists():
            return None
        
        with open(file_path, "r") as f:
            return json.load(f)
```

#### 3.2 Create Sync Mechanism

**File**: `src/graph/graph_sync.py`

```python
"""Graph Sync — Keep graph and JSON in sync."""
from typing import Dict, Any, List
from graph.graph_store import GraphStore
from versioning.version_store import VersionStore
from utils.logger import get_logger

logger = get_logger(__name__)


class GraphSync:
    """Synchronizes JSON and graph storage."""
    
    def __init__(self, version_store: VersionStore, graph_store: GraphStore):
        """Initialize sync manager.
        
        Args:
            version_store: VersionStore instance
            graph_store: GraphStore instance
        """
        self.version_store = version_store
        self.graph_store = graph_store
        logger.info("GraphSync initialized")
    
    def sync_all(self) -> Dict[str, Any]:
        """Sync all JSON models to graph.
        
        Returns:
            Sync results
        """
        logger.info("Starting full sync from JSON to graph")
        
        results = {
            "synced": 0,
            "failed": 0,
            "errors": []
        }
        
        for model_name in self.version_store.list_all():
            try:
                model = self.version_store.load(model_name)
                if model:
                    self.graph_store.save_mapping(model)
                    results["synced"] += 1
                    logger.debug(f"Synced: {model_name}")
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"{model_name}: {str(e)}")
                logger.error(f"Failed to sync {model_name}: {str(e)}")
        
        logger.info(f"Sync completed: {results['synced']} synced, {results['failed']} failed")
        return results
    
    def verify_sync(self, mapping_name: str) -> bool:
        """Verify that JSON and graph are in sync for a mapping.
        
        Args:
            mapping_name: Mapping name to verify
            
        Returns:
            True if in sync, False otherwise
        """
        json_model = self.version_store.load(mapping_name)
        graph_model = self.graph_store.load_mapping(mapping_name)
        
        if json_model is None and graph_model is None:
            return True  # Both missing (consistent)
        
        if json_model is None or graph_model is None:
            return False  # One missing (out of sync)
        
        # Compare key fields
        return (
            json_model.get("mapping_name") == graph_model.get("mapping_name") and
            len(json_model.get("transformations", [])) == len(graph_model.get("transformations", []))
        )
```

### Week 4: Query Layer Implementation

#### 4.1 Create Graph Query Service

**File**: `src/graph/graph_queries.py`

```python
"""Graph Queries — High-level query interface."""
from typing import Dict, Any, List, Optional
from graph.graph_store import GraphStore
from utils.logger import get_logger

logger = get_logger(__name__)


class GraphQueries:
    """High-level query interface for graph database."""
    
    def __init__(self, graph_store: GraphStore):
        """Initialize graph queries.
        
        Args:
            graph_store: GraphStore instance
        """
        self.graph_store = graph_store
        logger.info("GraphQueries initialized")
    
    def find_dependent_mappings(self, mapping_name: str) -> List[Dict[str, Any]]:
        """Find all mappings that depend on this mapping.
        
        Args:
            mapping_name: Mapping name
            
        Returns:
            List of dependent mappings with depth
        """
        with self.graph_store.driver.session() as session:
            result = session.run("""
                MATCH path = (m:Mapping {name: $name})<-[:DEPENDS_ON*]-(dependent:Mapping)
                RETURN dependent.name as name, 
                       dependent.mapping_name as mapping_name,
                       length(path) as depth
                ORDER BY depth
            """, name=mapping_name)
            
            return [dict(record) for record in result]
    
    def find_mappings_using_table(self, table_name: str, database: Optional[str] = None) -> List[Dict[str, Any]]:
        """Find all mappings using a specific table.
        
        Args:
            table_name: Table name
            database: Optional database name
            
        Returns:
            List of mappings using the table
        """
        with self.graph_store.driver.session() as session:
            if database:
                result = session.run("""
                    MATCH (t:Table {name: $table, database: $database})<-[:READS_TABLE]-(s:Source)<-[:HAS_SOURCE]-(m:Mapping)
                    RETURN DISTINCT m.name as name, m.mapping_name as mapping_name, m.complexity as complexity
                """, table=table_name, database=database)
            else:
                result = session.run("""
                    MATCH (t:Table {name: $table})<-[:READS_TABLE]-(s:Source)<-[:HAS_SOURCE]-(m:Mapping)
                    RETURN DISTINCT m.name as name, m.mapping_name as mapping_name, m.complexity as complexity
                """, table=table_name)
            
            return [dict(record) for record in result]
    
    def trace_lineage(self, source_table: str, target_table: str) -> List[Dict[str, Any]]:
        """Trace data lineage from source to target across mappings.
        
        Args:
            source_table: Source table name
            target_table: Target table name
            
        Returns:
            Lineage path
        """
        with self.graph_store.driver.session() as session:
            result = session.run("""
                MATCH path = (src:Table {name: $source})
                          <-[:READS_TABLE]-(s:Source)
                          <-[:HAS_SOURCE]-(m1:Mapping)
                          -[:HAS_TARGET]->(t1:Target)
                          -[:WRITES_TABLE]->(intermediate:Table)
                          <-[:READS_TABLE]-(s2:Source)
                          <-[:HAS_SOURCE]-(m2:Mapping)
                          -[:HAS_TARGET]->(t2:Target)
                          -[:WRITES_TABLE]->(tgt:Table {name: $target})
                RETURN path, 
                       [n in nodes(path) WHERE n:Mapping | n.name] as mappings
                LIMIT 10
            """, source=source_table, target=target_table)
            
            return [dict(record) for record in result]
    
    def find_similar_transformations(self, transformation_type: str, 
                                     pattern: Optional[str] = None) -> List[Dict[str, Any]]:
        """Find similar transformations across mappings.
        
        Args:
            transformation_type: Transformation type
            pattern: Optional pattern to match
            
        Returns:
            List of similar transformations
        """
        with self.graph_store.driver.session() as session:
            if pattern:
                result = session.run("""
                    MATCH (t:Transformation {type: $type})
                    WHERE t.properties CONTAINS $pattern
                    RETURN t.name as name, t.mapping as mapping, t.properties as properties
                    LIMIT 50
                """, type=transformation_type, pattern=pattern)
            else:
                result = session.run("""
                    MATCH (t:Transformation {type: $type})
                    RETURN t.name as name, t.mapping as mapping, t.properties as properties
                    LIMIT 50
                """, type=transformation_type)
            
            return [dict(record) for record in result]
    
    def get_migration_order(self) -> List[Dict[str, Any]]:
        """Get recommended migration order based on dependencies.
        
        Returns:
            List of mappings in recommended migration order
        """
        with self.graph_store.driver.session() as session:
            result = session.run("""
                MATCH (m:Mapping)
                WHERE NOT (m)-[:DEPENDS_ON]->()
                RETURN m.name as name, m.mapping_name as mapping_name, m.complexity as complexity
                ORDER BY m.complexity
            """)
            
            return [dict(record) for record in result]
```

---

## Phase 3: Graph-First Implementation (Weeks 5-12)

### Week 5-6: Migration Tools

#### 5.1 Create Migration Script

**File**: `scripts/migrate_to_graph.py`

```python
#!/usr/bin/env python3
"""Migration script: JSON to Neo4j."""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.graph.graph_store import GraphStore
from src.versioning.version_store import VersionStore
from src.graph.graph_sync import GraphSync
from utils.logger import get_logger

logger = get_logger(__name__)


def migrate_all():
    """Migrate all JSON models to Neo4j."""
    # Initialize stores
    version_store = VersionStore()
    graph_store = GraphStore()
    sync = GraphSync(version_store, graph_store)
    
    # Sync all
    results = sync.sync_all()
    
    print(f"Migration completed:")
    print(f"  Synced: {results['synced']}")
    print(f"  Failed: {results['failed']}")
    if results['errors']:
        print(f"  Errors: {len(results['errors'])}")
        for error in results['errors'][:10]:
            print(f"    - {error}")
    
    graph_store.close()


if __name__ == "__main__":
    migrate_all()
```

#### 5.2 Create Validation Script

**File**: `scripts/validate_graph_migration.py`

```python
#!/usr/bin/env python3
"""Validate graph migration."""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.graph.graph_store import GraphStore
from src.versioning.version_store import VersionStore
from src.graph.graph_sync import GraphSync

def validate_all():
    """Validate all mappings are in sync."""
    version_store = VersionStore()
    graph_store = GraphStore()
    sync = GraphSync(version_store, graph_store)
    
    all_synced = True
    for model_name in version_store.list_all():
        if not sync.verify_sync(model_name):
            print(f"❌ Out of sync: {model_name}")
            all_synced = False
        else:
            print(f"✅ In sync: {model_name}")
    
    if all_synced:
        print("\n✅ All mappings are in sync!")
    else:
        print("\n❌ Some mappings are out of sync")
    
    graph_store.close()


if __name__ == "__main__":
    validate_all()
```

### Week 7-8: Graph-First Storage

#### 7.1 Update VersionStore to Graph-First

**Modify**: `src/versioning/version_store.py`

```python
class VersionStore:
    def __init__(self, path: str = "./versions", 
                 graph_store: Optional[GraphStore] = None,
                 graph_first: bool = False):
        """Initialize version store.
        
        Args:
            path: Directory path for JSON storage (fallback/export)
            graph_store: GraphStore instance (required if graph_first=True)
            graph_first: Whether to use graph as primary storage
        """
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.graph_store = graph_store
        self.graph_first = graph_first
        
        if graph_first and not graph_store:
            raise ValueError("graph_store required when graph_first=True")
        
        logger.info(f"Version store initialized: graph_first={graph_first}")
    
    def save(self, name: str, model: Dict[str, Any]) -> str:
        """Save model (graph-first or JSON-first).
        
        Args:
            name: Model name/identifier
            model: Model data to save
            
        Returns:
            Path to saved file or mapping name
        """
        if self.graph_first:
            # Save to graph first
            self.graph_store.save_mapping(model)
            # Export to JSON for compatibility
            return self._save_json(name, model)
        else:
            # Save to JSON first
            json_path = self._save_json(name, model)
            # Sync to graph if enabled
            if self.graph_store:
                try:
                    self.graph_store.save_mapping(model)
                except Exception as e:
                    logger.warning(f"Failed to save to graph: {str(e)}")
            return json_path
    
    def load(self, name: str) -> Optional[Dict[str, Any]]:
        """Load model (graph-first or JSON-first).
        
        Args:
            name: Model name/identifier
            
        Returns:
            Model data or None if not found
        """
        if self.graph_first:
            # Load from graph first
            model = self.graph_store.load_mapping(name)
            if model:
                return model
            # Fall back to JSON
            return self._load_json(name)
        else:
            # Load from JSON first
            return self._load_json(name)
```

### Week 9-10: API Integration

#### 9.1 Add Graph Query Endpoints

**Modify**: `src/api/routes.py`

```python
@router.get("/graph/mappings/using-table/{table_name}")
async def get_mappings_using_table(table_name: str, database: Optional[str] = None):
    """Get all mappings using a specific table.
    
    Args:
        table_name: Table name
        database: Optional database name
        
    Returns:
        List of mappings
    """
    if not graph_store:
        raise HTTPException(status_code=503, detail="Graph store not enabled")
    
    from src.graph.graph_queries import GraphQueries
    queries = GraphQueries(graph_store)
    mappings = queries.find_mappings_using_table(table_name, database)
    
    return {
        "success": True,
        "table": table_name,
        "database": database,
        "mappings": mappings,
        "count": len(mappings)
    }

@router.get("/graph/mappings/{mapping_name}/dependencies")
async def get_dependencies(mapping_name: str):
    """Get all mappings that depend on this mapping.
    
    Args:
        mapping_name: Mapping name
        
    Returns:
        List of dependent mappings
    """
    if not graph_store:
        raise HTTPException(status_code=503, detail="Graph store not enabled")
    
    from src.graph.graph_queries import GraphQueries
    queries = GraphQueries(graph_store)
    dependencies = queries.find_dependent_mappings(mapping_name)
    
    return {
        "success": True,
        "mapping": mapping_name,
        "dependencies": dependencies,
        "count": len(dependencies)
    }

@router.get("/graph/lineage/trace")
async def trace_lineage(source_table: str, target_table: str):
    """Trace data lineage from source to target.
    
    Args:
        source_table: Source table name
        target_table: Target table name
        
    Returns:
        Lineage path
    """
    if not graph_store:
        raise HTTPException(status_code=503, detail="Graph store not enabled")
    
    from src.graph.graph_queries import GraphQueries
    queries = GraphQueries(graph_store)
    lineage = queries.trace_lineage(source_table, target_table)
    
    return {
        "success": True,
        "source": source_table,
        "target": target_table,
        "lineage": lineage
    }

@router.get("/graph/migration/order")
async def get_migration_order():
    """Get recommended migration order.
    
    Returns:
        List of mappings in migration order
    """
    if not graph_store:
        raise HTTPException(status_code=503, detail="Graph store not enabled")
    
    from src.graph.graph_queries import GraphQueries
    queries = GraphQueries(graph_store)
    order = queries.get_migration_order()
    
    return {
        "success": True,
        "migration_order": order,
        "count": len(order)
    }
```

### Week 11-12: Testing & Documentation

#### 11.1 Integration Tests

**File**: `tests/integration/test_graph_store.py`

```python
"""Integration tests for GraphStore."""
import pytest
from src.graph.graph_store import GraphStore
from src.versioning.version_store import VersionStore

@pytest.fixture
def graph_store():
    """Create GraphStore instance."""
    store = GraphStore(uri="bolt://localhost:7687", 
                      user="neo4j", 
                      password="password")
    yield store
    store.close()

def test_save_and_load_mapping(graph_store):
    """Test saving and loading mapping."""
    model = {
        "mapping_name": "M_TEST",
        "sources": [{"name": "SQ_TEST", "table": "TEST_TABLE"}],
        "targets": [],
        "transformations": [],
        "connectors": []
    }
    
    # Save
    graph_store.save_mapping(model)
    
    # Load
    loaded = graph_store.load_mapping("M_TEST")
    assert loaded is not None
    assert loaded["mapping_name"] == "M_TEST"

def test_query_dependencies(graph_store):
    """Test dependency queries."""
    # Create dependent mappings
    # Query dependencies
    deps = graph_store.query_dependencies("M_TEST")
    assert isinstance(deps, list)
```

#### 11.2 Performance Tests

**File**: `tests/performance/test_graph_performance.py`

```python
"""Performance tests for graph queries."""
import time
from src.graph.graph_store import GraphStore
from src.graph.graph_queries import GraphQueries

def test_query_performance():
    """Test query performance vs JSON scanning."""
    graph_store = GraphStore()
    queries = GraphQueries(graph_store)
    
    # Time graph query
    start = time.time()
    mappings = queries.find_mappings_using_table("CUSTOMER_SRC")
    graph_time = time.time() - start
    
    # Time JSON scanning (if implemented)
    # ...
    
    print(f"Graph query time: {graph_time:.3f}s")
    assert graph_time < 1.0  # Should be fast
```

---

## Implementation Checklist

### Phase 2: Hybrid (Weeks 1-4)

- [ ] **Week 1**: Neo4j Setup
  - [ ] Install Neo4j Community Edition
  - [ ] Install Python driver (`neo4j`)
  - [ ] Design graph model schema
  - [ ] Create indexes

- [ ] **Week 2**: Graph Store Implementation
  - [ ] Create `GraphStore` class
  - [ ] Implement `save_mapping()`
  - [ ] Implement `load_mapping()`
  - [ ] Implement query methods
  - [ ] Unit tests

- [ ] **Week 3**: Dual-Write
  - [ ] Update `VersionStore` for dual-write
  - [ ] Create `GraphSync` class
  - [ ] Implement sync mechanism
  - [ ] Integration tests

- [ ] **Week 4**: Query Layer
  - [ ] Create `GraphQueries` class
  - [ ] Implement high-level queries
  - [ ] Add query endpoints to API
  - [ ] Documentation

### Phase 3: Graph-First (Weeks 5-12)

- [ ] **Week 5-6**: Migration Tools
  - [ ] Create migration script
  - [ ] Create validation script
  - [ ] Test migration process
  - [ ] Rollback procedures

- [ ] **Week 7-8**: Graph-First Storage
  - [ ] Update `VersionStore` for graph-first
  - [ ] Implement JSON export
  - [ ] Update all code generators
  - [ ] Update AI agents

- [ ] **Week 9-10**: API Integration
  - [ ] Add graph query endpoints
  - [ ] Update existing endpoints
  - [ ] Add graph visualization endpoints
  - [ ] API documentation

- [ ] **Week 11-12**: Testing & Documentation
  - [ ] Integration tests
  - [ ] Performance tests
  - [ ] Load testing
  - [ ] User documentation
  - [ ] Migration guide

---

## Configuration

### Environment Variables

```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
ENABLE_GRAPH_STORE=true
GRAPH_FIRST=false  # Set to true in Phase 3
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

## Migration Risks & Mitigation

### Risks

1. **Data Loss**: Graph migration might lose data
   - **Mitigation**: Keep JSON as backup, validate after migration

2. **Performance**: Graph queries might be slow initially
   - **Mitigation**: Create proper indexes, optimize queries

3. **Compatibility**: Existing code expects JSON
   - **Mitigation**: Provide JSON export, gradual migration

4. **Infrastructure**: Neo4j requires separate infrastructure
   - **Mitigation**: Docker deployment, cloud options

### Rollback Plan

1. **Phase 2**: Can disable graph, fall back to JSON-only
2. **Phase 3**: Export all models to JSON, disable graph-first mode
3. **Data Recovery**: JSON files remain as backup

---

## Success Metrics

### Performance Metrics

- **Query Time**: Graph queries < 100ms for 1000 mappings
- **Load Time**: Graph load < 50ms per mapping
- **Sync Time**: Full sync < 5 minutes for 1000 mappings

### Functional Metrics

- **Query Coverage**: 100% of relationship queries via graph
- **Data Integrity**: 100% sync between JSON and graph
- **API Response**: All graph endpoints functional

---

## Next Steps

1. **Review Plan**: Validate approach with team
2. **Set Up Neo4j**: Install and configure Neo4j
3. **Start Phase 2**: Begin hybrid implementation
4. **Test Thoroughly**: Validate before Phase 3
5. **Migrate Gradually**: Phase 3 migration with validation

---

This plan provides a clear path from JSON-based storage to a graph-first architecture using Neo4j Community Edition, enabling enterprise-scale capabilities while maintaining backward compatibility.

