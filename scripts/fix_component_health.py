#!/usr/bin/env python3
"""Script to fix Component Health metrics by linking orphaned GeneratedCode nodes to transformations."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from graph.graph_store import GraphStore
from graph.graph_queries import GraphQueries

def fix_orphaned_code_nodes(graph_store: GraphStore):
    """Link orphaned GeneratedCode nodes to transformations."""
    print("=" * 80)
    print("Fixing Orphaned GeneratedCode Nodes")
    print("=" * 80)
    
    fixed_count = 0
    failed_count = 0
    
    with graph_store.driver.session() as session:
        # Find all GeneratedCode nodes without HAS_CODE relationships
        result = session.run("""
            MATCH (c:GeneratedCode)
            WHERE NOT (c)<-[:HAS_CODE]-()
            RETURN c.file_path as file_path, c.mapping_name as mapping_name
        """)
        
        orphaned_nodes = list(result)
        print(f"\nFound {len(orphaned_nodes)} orphaned GeneratedCode nodes")
        
        for record in orphaned_nodes:
            file_path = record['file_path']
            mapping_name = record['mapping_name']
            
            if not mapping_name:
                print(f"  ⚠️  Skipping {file_path}: no mapping_name")
                failed_count += 1
                continue
            
            # Try to find matching transformation
            match_result = session.run("""
                MATCH (t:Transformation {name: $mapping_name})
                WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
                RETURN t.name as name, t.source_component_type as source_type
                LIMIT 1
            """, mapping_name=mapping_name).single()
            
            if match_result:
                # Create HAS_CODE relationship
                link_result = session.run("""
                    MATCH (c:GeneratedCode {file_path: $file_path})
                    MATCH (t:Transformation {name: $mapping_name})
                    WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
                    MERGE (t)-[:HAS_CODE]->(c)
                    RETURN t.name as name
                """, file_path=file_path, mapping_name=mapping_name).single()
                
                if link_result:
                    print(f"  ✅ Linked {mapping_name} -> {file_path}")
                    fixed_count += 1
                else:
                    print(f"  ❌ Failed to link {mapping_name} -> {file_path}")
                    failed_count += 1
            else:
                print(f"  ⚠️  No transformation found for mapping_name: {mapping_name} (file: {file_path})")
                failed_count += 1
    
    print(f"\n📊 Summary:")
    print(f"  Fixed: {fixed_count}")
    print(f"  Failed: {failed_count}")
    return fixed_count, failed_count

def verify_fixes(graph_store: GraphStore, graph_queries: GraphQueries):
    """Verify the fixes by checking Component Health metrics."""
    print("\n" + "=" * 80)
    print("Verifying Fixes")
    print("=" * 80)
    
    overview = graph_queries.get_canonical_overview()
    health = overview.get('component_health', {})
    
    print("\n📊 Updated Component Health Metrics:")
    total = health.get('total', 0)
    if total > 0:
        print(f"  Total Transformations: {total}")
        print(f"  With Code: {health.get('with_code', 0)} ({health.get('with_code', 0) / total * 100:.1f}%)")
        print(f"  Without Code: {health.get('without_code', 0)} ({health.get('without_code', 0) / total * 100:.1f}%)")
        print(f"  Validated: {health.get('validated', 0)} ({health.get('validated', 0) / total * 100:.1f}%)")
        print(f"  AI Reviewed: {health.get('ai_reviewed', 0)} ({health.get('ai_reviewed', 0) / total * 100:.1f}%)")
        print(f"  AI Fixed: {health.get('ai_fixed', 0)} ({health.get('ai_fixed', 0) / total * 100:.1f}%)")
        print(f"  Needs Review: {health.get('needs_review', 0)} ({health.get('needs_review', 0) / total * 100:.1f}%)")
    else:
        print("  No transformations found in graph")

def main():
    print("Component Health Fix Script")
    print("=" * 80)
    
    try:
        gs = GraphStore()
        gq = GraphQueries(gs)
        
        # Get initial state
        print("\n📊 Initial Component Health Metrics:")
        overview = gq.get_canonical_overview()
        health = overview.get('component_health', {})
        total = health.get('total', 0)
        if total > 0:
            print(f"  With Code: {health.get('with_code', 0)}/{total} ({health.get('with_code', 0) / total * 100:.1f}%)")
            print(f"  Validated: {health.get('validated', 0)}/{total} ({health.get('validated', 0) / total * 100:.1f}%)")
            print(f"  AI Reviewed: {health.get('ai_reviewed', 0)}/{total} ({health.get('ai_reviewed', 0) / total * 100:.1f}%)")
        
        # Fix orphaned nodes
        fixed, failed = fix_orphaned_code_nodes(gs)
        
        # Verify fixes
        verify_fixes(gs, gq)
        
        gs.close()
        
        print("\n" + "=" * 80)
        print("Fix Complete")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

