# Source Component Type NULL Fix

## Root Cause Analysis

### Issue
`source_component_type` was NULL for some transformations, violating the design principle that all components should preserve their source component type when transformed into generic terminology.

### Root Causes Identified

1. **Nested Transformations Being Counted**
   - Nested transformations (EXPRESSION, LOOKUP, AGGREGATOR, etc. within a mapping) are created as `Transformation` nodes in Neo4j
   - These nested transformations have a `transformation` property pointing to their parent mapping
   - They don't have `source_component_type` set (and shouldn't, as they're not top-level components)
   - The queries in `get_canonical_overview` were counting ALL transformations, including nested ones
   - This caused Component Health metrics to be incorrect

2. **Main Transformations with NULL**
   - Some main transformations (mappings) might have `source_component_type = NULL` if:
     - They were created before the fix
     - The canonical model didn't have `source_component_type` set
   - These should always be `'mapping'`

## Fixes Applied

### 1. Updated Queries to Exclude Nested Transformations

**File**: `src/graph/graph_queries.py`

Changed all Component Health queries to only count main transformations (where `transformation IS NULL`):

```cypher
// Before
MATCH (t:Transformation)
WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL

// After
MATCH (t:Transformation)
WHERE (t.source_component_type = 'mapping' OR t.source_component_type IS NULL)
AND t.transformation IS NULL
```

This ensures:
- Only main transformations (mappings) are counted in Component Health metrics
- Nested transformations are excluded (they have `transformation` property set)

### 2. Ensured Nested Transformations Don't Get source_component_type

**File**: `src/graph/graph_store.py`

Updated `_create_transformation_tx` to explicitly remove `source_component_type` from nested transformations:

```cypher
MERGE (t:Transformation {name: $name, transformation: $transformation})
SET t += $props
// Ensure nested transformations don't have source_component_type
REMOVE t.source_component_type
```

This ensures nested transformations never have `source_component_type` set.

### 3. Created Fix Script

**File**: `scripts/fix_null_source_component_type.py`

Script to:
- Find all transformations with NULL `source_component_type`
- Identify which are main transformations (mappings) vs nested
- Fix main transformations that should be `'mapping'` (those with sources/targets)
- Verify the fix

## Design Principle

According to the design:
- **Main transformations** (mappings) should have `source_component_type: 'mapping'`
- **Nested transformations** (within mappings) should NOT have `source_component_type` (they're not top-level components)
- **Component Health metrics** should only count main transformations, not nested ones

## How to Run the Fix

1. **Restart the API** to load the updated queries
2. **Run the fix script** (if needed):
   ```bash
   python3 scripts/fix_null_source_component_type.py
   ```
   Note: Requires Python environment with dependencies installed

3. **Verify Component Health metrics** in the UI or via API

## Expected Results

After the fix:
- Component Health metrics should show correct percentages
- Only main transformations (mappings) are counted
- Nested transformations are excluded from metrics
- All main transformations have `source_component_type: 'mapping'`

## Files Changed

1. `src/graph/graph_queries.py`
   - Updated all Component Health queries to exclude nested transformations
   - Updated transformation count query

2. `src/graph/graph_store.py`
   - Updated `_create_transformation_tx` to remove `source_component_type` from nested transformations

3. `scripts/fix_null_source_component_type.py` (new)
   - Script to find and fix NULL `source_component_type` values

## Verification

To verify the fix worked:

1. Check Component Health metrics in UI - should show correct percentages
2. Query Neo4j directly:
   ```cypher
   // Count main transformations (should all have source_component_type = 'mapping')
   MATCH (t:Transformation)
   WHERE t.transformation IS NULL
   RETURN t.source_component_type, count(t) as count
   
   // Count nested transformations (should NOT have source_component_type)
   MATCH (t:Transformation)
   WHERE t.transformation IS NOT NULL
   RETURN t.source_component_type, count(t) as count
   ```

## Status

✅ **Fixed** - Queries now correctly exclude nested transformations and only count main transformations (mappings) in Component Health metrics.

