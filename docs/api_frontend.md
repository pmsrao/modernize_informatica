# Backend API & Frontend UI

## Backend API (FastAPI)

The backend offers endpoints such as:

- **POST /api/v1/upload**
  - Input: XML file
  - Output: file ID for subsequent operations

- **POST /api/v1/parse/workflow**
  - Input: file ID
  - Output: parsed workflow data

- **POST /api/v1/parse/mapping**
  - Input: file ID
  - Output: canonical model

- **POST /api/v1/generate/pyspark**
  - Input: canonical mapping name or model
  - Output: PySpark code

- **POST /api/v1/generate/dlt**
  - Input: canonical mapping model
  - Output: DLT pipeline code

- **POST /api/v1/generate/sql**
  - Input: canonical mapping model
  - Output: SQL queries

- **POST /api/v1/generate/spec**
  - Input: canonical mapping model
  - Output: mapping specification (Markdown/text)

- **POST /api/v1/ai/explain**
  - Input: mapping + scope
  - Output: AI-generated explanations, summaries, risk notes

- **POST /api/v1/dag/build**
  - Input: workflow/worklet/session data
  - Output: DAG JSON

- **POST /api/v1/dag/visualize**
  - Input: file ID, format (dot, json, mermaid, svg)
  - Output: DAG visualization

- **GET /health**
  - Basic health probe

---

## Frontend UI (React + Vite)

Key screens:

1. **Upload Screen**
   - Upload XML(s)
   - Trigger parsing and canonical model creation

2. **Mapping Explorer**
   - List mappings
   - View details
   - Drill into sources, targets, transformations

3. **Spec Viewer**
   - Render mapping_spec.md for a mapping

4. **Code Viewer**
   - Show generated PySpark, SQL, or DLT code
   - Allow copy/export

5. **Lineage & DAG Viewer**
   - Visualize mapping-level lineage
   - Visualize workflow DAGs
   - Interactive graph with zoom, pan, click

6. **AI Insights Panel**
   - Show rule explanations
   - Mapping summaries
   - Risk & optimization suggestions

---

## API Client

The frontend uses an API client (`frontend/src/services/api.js`) that provides:

- File upload
- Workflow/mapping parsing
- Code generation requests
- DAG visualization
- AI analysis requests

---

**Next**: Learn about [Deployment](deployment.md) and enterprise integration.

