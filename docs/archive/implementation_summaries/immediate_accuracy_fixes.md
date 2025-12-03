# Immediate Accuracy Fixes

## Quick Wins (Can Start Today)

### 1. Fix Field-Level Lineage Detection 🔧

**Issue**: No DERIVED_FROM/FEEDS relationships found

**Root Cause**: The field reference matching logic may be too strict or fields aren't being created correctly.

**Immediate Actions**:

1. **Add Debug Logging** (30 min):
   ```python
   # In graph_store.py, add logging before DERIVED_FROM creation:
   logger.debug(f"Creating DERIVED_FROM for port: {port_name}, expression: {port_expression}")
   logger.debug(f"Extracted field refs: {field_refs}")
   logger.debug(f"Looking for input field: {ref} in transformation: {trans_name}")
   ```

2. **Check Field Node Creation** (1 hour):
   - Verify Field nodes are created for all ports
   - Check if Field nodes have correct properties
   - Verify Port-Field relationships exist

3. **Improve Field Reference Matching** (2 hours):
   - Current regex may miss some patterns
   - Add support for port references (`:EXP.field_name`)
   - Better handling of qualified names

**Files to Modify**:
- `src/graph/graph_store.py` (lines 323-345)
- Add logging and improve matching logic

---

### 2. Fix Semantic Tag Detection 🔧

**Issue**: No semantic tags detected

**Root Cause**: Detection thresholds may be too high, or transformations don't match patterns.

**Immediate Actions**:

1. **Lower Detection Thresholds** (30 min):
   - Current: lookup_count >= 3, join_count >= 2, etc.
   - Try: lookup_count >= 1, join_count >= 1
   - Test with actual transformations

2. **Add Debug Logging** (30 min):
   ```python
   logger.debug(f"Transformation: {transformation_name}")
   logger.debug(f"Lookup count: {lookup_count}, Join count: {join_count}")
   logger.debug(f"SCD type: {scd_type}")
   logger.debug(f"Detected tags: {tags}")
   ```

3. **Fix SCD Tag Detection** (1 hour):
   - SCD structure is found, but tags aren't detected
   - Check if `scd_type` is being passed correctly
   - Verify tag is added when SCD type is not NONE

**Files to Modify**:
- `src/normalizer/semantic_tag_detector.py`
- `src/normalizer/mapping_normalizer.py` (verify tags are stored)

---

### 3. Improve Expression Parsing Accuracy 🔧

**Current Limitations**:
- Simple regex-based field extraction
- May miss complex expressions
- Port references not fully handled

**Immediate Actions**:

1. **Enhance Field Reference Extraction** (2 hours):
   - Improve regex patterns
   - Handle port references (`:EXP.field`, `:LKP.field`)
   - Handle qualified names (`transformation.field`)

2. **Add Expression Validation** (1 hour):
   - Validate expression syntax
   - Check for undefined references
   - Report parsing issues

**Files to Modify**:
- `src/graph/graph_store.py` (field reference extraction)
- `src/parser/mapping_parser.py` (expression parsing)

---

### 4. Generate Better Code for Custom Components 🔧

**Issue**: Custom transformations and stored procedures require manual intervention

**Immediate Actions**:

1. **Generate Function Stubs** (2 hours):
   - Generate Python function stubs for custom transformations
   - Generate SQL function stubs for stored procedures
   - Include metadata (parameters, return types) in comments

2. **Add Migration Guidance** (1 hour):
   - Add comments explaining what needs to be implemented
   - Provide examples
   - Link to documentation

**Files to Modify**:
- `src/generators/pyspark_generator.py`
- `src/generators/sql_generator.py`

---

## Code Generation Optimizations (High Impact)

### 5. Optimize PySpark Code Generation 🚀

**Current Areas**:
- Joins could use broadcast hints
- Aggregations could be optimized
- Unnecessary transformations could be reduced

**Immediate Actions**:

1. **Add Broadcast Join Hints** (2 hours):
   - Detect small lookup tables
   - Add broadcast hints for joins
   - Improve join performance

2. **Optimize Aggregations** (2 hours):
   - Use window functions where appropriate
   - Reduce unnecessary repartitioning
   - Optimize group by operations

3. **Add Performance Comments** (1 hour):
   - Add comments for optimization opportunities
   - Suggest partitioning strategies
   - Recommend caching

**Files to Modify**:
- `src/generators/pyspark_generator.py`

---

### 6. Improve Code Quality Checks ✅

**Current State**: Basic validation exists

**Immediate Actions**:

1. **Expand Validation** (3 hours):
   - Validate all transformations are represented
   - Check for missing connectors
   - Verify expression correctness

2. **Add Functional Tests** (4 hours):
   - Test generated code with sample data
   - Compare output with expected results
   - Validate data types

**Files to Modify**:
- `scripts/validate_generated_code.py`
- Create new test files

---

## Testing & Validation Improvements

### 7. Add Comprehensive Test Suite 🧪

**Current State**: Limited test coverage

**Immediate Actions**:

1. **Add Unit Tests** (1 week):
   - Test parsers with various XML structures
   - Test normalizers with different transformation types
   - Test generators with various canonical models

2. **Add Integration Tests** (1 week):
   - Test end-to-end flow
   - Test with real Informatica XML files
   - Test error scenarios

**Files to Create**:
- `tests/unit/test_parsers.py`
- `tests/unit/test_normalizers.py`
- `tests/unit/test_generators.py`
- `tests/integration/test_end_to_end.py`

---

## Performance Optimizations

### 8. Optimize Neo4j Operations ⚡

**Current Areas**:
- Some queries may be slow
- Writes could be batched

**Immediate Actions**:

1. **Review and Add Indexes** (1 hour):
   - Check query patterns
   - Add missing indexes
   - Optimize existing indexes

2. **Batch Neo4j Writes** (3 hours):
   - Batch node creation
   - Batch relationship creation
   - Reduce transaction overhead

**Files to Modify**:
- `src/graph/graph_store.py`
- `scripts/schema/create_neo4j_schema.py`

---

## Recommended Order

### Week 1: Critical Accuracy Fixes
1. Fix field-level lineage (add logging, improve matching)
2. Fix semantic tag detection (lower thresholds, add logging)
3. Improve expression parsing

### Week 2: Code Generation Optimization
1. Optimize PySpark code generation
2. Generate better code for custom components
3. Improve code validation

### Week 3: Testing & Quality
1. Add comprehensive test suite
2. Improve error handling
3. Optimize Neo4j operations

---

## Success Criteria

- **Field-level lineage**: 80%+ of transformations with expressions have DERIVED_FROM relationships
- **Semantic tags**: Tags detected for transformations matching patterns
- **Code quality**: Generated code quality score > 85/100
- **Performance**: Generated code performs within 15% of hand-written code
- **Test coverage**: 70%+ code coverage

