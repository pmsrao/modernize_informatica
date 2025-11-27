"""
PySpark Translator for AST → PySpark F API code.
Production-grade visitor with comprehensive function support.
"""
from typing import Any
from translator.ast_nodes import Identifier, Literal, BinaryOp, FunctionCall, PortReference, VariableReference
from translator.function_registry import FUNCTION_MAP, FUNCTION_ARGS


class PySparkTranslator:
    """Translates AST nodes to PySpark expressions."""
    
    def __init__(self):
        """Initialize translator."""
        self.function_map = FUNCTION_MAP
    
    def visit(self, node: Any) -> str:
        """Visit AST node and return PySpark expression string."""
        if isinstance(node, Identifier):
            return f"F.col('{node.name}')"
        
        if isinstance(node, Literal):
            if isinstance(node.value, str):
                return f"F.lit('{node.value}')"
            return f"F.lit({repr(node.value)})"
        
        if isinstance(node, BinaryOp):
            left = self.visit(node.left)
            right = self.visit(node.right)
            op = self._translate_operator(node.op)
            return f"({left} {op} {right})"
        
        if isinstance(node, FunctionCall):
            return self._translate_function(node)
        
        if isinstance(node, PortReference):
            # Port reference like :LKP.port_name
            return f"F.col('{node.transformation}_{node.port}')"
        
        if isinstance(node, VariableReference):
            # Variable reference like $$VAR
            if node.is_system:
                return f"F.lit(os.environ.get('{node.var_name}', ''))"
            return f"F.lit(variables.get('{node.var_name}', ''))"
        
        raise ValueError(f"Unsupported node type: {type(node)}")
    
    def _translate_operator(self, op: str) -> str:
        """Translate Informatica operators to Python operators."""
        operator_map = {
            "=": "==",
            "<>": "!=",
            "!=": "!=",
            "<": "<",
            ">": ">",
            "<=": "<=",
            ">=": ">=",
            "AND": "&",
            "OR": "|",
            "+": "+",
            "-": "-",
            "*": "*",
            "/": "/",
            "%": "%"
        }
        return operator_map.get(op.upper(), op)
    
    def _translate_function(self, func: FunctionCall) -> str:
        """Translate Informatica function to PySpark function."""
        name = func.name.upper()
        
        # Check if function is in registry
        if name not in self.function_map:
            # Fallback: try lowercase version
            fallback_name = name.lower()
            if fallback_name in dir(__import__('pyspark.sql.functions', fromlist=['F']).F):
                args_str = ', '.join(self.visit(a) for a in func.args)
                return f"F.{fallback_name}({args_str})"
            raise ValueError(f"Unsupported function: {name}")
        
        func_info = self.function_map[name]
        
        # Handle special cases
        if name == "IIF":
            if len(func.args) != 3:
                raise ValueError(f"IIF requires 3 arguments, got {len(func.args)}")
            cond, tcase, fcase = func.args
            return f"F.when({self.visit(cond)}, {self.visit(tcase)}).otherwise({self.visit(fcase)})"
        
        if name == "DECODE":
            # DECODE(value, search1, result1, search2, result2, ..., default)
            if len(func.args) < 3:
                raise ValueError(f"DECODE requires at least 3 arguments")
            value = func.args[0]
            when_exprs = []
            for i in range(1, len(func.args) - 1, 2):
                search = func.args[i]
                result = func.args[i + 1] if i + 1 < len(func.args) else None
                if result:
                    when_exprs.append(f"F.when({self.visit(value)} == {self.visit(search)}, {self.visit(result)})")
            
            default = func.args[-1] if len(func.args) % 2 == 0 else None
            if when_exprs:
                result = ".".join(when_exprs)
                if default:
                    result += f".otherwise({self.visit(default)})"
                return result
            return f"F.lit(None)"
        
        if name == "NVL":
            if len(func.args) != 2:
                raise ValueError(f"NVL requires 2 arguments")
            return f"F.coalesce({self.visit(func.args[0])}, {self.visit(func.args[1])})"
        
        if name == "NVL2":
            if len(func.args) != 3:
                raise ValueError(f"NVL2 requires 3 arguments")
            expr, not_null_val, null_val = func.args
            return f"F.when(F.isNotNull({self.visit(expr)}), {self.visit(not_null_val)}).otherwise({self.visit(null_val)})"
        
        if name == "CONCAT":
            # CONCAT can take variable arguments
            args_str = ', '.join(self.visit(a) for a in func.args)
            return f"F.concat({args_str})"
        
        if name == "SUBSTR" or name == "SUBSTRING":
            if len(func.args) < 2:
                raise ValueError(f"{name} requires at least 2 arguments")
            start = self.visit(func.args[1])
            length = self.visit(func.args[2]) if len(func.args) > 2 else "None"
            return f"F.substring({self.visit(func.args[0])}, {start}, {length})"
        
        if name == "TO_DATE":
            if len(func.args) < 2:
                return f"F.to_date({self.visit(func.args[0])})"
            return f"F.to_date({self.visit(func.args[0])}, {self.visit(func.args[1])})"
        
        if name == "TO_CHAR":
            if len(func.args) < 2:
                return f"F.col({self.visit(func.args[0])}).cast('string')"
            return f"F.date_format({self.visit(func.args[0])}, {self.visit(func.args[1])})"
        
        if name == "SYSDATE" or name == "SYSTIMESTAMP":
            return "F.current_timestamp()"
        
        if name == "ROUND":
            if len(func.args) == 1:
                return f"F.round({self.visit(func.args[0])})"
            return f"F.round({self.visit(func.args[0])}, {self.visit(func.args[1])})"
        
        # Default: use function name from registry
        func_name = func_info[0] if isinstance(func_info, tuple) else func_info
        args_str = ', '.join(self.visit(a) for a in func.args)
        return f"F.{func_name}({args_str})"
