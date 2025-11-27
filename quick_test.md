# Quick Test Guide - Frontend Lineage Visualization

## 🚀 Quick Start (3 Steps)

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

## 📋 Sample File IDs

After running the integration test, you can use these File IDs:

- **Workflow**: Use the File ID from `test_frontend_integration.py` output
- **Test Data**: Check `test_output/frontend_test_data.json` for the File ID

---

## ✅ What to Expect

### DAG Visualization Should Show:

```
S_M_LOAD_CUSTOMER (Session) [Blue]
    ↓
WK_DIM_BUILD (Worklet) [Yellow]  
    ↓
S_M_LOAD_FACT (Session) [Blue]
```

### Features to Test:

- ✅ Interactive graph with nodes and edges
- ✅ Color-coded nodes by type
- ✅ Click nodes to see details
- ✅ Execution levels displayed
- ✅ Export to different formats (JSON, DOT, Mermaid, SVG)

---

## 🐛 Quick Troubleshooting

**API not responding?**
- Check Terminal 1 - is uvicorn running?
- Test: `curl http://localhost:8000/health`

**Frontend can't connect?**
- Check API is running on port 8000
- Check browser console for errors
- Verify CORS is enabled in API

**No visualization?**
- Check File ID is correct
- Check browser console for errors
- Verify DAG was built successfully

---

## 📁 Test Files Created

After running tests:
- `test_output/frontend_test_data.json` - Test data
- `test_output/frontend_test.html` - HTML test page
- `test_output/dag.*` - Visualization files

---

**Ready to test!** 🎉

