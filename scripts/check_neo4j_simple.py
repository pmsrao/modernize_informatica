#!/usr/bin/env python3
"""Simple script to check Neo4j data without imports."""
import os
from neo4j import GraphDatabase

uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "password")

driver = GraphDatabase.driver(uri, auth=(user, password))

with driver.session() as s:
    print("=" * 60)
    print("Neo4j Database Contents")
    print("=" * 60)
    
    # Count nodes by type
    for node_type in ["Workflow", "Session", "Worklet", "Mapping"]:
        result = s.run(f'MATCH (n:{node_type}) RETURN count(n) as count').single()
        count = result["count"] if result else 0
        print(f"{node_type}: {count}")
        
        if count > 0:
            names = s.run(f'MATCH (n:{node_type}) RETURN n.name as name LIMIT 5').data()
            name_list = [n.get("name") for n in names]
            print(f"  Examples: {name_list}")
    
    print("\n" + "=" * 60)
    print("Relationships")
    print("=" * 60)
    
    # Count relationships
    rels = s.run("""
        MATCH ()-[r]->()
        RETURN type(r) as rel_type, count(r) as count
        ORDER BY count DESC
    """).data()
    
    for rel in rels:
        print(f"{rel['rel_type']}: {rel['count']}")
    
    print("\n" + "=" * 60)
    print("Workflow Structure for WF_CUSTOMER_ORDERS_ETL")
    print("=" * 60)
    
    # Check specific workflow
    wf_name = "WF_CUSTOMER_ORDERS_ETL"
    workflow_check = s.run("""
        MATCH (w:Workflow {name: $name})
        OPTIONAL MATCH (w)-[:CONTAINS]->(s:Session)
        OPTIONAL MATCH (w)-[:CONTAINS]->(wl:Worklet)-[:CONTAINS]->(s2:Session)
        RETURN w.name as workflow, 
               collect(DISTINCT s.name) as direct_sessions,
               collect(DISTINCT s2.name) as worklet_sessions
    """, name=wf_name).single()
    
    if workflow_check:
        print(f"Workflow: {workflow_check['workflow']}")
        print(f"Direct sessions: {workflow_check['direct_sessions']}")
        print(f"Worklet sessions: {workflow_check['worklet_sessions']}")
        
        # Check if sessions have EXECUTES relationships
        all_sessions = [s for s in (workflow_check['direct_sessions'] or []) if s] + \
                      [s for s in (workflow_check['worklet_sessions'] or []) if s]
        
        if all_sessions:
            print(f"\nChecking EXECUTES relationships for {len(all_sessions)} session(s):")
            for sess_name in all_sessions[:3]:
                exec_check = s.run("""
                    MATCH (s:Session {name: $name})
                    OPTIONAL MATCH (s)-[r]->(m:Mapping)
                    RETURN s.name as session, 
                           type(r) as rel_type,
                           m.name as mapping
                """, name=sess_name).data()
                print(f"  {sess_name}:")
                for rel in exec_check:
                    if rel.get("mapping"):
                        print(f"    -[{rel.get('rel_type', 'N/A')}]-> {rel['mapping']}")
                    else:
                        print(f"    - No relationships to mappings")
    else:
        print(f"Workflow {wf_name} not found")

driver.close()

