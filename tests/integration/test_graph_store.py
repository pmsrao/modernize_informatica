"""Integration tests for GraphStore."""
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
from src.graph.graph_sync import GraphSync
from src.config import settings


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
def sample_model():
    """Sample canonical model for testing."""
    return {
        "mapping_name": "M_TEST_MIGRATION",
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


def test_save_and_load_mapping(graph_store, sample_model):
    """Test saving and loading mapping."""
    # Save
    mapping_name = graph_store.save_mapping(sample_model)
    assert mapping_name == "M_TEST_MIGRATION"
    
    # Load
    loaded = graph_store.load_mapping("M_TEST_MIGRATION")
    assert loaded is not None
    assert loaded["mapping_name"] == "M_TEST_MIGRATION"
    assert len(loaded["sources"]) == 1
    assert len(loaded["targets"]) == 1
    assert len(loaded["transformations"]) == 1
    
    # Cleanup
    graph_store.delete_mapping("M_TEST_MIGRATION")


def test_query_mappings_using_table(graph_store, sample_model):
    """Test querying mappings by table."""
    # Save mapping
    graph_store.save_mapping(sample_model)
    
    # Query
    mappings = graph_store.query_mappings_using_table("TEST_TABLE", "test_db")
    assert "M_TEST_MIGRATION" in mappings
    
    # Cleanup
    graph_store.delete_mapping("M_TEST_MIGRATION")


def test_list_all_mappings(graph_store, sample_model):
    """Test listing all mappings."""
    # Save mapping
    graph_store.save_mapping(sample_model)
    
    # List
    mappings = graph_store.list_all_mappings()
    assert "M_TEST_MIGRATION" in mappings
    
    # Cleanup
    graph_store.delete_mapping("M_TEST_MIGRATION")


def test_delete_mapping(graph_store, sample_model):
    """Test deleting mapping."""
    # Save
    graph_store.save_mapping(sample_model)
    
    # Delete
    deleted = graph_store.delete_mapping("M_TEST_MIGRATION")
    assert deleted is True
    
    # Verify deleted
    loaded = graph_store.load_mapping("M_TEST_MIGRATION")
    assert loaded is None

