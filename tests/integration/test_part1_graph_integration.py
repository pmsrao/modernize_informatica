"""Integration tests for Part 1 flow with graph storage."""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from src.graph.graph_store import GraphStore
from src.versioning.version_store import VersionStore
from src.normalizer.mapping_normalizer import MappingNormalizer
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture(scope="module")
def graph_store():
    """Create GraphStore instance (skip if not enabled)."""
    if not settings.enable_graph_store:
        pytest.skip("Graph store not enabled")
    
    try:
        store = GraphStore(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password
        )
        yield store
        store.close()
    except Exception as e:
        pytest.skip(f"Neo4j not available: {str(e)}")


@pytest.fixture
def version_store(graph_store):
    """Create VersionStore with graph support."""
    if settings.graph_first:
        return VersionStore(
            path=settings.version_store_path,
            graph_store=graph_store,
            graph_first=True
        )
    else:
        return VersionStore(
            path=settings.version_store_path,
            graph_store=graph_store,
            graph_first=False
        )


@pytest.fixture
def sample_canonical_model():
    """Sample canonical model for testing."""
    return {
        "mapping_name": "M_TEST_PART1",
        "scd_type": "NONE",
        "incremental_keys": [],
        "sources": [
            {
                "name": "SQ_TEST",
                "table": "TEST_TABLE",
                "database": "test_db",
                "fields": [
                    {"name": "ID", "data_type": "STRING", "nullable": False},
                    {"name": "NAME", "data_type": "STRING", "nullable": True}
                ]
            }
        ],
        "targets": [
            {
                "name": "TGT_TEST",
                "table": "TEST_TARGET",
                "database": "test_db",
                "fields": []
            }
        ],
        "transformations": [
            {
                "name": "EXP_TEST",
                "type": "EXPRESSION",
                "ports": []
            }
        ],
        "connectors": [
            {
                "from_transformation": "SQ_TEST",
                "to_transformation": "EXP_TEST",
                "from_port": "*",
                "to_port": "*"
            }
        ]
    }


def test_part1_save_to_graph(graph_store, version_store, sample_canonical_model):
    """Test that Part 1 flow saves canonical model to graph."""
    mapping_name = sample_canonical_model["mapping_name"]
    
    # Simulate Part 1: Save to version store (which saves to graph if graph_first=True)
    version_store.save(mapping_name, sample_canonical_model)
    
    # Verify model is in graph
    loaded_from_graph = graph_store.load_mapping(mapping_name)
    assert loaded_from_graph is not None
    assert loaded_from_graph["mapping_name"] == mapping_name
    
    # Cleanup
    graph_store.delete_mapping(mapping_name)
    version_store.delete(mapping_name)


def test_part1_enhancement_saves_to_graph(graph_store, version_store, sample_canonical_model):
    """Test that enhanced canonical model is saved to graph."""
    from ai_agents.agent_orchestrator import AgentOrchestrator
    
    mapping_name = sample_canonical_model["mapping_name"]
    orchestrator = AgentOrchestrator()
    
    # Simulate Part 1 with enhancement
    enhanced_result = orchestrator.process_with_enhancement(
        sample_canonical_model,
        enable_enhancement=True
    )
    enhanced_model = enhanced_result.get("canonical_model", sample_canonical_model)
    
    # Save enhanced model
    version_store.save(mapping_name, enhanced_model)
    
    # Verify enhanced model is in graph
    loaded_from_graph = graph_store.load_mapping(mapping_name)
    assert loaded_from_graph is not None
    assert loaded_from_graph["mapping_name"] == mapping_name
    
    # Verify enhancement metadata exists
    assert "_provenance" in loaded_from_graph or "_optimization_hint" in str(loaded_from_graph)
    
    # Cleanup
    graph_store.delete_mapping(mapping_name)
    version_store.delete(mapping_name)


def test_part2_loads_from_graph(graph_store, version_store, sample_canonical_model):
    """Test that Part 2 (code generation) loads from graph."""
    mapping_name = sample_canonical_model["mapping_name"]
    
    # Part 1: Save to graph
    version_store.save(mapping_name, sample_canonical_model)
    
    # Part 2: Load from graph (simulating code generator)
    loaded_model = version_store.load(mapping_name)
    assert loaded_model is not None
    assert loaded_model["mapping_name"] == mapping_name
    
    # Verify it came from graph (if graph_first=True)
    if settings.graph_first:
        # Model should be loaded from graph
        graph_model = graph_store.load_mapping(mapping_name)
        assert graph_model is not None
        assert graph_model["mapping_name"] == mapping_name
    
    # Cleanup
    graph_store.delete_mapping(mapping_name)
    version_store.delete(mapping_name)

