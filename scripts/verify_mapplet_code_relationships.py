#!/usr/bin/env python3
"""Verify HAS_CODE relationships for mapplets in Neo4j."""

import os
from neo4j import GraphDatabase

# Get Neo4j connection from environment or use defaults
uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "password")


def verify_mapplet_code_relationships():
    """Verify HAS_CODE relationships for mapplets."""
    print("=" * 80)
    print("Mapplet Code Relationships Verification")
    print(f"Connecting to: {uri}")
    print("=" * 80)
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
    except Exception as e:
        print(f"❌ Failed to connect to Neo4j: {e}")
        print("\nTroubleshooting:")
        print("  1. Check if Neo4j is running: docker ps | grep neo4j")
        print("  2. Verify credentials in .env file or environment variables")
        return
    
    with driver.session() as session:
        # 1. Check all ReusableTransformation nodes
        print("\n1. ReusableTransformation Nodes:")
        result = session.run("""
            MATCH (rt:ReusableTransformation)
            RETURN rt.name as name, rt.source_component_type as source_type
            ORDER BY rt.name
        """)
        mapplets = list(result)
        print(f"   Total ReusableTransformations: {len(mapplets)}")
        for record in mapplets:
            print(f"     - {record['name']} (source_type: {record['source_type']})")
        
        if not mapplets:
            print("   ⚠️  No ReusableTransformation nodes found!")
            return
        
        # 2. Check GeneratedCode nodes for mapplets
        print("\n2. GeneratedCode Nodes (for mapplets):")
        result = session.run("""
            MATCH (rt:ReusableTransformation)-[:HAS_CODE]->(gc:GeneratedCode)
            RETURN DISTINCT gc.file_path as file_path, gc.code_type as code_type, 
                   collect(rt.name) as mapplet_names
            ORDER BY gc.file_path
        """)
        code_nodes = list(result)
        print(f"   Total GeneratedCode nodes linked to mapplets: {len(code_nodes)}")
        for record in code_nodes:
            print(f"     - File: {record['file_path']}")
            print(f"       Code Type: {record['code_type']}")
            print(f"       Linked Mapplets: {', '.join(record['mapplet_names'])}")
        
        # 3. Check HAS_CODE relationships
        print("\n3. HAS_CODE Relationships:")
        result = session.run("""
            MATCH (rt:ReusableTransformation)-[r:HAS_CODE]->(gc:GeneratedCode)
            RETURN rt.name as mapplet_name, gc.file_path as file_path, 
                   gc.code_type as code_type, gc.language as language,
                   gc.quality_score as quality_score,
                   gc.ai_reviewed as ai_reviewed, gc.ai_fixed as ai_fixed
            ORDER BY rt.name, gc.file_path
        """)
        relationships = list(result)
        print(f"   Total HAS_CODE relationships: {len(relationships)}")
        
        if relationships:
            print("\n   Detailed Relationships:")
            for record in relationships:
                print(f"     ✅ {record['mapplet_name']} -> {record['file_path']}")
                print(f"        Code Type: {record['code_type']}, Language: {record['language']}")
                print(f"        Quality Score: {record['quality_score']}")
                print(f"        AI Reviewed: {record['ai_reviewed']}, AI Fixed: {record['ai_fixed']}")
        else:
            print("   ⚠️  No HAS_CODE relationships found!")
        
        # 4. Check for mapplets without code
        print("\n4. Mapplets Without Code:")
        result = session.run("""
            MATCH (rt:ReusableTransformation)
            WHERE NOT EXISTS((rt)-[:HAS_CODE]->())
            RETURN rt.name as name
            ORDER BY rt.name
        """)
        mapplets_without_code = list(result)
        if mapplets_without_code:
            print(f"   ⚠️  Found {len(mapplets_without_code)} mapplet(s) without code:")
            for record in mapplets_without_code:
                print(f"     - {record['name']}")
        else:
            print("   ✅ All mapplets have code!")
        
        # 5. Check for orphaned GeneratedCode nodes (not linked to any mapplet)
        print("\n5. Orphaned GeneratedCode Nodes (for mapplets):")
        result = session.run("""
            MATCH (gc:GeneratedCode)
            WHERE (gc.file_path CONTAINS 'common_utils' OR gc.file_path CONTAINS 'shared')
            AND NOT EXISTS((:ReusableTransformation)-[:HAS_CODE]->(gc))
            RETURN gc.file_path as file_path, gc.code_type as code_type,
                   gc.mapplet_name as mapplet_name
            ORDER BY gc.file_path
        """)
        orphaned = list(result)
        if orphaned:
            print(f"   ⚠️  Found {len(orphaned)} potentially orphaned GeneratedCode node(s):")
            for record in orphaned:
                mapplet_info = f" (mapplet: {record['mapplet_name']})" if record.get('mapplet_name') else ""
                print(f"     - {record['file_path']} (type: {record['code_type']}){mapplet_info}")
            print("\n   ℹ️  Note: Shared files (common_utils_pyspark.py) are linked to multiple mapplets.")
            print("      If a file appears here but also appears in section 2, it's a false positive.")
        else:
            print("   ✅ No orphaned GeneratedCode nodes found!")
        
        # 6. Summary statistics
        print("\n6. Summary Statistics:")
        result = session.run("""
            MATCH (rt:ReusableTransformation)
            RETURN count(rt) as total_mapplets
        """).single()
        total_mapplets = result['total_mapplets'] if result else 0
        
        result = session.run("""
            MATCH (rt:ReusableTransformation)-[:HAS_CODE]->(gc:GeneratedCode)
            RETURN count(DISTINCT rt) as mapplets_with_code
        """).single()
        mapplets_with_code = result['mapplets_with_code'] if result else 0
        
        result = session.run("""
            MATCH (rt:ReusableTransformation)-[:HAS_CODE]->(gc:GeneratedCode)
            WHERE gc.ai_reviewed = true
            RETURN count(DISTINCT rt) as mapplets_ai_reviewed
        """).single()
        mapplets_ai_reviewed = result['mapplets_ai_reviewed'] if result else 0
        
        result = session.run("""
            MATCH (rt:ReusableTransformation)-[:HAS_CODE]->(gc:GeneratedCode)
            WHERE gc.ai_fixed = true
            RETURN count(DISTINCT rt) as mapplets_ai_fixed
        """).single()
        mapplets_ai_fixed = result['mapplets_ai_fixed'] if result else 0
        
        print(f"   Total Mapplets: {total_mapplets}")
        print(f"   Mapplets With Code: {mapplets_with_code} ({mapplets_with_code/max(total_mapplets,1)*100:.1f}%)")
        print(f"   Mapplets AI Reviewed: {mapplets_ai_reviewed} ({mapplets_ai_reviewed/max(total_mapplets,1)*100:.1f}%)")
        print(f"   Mapplets AI Fixed: {mapplets_ai_fixed} ({mapplets_ai_fixed/max(total_mapplets,1)*100:.1f}%)")
        
        # 7. Verify specific mapplets from logs
        print("\n7. Expected Mapplets (from logs):")
        expected_mapplets = ["MPL_CALCULATE_TOTALS", "MPL_DATA_CLEANSING"]
        for mapplet_name in expected_mapplets:
            result = session.run("""
                MATCH (rt:ReusableTransformation {name: $name})
                OPTIONAL MATCH (rt)-[:HAS_CODE]->(gc:GeneratedCode)
                RETURN rt.name as name, 
                       count(gc) as code_count,
                       collect(gc.file_path) as file_paths
            """, name=mapplet_name).single()
            
            if result and result['name']:
                code_count = result['code_count'] if result['code_count'] else 0
                file_paths = result['file_paths'] if result['file_paths'] else []
                if code_count > 0:
                    print(f"   ✅ {mapplet_name}: {code_count} code file(s)")
                    for fp in file_paths:
                        print(f"      - {fp}")
                else:
                    print(f"   ⚠️  {mapplet_name}: No code files linked!")
            else:
                print(f"   ❌ {mapplet_name}: Not found in graph!")
    
    print("\n" + "=" * 80)
    print("Verification Complete")
    print("=" * 80)


if __name__ == "__main__":
    try:
        verify_mapplet_code_relationships()
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

