"""Unit tests for code generators."""
import pytest
from generators import PySparkGenerator, DLTGenerator, SQLGenerator, SpecGenerator
from normalizer import MappingNormalizer
from parser import MappingParser


class TestPySparkGenerator:
    """Tests for PySparkGenerator."""
    
    def test_generate_basic_mapping(self):
        """Test generating PySpark code for basic mapping."""
        model = {
            "mapping_name": "M_TEST",
            "sources": [
                {
                    "name": "SRC1",
                    "table": "customers",
                    "fields": [
                        {"name": "customer_id", "data_type": "number"},
                        {"name": "customer_name", "data_type": "string"}
                    ]
                }
            ],
            "targets": [
                {
                    "name": "TGT1",
                    "table": "customer_target"
                }
            ],
            "transformations": [],
            "connectors": []
        }
        
        generator = PySparkGenerator()
        code = generator.generate(model)
        
        assert "from pyspark.sql" in code
        assert "SparkSession" in code
        assert "M_TEST" in code
        assert "customers" in code
    
    def test_generate_with_expression(self):
        """Test generating PySpark code with expression transformation."""
        model = {
            "mapping_name": "M_TEST",
            "sources": [
                {
                    "name": "SRC1",
                    "table": "customers",
                    "fields": []
                }
            ],
            "targets": [
                {
                    "name": "TGT1",
                    "table": "customer_target"
                }
            ],
            "transformations": [
                {
                    "type": "EXPRESSION",
                    "name": "EXP1",
                    "ports": [
                        {
                            "name": "customer_name_upper",
                            "port_type": "OUTPUT",
                            "expression": "F.upper(F.col('customer_name'))"
                        }
                    ]
                }
            ],
            "connectors": []
        }
        
        generator = PySparkGenerator()
        code = generator.generate(model)
        
        assert "withColumn" in code or "customer_name_upper" in code


class TestDLTGenerator:
    """Tests for DLTGenerator."""
    
    def test_generate_basic_dlt(self):
        """Test generating DLT code for basic mapping."""
        model = {
            "mapping_name": "M_TEST",
            "sources": [
                {
                    "name": "SRC1",
                    "table": "customers"
                }
            ],
            "targets": [
                {
                    "name": "TGT1",
                    "table": "customer_target"
                }
            ],
            "transformations": [],
            "connectors": []
        }
        
        generator = DLTGenerator()
        code = generator.generate(model)
        
        assert "import dlt" in code
        assert "@dlt.table" in code
        assert "customers" in code


class TestSQLGenerator:
    """Tests for SQLGenerator."""
    
    def test_generate_basic_sql(self):
        """Test generating SQL code for basic mapping."""
        model = {
            "mapping_name": "M_TEST",
            "sources": [
                {
                    "name": "SRC1",
                    "table": "customers",
                    "fields": [
                        {"name": "customer_id"},
                        {"name": "customer_name"}
                    ]
                }
            ],
            "targets": [
                {
                    "name": "TGT1",
                    "table": "customer_target"
                }
            ],
            "transformations": [],
            "connectors": []
        }
        
        generator = SQLGenerator()
        code = generator.generate(model)
        
        assert "SELECT" in code
        assert "FROM" in code
        assert "customers" in code
    
    def test_generate_sql_with_filter(self):
        """Test generating SQL code with filter."""
        model = {
            "mapping_name": "M_TEST",
            "sources": [
                {
                    "name": "SRC1",
                    "table": "customers",
                    "fields": []
                }
            ],
            "targets": [],
            "transformations": [
                {
                    "type": "FILTER",
                    "name": "FLT1",
                    "filter_condition": "customer_id > 100"
                }
            ],
            "connectors": []
        }
        
        generator = SQLGenerator()
        code = generator.generate(model)
        
        assert "WHERE" in code
        assert "customer_id > 100" in code
    
    def test_generate_view(self):
        """Test generating CREATE VIEW statement."""
        model = {
            "mapping_name": "M_TEST",
            "sources": [
                {
                    "name": "SRC1",
                    "table": "customers",
                    "fields": []
                }
            ],
            "targets": [],
            "transformations": [],
            "connectors": []
        }
        
        generator = SQLGenerator()
        code = generator.generate_view(model, "customer_view")
        
        assert "CREATE OR REPLACE VIEW" in code
        assert "customer_view" in code


class TestSpecGenerator:
    """Tests for SpecGenerator."""
    
    def test_generate_spec(self):
        """Test generating mapping specification."""
        model = {
            "mapping_name": "M_TEST",
            "sources": [
                {
                    "name": "SRC1",
                    "table": "customers"
                }
            ],
            "targets": [
                {
                    "name": "TGT1",
                    "table": "customer_target"
                }
            ],
            "transformations": [],
            "connectors": []
        }
        
        generator = SpecGenerator()
        spec = generator.generate(model)
        
        assert "M_TEST" in spec
        assert "SRC1" in spec
        assert "TGT1" in spec
