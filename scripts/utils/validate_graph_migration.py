#!/usr/bin/env python3
"""Validate graph migration."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from graph.graph_store import GraphStore
from versioning.version_store import VersionStore
from graph.graph_sync import GraphSync
from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def validate_all():
    """Validate all mappings are in sync."""
    print("=" * 60)
    print("Graph Migration Validation")
    print("=" * 60)
    print()
    
    # Check if graph store is enabled
    if not settings.enable_graph_store:
        print("❌ Graph store is not enabled.")
        print("   Set ENABLE_GRAPH_STORE=true in environment or .env file")
        return
    
    # Initialize stores
    print("Initializing stores...")
    version_store = VersionStore(path=settings.version_store_path)
    
    try:
        graph_store = GraphStore(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password
        )
    except Exception as e:
        print(f"❌ Failed to connect to Neo4j: {str(e)}")
        print("   Make sure Neo4j is running and credentials are correct")
        return
    
    sync = GraphSync(version_store, graph_store)
    
    # Verify all
    print()
    print("Validating mappings...")
    print("-" * 60)
    results = sync.verify_all()
    
    print()
    print("=" * 60)
    print("Validation Results")
    print("=" * 60)
    print(f"Total mappings: {results['total']}")
    print(f"✅ In sync: {results['in_sync']}")
    print(f"❌ Out of sync: {results['out_of_sync']}")
    print(f"⚠️  Missing in JSON: {results['missing_in_json']}")
    print(f"⚠️  Missing in graph: {results['missing_in_graph']}")
    
    if results['errors']:
        print()
        print("Errors:")
        for error in results['errors'][:10]:
            print(f"  - {error}")
    
    print()
    if results['in_sync'] == results['total'] and results['out_of_sync'] == 0:
        print("✅ All mappings are in sync!")
    else:
        print("❌ Some mappings are out of sync")
        print("   Run migrate_to_graph.py to sync")
    
    print("=" * 60)
    
    graph_store.close()


if __name__ == "__main__":
    validate_all()

