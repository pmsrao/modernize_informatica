# Frontend Testing Guide

## Overview

Guide for testing the frontend lineage visualization and UI components.

---

## Quick Start (3 Steps)

### Step 1: Start API (Terminal 1)
```bash
./start_api.sh
```

Or manually:
```bash
cd src && python -m uvicorn api.app:app --reload --port 8000
```

### Step 2: Run Integration Test (Terminal 2)
```bash
python test_frontend_integration.py
```

**Copy the File ID** from the output (looks like: `abc123-def456-...`)

### Step 3: Test Frontend

**Option A: HTML Test Page**
```bash
open test_output/frontend_test.html
```
- Enter the File ID
- Click "Load DAG"
- See the visualization!

**Option B: React Frontend (Terminal 3)**
```bash
cd frontend && npm run dev
```
- Open http://localhost:5173
- Go to Lineage page
- Enter File ID
- Click "Load DAG"

---

## What Was Set Up

### 1. Enhanced DAG Visualizer Backend ✅
- Multiple output formats (DOT, JSON, Mermaid, SVG)
- Color-coded nodes by type
- Execution level visualization
- Metadata support

### 2. DAG Visualization API Endpoint ✅
- **Endpoint**: `POST /api/v1/dag/visualize`
- **Parameters**: `format` (dot, json, mermaid, svg), `include_metadata`

### 3. Frontend Lineage Visualization ✅
- Interactive SVG graph
- Node click for details
- Color-coded nodes
- Execution levels display
- Export functionality

---

## Testing Status

### Backend Tests ✅
- ✅ Workflow parsing with sample files
- ✅ DAG building with topological sorting
- ✅ DAG visualization in multiple formats
- ✅ API endpoints functional

### Frontend Tests ✅
- ✅ HTML test page created
- ✅ React frontend integrated
- ✅ Lineage visualization working
- ✅ Node interaction functional

---

## Expected Results

### DAG Structure
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

---

## API Endpoints

### Upload File
```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@samples/complex/workflow_complex.xml"
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

## Validation Checklist

- [ ] API server starts successfully
- [ ] File upload works
- [ ] Workflow parsing works
- [ ] DAG building works
- [ ] DAG visualization displays
- [ ] Nodes are clickable
- [ ] Node details panel works
- [ ] Execution levels displayed
- [ ] Export functionality works
- [ ] No console errors

---

## Troubleshooting

See [Troubleshooting Guide](troubleshooting.md) for common frontend issues.

---

**For comprehensive testing guide, see [Testing Guide](guide.md)**

