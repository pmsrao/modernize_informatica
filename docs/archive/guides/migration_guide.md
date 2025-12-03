# Migration Guide

## Overview

This guide provides step-by-step instructions for migrating Informatica workflows and mappings to Databricks using the Informatica Modernization Accelerator.

---

## Pre-Migration Phase

### 1. Assessment

Before starting migration, assess your Informatica repository:

```bash
# Profile repository
informatica-modernize assess profile

# Analyze components and identify blockers
informatica-modernize assess analyze

# Generate migration wave plan
informatica-modernize assess waves --max-wave-size 10

# Calculate TCO and ROI
informatica-modernize assess tco \
  --informatica-cost 500000 \
  --migration-cost 200000 \
  --runtime-hours 8
```

### 2. Review Assessment Results

- **Repository Profile**: Understand component counts and complexity
- **Blockers**: Identify unsupported features or complex transformations
- **Migration Waves**: Review recommended migration order
- **TCO Analysis**: Understand cost implications and ROI

### 3. Prepare Migration Environment

- Set up Databricks workspace
- Configure Neo4j database
- Set up storage (S3, ADLS, GCS)
- Configure Unity Catalog (if using)

---

## Migration Phase

### Step 1: Upload Informatica Files

```bash
# Upload XML files
informatica-modernize upload \
  --files "path/to/workflows/*.xml" \
  --staging-dir test_log/staging
```

Or via API:
```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@workflow.xml"
```

### Step 2: Parse Files

```bash
# Parse uploaded files
informatica-modernize parse \
  --staging-dir test_log/staging \
  --parsed-dir test_log/parsed
```

This creates canonical models from Informatica XML files.

### Step 3: Enhance with AI (Optional)

```bash
# Enhance canonical models with AI analysis
informatica-modernize enhance \
  --parsed-dir test_log/parsed \
  --output-dir test_log/enhanced
```

### Step 4: Generate Target Code

```bash
# Generate PySpark code
informatica-modernize code \
  --target-language pyspark \
  --output-dir test_log/generated
```

### Step 5: Review Generated Code

- Review generated PySpark code
- Check code quality scores
- Review transformation logic
- Validate against business requirements

### Step 6: Generate Tests

```bash
# Tests are automatically generated with code
# Review test files in test_log/generated/<mapping_name>/test_*.py
```

---

## Post-Migration Phase

### 1. Reconciliation

After deploying to Databricks, reconcile data:

```bash
# Reconcile a mapping
informatica-modernize reconcile mapping \
  --mapping-name M_CustomerLoad \
  --source-connection '{"type": "informatica", "host": "..."}' \
  --target-connection '{"type": "databricks", "workspace": "..."}' \
  --method count \
  --output reconciliation_results.json

# Reconcile a workflow
informatica-modernize reconcile workflow \
  --workflow-name WF_Main \
  --method hash
```

### 2. Validation

Validate generated code:

- Run automated tests
- Validate data quality
- Check performance metrics
- Review reconciliation results

### 3. Performance Tuning

- Optimize PySpark code based on Databricks best practices
- Adjust partitioning strategies
- Optimize joins and aggregations
- Review Delta Lake configurations

---

## Migration Strategies

### Big Bang Migration

Migrate all workflows at once:

**Pros:**
- Single cutover point
- Complete migration in one phase

**Cons:**
- Higher risk
- Requires extensive testing
- Longer downtime

**When to Use:**
- Small to medium-sized repositories
- Well-tested migration process
- Minimal business impact tolerance

### Phased Migration

Migrate in waves based on dependencies:

**Pros:**
- Lower risk
- Incremental validation
- Learn and improve between waves

**Cons:**
- Longer overall timeline
- Need to maintain both systems
- More complex coordination

**When to Use:**
- Large repositories
- Complex dependencies
- Critical business systems

### Parallel Run

Run both systems in parallel:

**Pros:**
- Continuous validation
- Zero downtime
- Gradual cutover

**Cons:**
- Higher operational cost
- Need to maintain both systems
- Data synchronization complexity

**When to Use:**
- Critical production systems
- Zero downtime requirements
- Complex data dependencies

---

## Best Practices

### 1. Start Small

- Begin with simple mappings
- Build confidence and process
- Learn from initial migrations

### 2. Validate Early and Often

- Validate after each phase
- Run reconciliation regularly
- Review code quality continuously

### 3. Document Decisions

- Document transformation decisions
- Track manual changes
- Maintain migration log

### 4. Test Thoroughly

- Unit tests for transformations
- Integration tests for workflows
- End-to-end data validation

### 5. Monitor Performance

- Track execution times
- Monitor resource usage
- Optimize based on metrics

---

## Common Challenges and Solutions

### Challenge: Unsupported Transformations

**Solution:**
- Review blockers identified in assessment
- Implement custom transformations manually
- Use AI agents for suggestions

### Challenge: Complex Expressions

**Solution:**
- Review expression translation
- Test with sample data
- Use expression explainer agent

### Challenge: Performance Issues

**Solution:**
- Review generated code
- Apply Databricks best practices
- Optimize partitioning and caching

### Challenge: Data Quality Issues

**Solution:**
- Run data quality validation
- Review quality rules
- Adjust thresholds as needed

---

## Migration Checklist

### Pre-Migration
- [ ] Repository assessment completed
- [ ] Migration waves planned
- [ ] TCO analysis reviewed
- [ ] Environment prepared
- [ ] Team trained

### Migration
- [ ] Files uploaded and parsed
- [ ] Canonical models validated
- [ ] Code generated and reviewed
- [ ] Tests generated and executed
- [ ] Code quality validated

### Post-Migration
- [ ] Code deployed to Databricks
- [ ] Reconciliation completed
- [ ] Performance validated
- [ ] Documentation updated
- [ ] Team trained on new system

---

## Migration Wave Example

Based on assessment, migration waves might look like:

**Wave 1: Foundation (Low Complexity, No Dependencies)**
- Simple source-to-target mappings
- Basic transformations
- Estimated: 2-3 weeks

**Wave 2: Core Business Logic (Medium Complexity)**
- Business-critical mappings
- Standard transformations
- Estimated: 4-6 weeks

**Wave 3: Complex Logic (High Complexity)**
- Complex transformations
- Custom functions
- Estimated: 6-8 weeks

**Wave 4: Integration (Dependencies)**
- Dependent workflows
- Integration points
- Estimated: 4-6 weeks

---

## Related Documentation

- [Testing and Validation Guide](testing_validation.md) - Testing and validation
- [AI Agents Usage](ai_agents_usage.md) - Using AI agents for migration
- [Code Generators](modules/code_generators.md) - Understanding code generation
- [Assessment Guide](reference/lakebridge_comparison.md) - Assessment capabilities

---

*Last Updated: December 2, 2025*

