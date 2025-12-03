# Next Steps Summary - Accuracy & Optimization Focus

## Overview

Since we're parking multi-platform support and focusing on ensuring the Informatica solution is **proper, accurate, and optimized**, here are the recommended next steps.

---

## Immediate Priority: Accuracy Fixes

### 1. Fix Field-Level Lineage ⚠️ **HIGH PRIORITY**

**Status**: No DERIVED_FROM/FEEDS relationships found  
**Impact**: Column-level lineage not working  
**Effort**: 2-3 hours

**Actions**:
- ✅ Added debug logging to understand why relationships aren't created
- ⏳ Improve field reference extraction (handle port references, qualified names)
- ⏳ Verify Field nodes are created correctly
- ⏳ Test with transformations that have expressions

**Files Modified**:
- `src/graph/graph_store.py` - Added debug logging

---

### 2. Fix Semantic Tag Detection ⚠️ **MEDIUM PRIORITY**

**Status**: No semantic tags detected  
**Impact**: Missing metadata for transformations  
**Effort**: 1 hour

**Actions**:
- ✅ Lowered detection thresholds (lookup >= 1, join >= 1, etc.)
- ✅ Fixed tag detector to receive full canonical model
- ⏳ Test with actual transformations
- ⏳ Add debug logging if still not working

**Files Modified**:
- `src/normalizer/semantic_tag_detector.py` - Lowered thresholds
- `src/normalizer/mapping_normalizer.py` - Fixed model passed to detector

---

### 3. Improve Expression Parsing Accuracy 🔧 **HIGH PRIORITY**

**Status**: Basic regex-based extraction  
**Impact**: May miss complex expressions  
**Effort**: 3-4 hours

**Actions**:
- ⏳ Enhance field reference extraction
- ⏳ Handle port references (`:EXP.field`, `:LKP.field`)
- ⏳ Handle qualified names (`transformation.field`)
- ⏳ Add expression validation

**Files to Modify**:
- `src/graph/graph_store.py` - Improve field reference extraction
- `src/parser/mapping_parser.py` - Enhance expression parsing

---

### 4. Generate Better Code for Custom Components 🔧 **MEDIUM PRIORITY**

**Status**: Manual intervention warnings  
**Impact**: Custom transformations need manual work  
**Effort**: 3-4 hours

**Actions**:
- ⏳ Generate function stubs for custom transformations
- ⏳ Generate function stubs for stored procedures
- ⏳ Add migration guidance in comments

**Files to Modify**:
- `src/generators/pyspark_generator.py`
- `src/generators/sql_generator.py`

---

## Code Generation Optimization

### 5. Optimize PySpark Code Generation 🚀 **HIGH PRIORITY**

**Status**: Basic code generation  
**Impact**: Generated code may not be optimal  
**Effort**: 1 week

**Actions**:
- ⏳ Add broadcast join hints for small lookup tables
- ⏳ Optimize aggregation operations
- ⏳ Reduce unnecessary repartitioning
- ⏳ Add performance comments

**Files to Modify**:
- `src/generators/pyspark_generator.py`

---

### 6. Optimize DLT Code Generation 🚀 **MEDIUM PRIORITY**

**Status**: Basic DLT code generation  
**Impact**: May not leverage DLT features effectively  
**Effort**: 1 week

**Actions**:
- ⏳ Use DLT expectations for data quality
- ⏳ Optimize streaming pipelines
- ⏳ Better SCD handling with DLT merge

**Files to Modify**:
- `src/generators/dlt_generator.py`

---

### 7. Optimize SQL Code Generation 🚀 **MEDIUM PRIORITY**

**Status**: Basic SQL generation  
**Impact**: Generated SQL may not be optimal  
**Effort**: 1 week

**Actions**:
- ⏳ Use CTEs for complex queries
- ⏳ Optimize join order
- ⏳ Use window functions where appropriate

**Files to Modify**:
- `src/generators/sql_generator.py`

---

## Quality & Validation

### 8. Enhance Code Validation ✅ **HIGH PRIORITY**

**Status**: Basic validation exists  
**Impact**: Issues may not be caught early  
**Effort**: 1 week

**Actions**:
- ⏳ Validate all transformations are represented
- ⏳ Check for missing connectors
- ⏳ Verify expression correctness
- ⏳ Add functional tests with sample data

**Files to Modify**:
- `scripts/validate_generated_code.py`
- Create new test files

---

### 9. Improve Error Handling 🔧 **MEDIUM PRIORITY**

**Status**: Basic error handling  
**Impact**: Errors may not be clear  
**Effort**: 1 week

**Actions**:
- ⏳ Better error messages with context
- ⏳ Error categorization
- ⏳ Error recovery

**Files to Modify**:
- All parser files
- All generator files

---

## Performance Optimization

### 10. Optimize Parsing Performance ⚡ **MEDIUM PRIORITY**

**Status**: Sequential parsing  
**Impact**: Slow for large file sets  
**Effort**: 1 week

**Actions**:
- ⏳ Parallel file parsing
- ⏳ Batch Neo4j writes
- ⏳ Cache parsed results

**Files to Modify**:
- `scripts/test_flow.py`
- `src/graph/graph_store.py`

---

### 11. Optimize Neo4j Queries ⚡ **MEDIUM PRIORITY**

**Status**: Some queries may be slow  
**Impact**: UI may be slow  
**Effort**: 3-4 hours

**Actions**:
- ⏳ Review slow queries
- ⏳ Add missing indexes
- ⏳ Optimize query patterns

**Files to Modify**:
- `src/graph/graph_queries.py`
- `scripts/schema/create_neo4j_schema.py`

---

## Testing & Documentation

### 12. Add Comprehensive Test Suite 🧪 **HIGH PRIORITY**

**Status**: Limited test coverage  
**Impact**: Issues may not be caught  
**Effort**: 2 weeks

**Actions**:
- ⏳ Unit tests for parsers
- ⏳ Unit tests for normalizers
- ⏳ Unit tests for generators
- ⏳ Integration tests

**Files to Create**:
- `tests/unit/test_parsers.py`
- `tests/unit/test_normalizers.py`
- `tests/unit/test_generators.py`
- `tests/integration/test_end_to_end.py`

---

## Recommended Implementation Order

### Week 1: Critical Accuracy Fixes
1. ✅ Fix semantic tag detection (lowered thresholds, fixed model passing)
2. ⏳ Fix field-level lineage (added logging, need to test and improve)
3. ⏳ Improve expression parsing

### Week 2: Code Generation Optimization
1. ⏳ Optimize PySpark code generation
2. ⏳ Generate better code for custom components
3. ⏳ Enhance code validation

### Week 3-4: Quality & Performance
1. ⏳ Add comprehensive test suite
2. ⏳ Improve error handling
3. ⏳ Optimize parsing and Neo4j operations

---

## Success Metrics

### Accuracy Metrics
- **Field-level lineage**: 80%+ of transformations with expressions have DERIVED_FROM relationships
- **Semantic tags**: Tags detected for all transformations matching patterns
- **Expression parsing**: 95%+ accuracy for complex expressions
- **Reference resolution**: 100% of references resolved

### Code Quality Metrics
- **Generated code quality**: Average score > 85/100
- **Performance**: Generated code performs within 15% of hand-written code
- **Best practices**: Generated code follows platform best practices

### Performance Metrics
- **Parsing speed**: < 5 seconds per file for typical mappings
- **Code generation**: < 2 seconds per transformation
- **Neo4j queries**: < 100ms for typical queries

---

## Quick Wins (Can Do Today)

1. ✅ **Fixed semantic tag detection** - Lowered thresholds and fixed model passing
2. ✅ **Added debug logging for field-level lineage** - Will help diagnose issues
3. ⏳ **Review and add Neo4j indexes** - Quick performance win
4. ⏳ **Improve error messages** - Makes debugging easier

---

## Documentation Created

1. **`docs/development/accuracy_optimization_roadmap.md`** - Comprehensive roadmap
2. **`docs/development/immediate_accuracy_fixes.md`** - Quick wins and immediate fixes
3. **`docs/development/next_steps_summary.md`** - This document

---

## Next Actions

1. **Test the semantic tag fix** - Re-run test and validation to see if tags are detected
2. **Investigate field-level lineage** - Use debug logs to understand why relationships aren't created
3. **Start PySpark optimization** - High impact, improves generated code quality

