#!/usr/bin/env python3
"""Migration script: JSON to Neo4j."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from src.graph.graph_store import GraphStore
from src.versioning.version_store import VersionStore
from src.graph.graph_sync import GraphSync
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


def migrate_all():
    """Migrate all JSON models to Neo4j."""
    print("=" * 60)
    print("Neo4j Migration Tool")
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
    
    # Sync all
    print()
    print("Starting migration...")
    print("-" * 60)
    results = sync.sync_all()
    
    print()
    print("=" * 60)
    print("Migration Results")
    print("=" * 60)
    print(f"✅ Synced: {results['synced']}")
    print(f"❌ Failed: {results['failed']}")
    
    if results['errors']:
        print()
        print("Errors:")
        for error in results['errors'][:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(results['errors']) > 10:
            print(f"  ... and {len(results['errors']) - 10} more errors")
    
    print()
    print("=" * 60)
    
    graph_store.close()


if __name__ == "__main__":
    migrate_all()

