#!/usr/bin/env python3
"""Script to find and fix NULL source_component_type in Neo4j."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from graph.graph_store import GraphStore

def main():
    print("=" * 80)
    print("Finding NULL source_component_type")
    print("=" * 80)
    
    gs = GraphStore()
    
    with gs.driver.session() as session:
        # 1. Find all transformations with NULL source_component_type
        print("\n1. Transformations with NULL source_component_type:")
        result = session.run("""
            MATCH (t:Transformation)
            WHERE t.source_component_type IS NULL
            RETURN t.name as name, 
                   t.transformation as parent_transformation,
                   t.type as type,
                   labels(t) as labels
            ORDER BY t.name
        """)
        
        null_transformations = list(result)
        print(f"   Found {len(null_transformations)} transformations with NULL source_component_type")
        
        for record in null_transformations[:20]:
            print(f"   - {record['name']}")
            print(f"     parent_transformation: {record['parent_transformation']}")
            print(f"     type: {record['type']}")
            print(f"     labels: {record['labels']}")
        
        # 2. Analyze: Are these nested transformations or main mappings?
        print("\n2. Analysis:")
        print("   Checking if these are nested transformations (have 'transformation' property)...")
        
        nested_count = 0
        main_count = 0
        
        for record in null_transformations:
            if record['parent_transformation']:
                nested_count += 1
            else:
                main_count += 1
        
        print(f"   Nested transformations (have parent): {nested_count}")
        print(f"   Main transformations (no parent): {main_count}")
        
        # 3. Find main transformations (mappings) with NULL
        print("\n3. Main Transformations (mappings) with NULL:")
        result = session.run("""
            MATCH (t:Transformation)
            WHERE t.source_component_type IS NULL
            AND t.transformation IS NULL
            RETURN t.name as name, t.type as type
            ORDER BY t.name
        """)
        
        main_with_null = list(result)
        print(f"   Found {len(main_with_null)} main transformations with NULL")
        for record in main_with_null[:10]:
            print(f"   - {record['name']} (type: {record['type']})")
        
        # 4. Check if these main transformations should be 'mapping'
        print("\n4. Checking if these should be 'mapping':")
        for record in main_with_null[:5]:
            name = record['name']
            # Check if it has sources/targets (indicating it's a mapping)
            check_result = session.run("""
                MATCH (t:Transformation {name: $name})
                OPTIONAL MATCH (t)-[:HAS_SOURCE]->(s:Source)
                OPTIONAL MATCH (t)-[:HAS_TARGET]->(tg:Target)
                RETURN count(DISTINCT s) as source_count, count(DISTINCT tg) as target_count
            """, name=name).single()
            
            source_count = check_result['source_count'] if check_result else 0
            target_count = check_result['target_count'] if check_result else 0
            
            print(f"   - {name}: {source_count} sources, {target_count} targets")
            if source_count > 0 or target_count > 0:
                print(f"     ✅ Should be 'mapping'")
            else:
                print(f"     ⚠️  No sources/targets - might be nested or orphaned")
        
        # 5. Fix main transformations that should be 'mapping'
        print("\n5. Fixing main transformations:")
        fixed_count = 0
        
        for record in main_with_null:
            name = record['name']
            # Check if it has sources/targets
            check_result = session.run("""
                MATCH (t:Transformation {name: $name})
                WHERE t.source_component_type IS NULL
                OPTIONAL MATCH (t)-[:HAS_SOURCE]->(s:Source)
                OPTIONAL MATCH (t)-[:HAS_TARGET]->(tg:Target)
                RETURN count(DISTINCT s) as source_count, count(DISTINCT tg) as target_count
            """, name=name).single()
            
            if check_result:
                source_count = check_result['source_count'] or 0
                target_count = check_result['target_count'] or 0
                
                # If it has sources or targets, it's a mapping
                if source_count > 0 or target_count > 0:
                    session.run("""
                        MATCH (t:Transformation {name: $name})
                        WHERE t.source_component_type IS NULL
                        SET t.source_component_type = 'mapping'
                    """, name=name)
                    print(f"   ✅ Fixed {name} -> 'mapping'")
                    fixed_count += 1
        
        print(f"\n   Fixed {fixed_count} main transformations")
        
        # 6. For nested transformations, they shouldn't have source_component_type
        # But if they do exist, we should set them appropriately
        # Actually, nested transformations shouldn't be counted in Component Health metrics
        # The queries should filter them out by checking if they have a parent transformation
        
        # 7. Verify fix
        print("\n6. Verification:")
        result = session.run("""
            MATCH (t:Transformation)
            WHERE t.source_component_type IS NULL
            AND t.transformation IS NULL
            RETURN count(t) as count
        """).single()
        remaining_null = result['count'] if result else 0
        print(f"   Remaining main transformations with NULL: {remaining_null}")
        
        if remaining_null == 0:
            print("   ✅ All main transformations now have source_component_type set!")
        else:
            print(f"   ⚠️  {remaining_null} main transformations still have NULL")
    
    gs.close()
    print("\n" + "=" * 80)
    print("Fix Complete")
    print("=" * 80)

if __name__ == "__main__":
    main()

