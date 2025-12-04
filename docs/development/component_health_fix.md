# Component Health Metrics Fix

## Issue

Component Health metrics were showing very low percentages:
- With Code: 5%
- Without Code: 95%
- Validated: 5%
- AI Reviewed: 5%
- AI Fixed: 5%
- Needs Review: 95%

## Root Cause

The issue was in `src/graph/graph_store.py` in the `_create_code_metadata_tx` function. When saving code metadata, the function was trying to create a `HAS_CODE` relationship between a `Transformation` node and a `GeneratedCode` node using this query:

```cypher
MATCH (t:Transformation {name: $mapping_name, source_component_type: 'mapping'})
MERGE (t)-[:HAS_CODE]->(c)
```

**Problem**: This query required BOTH:
1. `name` = `mapping_name` 
2. `source_component_type` = `'mapping'`

However, some transformations in Neo4j might have:
- `source_component_type` = `NULL` (not set)
- `source_component_type` = `'mapping'` (correctly set)

If a transformation had `source_component_type` = `NULL`, the MATCH would fail silently, and the `HAS_CODE` relationship would never be created. This resulted in:
- GeneratedCode nodes existing in Neo4j
- But no relationships to Transformation nodes
- Component Health metrics showing low "With Code" percentages

## Solution

### 1. Fixed the Query in `_create_code_metadata_tx`

Changed the query to be more flexible:

```cypher
MATCH (t:Transformation {name: $mapping_name})
WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
MERGE (t)-[:HAS_CODE]->(c)
```

This now matches transformations where `source_component_type` is either `'mapping'` OR `NULL`.

### 2. Added Better Error Handling

Added logging to detect when relationships fail to be created:

```python
result = tx.run("""
    MERGE (c:GeneratedCode {file_path: $file_path})
    SET c += $props
    WITH c
    MATCH (t:Transformation {name: $mapping_name})
    WHERE t.source_component_type = 'mapping' OR t.source_component_type IS NULL
    MERGE (t)-[r:HAS_CODE]->(c)
    RETURN t.name as transformation_name, r
""", ...)

match_result = result.single()
if not match_result:
    logger.warning(f"Failed to create HAS_CODE relationship for mapping '{mapping_name}'...")
```

### 3. Initialize AI Review Fields

Added initialization of AI review fields when creating GeneratedCode nodes:

```python
code_props = {
    ...
    "ai_reviewed": False,
    "ai_review_score": None,
    "ai_fixed": False,
    "ai_reviewed_at": None,
    "ai_fixed_at": None
}
```

### 4. Created Fix Script

Created `scripts/fix_component_health.py` to:
- Find all orphaned GeneratedCode nodes (no HAS_CODE relationship)
- Link them to transformations by matching `mapping_name`
- Verify the fixes by checking Component Health metrics

## How to Fix Existing Data

Run the fix script to link existing orphaned GeneratedCode nodes:

```bash
python3 scripts/fix_component_health.py
```

This will:
1. Find all GeneratedCode nodes without HAS_CODE relationships
2. Try to match them to transformations by `mapping_name`
3. Create the missing HAS_CODE relationships
4. Show updated Component Health metrics

## Verification

After running the fix script, check the Component Health metrics in the UI or via API:

```bash
curl http://localhost:8000/api/graph/canonical/overview | jq '.component_health'
```

Expected results:
- **With Code**: Should increase significantly (closer to 100% if all transformations have code)
- **Validated**: Should increase if code has quality scores
- **AI Reviewed**: Should increase if code has been reviewed
- **Needs Review**: Should decrease accordingly

## Prevention

Going forward, all new code metadata will be saved with the fixed query, so this issue should not recur. The fix ensures that:

1. Transformations with `source_component_type = 'mapping'` are matched
2. Transformations with `source_component_type = NULL` are also matched
3. Failed relationship creation is logged for debugging

## Files Changed

1. `src/graph/graph_store.py`
   - `_create_code_metadata_tx()`: Fixed MATCH query to handle NULL source_component_type
   - Added error handling and logging
   - Initialize AI review fields

2. `scripts/fix_component_health.py` (new)
   - Script to fix existing orphaned GeneratedCode nodes

## Related Issues

- Component Health metrics showing low percentages
- GeneratedCode nodes not linked to transformations
- AI review status not being tracked correctly

## Status

✅ **Fixed** - The query now handles both `source_component_type = 'mapping'` and `NULL` cases.

