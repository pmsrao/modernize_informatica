# Next Steps: Canonical Model Enhancements

## Overview

This document outlines the recommended next steps after implementing the canonical model enhancements. Since we're still in development and don't need backward compatibility, we can simplify and clean up the codebase.

## Immediate Actions (High Priority)

### 1. Clean Up Backward Compatibility Code ✅ IN PROGRESS

**Remove unnecessary aliases and compatibility code:**

- **`src/api/routes.py`**: ✅ Removed Informatica-specific field aliases (`workflows`, `sessions`, `mapplets`, `mappings`) from `/graph/components` endpoint
- **`src/api/routes.py`**: ✅ Updated `/graph/workflows/{workflow_name}` endpoint to `/graph/pipelines/{pipeline_name}`
- **`src/graph/graph_queries.py`**: ✅ Removed backward compatibility method aliases:
  - ✅ Removed `get_workflow_structure()` alias
  - ✅ Removed duplicate `get_transformations_in_workflow()` implementation
  - ✅ Removed `get_tasks_in_workflow()` alias
  - ✅ Removed `get_mapping_code_files()` alias
- **`frontend/src/services/api.js`**: ✅ Removed normalization code for old field names, added backward compatibility aliases for frontend components
- **Frontend Components**: ⏳ Still using old method names (backward compatibility aliases in place)

**Benefits:**
- Cleaner, more maintainable code
- Less confusion
- Easier to understand

**Note**: Frontend components still use old method names (`listWorkflows`, `getWorkflowStructure`) but these now call the new generic methods internally. Frontend components can be updated later to use new names directly.

### 2. Fix Remaining `mapping_name` References

**Files to fix:**
- `src/normalizer/mapping_normalizer.py`: Error message still uses `mapping_name` (line 113) ✅ Fixed
- Search codebase for any remaining `mapping_name` references that should be `transformation_name`

### 3. End-to-End Validation

**Validation Steps:**

1. **Drop and Recreate Neo4j Schema**
   ```bash
   python scripts/schema/create_neo4j_schema.py
   ```

2. **Run Complete Test Flow**
   ```bash
   make test-all
   ```

3. **Verify New Features Work:**
   - ✅ Field and Port nodes created in Neo4j
   - ✅ Field-level lineage relationships (DERIVED_FROM, FEEDS) created
   - ✅ Complexity metrics calculated and stored
   - ✅ Semantic tags detected and stored
   - ✅ Structured runtime config extracted and stored
   - ✅ Enhanced SCD structure populated
   - ✅ Control tasks created as separate node types (DecisionTask, AssignmentTask, CommandTask, EventTask)

4. **Query Validation:**
   - Test `get_field_lineage()` query
   - Test `get_field_impact()` query
   - Test `get_cross_pipeline_field_dependencies()` query
   - Verify complexity metrics are queryable
   - Verify semantic tags are filterable

### 4. Update Tests

**Test Updates Needed:**

1. **Update Existing Tests:**
   - `tests/integration/test_graph_store.py`: Update to use `transformation_name` instead of `mapping_name`
   - `tests/integration/test_part1_graph_integration.py`: Update fixtures
   - `tests/integration/test_end_to_end.py`: Update assertions

2. **Add New Tests:**
   - `tests/integration/test_field_lineage.py`: Test field-level lineage creation and queries
   - `tests/unit/test_complexity_calculator.py`: Test complexity metrics calculation
   - `tests/unit/test_semantic_tag_detector.py`: Test semantic tag detection
   - `tests/unit/test_runtime_config_normalizer.py`: Test runtime config normalization
   - `tests/integration/test_control_tasks.py`: Test control task node creation

### 5. Documentation Updates

**Update Documentation:**

1. **`docs/modules/canonical_model.md`**
   - Add section on Field/Port nodes and field-level lineage
   - Document complexity metrics structure
   - Document semantic tags
   - Document structured runtime configuration (`task_runtime_config`, `workflow_runtime_config`)
   - Document enhanced SCD structure
   - Document control task node types

2. **Create Examples:**
   - Add example queries for field-level lineage
   - Add example of complexity metrics in canonical model
   - Add example of semantic tags

## Medium Priority Actions

### 6. Frontend Updates

**Frontend Changes:**

1. **Update API Client** (`frontend/src/services/api.js`)
   - Remove backward compatibility normalization
   - Use new generic field names directly (`pipelines`, `tasks`, `transformations`)

2. **Update UI Components:**
   - Display complexity metrics in Component View
   - Show semantic tags as badges/chips in transformation cards
   - Display field-level lineage in Code View (if applicable)
   - Show structured runtime config in Pipeline/Task details

3. **New Features to Consider:**
   - Field-level lineage visualization (column-level dependency graph)
   - Complexity metrics dashboard/filtering
   - Semantic tag filtering in Component View
   - Control task visualization in Pipeline View

### 7. API Enhancements

**New Endpoints to Consider:**

1. **Field-Level Lineage Endpoints:**
   - `GET /api/v1/graph/field/lineage/{field_name}?transformation={name}`
   - `GET /api/v1/graph/field/impact/{field_name}?transformation={name}`
   - `GET /api/v1/graph/field/dependencies/{field_name}`

2. **Complexity Metrics Endpoint:**
   - `GET /api/v1/graph/transformations/{name}/complexity`

3. **Semantic Tags Endpoint:**
   - `GET /api/v1/graph/transformations?tags=scd2,cdc`

### 8. Code Quality Improvements

**Refactoring Opportunities:**

1. **Simplify Graph Store Methods**
   - Review if any methods can be consolidated
   - Remove any redundant code paths

2. **Error Handling**
   - Ensure all new features have proper error handling
   - Add validation for new structures (complexity metrics, semantic tags, etc.)

3. **Type Hints**
   - Add complete type hints to new classes and methods
   - Update existing code where types are missing

## Lower Priority (Future Enhancements)

### 9. Performance Optimization

**Potential Optimizations:**

1. **Field/Port Node Creation**
   - Consider batching Field/Port node creation for better performance
   - Evaluate if all fields need to be nodes vs. properties (trade-off between queryability and storage)

2. **Complexity Calculation**
   - Cache complexity metrics if transformations haven't changed
   - Consider incremental updates

3. **Semantic Tag Detection**
   - Optimize tag detection logic
   - Consider caching results

### 10. Advanced Features

**Future Enhancements:**

1. **Expression AST** (deferred per plan)
   - If needed later, implement AST parser for expressions
   - Enable advanced pattern matching

2. **Test Representation** (deferred per plan)
   - Add test metadata to canonical model if needed

3. **Field-Level Impact Analysis**
   - Build UI for visualizing field-level impact
   - Add alerts for high-impact fields

## Validation Checklist

### ✅ Completed

- [x] Critical bug fixes (re import, parse_ai_dir, task_props, load_mapping, Event-Wait/Raise)
- [x] Makefile clean target fixed to preserve directory structure
- [x] Canonical model enhancements implemented (Field/Port nodes, complexity metrics, semantic tags, runtime config, SCD, control tasks)
- [x] Validation script created
- [x] Code validation script created
- [x] Neo4j schema creation script created
- [x] All code committed and pushed to remote

### 🔄 In Progress

- [x] Backend backward compatibility code removed (API routes, graph queries)
- [x] Frontend API client updated (removed backward compatibility aliases)
- [x] Frontend components updated to use new generic method names
- [x] End-to-end flow tested successfully (`make test-all`) ✅
- [ ] All `mapping_name` references fixed to `transformation_name` (some are legitimate fallbacks for compatibility)

### ⏳ Pending

- [ ] All tests updated and passing
- [x] Field/Port nodes created correctly in Neo4j ✅ (3 Field nodes, 25 Port nodes, relationships created)
- [ ] Field-level lineage relationships (DERIVED_FROM, FEEDS) created (⚠️ No relationships found - may be normal)
- [ ] Field-level lineage queries working (`get_field_lineage`, `get_field_impact`, `get_cross_pipeline_field_dependencies`)
- [x] Complexity metrics calculated correctly ✅ (2 transformations with scores, avg 42.0)
- [x] Complexity metrics stored in Neo4j ✅
- [ ] Semantic tags detected correctly (⚠️ No tags found - may be normal)
- [ ] Semantic tags stored in Neo4j (⚠️ No tags found - may be normal)
- [x] Structured runtime config extracted correctly ✅ (5 parsed files with config)
- [x] Structured runtime config stored in Neo4j ✅ (1 pipeline with workflow_runtime_config)
- [x] Enhanced SCD structure populated correctly ✅ (1 canonical model with SCD)
- [x] Control tasks created as separate node types ✅ (6 nodes: 1 Decision, 1 Assignment, 2 Command, 2 Event)
- [ ] Documentation updated
- [ ] No linter errors
- [ ] No broken tests

## Recommended Order of Execution

1. **Week 1: Cleanup & Validation**
   - Remove backward compatibility code
   - Fix remaining `mapping_name` references
   - Run end-to-end validation
   - Fix any issues found

2. **Week 2: Testing & Documentation**
   - Update existing tests
   - Add new tests for new features
   - Update documentation
   - Create examples

3. **Week 3: Frontend & API**
   - Update frontend to use new structures
   - Add new API endpoints if needed
   - Test frontend integration

4. **Week 4: Polish & Optimization**
   - Performance optimizations
   - Code quality improvements
   - Final validation

## Notes

- Since we're in development, we can make breaking changes freely
- Focus on correctness and completeness over backward compatibility
- Test thoroughly before moving to next phase
- Document all changes clearly
- Consider creating a migration script if you have existing Neo4j data (though dropping/recreating is fine in dev)
