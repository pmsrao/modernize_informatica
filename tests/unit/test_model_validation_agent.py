"""Unit tests for Model Validation Agent."""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from ai_agents.model_validation_agent import ModelValidationAgent


@pytest.fixture
def valid_canonical_model():
    """Valid canonical model for testing."""
    return {
        "mapping_name": "M_TEST",
        "sources": [
            {
                "name": "SQ_CUSTOMER",
                "table": "CUSTOMER_SRC",
                "fields": []
            }
        ],
        "targets": [
            {
                "name": "TGT_CUSTOMER",
                "table": "CUSTOMER_TGT",
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
        "connectors": []
    }


@pytest.fixture
def enhanced_model():
    """Enhanced canonical model for testing."""
    return {
        "mapping_name": "M_TEST",
        "sources": [
            {
                "name": "SQ_CUSTOMER",
                "table": "CUSTOMER_SRC",
                "fields": [
                    {"name": "CUSTOMER_ID", "data_type": "STRING"}
                ]
            }
        ],
        "targets": [
            {
                "name": "TGT_CUSTOMER",
                "table": "CUSTOMER_TGT",
                "fields": []
            }
        ],
        "transformations": [
            {
                "name": "EXP_DERIVE",
                "type": "EXPRESSION",
                "_optimization_hint": "consider_splitting",
                "ports": []
            }
        ],
        "connectors": [],
        "_provenance": {
            "enhanced_at": "2024-01-01T00:00:00",
            "enhancement_agent": "ModelEnhancementAgent"
        },
        "_data_quality_rules": [],
        "_performance_metadata": {
            "complexity": "LOW"
        }
    }


@pytest.fixture
def validation_agent():
    """Create validation agent instance."""
    return ModelValidationAgent()


class TestModelValidationAgent:
    """Test cases for Model Validation Agent."""
    
    def test_validate_valid_model(self, validation_agent, valid_canonical_model):
        """Test validation of valid model."""
        result = validation_agent.validate(valid_canonical_model)
        
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
    
    def test_validate_invalid_model(self, validation_agent):
        """Test validation of invalid model."""
        invalid_model = {}  # Missing required fields
        
        result = validation_agent.validate(invalid_model)
        
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0
    
    def test_validate_schema(self, validation_agent, valid_canonical_model):
        """Test schema validation."""
        result = validation_agent._validate_schema(valid_canonical_model)
        
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
    
    def test_validate_schema_missing_fields(self, validation_agent):
        """Test schema validation with missing fields."""
        invalid_model = {"sources": []}  # Missing mapping_name
        
        result = validation_agent._validate_schema(invalid_model)
        
        assert result["is_valid"] is False
        assert any("mapping_name" in error for error in result["errors"])
    
    def test_check_consistency(self, validation_agent, valid_canonical_model):
        """Test consistency checking."""
        result = validation_agent._check_consistency(valid_canonical_model)
        
        assert result["is_valid"] is True
    
    def test_check_consistency_duplicate_names(self, validation_agent):
        """Test consistency check with duplicate transformation names."""
        model_with_duplicates = {
            "mapping_name": "M_TEST",
            "transformations": [
                {"name": "EXP1", "type": "EXPRESSION"},
                {"name": "EXP1", "type": "EXPRESSION"}  # Duplicate
            ]
        }
        
        result = validation_agent._check_consistency(model_with_duplicates)
        
        assert result["is_valid"] is False
        assert any("duplicate" in error.lower() for error in result["errors"])
    
    def test_compare_models(self, validation_agent, valid_canonical_model, enhanced_model):
        """Test model comparison."""
        result = validation_agent._compare_models(valid_canonical_model, enhanced_model)
        
        assert "breaking_changes" in result
        assert "non_breaking_changes" in result
        assert len(result["non_breaking_changes"]) > 0  # Should have enhancement fields
    
    def test_validate_with_original_comparison(self, validation_agent, valid_canonical_model, enhanced_model):
        """Test validation with original model comparison."""
        result = validation_agent.validate(enhanced_model, valid_canonical_model)
        
        assert "validation_details" in result
        assert "diff_analysis" in result["validation_details"]
    
    def test_check_enhancement_quality(self, validation_agent, enhanced_model):
        """Test enhancement quality checking."""
        result = validation_agent._check_enhancement_quality(enhanced_model)
        
        assert "is_valid" in result
        assert "confidence_score" in result
        assert "enhancements_count" in result
    
    def test_validate_rollback_recommendation(self, validation_agent):
        """Test rollback recommendation logic."""
        # Model with many errors should recommend rollback
        invalid_model = {
            "mapping_name": "M_TEST",
            "transformations": [
                {"name": "T1", "type": "EXPRESSION"},
                {"name": "T1", "type": "EXPRESSION"}  # Duplicate
            ]
        }
        
        result = validation_agent.validate(invalid_model)
        
        assert result["rollback_recommended"] is True
    
    def test_validate_handles_missing_provenance(self, validation_agent, valid_canonical_model):
        """Test validation handles models without provenance."""
        result = validation_agent.validate(valid_canonical_model)
        
        # Should still validate successfully
        assert result["is_valid"] is True

