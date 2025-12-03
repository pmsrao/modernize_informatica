# Comprehensive Testing Guide

## Overview

This guide provides step-by-step instructions for testing the Informatica Modernization Accelerator **with** and **without** the frontend, including validation steps.

---

## Table of Contents

1. [Testing Without Frontend](#testing-without-frontend)
2. [Testing With Frontend](#testing-with-frontend)
3. [Viewing DAG Visualizations](#viewing-dag-visualizations)
4. [Validation Checklist](#validation-checklist)
5. [Troubleshooting](#troubleshooting)

---

## Testing Without Frontend

### Prerequisites

- Python 3.10+
- Dependencies installed: `pip install -r requirements.txt`
- Sample files in `samples/simple/` and `samples/complex/` directories

### Step 1: Run Test Script

```bash
python scripts/test_samples.py
```

**What it does:**
- Processes all XML files in `samples/simple/` and `samples/complex/` folders
- Parses workflows, mappings, sessions, worklets
- Builds DAGs
- Generates visualizations
- Generates target code (PySpark, DLT, SQL)
- Generates test suites

### Step 2: Check Output

**Console Output:**
- ✅ Success indicators for each test
- 📊 DAG visualization previews
- 📝 Code generation confirmations
- File paths for generated artifacts

**Generated Files:**

1. **DAG Visualizations** (`tests/output/`):
   - `dag.dot` - Graphviz DOT format
   - `dag.json` - JSON format with complete structure
   - `dag.mermaid` - Mermaid diagram format

2. **Target Architecture Code** (`generated_code/<mapping_name>/`):
   - `pyspark_code.py` - PySpark DataFrame code
   - `dlt_pipeline.py` - Delta Live Tables pipeline
   - `sql_queries.sql` - SQL queries
   - `mapping_spec.md` - Mapping specification
   - `generated_tests.py` - Pytest test suite
   - `test_data_generator.py` - Test data generator

### Step 3: Validate Results

**Check DAG Files:**
```bash
# View JSON structure
cat tests/output/dag.json | python -m json.tool

# View DOT format
cat tests/output/dag.dot

# View Mermaid format
cat test_output/dag.mermaid
```

**Check Generated Code:**
```bash
# List all generated mappings
ls -la generated_code/

# View PySpark code for a mapping (from simple sample)
cat generated_code/m_load_customer/pyspark_code.py

# View PySpark code for complex mapping
cat generated_code/m_complex_sales_analytics/pyspark_code.py
```

### Step 4: Run Generated Tests

```bash
cd generated_code/m_load_customer
pytest generated_tests.py -v
```

---

## Testing With Frontend

### Prerequisites

- API server running (see Step 1 below)
- Node.js and npm installed
- Frontend dependencies: `cd frontend && npm install`

### Step 1: Start API Server

**Terminal 1:**
```bash
./start_api.sh
```

Or manually:
```bash
cd src
python -m uvicorn api.app:app --reload --port 8000
```

**Verify API is running:**
```bash
curl http://localhost:8000/health
```

### Step 2: Run Integration Test

**Terminal 2:**
```bash
python scripts/test_frontend_integration.py
```

**What it does:**
- Uploads sample workflow file
- Parses workflow
- Builds DAG
- Gets visualizations
- Creates test data file

**Output:**
- File ID (copy this for frontend testing)
- DAG structure summary

### Step 3: Start Frontend

**Terminal 3:**
```bash
cd frontend
npm run dev
```

Frontend will start on `http://localhost:5173`

### Step 4: Test in Browser

1. Navigate to Lineage page
2. Enter File ID from Step 2
3. Click "Load DAG"
4. Interactive graph should display

---

## Viewing DAG Visualizations

### Location of Generated Files

**DAG Visualizations:**
- `test_output/dag.dot`
- `test_output/dag.json`
- `test_output/dag.mermaid`

### How to View Each Format

#### DOT Format (Graphviz)
- **Online**: https://dreampuf.github.io/GraphvizOnline/
- **Command**: `dot -Tpng test_output/dag.dot -o dag.png`

#### JSON Format
```bash
cat test_output/dag.json | python -m json.tool
```

#### Mermaid Format
- **Online**: https://mermaid.live/
- **GitHub**: Supported natively in Markdown

---

## Validation Checklist

### Backend Testing
- [ ] All sample files parsed successfully
- [ ] DAG built with correct nodes and edges
- [ ] Visualizations generated in all formats
- [ ] Code generated (PySpark, DLT, SQL)
- [ ] Test suite generated

### Frontend Testing
- [ ] API server starts successfully
- [ ] File upload works
- [ ] DAG visualization displays
- [ ] Nodes are clickable
- [ ] Export functionality works

---

## Troubleshooting

See [Troubleshooting Guide](troubleshooting.md) for common issues and solutions.

---

**For detailed test results, see [Test Results](results.md)**

