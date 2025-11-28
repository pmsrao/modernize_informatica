"""Unit tests for Model Enhancement Agent."""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from ai_agents.model_enhancement_agent import ModelEnhancementAgent


@pytest.fixture
def sample_canonical_model():
    """Sample canonical model for testing."""
    return {
        "mapping_name": "M_TEST",
        "sources": [
            {
                "name": "SQ_CUSTOMER",
                "table": "CUSTOMER_SRC",
                "database": "source_db",
                "fields": [
                    {"name": "CUSTOMER_ID"},
                    {"name": "FIRST_NAME"},
                    {"name": "ORDER_DATE"},
                    {"name": "ORDER_AMT"}
                ]
            }
        ],
        "targets": [
            {
                "name": "TGT_CUSTOMER",
                "table": "CUSTOMER_TGT",
                "fields": [
                    {"name": "CUSTOMER_ID"},
                    {"name": "FULL_NAME"}
                ]
            }
        ],
        "transformations": [
            {
                "name": "EXP_DERIVE",
                "type": "EXPRESSION",
                "ports": [
                    {
                        "name": "FULL_NAME",
                        "port_type": "OUTPUT",
                        "expression": "FIRST_NAME || ' ' || LAST_NAME"
                    }
                ]
            },
            {
                "name": "LK_REGION",
                "type": "LOOKUP",
                "ports": []
            },
            {
                "name": "AGG_SALES",
                "type": "AGGREGATOR",
                "group_by_ports": ["CUSTOMER_ID"],
                "ports": []
            },
            {
                "name": "FILTER_ACTIVE",
                "type": "FILTER",
                "ports": []
            }
        ],
        "connectors": []
    }


@pytest.fixture
def enhancement_agent():
    """Create enhancement agent instance."""
    return ModelEnhancementAgent(use_llm=False)


class TestModelEnhancementAgent:
    """Test cases for Model Enhancement Agent."""
    
    def test_enhance_adds_data_types(self, enhancement_agent, sample_canonical_model):
        """Test that enhancement adds missing data types."""
        enhanced = enhancement_agent.enhance(sample_canonical_model)
        
        # Check that data types were inferred
        source_fields = enhanced["sources"][0]["fields"]
        date_field = next((f for f in source_fields if "DATE" in f["name"]), None)
        assert date_field is not None
        assert "data_type" in date_field
        assert date_field["data_type"] == "TIMESTAMP"
    
    def test_enhance_adds_optimization_hints(self, enhancement_agent, sample_canonical_model):
        """Test that enhancement adds optimization hints."""
        enhanced = enhancement_agent.enhance(sample_canonical_model)
        
        # Check lookup has broadcast hint
        lookup_trans = next((t for t in enhanced["transformations"] if t["name"] == "LK_REGION"), None)
        assert lookup_trans is not None
        assert "_optimization_hint" in lookup_trans
        assert lookup_trans["_optimization_hint"] == "broadcast_join"
        
        # Check aggregator has partition hint
        agg_trans = next((t for t in enhanced["transformations"] if t["name"] == "AGG_SALES"), None)
        assert agg_trans is not None
        assert "_optimization_hint" in agg_trans
        assert agg_trans["_optimization_hint"] == "partition_by_group_by"
        
        # Check filter has pushdown hint
        filter_trans = next((t for t in enhanced["transformations"] if t["name"] == "FILTER_ACTIVE"), None)
        assert filter_trans is not None
        assert "_optimization_hint" in filter_trans
        assert filter_trans["_optimization_hint"] == "filter_pushdown"
    
    def test_enhance_adds_data_quality_rules(self, enhancement_agent, sample_canonical_model):
        """Test that enhancement adds data quality rules."""
        enhanced = enhancement_agent.enhance(sample_canonical_model)
        
        assert "_data_quality_rules" in enhanced
        assert isinstance(enhanced["_data_quality_rules"], list)
        
        # Check for NOT_NULL rule on key field
        key_rules = [r for r in enhanced["_data_quality_rules"] if "CUSTOMER_ID" in r.get("field", "")]
        assert len(key_rules) > 0
    
    def test_enhance_adds_performance_metadata(self, enhancement_agent, sample_canonical_model):
        """Test that enhancement adds performance metadata."""
        enhanced = enhancement_agent.enhance(sample_canonical_model)
        
        assert "_performance_metadata" in enhanced
        assert "complexity" in enhanced["_performance_metadata"]
        assert "estimated_runtime" in enhanced["_performance_metadata"]
    
    def test_enhance_adds_provenance(self, enhancement_agent, sample_canonical_model):
        """Test that enhancement adds provenance tracking."""
        enhanced = enhancement_agent.enhance(sample_canonical_model)
        
        assert "_provenance" in enhanced
        provenance = enhanced["_provenance"]
        assert "original_model_hash" in provenance
        assert "enhanced_model_hash" in provenance
        assert "enhanced_at" in provenance
        assert "enhancement_agent" in provenance
        assert provenance["enhancement_agent"] == "ModelEnhancementAgent"
    
    def test_enhance_tracks_changes(self, enhancement_agent, sample_canonical_model):
        """Test that enhancement tracks applied changes."""
        enhanced = enhancement_agent.enhance(sample_canonical_model)
        
        assert "_enhancements_applied" in enhanced
        assert isinstance(enhanced["_enhancements_applied"], list)
        assert len(enhanced["_enhancements_applied"]) > 0
    
    def test_enhance_preserves_original_structure(self, enhancement_agent, sample_canonical_model):
        """Test that enhancement preserves original model structure."""
        enhanced = enhancement_agent.enhance(sample_canonical_model)
        
        # Original fields should still be present
        assert "mapping_name" in enhanced
        assert enhanced["mapping_name"] == "M_TEST"
        assert "sources" in enhanced
        assert "targets" in enhanced
        assert "transformations" in enhanced
        assert len(enhanced["transformations"]) == len(sample_canonical_model["transformations"])
    
    def test_enhance_handles_empty_model(self, enhancement_agent):
        """Test that enhancement handles edge cases."""
        empty_model = {"mapping_name": "EMPTY"}
        
        # Empty model should still be enhanced (just with minimal enhancements)
        enhanced = enhancement_agent.enhance(empty_model)
        assert enhanced["mapping_name"] == "EMPTY"
        assert "_provenance" in enhanced
    
    def test_infer_data_type_patterns(self, enhancement_agent):
        """Test data type inference patterns."""
        assert enhancement_agent._infer_data_type("ORDER_DATE") == "TIMESTAMP"
        assert enhancement_agent._infer_data_type("CUSTOMER_ID") == "STRING"
        assert enhancement_agent._infer_data_type("ORDER_AMT") == "DECIMAL"
        assert enhancement_agent._infer_data_type("ORDER_COUNT") == "INTEGER"
        assert enhancement_agent._infer_data_type("IS_ACTIVE") == "BOOLEAN"
        assert enhancement_agent._infer_data_type("UNKNOWN_FIELD") is None

