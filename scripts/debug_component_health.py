#!/usr/bin/env python3
"""Debug script to investigate Component Health metrics issues."""

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
    print("Component Health Debug")
    print("=" * 80)
    
    gs = GraphStore()
    gq = GraphQueries(gs)
    
    with gs.driver.session() as session:
        # 1. Count all transformations
        print("\n1. All Transformations:")
        result = session.run("""
            MATCH (t:Transformation)
            WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
            RETURN count(t) as total
        """).single()
        total = result['total'] if result else 0
        print(f"   Total: {total}")
        
        # List all transformations with their source_component_type
        result = session.run("""
            MATCH (t:Transformation)
            WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
            RETURN t.name as name, t.source_component_type as source_type, t.transformation_name as transformation_name
            ORDER BY t.name
        """)
        transformations = list(result)
        print(f"   Sample (first 10):")
        for record in transformations[:10]:
            print(f"     - {record['name']} (source_type: {record['source_type']}, transformation_name: {record['transformation_name']})")
        
        # 2. Count all GeneratedCode nodes
        print("\n2. All GeneratedCode Nodes:")
        result = session.run("""
            MATCH (c:GeneratedCode)
            RETURN count(c) as total
        """).single()
        total_code = result['total'] if result else 0
        print(f"   Total: {total_code}")
        
        # List all GeneratedCode nodes
        result = session.run("""
            MATCH (c:GeneratedCode)
            RETURN c.file_path as file_path, 
                   c.mapping_name as mapping_name,
                   c.quality_score as quality_score, 
                   c.ai_reviewed as ai_reviewed
            ORDER BY c.file_path
        """)
        code_nodes = list(result)
        print(f"   Sample (first 10):")
        for record in code_nodes[:10]:
            print(f"     - {record['file_path']}")
            print(f"       mapping_name: {record['mapping_name']}")
            print(f"       quality_score: {record['quality_score']}")
            print(f"       ai_reviewed: {record['ai_reviewed']}")
        
        # 3. Check HAS_CODE relationships
        print("\n3. HAS_CODE Relationships:")
        result = session.run("""
            MATCH (t:Transformation)-[r:HAS_CODE]->(c:GeneratedCode)
            WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
            RETURN count(DISTINCT t) as with_code
        """).single()
        with_code = result['with_code'] if result else 0
        print(f"   Transformations with HAS_CODE: {with_code}")
        
        # List all HAS_CODE relationships
        result = session.run("""
            MATCH (t:Transformation)-[r:HAS_CODE]->(c:GeneratedCode)
            WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
            RETURN t.name as transformation_name, 
                   t.source_component_type as source_type,
                   c.file_path as file_path,
                   c.mapping_name as code_mapping_name
            ORDER BY t.name
        """)
        relationships = list(result)
        print(f"   All relationships ({len(relationships)}):")
        for record in relationships:
            print(f"     - {record['transformation_name']} (source_type: {record['source_type']})")
            print(f"       -> {record['file_path']}")
            print(f"       code.mapping_name: {record['code_mapping_name']}")
        
        # 4. Check which transformations DON'T have code
        print("\n4. Transformations WITHOUT Code:")
        result = session.run("""
            MATCH (t:Transformation)
            WHERE (t.source_component_type = 'mapping' OR t.source_component_type IS NULL)
            AND NOT (t)-[:HAS_CODE]->()
            RETURN t.name as name, t.source_component_type as source_type
            ORDER BY t.name
        """)
        without_code = list(result)
        print(f"   Count: {len(without_code)}")
        for record in without_code[:20]:
            print(f"     - {record['name']} (source_type: {record['source_type']})")
        
        # 5. Check for GeneratedCode nodes that should match transformations
        print("\n5. GeneratedCode -> Transformation Matching:")
        for code_record in code_nodes[:10]:
            mapping_name = code_record['mapping_name']
            if not mapping_name:
                continue
            
            # Check if transformation exists
            trans_result = session.run("""
                MATCH (t:Transformation {name: $mapping_name})
                WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
                RETURN t.name as name, t.source_component_type as source_type
            """, mapping_name=mapping_name).single()
            
            if trans_result:
                # Check if relationship exists
                rel_result = session.run("""
                    MATCH (t:Transformation {name: $mapping_name})-[r:HAS_CODE]->(c:GeneratedCode {file_path: $file_path})
                    RETURN r
                """, mapping_name=mapping_name, file_path=code_record['file_path']).single()
                
                if rel_result:
                    print(f"   ✅ {mapping_name} -> {code_record['file_path']} (linked)")
                else:
                    print(f"   ❌ {mapping_name} -> {code_record['file_path']} (NOT linked, but transformation exists)")
            else:
                print(f"   ⚠️  {mapping_name} -> {code_record['file_path']} (transformation NOT found)")
        
        # 6. Test the exact query used in get_canonical_overview
        print("\n6. Testing get_canonical_overview Query:")
        result = session.run("""
            MATCH (t:Transformation {source_component_type: 'mapping'})-[:HAS_CODE]->(c:GeneratedCode)
            RETURN count(DISTINCT t) as count
        """).single()
        count_with_mapping_type = result['count'] if result else 0
        print(f"   With source_component_type='mapping': {count_with_mapping_type}")
        
        result = session.run("""
            MATCH (t:Transformation)-[:HAS_CODE]->(c:GeneratedCode)
            WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
            RETURN count(DISTINCT t) as count
        """).single()
        count_with_null = result['count'] if result else 0
        print(f"   With source_component_type='mapping' OR NULL: {count_with_null}")
        
        result = session.run("""
            MATCH (t:Transformation)-[:HAS_CODE]->(c:GeneratedCode)
            WHERE t.source_component_type IS NULL
            RETURN count(DISTINCT t) as count
        """).single()
        count_only_null = result['count'] if result else 0
        print(f"   With source_component_type IS NULL only: {count_only_null}")
    
    gs.close()

if __name__ == "__main__":
    main()

