#!/usr/bin/env python3
"""Check if mapplets (ReusableTransformations) have code generated and are included in health metrics."""

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
    print("Mapplet Code Generation & Health Metrics Check")
    print("=" * 80)
    
    gs = GraphStore()
    gq = GraphQueries(gs)
    
    with gs.driver.session() as session:
        # 1. Count ReusableTransformations
        print("\n1. ReusableTransformations (Mapplets):")
        result = session.run("""
            MATCH (rt:ReusableTransformation)
            RETURN count(rt) as total
        """).single()
        total_mapplets = result['total'] if result else 0
        print(f"   Total: {total_mapplets}")
        
        # List all mapplets
        result = session.run("""
            MATCH (rt:ReusableTransformation)
            RETURN rt.name as name, rt.source_component_type as source_type
            ORDER BY rt.name
        """)
        mapplets = list(result)
        print(f"   Mapplets:")
        for record in mapplets:
            print(f"     - {record['name']} (source_type: {record['source_type']})")
        
        # 2. Check if mapplets have GeneratedCode nodes
        print("\n2. Mapplets with GeneratedCode:")
        result = session.run("""
            MATCH (rt:ReusableTransformation)-[:HAS_CODE]->(c:GeneratedCode)
            RETURN rt.name as name, c.file_path as file_path
            ORDER BY rt.name
        """)
        mapplets_with_code = list(result)
        print(f"   Count: {len(mapplets_with_code)}")
        for record in mapplets_with_code:
            print(f"     - {record['name']} -> {record['file_path']}")
        
        if len(mapplets_with_code) == 0:
            print("   ⚠️  No mapplets have GeneratedCode nodes!")
        
        # 3. Check Component Health metrics query
        print("\n3. Component Health Metrics Query Analysis:")
        print("   Current query only counts:")
        print("     - Transformation nodes with source_component_type = 'mapping'")
        print("     - That have sources or targets")
        print("   This EXCLUDES ReusableTransformation nodes")
        
        # 4. Check if mapplets should be included
        print("\n4. Should Mapplets be Included?")
        print("   Design Question:")
        print("     - Mapplets are reusable transformation sets")
        print("     - They can be used by multiple mappings")
        print("     - Do they need standalone code generation?")
        print("     - Should they be included in Component Health metrics?")
        
        # 5. Check how mapplets are used
        print("\n5. Mapplet Usage:")
        result = session.run("""
            MATCH (t:Transformation)-[:USES_REUSABLE_TRANSFORMATION]->(rt:ReusableTransformation)
            RETURN rt.name as mapplet_name, count(DISTINCT t) as usage_count
            ORDER BY rt.name
        """)
        mapplet_usage = list(result)
        print(f"   Mapplets used by mappings:")
        for record in mapplet_usage:
            print(f"     - {record['mapplet_name']}: used by {record['usage_count']} mapping(s)")
        
        if len(mapplet_usage) == 0:
            print("     ⚠️  No mappings are using mapplets (or relationships not created)")
        
        # 6. Check transformation count
        print("\n6. Transformation Count:")
        result = session.run("""
            MATCH (t:Transformation)
            WHERE t.source_component_type = 'mapping'
            AND t.transformation IS NULL
            AND (EXISTS((t)-[:HAS_SOURCE]->()) OR EXISTS((t)-[:HAS_TARGET]->()))
            RETURN count(t) as count
        """).single()
        transformation_count = result['count'] if result else 0
        print(f"   Main Transformations (Mappings): {transformation_count}")
        
        # List them
        result = session.run("""
            MATCH (t:Transformation)
            WHERE t.source_component_type = 'mapping'
            AND t.transformation IS NULL
            AND (EXISTS((t)-[:HAS_SOURCE]->()) OR EXISTS((t)-[:HAS_TARGET]->()))
            RETURN t.name as name
            ORDER BY t.name
        """)
        transformations = list(result)
        print(f"   Mappings:")
        for record in transformations:
            print(f"     - {record['name']}")
    
    gs.close()
    print("\n" + "=" * 80)
    print("Analysis Complete")
    print("=" * 80)

if __name__ == "__main__":
    main()

