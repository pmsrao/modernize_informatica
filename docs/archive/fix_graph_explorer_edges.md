# Fix Graph Explorer Edges - Action Required

## Problem Summary

The Graph Explorer is not showing arrows/edges between components because:

1. **Sources are missing** (0 sources in Neo4j)
2. **Connectors are incomplete** (only 10 connectors, should be ~15)
3. **The mapping was parsed with the old parser** that didn't extract connectors properly

## Root Cause

The mapping `M_COMPLEX_SALES_ANALYTICS` was parsed and saved to Neo4j **before** the connector parser was fixed. The old parser:
- Didn't extract connectors from `FROMINSTANCE`/`TOINSTANCE` attributes
- Only looked for `FROMTRANSFORMATION`/`TOTRANSFORMATION` child elements

## Solution

**Re-parse the mapping** with the fixed parser:

### Option 1: Re-parse via UI (Recommended)

1. Go to **Upload & Parse** tab
2. Select `M_COMPLEX_SALES_ANALYTICS` from the dropdown
3. **Check** "Enhance Model (AI enhancement + save to Neo4j)"
4. Click **"Parse Mapping"**
5. Wait for success message
6. Go to **Graph Explorer** tab
7. Select `M_COMPLEX_SALES_ANALYTICS` again
8. You should now see:
   - Sources (CUSTOMER_SRC, ORDER_SRC, PRODUCT_SRC)
   - All transformations connected with arrows
   - Proper data flow visualization

### Option 2: Clean and Re-upload

If Option 1 doesn't work:

```bash
# Clean Neo4j and uploaded files
python scripts/utils/cleanup.py --neo4j --uploads --yes

# Then re-upload and parse via UI:
# 1. Upload the mapping file again
# 2. Parse with "Enhance Model" enabled
```

## What Was Fixed

### 1. Connector Parser (`src/parser/mapping_parser.py`)
- Now handles `FROMINSTANCE`/`TOINSTANCE` attributes (Informatica format)
- Falls back to `FROMTRANSFORMATION`/`TOTRANSFORMATION` if needed
- Handles `FROMFIELD`/`TOFIELD` in addition to `FROMPORT`/`TOPORT`

### 2. Graph Store (`src/graph/graph_store.py`)
- Now saves **Source → Transformation** connectors
- Now saves **Transformation → Target** connectors
- Now saves **Transformation → Transformation** connectors
- All stored as `CONNECTS_TO` relationships in Neo4j

### 3. Graph Loading (`src/graph/graph_store.py`)
- Loads all connector types from Neo4j relationships
- Reconstructs connectors for Source→Trans, Trans→Trans, Trans→Target

### 4. API Endpoint (`src/api/routes.py`)
- Queries all `CONNECTS_TO` relationships from graph
- Merges graph relationships with canonical model connectors
- Ensures all connections are available for edge generation

### 5. Frontend (`frontend/src/pages/GraphExplorerPage.jsx`)
- Enhanced edge styling with colors and animation
- Added debugging console logs
- Improved React Flow edge rendering

## Verification

After re-parsing, check:

1. **Browser Console** (F12):
   - Should see: "Processed edges: X edges created" (where X > 20)
   - Should see edge details with source/target IDs

2. **Graph Explorer**:
   - Should see sources on the left
   - Should see blue animated arrows connecting components
   - Should see proper hierarchical layout

3. **API Response**:
   ```bash
   curl "http://localhost:8000/api/v1/graph/mappings/M_COMPLEX_SALES_ANALYTICS/structure" | jq '.graph.edges | length'
   ```
   Should return > 20 edges

## Expected Result

After re-parsing, you should see:
- **Sources**: 3 (CUSTOMER_SRC, ORDER_SRC, PRODUCT_SRC)
- **Targets**: 3 (TGT_SALES_FACT, TGT_CUSTOMER_DIM, TGT_PRODUCT_SUMMARY)
- **Transformations**: 11 (all transformations)
- **Edges**: ~20-25 (all data flow connections)
- **Visual**: Blue animated arrows showing data flow from sources → transformations → targets

