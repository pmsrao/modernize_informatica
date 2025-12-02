# Code Generation Issues & Fixes

## Issues Identified from Test Run

### Issue 1: Workflow-Aware Generation Not Triggering

**Problem**: Code generation fell back to file-based generation instead of workflow-aware generation.

**Root Cause**: 
- Settings check failed: `'Settings' object has no attribute 'ENABLE_GRAPH_STORE'`
- The settings object uses lowercase `enable_graph_store` but code was checking `ENABLE_GRAPH_STORE`

**Fix Applied**:
- Updated `scripts/test_flow.py` to use `getattr(settings, 'enable_graph_store', False)` and also check environment variables directly
- Added fallback to check `os.getenv('ENABLE_GRAPH_STORE', 'false').lower() == 'true'`

**Status**: ✅ Fixed

---

### Issue 2: Generated Code Structure Not Workflow-Based

**Problem**: Generated code is in flat structure (`generated/{mapping_name}/`) instead of workflow-based structure (`workflows/{workflow}/sessions/{session}/mappings/{mapping}/`).

**Root Cause**:
- Workflow-aware generation didn't trigger (Issue 1)
- Even if it did, workflows may not be in Neo4j (workflows are only saved to JSON, not Neo4j)

**Fix Needed**:
1. ✅ Fixed settings check (Issue 1)
2. ⚠️ Need to ensure workflows are saved to Neo4j during parsing
3. ⚠️ Need to add `save_workflow()` method to GraphStore

**Status**: Partially fixed - settings check fixed, but workflows need to be saved to Neo4j

---

### Issue 3: Generated_AI Folder Has Flat Structure

**Problem**: Review process saves all files flat in `generated_ai/` without preserving directory structure.

**Root Cause**: Review code doesn't preserve relative directory structure from source.

**Fix Applied**:
- Updated `review_code()` method to preserve directory structure
- Creates subdirectories in output to match source structure

**Status**: ✅ Fixed

---

### Issue 4: File Naming Issue - SQL File Contains Python Code

**Problem**: `stage_orders_sql.sql` file contains PySpark DataFrame code (Python), but filename still ends with `.sql`.

**Root Cause**: 
- AI review changed SQL code to DataFrame operations (Python)
- Review process didn't detect code type change and rename file

**Fix Applied**:
- Added `_detect_code_type()` method to detect actual code type from content
- Review process now:
  1. Detects code type before and after fix
  2. Renames file if code type changes (e.g., `.sql` → `.py`)
  3. Uses descriptive naming: `{mapping_name}_pyspark.py` or `{mapping_name}_dlt.py`

**Status**: ✅ Fixed

---

## Additional Fixes Needed

### Fix 5: Save Workflows to Neo4j

**Problem**: Workflows are parsed but not saved to Neo4j, so workflow-aware generation can't find them.

**Solution**: Add workflow/session/worklet saving to GraphStore and update parsing to save them.

**Implementation**:
1. Add `save_workflow()`, `save_session()`, `save_worklet()` methods to GraphStore
2. Update parsing endpoints to save workflows/sessions/worklets to Neo4j
3. Update hierarchy builder to save workflow structure to Neo4j

---

## Summary of Changes

### ✅ Fixed

1. **Settings Check**: Fixed `ENABLE_GRAPH_STORE` attribute access
2. **Directory Structure Preservation**: Review process now preserves directory structure
3. **File Renaming**: Review process detects code type changes and renames files appropriately
4. **Code Type Detection**: Added method to detect Python/SQL/DLT from code content

### ⚠️ Pending

1. **Workflow Storage in Neo4j**: Need to save workflows/sessions/worklets to Neo4j during parsing
2. **Workflow-Aware Generation**: Once workflows are in Neo4j, workflow-aware generation will work

---

## Testing Recommendations

1. **Re-run test**: `make test-all` after fixes
2. **Verify workflow structure**: Check if `generated_code/workflows/` structure is created
3. **Verify file naming**: Check if SQL files converted to Python are renamed correctly
4. **Verify directory structure**: Check if `generated_ai/` preserves subdirectories

---

## Next Steps

1. Implement workflow/session/worklet saving to Neo4j
2. Test workflow-aware generation end-to-end
3. Verify all file naming scenarios (SQL → Python, Python → SQL, etc.)

