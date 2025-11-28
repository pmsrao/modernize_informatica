# Graph Explorer UI Guide

## Overview

The Graph Explorer UI provides an interactive way to navigate and visualize canonical models stored in Neo4j. This guide will walk you through setting up and using the Graph Explorer.

---

## Prerequisites

### 1. Neo4j Setup

First, ensure Neo4j is running:

```bash
# Start Neo4j using Docker
./scripts/setup_neo4j.sh

# Or if Neo4j is already set up, verify it's running
docker ps | grep neo4j
```

### 2. Environment Configuration

Ensure your `.env` file has the correct Neo4j settings:

```bash
# .env file
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
ENABLE_GRAPH_STORE=true
GRAPH_FIRST=true
```

### 3. Start Backend API

```bash
# Start the API server
./start_api.sh
```

The API should be running at `http://localhost:8000`

### 4. Start Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (if not already done)
npm install

# Start development server
npm run dev
```

The frontend should be running at `http://localhost:5173` (or another port if 5173 is busy)

---

## Step-by-Step Usage Guide

### Step 1: Load Mappings into Neo4j

Before you can explore mappings in the UI, you need to parse and save mappings to Neo4j.

#### Option A: Using the API (Recommended)

1. **Upload a mapping file:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/upload" \
     -F "file=@samples/complex/mapping_complex.xml"
   ```
   
   Save the `file_id` from the response.

2. **Parse the mapping with AI enhancement (saves to Neo4j):**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/parse/mapping" \
     -H "Content-Type: application/json" \
     -d '{
       "file_id": "YOUR_FILE_ID_HERE",
       "enhance_model": true
     }'
   ```

   This will:
   - Parse the XML file
   - Normalize to canonical model
   - Apply AI enhancements
   - **Save to Neo4j graph database**

3. **Repeat for additional mappings:**
   ```bash
   # Upload and parse more mappings
   curl -X POST "http://localhost:8000/api/v1/upload" \
     -F "file=@samples/simple/mapping_simple.xml"
   
   curl -X POST "http://localhost:8000/api/v1/parse/mapping" \
     -H "Content-Type: application/json" \
     -d '{"file_id": "NEW_FILE_ID", "enhance_model": true}'
   ```

#### Option B: Using the Upload & Parse UI

1. Click the **"Upload & Parse"** tab in the UI
2. Upload your Informatica XML file
3. After upload, you'll see a checkbox: **"Enhance Model (AI enhancement + save to Neo4j)"**
   - ✅ **Checked** (default): Enables AI enhancement and saves to Neo4j
   - ☐ **Unchecked**: Parses only, does not save to Neo4j
4. Click **"Parse Mapping"** button
5. If "Enhance Model" is checked, the mapping will be automatically saved to Neo4j

---

### Step 2: Access Graph Explorer

1. Open your browser to `http://localhost:5173`
2. Click the **"Graph Explorer"** tab (should be the default)
3. You should see:
   - **Statistics bar** at the top showing total mappings, transformations, and tables
   - **Sidebar** on the left with mapping list
   - **Main visualization area** on the right

---

### Step 3: Explore Mappings

#### View Mapping List

The left sidebar shows all mappings in Neo4j with:
- **Mapping name** (clickable)
- **Complexity** level
- **Source count** (number of source tables)
- **Target count** (number of target tables)
- **Transformation count** (number of transformations)

#### Search Mappings

Use the search box at the top of the sidebar to filter mappings by name.

#### View Mapping Graph

1. **Click on any mapping** in the sidebar
2. The graph visualization will load showing:
   - **Blue node** = Mapping (center)
   - **Green nodes** = Source tables (left)
   - **Red nodes** = Target tables (right)
   - **Colored nodes** = Transformations (middle, color-coded by type)

#### Interact with the Graph

- **Zoom**: Use mouse wheel or zoom controls
- **Pan**: Click and drag the background
- **Select node**: Click on any node to see details
- **Minimap**: Use the minimap in the bottom-right to navigate large graphs
- **Fit view**: Click the fit view button to see the entire graph

---

### Step 4: Explore Node Details

1. **Click any node** in the graph (mapping, source, target, or transformation)
2. A **details panel** will appear on the right showing:
   - Node type
   - Node name
   - Table information (for sources/targets)
   - Transformation type (for transformations)
   - Complexity (for mappings)

3. **Close the panel**: Click the × button or click elsewhere

---

## Understanding the Graph Visualization

### Node Types and Colors

| Node Type | Color | Description |
|-----------|-------|-------------|
| **Mapping** | Blue | The main mapping container |
| **Source** | Green | Source tables that provide data |
| **Target** | Red | Target tables that receive data |
| **Expression** | Orange | Expression transformations |
| **Lookup** | Purple | Lookup transformations |
| **Aggregator** | Light Blue | Aggregation transformations |
| **Joiner** | Red | Join transformations |
| **Router** | Teal | Router transformations |
| **Filter** | Yellow | Filter transformations |
| **Union** | Dark Teal | Union transformations |
| **SourceQualifier** | Dark Gray | Source qualifier transformations |
| **UpdateStrategy** | Orange | Update strategy transformations |
| **Sorter** | Gray | Sorter transformations |
| **Rank** | Dark Orange | Rank transformations |

### Graph Layout

The graph uses a **hierarchical layout**:
- **Left**: Source tables
- **Center**: Mapping and transformations
- **Right**: Target tables
- **Edges**: Show data flow direction (animated arrows)

---

## Troubleshooting

### Issue: "0 mapping(s) found" or "Not Found"

**Cause**: No mappings have been saved to Neo4j yet.

**Solution**:
1. Verify Neo4j is running: `docker ps | grep neo4j`
2. Check `.env` has `ENABLE_GRAPH_STORE=true` and `GRAPH_FIRST=true`
3. Parse at least one mapping with `enhance_model: true` (see Step 1)
4. Refresh the Graph Explorer page

### Issue: "Graph store not enabled" error

**Cause**: Graph store is not enabled in configuration.

**Solution**:
1. Check `.env` file has:
   ```
   ENABLE_GRAPH_STORE=true
   GRAPH_FIRST=true
   ```
2. Restart the API server: `./start_api.sh`

### Issue: Cannot connect to API

**Cause**: Backend API is not running.

**Solution**:
1. Check API is running: `curl http://localhost:8000/health`
2. Start API: `./start_api.sh`
3. Check API logs for errors

### Issue: Graph visualization is empty

**Cause**: Mapping structure might not have been loaded correctly.

**Solution**:
1. Check browser console for errors (F12)
2. Verify the mapping exists in Neo4j:
   ```bash
   curl "http://localhost:8000/api/v1/graph/mappings"
   ```
3. Try reloading the mapping structure:
   - Click "Back to List"
   - Click the mapping again

### Issue: Nodes are overlapping

**Solution**: 
- Use zoom controls to zoom out
- Click "Fit View" button
- Use minimap to navigate
- The layout will adjust automatically

---

## Advanced Features

### View Statistics

The statistics bar at the top shows:
- **Total Mappings**: Number of mappings in Neo4j
- **Total Transformations**: Total transformation nodes
- **Total Tables**: Total table nodes (sources + targets)

### Search Functionality

The search box filters mappings in real-time by:
- Mapping name
- Mapping display name

### Multiple Mappings

You can load multiple mappings and switch between them:
1. Click different mappings in the sidebar
2. Each mapping will show its own graph structure
3. Use "Back to List" to return to the mapping list

---

## Quick Reference

### Keyboard Shortcuts (in Graph View)

- **Mouse wheel**: Zoom in/out
- **Click + drag**: Pan the graph
- **Click node**: View node details
- **Double-click**: (Future: Expand/collapse node)

### API Endpoints Used

The Graph Explorer uses these endpoints:
- `GET /api/v1/graph/mappings` - List all mappings
- `GET /api/v1/graph/mappings/{name}/structure` - Get mapping graph structure
- `GET /api/v1/graph/statistics` - Get graph statistics

---

## Example Workflow

1. **Start services:**
   ```bash
   # Terminal 1: Start Neo4j
   ./scripts/setup_neo4j.sh
   
   # Terminal 2: Start API
   ./start_api.sh
   
   # Terminal 3: Start Frontend
   cd frontend && npm run dev
   ```

2. **Load a mapping:**
   ```bash
   # Upload
   curl -X POST "http://localhost:8000/api/v1/upload" \
     -F "file=@samples/complex/mapping_complex.xml"
   
   # Parse (replace FILE_ID with actual ID)
   curl -X POST "http://localhost:8000/api/v1/parse/mapping" \
     -H "Content-Type: application/json" \
     -d '{"file_id": "FILE_ID", "enhance_model": true}'
   ```

3. **Open Graph Explorer:**
   - Navigate to `http://localhost:5173`
   - Click "Graph Explorer" tab
   - Click on "M_COMPLEX_SALES_ANALYTICS" (or your mapping name)
   - Explore the graph!

---

## Next Steps

After exploring mappings in the Graph Explorer:

1. **Generate Code**: Use the mapping to generate PySpark/DLT code
2. **View Lineage**: Check the "Lineage" tab for workflow-level lineage
3. **View Spec**: Check the "View Spec" tab for mapping specifications
4. **Impact Analysis**: Use API endpoints to analyze dependencies

---

## Support

For issues or questions:
- Check the troubleshooting section above
- Review API logs: Check terminal where `./start_api.sh` is running
- Check browser console: Press F12 in browser
- Review Neo4j logs: `docker logs neo4j-modernize`

---

**Happy Exploring! 🚀**

