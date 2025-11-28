#!/usr/bin/env python3
"""Test AI agents directly."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from parser import MappingParser
from normalizer import MappingNormalizer
from ai_agents.rule_explainer_agent import RuleExplainerAgent
from ai_agents.mapping_summary_agent import MappingSummaryAgent
from ai_agents.risk_detection_agent import RiskDetectionAgent
from ai_agents.transformation_suggestion_agent import TransformationSuggestionAgent
from utils.logger import get_logger

logger = get_logger(__name__)


def test_ai_agents(mapping_file: str = "samples/simple/mapping_simple.xml"):
    """Test all AI agents.
    
    Args:
        mapping_file: Path to mapping XML file to test
    """
    
    # Parse and normalize a mapping
    print("=" * 80)
    print("STEP 1: Parse and Normalize Mapping")
    print("=" * 80)
    
    try:
        parser = MappingParser(mapping_file)
        mapping_data = parser.parse()
        
        normalizer = MappingNormalizer()
        canonical_model = normalizer.normalize(mapping_data)
        
        print(f"✅ Mapping parsed: {canonical_model.get('mapping_name')}")
        print(f"   Sources: {len(canonical_model.get('sources', []))}")
        print(f"   Targets: {len(canonical_model.get('targets', []))}")
        print(f"   Transformations: {len(canonical_model.get('transformations', []))}")
    except Exception as e:
        print(f"❌ Error parsing mapping: {e}")
        return
    
    # Test Rule Explainer Agent
    print("\n" + "=" * 80)
    print("STEP 2: Test Rule Explainer Agent")
    print("=" * 80)
    
    try:
        explainer = RuleExplainerAgent()
        expression = "IIF(AGE < 30, 'YOUNG', 'OTHER')"
        explanation = explainer.explain_expression(expression, "AGE_BUCKET", {})
        
        print(f"Expression: {expression}")
        print(f"Explanation: {explanation}")
        print(f"✅ Rule Explainer Agent working")
    except Exception as e:
        print(f"❌ Rule Explainer Agent failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test Mapping Summary Agent
    print("\n" + "=" * 80)
    print("STEP 3: Test Mapping Summary Agent")
    print("=" * 80)
    
    try:
        summary_agent = MappingSummaryAgent()
        summary = summary_agent.summarize(canonical_model)
        
        if isinstance(summary, dict):
            summary_text = summary.get('summary', str(summary))
        else:
            summary_text = str(summary)
        
        print(f"Summary: {summary_text[:300]}...")
        print(f"✅ Mapping Summary Agent working")
    except Exception as e:
        print(f"❌ Mapping Summary Agent failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test Risk Detection Agent
    print("\n" + "=" * 80)
    print("STEP 4: Test Risk Detection Agent")
    print("=" * 80)
    
    try:
        risk_agent = RiskDetectionAgent()
        risks = risk_agent.detect_risks(canonical_model)
        
        if isinstance(risks, dict):
            risk_list = risks.get('risks', [])
        else:
            risk_list = risks if isinstance(risks, list) else []
        
        print(f"Risks detected: {len(risk_list)}")
        for risk in risk_list[:3]:
            if isinstance(risk, dict):
                print(f"  - {risk.get('type', 'UNKNOWN')}: {risk.get('description', '')[:100]}")
            else:
                print(f"  - {risk}")
        print(f"✅ Risk Detection Agent working")
    except Exception as e:
        print(f"❌ Risk Detection Agent failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test Transformation Suggestion Agent
    print("\n" + "=" * 80)
    print("STEP 5: Test Transformation Suggestion Agent")
    print("=" * 80)
    
    try:
        suggestion_agent = TransformationSuggestionAgent()
        suggestions = suggestion_agent.suggest(canonical_model)
        
        if isinstance(suggestions, dict):
            suggestion_list = suggestions.get('suggestions', [])
        else:
            suggestion_list = suggestions if isinstance(suggestions, list) else []
        
        print(f"Suggestions: {len(suggestion_list)}")
        for suggestion in suggestion_list[:3]:
            if isinstance(suggestion, dict):
                print(f"  - {suggestion.get('type', 'UNKNOWN')}: {suggestion.get('description', '')[:100]}")
            else:
                print(f"  - {suggestion}")
        print(f"✅ Transformation Suggestion Agent working")
    except Exception as e:
        print(f"❌ Transformation Suggestion Agent failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("AI AGENTS TESTING COMPLETE")
    print("=" * 80)
    print("\n📋 Summary:")
    print("   - Check the output above to verify each agent is working")
    print("   - If any agent failed, check LLM configuration and API keys")
    print("   - See test_end_to_end.md for detailed testing guide")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test AI agents")
    parser.add_argument(
        "--mapping",
        default="samples/simple/mapping_simple.xml",
        help="Path to mapping XML file (default: samples/simple/mapping_simple.xml)"
    )
    
    args = parser.parse_args()
    test_ai_agents(args.mapping)

