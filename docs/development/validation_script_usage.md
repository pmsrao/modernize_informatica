# Canonical Model Enhancements Validation Script

## Overview

The validation script (`scripts/validate_canonical_model_enhancements.py`) verifies that all new canonical model enhancements are working correctly after running the test flow.

## Usage

```bash
# Run validation after test flow completes
python scripts/validate_canonical_model_enhancements.py
```

## What It Validates

The script checks the following features:

### 1. Field and Port Nodes ✅
- Verifies that `:Field` and `:Port` nodes are created in Neo4j
- Checks relationships: `(:Port)-[:HAS_FIELD]->(:Field)` and `(:Transformation)-[:HAS_PORT]->(:Port)`

### 2. Field-Level Lineage ✅
- Checks for `DERIVED_FROM` relationships between fields
- Checks for `FEEDS` relationships between fields
- Validates field-level lineage paths exist

### 3. Complexity Metrics ✅
- Verifies `complexity_score` is stored on `:Transformation` nodes
- Checks for `cyclomatic_complexity` and other metrics
- Validates complexity metrics exist in canonical model JSON files

### 4. Semantic Tags ✅
- Checks for `semantic_tags` array on `:Transformation` nodes
- Validates tags are detected and stored correctly
- Shows tag distribution

### 5. Structured Runtime Configuration ✅
- Verifies `task_runtime_config` is extracted and stored for tasks
- Verifies `workflow_runtime_config` is extracted and stored for pipelines
- Checks parsed files for structured config

### 6. Enhanced SCD Structure ✅
- Validates SCD type information is stored
- Checks for enhanced SCD structure in canonical models
- Shows SCD type distribution

### 7. Control Task Node Types ✅
- Verifies `:DecisionTask` nodes are created
- Verifies `:AssignmentTask` nodes are created
- Verifies `:CommandTask` nodes are created
- Verifies `:EventTask` nodes are created

## Output

The script outputs:
- Real-time validation status for each feature
- Detailed counts and statistics
- Summary report at the end
- JSON results file: `test_log/canonical_model_validation.json`

## Example Output

```
================================================================================
CANONICAL MODEL ENHANCEMENTS VALIDATION
================================================================================

🔍 Validating Field and Port nodes...
   ✅ Found 22 Port nodes (Fields: 0)

🔍 Validating field-level lineage relationships...
   ⚠️  No field-level lineage relationships found (may be normal)

🔍 Validating complexity metrics...
   ✅ Found complexity metrics for 1 transformations

🔍 Validating semantic tags...
   ✅ Found semantic tags for 1 transformations
      Tags: scd2, lookup-heavy

🔍 Validating structured runtime configuration...
   ✅ Found structured runtime config for 2 components

🔍 Validating enhanced SCD structure...
   ✅ Found SCD information for 1 transformations

🔍 Validating control task node types...
   ✅ Found 3 control task nodes

================================================================================
VALIDATION SUMMARY
================================================================================
...
```

## Interpreting Results

### ✅ PASS
Feature is working correctly. All expected data is present.

### ⚠️ WARNING
Feature may not be applicable (e.g., no control tasks in workflows, no SCD patterns in transformations). This is often normal.

### ❌ FAIL
Feature is not working. Expected data is missing. Review the implementation.

### ❌ ERROR
Error occurred during validation. Check the error message for details.

## When to Run

Run the validation script:
- After running `make test-all`
- After dropping and recreating Neo4j schema
- After making changes to canonical model code
- Before committing changes

## Troubleshooting

### "No Field or Port nodes found"
- Check if `make test-all` completed successfully
- Verify Neo4j schema was created: `python scripts/schema/create_neo4j_schema.py`
- Check if transformations were parsed and saved to Neo4j

### "No field-level lineage relationships found"
- This may be normal if transformations don't have expressions
- Check if transformations have output ports with expressions
- Verify `DERIVED_FROM` relationships are created in `graph_store.py`

### "No complexity metrics found"
- Check if `ComplexityCalculator` is imported and used in `mapping_normalizer.py`
- Verify transformations were normalized after adding complexity calculation

### "No semantic tags found"
- Check if `SemanticTagDetector` is imported and used in `mapping_normalizer.py`
- Verify transformations match tag detection patterns

### "No structured runtime config found"
- Check if `RuntimeConfigNormalizer` is used in parsers
- Verify sessions/workflows were parsed after adding runtime config normalization

### "No control task nodes found"
- This may be normal if workflows don't have control tasks
- Check if workflows have Decision, Assignment, Command, or Event tasks
- Verify control tasks are parsed and saved correctly

## Integration with CI/CD

The script exits with code 1 if there are errors, making it suitable for CI/CD:

```bash
python scripts/validate_canonical_model_enhancements.py || exit 1
```

