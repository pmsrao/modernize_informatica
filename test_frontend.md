# Frontend Lineage Visualization Testing Guide

## Overview

This guide helps you test the frontend lineage visualization with the sample workflow files.

---

## Prerequisites

1. **Python dependencies installed**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Node.js and npm** (for frontend):
   ```bash
   cd frontend
   npm install
   ```

---

## Step 1: Start the API Server

Open a terminal and run:

```bash
cd src
uvicorn api.app:app --reload --port 8000
```

Or from the project root:

```bash
python -m uvicorn src.api.app:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Keep this terminal open** - the API needs to be running.

---

## Step 2: Test API Endpoints

In a **new terminal**, run the integration test:

```bash
python test_frontend_integration.py
```

This will:
- ✅ Check API health
- ✅ Upload `samples/workflow_complex.xml`
- ✅ Parse the workflow
- ✅ Build the DAG
- ✅ Get visualizations in multiple formats
- ✅ Create test data file for frontend

**Expected output:**
```
✅ API is running
✅ File uploaded: workflow_complex.xml
   File ID: <some-uuid>
✅ Workflow parsed successfully
✅ DAG built successfully
   Nodes: 3
   Edges: 2
✅ DAG visualization retrieved (JSON)
✅ DAG visualization retrieved (DOT)
✅ DAG visualization retrieved (Mermaid)
```

**Note the File ID** - you'll need it for frontend testing.

---

## Step 3: Test with HTML Test Page

A simple HTML test page has been created at `test_output/frontend_test.html`.

1. **Open the file in a browser**:
   ```bash
   open test_output/frontend_test.html  # macOS
   # or
   xdg-open test_output/frontend_test.html  # Linux
   # or just double-click the file
   ```

2. **Test the page**:
   - Click "Test API Connection" - should show ✅
   - Upload `samples/workflow_complex.xml` - should get a File ID
   - Enter the File ID and click "Load DAG" - should display the DAG visualization

---

## Step 4: Test with React Frontend

### Start the Frontend

In a **new terminal**:

```bash
cd frontend
npm run dev
```

The frontend should start on `http://localhost:5173` (or similar).

### Test the Lineage Page

1. **Navigate to the Lineage page** in the browser
2. **Enter the File ID** from Step 2
3. **Click "Load DAG"**
4. **Verify**:
   - DAG visualization appears
   - Nodes are color-coded (Sessions = blue, Worklets = yellow)
   - Edges show connections
   - Execution levels are displayed
   - Node details panel works when clicking nodes

---

## Step 5: Test Different Formats

You can test exporting the DAG in different formats:

1. **In the frontend**, select a format from the dropdown:
   - JSON
   - DOT
   - Mermaid
   - SVG

2. **Click "Export DAG"** - the file should download

---

## Expected Results

### DAG Structure

The workflow `WF_CUSTOMER_DAILY` should show:

```
S_M_LOAD_CUSTOMER (Session) - Blue
    ↓
WK_DIM_BUILD (Worklet) - Yellow
    ↓
S_M_LOAD_FACT (Session) - Blue
```

### Execution Levels

- **Level 1**: `S_M_LOAD_CUSTOMER` (runs first)
- **Level 2**: `WK_DIM_BUILD` (runs after Level 1)
- **Level 3**: `S_M_LOAD_FACT` (runs after Level 2)

### Node Details

Clicking on a node should show:
- Node name
- Node type
- Metadata (if available)

---

## Troubleshooting

### API Not Running

**Error**: `Cannot connect to API`

**Solution**: 
1. Check if API is running on port 8000
2. Verify with: `curl http://localhost:8000/health`
3. Check for port conflicts

### CORS Errors

**Error**: CORS policy blocking requests

**Solution**: 
- The API has CORS enabled for all origins
- If issues persist, check `src/api/app.py` CORS settings

### File Upload Fails

**Error**: File upload returns error

**Solution**:
1. Check file size (max 100MB)
2. Verify file is XML format
3. Check `uploads/` directory exists and is writable

### DAG Not Displaying

**Error**: DAG visualization is empty

**Solution**:
1. Verify workflow was parsed correctly
2. Check browser console for errors
3. Verify File ID is correct
4. Check API response in Network tab

---

## Manual API Testing

You can also test the API directly with curl:

### Upload File
```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@samples/workflow_complex.xml"
```

### Parse Workflow
```bash
curl -X POST http://localhost:8000/api/v1/parse/workflow \
  -H "Content-Type: application/json" \
  -d '{"file_id": "<file-id-from-upload>"}'
```

### Build DAG
```bash
curl -X POST http://localhost:8000/api/v1/dag/build \
  -H "Content-Type: application/json" \
  -d '{"file_id": "<file-id>"}'
```

### Get Visualization
```bash
curl -X POST "http://localhost:8000/api/v1/dag/visualize?format=json" \
  -H "Content-Type: application/json" \
  -d '{"file_id": "<file-id>"}'
```

---

## Test Data Files

After running `test_frontend_integration.py`, you'll have:

- `test_output/frontend_test_data.json` - Test data with File ID and DAG structure
- `test_output/frontend_test.html` - Simple HTML test page
- `test_output/dag.dot` - DOT format visualization
- `test_output/dag.json` - JSON format visualization
- `test_output/dag.mermaid` - Mermaid format visualization

---

## Next Steps

1. ✅ Test with more complex workflows
2. ✅ Test with multiple files
3. ✅ Test worklet expansion
4. ✅ Test with mapping files for column-level lineage
5. ✅ Test export functionality
6. ✅ Test node interaction (click, hover, etc.)

---

## Quick Start Commands

```bash
# Terminal 1: Start API
cd src && uvicorn api.app:app --reload --port 8000

# Terminal 2: Run integration test
python test_frontend_integration.py

# Terminal 3: Start frontend
cd frontend && npm run dev
```

Then open `http://localhost:5173` in your browser!

---

**Status**: Ready for testing! 🚀

