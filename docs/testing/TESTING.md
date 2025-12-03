# Testing Guide

Complete guide for testing the Informatica Modernization Accelerator, including step-by-step instructions, test organization, and troubleshooting.

---

## Overview

The testing infrastructure provides a command-line interface to test each stage of the modernization process:

1. **Upload** - Copy source files to staging directory
2. **Parse** - Parse Informatica XML files into canonical models
3. **Enhance** - Enhance parsed models with AI
4. **Hierarchy** - Generate hierarchy/tree structure
5. **Lineage** - Generate lineage diagrams
6. **Canonical** - Generate canonical model visualizations
7. **Code** - Generate target code (PySpark/DLT/SQL)
8. **Review** - Review and fix generated code with AI

---

## Quick Start

### Run Complete Test Flow

Run all steps in sequence:

```bash
make test-all
```

This will:
1. Clean the workspace directory
2. Upload files
3. Parse mappings
4. Enhance with AI
5. Generate hierarchy
6. Generate lineage
7. Generate canonical visualizations
8. Generate code
9. Review and fix code

### Run Individual Steps

```bash
# Upload files
make upload FILES='samples/complex/*.xml'

# Parse mappings
make parse

# Generate code
make code
```

### Run Unit/Integration Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v
```

---

## Prerequisites

1. **API Server Running** (optional, but recommended):
   ```bash
   ./start_api.sh
   ```

2. **Neo4j Running** (for graph operations):
   ```bash
   ./scripts/setup/setup_neo4j.sh
   ```

3. **Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**:
   - Create `.env` file with required settings
   - Configure LLM provider (for AI features)
   - Set Neo4j connection details (if using graph store)

---

## Directory Structure

The test flow creates the following directory structure:

```
workspace/
├── staging/          # Uploaded source files
├── parsed/           # Parsed canonical models (JSON)
├── parse_ai/         # AI-enhanced canonical models
├── generated/        # Generated code (PySpark/DLT/SQL)
├── generated_ai/     # AI-reviewed and fixed code
├── diagrams/         # Visualizations (hierarchy, lineage, canonical)
└── diffs/            # Diff reports (parse vs enhance, code vs review)
```

---

## Step-by-Step Guide

### Step A: Upload Files

Upload Informatica XML files (mappings, workflows, sessions, worklets) to the staging directory:

```bash
make upload FILES='samples/complex/*.xml'
```

Or specify individual files:

```bash
make upload FILES='samples/complex/mapping_complex.xml samples/complex/workflow_complex.xml'
```

**What it does:**
- Copies files to `workspace/staging/`
- Optionally uploads to API (if API is running)
- Creates `upload_results.json` with file IDs

**Output:**
- Files in `workspace/staging/`
- `workspace/staging/upload_results.json`

---

### Step B: Parse Mappings

Parse all mapping files in the staging directory:

```bash
make parse
```

**What it does:**
- Finds all `*mapping*.xml` files in staging
- Parses each mapping to canonical model
- Saves JSON files to `workspace/parsed/`

**Output:**
- `workspace/parsed/{mapping_name}.json` for each mapping
- `workspace/parsed/parse_summary.json`

---

### Step C: Enhance with AI

Enhance parsed canonical models with AI:

```bash
make enhance
```

**What it does:**
- Loads parsed models from `workspace/parsed/`
- Enhances each model using AI agents
- Saves enhanced models to `workspace/parse_ai/`

**Output:**
- `workspace/parse_ai/{mapping_name}_enhanced.json` for each mapping
- `workspace/parse_ai/enhance_summary.json`

**Note:** Requires LLM configuration (OpenAI, Azure, or Local LLM).

---

### Step D: Generate Hierarchy

Generate the Informatica object hierarchy (Workflow → Worklet → Session → Mapping):

```bash
make hierarchy
```

**What it does:**
- Fetches hierarchy from API (if available)
- Generates JSON and text tree representations

**Output:**
- `workspace/diagrams/hierarchy.json`
- `workspace/diagrams/hierarchy_tree.txt`

**Note:** Requires API to be running and files to be uploaded via API.

---

### Step E: Generate Lineage Diagrams

Generate lineage diagrams for workflows:

```bash
make lineage
```

**What it does:**
- Finds workflow files in staging
- Parses workflows and builds DAGs
- Generates Mermaid, DOT, and JSON formats

**Output:**
- `workspace/diagrams/{workflow_name}_lineage.mermaid`
- `workspace/diagrams/{workflow_name}_lineage.dot`
- `workspace/diagrams/{workflow_name}_lineage.json`

---

### Step F: Generate Canonical Model Visualizations

Generate visualizations of canonical models:

```bash
make canonical
```

**What it does:**
- Finds canonical models (parsed or enhanced)
- Generates Mermaid diagrams showing structure

**Output:**
- `workspace/diagrams/{mapping_name}_canonical.mermaid` for each model

---

### Step G: Generate Code

Generate target code (PySpark, DLT, SQL) from canonical models:

```bash
make code
```

**What it does:**
- Loads canonical models (prefers enhanced, falls back to parsed)
- Generates PySpark, DLT, and SQL code
- Saves code to mapping-specific directories

**Output:**
- `workspace/generated/{mapping_name}/pyspark_code.py`
- `workspace/generated/{mapping_name}/dlt_pipeline.py`
- `workspace/generated/{mapping_name}/sql_queries.sql`
- `workspace/generated/generation_summary.json`

---

### Step H: Review & Fix Code with AI

Review and fix generated code using AI:

```bash
make review
```

**What it does:**
- Finds all generated code files
- Reviews each file for issues
- Fixes code if issues are found
- Saves review results and fixed code

**Output:**
- `workspace/generated_ai/{filename}_review.json` for each file
- `workspace/generated_ai/{filename}` (fixed code)
- `workspace/generated_ai/review_summary.json`

**Note:** Requires LLM configuration.

---

## Test Organization

### Sample Files

- **`samples/simple/`** - Basic test files for initial validation
- **`samples/complex/`** - Complex workflows with multiple sessions, worklets, and transformations
- **`samples/super_complex/`** - Advanced workflows with complex transformations
- **`samples/super_complex_enhanced/`** - Enhanced test cases

### Test Scripts

- **`scripts/test_flow.py`** - Main test workflow script (Makefile uses this)
- **`scripts/dev/test_frontend_integration.py`** - Frontend API integration tests
- **`tests/e2e/test_samples.py`** - End-to-end sample tests

### Test Suites

- **`tests/unit/`** - Unit tests for individual components
- **`tests/integration/`** - Integration tests for component interactions
- **`tests/e2e/`** - End-to-end tests

### Generated Tests

- **`build/generated_code/<mapping_name>/generated_tests.py`** - Auto-generated pytest test suites

---

## Test Types

1. **Parser Tests** - Validate XML parsing for workflows, mappings, sessions, worklets, mapplets
2. **DAG Tests** - Validate DAG building and visualization
3. **Code Generation Tests** - Validate PySpark, DLT, SQL code generation
4. **Test Generation Tests** - Validate auto-generated test suites
5. **Frontend Tests** - Validate UI and lineage visualization
6. **Integration Tests** - End-to-end pipeline testing
7. **Field-Level Lineage Tests** - Validate field-level data lineage tracking
8. **Semantic Tag Detection Tests** - Validate pattern detection (SCD, lookup-heavy, etc.)

---

## Advanced Usage

### Using Python Script Directly

You can also use the Python script directly for more control:

```bash
# Upload files
python scripts/test_flow.py upload --files "samples/complex/*.xml" --staging-dir workspace/staging

# Parse mappings
python scripts/test_flow.py parse --staging-dir workspace/staging --output-dir workspace/parsed

# Enhance with AI
python scripts/test_flow.py enhance --parsed-dir workspace/parsed --output-dir workspace/parse_ai

# Generate hierarchy
python scripts/test_flow.py hierarchy --output-dir workspace

# Generate lineage
python scripts/test_flow.py lineage --output-dir workspace --staging-dir workspace/staging

# Generate canonical images
python scripts/test_flow.py canonical --output-dir workspace

# Generate code
python scripts/test_flow.py code --output-dir workspace/generated

# Review code
python scripts/test_flow.py review --generated-dir workspace/generated --output-dir workspace/generated_ai
```

### Custom API URL

If your API is running on a different URL:

```bash
make upload FILES='samples/complex/*.xml' API_URL=http://localhost:9000
```

Or in the Makefile, set:

```makefile
API_URL = http://localhost:9000
```

### Without API

To use direct Python calls instead of API:

```bash
python scripts/test_flow.py upload --files "samples/complex/*.xml" --no-api
```

---

## Example Workflow

Complete example workflow:

```bash
# 1. Start services
./scripts/setup/setup_neo4j.sh
./start_api.sh

# 2. Upload files
make upload FILES='samples/complex/*.xml'

# 3. Parse mappings
make parse

# 4. Enhance with AI (optional, requires LLM)
make enhance

# 5. Generate hierarchy
make hierarchy

# 6. Generate lineage
make lineage

# 7. Generate canonical visualizations
make canonical

# 8. Generate code
make code

# 9. Review code (optional, requires LLM)
make review

# 10. Generate diff reports
make diff
```

---

## Output Files Summary

After running all steps, you'll have:

```
workspace/
├── staging/
│   ├── *.xml                    # Source files
│   └── upload_results.json      # Upload summary
├── parsed/
│   ├── {mapping_name}.json      # Parsed models
│   └── parse_summary.json       # Parse summary
├── parse_ai/
│   ├── {mapping_name}_enhanced.json  # Enhanced models
│   └── enhance_summary.json     # Enhancement summary
├── diagrams/
│   ├── hierarchy.json           # Hierarchy structure
│   ├── hierarchy_tree.txt       # Text tree view
│   ├── {workflow}_lineage.mermaid    # Lineage diagrams
│   ├── {workflow}_lineage.dot
│   ├── {workflow}_lineage.json
│   └── {mapping}_canonical.mermaid  # Canonical visualizations
├── generated/
│   ├── {mapping_name}/
│   │   ├── pyspark_code.py
│   │   ├── dlt_pipeline.py
│   │   └── sql_queries.sql
│   └── generation_summary.json
├── generated_ai/
│   ├── {filename}_review.json   # Review results
│   ├── {filename}                # Fixed code
│   └── review_summary.json       # Review summary
└── diffs/
    ├── index.html                # Diff report index
    └── *.html                    # Individual diff reports
```

---

## Cleaning Up

### Clean Workspace Contents

Remove all test results but keep directory structure:

```bash
make clean
```

### Remove Workspace Completely

Remove the entire workspace directory:

```bash
make clean-all
```

---

## Troubleshooting

### API Connection Errors

If you see API connection errors:
- Ensure API is running: `./start_api.sh`
- Check API URL: Default is `http://localhost:8000`
- Verify API is accessible: `curl http://localhost:8000/api/v1/health`

### Missing Dependencies

If you see import errors:
- Install dependencies: `pip install -r requirements.txt`
- Check Python path: Script should handle this automatically
- Verify virtual environment is activated (if using one)

### LLM Errors

If AI enhancement or code review fails:
- Check LLM configuration in `.env`
- Verify API keys are set (for OpenAI/Azure)
- Check local LLM is running (for local provider)
- Review logs for specific error messages

### File Not Found

If files aren't found:
- Check file paths are correct
- Use absolute paths if relative paths don't work
- Verify files exist: `ls -la samples/complex/`

### Neo4j Connection Issues

If graph operations fail:
- Ensure Neo4j is running: `./scripts/setup/setup_neo4j.sh`
- Check connection details in `.env`
- Verify Neo4j is accessible: `cypher-shell -u neo4j -p password`

### Test Failures

If tests fail:
- Check test output for specific errors
- Verify test data files exist
- Review test logs in `tests/output/`
- Check coverage reports in `tests/coverage/`

---

## Additional Resources

### Related Documentation

- 📖 [Comprehensive Testing Guide](guide.md) - Detailed testing with validation checklists
- 📊 [Test Results](results.md) - Detailed test results and validation
- 🔧 [Troubleshooting Guide](troubleshooting.md) - Common issues and solutions
- 🎨 [Frontend Testing](frontend.md) - Frontend lineage visualization testing
- 🔄 [End-to-End Testing](test_end_to_end.md) - Complete end-to-end test workflows

### Getting Help

- **Issues?** Check [Troubleshooting Guide](troubleshooting.md)
- **Frontend?** See [Frontend Testing](frontend.md)
- **Details?** Read [Comprehensive Guide](guide.md)
- **Results?** Review [Test Results](results.md)

---

**Last Updated**: December 3, 2025
