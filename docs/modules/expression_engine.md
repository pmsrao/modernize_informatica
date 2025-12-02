# Expression AST Engine

## Role

Informatica expressions are complex and tool-specific. The AST engine:

1. Parses these expressions into a structured AST
2. Translates them to PySpark and SQL
3. Provides inputs for AI-based explanations and risk analysis

---

## Stages

1. **Tokenization**
   - Splits expression into tokens: identifiers, functions, literals, operators.

2. **Parsing into AST**
   - Applies a grammar to build a tree:
     - binary operations (+, -, *, /, <, >, =…)
     - function calls (IIF, NVL, DECODE, TO_CHAR, etc.)
     - conditionals (nested IIF)

3. **AST Normalization**
   - Aligns function semantics with target platforms.

4. **Translation**
   - AST → PySpark expression string
   - AST → SQL expression string

---

## Example

**Informatica Expression**
```
IIF(AGE < 30, 'YOUNG', 'OTHER')
```

**PySpark Translation**
```python
F.when(F.col("AGE") < 30, F.lit("YOUNG")).otherwise("OTHER")
```

**SQL Translation**
```sql
CASE WHEN AGE < 30 THEN 'YOUNG' ELSE 'OTHER' END
```

The AST engine ensures a single source of truth for these semantics, which reduces drift between SQL and PySpark.

---

## Supported Functions

The engine supports common Informatica functions:

- **Conditional**: IIF, DECODE
- **String**: TO_CHAR, SUBSTR, CONCAT
- **Numeric**: ROUND, TRUNC, ABS
- **Date**: TO_DATE, DATE_DIFF
- **Null Handling**: NVL, ISNULL

---

**Next**: Learn about [Code Generators](code_generators.md) that use the AST.

