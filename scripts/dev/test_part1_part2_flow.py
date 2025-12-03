#!/usr/bin/env python3
"""Test Part 1 and Part 2 flow with graph storage."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from graph.graph_store import GraphStore
from versioning.version_store import VersionStore
from normalizer.mapping_normalizer import MappingNormalizer
from generators.pyspark_generator import PySparkGenerator
from config import settings
from utils.logger import get_logger
from ai_agents.agent_orchestrator import AgentOrchestrator

logger = get_logger(__name__)


def test_part1_flow():
    """Test Part 1: Source to Canonical Form with graph storage."""
    print("=" * 60)
    print("Testing Part 1: Source to Canonical Form")
    print("=" * 60)
    print()
    
    if not settings.enable_graph_store:
        print("❌ Graph store is not enabled.")
        print("   Set ENABLE_GRAPH_STORE=true in .env file")
        return False
    
    try:
        # Initialize components
        graph_store = GraphStore(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password
        )
        
        version_store = VersionStore(
            path=settings.version_store_path,
            graph_store=graph_store,
            graph_first=settings.graph_first
        )
        
        normalizer = MappingNormalizer()
        orchestrator = AgentOrchestrator()
        
        # Sample canonical model (simulating parsed mapping)
        canonical_model = {
            "mapping_name": "M_TEST_FLOW",
            "scd_type": "NONE",
            "incremental_keys": [],
            "sources": [
                {
                    "name": "SQ_CUSTOMER",
                    "table": "CUSTOMER_SRC",
                    "database": "source_db",
                    "fields": [
                        {"name": "CUSTOMER_ID", "data_type": "STRING", "nullable": False},
                        {"name": "FIRST_NAME", "data_type": "STRING", "nullable": True}
                    ]
                }
            ],
            "targets": [
                {
                    "name": "TGT_CUSTOMER",
                    "table": "CUSTOMER_TGT",
                    "database": "target_db",
                    "fields": []
                }
            ],
            "transformations": [
                {
                    "name": "EXP_DERIVE",
                    "type": "EXPRESSION",
                    "ports": []
                }
            ],
            "connectors": [
                {
                    "from_transformation": "SQ_CUSTOMER",
                    "to_transformation": "EXP_DERIVE",
                    "from_port": "*",
                    "to_port": "*"
                }
            ]
        }
        
        print("Step 1: Normalize to canonical model")
        print(f"  Mapping: {canonical_model['mapping_name']}")
        print()
        
        print("Step 2: AI Enhancement")
        enhanced_result = orchestrator.process_with_enhancement(
            canonical_model,
            enable_enhancement=True
        )
        enhanced_model = enhanced_result.get("canonical_model", canonical_model)
        enhancement_applied = enhanced_result.get("enhancement_applied", False)
        print(f"  Enhancement applied: {enhancement_applied}")
        print()
        
        print("Step 3: Save to graph (Part 1)")
        mapping_name = enhanced_model["mapping_name"]
        version_store.save(mapping_name, enhanced_model)
        print(f"  ✅ Saved to graph: {mapping_name}")
        print()
        
        # Verify in graph
        print("Step 4: Verify in graph")
        loaded_from_graph = graph_store.load_mapping(mapping_name)
        if loaded_from_graph:
            print(f"  ✅ Verified in graph: {mapping_name}")
            print(f"     Sources: {len(loaded_from_graph.get('sources', []))}")
            print(f"     Targets: {len(loaded_from_graph.get('targets', []))}")
            print(f"     Transformations: {len(loaded_from_graph.get('transformations', []))}")
        else:
            print(f"  ❌ Not found in graph")
            return False
        
        print()
        print("=" * 60)
        print("✅ Part 1 flow test passed!")
        print("=" * 60)
        print()
        
        return True, mapping_name, enhanced_model
        
    except Exception as e:
        print(f"❌ Part 1 flow test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None, None


def test_part2_flow(mapping_name, enhanced_model):
    """Test Part 2: Canonical Form to Target Stack."""
    print("=" * 60)
    print("Testing Part 2: Canonical Form to Target Stack")
    print("=" * 60)
    print()
    
    if not settings.enable_graph_store:
        print("❌ Graph store is not enabled.")
        return False
    
    try:
        # Initialize components
        graph_store = GraphStore(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password
        )
        
        version_store = VersionStore(
            path=settings.version_store_path,
            graph_store=graph_store,
            graph_first=settings.graph_first
        )
        
        generator = PySparkGenerator()
        
        print("Step 1: Load from graph (Part 2)")
        if settings.graph_first:
            print("  Loading from graph (graph_first=True)...")
        else:
            print("  Loading from version store...")
        
        loaded_model = version_store.load(mapping_name)
        if not loaded_model:
            print(f"  ❌ Failed to load: {mapping_name}")
            return False
        
        print(f"  ✅ Loaded: {mapping_name}")
        print(f"     Sources: {len(loaded_model.get('sources', []))}")
        print(f"     Targets: {len(loaded_model.get('targets', []))}")
        print()
        
        print("Step 2: Generate code from loaded model")
        code = generator.generate(loaded_model)
        if code:
            print(f"  ✅ Code generated ({len(code)} characters)")
            print(f"     Preview: {code[:100]}...")
        else:
            print(f"  ❌ Code generation failed")
            return False
        
        print()
        print("=" * 60)
        print("✅ Part 2 flow test passed!")
        print("=" * 60)
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Part 2 flow test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def cleanup(mapping_name):
    """Clean up test data."""
    print()
    print("Cleaning up test data...")
    try:
        graph_store = GraphStore(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password
        )
        
        version_store = VersionStore(
            path=settings.version_store_path,
            graph_store=graph_store,
            graph_first=settings.graph_first
        )
        
        graph_store.delete_mapping(mapping_name)
        version_store.delete(mapping_name)
        print(f"  ✅ Cleaned up: {mapping_name}")
        
        graph_store.close()
    except Exception as e:
        print(f"  ⚠️  Cleanup warning: {str(e)}")


def main():
    """Run Part 1 and Part 2 flow tests."""
    print()
    print("Part 1 & Part 2 Flow Test Suite")
    print("=" * 60)
    print()
    
    # Test Part 1
    part1_result, mapping_name, enhanced_model = test_part1_flow()
    if not part1_result:
        print("❌ Part 1 test failed. Cannot proceed to Part 2.")
        return 1
    
    # Test Part 2
    if not test_part2_flow(mapping_name, enhanced_model):
        cleanup(mapping_name)
        print("❌ Part 2 test failed.")
        return 1
    
    # Cleanup
    cleanup(mapping_name)
    
    print()
    print("=" * 60)
    print("✅ All flow tests passed!")
    print("=" * 60)
    print()
    print("Summary:")
    print("  ✅ Part 1: Source → Canonical → Graph storage")
    print("  ✅ Part 2: Graph → Load → Code generation")
    print()
    print("Next Steps:")
    print("  1. Test with real mapping files via API")
    print("  2. Verify graph queries work")
    print("  3. Proceed with short-term enhancements")
    print()
    
    return 0


if __name__ == "__main__":
    exit(main())

