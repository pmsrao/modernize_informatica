"""Unit tests for translators."""
import pytest
from translator import PySparkTranslator, SQLTranslator, tokenize, Parser
from translator.ast_nodes import Identifier, Literal, BinaryOp, FunctionCall, PortReference, VariableReference


class TestPySparkTranslator:
    """Tests for PySparkTranslator."""
    
    def test_translate_identifier(self):
        """Test translating identifier to PySpark."""
        translator = PySparkTranslator()
        node = Identifier("customer_id")
        result = translator.visit(node)
        assert result == "F.col('customer_id')"
    
    def test_translate_literal_string(self):
        """Test translating string literal."""
        translator = PySparkTranslator()
        node = Literal("test")
        result = translator.visit(node)
        assert "F.lit('test')" in result
    
    def test_translate_literal_number(self):
        """Test translating number literal."""
        translator = PySparkTranslator()
        node = Literal(42)
        result = translator.visit(node)
        assert "F.lit(42)" in result
    
    def test_translate_binary_op(self):
        """Test translating binary operation."""
        translator = PySparkTranslator()
        node = BinaryOp(
            Identifier("a"),
            "+",
            Identifier("b")
        )
        result = translator.visit(node)
        assert "+" in result
        assert "F.col('a')" in result
        assert "F.col('b')" in result
    
    def test_translate_iif_function(self):
        """Test translating IIF function."""
        translator = PySparkTranslator()
        node = FunctionCall(
            "IIF",
            [
                BinaryOp(Identifier("x"), ">", Literal(0)),
                Literal("positive"),
                Literal("negative")
            ]
        )
        result = translator.visit(node)
        assert "F.when" in result
        assert "otherwise" in result
    
    def test_translate_port_reference(self):
        """Test translating port reference."""
        translator = PySparkTranslator()
        node = PortReference("LKP", "customer_name")
        result = translator.visit(node)
        assert "LKP_customer_name" in result
    
    def test_translate_variable_reference(self):
        """Test translating variable reference."""
        translator = PySparkTranslator()
        node = VariableReference("VAR1", is_system=False)
        result = translator.visit(node)
        assert "variables.get" in result or "os.environ" in result
    
    def test_translate_expression(self):
        """Test translating a complete expression."""
        tokens = tokenize("UPPER(customer_name)")
        parser = Parser(tokens)
        ast = parser.parse()
        
        translator = PySparkTranslator()
        result = translator.visit(ast)
        assert "F.upper" in result or "F.col('customer_name')" in result


class TestSQLTranslator:
    """Tests for SQLTranslator."""
    
    def test_translate_identifier(self):
        """Test translating identifier to SQL."""
        translator = SQLTranslator()
        node = Identifier("customer_id")
        result = translator.visit(node)
        assert '"customer_id"' in result
    
    def test_translate_literal_string(self):
        """Test translating string literal to SQL."""
        translator = SQLTranslator()
        node = Literal("test")
        result = translator.visit(node)
        assert "'test'" in result
    
    def test_translate_literal_number(self):
        """Test translating number literal to SQL."""
        translator = SQLTranslator()
        node = Literal(42)
        result = translator.visit(node)
        assert "42" in result
    
    def test_translate_binary_op(self):
        """Test translating binary operation to SQL."""
        translator = SQLTranslator()
        node = BinaryOp(
            Identifier("a"),
            "+",
            Identifier("b")
        )
        result = translator.visit(node)
        assert "+" in result
        assert '"a"' in result
        assert '"b"' in result
    
    def test_translate_iif_function(self):
        """Test translating IIF function to SQL CASE."""
        translator = SQLTranslator()
        node = FunctionCall(
            "IIF",
            [
                BinaryOp(Identifier("x"), ">", Literal(0)),
                Literal("positive"),
                Literal("negative")
            ]
        )
        result = translator.visit(node)
        assert "CASE" in result
        assert "WHEN" in result
        assert "THEN" in result
        assert "ELSE" in result
        assert "END" in result
    
    def test_translate_decode_function(self):
        """Test translating DECODE function to SQL CASE."""
        translator = SQLTranslator()
        node = FunctionCall(
            "DECODE",
            [
                Identifier("status"),
                Literal("A"),
                Literal("Active"),
                Literal("I"),
                Literal("Inactive"),
                Literal("Unknown")
            ]
        )
        result = translator.visit(node)
        assert "CASE" in result
        assert "WHEN" in result
        assert "ELSE" in result
    
    def test_translate_nvl_function(self):
        """Test translating NVL function to SQL COALESCE."""
        translator = SQLTranslator()
        node = FunctionCall(
            "NVL",
            [
                Identifier("value"),
                Literal(0)
            ]
        )
        result = translator.visit(node)
        assert "COALESCE" in result
    
    def test_translate_concat_function(self):
        """Test translating CONCAT function to SQL ||."""
        translator = SQLTranslator()
        node = FunctionCall(
            "CONCAT",
            [
                Identifier("first_name"),
                Literal(" "),
                Identifier("last_name")
            ]
        )
        result = translator.visit(node)
        assert "||" in result
    
    def test_translate_port_reference(self):
        """Test translating port reference to SQL."""
        translator = SQLTranslator()
        node = PortReference("LKP", "customer_name")
        result = translator.visit(node)
        assert "LKP_customer_name" in result
    
    def test_translate_variable_reference(self):
        """Test translating variable reference to SQL."""
        translator = SQLTranslator()
        node = VariableReference("VAR1", is_system=False)
        result = translator.visit(node)
        assert ":VAR1" in result or "'VAR1'" in result


class TestTokenizer:
    """Tests for tokenizer."""
    
    def test_tokenize_simple_expression(self):
        """Test tokenizing a simple expression."""
        tokens = tokenize("customer_id + 10")
        assert len(tokens) > 0
        assert any(t.value == "customer_id" for t in tokens)
        assert any(t.value == "+" for t in tokens)
        assert any(t.value == 10 for t in tokens)
    
    def test_tokenize_function_call(self):
        """Test tokenizing a function call."""
        tokens = tokenize("UPPER(customer_name)")
        assert len(tokens) > 0
        assert any(t.value == "UPPER" for t in tokens)
    
    def test_tokenize_string_literal(self):
        """Test tokenizing string literal."""
        tokens = tokenize("'test string'")
        assert len(tokens) > 0
        assert any(t.value == "test string" for t in tokens)


class TestParser:
    """Tests for expression parser."""
    
    def test_parse_simple_expression(self):
        """Test parsing a simple expression."""
        tokens = tokenize("a + b")
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)
        assert ast.op == "+"
    
    def test_parse_function_call(self):
        """Test parsing a function call."""
        tokens = tokenize("UPPER(name)")
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, FunctionCall)
        assert ast.name == "UPPER"
    
    def test_parse_nested_expression(self):
        """Test parsing nested expression."""
        tokens = tokenize("a + (b * c)")
        parser = Parser(tokens)
        ast = parser.parse()
        assert isinstance(ast, BinaryOp)

