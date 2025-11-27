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
- Sample files in `samples/` directory

### Step 1: Run Test Script

```bash
python test_samples.py
```

**What it does:**
- Processes all XML files in `samples/` folder
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

1. **DAG Visualizations** (`test_output/`):
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
cat test_output/dag.json

# View DOT format
cat test_output/dag.dot

# View Mermaid format
cat test_output/dag.mermaid
```

**Check Generated Code:**
```bash
# List all generated mappings
ls -la generated_code/

# View PySpark code for a mapping
cat generated_code/m_load_customer/pyspark_code.py

# View SQL queries
cat generated_code/m_load_customer/sql_queries.sql
```

### Step 4: Run Generated Tests

```bash
# Run tests for a specific mapping
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

Expected response:
```json
{
  "status": "ok",
  "version": "0.1.0",
  "service": "Informatica Modernization Accelerator"
}
```

### Step 2: Run Integration Test

**Terminal 2:**
```bash
python test_frontend_integration.py
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
- Test data file location

### Step 3: Start Frontend

**Terminal 3:**
```bash
cd frontend
npm run dev
```

Frontend will start on `http://localhost:5173` (or similar port)

### Step 4: Test in Browser

#### Option A: HTML Test Page

1. **Open test page:**
   ```bash
   open test_output/frontend_test.html
   ```

2. **Test API Connection:**
   - Click "Test API Connection"
   - Should show ✅ API is running

3. **Upload File:**
   - Click "Choose File"
   - Select `samples/workflow_complex.xml`
   - Click "Upload File"
   - Copy the File ID

4. **Load DAG:**
   - Paste File ID in input field
   - Click "Load DAG"
   - Visualization should appear

#### Option B: React Frontend

1. **Navigate to Lineage Page:**
   - Open `http://localhost:5173`
   - Go to Lineage page

2. **Load DAG:**
   - Enter File ID from Step 2
   - Click "Load DAG"
   - Interactive graph should display

3. **Test Features:**
   - Click nodes to see details
   - Check execution levels
   - Test export functionality

### Step 5: Validate Frontend

**Check:**
- ✅ DAG visualization displays correctly
- ✅ Nodes are color-coded (Sessions=blue, Worklets=yellow)
- ✅ Edges show connections
- ✅ Node details panel works
- ✅ Execution levels displayed
- ✅ Export buttons work

---

## Viewing DAG Visualizations

### Location of Generated Files

**DAG Visualizations:**
- `test_output/dag.dot`
- `test_output/dag.json`
- `test_output/dag.mermaid`

### How to View Each Format

#### 1. DOT Format (Graphviz)

**View as text:**
```bash
cat test_output/dag.dot
```

**Render as image:**
```bash
# Install Graphviz first: brew install graphviz (macOS) or apt-get install graphviz (Linux)
dot -Tpng test_output/dag.dot -o dag.png
open dag.png  # macOS
```

**Online viewer:**
- Copy content to: https://dreampuf.github.io/GraphvizOnline/
- Or use: https://edotor.net/

#### 2. JSON Format

**View structure:**
```bash
cat test_output/dag.json | python -m json.tool
```

**Or use jq:**
```bash
cat test_output/dag.json | jq '.'
```

**In Python:**
```python
import json
with open('test_output/dag.json') as f:
    dag = json.load(f)
    print(f"Nodes: {len(dag['nodes'])}")
    print(f"Edges: {len(dag['edges'])}")
    print(f"Execution Levels: {dag['execution_levels']}")
```

#### 3. Mermaid Format

**View as text:**
```bash
cat test_output/dag.mermaid
```

**Render online:**
- Copy content to: https://mermaid.live/
- Or use GitHub/GitLab (Mermaid is supported natively)

**In Markdown:**
```markdown
```mermaid
[paste mermaid content here]
```
```

#### 4. In Frontend

**HTML Test Page:**
- Open `test_output/frontend_test.html`
- Enter File ID and click "Load DAG"
- Interactive SVG visualization

**React Frontend:**
- Navigate to Lineage page
- Enter File ID
- Interactive graph with zoom, pan, click

---

## Validation Checklist

### Backend Testing (Without Frontend)

- [ ] All sample files parsed successfully
- [ ] DAG built with correct nodes and edges
- [ ] Topological order is correct
- [ ] Execution levels identified
- [ ] Visualizations generated in all formats
- [ ] PySpark code generated
- [ ] DLT code generated
- [ ] SQL code generated
- [ ] Test suite generated
- [ ] All files saved to correct directories

### Frontend Testing (With Frontend)

- [ ] API server starts successfully
- [ ] Health check endpoint works
- [ ] File upload works
- [ ] Workflow parsing works
- [ ] DAG building works
- [ ] DAG visualization displays
- [ ] Nodes are clickable
- [ ] Node details panel works
- [ ] Execution levels displayed
- [ ] Export functionality works
- [ ] No console errors

### Code Generation Validation

- [ ] PySpark code is syntactically correct
- [ ] DLT code follows DLT patterns
- [ ] SQL queries are valid
- [ ] Generated tests can run
- [ ] Code matches mapping structure

### DAG Validation

- [ ] All nodes present
- [ ] All edges correct
- [ ] No cycles detected
- [ ] Topological order makes sense
- [ ] Execution levels are logical

---

## Troubleshooting

### API Not Starting

**Error:** `ModuleNotFoundError` or import errors

**Solution:**
```bash
# Install dependencies
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

### File Upload Fails

**Error:** `File not found` or upload errors

**Solution:**
- Check file exists in `samples/` directory
- Verify file is XML format
- Check file size (max 100MB)
- Ensure `uploads/` directory exists and is writable

### DAG Not Displaying

**Error:** Empty visualization or errors

**Solution:**
- Check File ID is correct
- Verify workflow was parsed successfully
- Check browser console for errors
- Verify API response in Network tab
- Check DAG was built (check API logs)

### Code Generation Issues

**Error:** Generated code has errors

**Solution:**
- Check canonical model structure
- Verify transformations are parsed correctly
- Review generated code for syntax errors
- Check generator logs for warnings

### Frontend Connection Issues

**Error:** CORS errors or connection refused

**Solution:**
- Verify API is running on port 8000
- Check CORS settings in `src/api/app.py`
- Verify frontend API base URL in `frontend/src/services/api.js`
- Check firewall settings

---

## Quick Reference

### Test Commands

```bash
# Backend only
python test_samples.py

# With API
./start_api.sh  # Terminal 1
python test_frontend_integration.py  # Terminal 2

# With Frontend
cd frontend && npm run dev  # Terminal 3
```

### File Locations

```
test_output/
  ├── dag.dot
  ├── dag.json
  ├── dag.mermaid
  └── frontend_test.html

generated_code/
  └── <mapping_name>/
      ├── pyspark_code.py
      ├── dlt_pipeline.py
      ├── sql_queries.sql
      ├── mapping_spec.md
      ├── generated_tests.py
      └── test_data_generator.py
```

### API Endpoints

- Health: `GET http://localhost:8000/health`
- Upload: `POST http://localhost:8000/api/v1/upload`
- Parse: `POST http://localhost:8000/api/v1/parse/workflow`
- Build DAG: `POST http://localhost:8000/api/v1/dag/build`
- Visualize: `POST http://localhost:8000/api/v1/dag/visualize`

### Viewing Visualizations

- **DOT**: Use Graphviz or online viewer
- **JSON**: Use `cat` or `jq` or Python
- **Mermaid**: Use mermaid.live or GitHub
- **Frontend**: Open HTML page or React app

---

## Next Steps

1. ✅ Run backend tests
2. ✅ Validate generated code
3. ✅ Test with frontend
4. ✅ Review visualizations
5. ✅ Run generated test suites
6. ✅ Customize generated code

---

**Status**: Ready for comprehensive testing! 🚀

