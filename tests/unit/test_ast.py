"""Unit tests for AST nodes."""
import pytest
from translator.ast_nodes import (
    Identifier, Literal, BinaryOp, FunctionCall,
    PortReference, VariableReference
)


class TestASTNodes:
    """Tests for AST node classes."""
    
    def test_identifier(self):
        """Test Identifier node."""
        node = Identifier("customer_id")
        assert node.name == "customer_id"
        assert "customer_id" in repr(node)
    
    def test_literal_string(self):
        """Test Literal node with string."""
        node = Literal("test")
        assert node.value == "test"
        assert isinstance(node.value, str)
    
    def test_literal_number(self):
        """Test Literal node with number."""
        node = Literal(42)
        assert node.value == 42
        assert isinstance(node.value, int)
    
    def test_literal_boolean(self):
        """Test Literal node with boolean."""
        node = Literal(True)
        assert node.value is True
        assert isinstance(node.value, bool)
    
    def test_binary_op(self):
        """Test BinaryOp node."""
        left = Identifier("a")
        right = Identifier("b")
        node = BinaryOp(left, "+", right)
        
        assert node.left == left
        assert node.right == right
        assert node.op == "+"
    
    def test_function_call(self):
        """Test FunctionCall node."""
        args = [Identifier("x"), Literal(10)]
        node = FunctionCall("UPPER", args)
        
        assert node.name == "UPPER"
        assert len(node.args) == 2
        assert node.args[0] == args[0]
        assert node.args[1] == args[1]
    
    def test_port_reference(self):
        """Test PortReference node."""
        node = PortReference("LKP", "customer_name")
        
        assert node.transformation == "LKP"
        assert node.port == "customer_name"
        assert "LKP" in repr(node)
        assert "customer_name" in repr(node)
    
    def test_variable_reference(self):
        """Test VariableReference node."""
        node = VariableReference("VAR1", is_system=False)
        
        assert node.var_name == "VAR1"
        assert node.is_system is False
        
        system_node = VariableReference("PMRootDir", is_system=True)
        assert system_node.is_system is True
    
    def test_nested_ast(self):
        """Test nested AST structure."""
        # Create: (a + b) * c
        add_node = BinaryOp(
            Identifier("a"),
            "+",
            Identifier("b")
        )
        mult_node = BinaryOp(
            add_node,
            "*",
            Identifier("c")
        )
        
        assert isinstance(mult_node.left, BinaryOp)
        assert mult_node.op == "*"
        assert isinstance(mult_node.right, Identifier)
