"""Reconciliation Report Generator - Creates reconciliation reports."""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from utils.logger import get_logger

logger = get_logger(__name__)


class ReconciliationReportGenerator:
    """Generates reconciliation reports in various formats."""
    
    def __init__(self):
        """Initialize report generator."""
        logger.info("ReconciliationReportGenerator initialized")
    
    def generate_summary_report(self, reconciliation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary reconciliation report.
        
        Args:
            reconciliation_results: List of reconciliation results
            
        Returns:
            Summary report dictionary
        """
        total = len(reconciliation_results)
        matches = sum(1 for r in reconciliation_results if r.get('status') == 'match')
        mismatches = sum(1 for r in reconciliation_results if r.get('status') == 'mismatch')
        errors = sum(1 for r in reconciliation_results if r.get('status') == 'error')
        
        match_percentage = (matches / total * 100) if total > 0 else 0
        
        return {
            'title': 'Reconciliation Summary Report',
            'timestamp': datetime.now().isoformat(),
            'total_mappings': total,
            'matches': matches,
            'mismatches': mismatches,
            'errors': errors,
            'match_percentage': match_percentage,
            'status': 'pass' if errors == 0 and mismatches == 0 else 'fail',
            'results': reconciliation_results
        }
    
    def generate_detailed_report(self, reconciliation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed reconciliation report for a single mapping.
        
        Args:
            reconciliation_result: Single reconciliation result
            
        Returns:
            Detailed report dictionary
        """
        return {
            'title': f"Detailed Reconciliation Report - {reconciliation_result.get('mapping_name', 'Unknown')}",
            'timestamp': datetime.now().isoformat(),
            'mapping_name': reconciliation_result.get('mapping_name'),
            'comparison_method': reconciliation_result.get('comparison_method'),
            'status': reconciliation_result.get('status'),
            'source_table': reconciliation_result.get('source_table'),
            'target_table': reconciliation_result.get('target_table'),
            'details': reconciliation_result.get('details', {}),
            'comparison_results': {
                k: v for k, v in reconciliation_result.items()
                if k not in ['mapping_name', 'comparison_method', 'status', 'source_table', 'target_table', 'details', 'timestamp']
            }
        }
    
    def generate_drill_down_report(self,
                                  reconciliation_result: Dict[str, Any],
                                  drill_down_level: str = "row") -> Dict[str, Any]:
        """Generate drill-down report for mismatches.
        
        Args:
            reconciliation_result: Reconciliation result with mismatches
            drill_down_level: Level of drill-down ('row', 'column', 'value')
            
        Returns:
            Drill-down report dictionary
        """
        if reconciliation_result.get('status') == 'match':
            return {
                'title': 'Drill-Down Report',
                'message': 'No mismatches found - drill-down not applicable',
                'status': 'match'
            }
        
        mismatches = []
        
        if reconciliation_result.get('method') == 'count':
            mismatches.append({
                'type': 'count_mismatch',
                'source_count': reconciliation_result.get('source_count'),
                'target_count': reconciliation_result.get('target_count'),
                'difference': reconciliation_result.get('difference')
            })
        elif reconciliation_result.get('method') == 'threshold':
            mismatches.extend(reconciliation_result.get('mismatches', []))
        
        return {
            'title': f"Drill-Down Report - {reconciliation_result.get('mapping_name', 'Unknown')}",
            'timestamp': datetime.now().isoformat(),
            'mapping_name': reconciliation_result.get('mapping_name'),
            'drill_down_level': drill_down_level,
            'mismatches': mismatches,
            'recommendations': self._generate_recommendations(reconciliation_result)
        }
    
    def export_to_json(self, report_data: Dict[str, Any], output_path: Path):
        """Export report to JSON.
        
        Args:
            report_data: Report data dictionary
            output_path: Output file path
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Exported reconciliation report to JSON: {output_path}")
    
    def export_to_html(self, report_data: Dict[str, Any], output_path: Path):
        """Export report to HTML.
        
        Args:
            report_data: Report data dictionary
            output_path: Output file path
        """
        html_content = self._generate_html_content(report_data)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"Exported reconciliation report to HTML: {output_path}")
    
    def _generate_html_content(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML content from report data.
        
        Args:
            report_data: Report data dictionary
            
        Returns:
            HTML string
        """
        status_color = {
            'match': '#4CAF50',
            'mismatch': '#F44336',
            'error': '#FF9800',
            'pass': '#4CAF50',
            'fail': '#F44336'
        }.get(report_data.get('status', 'unknown'), '#666')
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{report_data.get('title', 'Reconciliation Report')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; }}
        h1 {{ color: #333; border-bottom: 3px solid {status_color}; padding-bottom: 10px; }}
        .summary {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .metric {{ display: inline-block; margin: 10px 20px 10px 0; padding: 10px; background-color: #e8f5e9; border-radius: 5px; }}
        .status {{ padding: 5px 15px; border-radius: 3px; color: white; background-color: {status_color}; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .match {{ background-color: #e8f5e9; }}
        .mismatch {{ background-color: #ffebee; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{report_data.get('title', 'Reconciliation Report')}</h1>
        <div class="summary">
            <p><strong>Generated:</strong> {report_data.get('timestamp', 'Unknown')}</p>
            <p><strong>Status:</strong> <span class="status">{report_data.get('status', 'unknown').upper()}</span></p>
        </div>
        {self._generate_html_details(report_data)}
    </div>
</body>
</html>
"""
        return html
    
    def _generate_html_details(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML details section.
        
        Args:
            report_data: Report data dictionary
            
        Returns:
            HTML string
        """
        if 'total_mappings' in report_data:
            # Summary report
            return f"""
            <h2>Summary</h2>
            <div class="metric">
                <strong>Total Mappings:</strong> {report_data.get('total_mappings', 0)}
            </div>
            <div class="metric">
                <strong>Matches:</strong> {report_data.get('matches', 0)}
            </div>
            <div class="metric">
                <strong>Mismatches:</strong> {report_data.get('mismatches', 0)}
            </div>
            <div class="metric">
                <strong>Errors:</strong> {report_data.get('errors', 0)}
            </div>
            <div class="metric">
                <strong>Match Percentage:</strong> {report_data.get('match_percentage', 0):.2f}%
            </div>
            """
        else:
            # Detailed report
            return f"""
            <h2>Details</h2>
            <p><strong>Mapping:</strong> {report_data.get('mapping_name', 'Unknown')}</p>
            <p><strong>Method:</strong> {report_data.get('comparison_method', 'Unknown')}</p>
            <p><strong>Source Table:</strong> {report_data.get('source_table', 'Unknown')}</p>
            <p><strong>Target Table:</strong> {report_data.get('target_table', 'Unknown')}</p>
            """
    
    def _generate_recommendations(self, reconciliation_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on reconciliation results.
        
        Args:
            reconciliation_result: Reconciliation result
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if reconciliation_result.get('status') == 'mismatch':
            if reconciliation_result.get('method') == 'count':
                recommendations.append("Row count mismatch detected. Review data loading process.")
                recommendations.append("Check for filtering differences between source and target.")
            elif reconciliation_result.get('method') == 'threshold':
                recommendations.append("Aggregate values exceed threshold. Review transformation logic.")
                recommendations.append("Verify calculation formulas match between source and target.")
        
        return recommendations

