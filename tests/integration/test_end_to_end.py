"""Integration tests for end-to-end pipeline."""
import pytest
import tempfile
from pathlib import Path
from parser import MappingParser
from normalizer import MappingNormalizer
from generators import PySparkGenerator, DLTGenerator, SQLGenerator
from translator import PySparkTranslator, SQLTranslator, tokenize, Parser


class TestEndToEndPipeline:
    """Tests for complete parse → normalize → translate → generate pipeline."""
    
    def test_full_pipeline(self, tmp_path):
        """Test complete pipeline from XML to generated code."""
        # Create sample mapping XML
        xml_content = """<?xml version="1.0"?>
<MAPPING NAME="M_CUSTOMER_LOAD">
    <SOURCE NAME="SRC_CUSTOMERS">
        <TABLE NAME="customers"/>
        <FIELD NAME="customer_id" DATATYPE="number"/>
        <FIELD NAME="customer_name" DATATYPE="string"/>
        <FIELD NAME="email" DATATYPE="string"/>
    </SOURCE>
    <TARGET NAME="TGT_CUSTOMERS" TABLE="customer_target"/>
    <TRANSFORMATION NAME="EXP1" TYPE="EXPRESSION">
        <PORT NAME="customer_id" PORTTYPE="INPUT" DATATYPE="number"/>
        <PORT NAME="customer_name" PORTTYPE="INPUT" DATATYPE="string"/>
        <PORT NAME="email" PORTTYPE="INPUT" DATATYPE="string"/>
        <PORT NAME="email_upper" PORTTYPE="OUTPUT" DATATYPE="string" EXPRESSION="UPPER(email)"/>
    </TRANSFORMATION>
</MAPPING>"""
        
        xml_file = tmp_path / "mapping.xml"
        xml_file.write_text(xml_content)
        
        # Step 1: Parse
        parser = MappingParser(str(xml_file))
        raw_mapping = parser.parse()
        assert raw_mapping["name"] == "M_CUSTOMER_LOAD"
        
        # Step 2: Normalize
        normalizer = MappingNormalizer()
        canonical_model = normalizer.normalize(raw_mapping)
        # Canonical model uses transformation_name, not mapping_name
        assert canonical_model.get("transformation_name") == "M_CUSTOMER_LOAD" or canonical_model.get("mapping_name") == "M_CUSTOMER_LOAD"
        assert "sources" in canonical_model
        assert "targets" in canonical_model
        assert "transformations" in canonical_model
        
        # Step 3: Generate PySpark
        pyspark_generator = PySparkGenerator()
        pyspark_code = pyspark_generator.generate(canonical_model)
        assert "from pyspark.sql" in pyspark_code
        assert "M_CUSTOMER_LOAD" in pyspark_code
        
        # Step 4: Generate DLT
        dlt_generator = DLTGenerator()
        dlt_code = dlt_generator.generate(canonical_model)
        assert "import dlt" in dlt_code
        
        # Step 5: Generate SQL
        sql_generator = SQLGenerator()
        sql_code = sql_generator.generate(canonical_model)
        assert "SELECT" in sql_code or "FROM" in sql_code
    
    def test_expression_translation_pipeline(self):
        """Test expression translation through the pipeline."""
        # Test expression: UPPER(customer_name)
        expression = "UPPER(customer_name)"
        
        # Tokenize
        tokens = tokenize(expression)
        assert len(tokens) > 0
        
        # Parse
        parser = Parser(tokens)
        ast = parser.parse()
        assert ast is not None
        
        # Translate to PySpark
        pyspark_translator = PySparkTranslator()
        pyspark_code = pyspark_translator.visit(ast)
        assert "F.upper" in pyspark_code or "upper" in pyspark_code.lower()
        
        # Translate to SQL
        sql_translator = SQLTranslator()
        sql_code = sql_translator.visit(ast)
        assert "UPPER" in sql_code
    
    def test_complex_expression_translation(self):
        """Test translation of complex expressions."""
        expressions = [
            "IIF(customer_id > 100, 'VIP', 'Regular')",
            "NVL(email, 'no-email@example.com')",
            "CONCAT(first_name, ' ', last_name)",
            "TO_DATE(created_date, 'YYYY-MM-DD')"
        ]
        
        for expr in expressions:
            tokens = tokenize(expr)
            parser = Parser(tokens)
            ast = parser.parse()
            
            # Should not raise exception
            pyspark_translator = PySparkTranslator()
            pyspark_code = pyspark_translator.visit(ast)
            assert len(pyspark_code) > 0
            
            sql_translator = SQLTranslator()
            sql_code = sql_translator.visit(ast)
            assert len(sql_code) > 0
    
    def test_canonical_model_structure(self, tmp_path):
        """Test that canonical model has correct structure."""
        xml_content = """<?xml version="1.0"?>
<MAPPING NAME="M_TEST">
    <SOURCE NAME="SRC1">
        <TABLE NAME="table1"/>
    </SOURCE>
    <TARGET NAME="TGT1" TABLE="table2"/>
</MAPPING>"""
        
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content)
        
        parser = MappingParser(str(xml_file))
        raw_mapping = parser.parse()
        
        normalizer = MappingNormalizer()
        canonical_model = normalizer.normalize(raw_mapping)
        
        # Verify canonical model structure
        required_fields = [
            "sources",
            "targets",
            "transformations",
            "connectors",
            "lineage",
            "scd_type",
            "incremental_keys"
        ]
        
        # transformation_name or mapping_name should be present
        assert "transformation_name" in canonical_model or "mapping_name" in canonical_model, "Missing transformation_name or mapping_name"
        
        for field in required_fields:
            assert field in canonical_model, f"Missing field: {field}"
        
        assert isinstance(canonical_model["sources"], list)
        assert isinstance(canonical_model["targets"], list)
        assert isinstance(canonical_model["transformations"], list)
        assert isinstance(canonical_model["connectors"], list)
        assert isinstance(canonical_model["lineage"], dict)
        assert canonical_model["scd_type"] in ["SCD1", "SCD2", "SCD3", "NONE"]
        assert isinstance(canonical_model["incremental_keys"], list)

