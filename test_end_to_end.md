# End-to-End Testing Guide

## Overview

This guide provides comprehensive test steps to validate the complete flow from Informatica XML files to generated code, including AI enhancement, graph storage, code generation, and code review.

---

## Prerequisites

### 1. Environment Setup

```bash
# 1. Set up Neo4j
./scripts/setup_neo4j.sh

# 2. Configure environment
cp .env.example .env
# Edit .env with Neo4j credentials:
# NEO4J_URI=bolt://localhost:7687
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=password
# ENABLE_GRAPH_STORE=true
# GRAPH_FIRST=true

# 3. Verify Neo4j connection
python scripts/test_graph_store.py
```

### 2. Start API Server

```bash
./start_api.sh
```

The API should be accessible at `http://localhost:8000`

### 3. Optional: Configure LLM (for AI enhancements)

```bash
# Add to .env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
```

---

## Part 1: Source to Canonical Form (with AI Enhancement)

### Step 1: Upload Informatica Mapping XML

```bash
# Upload a mapping file
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@samples/complex/mapping_complex.xml"
```

**Expected Response**:
```json
{
  "file_id": "abc123...",
  "filename": "mapping_complex.xml",
  "file_type": "mapping",
  "uploaded_at": "2024-01-01T12:00:00",
  "message": "File uploaded successfully"
}
```

**Save the `file_id` for next steps.**

---

### Step 2: Parse Mapping with AI Enhancement

```bash
# Parse with AI enhancement enabled (default)
curl -X POST "http://localhost:8000/api/v1/parse/mapping" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "abc123...",
    "enhance_model": true
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "data": {
    "mapping_name": "M_LOAD_CUSTOMER",
    "sources": [...],
    "targets": [...],
    "transformations": [...],
    "_enhancements_applied": [...],
    "_provenance": {...}
  },
  "message": "Mapping parsed successfully"
}
```

**What Happens**:
1. XML is parsed into raw data
2. Raw data is normalized to canonical model
3. AI Enhancement Agent enhances the model:
   - Pattern-based enhancements (fast)
   - LLM-based enhancements (if enabled)
4. Model Validation Agent validates the enhanced model
5. Enhanced model is saved to Graph Store (Neo4j)

**Verify in API Logs**:
```
INFO: Mapping parsed successfully: M_LOAD_CUSTOMER (enhancement: True)
DEBUG: Model explicitly saved to graph: M_LOAD_CUSTOMER
```

---

### Step 3: Visualize Canonical Model in Neo4j Browser

#### 3.1 Access Neo4j Browser

1. Open browser: http://localhost:7474
2. Login with credentials:
   - Username: `neo4j`
   - Password: (from `.env`)

#### 3.2 View All Mappings

```cypher
MATCH (m:Mapping)
RETURN m.name, m.mapping_name, m.complexity
ORDER BY m.name
```

#### 3.3 View Mapping Structure

```cypher
// View complete mapping structure
MATCH (m:Mapping {name: "M_LOAD_CUSTOMER"})
OPTIONAL MATCH (m)-[:HAS_SOURCE]->(s:Source)
OPTIONAL MATCH (m)-[:HAS_TARGET]->(t:Target)
OPTIONAL MATCH (m)-[:HAS_TRANSFORMATION]->(trans:Transformation)
RETURN m, s, t, trans
```

#### 3.4 View Transformations

```cypher
// View all transformations in a mapping
MATCH (m:Mapping {name: "M_LOAD_CUSTOMER"})-[:HAS_TRANSFORMATION]->(t:Transformation)
RETURN t.name, t.type, t.properties
ORDER BY t.name
```

#### 3.5 View Data Lineage

```cypher
// View data flow
MATCH path = (s:Source)-[:FLOWS_TO*]->(t:Target)
WHERE s.mapping = "M_LOAD_CUSTOMER"
RETURN path
LIMIT 10
```

#### 3.6 View Tables Used

```cypher
// View all tables used by mapping
MATCH (m:Mapping {name: "M_LOAD_CUSTOMER"})-[:HAS_SOURCE|:HAS_TARGET]->(st)-[:READS_TABLE|:WRITES_TABLE]->(tab:Table)
RETURN DISTINCT tab.name, tab.database
```

#### 3.7 View Enhancement Metadata

```cypher
// View AI enhancements applied
MATCH (m:Mapping {name: "M_LOAD_CUSTOMER"})
RETURN m._enhancements_applied, m._provenance
```

---

### Step 4: Verify Graph Storage

#### 4.1 Check Mapping Exists in Graph

```bash
# Use API endpoint
curl "http://localhost:8000/api/v1/graph/mappings/M_LOAD_CUSTOMER"
```

#### 4.2 Check Graph Statistics

```bash
curl "http://localhost:8000/api/v1/graph/statistics"
```

**Expected Response**:
```json
{
  "success": true,
  "statistics": {
    "total_mappings": 1,
    "total_transformations": 5,
    "total_tables": 3,
    ...
  }
}
```

---

## Part 2: Canonical Form to Target Stack (Code Generation & Review)

### Step 5: Generate PySpark Code

```bash
# Generate code with auto-review enabled (default)
curl -X POST "http://localhost:8000/api/v1/generate/pyspark" \
  -H "Content-Type: application/json" \
  -d '{
    "mapping_id": "M_LOAD_CUSTOMER",
    "review_code": true
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "code": "from pyspark.sql import functions as F\n...",
  "language": "pyspark",
  "message": "PySpark code generated successfully",
  "review": {
    "issues": [...],
    "suggestions": [...],
    "needs_fix": false,
    "severity": "LOW",
    "score": 85,
    "review_summary": "Code review completed. Quality score: 85/100."
  }
}
```

**What Happens**:
1. Canonical model is loaded from Graph Store (Neo4j)
2. Expressions are translated to PySpark syntax
3. Code is generated from canonical model
4. Code Review Agent reviews the generated code:
   - Pattern-based review (fast)
   - LLM-based review (if enabled)
5. If high-severity issues found, Code Fix Agent fixes them automatically
6. Final code is returned with review results

**Verify in API Logs**:
```
INFO: Loading from graph (graph_first=True)...
INFO: Model loaded from graph: M_LOAD_CUSTOMER
INFO: Code review completed: LOW severity, score: 85/100
```

---

### Step 6: Review Generated Code (Standalone)

If you want to review code separately:

```bash
curl -X POST "http://localhost:8000/api/v1/review/code" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "from pyspark.sql import functions as F\n...",
    "canonical_model": {...}
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "review": {
    "issues": [
      {
        "category": "Performance",
        "severity": "MEDIUM",
        "issue": "Using collect() without null check",
        "location": "code",
        "recommendation": "Check for empty results before accessing"
      }
    ],
    "suggestions": [...],
    "needs_fix": true,
    "severity": "MEDIUM",
    "score": 75,
    "review_summary": "..."
  }
}
```

---

### Step 7: Fix Code Issues (if needed)

If review found issues, the code is automatically fixed. To manually fix:

```bash
curl -X POST "http://localhost:8000/api/v1/analyze/fix" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "...",
    "error_message": "...",
    "canonical_model": {...}
  }'
```

---

## Additional Testing Scenarios

### Scenario 1: Test AI Analysis Endpoints

#### Get Mapping Summary

```bash
curl -X POST "http://localhost:8000/api/v1/analyze/summary" \
  -H "Content-Type: application/json" \
  -d '{
    "mapping_id": "M_LOAD_CUSTOMER"
  }'
```

#### Get Risk Analysis

```bash
curl -X POST "http://localhost:8000/api/v1/analyze/risks" \
  -H "Content-Type: application/json" \
  -d '{
    "mapping_id": "M_LOAD_CUSTOMER"
  }'
```

#### Get Transformation Suggestions

```bash
curl -X POST "http://localhost:8000/api/v1/analyze/suggestions" \
  -H "Content-Type: application/json" \
  -d '{
    "mapping_id": "M_LOAD_CUSTOMER"
  }'
```

---

### Scenario 2: Test Graph Queries

#### Find Mappings Using a Table

```bash
curl "http://localhost:8000/api/v1/graph/mappings/using-table/CUSTOMER_SRC"
```

#### Get Dependencies

```bash
curl "http://localhost:8000/api/v1/graph/mappings/M_LOAD_CUSTOMER/dependencies"
```

#### Get Impact Analysis

```bash
curl "http://localhost:8000/api/v1/graph/mappings/M_LOAD_CUSTOMER/impact"
```

#### Get Migration Readiness

```bash
curl "http://localhost:8000/api/v1/graph/migration/readiness"
```

---

### Scenario 3: Test End-to-End Script

Run the automated test script:

```bash
python scripts/test_part1_part2_flow.py
```

**Expected Output**:
```
✅ Part 1 flow test passed!
✅ Part 2 flow test passed!
✅ All flow tests passed!
```

---

## Validation Checklist

### Part 1 Validation

- [ ] Mapping XML uploaded successfully
- [ ] Parse endpoint returns canonical model
- [ ] Enhanced model includes `_enhancements_applied` field
- [ ] Enhanced model includes `_provenance` field
- [ ] Model visible in Neo4j Browser
- [ ] Graph statistics show mapping exists
- [ ] Graph queries return expected results

### Part 2 Validation

- [ ] Code generation loads from graph
- [ ] Generated code is valid Python/PySpark
- [ ] Code review returns results
- [ ] Review includes issues, suggestions, and score
- [ ] High-severity issues are auto-fixed
- [ ] Final code quality score is acceptable (>70)

### Graph Validation

- [ ] Mapping nodes exist in Neo4j
- [ ] Transformations linked to mapping
- [ ] Sources and targets linked correctly
- [ ] Tables linked to sources/targets
- [ ] Lineage relationships exist
- [ ] Enhancement metadata stored

---

## Troubleshooting

### Issue: Neo4j Connection Fails

**Solution**:
```bash
# Check if Neo4j is running
docker ps | grep neo4j

# Check Neo4j logs
docker logs neo4j-modernize

# Test connection manually
docker exec neo4j-modernize cypher-shell -u neo4j -p password "RETURN 1"
```

### Issue: Model Not Saved to Graph

**Solution**:
1. Check `.env` has `ENABLE_GRAPH_STORE=true`
2. Check `.env` has `GRAPH_FIRST=true`
3. Restart API server
4. Check API logs for errors

### Issue: Code Review Returns Empty Results

**Solution**:
1. Check if code is valid Python
2. Check LLM configuration (if using LLM review)
3. Review pattern-based checks (should always work)

### Issue: LLM Enhancements Not Working

**Solution**:
1. Check LLM API keys in `.env`
2. Check `LLM_PROVIDER` setting
3. Verify API key is valid
4. Check API logs for LLM errors

---

## Success Criteria

✅ **Part 1 Complete** when:
- Mapping parsed and enhanced successfully
- Enhanced model saved to graph
- Model visible in Neo4j Browser
- Graph queries work

✅ **Part 2 Complete** when:
- Code generated from graph
- Code review completed
- Code quality score acceptable
- No critical issues in generated code

✅ **End-to-End Complete** when:
- All steps execute successfully
- Graph contains complete mapping structure
- Generated code is production-ready
- All validations pass

---

## Next Steps

After completing end-to-end testing:

1. **Test with Multiple Mappings**: Upload and process multiple mappings
2. **Test Graph Queries**: Explore cross-mapping queries
3. **Test AI Analysis**: Try all AI analysis endpoints
4. **Performance Testing**: Test with large mappings
5. **Integration Testing**: Test with real Informatica exports

---

**For detailed API documentation, see**: `src/api/routes.py`  
**For architecture details, see**: `solution.md`  
**For implementation status, see**: `roadmap.md`

