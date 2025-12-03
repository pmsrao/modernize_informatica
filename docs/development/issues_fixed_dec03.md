# Issues Found and Fixed - December 3, 2025

## Summary

After reviewing `test_log/exec_steps_logs.txt` and `test_log/canonical_model_validation.json`, several issues were identified and fixed.

## Issues Found

### 1. ❌ `name 're' is not defined` (CRITICAL)
**Location**: `src/graph/graph_store.py:329`  
**Error**: `re.findall()` used but `re` module not imported  
**Impact**: Failed to save `M_STAGE_CUSTOMERS_ENHANCED` to Neo4j, causing EXECUTES relationship failure  
**Fix**: Added `import re` at the top of `graph_store.py`  
**Status**: ✅ FIXED

### 2. ❌ `name 'parse_ai_dir' is not defined` (HIGH)
**Location**: `scripts/test_flow.py:251`  
**Error**: Variable `parse_ai_dir` used before definition  
**Impact**: Failed to save mapplets to version store  
**Fix**: Added `parse_ai_dir = os.path.join(base_dir, "parse_ai")` before use  
**Status**: ✅ FIXED

### 3. ❌ `cannot access local variable 'task_props'` (HIGH)
**Location**: `src/graph/graph_store.py:1145-1157`  
**Error**: `task_props` used for Email/Timer/Control tasks but not initialized  
**Impact**: Failed to save workflow to Neo4j  
**Fix**: Initialize `task_props` for each task type before use  
**Status**: ✅ FIXED

### 4. ❌ `'GraphStore' object has no attribute 'load_mapping'` (MEDIUM)
**Location**: `src/versioning/version_store.py:129`  
**Error**: Method name changed from `load_mapping` to `load_transformation`  
**Impact**: Failed to load models from graph  
**Fix**: Changed `load_mapping` to `load_transformation`  
**Status**: ✅ FIXED

### 5. ⚠️ Missing Event-Wait/Raise Task Handling (MEDIUM)
**Location**: `src/graph/graph_store.py`  
**Issue**: Event-Wait and Event-Raise tasks not handled as `:EventTask` nodes  
**Impact**: Control tasks not created as separate node types  
**Fix**: Added handling for Event-Wait/Raise tasks to create `:EventTask` nodes  
**Status**: ✅ FIXED

## Validation Results Analysis

### ✅ Working Features
- **Complexity Metrics**: ✅ Calculated and stored correctly (1 transformation with score 29.0)
- **SCD Structure**: ✅ Found in canonical models (1 transformation)
- **Runtime Config**: ✅ Found in parsed files (5 files)

### ⚠️ Warnings (May Be Normal)
- **Field Lineage**: No DERIVED_FROM/FEEDS relationships found
  - **Possible Cause**: Transformations may not have expressions or connectors yet
  - **Action**: Verify after fixes are applied
- **Semantic Tags**: No semantic tags found
  - **Possible Cause**: Transformations may not match tag detection patterns
  - **Action**: Verify tag detection logic

### ❌ Issues Requiring Investigation
- **Field/Port Nodes**: Port nodes exist (22) but:
  - Field nodes: 0 (expected > 0)
  - Port-Field relationships: 0 (expected > 0)
  - Transformation-Port relationships: 0 (expected > 0)
  - **Possible Causes**:
    1. Field nodes not being created (code issue)
    2. Relationships not being created (MERGE issue)
    3. Query in validation script incorrect
  - **Action**: Verify Field node creation after fixes

- **Control Tasks**: Found in parsed files (12) but not in Neo4j (0 nodes)
  - **Possible Causes**:
    1. Control tasks not being saved (fixed with task_props fix)
    2. Event-Wait/Raise not handled (fixed)
  - **Action**: Re-run test after fixes

## Files Modified

1. `src/graph/graph_store.py`
   - Added `import re`
   - Fixed `task_props` initialization for Email/Timer/Control/Other tasks
   - Added Event-Wait/Raise handling

2. `src/versioning/version_store.py`
   - Changed `load_mapping` to `load_transformation`

3. `scripts/test_flow.py`
   - Added `parse_ai_dir` definition before use

## Next Steps

1. **Re-run Test Flow**: `make test-all`
2. **Re-run Validation**: `python scripts/validate_canonical_model_enhancements.py`
3. **Verify Fixes**:
   - Check that `M_STAGE_CUSTOMERS_ENHANCED` saves to Neo4j
   - Check that workflows save to Neo4j
   - Check that control tasks are created as separate node types
   - Check that Field/Port nodes and relationships are created

## Expected Improvements

After fixes:
- ✅ All transformations should save to Neo4j successfully
- ✅ Workflows should save to Neo4j successfully
- ✅ Control tasks should be created as separate node types
- ✅ Field/Port nodes and relationships should be created (if transformations have ports)
- ✅ Field-level lineage relationships should be created (if transformations have expressions)

## Notes

- API upload failures are expected if API server is not running (non-critical)
- Some warnings may be normal if transformations don't have certain features (expressions, tags, etc.)
- Field/Port node creation needs verification after fixes are applied

