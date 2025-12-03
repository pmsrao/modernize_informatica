
"""
Pratt Parser for Informatica expressions.
Clean production-grade implementation.
"""
from translator.tokenizer import tokenize
from translator.ast_nodes import Identifier, Literal, BinaryOp, FunctionCall

PRECEDENCE = {
    "OR": 1, "AND": 2,
    "=": 3, "<": 3, ">": 3, "<=": 3, ">=": 3, "<>":3, "!=":3, "==": 3,
    "||": 3,  # String concatenation operator
    "|": 3,   # Pipe operator (bitwise OR)
    "+": 4, "-": 4,
    "*": 5, "/": 5
}

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else (None,None)

    def advance(self):
        t = self.peek()
        self.pos += 1
        return t

    def parse(self):
        return self.parse_expr()

    def parse_expr(self, prec=0):
        left = self.parse_primary()
        while True:
            ttype, tval = self.peek()
            if ttype == "OP" or (ttype=="IDENT" and tval.upper() in ("AND","OR")):
                op = tval.upper() if ttype == "IDENT" else tval
                op_prec = PRECEDENCE.get(op)
                if op_prec and op_prec > prec:
                    self.advance()
                    right = self.parse_expr(op_prec)
                    left = BinaryOp(left, op, right)
                else:
                    break
            else:
                break
        return left

    def parse_primary(self):
        ttype, tval = self.advance()
        if ttype == "NUMBER":
            return Literal(float(tval) if "." in tval else int(tval))
        if ttype == "STRING":
            return Literal(tval.strip("'"))
        if ttype == "IDENT":
            nt, nv = self.peek()
            if nt == "LPAREN":
                return self.parse_func(tval)
            return Identifier(tval)
        if ttype == "LPAREN":
            expr = self.parse_expr()
            self.advance()
            return expr
        if ttype == "OP":
            # Operators should be handled in parse_expr, not here
            # This is a fallback for unexpected operator positions
            raise ValueError(f"Unexpected operator in primary expression: {tval}")
        raise ValueError(f"Unexpected token in primary: {tval}")

    def parse_func(self, name):
        self.advance()  # LPAREN
        args = []
        while True:
            if self.peek()[0] == "RPAREN":
                self.advance()
                break
            args.append(self.parse_expr())
            if self.peek()[0] == "COMMA":
                self.advance()
                continue
            if self.peek()[0] == "RPAREN":
                self.advance()
                break
        return FunctionCall(name, args)
