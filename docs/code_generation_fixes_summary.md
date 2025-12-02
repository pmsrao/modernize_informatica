# Code Generation Fixes Summary

## Issues Fixed

### Issue 1: Diff Report Not Showing Code Comparisons ✅

**Problem**: The diff report showed "0 Code Comparisons" and "0 Code Files with Changes" even though code was reviewed.

**Root Cause**: 
- The diff generation code was looking for reviewed files using `os.path.basename()` which lost the directory structure
- Since we now preserve directory structure in `generated_ai/`, files are in subdirectories (e.g., `generated_ai/stage_orders/stage_orders_pyspark.py`)
- But the diff code was looking for them in the root (e.g., `generated_ai/stage_orders_pyspark.py`)

**Fix Applied**:
- Updated `scripts/generate_diff.py` to preserve directory structure when looking for reviewed files
- Added fallback to check both structured and flat paths for backward compatibility
- Now correctly finds reviewed files in subdirectories

**Files Changed**:
- `scripts/generate_diff.py`: Updated `_diff_code_files_html()` method

---

### Issue 2: Workflow/Worklet/Session Code Generation ✅

**Problem**: Code was being generated for workflows, worklets, and sessions even though they don't have canonical models, resulting in empty/minimal code files.

**Root Cause**:
- Code generation was processing all JSON files in `test_log/parsed/` and `test_log/parse_ai/`
- Workflow/worklet/session JSON files (e.g., `WF_CUSTOMER_ORDERS_ETL_workflow.json`) were being treated as canonical models
- These files don't have `mapping_name` or transformation logic, so they generated empty code

**Fix Applied**:
- Added check to skip files with `_workflow.json`, `_session.json`, or `_worklet.json` suffixes
- Added validation to ensure canonical model has `mapping_name` before generating code
- Only mappings (with canonical models) will generate code now

**Files Changed**:
- `scripts/test_flow.py`: Updated `_generate_code_file_based()` method

---

### Issue 3: PySpark vs DLT Code Generation ✅

**Problem**: User wants regular PySpark transformation code, not DLT pipeline code.

**Root Cause**:
- Code generation was generating all three types: PySpark, DLT, and SQL
- User specifically wants regular PySpark DataFrame transformation code (not DLT-specific)

**Fix Applied**:
- Disabled DLT and SQL generation by default
- Only PySpark generator is active now
- Generates regular PySpark DataFrame operations (not DLT pipeline code)
- Can be re-enabled via configuration if needed

**Files Changed**:
- `scripts/test_flow.py`: 
  - Updated `generate_code()` to only use PySpark generator
  - Updated `_generate_code_file_based()` to only generate PySpark
  - Updated `_generate_code_workflow_aware()` to only generate PySpark
  - Updated `_generate_code_workflow_aware_from_files()` to only generate PySpark

---

## Summary of Changes

### Files Modified

1. **scripts/generate_diff.py**
   - Fixed directory structure preservation in diff file matching
   - Now correctly finds reviewed files in subdirectories

2. **scripts/test_flow.py**
   - Added skip logic for workflow/worklet/session files
   - Added validation for canonical models (must have `mapping_name`)
   - Changed to only generate PySpark code (disabled DLT and SQL)

### What Gets Generated Now

**Before**:
- ❌ Generated code for workflows/worklets/sessions (empty files)
- ❌ Generated PySpark, DLT, and SQL for each mapping
- ❌ Diff report couldn't find reviewed files

**After**:
- ✅ Only generates code for mappings (with canonical models)
- ✅ Only generates PySpark transformation code (regular DataFrame operations)
- ✅ Diff report correctly finds and compares reviewed files
- ✅ Skips workflow/worklet/session files (no code generation needed)

---

## Testing

After these fixes, when you run `make test-all`:

1. **Code Generation**: 
   - Only mappings will generate code
   - Only PySpark files will be generated (`.py` files)
   - Workflow/worklet/session files will be skipped

2. **Diff Report**:
   - Should show code comparisons in Section B
   - Should correctly compare generated vs reviewed code files
   - Should show changes made during AI review

3. **Generated Files**:
   - Structure: `generated/{mapping_name}/{mapping_name}_pyspark.py`
   - Reviewed: `generated_ai/{mapping_name}/{mapping_name}_pyspark.py`
   - Diff reports: `test_log/diffs/{mapping_name}_pyspark_code_diff.html`

---

## Re-enabling DLT/SQL Generation (If Needed)

If you want to re-enable DLT or SQL generation in the future, modify `scripts/test_flow.py`:

```python
# In generate_code() method, change:
generators = {
    "pyspark": PySparkGenerator(),
    # "dlt": DLTGenerator(),  # Uncomment to enable
    # "sql": SQLGenerator()   # Uncomment to enable
}
```

And update the code generation loops to iterate over all generators instead of just PySpark.

---

## Next Steps

1. Re-run `make test-all` to verify fixes
2. Check diff report to confirm code comparisons are showing
3. Verify only mapping files generate code (workflows/worklets/sessions are skipped)
4. Verify only PySpark files are generated (no DLT or SQL)

