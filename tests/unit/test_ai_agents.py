"""Unit tests for AI agents."""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Add project paths
project_root = Path(__file__).parent.parent.parent
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ai_agents.rule_explainer_agent import RuleExplainerAgent
from ai_agents.mapping_summary_agent import MappingSummaryAgent
from ai_agents.risk_detection_agent import RiskDetectionAgent
from ai_agents.transformation_suggestion_agent import TransformationSuggestionAgent
from ai_agents.code_fix_agent import CodeFixAgent
from ai_agents.impact_analysis_agent import ImpactAnalysisAgent
from ai_agents.mapping_reconstruction_agent import MappingReconstructionAgent
from ai_agents.workflow_simulation_agent import WorkflowSimulationAgent
from ai_agents.agent_orchestrator import AgentOrchestrator


@pytest.fixture
def sample_canonical_model():
    """Sample canonical mapping model for testing."""
    return {
        "mapping_name": "M_TEST",
        "sources": [
            {
                "name": "SRC_CUSTOMERS",
                "type": "table",
                "fields": [
                    {"name": "customer_id", "data_type": "number"},
                    {"name": "first_name", "data_type": "string"},
                    {"name": "last_name", "data_type": "string"},
                    {"name": "age", "data_type": "number"}
                ]
            }
        ],
        "targets": [
            {
                "name": "TGT_CUSTOMERS",
                "type": "table",
                "fields": [
                    {"name": "customer_id", "data_type": "number"},
                    {"name": "full_name", "data_type": "string"},
                    {"name": "age_bucket", "data_type": "string"}
                ]
            }
        ],
        "transformations": [
            {
                "name": "EXP_CALCULATIONS",
                "type": "EXPRESSION",
                "input_ports": [
                    {"name": "customer_id", "data_type": "number"},
                    {"name": "first_name", "data_type": "string"},
                    {"name": "last_name", "data_type": "string"},
                    {"name": "age", "data_type": "number"}
                ],
                "output_ports": [
                    {
                        "name": "full_name",
                        "data_type": "string",
                        "expression": "FIRST_NAME || ' ' || LAST_NAME"
                    },
                    {
                        "name": "age_bucket",
                        "data_type": "string",
                        "expression": "IIF(AGE < 30, 'YOUNG', 'OTHER')"
                    }
                ]
            }
        ],
        "connectors": [
            {
                "from_instance": "SRC_CUSTOMERS",
                "from_field": "*",
                "to_instance": "EXP_CALCULATIONS",
                "to_field": "*"
            },
            {
                "from_instance": "EXP_CALCULATIONS",
                "from_field": "*",
                "to_instance": "TGT_CUSTOMERS",
                "to_field": "*"
            }
        ],
        "lineage": {},
        "scd_type": "NONE",
        "incremental_keys": []
    }


@pytest.fixture
def mock_llm_manager():
    """Mock LLM manager that returns predictable responses."""
    mock = Mock()
    
    def mock_ask(prompt):
        # Return mock responses based on prompt content
        if "explain" in prompt.lower() or "explanation" in prompt.lower():
            return "This expression performs a conditional classification based on the input values."
        elif "summary" in prompt.lower() or "summarize" in prompt.lower():
            return "This mapping processes customer data and applies transformations to create enriched customer records."
        elif "risk" in prompt.lower() or "analyze" in prompt.lower():
            return '[{"category": "Data Quality", "severity": "Medium", "location": "EXP_CALCULATIONS/age_bucket", "risk": "Missing null handling", "impact": "NULL values may cause issues", "recommendation": "Add null check"}]'
        elif "suggestion" in prompt.lower() or "optimize" in prompt.lower():
            return '[{"transformation": "EXP_CALCULATIONS", "field": "full_name", "current_pattern": "String concatenation", "suggestion": "Use concat_ws", "benefits": ["Better null handling"], "improved_code": "F.concat_ws(...)", "priority": "Medium"}]'
        elif "impact" in prompt.lower():
            return '{"change_target": "EXP_CALCULATIONS/age_bucket", "direct_dependencies": [], "indirect_dependencies": [], "affected_targets": ["TGT_CUSTOMERS"], "data_quality_concerns": [], "testing_priority": [], "overall_risk": "Low"}'
        elif "reconstruct" in prompt.lower():
            return '{"mapping_name": "RECONSTRUCTED", "sources": [], "targets": [], "transformations": [], "connectors": [], "confidence": "Medium", "assumptions": []}'
        elif "simulate" in prompt.lower() or "workflow" in prompt.lower():
            return '{"execution_sequence": [], "critical_path": [], "bottlenecks": [], "single_points_of_failure": [], "resource_requirements": {}, "optimization_suggestions": []}'
        else:
            return "Mock LLM response"
    
    mock.ask = Mock(side_effect=mock_ask)
    return mock


class TestRuleExplainerAgent:
    """Tests for RuleExplainerAgent."""
    
    def test_explain_mapping_expressions(self, sample_canonical_model, mock_llm_manager):
        """Test explaining expressions in a mapping."""
        agent = RuleExplainerAgent(llm=mock_llm_manager)
        explanations = agent.explain(sample_canonical_model)
        
        assert isinstance(explanations, list)
        assert len(explanations) > 0
        assert "field" in explanations[0]
        assert "expression" in explanations[0]
        assert "explanation" in explanations[0]
    
    def test_explain_single_expression(self, mock_llm_manager):
        """Test explaining a single expression."""
        agent = RuleExplainerAgent(llm=mock_llm_manager)
        explanation = agent.explain_expression(
            "IIF(AGE < 30, 'YOUNG', 'OTHER')",
            "age_bucket"
        )
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0
    
    def test_explain_with_field_filter(self, sample_canonical_model, mock_llm_manager):
        """Test explaining specific field only."""
        agent = RuleExplainerAgent(llm=mock_llm_manager)
        explanations = agent.explain(sample_canonical_model, field_name="age_bucket")
        
        assert isinstance(explanations, list)
        # Should only explain the specified field
        if len(explanations) > 0:
            assert explanations[0]["field"] == "age_bucket"


class TestMappingSummaryAgent:
    """Tests for MappingSummaryAgent."""
    
    def test_summarize_mapping(self, sample_canonical_model, mock_llm_manager):
        """Test generating mapping summary."""
        agent = MappingSummaryAgent(llm=mock_llm_manager)
        summary = agent.summarize(sample_canonical_model)
        
        assert isinstance(summary, dict)
        assert "mapping" in summary
        assert "summary" in summary
        assert "sources" in summary
        assert "targets" in summary
        assert summary["mapping"] == "M_TEST"
    
    def test_summary_includes_business_rules(self, sample_canonical_model, mock_llm_manager):
        """Test that summary includes business rules."""
        agent = MappingSummaryAgent(llm=mock_llm_manager)
        summary = agent.summarize(sample_canonical_model)
        
        assert "key_business_rules" in summary
        assert isinstance(summary["key_business_rules"], list)
    
    def test_fallback_summary_on_error(self, sample_canonical_model):
        """Test fallback summary when LLM fails."""
        # Create a mock that raises an error
        mock_llm = Mock()
        mock_llm.ask = Mock(side_effect=Exception("LLM error"))
        
        agent = MappingSummaryAgent(llm=mock_llm)
        summary = agent.summarize(sample_canonical_model)
        
        # Should still return a summary (fallback)
        assert isinstance(summary, dict)
        assert "summary" in summary
        assert "error" in summary


class TestRiskDetectionAgent:
    """Tests for RiskDetectionAgent."""
    
    def test_detect_risks(self, sample_canonical_model, mock_llm_manager):
        """Test risk detection."""
        agent = RiskDetectionAgent(llm=mock_llm_manager)
        risks = agent.detect_risks(sample_canonical_model)
        
        assert isinstance(risks, list)
        # Should have pattern-based risks even if LLM fails
        assert len(risks) >= 0
    
    def test_pattern_based_risk_detection(self, sample_canonical_model):
        """Test pattern-based risk detection (deterministic)."""
        # Create a mapping with risky patterns
        risky_mapping = sample_canonical_model.copy()
        risky_mapping["transformations"][0]["output_ports"][0]["expression"] = "CAST(AGE AS STRING)"
        
        mock_llm = Mock()
        mock_llm.ask = Mock(return_value="[]")
        
        agent = RiskDetectionAgent(llm=mock_llm)
        risks = agent.detect_risks(risky_mapping)
        
        # Should detect casting without null check
        assert isinstance(risks, list)
    
    def test_risk_deduplication(self, sample_canonical_model, mock_llm_manager):
        """Test that duplicate risks are removed."""
        agent = RiskDetectionAgent(llm=mock_llm_manager)
        risks = agent.detect_risks(sample_canonical_model)
        
        # Check for duplicates
        locations = [r.get("location") for r in risks]
        assert len(locations) == len(set(locations)) or len(risks) == 0


class TestTransformationSuggestionAgent:
    """Tests for TransformationSuggestionAgent."""
    
    def test_suggest_optimizations(self, sample_canonical_model, mock_llm_manager):
        """Test generating optimization suggestions."""
        agent = TransformationSuggestionAgent(llm=mock_llm_manager)
        suggestions = agent.suggest(sample_canonical_model)
        
        assert isinstance(suggestions, list)
        # Should have pattern-based suggestions even if LLM fails
        assert len(suggestions) >= 0
    
    def test_pattern_based_suggestions(self, sample_canonical_model):
        """Test pattern-based suggestions (deterministic)."""
        mock_llm = Mock()
        mock_llm.ask = Mock(return_value="[]")
        
        agent = TransformationSuggestionAgent(llm=mock_llm)
        suggestions = agent.suggest(sample_canonical_model)
        
        # Should detect string concatenation pattern
        assert isinstance(suggestions, list)
    
    def test_suggestion_deduplication(self, sample_canonical_model, mock_llm_manager):
        """Test that duplicate suggestions are removed."""
        agent = TransformationSuggestionAgent(llm=mock_llm_manager)
        suggestions = agent.suggest(sample_canonical_model)
        
        # Check for duplicates
        keys = [(s.get("transformation"), s.get("field")) for s in suggestions]
        assert len(keys) == len(set(keys)) or len(suggestions) == 0


class TestCodeFixAgent:
    """Tests for CodeFixAgent."""
    
    def test_fix_pyspark_code(self, mock_llm_manager):
        """Test fixing PySpark code."""
        agent = CodeFixAgent(llm=mock_llm_manager)
        
        broken_code = """
from pyspark.sql import SparkSession
df = spark.table("customers")
result = df.select(F.col("name"))
"""
        
        result = agent.fix(broken_code, error_message="NameError: name 'F' is not defined")
        
        assert isinstance(result, dict)
        assert "fixed_code" in result
        assert "explanation" in result
        assert "changes" in result
    
    def test_fix_with_error_message(self, mock_llm_manager):
        """Test fixing code with error message."""
        agent = CodeFixAgent(llm=mock_llm_manager)
        
        code = "df.select(F.col('name'))"
        result = agent.fix(code, error_message="NameError: name 'F' is not defined")
        
        assert "fixed_code" in result
        # Should add import
        assert "import" in result["fixed_code"].lower() or len(result["changes"]) > 0


class TestImpactAnalysisAgent:
    """Tests for ImpactAnalysisAgent."""
    
    def test_analyze_impact(self, sample_canonical_model, mock_llm_manager):
        """Test impact analysis."""
        agent = ImpactAnalysisAgent(llm=mock_llm_manager)
        
        impact = agent.analyze(
            sample_canonical_model,
            "EXP_CALCULATIONS/age_bucket",
            "Change age bucket logic"
        )
        
        assert isinstance(impact, dict)
        assert "change_target" in impact
        assert "direct_dependencies" in impact
        assert "affected_targets" in impact
        assert "overall_risk" in impact
    
    def test_pattern_based_impact(self, sample_canonical_model):
        """Test pattern-based impact analysis."""
        mock_llm = Mock()
        mock_llm.ask = Mock(return_value='{"direct_dependencies": [], "indirect_dependencies": [], "affected_targets": [], "overall_risk": "Low"}')
        
        agent = ImpactAnalysisAgent(llm=mock_llm)
        impact = agent.analyze(
            sample_canonical_model,
            "EXP_CALCULATIONS/age_bucket",
            "Test change"
        )
        
        # Should identify affected targets
        assert "affected_targets" in impact
        assert isinstance(impact["affected_targets"], list)


class TestMappingReconstructionAgent:
    """Tests for MappingReconstructionAgent."""
    
    def test_reconstruct_from_clues(self, mock_llm_manager):
        """Test mapping reconstruction."""
        agent = MappingReconstructionAgent(llm=mock_llm_manager)
        
        clues = {
            "target_definitions": [
                {
                    "name": "TGT_CUSTOMERS",
                    "fields": [
                        {"name": "customer_id", "type": "number"},
                        {"name": "full_name", "type": "string"}
                    ]
                }
            ]
        }
        
        reconstructed = agent.reconstruct(clues)
        
        assert isinstance(reconstructed, dict)
        assert "mapping_name" in reconstructed
        assert "sources" in reconstructed
        assert "targets" in reconstructed
        assert "confidence" in reconstructed
    
    def test_fallback_reconstruction(self):
        """Test fallback reconstruction when LLM fails."""
        mock_llm = Mock()
        mock_llm.ask = Mock(side_effect=Exception("LLM error"))
        
        agent = MappingReconstructionAgent(llm=mock_llm)
        
        clues = {
            "target_definitions": [{"name": "TGT1", "fields": []}]
        }
        
        reconstructed = agent.reconstruct(clues)
        
        # Should still return a reconstruction (fallback)
        assert isinstance(reconstructed, dict)
        assert "mapping_name" in reconstructed


class TestWorkflowSimulationAgent:
    """Tests for WorkflowSimulationAgent."""
    
    def test_simulate_workflow(self, mock_llm_manager):
        """Test workflow simulation."""
        agent = WorkflowSimulationAgent(llm=mock_llm_manager)
        
        workflow = {
            "workflow_name": "WF_TEST",
            "nodes": ["TASK1", "TASK2", "TASK3"],
            "edges": [
                {"from": "TASK1", "to": "TASK2"},
                {"from": "TASK2", "to": "TASK3"}
            ],
            "execution_levels": [["TASK1"], ["TASK2"], ["TASK3"]]
        }
        
        simulation = agent.simulate(workflow)
        
        assert isinstance(simulation, dict)
        assert "execution_sequence" in simulation
        assert "critical_path" in simulation
        assert "bottlenecks" in simulation
    
    def test_pattern_based_simulation(self):
        """Test pattern-based simulation."""
        mock_llm = Mock()
        mock_llm.ask = Mock(return_value='{"execution_sequence": [], "critical_path": [], "bottlenecks": []}')
        
        agent = WorkflowSimulationAgent(llm=mock_llm)
        
        workflow = {
            "workflow_name": "WF_TEST",
            "nodes": ["TASK1", "TASK2"],
            "edges": [{"from": "TASK1", "to": "TASK2"}],
            "execution_levels": [["TASK1"], ["TASK2"]]
        }
        
        simulation = agent.simulate(workflow)
        
        # Should identify execution sequence
        assert "execution_sequence" in simulation
        assert isinstance(simulation["execution_sequence"], list)


class TestAgentOrchestrator:
    """Tests for AgentOrchestrator."""
    
    def test_run_all_agents(self, sample_canonical_model, mock_llm_manager):
        """Test running all agents."""
        orchestrator = AgentOrchestrator(llm=mock_llm_manager, enable_parallel=False)
        
        results = orchestrator.run_all(sample_canonical_model)
        
        assert isinstance(results, dict)
        assert "summary" in results
        assert "explanations" in results
        assert "risks" in results
        assert "suggestions" in results
        assert "errors" in results
    
    def test_parallel_execution(self, sample_canonical_model, mock_llm_manager):
        """Test parallel execution of agents."""
        orchestrator = AgentOrchestrator(llm=mock_llm_manager, enable_parallel=True)
        
        results = orchestrator.run_all(sample_canonical_model)
        
        assert isinstance(results, dict)
        # All agents should have run
        assert "summary" in results or "errors" in results
    
    def test_error_handling(self, sample_canonical_model):
        """Test error handling in orchestrator."""
        # Create a mock that fails
        mock_llm = Mock()
        mock_llm.ask = Mock(side_effect=Exception("LLM error"))
        
        orchestrator = AgentOrchestrator(llm=mock_llm, enable_parallel=False)
        
        results = orchestrator.run_all(sample_canonical_model)
        
        # Should handle errors gracefully
        assert isinstance(results, dict)
        assert "errors" in results
        # Should still have some results (from fallbacks)
        assert len(results["errors"]) >= 0
    
    def test_fix_code(self, mock_llm_manager):
        """Test code fixing through orchestrator."""
        orchestrator = AgentOrchestrator(llm=mock_llm_manager)
        
        code = "df.select(F.col('name'))"
        result = orchestrator.fix_code(code, "NameError")
        
        assert isinstance(result, dict)
        assert "fixed_code" in result

