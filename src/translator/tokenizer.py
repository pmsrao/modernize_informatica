
"""
Tokenizer module for Informatica expression parsing.
Production-grade with clear token definitions.
"""
import re
TOKEN_SPEC = [
    ("NUMBER", r"\d+(?:\.\d+)?"),
    ("STRING", r"'([^']*)'"),
    ("IDENT", r"[A-Za-z_][A-Za-z0-9_]*"),
    ("OP", r"<=|>=|<>|!=|==|\|\||=|<|>|\+|-|\*|/|\|"),
    ("COMMA", r","),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("WS", r"[ \t\n]+"),
    ("MISMATCH", r"."),
]
TOKEN_REGEX = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC))
def tokenize(expr: str):
    tokens = []
    for m in TOKEN_REGEX.finditer(expr):
        typ = m.lastgroup
        val = m.group()
        if typ == "WS":
            continue
        if typ == "MISMATCH":
            raise ValueError(f"Unexpected token: {val}")
        tokens.append((typ, val))
    return tokens
