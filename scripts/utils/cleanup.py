#!/usr/bin/env python3
"""Cleanup utility for Neo4j data and file storage."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

import argparse
from typing import Optional
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


def cleanup_neo4j(confirm: bool = False, component_type: Optional[str] = None):
    """Clean up data from Neo4j.
    
    Args:
        confirm: Skip confirmation prompt
        component_type: Optional component type to delete (Mapping, Workflow, Session, Worklet, or None for all)
    """
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
        
        with graph_store.driver.session() as session:
            # Get counts before deletion
            if component_type:
                # Count specific component type
                count_query = f"MATCH (n:{component_type}) RETURN count(n) as count"
                result = session.run(count_query).single()
                component_count = result["count"] if result else 0
                
                if component_count == 0:
                    print(f"ℹ️  No {component_type} nodes found in Neo4j.")
                    return True
                
                if not confirm:
                    print(f"⚠️  This will delete {component_count} {component_type} node(s) and their relationships!")
                    response = input(f"Type 'DELETE {component_type.upper()}' to confirm: ")
                    if response != f"DELETE {component_type.upper()}":
                        print("❌ Cleanup cancelled.")
                        return False
                
                print(f"🗑️  Deleting {component_type} nodes and relationships from Neo4j...")
                
                # Delete relationships connected to this component type
                result = session.run(f"""
                    MATCH (n:{component_type})-[r]-()
                    DELETE r
                """)
                deleted_rels = result.consume().counters.relationships_deleted
                print(f"   Deleted {deleted_rels} relationships")
                
                # Delete nodes of this type
                result = session.run(f"MATCH (n:{component_type}) DELETE n")
                deleted_nodes = result.consume().counters.nodes_deleted
                print(f"   Deleted {deleted_nodes} {component_type} node(s)")
                
            else:
                # Get counts by type before deletion
                count_query = """
                    MATCH (n)
                    RETURN labels(n)[0] as type, count(n) as count
                    ORDER BY type
                """
                type_counts = {}
                for record in session.run(count_query):
                    node_type = record["type"]
                    count = record["count"]
                    type_counts[node_type] = count
                
                if not confirm:
                    print("⚠️  This will delete ALL data from Neo4j!")
                    if type_counts:
                        print("\n   Current data in Neo4j:")
                        for node_type, count in type_counts.items():
                            print(f"      - {node_type}: {count} node(s)")
                    print()
                    response = input("Type 'DELETE ALL' to confirm: ")
                    if response != "DELETE ALL":
                        print("❌ Cleanup cancelled.")
                        return False
                
                print("🗑️  Deleting all nodes and relationships from Neo4j...")
                
                if type_counts:
                    print("\n   Deleting by type:")
                    # Show component types first (workflows, sessions, worklets, mappings)
                    component_types = [
                        "Workflow", "Session", "Worklet", "Mapping", 
                        "Transformation", "Source", "Target", "Table",
                        "SourceFile", "GeneratedCode", "Field", "Database"
                    ]
                    for comp_type in component_types:
                        if comp_type in type_counts:
                            print(f"      - {comp_type}: {type_counts[comp_type]} node(s)")
                    # Show any other types
                    for node_type, count in type_counts.items():
                        if node_type not in component_types:
                            print(f"      - {node_type}: {count} node(s)")
                
                # Delete all relationships first
                result = session.run("MATCH ()-[r]->() DELETE r")
                deleted_rels = result.consume().counters.relationships_deleted
                print(f"\n   ✅ Deleted {deleted_rels} relationship(s)")
                
                # Delete all nodes (this includes all component types and metadata)
                result = session.run("MATCH (n) DELETE n")
                deleted_nodes = result.consume().counters.nodes_deleted
                print(f"   ✅ Deleted {deleted_nodes} node(s) (including:")
                print(f"      • Workflows, Sessions, Worklets, Mappings")
                print(f"      • Transformations, Sources, Targets, Tables")
                print(f"      • SourceFile (file metadata)")
                print(f"      • GeneratedCode (code metadata)")
                print(f"      • All other node types)")
        
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


def cleanup_assessment_reports(confirm: bool = False):
    """Clean up assessment report files."""
    project_root = Path(__file__).parent.parent
    assessment_dir = project_root / "test_log" / "assessment"
    
    if not assessment_dir.exists():
        print(f"ℹ️  Assessment directory does not exist: {assessment_dir}")
        return True
    
    # Find assessment report files
    report_files = list(assessment_dir.glob("*.json")) + list(assessment_dir.glob("*.html"))
    
    if not report_files:
        print("ℹ️  No assessment report files found.")
        return True
    
    if not confirm:
        print(f"⚠️  This will delete {len(report_files)} assessment report file(s) from {assessment_dir}")
        response = input("Type 'DELETE ASSESSMENT' to confirm: ")
        if response != "DELETE ASSESSMENT":
            print("❌ Cleanup cancelled.")
            return False
    
    print(f"🗑️  Deleting {len(report_files)} assessment report file(s) from {assessment_dir}...")
    
    deleted_count = 0
    for file_path in report_files:
        try:
            file_path.unlink()
            deleted_count += 1
            print(f"   Deleted: {file_path.name}")
        except Exception as e:
            print(f"   ❌ Failed to delete {file_path.name}: {str(e)}")
    
    print(f"✅ Assessment reports cleanup completed: {deleted_count}/{len(report_files)} files deleted")
    return True


def cleanup_all(confirm: bool = False):
    """Clean up everything."""
    print("=" * 60)
    print("🧹 Complete Cleanup")
    print("=" * 60)
    
    if not confirm:
        print("\n⚠️  WARNING: This will delete:")
        print("   - All Neo4j graph data:")
        print("     • Workflows, Sessions, Worklets, Mappings")
        print("     • Transformations, Sources, Targets, Tables")
        print("     • SourceFile nodes (file metadata)")
        print("     • GeneratedCode nodes (code metadata)")
        print("     • All relationships (CONTAINS, EXECUTES, HAS_SOURCE, HAS_TARGET,")
        print("       HAS_TRANSFORMATION, HAS_CODE, LOADED_FROM, etc.)")
        print("   - All uploaded XML files")
        print("   - All version store JSON files")
        print("   - All assessment report files")
        print("\nThis action cannot be undone!")
        response = input("\nType 'CLEANUP ALL' to confirm: ")
        if response != "CLEANUP ALL":
            print("❌ Cleanup cancelled.")
            return False
    
    print("\n")
    success = True
    
    # Clean Neo4j
    print("1️⃣  Cleaning Neo4j (all nodes and relationships)...")
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
    
    # Clean assessment reports
    print("4️⃣  Cleaning assessment reports...")
    if not cleanup_assessment_reports(confirm=True):
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
    parser = argparse.ArgumentParser(
        description="Cleanup utility for Neo4j and file storage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Clean up everything (Neo4j, files, version store, assessment reports)
  python scripts/utils/cleanup.py --all --yes

  # Clean up only Neo4j
  python scripts/utils/cleanup.py --neo4j --yes

  # Clean up only workflows from Neo4j
  python scripts/utils/cleanup.py --neo4j --component Workflow --yes

  # Clean up only mappings from Neo4j
  python scripts/utils/cleanup.py --neo4j --component Mapping --yes

  # Clean up only assessment reports
  python scripts/utils/cleanup.py --assessment --yes

Available component types: Mapping, Workflow, Session, Worklet, Transformation, Source, Target, Table, SourceFile, GeneratedCode, Field, Database
        """
    )
    parser.add_argument(
        "--neo4j",
        action="store_true",
        help="Clean up Neo4j graph database"
    )
    parser.add_argument(
        "--component",
        type=str,
        choices=["Mapping", "Workflow", "Session", "Worklet", "Transformation", "Source", "Target", "Table", "SourceFile", "GeneratedCode"],
        help="Clean up specific component type from Neo4j (use with --neo4j)"
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
        "--assessment",
        action="store_true",
        help="Clean up assessment report files"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Clean up everything (Neo4j, files, version store, assessment reports)"
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompts (use with caution!)"
    )
    
    args = parser.parse_args()
    
    if not any([args.neo4j, args.files, args.version_store, args.assessment, args.all]):
        parser.print_help()
        return
    
    if args.component and not args.neo4j:
        print("❌ --component can only be used with --neo4j")
        parser.print_help()
        return
    
    if args.all:
        cleanup_all(confirm=args.yes)
    else:
        if args.neo4j:
            cleanup_neo4j(confirm=args.yes, component_type=args.component)
        if args.files:
            cleanup_files(confirm=args.yes)
        if args.version_store:
            cleanup_version_store(confirm=args.yes)
        if args.assessment:
            cleanup_assessment_reports(confirm=args.yes)


if __name__ == "__main__":
    main()

