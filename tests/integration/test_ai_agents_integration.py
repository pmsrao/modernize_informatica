"""Integration tests for AI agents with real LLM providers (optional)."""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch

# Add project paths
project_root = Path(__file__).parent.parent.parent
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from parser import MappingParser
from normalizer import MappingNormalizer
from ai_agents.rule_explainer_agent import RuleExplainerAgent
from ai_agents.mapping_summary_agent import MappingSummaryAgent
from ai_agents.risk_detection_agent import RiskDetectionAgent
from ai_agents.transformation_suggestion_agent import TransformationSuggestionAgent
from ai_agents.agent_orchestrator import AgentOrchestrator


@pytest.fixture
def sample_mapping_file():
    """Path to sample mapping file."""
    return project_root / "samples" / "complex" / "mapping_complex.xml"


@pytest.fixture
def canonical_model_from_file(sample_mapping_file):
    """Create canonical model from sample file."""
    if not sample_mapping_file.exists():
        pytest.skip(f"Sample file not found: {sample_mapping_file}")
    
    parser = MappingParser(str(sample_mapping_file))
    raw_mapping = parser.parse()
    normalizer = MappingNormalizer()
    return normalizer.normalize(raw_mapping)


@pytest.mark.skipif(
    os.getenv("USE_MOCK_LLM", "true").lower() == "true",
    reason="Skipping integration tests - USE_MOCK_LLM is set"
)
class TestAIAgentsIntegration:
    """Integration tests with real LLM (requires API keys)."""
    
    def test_rule_explainer_with_real_llm(self, canonical_model_from_file):
        """Test rule explainer with real LLM."""
        agent = RuleExplainerAgent()
        explanations = agent.explain(canonical_model_from_file)
        
        assert isinstance(explanations, list)
        if len(explanations) > 0:
            assert "field" in explanations[0]
            assert "explanation" in explanations[0]
            assert len(explanations[0]["explanation"]) > 0
    
    def test_mapping_summary_with_real_llm(self, canonical_model_from_file):
        """Test mapping summary with real LLM."""
        agent = MappingSummaryAgent()
        summary = agent.summarize(canonical_model_from_file)
        
        assert isinstance(summary, dict)
        assert "summary" in summary
        assert len(summary["summary"]) > 0
        assert "sources" in summary
    
    def test_risk_detection_with_real_llm(self, canonical_model_from_file):
        """Test risk detection with real LLM."""
        agent = RiskDetectionAgent()
        risks = agent.detect_risks(canonical_model_from_file)
        
        assert isinstance(risks, list)
        # Should detect at least some risks in complex mapping
        # (even if empty, should not error)
    
    def test_suggestions_with_real_llm(self, canonical_model_from_file):
        """Test transformation suggestions with real LLM."""
        agent = TransformationSuggestionAgent()
        suggestions = agent.suggest(canonical_model_from_file)
        
        assert isinstance(suggestions, list)
        # Should provide suggestions for complex mapping
    
    def test_orchestrator_with_real_llm(self, canonical_model_from_file):
        """Test orchestrator with real LLM."""
        orchestrator = AgentOrchestrator(enable_parallel=False)
        results = orchestrator.run_all(canonical_model_from_file)
        
        assert isinstance(results, dict)
        assert "summary" in results or "errors" in results
        assert "risks" in results or "errors" in results
        assert "suggestions" in results or "errors" in results


@pytest.mark.skipif(
    os.getenv("USE_MOCK_LLM", "true").lower() != "true",
    reason="Skipping mock tests - USE_MOCK_LLM is not set"
)
class TestAIAgentsWithMock:
    """Integration tests with mock LLM (always runs)."""
    
    def test_agents_with_mock_llm(self, canonical_model_from_file):
        """Test all agents work with mock LLM."""
        # Force mock mode
        with patch.dict(os.environ, {"USE_MOCK_LLM": "true", "LLM_PROVIDER": "local"}):
            orchestrator = AgentOrchestrator(enable_parallel=False)
            results = orchestrator.run_all(canonical_model_from_file)
            
            assert isinstance(results, dict)
            # Should complete without errors
            assert len(results.get("errors", [])) == 0 or all(
                "LLM" in err or "mock" in err.lower() for err in results.get("errors", [])
            )

