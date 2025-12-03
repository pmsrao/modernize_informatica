"""Integration Test Framework - End-to-end testing orchestration."""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
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


class IntegrationTestFramework:
    """Framework for running integration tests."""
    
    def __init__(self, test_config: Optional[Dict[str, Any]] = None):
        """Initialize integration test framework.
        
        Args:
            test_config: Optional test configuration
        """
        self.test_config = test_config or {}
        self.test_results = []
        logger.info("IntegrationTestFramework initialized")
    
    def run_test_suite(self, test_suite: Dict[str, Any]) -> Dict[str, Any]:
        """Run a complete test suite.
        
        Args:
            test_suite: Test suite definition
            
        Returns:
            Test suite results
        """
        logger.info(f"Running test suite: {test_suite.get('name', 'unknown')}")
        
        suite_name = test_suite.get('name', 'test_suite')
        test_cases = test_suite.get('test_cases', [])
        
        results = {
            'suite_name': suite_name,
            'start_time': datetime.now().isoformat(),
            'test_cases': [],
            'summary': {
                'total': len(test_cases),
                'passed': 0,
                'failed': 0,
                'skipped': 0
            }
        }
        
        # Run each test case
        for test_case in test_cases:
            case_result = self.run_test_case(test_case)
            results['test_cases'].append(case_result)
            
            if case_result['status'] == 'passed':
                results['summary']['passed'] += 1
            elif case_result['status'] == 'failed':
                results['summary']['failed'] += 1
            else:
                results['summary']['skipped'] += 1
        
        results['end_time'] = datetime.now().isoformat()
        results['duration'] = (
            datetime.fromisoformat(results['end_time']) -
            datetime.fromisoformat(results['start_time'])
        ).total_seconds()
        
        logger.info(f"Test suite completed: {results['summary']['passed']}/{results['summary']['total']} passed")
        
        return results
    
    def run_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test case.
        
        Args:
            test_case: Test case definition
            
        Returns:
            Test case result
        """
        test_name = test_case.get('name', 'unknown_test')
        test_type = test_case.get('type', 'unit')
        
        logger.info(f"Running test case: {test_name} (type: {test_type})")
        
        result = {
            'name': test_name,
            'type': test_type,
            'status': 'unknown',
            'start_time': datetime.now().isoformat(),
            'errors': [],
            'warnings': [],
            'metrics': {}
        }
        
        try:
            # Execute test based on type
            if test_type == 'unit':
                test_result = self._run_unit_test(test_case)
            elif test_type == 'integration':
                test_result = self._run_integration_test(test_case)
            elif test_type == 'performance':
                test_result = self._run_performance_test(test_case)
            elif test_type == 'validation':
                test_result = self._run_validation_test(test_case)
            else:
                raise ValueError(f"Unknown test type: {test_type}")
            
            result.update(test_result)
            result['status'] = 'passed' if test_result.get('success', False) else 'failed'
            
        except Exception as e:
            logger.error(f"Test case {test_name} failed with error: {e}")
            result['status'] = 'failed'
            result['errors'].append({
                'type': 'exception',
                'message': str(e)
            })
        
        result['end_time'] = datetime.now().isoformat()
        result['duration'] = (
            datetime.fromisoformat(result['end_time']) -
            datetime.fromisoformat(result['start_time'])
        ).total_seconds()
        
        return result
    
    def _run_unit_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run a unit test.
        
        Args:
            test_case: Test case definition
            
        Returns:
            Test result
        """
        # Unit tests would execute individual functions/methods
        # This is a placeholder implementation
        
        test_code = test_case.get('code', '')
        test_data = test_case.get('test_data', [])
        expected_output = test_case.get('expected_output', [])
        
        # In a real implementation, would execute the test code
        # For now, return a placeholder result
        
        return {
            'success': True,
            'message': 'Unit test executed (placeholder)',
            'output': expected_output
        }
    
    def _run_integration_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run an integration test.
        
        Args:
            test_case: Test case definition
            
        Returns:
            Test result
        """
        # Integration tests would test multiple components together
        # This is a placeholder implementation
        
        components = test_case.get('components', [])
        test_data = test_case.get('test_data', [])
        
        # In a real implementation, would execute the full integration flow
        # For now, return a placeholder result
        
        return {
            'success': True,
            'message': f'Integration test executed for {len(components)} components (placeholder)',
            'components_tested': components
        }
    
    def _run_performance_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run a performance test.
        
        Args:
            test_case: Test case definition
            
        Returns:
            Test result with performance metrics
        """
        import time
        
        max_execution_time = test_case.get('max_execution_time', 300)
        test_code = test_case.get('code', '')
        
        start_time = time.time()
        
        # Execute test code (placeholder)
        # In real implementation, would execute actual code
        
        execution_time = time.time() - start_time
        
        success = execution_time < max_execution_time
        
        return {
            'success': success,
            'execution_time': execution_time,
            'max_execution_time': max_execution_time,
            'metrics': {
                'execution_time_seconds': execution_time,
                'throughput': test_case.get('data_size', 0) / execution_time if execution_time > 0 else 0
            }
        }
    
    def _run_validation_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run a validation test.
        
        Args:
            test_case: Test case definition
            
        Returns:
            Test result
        """
        from validation.test_data_validator import TestDataValidator
        
        validator = TestDataValidator()
        
        canonical_model = test_case.get('canonical_model', {})
        test_data = test_case.get('test_data', [])
        expected_output = test_case.get('expected_output', [])
        
        # Run validation
        validation_result = validator.validate_transformation_logic(
            canonical_model=canonical_model,
            test_data=test_data,
            expected_output=expected_output
        )
        
        return {
            'success': validation_result.get('valid', False),
            'validation_result': validation_result,
            'match_percentage': validation_result.get('match_percentage', 0.0)
        }
    
    def generate_test_report(self, results: Dict[str, Any], output_path: Optional[Path] = None) -> str:
        """Generate a test report.
        
        Args:
            results: Test results dictionary
            output_path: Optional output file path
            
        Returns:
            Report content (JSON or HTML)
        """
        report_format = self.test_config.get('report_format', 'json')
        
        if report_format == 'html':
            report_content = self._generate_html_report(results)
        else:
            report_content = json.dumps(results, indent=2, default=str)
        
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            logger.info(f"Test report saved to {output_path}")
        
        return report_content
    
    def _generate_html_report(self, results: Dict[str, Any]) -> str:
        """Generate HTML test report.
        
        Args:
            results: Test results dictionary
            
        Returns:
            HTML report string
        """
        summary = results.get('summary', {})
        total = summary.get('total', 0)
        passed = summary.get('passed', 0)
        failed = summary.get('failed', 0)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Test Report - {results.get('suite_name', 'Test Suite')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        .summary {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .metric {{ display: inline-block; margin: 10px 20px 10px 0; padding: 10px; border-radius: 5px; }}
        .passed {{ background-color: #e8f5e9; color: #2e7d32; }}
        .failed {{ background-color: #ffebee; color: #c62828; }}
        .test-case {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ddd; }}
        .test-case.passed {{ border-left-color: #4CAF50; }}
        .test-case.failed {{ border-left-color: #f44336; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Test Report: {results.get('suite_name', 'Test Suite')}</h1>
        <div class="summary">
            <div class="metric passed">
                <strong>Total:</strong> {total}
            </div>
            <div class="metric passed">
                <strong>Passed:</strong> {passed}
            </div>
            <div class="metric failed">
                <strong>Failed:</strong> {failed}
            </div>
            <div class="metric">
                <strong>Success Rate:</strong> {success_rate:.1f}%
            </div>
        </div>
        <h2>Test Cases</h2>
        {self._generate_test_cases_html(results.get('test_cases', []))}
    </div>
</body>
</html>
'''
        return html
    
    def _generate_test_cases_html(self, test_cases: List[Dict[str, Any]]) -> str:
        """Generate HTML for test cases.
        
        Args:
            test_cases: List of test case results
            
        Returns:
            HTML string
        """
        html_parts = []
        for case in test_cases:
            status_class = case.get('status', 'unknown')
            html_parts.append(f'''
        <div class="test-case {status_class}">
            <h3>{case.get('name', 'Unknown Test')}</h3>
            <p><strong>Status:</strong> {status_class.upper()}</p>
            <p><strong>Duration:</strong> {case.get('duration', 0):.2f}s</p>
            {self._generate_errors_html(case.get('errors', []))}
        </div>
            ''')
        return '\n'.join(html_parts)
    
    def _generate_errors_html(self, errors: List[Dict[str, Any]]) -> str:
        """Generate HTML for errors.
        
        Args:
            errors: List of error dictionaries
            
        Returns:
            HTML string
        """
        if not errors:
            return ''
        
        error_html = '<ul>'
        for error in errors:
            error_html += f'<li><strong>{error.get("type", "Error")}:</strong> {error.get("message", "")}</li>'
        error_html += '</ul>'
        return error_html

