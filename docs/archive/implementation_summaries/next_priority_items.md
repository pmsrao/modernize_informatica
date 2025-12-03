# Next Priority Items - Action Plan

Based on the review of `next_steps_summary.md`, here are the prioritized next items to work on:

---

## 🔴 HIGH PRIORITY Items

### 1. Enhance Code Validation ⚠️ **HIGH PRIORITY**

**Current Status**: Basic validation exists (`scripts/validate_generated_code.py`)
- ✅ Validates code files exist
- ✅ Validates syntax (Python/SQL)
- ✅ Validates code structure (imports, functions)
- ✅ Validates code quality metrics

**Missing Capabilities**:
- ⏳ Validate all transformations are represented in canonical model
- ⏳ Check for missing connectors (data flow gaps)
- ⏳ Verify expression correctness (syntax, function mapping)
- ⏳ Add functional tests with sample data
- ⏳ Validate canonical model completeness

**Files to Enhance**:
- `scripts/validate_generated_code.py` - Add transformation completeness checks
- `src/validation/test_data_validator.py` - Enhance functional testing
- Create `scripts/validate_canonical_model.py` - New validation script

**Effort**: 1 week
**Impact**: High - Catch issues early before code generation

**Recommended Actions**:
1. Add canonical model validation:
   - Check all transformations have sources/targets
   - Verify all connectors are valid (from/to transformations exist)
   - Validate expression syntax
   - Check for circular dependencies
2. Enhance functional testing:
   - Test transformations with sample data
   - Verify output matches expected results
   - Test edge cases (nulls, empty data, etc.)
3. Add connector validation:
   - Ensure all transformations are connected
   - Check for orphaned transformations
   - Verify data flow completeness

---

### 2. Add Comprehensive Test Suite 🧪 **HIGH PRIORITY**

**Current Status**: Limited test coverage
- ✅ Some unit tests exist (`tests/unit/`)
- ✅ Some integration tests exist (`tests/integration/`)
- ⚠️ Coverage gaps in parsers, normalizers, generators

**Missing Test Coverage**:
- ⏳ Comprehensive unit tests for parsers (all parser types)
- ⏳ Unit tests for normalizers (mapping_normalizer, lineage_engine, scd_detector)
- ⏳ Unit tests for generators (pyspark, dlt, sql, spec)
- ⏳ Integration tests for end-to-end flows
- ⏳ Test fixtures for various transformation types

**Files to Create/Enhance**:
- `tests/unit/test_parsers.py` - Comprehensive parser tests
- `tests/unit/test_normalizers.py` - Normalizer tests
- `tests/unit/test_generators.py` - Generator tests (if not comprehensive)
- `tests/integration/test_end_to_end.py` - End-to-end integration tests
- `tests/fixtures/` - Add more test fixtures

**Effort**: 2 weeks
**Impact**: High - Prevents regressions, ensures quality

**Recommended Actions**:
1. **Parser Tests**:
   - Test all parser types (mapping, workflow, session, worklet, mapplet)
   - Test edge cases (missing fields, invalid XML, etc.)
   - Test reference resolution
2. **Normalizer Tests**:
   - Test canonical model creation
   - Test lineage building
   - Test SCD detection
   - Test complexity calculation
3. **Generator Tests**:
   - Test code generation for all transformation types
   - Test expression translation
   - Test code quality
4. **Integration Tests**:
   - Test full flow: parse → normalize → generate
   - Test with real Informatica XML files
   - Test graph store integration

---

## 🟡 MEDIUM PRIORITY (Quick Wins)

### 3. Optimize Neo4j Queries ⚡ **MEDIUM PRIORITY** (Quick Win: 3-4 hours)

**Current Status**: Some queries may be slow
- ✅ Indexes exist for common properties (name, source_component_type)
- ⏳ May need additional indexes for relationships
- ⏳ Query patterns may need optimization

**Actions**:
- ⏳ Review slow queries in `src/graph/graph_queries.py`
- ⏳ Add composite indexes for common query patterns
- ⏳ Optimize relationship queries
- ⏳ Add query performance logging

**Files to Modify**:
- `src/graph/graph_queries.py` - Optimize query patterns
- `scripts/schema/create_neo4j_schema.py` - Add missing indexes

**Effort**: 3-4 hours
**Impact**: Medium - Improves UI responsiveness

**Recommended Actions**:
1. Profile slow queries:
   - Add timing logs to graph queries
   - Identify queries taking > 100ms
   - Review query execution plans
2. Add missing indexes:
   - Composite indexes for common patterns
   - Relationship property indexes
   - Full-text indexes if needed
3. Optimize query patterns:
   - Use shortest path queries where appropriate
   - Batch queries where possible
   - Cache frequently accessed data

---

### 4. Improve Error Handling 🔧 **MEDIUM PRIORITY**

**Current Status**: Basic error handling exists
- ✅ Custom exceptions defined (`src/utils/exceptions.py`)
- ⏳ Error messages may lack context
- ⏳ Error recovery could be improved

**Actions**:
- ⏳ Better error messages with context (file, line, transformation)
- ⏳ Error categorization (parsing, generation, validation)
- ⏳ Error recovery strategies (retry, skip, use defaults)
- ⏳ Error reporting and aggregation

**Files to Modify**:
- All parser files (`src/parser/*.py`)
- All generator files (`src/generators/*.py`)
- `src/utils/exceptions.py` - Enhance exception classes

**Effort**: 1 week
**Impact**: Medium - Better developer experience

---

## 📋 Recommended Implementation Order

### Week 1: Code Validation Enhancement
1. **Day 1-2**: Add canonical model validation
   - Validate transformation completeness
   - Check connectors
   - Verify expressions
2. **Day 3-4**: Enhance functional testing
   - Add sample data tests
   - Test edge cases
3. **Day 5**: Quick win - Optimize Neo4j queries (3-4 hours)

### Week 2-3: Comprehensive Test Suite
1. **Week 2**: Parser and Normalizer tests
   - Unit tests for all parsers
   - Unit tests for normalizers
2. **Week 3**: Generator and Integration tests
   - Unit tests for generators
   - End-to-end integration tests

### Week 4: Error Handling (if time permits)
1. Enhance error messages
2. Add error categorization
3. Implement error recovery

---

## 🎯 Success Criteria

### Code Validation
- ✅ 100% of transformations validated
- ✅ All connectors verified
- ✅ Expression syntax validated
- ✅ Functional tests pass with sample data

### Test Coverage
- ✅ 80%+ code coverage
- ✅ All parser types tested
- ✅ All normalizer components tested
- ✅ All generator types tested
- ✅ End-to-end flows tested

### Performance
- ✅ Neo4j queries < 100ms for typical queries
- ✅ Query performance logged and monitored

---

## 🚀 Quick Wins (Can Start Today)

1. **Optimize Neo4j Queries** (3-4 hours)
   - Review `src/graph/graph_queries.py` for slow queries
   - Add missing indexes
   - Test query performance

2. **Add Missing Validation Checks** (2-3 hours)
   - Add connector validation to `validate_generated_code.py`
   - Add transformation completeness check
   - Test with existing transformations

3. **Add Parser Unit Tests** (1-2 days)
   - Start with mapping parser tests
   - Use existing fixtures
   - Expand to other parsers

---

## 📝 Notes

- **Testing Priority**: Focus on parsers and normalizers first (foundation)
- **Validation Priority**: Focus on canonical model completeness (catches issues early)
- **Performance**: Neo4j optimization is quick win (3-4 hours)
- **Error Handling**: Can be done incrementally alongside other work

---

*Last Updated: 2025-12-03*
*Based on: `docs/development/next_steps_summary.md`*

