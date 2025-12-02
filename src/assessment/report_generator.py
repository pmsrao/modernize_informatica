"""Report Generator — Creates assessment reports."""
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from src.graph.graph_store import GraphStore
from src.assessment.profiler import Profiler
from src.assessment.analyzer import Analyzer
from src.assessment.wave_planner import WavePlanner
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ReportGenerator:
    """Generates assessment reports in various formats."""
    
    def __init__(self, graph_store: GraphStore,
                 profiler: Optional[Profiler] = None,
                 analyzer: Optional[Analyzer] = None,
                 wave_planner: Optional[WavePlanner] = None):
        """Initialize report generator.
        
        Args:
            graph_store: GraphStore instance
            profiler: Optional Profiler instance
            analyzer: Optional Analyzer instance
            wave_planner: Optional WavePlanner instance
        """
        self.graph_store = graph_store
        self.profiler = profiler or Profiler(graph_store)
        self.analyzer = analyzer or Analyzer(graph_store, self.profiler)
        self.wave_planner = wave_planner or WavePlanner(graph_store, self.profiler, self.analyzer)
        logger.info("ReportGenerator initialized")
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Create executive summary.
        
        Returns:
            Dictionary with summary information:
            - repository_statistics: Dict
            - overall_complexity: str
            - total_effort_days: float
            - blocker_count: int
            - wave_count: int
            - key_findings: List[str]
        """
        logger.info("Generating summary report...")
        
        # Get repository statistics
        repo_stats = self.profiler.profile_repository()
        
        # Get complexity metrics
        complexity_metrics = self.profiler.calculate_complexity_metrics()
        
        # Get effort estimates
        effort_estimates = self.analyzer.estimate_migration_effort()
        
        # Get blockers
        blockers = self.analyzer.identify_blockers()
        
        # Get migration waves
        waves = self.wave_planner.plan_migration_waves()
        
        # Generate key findings
        key_findings = []
        
        if repo_stats["total_mappings"] > 0:
            key_findings.append(
                f"Repository contains {repo_stats['total_mappings']} mappings across "
                f"{repo_stats['total_workflows']} workflows"
            )
        
        if complexity_metrics["overall_complexity"] == "HIGH":
            key_findings.append(
                f"Overall complexity is HIGH with {len(complexity_metrics['high_complexity_mappings'])} "
                f"high-complexity mappings"
            )
        
        if len(blockers) > 0:
            high_severity_blockers = [b for b in blockers if b["severity"] == "HIGH"]
            if high_severity_blockers:
                key_findings.append(
                    f"Found {len(high_severity_blockers)} high-severity migration blockers"
                )
        
        key_findings.append(
            f"Estimated total migration effort: {effort_estimates['total_effort_days']:.1f} days"
        )
        
        key_findings.append(
            f"Recommended migration approach: {len(waves)} waves"
        )
        
        summary = {
            "repository_statistics": repo_stats,
            "overall_complexity": complexity_metrics["overall_complexity"],
            "total_effort_days": effort_estimates["total_effort_days"],
            "blocker_count": len(blockers),
            "wave_count": len(waves),
            "key_findings": key_findings,
            "generated_at": datetime.now().isoformat()
        }
        
        logger.info("Summary report generated")
        return summary
    
    def generate_detailed_report(self) -> Dict[str, Any]:
        """Create detailed component analysis.
        
        Returns:
            Dictionary with detailed analysis:
            - repository_profile: Dict
            - workflow_profiles: List[Dict]
            - mapping_profiles: List[Dict]
            - transformation_profiles: Dict
            - complexity_metrics: Dict
            - patterns: Dict
            - blockers: List[Dict]
            - effort_estimates: Dict
            - dependencies: Dict
        """
        logger.info("Generating detailed report...")
        
        detailed = {
            "repository_profile": self.profiler.profile_repository(),
            "workflow_profiles": self.profiler.profile_workflows(),
            "mapping_profiles": self.profiler.profile_mappings(),
            "transformation_profiles": self.profiler.profile_transformations(),
            "complexity_metrics": self.profiler.calculate_complexity_metrics(),
            "patterns": self.analyzer.identify_patterns(),
            "blockers": self.analyzer.identify_blockers(),
            "effort_estimates": self.analyzer.estimate_migration_effort(),
            "dependencies": self.analyzer.find_dependencies(),
            "categorized_components": self.analyzer.categorize_by_complexity(),
            "generated_at": datetime.now().isoformat()
        }
        
        logger.info("Detailed report generated")
        return detailed
    
    def generate_wave_plan(self, max_wave_size: int = 10) -> Dict[str, Any]:
        """Create migration wave recommendations.
        
        Args:
            max_wave_size: Maximum number of components per wave
        
        Returns:
            Dictionary with wave plan:
            - waves: List[Dict]
            - total_waves: int
            - total_effort_days: float
            - wave_summary: Dict
        """
        logger.info(f"Generating wave plan (max wave size: {max_wave_size})...")
        
        waves = self.wave_planner.plan_migration_waves(max_wave_size=max_wave_size)
        
        total_effort = sum(wave["total_effort_days"] for wave in waves)
        
        # Wave summary
        wave_summary = {
            "total_waves": len(waves),
            "average_wave_size": sum(len(w["components"]) for w in waves) / len(waves) if waves else 0,
            "total_effort_days": total_effort,
            "average_effort_per_wave": total_effort / len(waves) if waves else 0
        }
        
        wave_plan = {
            "waves": waves,
            "total_waves": len(waves),
            "total_effort_days": total_effort,
            "wave_summary": wave_summary,
            "generated_at": datetime.now().isoformat()
        }
        
        logger.info(f"Wave plan generated: {len(waves)} waves, {total_effort:.1f} days")
        return wave_plan
    
    def export_to_json(self, report_data: Dict[str, Any], output_path: str) -> str:
        """Export assessment data as JSON.
        
        Args:
            report_data: Report data dictionary
            output_path: Output file path
        
        Returns:
            Path to exported file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported report to JSON: {output_file}")
        return str(output_file)
    
    def export_to_html(self, report_data: Dict[str, Any], output_path: str) -> str:
        """Export assessment as HTML report.
        
        Args:
            report_data: Report data dictionary
            output_path: Output file path
        
        Returns:
            Path to exported file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate HTML report
        html_content = self._generate_html_content(report_data)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Exported report to HTML: {output_file}")
        return str(output_file)
    
    def _generate_html_content(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML content from report data.
        
        Args:
            report_data: Report data dictionary
        
        Returns:
            HTML string
        """
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Informatica Migration Assessment Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
            border-bottom: 2px solid #ddd;
            padding-bottom: 5px;
        }}
        .summary {{
            background-color: #f9f9f9;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .metric {{
            display: inline-block;
            margin: 10px 20px 10px 0;
            padding: 10px;
            background-color: #e8f5e9;
            border-radius: 5px;
            min-width: 150px;
        }}
        .metric-label {{
            font-weight: bold;
            color: #666;
            font-size: 0.9em;
        }}
        .metric-value {{
            font-size: 1.5em;
            color: #2e7d32;
            font-weight: bold;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        .blocker-high {{
            background-color: #ffebee;
            border-left: 4px solid #f44336;
        }}
        .blocker-medium {{
            background-color: #fff3e0;
            border-left: 4px solid #ff9800;
        }}
        .blocker-low {{
            background-color: #f1f8e9;
            border-left: 4px solid #8bc34a;
        }}
        .wave {{
            margin: 20px 0;
            padding: 15px;
            background-color: #e3f2fd;
            border-radius: 5px;
            border-left: 4px solid #2196F3;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 0.9em;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Informatica Migration Assessment Report</h1>
        <div class="footer">
            Generated: {report_data.get('generated_at', datetime.now().isoformat())}
        </div>
"""
        
        # Add summary section
        if "repository_statistics" in report_data:
            repo_stats = report_data["repository_statistics"]
            html += """
        <h2>Repository Summary</h2>
        <div class="summary">
"""
            html += f"""
            <div class="metric">
                <div class="metric-label">Total Workflows</div>
                <div class="metric-value">{repo_stats.get('total_workflows', 0)}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Total Mappings</div>
                <div class="metric-value">{repo_stats.get('total_mappings', 0)}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Total Transformations</div>
                <div class="metric-value">{repo_stats.get('total_transformations', 0)}</div>
            </div>
"""
            if "overall_complexity" in report_data:
                html += f"""
            <div class="metric">
                <div class="metric-label">Overall Complexity</div>
                <div class="metric-value">{report_data['overall_complexity']}</div>
            </div>
"""
            if "total_effort_days" in report_data:
                html += f"""
            <div class="metric">
                <div class="metric-label">Total Effort (Days)</div>
                <div class="metric-value">{report_data['total_effort_days']:.1f}</div>
            </div>
"""
            html += """
        </div>
"""
        
        # Add blockers section
        if "blockers" in report_data and report_data["blockers"]:
            html += """
        <h2>Migration Blockers</h2>
        <table>
            <tr>
                <th>Component</th>
                <th>Type</th>
                <th>Severity</th>
                <th>Description</th>
                <th>Recommendation</th>
            </tr>
"""
            for blocker in report_data["blockers"]:
                severity_class = f"blocker-{blocker['severity'].lower()}"
                html += f"""
            <tr class="{severity_class}">
                <td>{blocker['component_name']}</td>
                <td>{blocker['component_type']}</td>
                <td>{blocker['severity']}</td>
                <td>{blocker['description']}</td>
                <td>{blocker['recommendation']}</td>
            </tr>
"""
            html += """
        </table>
"""
        
        # Add waves section
        if "waves" in report_data:
            html += """
        <h2>Migration Wave Plan</h2>
"""
            for wave in report_data["waves"]:
                html += f"""
        <div class="wave">
            <h3>Wave {wave['wave_number']}</h3>
            <p><strong>Components:</strong> {len(wave['components'])}</p>
            <p><strong>Total Effort:</strong> {wave['total_effort_days']:.1f} days</p>
            <p><strong>Complexity Distribution:</strong> 
                LOW: {wave['complexity_distribution'].get('LOW', 0)}, 
                MEDIUM: {wave['complexity_distribution'].get('MEDIUM', 0)}, 
                HIGH: {wave['complexity_distribution'].get('HIGH', 0)}
            </p>
            <p><strong>Dependencies Satisfied:</strong> {'Yes' if wave.get('dependencies_satisfied', False) else 'No'}</p>
        </div>
"""
        
        html += """
    </div>
    <div class="footer">
        <p>Generated by Informatica Modernization Accelerator</p>
        <p>Report Date: {}</p>
    </div>
</body>
</html>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        return html

