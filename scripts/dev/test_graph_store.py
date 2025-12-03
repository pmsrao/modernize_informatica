#!/usr/bin/env python3
"""Test GraphStore connection and basic operations."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from graph.graph_store import GraphStore
from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def test_connection():
    """Test Neo4j connection."""
    print("=" * 60)
    print("Testing Neo4j Connection")
    print("=" * 60)
    print()
    
    if not settings.enable_graph_store:
        print("❌ Graph store is not enabled.")
        print("   Set ENABLE_GRAPH_STORE=true in .env file")
        return False
    
    try:
        print(f"Connecting to Neo4j...")
        print(f"  URI: {settings.neo4j_uri}")
        print(f"  User: {settings.neo4j_user}")
        print()
        
        graph_store = GraphStore(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password
        )
        
        print("✅ Connection successful!")
        print()
        
        # Test basic query
        print("Testing basic query...")
        with graph_store.driver.session() as session:
            result = session.run("RETURN 1 as test").single()
            if result and result["test"] == 1:
                print("✅ Basic query successful!")
            else:
                print("❌ Basic query failed")
                return False
        
        print()
        print("=" * 60)
        print("✅ All connection tests passed!")
        print("=" * 60)
        
        graph_store.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print()
        print("Troubleshooting:")
        print("  1. Check if Neo4j is running: docker ps | grep neo4j")
        print("  2. Verify credentials in .env file")
        print("  3. Check Neo4j logs: docker logs neo4j-modernize")
        return False


def test_save_load():
    """Test save and load operations."""
    print()
    print("=" * 60)
    print("Testing Save/Load Operations")
    print("=" * 60)
    print()
    
    if not settings.enable_graph_store:
        print("❌ Graph store is not enabled.")
        return False
    
    try:
        graph_store = GraphStore(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password
        )
        
        # Sample canonical model
        test_model = {
            "mapping_name": "M_TEST_CONNECTION",
            "scd_type": "NONE",
            "incremental_keys": [],
            "sources": [
                {
                    "name": "SQ_TEST",
                    "table": "TEST_TABLE",
                    "database": "test_db",
                    "fields": [
                        {"name": "ID", "data_type": "STRING", "nullable": False},
                        {"name": "NAME", "data_type": "STRING", "nullable": True}
                    ]
                }
            ],
            "targets": [
                {
                    "name": "TGT_TEST",
                    "table": "TEST_TARGET",
                    "database": "test_db",
                    "fields": []
                }
            ],
            "transformations": [
                {
                    "name": "EXP_TEST",
                    "type": "EXPRESSION",
                    "ports": []
                }
            ],
            "connectors": [
                {
                    "from_transformation": "SQ_TEST",
                    "to_transformation": "EXP_TEST",
                    "from_port": "*",
                    "to_port": "*"
                }
            ]
        }
        
        print("Saving test model...")
        mapping_name = graph_store.save_mapping(test_model)
        print(f"✅ Model saved: {mapping_name}")
        print()
        
        print("Loading test model...")
        loaded_model = graph_store.load_mapping("M_TEST_CONNECTION")
        if loaded_model:
            print("✅ Model loaded successfully!")
            print(f"   Mapping: {loaded_model.get('mapping_name')}")
            print(f"   Sources: {len(loaded_model.get('sources', []))}")
            print(f"   Targets: {len(loaded_model.get('targets', []))}")
            print(f"   Transformations: {len(loaded_model.get('transformations', []))}")
        else:
            print("❌ Model load failed")
            return False
        
        print()
        print("Cleaning up test data...")
        deleted = graph_store.delete_mapping("M_TEST_CONNECTION")
        if deleted:
            print("✅ Test data cleaned up")
        else:
            print("⚠️  Test data cleanup failed (may not exist)")
        
        print()
        print("=" * 60)
        print("✅ All save/load tests passed!")
        print("=" * 60)
        
        graph_store.close()
        return True
        
    except Exception as e:
        print(f"❌ Save/load test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print()
    print("GraphStore Test Suite")
    print("=" * 60)
    print()
    
    # Test connection
    if not test_connection():
        print()
        print("❌ Connection test failed. Please fix connection issues first.")
        return 1
    
    # Test save/load
    if not test_save_load():
        print()
        print("❌ Save/load test failed.")
        return 1
    
    print()
    print("=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    print()
    print("Next Steps:")
    print("  1. Proceed with Step 2: Integrate Graph Store into Part 1 Flow")
    print("  2. Test with real mapping files")
    print()
    
    return 0


if __name__ == "__main__":
    exit(main())

