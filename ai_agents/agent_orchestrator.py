
"""Agent Orchestrator
Coordinates multiple AI agents.
"""

from ai_agents.rule_explainer_agent import RuleExplainerAgent
from ai_agents.mapping_summary_agent import MappingSummaryAgent
from ai_agents.risk_detection_agent import RiskDetectionAgent
from ai_agents.transformation_suggestion_agent import TransformationSuggestionAgent

class AgentOrchestrator:
    def __init__(self):
        self.rule_agent = RuleExplainerAgent()
        self.summary_agent = MappingSummaryAgent()
        self.risk_agent = RiskDetectionAgent()
        self.suggestion_agent = TransformationSuggestionAgent()

    def run_all(self, mapping):
        return {
            "summary": self.summary_agent.summarize(mapping),
            "explanations": self.rule_agent.explain(mapping),
            "risks": self.risk_agent.detect_risks(mapping),
            "suggestions": self.suggestion_agent.suggest(mapping)
        }
