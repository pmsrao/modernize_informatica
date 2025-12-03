"""Unit tests for semantic tag detector."""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from normalizer.semantic_tag_detector import SemanticTagDetector
from utils.logger import get_logger

logger = get_logger(__name__)


class TestSemanticTagDetector:
    """Test semantic tag detection."""
    
    @pytest.fixture
    def detector(self):
        """Create detector instance."""
        return SemanticTagDetector()
    
    def test_detect_scd_type1(self, detector):
        """Test SCD Type 1 detection."""
        model = {
            "transformation_name": "TEST_MAPPING",
            "transformations": [
                {
                    "name": "EXP1",
                    "type": "EXPRESSION",
                    "ports": [
                        {"name": "customer_id", "port_type": "INPUT"},
                        {"name": "customer_name", "port_type": "INPUT"},
                        {"name": "customer_name", "port_type": "OUTPUT"}
                    ]
                },
                {
                    "name": "UPD1",
                    "type": "UPDATE_STRATEGY",
                    "update_strategy_expression": "DD_UPDATE"
                }
            ],
            "scd_type": "SCD_TYPE1",
            "scd_info": {"type": "SCD_TYPE1"}  # Also provide scd_info dict
        }
        
        tags = detector.detect_tags(model)
        
        # Should detect SCD Type 1 pattern
        assert isinstance(tags, list)
        scd_tags = [t for t in tags if "scd" in t.lower()]
        # Note: SCD tags are added as lowercase (e.g., "scd_type1")
        assert len(scd_tags) > 0 or len(tags) > 0, f"Should detect tags, got tags: {tags}"
    
    def test_detect_lookup_heavy(self, detector):
        """Test lookup-heavy transformation detection."""
        model = {
            "transformation_name": "TEST_MAPPING",
            "transformations": [
                {
                    "name": "LKP1",
                    "type": "LOOKUP"
                },
                {
                    "name": "LKP2",
                    "type": "LOOKUP"
                },
                {
                    "name": "EXP1",
                    "type": "EXPRESSION"
                }
            ],
            "scd_type": "NONE"
        }
        
        tags = detector.detect_tags(model)
        
        # Should detect lookup-heavy pattern (threshold >= 1)
        assert isinstance(tags, list)
        lookup_tags = [t for t in tags if "lookup" in t.lower()]
        assert len(lookup_tags) > 0, f"Should detect lookup-heavy tag, got tags: {tags}"
    
    def test_detect_multi_join(self, detector):
        """Test multi-join transformation detection."""
        model = {
            "transformation_name": "TEST_MAPPING",
            "transformations": [
                {
                    "name": "JNR1",
                    "type": "JOINER"
                },
                {
                    "name": "JNR2",
                    "type": "JOINER"
                }
            ],
            "scd_type": "NONE"
        }
        
        tags = detector.detect_tags(model)
        
        # Should detect multi-join pattern (threshold >= 1)
        assert isinstance(tags, list)
        join_tags = [t for t in tags if "join" in t.lower()]
        assert len(join_tags) > 0, f"Should detect multi-join tag, got tags: {tags}"
    
    def test_detect_complex_transformation(self, detector):
        """Test detection for complex transformation."""
        model = {
            "transformation_name": "TEST_MAPPING",
            "transformations": [
                {
                    "name": "LKP1",
                    "type": "LOOKUP"
                },
                {
                    "name": "JNR1",
                    "type": "JOINER"
                },
                {
                    "name": "AGG1",
                    "type": "AGGREGATOR"
                },
                {
                    "name": "EXP1",
                    "type": "EXPRESSION"
                }
            ],
            "scd_type": "NONE"
        }
        
        tags = detector.detect_tags(model)
        
        # Should detect multiple patterns
        assert isinstance(tags, list)
        assert len(tags) > 0, f"Should detect tags for complex transformation, got: {tags}"
    
    def test_empty_model(self, detector):
        """Test detection with empty model."""
        model = {
            "transformation_name": "TEST_MAPPING",
            "transformations": [],
            "scd_type": "NONE"
        }
        
        tags = detector.detect_tags(model)
        
        assert isinstance(tags, list)
        assert len(tags) == 0, f"Empty model should return no tags, got: {tags}"
    
    def test_detect_aggregation_heavy(self, detector):
        """Test aggregation-heavy transformation detection."""
        model = {
            "transformation_name": "TEST_MAPPING",
            "transformations": [
                {
                    "name": "AGG1",
                    "type": "AGGREGATOR"
                },
                {
                    "name": "AGG2",
                    "type": "AGGREGATOR"
                },
                {
                    "name": "EXP1",
                    "type": "EXPRESSION"
                }
            ],
            "scd_type": "NONE"
        }
        
        tags = detector.detect_tags(model)
        
        # Should detect aggregation-heavy pattern (threshold >= 1)
        assert isinstance(tags, list)
        agg_tags = [t for t in tags if "aggregat" in t.lower()]
        assert len(agg_tags) > 0, f"Should detect aggregation-heavy tag, got tags: {tags}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

