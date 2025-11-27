"""SQL Translator for AST → SQL expressions.
Translates Informatica expressions to SQL syntax.
"""
from typing import Any
from translator.ast_nodes import Identifier, Literal, BinaryOp, FunctionCall, PortReference, VariableReference
from translator.function_registry import FUNCTION_MAP, FUNCTION_ARGS
from utils.logger import get_logger

logger = get_logger(__name__)


class SQLTranslator:
    """Translates AST nodes to SQL expressions."""
    
    def __init__(self):
        """Initialize SQL translator."""
        self.function_map = FUNCTION_MAP
    
    def visit(self, node: Any) -> str:
        """Visit AST node and return SQL expression string.
        
        Args:
            node: AST node to translate
            
        Returns:
            SQL expression as string
        """
        if isinstance(node, Identifier):
            # SQL column reference
            return f'"{node.name}"'
        
        if isinstance(node, Literal):
            if isinstance(node.value, str):
                # Escape single quotes in strings
                escaped = node.value.replace("'", "''")
                return f"'{escaped}'"
            elif isinstance(node.value, bool):
                return "TRUE" if node.value else "FALSE"
            elif node.value is None:
                return "NULL"
            return str(node.value)
        
        if isinstance(node, BinaryOp):
            left = self.visit(node.left)
            right = self.visit(node.right)
            op = self._translate_operator(node.op)
            return f"({left} {op} {right})"
        
        if isinstance(node, FunctionCall):
            return self._translate_function(node)
        
        if isinstance(node, PortReference):
            # Port reference like :LKP.port_name -> use column name
            return f'"{node.transformation}_{node.port}"'
        
        if isinstance(node, VariableReference):
            # Variable reference like $$VAR -> use parameter or literal
            if node.is_system:
                return f"'{node.var_name}'"  # System variable as literal
            return f":{node.var_name}"  # User variable as parameter
        
        raise ValueError(f"Unsupported node type: {type(node)}")
    
    def _translate_operator(self, op: str) -> str:
        """Translate Informatica operators to SQL operators."""
        operator_map = {
            "+": "+",
            "-": "-",
            "*": "*",
            "/": "/",
            "=": "=",
            "!=": "<>",
            "<>": "<>",
            "<": "<",
            ">": ">",
            "<=": "<=",
            ">=": ">=",
            "AND": "AND",
            "OR": "OR",
            "NOT": "NOT",
            "||": "||",  # SQL concatenation
        }
        return operator_map.get(op.upper(), op)
    
    def _translate_function(self, node: FunctionCall) -> str:
        """Translate Informatica function to SQL.
        
        Args:
            node: FunctionCall AST node
            
        Returns:
            SQL function expression
        """
        func_name = node.name.upper()
        args = [self.visit(arg) for arg in node.args]
        
        # Special handling for common functions
        if func_name == "IIF":
            # IIF(condition, true_value, false_value) -> CASE WHEN ... THEN ... ELSE ... END
            if len(args) == 3:
                return f"CASE WHEN {args[0]} THEN {args[1]} ELSE {args[2]} END"
            raise ValueError("IIF requires 3 arguments")
        
        if func_name == "DECODE":
            # DECODE(expr, val1, res1, val2, res2, default) -> CASE WHEN ... THEN ... ELSE ... END
            if len(args) < 3:
                raise ValueError("DECODE requires at least 3 arguments")
            if len(args) % 2 == 0:
                # Even number of args means no default
                default = "NULL"
            else:
                default = args[-1]
                args = args[:-1]
            
            expr = args[0]
            cases = []
            for i in range(1, len(args), 2):
                if i + 1 < len(args):
                    cases.append(f"WHEN {expr} = {args[i]} THEN {args[i+1]}")
            
            if cases:
                return f"CASE {' '.join(cases)} ELSE {default} END"
            return default
        
        if func_name == "NVL":
            # NVL(expr, default) -> COALESCE(expr, default)
            if len(args) == 2:
                return f"COALESCE({args[0]}, {args[1]})"
            raise ValueError("NVL requires 2 arguments")
        
        if func_name == "NVL2":
            # NVL2(expr, not_null_value, null_value) -> CASE WHEN expr IS NOT NULL THEN ... ELSE ... END
            if len(args) == 3:
                return f"CASE WHEN {args[0]} IS NOT NULL THEN {args[1]} ELSE {args[2]} END"
            raise ValueError("NVL2 requires 3 arguments")
        
        if func_name == "CONCAT":
            # CONCAT(str1, str2, ...) -> str1 || str2 || ...
            return " || ".join(args)
        
        if func_name == "SUBSTR" or func_name == "SUBSTRING":
            # SUBSTR(str, start, length) -> SUBSTRING(str, start, length)
            if len(args) >= 2:
                if len(args) == 2:
                    return f"SUBSTRING({args[0]}, {args[1]})"
                return f"SUBSTRING({args[0]}, {args[1]}, {args[2]})"
            raise ValueError("SUBSTR requires at least 2 arguments")
        
        if func_name == "INSTR":
            # INSTR(str, substr) -> POSITION(substr IN str)
            if len(args) >= 2:
                return f"POSITION({args[1]} IN {args[0]})"
            raise ValueError("INSTR requires at least 2 arguments")
        
        if func_name == "TO_DATE":
            # TO_DATE(str, format) -> CAST(str AS DATE) or TO_DATE(str, format)
            if len(args) >= 1:
                if len(args) == 1:
                    return f"CAST({args[0]} AS DATE)"
                return f"TO_DATE({args[0]}, {args[1]})"
            raise ValueError("TO_DATE requires at least 1 argument")
        
        if func_name == "TO_CHAR":
            # TO_CHAR(date, format) -> TO_CHAR(date, format)
            if len(args) >= 1:
                if len(args) == 1:
                    return f"CAST({args[0]} AS VARCHAR)"
                return f"TO_CHAR({args[0]}, {args[1]})"
            raise ValueError("TO_CHAR requires at least 1 argument")
        
        if func_name == "SYSDATE" or func_name == "SYSTIMESTAMP":
            return "CURRENT_TIMESTAMP"
        
        if func_name == "ADD_TO_DATE":
            # ADD_TO_DATE(date, interval_type, value) -> DATE_ADD or similar
            if len(args) >= 3:
                interval_type = args[1].upper().replace("'", "")
                value = args[2]
                date_expr = args[0]
                if "YEAR" in interval_type:
                    return f"DATE_ADD({date_expr}, INTERVAL {value} YEAR)"
                elif "MONTH" in interval_type:
                    return f"DATE_ADD({date_expr}, INTERVAL {value} MONTH)"
                elif "DAY" in interval_type:
                    return f"DATE_ADD({date_expr}, INTERVAL {value} DAY)"
                else:
                    return f"DATE_ADD({date_expr}, INTERVAL {value} {interval_type})"
            raise ValueError("ADD_TO_DATE requires 3 arguments")
        
        if func_name == "SUBTRACT_TO_DATE":
            # SUBTRACT_TO_DATE(date, interval_type, value) -> DATE_SUB
            if len(args) >= 3:
                interval_type = args[1].upper().replace("'", "")
                value = args[2]
                date_expr = args[0]
                if "YEAR" in interval_type:
                    return f"DATE_SUB({date_expr}, INTERVAL {value} YEAR)"
                elif "MONTH" in interval_type:
                    return f"DATE_SUB({date_expr}, INTERVAL {value} MONTH)"
                elif "DAY" in interval_type:
                    return f"DATE_SUB({date_expr}, INTERVAL {value} DAY)"
                else:
                    return f"DATE_SUB({date_expr}, INTERVAL {value} {interval_type})"
            raise ValueError("SUBTRACT_TO_DATE requires 3 arguments")
        
        if func_name == "DATE_DIFF":
            # DATE_DIFF(date1, date2) -> DATEDIFF(date1, date2)
            if len(args) == 2:
                return f"DATEDIFF({args[0]}, {args[1]})"
            raise ValueError("DATE_DIFF requires 2 arguments")
        
        if func_name == "MONTHS_BETWEEN":
            # MONTHS_BETWEEN(date1, date2) -> MONTHS_BETWEEN(date1, date2)
            if len(args) == 2:
                return f"MONTHS_BETWEEN({args[0]}, {args[1]})"
            raise ValueError("MONTHS_BETWEEN requires 2 arguments")
        
        if func_name == "YEAR":
            return f"YEAR({args[0]})" if args else "YEAR(CURRENT_DATE)"
        if func_name == "MONTH":
            return f"MONTH({args[0]})" if args else "MONTH(CURRENT_DATE)"
        if func_name == "DAY" or func_name == "DAYOFMONTH":
            return f"DAY({args[0]})" if args else "DAY(CURRENT_DATE)"
        if func_name == "HOUR":
            return f"HOUR({args[0]})" if args else "HOUR(CURRENT_TIMESTAMP)"
        if func_name == "MINUTE":
            return f"MINUTE({args[0]})" if args else "MINUTE(CURRENT_TIMESTAMP)"
        if func_name == "SECOND":
            return f"SECOND({args[0]})" if args else "SECOND(CURRENT_TIMESTAMP)"
        
        # Standard SQL functions (UPPER, LOWER, TRIM, LENGTH, etc.)
        sql_function_map = {
            "UPPER": "UPPER",
            "LOWER": "LOWER",
            "TRIM": "TRIM",
            "LTRIM": "LTRIM",
            "RTRIM": "RTRIM",
            "LENGTH": "LENGTH",
            "LPAD": "LPAD",
            "RPAD": "RPAD",
            "REPLACE": "REPLACE",
            "REPLACESTR": "REPLACE",
            "ABS": "ABS",
            "ROUND": "ROUND",
            "FLOOR": "FLOOR",
            "CEIL": "CEIL",
            "CEILING": "CEIL",
            "SQRT": "SQRT",
            "POWER": "POWER",
            "EXP": "EXP",
            "LOG": "LOG",
            "LOG10": "LOG10",
            "SIN": "SIN",
            "COS": "COS",
            "TAN": "TAN",
            "ASIN": "ASIN",
            "ACOS": "ACOS",
            "ATAN": "ATAN",
            "MAX": "MAX",
            "MIN": "MIN",
            "SUM": "SUM",
            "AVG": "AVG",
            "COUNT": "COUNT",
            "ISNULL": "IS NULL",
            "ISNOTNULL": "IS NOT NULL",
        }
        
        if func_name in sql_function_map:
            sql_func = sql_function_map[func_name]
            if func_name in ["ISNULL", "ISNOTNULL"]:
                # These are operators, not functions
                if args:
                    return f"({args[0]} {sql_func})"
                return sql_func
            if args:
                return f"{sql_func}({', '.join(args)})"
            return f"{sql_func}()"
        
        # Default: try to use function name as-is (may not work for all functions)
        logger.warning(f"Unknown function: {func_name}, using as-is")
        if args:
            return f"{func_name}({', '.join(args)})"
        return f"{func_name}()"

