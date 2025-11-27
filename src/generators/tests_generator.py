"""Tests Generator — Enhanced with comprehensive test generation."""
from typing import Dict, List, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class TestsGenerator:
    """Generates comprehensive test suites for mappings and transformations."""
    
    def generate(self, model: Dict[str, Any], test_type: str = "all") -> str:
        """Generate test code for canonical model.
        
        Args:
            model: Canonical model from normalizer
            test_type: Type of tests to generate - 'all', 'unit', 'integration', 'golden'
            
        Returns:
            Generated test code as string
        """
        if test_type == "all":
            return self._generate_all_tests(model)
        elif test_type == "unit":
            return self._generate_unit_tests(model)
        elif test_type == "integration":
            return self._generate_integration_tests(model)
        elif test_type == "golden":
            return self._generate_golden_tests(model)
        else:
            raise ValueError(f"Unknown test type: {test_type}")
    
    def _generate_all_tests(self, model: Dict[str, Any]) -> str:
        """Generate all test types.
        
        Args:
            model: Canonical model
            
        Returns:
            Complete test suite
        """
        lines = [
            "import pytest",
            "from pyspark.sql import SparkSession",
            "from pyspark.sql.types import *",
            "from pyspark.sql.functions import *",
            "",
            "# Test configuration",
            "pytest_plugins = ['pytest_spark']",
            "",
            f"# Tests for mapping: {model.get('name', 'Unknown')}",
            ""
        ]
        
        # Add unit tests
        lines.append("# ============================================================================")
        lines.append("# Unit Tests")
        lines.append("# ============================================================================")
        lines.extend(self._generate_unit_tests(model).split("\n"))
        lines.append("")
        lines.append("")
        
        # Add integration tests
        lines.append("# ============================================================================")
        lines.append("# Integration Tests")
        lines.append("# ============================================================================")
        lines.extend(self._generate_integration_tests(model).split("\n"))
        lines.append("")
        lines.append("")
        
        # Add golden tests
        lines.append("# ============================================================================")
        lines.append("# Golden Row Tests")
        lines.append("# ============================================================================")
        lines.extend(self._generate_golden_tests(model).split("\n"))
        
        return "\n".join(lines)
    
    def _generate_unit_tests(self, model: Dict[str, Any]) -> str:
        """Generate unit tests for transformations.
        
        Args:
            model: Canonical model
            
        Returns:
            Unit test code
        """
        lines = [
            "@pytest.fixture",
            "def spark():",
            "    spark = SparkSession.builder.appName('test').getOrCreate()",
            "    yield spark",
            "    spark.stop()",
            "",
            ""
        ]
        
        # Test each transformation
        transformations = model.get("transformations", [])
        for i, trans in enumerate(transformations):
            trans_name = trans.get("name", f"trans_{i}")
            trans_type = trans.get("type", "Unknown")
            
            lines.append(f"def test_{trans_name.lower().replace(' ', '_')}_transformation(spark):")
            lines.append(f'    """Test {trans_type} transformation: {trans_name}"""')
            lines.append("    # Test data")
            lines.append("    test_data = [")
            
            # Generate test data based on input ports
            input_ports = trans.get("input_ports", [])
            if input_ports:
                sample_row = "        {"
                for port in input_ports[:3]:  # Limit to first 3 ports
                    port_name = port.get("name", "col")
                    port_type = port.get("data_type", "string")
                    if "int" in port_type.lower():
                        sample_row += f'"{port_name}": 1, '
                    elif "float" in port_type.lower() or "double" in port_type.lower():
                        sample_row += f'"{port_name}": 1.0, '
                    elif "date" in port_type.lower():
                        sample_row += f'"{port_name}": "2024-01-01", '
                    else:
                        sample_row += f'"{port_name}": "test", '
                sample_row = sample_row.rstrip(", ") + "}"
                lines.append(sample_row)
            
            lines.append("    ]")
            lines.append("    df = spark.createDataFrame(test_data)")
            lines.append("")
            lines.append("    # Apply transformation logic")
            lines.append(f"    # TODO: Implement {trans_type} transformation test")
            lines.append("    result = df")
            lines.append("")
            lines.append("    # Assertions")
            lines.append("    assert result is not None")
            lines.append("    assert result.count() > 0")
            
            # Test output ports
            output_ports = trans.get("output_ports", [])
            if output_ports:
                lines.append("    # Verify output columns")
                for port in output_ports[:5]:  # Limit to first 5
                    port_name = port.get("name", "col")
                    lines.append(f'    assert "{port_name}" in result.columns')
            
            lines.append("")
            lines.append("")
        
        # Test expressions
        expressions = model.get("expressions", [])
        if expressions:
            lines.append("# Expression Tests")
            lines.append("")
            for i, expr in enumerate(expressions):
                expr_name = expr.get("name", f"expr_{i}")
                expr_formula = expr.get("formula", "")
                
                lines.append(f"def test_expression_{expr_name.lower().replace(' ', '_')}(spark):")
                lines.append(f'    """Test expression: {expr_name}"""')
                lines.append("    # Test data")
                lines.append("    test_data = [{\"col1\": 1, \"col2\": 2}]")
                lines.append("    df = spark.createDataFrame(test_data)")
                lines.append("")
                lines.append(f"    # Expression: {expr_formula}")
                lines.append("    # TODO: Implement expression evaluation")
                lines.append("    result = df.select(col(\"col1\"))")
                lines.append("")
                lines.append("    assert result is not None")
                lines.append("")
                lines.append("")
        
        return "\n".join(lines)
    
    def _generate_integration_tests(self, model: Dict[str, Any]) -> str:
        """Generate integration tests for full mapping.
        
        Args:
            model: Canonical model
            
        Returns:
            Integration test code
        """
        mapping_name = model.get("name", "Unknown")
        
        lines = [
            "@pytest.fixture",
            "def spark():",
            "    spark = SparkSession.builder.appName('integration_test').getOrCreate()",
            "    yield spark",
            "    spark.stop()",
            "",
            "",
            f"def test_{mapping_name.lower().replace(' ', '_')}_full_pipeline(spark):",
            f'    """Integration test for full mapping: {mapping_name}"""',
            "    # Load source data",
            "    sources = ["
        ]
        
        # Generate source data fixtures
        sources = model.get("sources", [])
        for source in sources:
            source_name = source.get("name", "source")
            lines.append(f'        ("{source_name}", "path/to/{source_name}.parquet"),')
        
        lines.append("    ]")
        lines.append("")
        lines.append("    # Load all sources")
        lines.append("    source_dfs = {}")
        lines.append("    for name, path in sources:")
        lines.append("        source_dfs[name] = spark.read.parquet(path)")
        lines.append("")
        lines.append("    # Apply transformations")
        lines.append("    # TODO: Implement full transformation pipeline")
        lines.append("    result = source_dfs[list(source_dfs.keys())[0]]")
        lines.append("")
        lines.append("    # Validate results")
        lines.append("    assert result is not None")
        lines.append("    assert result.count() > 0")
        
        # Validate target structure
        targets = model.get("targets", [])
        if targets:
            lines.append("    # Verify target columns")
            for target in targets:
                target_name = target.get("name", "target")
                target_columns = target.get("columns", [])
                lines.append(f'    # Target: {target_name}')
                for col in target_columns[:5]:  # Limit to first 5
                    col_name = col.get("name", "col")
                    lines.append(f'    assert "{col_name}" in result.columns')
        
        lines.append("")
        lines.append("")
        lines.append("@pytest.mark.parametrize('source_file', [")
        lines.append("    'test_data/source1.parquet',")
        lines.append("    'test_data/source2.parquet',")
        lines.append("])")
        lines.append("def test_mapping_with_different_sources(spark, source_file):")
        lines.append('    """Test mapping with different source files."""')
        lines.append("    df = spark.read.parquet(source_file)")
        lines.append("    # TODO: Apply mapping transformations")
        lines.append("    result = df")
        lines.append("    assert result.count() > 0")
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_golden_tests(self, model: Dict[str, Any]) -> str:
        """Generate golden row tests.
        
        Args:
            model: Canonical model
            
        Returns:
            Golden test code
        """
        mapping_name = model.get("name", "Unknown")
        
        lines = [
            "@pytest.fixture",
            "def spark():",
            "    spark = SparkSession.builder.appName('golden_test').getOrCreate()",
            "    yield spark",
            "    spark.stop()",
            "",
            "",
            f"def test_{mapping_name.lower().replace(' ', '_')}_golden_rows(spark):",
            f'    """Golden row test for mapping: {mapping_name}"""',
            "    # Golden test data (expected input/output pairs)",
            "    golden_rows = [",
            "        {",
            "            'input': {"
        ]
        
        # Generate sample input data
        sources = model.get("sources", [])
        if sources:
            source = sources[0]
            columns = source.get("columns", [])
            for col in columns[:5]:  # Limit to first 5
                col_name = col.get("name", "col")
                col_type = col.get("data_type", "string")
                if "int" in col_type.lower():
                    lines.append(f"                '{col_name}': 100,")
                elif "float" in col_type.lower() or "double" in col_type.lower():
                    lines.append(f"                '{col_name}': 100.5,")
                elif "date" in col_type.lower():
                    lines.append(f"                '{col_name}': '2024-01-01',")
                else:
                    lines.append(f"                '{col_name}': 'test_value',")
        
        lines.append("            },")
        lines.append("            'expected_output': {")
        
        # Generate expected output data
        targets = model.get("targets", [])
        if targets:
            target = targets[0]
            columns = target.get("columns", [])
            for col in columns[:5]:  # Limit to first 5
                col_name = col.get("name", "col")
                col_type = col.get("data_type", "string")
                if "int" in col_type.lower():
                    lines.append(f"                '{col_name}': 200,")
                elif "float" in col_type.lower() or "double" in col_type.lower():
                    lines.append(f"                '{col_name}': 200.5,")
                elif "date" in col_type.lower():
                    lines.append(f"                '{col_name}': '2024-01-02',")
                else:
                    lines.append(f"                '{col_name}': 'transformed_value',")
        
        lines.append("            }")
        lines.append("        },")
        lines.append("    ]")
        lines.append("")
        lines.append("    # Test each golden row")
        lines.append("    for golden_row in golden_rows:")
        lines.append("        input_df = spark.createDataFrame([golden_row['input']])")
        lines.append("        expected_output = golden_row['expected_output']")
        lines.append("")
        lines.append("        # Apply transformations")
        lines.append("        # TODO: Implement actual transformation logic")
        lines.append("        result_df = input_df")
        lines.append("")
        lines.append("        # Validate against expected output")
        lines.append("        result_row = result_df.collect()[0]")
        lines.append("        for key, expected_value in expected_output.items():")
        lines.append("            actual_value = result_row[key]")
        lines.append("            assert actual_value == expected_value, \\")
        lines.append(f"                f'Golden row test failed for {{key}}: expected {{expected_value}}, got {{actual_value}}'")
        lines.append("")
        lines.append("")
        lines.append("def test_data_quality_checks(spark):")
        lines.append('    """Test data quality assertions."""')
        lines.append("    # Test data")
        lines.append("    test_data = [{'col1': 1, 'col2': 'value'}]")
        lines.append("    df = spark.createDataFrame(test_data)")
        lines.append("")
        lines.append("    # Data quality checks")
        lines.append("    assert df.count() > 0, 'Data should not be empty'")
        lines.append("    assert 'col1' in df.columns, 'Required column missing'")
        lines.append("    assert df.filter(col('col1').isNull()).count() == 0, 'No nulls allowed in col1'")
        lines.append("")
        
        return "\n".join(lines)
    
    def generate_test_data(self, model: Dict[str, Any], num_rows: int = 10) -> str:
        """Generate test data generator code.
        
        Args:
            model: Canonical model
            num_rows: Number of test rows to generate
            
        Returns:
            Test data generator code
        """
        lines = [
            "import random",
            "from datetime import datetime, timedelta",
            "",
            "",
            "def generate_test_data(num_rows=10):",
            '    """Generate test data for mapping."""',
            "    data = []",
            "",
            "    for i in range(num_rows):",
            "        row = {"
        ]
        
        # Generate columns from first source
        sources = model.get("sources", [])
        if sources:
            source = sources[0]
            columns = source.get("columns", [])
            for col in columns[:10]:  # Limit to first 10
                col_name = col.get("name", "col")
                col_type = col.get("data_type", "string")
                
                if "int" in col_type.lower():
                    lines.append(f"            '{col_name}': random.randint(1, 1000),")
                elif "float" in col_type.lower() or "double" in col_type.lower():
                    lines.append(f"            '{col_name}': round(random.uniform(1.0, 1000.0), 2),")
                elif "date" in col_type.lower():
                    lines.append(f"            '{col_name}': (datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d'),")
                elif "bool" in col_type.lower() or "boolean" in col_type.lower():
                    lines.append(f"            '{col_name}': random.choice([True, False]),")
                else:
                    lines.append(f"            '{col_name}': f'test_value_{i}',")
        
        lines.append("        }")
        lines.append("        data.append(row)")
        lines.append("")
        lines.append("    return data")
        lines.append("")
        
        return "\n".join(lines)
