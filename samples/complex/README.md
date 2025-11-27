# Complex Test Files

This folder contains **realistic, enterprise-level complex Informatica XML assets** to fully test the modernization platform with advanced scenarios.

## Purpose

Complex test files are used for:
- Enterprise workflow testing
- Multi-source, multi-target mappings
- Complex transformation patterns
- Nested worklet structures
- Advanced features (SCD2, incremental loads, error handling)
- Performance testing
- End-to-end pipeline validation

---

## Files

### workflow_complex.xml
**Enterprise ETL Pipeline** with:
- **9 tasks** (3 load sessions, 2 worklets, 4 processing sessions)
- **Parallel execution** paths (multiple sources load simultaneously)
- **Sequential dependencies** (dimensions → facts → aggregations)
- **Error handling** paths (failed task routing)
- **Nested worklets** (dimension build, fact processing)
- **Data quality validation** step
- **Final reconciliation** step

**Complexity Features**:
- Multiple execution levels (6 levels)
- Parallel and sequential execution
- Error path handling
- Worklet nesting

**Use Case**: Test complex workflow parsing, DAG building with parallel execution, error handling, and nested structures

---

### mapping_complex.xml
**Complex Sales Analytics Mapping** with:
- **3 Source Qualifiers** (customers, orders, products)
- **2 Expression Transformations** (customer enrichment, order calculations)
- **3 Lookup Transformations** (region, product category, supplier)
- **1 Joiner Transformation** (customer-order join)
- **1 Router Transformation** (high/medium/low value routing)
- **2 Aggregator Transformations** (sales by customer, product performance)
- **1 Rank Transformation** (top 100 customers)
- **1 Filter Transformation** (valid records only)
- **1 Update Strategy** (SCD2 handling)
- **3 Target Tables** (fact table, SCD2 dimension, summary table)

**Complexity Features**:
- Multiple sources with different SQL queries
- Complex nested expressions (IIF, SUBSTR, INSTR, TO_CHAR, date calculations)
- Multiple lookups with return fields
- Joiner with join conditions
- Router with multiple groups
- Aggregators with multiple group-by fields
- Rank transformation
- Filter with complex conditions
- SCD2 update strategy
- Multiple target tables

**Use Case**: Test complex mapping parsing, expression engine, code generation for advanced patterns, SCD2 detection

---

### worklet_complex.xml
**Complex Dimension Build Worklet** with:
- **8 tasks** (5 dimension sessions, 1 nested worklet, 1 hierarchy session, 1 validation session)
- **Parallel execution** (5 base dimensions load simultaneously)
- **Nested worklet** (time dimensions)
- **Sequential dependencies** (base dimensions → hierarchy → validation)

**Complexity Features**:
- Multiple parallel tasks
- Nested worklet structure
- Sequential validation step
- Complex dependency graph

**Use Case**: Test nested worklet parsing, parallel execution handling, complex dependency resolution

---

### session_complex.xml
**Complex Session Configuration** with:
- **3 Sources** (customers, orders, products) with different configurations
- **3 Targets** (fact table, SCD2 dimension, summary table)
- **Performance settings** (partitioning, buffer sizes, commit intervals)
- **Error handling** (stop on errors, reject files)
- **SCD2 configuration** (effective dates, current flag)
- **Pre/Post SQL** (data cleanup, updates)
- **Variables** (batch date, environment, commit size)

**Complexity Features**:
- Multiple sources with different fetch sizes and partitions
- Multiple targets with different load types
- SCD2 configuration
- Pre/post session SQL
- Variable usage
- Performance tuning parameters

**Use Case**: Test session parser, SCD2 detection, configuration extraction, variable handling

---

### dag_complex.json
**Complex DAG Structure** representing:
- **9 nodes** (3 load sessions, 2 worklets, 4 processing sessions)
- **11 edges** (9 success paths, 2 error paths)
- **6 execution levels** (parallel and sequential)
- **Metadata** (nested task counts, mapping references)

**Use Case**: Test DAG builder, visualization, execution level calculation, cycle detection

---

## Complexity Highlights

### Workflow Complexity
- ✅ Multiple parallel execution paths
- ✅ Nested worklets (2 levels)
- ✅ Error handling paths
- ✅ 6 execution levels
- ✅ 9 total tasks

### Mapping Complexity
- ✅ 3 sources with complex SQL
- ✅ 10+ transformations
- ✅ Complex nested expressions
- ✅ Multiple lookups
- ✅ Router with multiple groups
- ✅ SCD2 patterns
- ✅ 3 target tables

### Worklet Complexity
- ✅ 8 nested tasks
- ✅ Parallel execution
- ✅ Nested worklet
- ✅ Sequential validation

### Session Complexity
- ✅ Multiple sources/targets
- ✅ SCD2 configuration
- ✅ Performance tuning
- ✅ Pre/post SQL
- ✅ Variables

---

## Testing Scenarios

These files provide **full coverage** for:

1. **Parser Testing**
   - Complex XML structures
   - Nested elements
   - Multiple attributes
   - Advanced patterns

2. **DAG Building**
   - Parallel execution
   - Complex dependencies
   - Error paths
   - Execution levels

3. **Code Generation**
   - Multi-source joins
   - Complex expressions
   - SCD2 patterns
   - Multiple targets

4. **Expression Engine**
   - Nested functions
   - Date calculations
   - String manipulations
   - Conditional logic

5. **AI Agents**
   - Complex mapping summarization
   - Risk detection in complex logic
   - Expression explanation
   - Optimization suggestions

6. **Lineage**
   - Multi-level lineage
   - Complex transformations
   - Cross-mapping dependencies

---

## Comparison: Simple vs Complex

| Feature | Simple | Complex |
|---------|--------|---------|
| Workflow Tasks | 3 | 9 |
| Mapping Sources | 1 | 3 |
| Mapping Transformations | 3 | 10+ |
| Worklet Tasks | 2 | 8 |
| Execution Levels | 3 | 6 |
| Error Handling | No | Yes |
| SCD2 | No | Yes |
| Nested Worklets | 1 level | 2 levels |
| Parallel Execution | No | Yes |

---

**Start with `samples/simple/` for learning, then use `samples/complex/` for enterprise testing!**
