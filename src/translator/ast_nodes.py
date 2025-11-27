"""
AST Node Definitions for Informatica Expression Parsing.
Clean, production-ready implementation.
"""
from typing import List, Any


class ASTNode: 
    """Base class for all AST nodes."""
    pass


class Identifier(ASTNode):
    """Represents a field/column identifier."""
    def __init__(self, name: str):
        self.name = name
    
    def __repr__(self):
        return f"Identifier({self.name})"


class Literal(ASTNode):
    """Represents a literal value (string, number, etc.)."""
    def __init__(self, value: Any):
        self.value = value
    
    def __repr__(self):
        return f"Literal({repr(self.value)})"


class BinaryOp(ASTNode):
    """Represents a binary operation (+, -, *, /, =, <, >, etc.)."""
    def __init__(self, left: ASTNode, op: str, right: ASTNode):
        self.left = left
        self.op = op
        self.right = right
    
    def __repr__(self):
        return f"BinaryOp({self.left}, {self.op}, {self.right})"


class FunctionCall(ASTNode):
    """Represents a function call."""
    def __init__(self, name: str, args: List[ASTNode]):
        self.name = name.upper()
        self.args = args
    
    def __repr__(self):
        return f"FunctionCall({self.name}, {self.args})"


class PortReference(ASTNode):
    """Represents a port reference like :LKP.port_name or :AGG.port_name."""
    def __init__(self, transformation: str, port: str):
        self.transformation = transformation
        self.port = port
    
    def __repr__(self):
        return f"PortReference({self.transformation}.{self.port})"


class VariableReference(ASTNode):
    """Represents a variable reference like $$VAR or $$PMRootDir."""
    def __init__(self, var_name: str, is_system: bool = False):
        self.var_name = var_name
        self.is_system = is_system
    
    def __repr__(self):
        sys_str = "system" if self.is_system else "user"
        return f"VariableReference($${self.var_name}, {sys_str})"
