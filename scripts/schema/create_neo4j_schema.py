"""Neo4j Schema Creation Script

This script drops all existing nodes and relationships in Neo4j and creates
a fresh schema with platform-agnostic terminology.

Usage:
    python scripts/schema/create_neo4j_schema.py

Environment Variables:
    NEO4J_URI: Neo4j connection URI (default: bolt://localhost:7687)
    NEO4J_USER: Neo4j username (default: neo4j)
    NEO4J_PASSWORD: Neo4j password (default: password)
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

try:
    from neo4j import GraphDatabase
except ImportError:
    print("ERROR: Neo4j driver not installed. Install with: pip install neo4j")
    sys.exit(1)

from utils.logger import get_logger

logger = get_logger(__name__)


def create_schema(uri: str, user: str, password: str):
    """Create Neo4j schema with platform-agnostic terminology.
    
    Args:
        uri: Neo4j connection URI
        user: Neo4j username
        password: Neo4j password
    """
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    try:
        # Verify connectivity
        with driver.session() as session:
            session.run("RETURN 1")
        logger.info("Neo4j connection verified")
        
        # Drop all existing nodes and relationships
        logger.info("Dropping all existing nodes and relationships...")
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as count")
            count = result.single()["count"]
            logger.info(f"Found {count} existing nodes")
            
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("All nodes and relationships deleted")
        
        # Create indexes with new generic labels
        logger.info("Creating indexes with generic labels...")
        indexes = [
            # Core component indexes
            "CREATE INDEX transformation_name IF NOT EXISTS FOR (t:Transformation) ON (t.name)",
            "CREATE INDEX reusable_transformation_name IF NOT EXISTS FOR (r:ReusableTransformation) ON (r.name)",
            "CREATE INDEX pipeline_name IF NOT EXISTS FOR (p:Pipeline) ON (p.name)",
            "CREATE INDEX task_name IF NOT EXISTS FOR (t:Task) ON (t.name)",
            "CREATE INDEX sub_pipeline_name IF NOT EXISTS FOR (s:SubPipeline) ON (s.name)",
            
            # Source component type index for filtering
            "CREATE INDEX source_component_type_transformation IF NOT EXISTS FOR (t:Transformation) ON (t.source_component_type)",
            "CREATE INDEX source_component_type_reusable_transformation IF NOT EXISTS FOR (r:ReusableTransformation) ON (r.source_component_type)",
            "CREATE INDEX source_component_type_pipeline IF NOT EXISTS FOR (p:Pipeline) ON (p.source_component_type)",
            "CREATE INDEX source_component_type_task IF NOT EXISTS FOR (t:Task) ON (t.source_component_type)",
            "CREATE INDEX source_component_type_sub_pipeline IF NOT EXISTS FOR (s:SubPipeline) ON (s.source_component_type)",
            
            # File and code indexes
            "CREATE INDEX source_file_path IF NOT EXISTS FOR (f:SourceFile) ON (f.file_path)",
            "CREATE INDEX generated_code_path IF NOT EXISTS FOR (c:GeneratedCode) ON (c.file_path)",
            
            # Data model indexes
            "CREATE INDEX table_name IF NOT EXISTS FOR (t:Table) ON (t.name)",
            "CREATE INDEX source_name IF NOT EXISTS FOR (s:Source) ON (s.name)",
            "CREATE INDEX target_name IF NOT EXISTS FOR (t:Target) ON (t.name)",
            
            # Field and Port indexes for column-level lineage
            "CREATE INDEX field_name IF NOT EXISTS FOR (f:Field) ON (f.name)",
            "CREATE INDEX field_transformation IF NOT EXISTS FOR (f:Field) ON (f.transformation)",
            "CREATE INDEX port_name IF NOT EXISTS FOR (p:Port) ON (p.name)",
            "CREATE INDEX port_transformation IF NOT EXISTS FOR (p:Port) ON (p.transformation)",
            
            # Composite indexes for common query patterns
            "CREATE INDEX transformation_name_type IF NOT EXISTS FOR (t:Transformation) ON (t.name, t.type)",
            "CREATE INDEX field_name_transformation IF NOT EXISTS FOR (f:Field) ON (f.name, f.transformation)",
            "CREATE INDEX port_name_transformation IF NOT EXISTS FOR (p:Port) ON (p.name, p.transformation)",
            "CREATE INDEX port_transformation_type IF NOT EXISTS FOR (p:Port) ON (p.transformation, p.port_type)",
        ]
        
        with driver.session() as session:
            for index_query in indexes:
                try:
                    session.run(index_query)
                    logger.debug(f"Created index: {index_query[:50]}...")
                except Exception as e:
                    logger.warning(f"Index creation warning: {str(e)}")
        
        logger.info("Schema creation completed successfully")
        
    except Exception as e:
        logger.error(f"Schema creation failed: {str(e)}", error=e)
        raise
    finally:
        driver.close()


def main():
    """Main entry point."""
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    
    print("=" * 60)
    print("Neo4j Schema Creation Script")
    print("=" * 60)
    print(f"URI: {uri}")
    print(f"User: {user}")
    print("=" * 60)
    print()
    print("WARNING: This will DELETE ALL existing data in Neo4j!")
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() != "yes":
        print("Aborted.")
        return
    
    try:
        create_schema(uri, user, password)
        print()
        print("=" * 60)
        print("Schema creation completed successfully!")
        print("=" * 60)
    except Exception as e:
        print()
        print("=" * 60)
        print(f"ERROR: Schema creation failed: {str(e)}")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()

