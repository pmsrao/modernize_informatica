# Code Validation Process

## Overview

The `quality_score` that appears in the Component Health metrics is calculated by the **`CodeQualityChecker`** class during the code generation process.

## Validation Flow

### 1. **When Validation Happens**

Validation occurs automatically during code generation in `scripts/test_flow.py`:

```python
# In scripts/test_flow.py, _generate_code_workflow_aware() method
quality_score = None
try:
    from generators.code_quality_checker import CodeQualityChecker
    quality_checker = CodeQualityChecker()
    quality_report = quality_checker.check_code_quality(code, canonical_model)
    quality_score = quality_report.get("overall_score")
except Exception:
    pass  # Quality check is optional
```

### 2. **What Gets Validated**

The `CodeQualityChecker` (`src/generators/code_quality_checker.py`) performs comprehensive checks:

#### **Syntax Validation** (30% weight)
- Python/PySpark: Uses `ast.parse()` to validate syntax
- SQL: Checks for balanced parentheses and quotes
- **If syntax is invalid, overall score = 0**

#### **Type Safety** (15% weight)
- Missing type hints in function definitions
- Potential None/Null issues
- Missing null checks in DataFrame operations

#### **Performance Checks** (20% weight)
- Cartesian joins (missing join conditions)
- `collect()` usage (memory issues)
- Multiple DataFrame operations without caching
- Missing partition hints in write operations
- SQL queries without WHERE clauses

#### **Best Practices** (20% weight)
- Hardcoded values (passwords, API keys, localhost)
- Magic numbers
- Long functions (>50 lines)
- Missing docstrings
- Missing error handling in write operations

#### **Security Checks** (15% weight)
- SQL injection risks (string concatenation)
- `eval()` or `exec()` usage
- Hardcoded credentials

#### **Complexity Score**
- Based on lines of code
- Control flow statements (if, for, while, try)
- Function definitions
- Nesting depth

### 3. **How the Score is Calculated**

The `overall_score` (0-100) is calculated using weighted averages:

```python
weights = {
    "syntax": 0.30,        # 30% - syntax must be valid
    "type_safety": 0.15,   # 15%
    "performance": 0.20,   # 20%
    "best_practices": 0.20, # 20%
    "security": 0.15      # 15% - security is critical
}
```

**Scoring Rules:**
- If syntax is invalid → **score = 0**
- Performance score = 100 - (number of high/medium issues × 10)
- Security score = 100 - (number of issues × 25)
- Type safety and best practices have individual scores (0-100)

### 4. **Where the Score is Stored**

After validation, the `quality_score` is saved to Neo4j:

```python
# In scripts/test_flow.py
graph_store.save_code_metadata(
    mapping_name=transformation_name,
    code_type=code_type,
    file_path=rel_path,
    language=language,
    quality_score=quality_score  # <-- Stored here
)
```

This creates/updates a `GeneratedCode` node with the `quality_score` property and links it to the `Transformation` via `HAS_CODE` relationship.

### 5. **Component Health Metrics**

The Component Health metrics in the UI query Neo4j:

- **With Code**: Transformations with `HAS_CODE` relationship to `GeneratedCode`
- **Without Code**: Transformations without `HAS_CODE` relationship
- **Validated**: Transformations with code where `quality_score > 0`
- **Needs Review**: All transformations that aren't validated (`total - validated`)

## Complete Process Flow

The actual flow is more complex than just validation:

```
1. Parse XML → Raw Parsed Data
    ↓
2. Enhance → Canonical Model (technology-neutral JSON)
    ↓
3. Generate Code → PySpark/SQL Code (from canonical model)
    ↓
4. CodeQualityChecker → Calculates quality_score (0-100)
    ↓
5. Save to Neo4j → GeneratedCode.quality_score (during generation)
    ↓
6. AI Review (CodeReviewAgent) → Reviews code for issues
    ↓
7. Code Fix (CodeFixAgent) → Fixes issues if needed
    ↓
8. Final Code → Saved to workspace/generated_ai/
```

**Important Notes:**
- **Canonical Model comes FIRST** (before code generation)
- **Code is generated FROM canonical model**
- **Quality Score** is calculated during code generation (before AI review)
- **AI Review** happens AFTER code generation (separate step)
- **"Validated" metric** currently only reflects `quality_score > 0`, not AI review status

## Validation Process Summary

```
Code Generation (from Canonical Model)
    ↓
CodeQualityChecker.check_code_quality()
    ↓
Checks: Syntax, Type Safety, Performance, Best Practices, Security
    ↓
Calculates overall_score (0-100)
    ↓
Saves to Neo4j: GeneratedCode.quality_score
    ↓
[Later: AI Review happens separately]
    ↓
Component Health UI displays: quality_score > 0 = "Validated"
```

## Notes

- **Validation is optional**: If `CodeQualityChecker` fails to import or raises an exception, code generation continues without a quality score
- **Score of 0**: Can mean either syntax errors or very poor code quality
- **Score > 0**: Indicates the code passed basic validation checks
- **Higher scores**: Indicate better code quality (fewer issues, better practices)

## AI Review Status Tracking

**✅ IMPLEMENTED**: The system now tracks AI review status separately from quality_score:

- `ai_reviewed`: Boolean indicating if CodeReviewAgent has reviewed the code
- `ai_review_score`: Score from AI review (0-100, separate from quality_score)
- `ai_fixed`: Boolean indicating if code was fixed by CodeFixAgent

**Component Health Metrics Now Show:**
- **Validated**: Code has `quality_score > 0` (basic validation passed during generation)
- **AI Reviewed**: Code has been reviewed by AI agents (CodeReviewAgent)
- **AI Fixed**: Code has been fixed by AI agents (CodeFixAgent)

**Implementation Details:**
- `GraphStore.update_ai_review_status()`: Saves AI review metadata to Neo4j
- `test_flow.py`: Calls this method after AI review completes
- `graph_queries.py`: Queries for AI review status in Component Health
- UI displays all three metrics separately

## Related Files

- `src/generators/code_quality_checker.py` - Main validation logic
- `scripts/test_flow.py` - Calls validation during code generation
- `src/graph/graph_store.py` - Saves quality_score to Neo4j
- `src/graph/graph_queries.py` - Queries quality_score for Component Health metrics

