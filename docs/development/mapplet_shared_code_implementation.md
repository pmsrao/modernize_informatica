# Mapplet Shared Code Generation Implementation

## Overview

Implemented standalone shared code generation for mapplets (ReusableTransformations), extracting them to `shared/common_utils_pyspark.py` and saving code metadata to Neo4j.

## Changes Made

### 1. GraphStore Updates (`src/graph/graph_store.py`)

#### Added `component_type` parameter to `save_code_metadata()`
- Now accepts `component_type` parameter ('mapping' or 'mapplet')
- Routes to appropriate transaction function based on component type

#### Added `_create_mapplet_code_metadata_tx()` method
- Creates `GeneratedCode` nodes for mapplets
- Links `ReusableTransformation` nodes to `GeneratedCode` via `HAS_CODE` relationship
- Stores mapplet-specific metadata (`mapplet_name`)

### 2. PySparkGenerator Updates (`src/generators/pyspark_generator.py`)

#### Added `generate_mapplet_function()` method
- Generates standalone Python functions for mapplets
- Function signature: `def mapplet_{mapplet_name}(df, **kwargs):`
- Handles input/output ports
- Generates code for all transformations within the mapplet
- Returns properly formatted function code

**Example Output:**
```python
def mapplet_calculate_totals(df, **kwargs):
    """Mapplet: MPL_CALCULATE_TOTALS
    Input ports: AMOUNT, QUANTITY
    Output ports: TOTAL_AMOUNT, TOTAL_QUANTITY
    """
    # Transformation: AGG_TOTALS (AGGREGATOR)
    df = df.groupBy(...).agg(...)
    
    return df.select(F.col('TOTAL_AMOUNT'), F.col('TOTAL_QUANTITY'))
```

### 3. TestFlow Updates (`scripts/test_flow.py`)

#### Enhanced `_generate_shared_code()` method
- Now accepts `version_store`, `graph_store`, and `generators` parameters
- Loads mapplets from Neo4j graph or version store
- Generates mapplet functions using `PySparkGenerator.generate_mapplet_function()`
- Writes all mapplet functions to `shared/common_utils_pyspark.py`
- Saves code metadata for each mapplet to Neo4j

#### Updated all calls to `_generate_shared_code()`
- `_generate_code_workflow_aware()`: Passes version_store, graph_store, generators
- `_generate_code_workflow_aware_from_files()`: Passes version_store, generators

### 4. Component Health Metrics (`src/graph/graph_queries.py`)

#### Already Updated (from previous fix)
- Queries now include ReusableTransformations in Component Health metrics
- Counts both mappings and mapplets
- Tracks code, validation, AI review, and AI fix status for mapplets

## File Structure

### Generated Files

```
workspace/generated/shared/
├── common_utils_pyspark.py    # NEW: Contains all mapplet functions
├── common_utils.py            # Legacy: Empty template (backward compatibility)
└── config/
    ├── database_config.py
    └── spark_config.py
```

### Neo4j Structure

```
(ReusableTransformation {name: "MPL_CALCULATE_TOTALS"})
  -[:HAS_CODE]->
(GeneratedCode {
  file_path: "workspace/generated/shared/common_utils_pyspark.py",
  mapplet_name: "MPL_CALCULATE_TOTALS",
  code_type: "pyspark",
  language: "python",
  quality_score: <score>,
  ai_reviewed: <bool>,
  ai_fixed: <bool>
})
```

## Usage in Mapping Code

Mapplets can now be used in two ways:

### Option 1: Import and Call (Recommended)
```python
from shared.common_utils_pyspark import mapplet_calculate_totals

# In mapping code:
df = mapplet_calculate_totals(df)
```

### Option 2: Inline (Current Behavior)
Mapplets are still inlined into mapping code when used as instances, but the standalone functions are available for reuse.

## Component Health Metrics

After implementation, Component Health will show:
- **Total**: Mappings + Mapplets (e.g., 1 + 2 = 3)
- **With Code**: Mappings with code + Mapplets with code
- **Validated**: Mappings validated + Mapplets validated
- **AI Reviewed**: Mappings reviewed + Mapplets reviewed
- **AI Fixed**: Mappings fixed + Mapplets fixed

## Testing

To test the implementation:

1. **Run code generation:**
   ```bash
   python3 scripts/test_flow.py --step generate-code
   ```

2. **Verify shared code file:**
   ```bash
   cat workspace/generated/shared/common_utils_pyspark.py
   ```

3. **Check Neo4j relationships:**
   ```cypher
   MATCH (rt:ReusableTransformation)-[:HAS_CODE]->(c:GeneratedCode)
   RETURN rt.name, c.file_path, c.mapplet_name
   ```

4. **Verify Component Health metrics:**
   - Check UI or API: `GET /api/graph/canonical/overview`
   - Should show mapplets included in metrics

## CLI Operations

**No changes needed** - CLI doesn't handle code generation. Code generation is handled by `test_flow.py`, which has been updated.

## Backward Compatibility

- Existing `common_utils.py` file is preserved (empty template)
- New `common_utils_pyspark.py` contains actual mapplet functions
- Mapplet inlining in mapping code still works (dual approach)
- Component Health metrics work with or without mapplet code

## Status

✅ **Completed**
- GraphStore supports mapplet code metadata
- PySparkGenerator generates mapplet functions
- TestFlow generates shared code and saves metadata
- Component Health metrics include mapplets
- CLI operations verified (no changes needed)

## Next Steps

1. Test the implementation with actual mapplets
2. Verify Component Health metrics update correctly
3. Consider updating mapping code generators to use imported mapplet functions instead of inlining

