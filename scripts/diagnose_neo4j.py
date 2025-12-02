#!/usr/bin/env python3
"""Diagnostic script to check Neo4j data and relationships."""
import os
from neo4j import GraphDatabase

# Get Neo4j connection from environment or use defaults
uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "password")

def diagnose():
    """Run comprehensive Neo4j diagnostics."""
    print("=" * 80)
    print("Neo4j Database Diagnostic")
    print(f"Connecting to: {uri}")
    print("=" * 80)
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as s:
            # 1. Count all node types
            print("\n1. Node Counts by Type:")
            print("-" * 80)
            result = s.run("""
                MATCH (n)
                RETURN labels(n)[0] as type, count(n) as count
                ORDER BY count DESC
            """).data()
            for record in result:
                print(f"   {record['type']}: {record['count']}")
            
            # 2. List all workflows
            print("\n2. All Workflows:")
            print("-" * 80)
            workflows = s.run("MATCH (w:Workflow) RETURN w.name as name, w.type as type ORDER BY w.name").data()
            for wf in workflows:
                print(f"   - {wf['name']} ({wf.get('type', 'N/A')})")
            
            # 3. Check workflow -> session relationships
            print("\n3. Workflow -> Task (Session) Relationships:")
            print("-" * 80)
            wf_sess = s.run("""
                MATCH (w:Workflow)-[r:CONTAINS]->(s:Session)
                RETURN w.name as workflow, s.name as task, type(r) as rel_type
                ORDER BY w.name, s.name
            """).data()
            if wf_sess:
                for rel in wf_sess:
                    print(f"   {rel['workflow']} -[CONTAINS]-> {rel['task']}")
            else:
                print("   ❌ NO RELATIONSHIPS FOUND!")
            
            # 4. Check session -> mapping relationships
            print("\n4. Task (Session) -> Transformation (Mapping) Relationships:")
            print("-" * 80)
            sess_map = s.run("""
                MATCH (s:Session)-[r]->(m:Mapping)
                RETURN s.name as task, m.name as transformation, type(r) as rel_type
                ORDER BY s.name, m.name
            """).data()
            if sess_map:
                for rel in sess_map:
                    print(f"   {rel['task']} -[{rel['rel_type']}]-> {rel['transformation']}")
            else:
                print("   ❌ NO RELATIONSHIPS FOUND!")
            
            # 5. Check specific workflow structure
            print("\n5. Detailed Workflow Structure (WF_CUSTOMER_ORDERS_ETL):")
            print("-" * 80)
            wf_name = "WF_CUSTOMER_ORDERS_ETL"
            structure = s.run("""
                MATCH (w:Workflow {name: $name})
                OPTIONAL MATCH (w)-[:CONTAINS]->(s:Session)
                OPTIONAL MATCH (w)-[:CONTAINS]->(wl:Worklet)-[:CONTAINS]->(s2:Session)
                RETURN w.name as workflow,
                       collect(DISTINCT s.name) as direct_tasks,
                       collect(DISTINCT s2.name) as worklet_tasks
            """, name=wf_name).single()
            
            if structure:
                print(f"   Workflow: {structure['workflow']}")
                print(f"   Direct tasks: {structure['direct_tasks']}")
                print(f"   Worklet tasks: {structure['worklet_tasks']}")
                
                # Check each task's transformations
                all_tasks = [t for t in (structure['direct_tasks'] or []) if t] + \
                           [t for t in (structure['worklet_tasks'] or []) if t]
                if all_tasks:
                    print(f"\n   Task Details:")
                    for task_name in all_tasks[:5]:  # Check first 5
                        task_trans = s.run("""
                            MATCH (s:Session {name: $name})-[r]->(m:Mapping)
                            RETURN type(r) as rel_type, m.name as transformation
                        """, name=task_name).data()
                        if task_trans:
                            for trans in task_trans:
                                print(f"      {task_name} -[{trans['rel_type']}]-> {trans['transformation']}")
                        else:
                            print(f"      {task_name} - NO TRANSFORMATIONS")
                else:
                    print("   ❌ NO TASKS FOUND IN WORKFLOW!")
            else:
                print(f"   ❌ Workflow {wf_name} not found!")
            
            # 6. Test the actual query used by get_workflow_structure
            print("\n6. Testing get_workflow_structure Query:")
            print("-" * 80)
            test_query = s.run("""
                MATCH (w:Workflow {name: $name})
                OPTIONAL MATCH (w)-[:CONTAINS]->(t:Session)
                OPTIONAL MATCH (w)-[:CONTAINS]->(wl:Worklet)-[:CONTAINS]->(t2:Session)
                WITH collect(DISTINCT t) + collect(DISTINCT t2) as all_tasks
                UNWIND [task IN all_tasks WHERE task IS NOT NULL] as task_node
                RETURN DISTINCT task_node.name as name, 
                       task_node.type as type, 
                       properties(task_node) as properties
                ORDER BY task_node.name
            """, name=wf_name).data()
            
            if test_query:
                print(f"   Found {len(test_query)} task(s):")
                for task in test_query:
                    print(f"      - {task['name']} ({task.get('type', 'N/A')})")
            else:
                print("   ❌ Query returned NO TASKS!")
            
            # 7. Check if sessions exist but aren't linked
            print("\n7. Orphaned Sessions (not linked to workflows):")
            print("-" * 80)
            orphans = s.run("""
                MATCH (s:Session)
                WHERE NOT (s)<-[:CONTAINS]-()
                RETURN s.name as name
                LIMIT 10
            """).data()
            if orphans:
                print(f"   Found {len(orphans)} orphaned session(s):")
                for orphan in orphans:
                    print(f"      - {orphan['name']}")
            else:
                print("   No orphaned sessions")
            
        driver.close()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose()

