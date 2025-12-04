#!/usr/bin/env python3
"""Diagnostic script to investigate Component Health metrics issues."""

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

def main():
    print("=" * 80)
    print("Component Health Diagnostic")
    print("=" * 80)
    
    gs = GraphStore()
    gq = GraphQueries(gs)
    
    # Get current overview
    overview = gq.get_canonical_overview()
    health = overview.get('component_health', {})
    
    print("\n📊 Current Component Health Metrics:")
    print(f"  Total Transformations: {health.get('total', 0)}")
    print(f"  With Code: {health.get('with_code', 0)} ({health.get('with_code', 0) / max(health.get('total', 1), 1) * 100:.1f}%)")
    print(f"  Without Code: {health.get('without_code', 0)} ({health.get('without_code', 0) / max(health.get('total', 1), 1) * 100:.1f}%)")
    print(f"  Validated: {health.get('validated', 0)} ({health.get('validated', 0) / max(health.get('total', 1), 1) * 100:.1f}%)")
    print(f"  AI Reviewed: {health.get('ai_reviewed', 0)} ({health.get('ai_reviewed', 0) / max(health.get('total', 1), 1) * 100:.1f}%)")
    print(f"  AI Fixed: {health.get('ai_fixed', 0)} ({health.get('ai_fixed', 0) / max(health.get('total', 1), 1) * 100:.1f}%)")
    print(f"  Needs Review: {health.get('needs_review', 0)} ({health.get('needs_review', 0) / max(health.get('total', 1), 1) * 100:.1f}%)")
    
    with gs.driver.session() as session:
        # 1. Count all transformations
        print("\n" + "=" * 80)
        print("1. Transformations Analysis")
        print("=" * 80)
        
        result = session.run("""
            MATCH (t:Transformation)
            WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
            RETURN count(t) as total
        """).single()
        total_transformations = result['total'] if result else 0
        print(f"\nTotal transformations (mappings): {total_transformations}")
        
        # List all transformations
        result = session.run("""
            MATCH (t:Transformation)
            WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
            RETURN t.name as name, t.source_component_type as source_type, t.transformation_name as transformation_name
            ORDER BY t.name
            LIMIT 20
        """)
        print("\nSample transformations (first 20):")
        for record in result:
            print(f"  - {record['name']} (source_type: {record['source_type']}, transformation_name: {record['transformation_name']})")
        
        # 2. Count GeneratedCode nodes
        print("\n" + "=" * 80)
        print("2. GeneratedCode Analysis")
        print("=" * 80)
        
        result = session.run("""
            MATCH (c:GeneratedCode)
            RETURN count(c) as total
        """).single()
        total_code = result['total'] if result else 0
        print(f"\nTotal GeneratedCode nodes: {total_code}")
        
        # List all GeneratedCode nodes
        result = session.run("""
            MATCH (c:GeneratedCode)
            RETURN c.file_path as file_path, 
                   c.mapping_name as mapping_name,
                   c.quality_score as quality_score, 
                   c.ai_reviewed as ai_reviewed, 
                   c.ai_fixed as ai_fixed,
                   c.ai_review_score as ai_review_score
            ORDER BY c.file_path
            LIMIT 20
        """)
        print("\nSample GeneratedCode nodes (first 20):")
        for record in result:
            print(f"  - {record['file_path']}")
            print(f"    mapping_name: {record['mapping_name']}")
            print(f"    quality_score: {record['quality_score']}")
            print(f"    ai_reviewed: {record['ai_reviewed']}")
            print(f"    ai_fixed: {record['ai_fixed']}")
            print(f"    ai_review_score: {record['ai_review_score']}")
        
        # 3. Check HAS_CODE relationships
        print("\n" + "=" * 80)
        print("3. HAS_CODE Relationships Analysis")
        print("=" * 80)
        
        result = session.run("""
            MATCH (t:Transformation)-[r:HAS_CODE]->(c:GeneratedCode)
            WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
            RETURN count(DISTINCT t) as with_code
        """).single()
        with_code = result['with_code'] if result else 0
        print(f"\nTransformations with HAS_CODE relationship: {with_code}")
        
        # List transformations with code
        result = session.run("""
            MATCH (t:Transformation)-[r:HAS_CODE]->(c:GeneratedCode)
            WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
            RETURN t.name as transformation_name, 
                   t.source_component_type as source_type,
                   c.file_path as file_path,
                   c.mapping_name as code_mapping_name
            ORDER BY t.name
            LIMIT 20
        """)
        print("\nTransformations WITH code (first 20):")
        for record in result:
            print(f"  - {record['transformation_name']} (source_type: {record['source_type']})")
            print(f"    -> {record['file_path']}")
            print(f"    code.mapping_name: {record['code_mapping_name']}")
        
        # 4. Find orphaned GeneratedCode nodes (no HAS_CODE relationship)
        print("\n" + "=" * 80)
        print("4. Orphaned GeneratedCode Nodes")
        print("=" * 80)
        
        result = session.run("""
            MATCH (c:GeneratedCode)
            WHERE NOT (c)<-[:HAS_CODE]-()
            RETURN c.file_path as file_path, c.mapping_name as mapping_name
            LIMIT 20
        """)
        orphaned = list(result)
        print(f"\nOrphaned GeneratedCode nodes (no HAS_CODE relationship): {len(orphaned)}")
        for record in orphaned[:10]:
            print(f"  - {record['file_path']} (mapping_name: {record['mapping_name']})")
        
        # 5. Find transformations without code
        print("\n" + "=" * 80)
        print("5. Transformations WITHOUT Code")
        print("=" * 80)
        
        result = session.run("""
            MATCH (t:Transformation)
            WHERE (t.source_component_type = 'mapping' OR t.source_component_type IS NULL)
            AND NOT (t)-[:HAS_CODE]->()
            RETURN t.name as name, t.source_component_type as source_type
            ORDER BY t.name
            LIMIT 20
        """)
        without_code = list(result)
        print(f"\nTransformations WITHOUT code: {len(without_code)}")
        for record in without_code[:10]:
            print(f"  - {record['name']} (source_type: {record['source_type']})")
        
        # 6. Check for mismatched names
        print("\n" + "=" * 80)
        print("6. Name Mismatch Analysis")
        print("=" * 80)
        
        result = session.run("""
            MATCH (c:GeneratedCode)
            WHERE c.mapping_name IS NOT NULL
            OPTIONAL MATCH (t:Transformation {name: c.mapping_name})
            WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
            RETURN c.file_path as file_path,
                   c.mapping_name as code_mapping_name,
                   t.name as transformation_name,
                   t.source_component_type as source_type
            ORDER BY c.file_path
            LIMIT 20
        """)
        print("\nGeneratedCode -> Transformation matching (first 20):")
        mismatches = 0
        for record in result:
            if record['transformation_name'] is None:
                print(f"  ❌ NO MATCH: {record['code_mapping_name']} (file: {record['file_path']})")
                mismatches += 1
            else:
                print(f"  ✅ MATCH: {record['code_mapping_name']} -> {record['transformation_name']} (source_type: {record['source_type']})")
        
        if mismatches > 0:
            print(f"\n⚠️  Found {mismatches} GeneratedCode nodes that don't match any transformation!")
    
    gs.close()
    print("\n" + "=" * 80)
    print("Diagnostic Complete")
    print("=" * 80)

if __name__ == "__main__":
    main()

