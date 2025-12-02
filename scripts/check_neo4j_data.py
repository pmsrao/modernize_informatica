#!/usr/bin/env python3
"""Quick script to check what's in Neo4j."""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from src.graph.graph_store import GraphStore
from src.config import settings

try:
    gs = GraphStore()
    with gs.driver.session() as s:
        # Count nodes by type
        print("=" * 60)
        print("Neo4j Database Contents")
        print("=" * 60)
        
        for node_type in ["Workflow", "Session", "Worklet", "Mapping"]:
            result = s.run(f'MATCH (n:{node_type}) RETURN count(n) as count').single()
            count = result["count"] if result else 0
            print(f"{node_type}: {count}")
            
            if count > 0:
                # List names
                names = s.run(f'MATCH (n:{node_type}) RETURN n.name as name LIMIT 10').data()
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
        print("Workflow Structure Check")
        print("=" * 60)
        
        # Check if workflows have sessions
        workflow_check = s.run("""
            MATCH (w:Workflow)
            OPTIONAL MATCH (w)-[:CONTAINS]->(s:Session)
            RETURN w.name as workflow, count(s) as session_count
            ORDER BY w.name
        """).data()
        
        for wf in workflow_check:
            print(f"{wf['workflow']}: {wf['session_count']} session(s)")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

