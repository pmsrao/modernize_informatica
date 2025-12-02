# Step-by-Step Testing Guide

This guide explains how to use the Makefile and `test_flow.py` script to test the Informatica Modernization flow step by step.

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

## Prerequisites

1. **API Server Running** (optional, but recommended):
   ```bash
   ./start_api.sh
   ```

2. **Neo4j Running** (for graph operations):
   ```bash
   ./scripts/setup_neo4j.sh
   ```

3. **Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Directory Structure

The test flow creates the following directory structure:

```
test_log/
├── staging/          # Uploaded source files
├── parsed/           # Parsed canonical models (JSON)
├── parse_ai/         # AI-enhanced canonical models
├── generated/        # Generated code (PySpark/DLT/SQL)
└── generated_ai/     # AI-reviewed and fixed code
```

## Usage

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
- Copies files to `test_log/staging/`
- Optionally uploads to API (if API is running)
- Creates `upload_results.json` with file IDs

**Output:**
- Files in `test_log/staging/`
- `test_log/staging/upload_results.json`

---

### Step B: Parse Mappings

Parse all mapping files in the staging directory:

```bash
make parse
```

**What it does:**
- Finds all `*mapping*.xml` files in staging
- Parses each mapping to canonical model
- Saves JSON files to `test_log/parsed/`

**Output:**
- `test_log/parsed/{mapping_name}.json` for each mapping
- `test_log/parsed/parse_summary.json`

---

### Step C: Enhance with AI

Enhance parsed canonical models with AI:

```bash
make enhance
```

**What it does:**
- Loads parsed models from `test_log/parsed/`
- Enhances each model using AI agents
- Saves enhanced models to `test_log/parse_ai/`

**Output:**
- `test_log/parse_ai/{mapping_name}_enhanced.json` for each mapping
- `test_log/parse_ai/enhance_summary.json`

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
- `test_log/hierarchy.json`
- `test_log/hierarchy_tree.txt`

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
- `test_log/{workflow_name}_lineage.mermaid`
- `test_log/{workflow_name}_lineage.dot`
- `test_log/{workflow_name}_lineage.json`

---

### Step F: Generate Canonical Model Images

Generate visualizations of canonical models:

```bash
make canonical
```

**What it does:**
- Finds canonical models (parsed or enhanced)
- Generates Mermaid diagrams showing structure

**Output:**
- `test_log/{mapping_name}_canonical.mermaid` for each model

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
- `test_log/generated/{mapping_name}/pyspark_code.py`
- `test_log/generated/{mapping_name}/dlt_pipeline.py`
- `test_log/generated/{mapping_name}/sql_queries.sql`
- `test_log/generated/generation_summary.json`

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
- `test_log/generated_ai/{filename}_review.json` for each file
- `test_log/generated_ai/{filename}` (fixed code)
- `test_log/generated_ai/review_summary.json`

**Note:** Requires LLM configuration.

---

## Running All Steps

Run all steps in sequence:

```bash
make test-all
```

This will:
1. Clean the test_log directory
2. Upload files
3. Parse mappings
4. Enhance with AI
5. Generate hierarchy
6. Generate lineage
7. Generate canonical visualizations
8. Generate code
9. Review and fix code

---

## Advanced Usage

### Using Python Script Directly

You can also use the Python script directly for more control:

```bash
# Upload files
python scripts/test_flow.py upload --files "samples/complex/*.xml" --staging-dir test_log/staging

# Parse mappings
python scripts/test_flow.py parse --staging-dir test_log/staging --output-dir test_log/parsed

# Enhance with AI
python scripts/test_flow.py enhance --parsed-dir test_log/parsed --output-dir test_log/parse_ai

# Generate hierarchy
python scripts/test_flow.py hierarchy --output-dir test_log

# Generate lineage
python scripts/test_flow.py lineage --output-dir test_log --staging-dir test_log/staging

# Generate canonical images
python scripts/test_flow.py canonical --output-dir test_log

# Generate code
python scripts/test_flow.py code --output-dir test_log/generated

# Review code
python scripts/test_flow.py review --generated-dir test_log/generated --output-dir test_log/generated_ai
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

## Cleaning Up

Remove all test results:

```bash
make clean
```

This deletes the entire `test_log/` directory.

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

### LLM Errors

If AI enhancement or code review fails:
- Check LLM configuration in `.env`
- Verify API keys are set
- Review logs for specific error messages

### File Not Found

If files aren't found:
- Check file paths are correct
- Use absolute paths if relative paths don't work
- Verify files exist: `ls -la samples/complex/`

---

## Example Workflow

Complete example workflow:

```bash
# 1. Start services
./scripts/setup_neo4j.sh
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
```

---

## Output Files Summary

After running all steps, you'll have:

```
test_log/
├── staging/
│   ├── *.xml                    # Source files
│   └── upload_results.json      # Upload summary
├── parsed/
│   ├── {mapping_name}.json      # Parsed models
│   └── parse_summary.json       # Parse summary
├── parse_ai/
│   ├── {mapping_name}_enhanced.json  # Enhanced models
│   └── enhance_summary.json     # Enhancement summary
├── hierarchy.json               # Hierarchy structure
├── hierarchy_tree.txt           # Text tree view
├── {workflow}_lineage.mermaid    # Lineage diagrams
├── {workflow}_lineage.dot
├── {workflow}_lineage.json
├── {mapping}_canonical.mermaid  # Canonical visualizations
├── generated/
│   ├── {mapping_name}/
│   │   ├── pyspark_code.py
│   │   ├── dlt_pipeline.py
│   │   └── sql_queries.sql
│   └── generation_summary.json
└── generated_ai/
    ├── {filename}_review.json   # Review results
    ├── {filename}                # Fixed code
    └── review_summary.json       # Review summary
```

---

## Next Steps

After testing:
1. Review generated code in `test_log/generated/`
2. Check AI enhancements in `test_log/parse_ai/`
3. View lineage diagrams in Mermaid Live Editor
4. Use fixed code from `test_log/generated_ai/`

For more information, see:
- `test_end_to_end.md` - End-to-end testing guide
- `docs/testing_guide.md` - Detailed testing documentation

