#!/usr/bin/env python3
"""Cleanup utility for Neo4j data and file storage."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

import argparse
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


def cleanup_neo4j(confirm: bool = False):
    """Clean up all data from Neo4j."""
    if not settings.enable_graph_store:
        print("❌ Graph store is not enabled. Set ENABLE_GRAPH_STORE=true in .env")
        return False
    
    try:
        from src.graph.graph_store import GraphStore
        
        graph_store = GraphStore(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password
        )
        
        if not confirm:
            print("⚠️  This will delete ALL data from Neo4j!")
            response = input("Type 'DELETE ALL' to confirm: ")
            if response != "DELETE ALL":
                print("❌ Cleanup cancelled.")
                return False
        
        print("🗑️  Deleting all nodes and relationships from Neo4j...")
        
        with graph_store.driver.session() as session:
            # Delete all relationships first
            result = session.run("MATCH ()-[r]->() DELETE r")
            deleted_rels = result.consume().counters.relationships_deleted
            print(f"   Deleted {deleted_rels} relationships")
            
            # Delete all nodes
            result = session.run("MATCH (n) DELETE n")
            deleted_nodes = result.consume().counters.nodes_deleted
            print(f"   Deleted {deleted_nodes} nodes")
        
        print("✅ Neo4j cleanup completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Neo4j cleanup failed: {str(e)}")
        logger.error(f"Neo4j cleanup failed: {str(e)}")
        return False


def cleanup_files(confirm: bool = False):
    """Clean up uploaded files from storage."""
    upload_dir = Path(settings.upload_dir)
    
    if not upload_dir.exists():
        print(f"ℹ️  Upload directory does not exist: {upload_dir}")
        return True
    
    files = list(upload_dir.glob("*"))
    xml_files = [f for f in files if f.is_file() and f.suffix.lower() == '.xml']
    
    if not xml_files:
        print("ℹ️  No XML files found in upload directory.")
        return True
    
    if not confirm:
        print(f"⚠️  This will delete {len(xml_files)} file(s) from {upload_dir}")
        response = input("Type 'DELETE FILES' to confirm: ")
        if response != "DELETE FILES":
            print("❌ Cleanup cancelled.")
            return False
    
    print(f"🗑️  Deleting {len(xml_files)} file(s) from {upload_dir}...")
    
    deleted_count = 0
    for file_path in xml_files:
        try:
            file_path.unlink()
            deleted_count += 1
            print(f"   Deleted: {file_path.name}")
        except Exception as e:
            print(f"   ❌ Failed to delete {file_path.name}: {str(e)}")
    
    # Also clear the file manager registry if API is running
    try:
        from src.api.file_manager import file_manager
        file_manager.clear_registry()
        print("   ✅ Cleared file manager registry")
    except Exception as e:
        print(f"   ⚠️  Could not clear file manager registry (API may not be running): {e}")
    
    print(f"✅ File cleanup completed: {deleted_count}/{len(xml_files)} files deleted")
    return True


def cleanup_version_store(confirm: bool = False):
    """Clean up version store (JSON files)."""
    version_store_path = Path(settings.version_store_path)
    
    if not version_store_path.exists():
        print(f"ℹ️  Version store directory does not exist: {version_store_path}")
        return True
    
    json_files = list(version_store_path.glob("*.json"))
    
    if not json_files:
        print("ℹ️  No JSON files found in version store.")
        return True
    
    if not confirm:
        print(f"⚠️  This will delete {len(json_files)} JSON file(s) from {version_store_path}")
        response = input("Type 'DELETE JSON' to confirm: ")
        if response != "DELETE JSON":
            print("❌ Cleanup cancelled.")
            return False
    
    print(f"🗑️  Deleting {len(json_files)} JSON file(s) from {version_store_path}...")
    
    deleted_count = 0
    for file_path in json_files:
        try:
            file_path.unlink()
            deleted_count += 1
            print(f"   Deleted: {file_path.name}")
        except Exception as e:
            print(f"   ❌ Failed to delete {file_path.name}: {str(e)}")
    
    print(f"✅ Version store cleanup completed: {deleted_count}/{len(json_files)} files deleted")
    return True


def cleanup_all(confirm: bool = False):
    """Clean up everything."""
    print("=" * 60)
    print("🧹 Complete Cleanup")
    print("=" * 60)
    
    if not confirm:
        print("\n⚠️  WARNING: This will delete:")
        print("   - All Neo4j graph data")
        print("   - All uploaded XML files")
        print("   - All version store JSON files")
        print("\nThis action cannot be undone!")
        response = input("\nType 'CLEANUP ALL' to confirm: ")
        if response != "CLEANUP ALL":
            print("❌ Cleanup cancelled.")
            return False
    
    print("\n")
    success = True
    
    # Clean Neo4j
    print("1️⃣  Cleaning Neo4j...")
    if not cleanup_neo4j(confirm=True):
        success = False
    print()
    
    # Clean files
    print("2️⃣  Cleaning uploaded files...")
    if not cleanup_files(confirm=True):
        success = False
    print()
    
    # Clean version store
    print("3️⃣  Cleaning version store...")
    if not cleanup_version_store(confirm=True):
        success = False
    print()
    
    if success:
        print("=" * 60)
        print("✅ All cleanup operations completed successfully!")
        print("=" * 60)
    else:
        print("=" * 60)
        print("⚠️  Some cleanup operations had errors. Check the output above.")
        print("=" * 60)
    
    return success


def main():
    parser = argparse.ArgumentParser(description="Cleanup utility for Neo4j and file storage")
    parser.add_argument(
        "--neo4j",
        action="store_true",
        help="Clean up Neo4j graph database"
    )
    parser.add_argument(
        "--files",
        "--uploads",
        dest="files",
        action="store_true",
        help="Clean up uploaded XML files (--files or --uploads)"
    )
    parser.add_argument(
        "--version-store",
        action="store_true",
        help="Clean up version store JSON files"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Clean up everything (Neo4j, files, version store)"
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompts (use with caution!)"
    )
    
    args = parser.parse_args()
    
    if not any([args.neo4j, args.files, args.version_store, args.all]):
        parser.print_help()
        return
    
    if args.all:
        cleanup_all(confirm=args.yes)
    else:
        if args.neo4j:
            cleanup_neo4j(confirm=args.yes)
        if args.files:
            cleanup_files(confirm=args.yes)
        if args.version_store:
            cleanup_version_store(confirm=args.yes)


if __name__ == "__main__":
    main()

