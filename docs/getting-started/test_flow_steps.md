# Test Flow Execution Steps

This document outlines the complete steps to run the test flow, including Neo4j schema setup.

## Prerequisites

1. **Python Dependencies**: Install required packages
   ```bash
   pip install -r requirements.txt
   ```

2. **Neo4j Running** (if using graph store):
   ```bash
   ./scripts/setup/setup_neo4j.sh
   ```
   Or manually:
   ```bash
   docker run -d \
       --name neo4j-modernize \
       -p 7474:7474 -p 7687:7687 \
       -e NEO4J_AUTH=neo4j/password \
       neo4j:5.15-community
   ```

3. **Environment Configuration**: Create/update `.env` file
   ```bash
   # Neo4j Configuration (if using graph store)
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=password
   ENABLE_GRAPH_STORE=true
   GRAPH_FIRST=true
   ```

4. **API Server** (optional, but recommended):
   ```bash
   ./start_api.sh
   ```

---

## Step-by-Step Execution

### Step 0: Create Neo4j Schema (Required if using graph store)

**⚠️ IMPORTANT**: Before running the test flow with Neo4j enabled, you must create the schema. This will **DELETE ALL EXISTING DATA** in Neo4j.

```bash
python scripts/schema/create_neo4j_schema.py
```

**What it does:**
- Drops all existing nodes and relationships in Neo4j
- Creates indexes with platform-agnostic labels (`:Transformation`, `:Pipeline`, `:Task`, etc.)
- Sets up constraints for uniqueness

**When to run:**
- **First time setup**: Before running test flow for the first time
- **After schema changes**: If the Neo4j schema has been updated
- **Clean slate**: When you want to start fresh (deletes all existing data)

**Note**: The script will prompt for confirmation before deleting data.

---

### Step 1: Upload Files

Upload Informatica XML files to the staging directory:

```bash
make upload FILES='samples/super_complex_enhanced/*.xml'
```

Or use default files:
```bash
make upload
```

**What it does:**
- Copies XML files to `workspace/staging/`
- Optionally uploads to API (if running)
- Creates `upload_results.json` with file IDs

**Output:**
- Files in `workspace/staging/`
- `workspace/staging/upload_results.json`

---

### Step 2: Parse Files

Parse all uploaded files (transformations, pipelines, tasks, sub pipelines, reusable transformations):

```bash
make parse
```

**What it does:**
- Parses all XML files in staging directory
- Creates canonical models for transformations
- Parses structure for pipelines, tasks, sub pipelines, reusable transformations
- Saves parsed data to `workspace/parsed/`
- **If Neo4j enabled**: Saves components to Neo4j graph database

**Output:**
- `workspace/parsed/{transformation_name}.json` (canonical models)
- `workspace/parsed/{component_name}_{type}.json` (other components)
- Neo4j nodes and relationships (if graph store enabled)

---

### Step 3: Enhance with AI

Enhance parsed transformation models with AI:

```bash
make enhance
```

**What it does:**
- Loads parsed canonical models from `workspace/parsed/`
- Enhances with AI (adds optimization hints, data quality rules, etc.)
- Saves enhanced models to `workspace/parse_ai/`
- **If Neo4j enabled**: Updates Neo4j with enhanced models

**Output:**
- `workspace/parse_ai/{transformation_name}.json` (enhanced canonical models)

**Note**: Only transformations are enhanced. Pipelines, tasks, and sub pipelines are not enhanced.

---

### Step 4: Generate Hierarchy (Optional)

Generate hierarchy/tree structure visualization:

```bash
make hierarchy
```

**What it does:**
- Generates hierarchy diagrams showing component relationships
- Saves diagrams to `workspace/diagrams/`

**Output:**
- `workspace/diagrams/hierarchy_*.png` or similar

---

### Step 5: Generate Lineage (Optional)

Generate lineage diagrams:

```bash
make lineage
```

**What it does:**
- Generates lineage diagrams showing data flow
- Saves diagrams to `workspace/diagrams/`

**Output:**
- `workspace/diagrams/lineage_*.png` or similar

---

### Step 6: Generate Canonical Model Images (Optional)

Generate canonical model visualizations:

```bash
make canonical
```

**What it does:**
- Generates visual representations of canonical models
- Saves images to `workspace/diagrams/`

**Output:**
- `workspace/diagrams/canonical_*.png` or similar

---

### Step 7: Generate Code

Generate target platform code (PySpark, DLT, SQL):

```bash
make code
```

**What it does:**
- Loads canonical models (prefers enhanced from `workspace/parse_ai/`, falls back to `workspace/parsed/`)
- **If Neo4j enabled**: Uses workflow-aware generation (organizes by pipeline structure)
- **If Neo4j disabled**: Uses file-based generation (flat structure)
- Generates PySpark, DLT, and SQL code
- Saves code to `workspace/generated/`

**Output:**
- `workspace/generated/{transformation_name}/` directories with code files
- `workspace/generated/generation_summary.json`

**Workflow-Aware Structure** (if Neo4j enabled):
```
workspace/generated/workflows/
├── {pipeline_name}/
│   ├── sessions/
│   │   └── {task_name}/
│   │       └── transformations/
│   │           └── {transformation_name}/
│   │               ├── {transformation_name}_pyspark.py
│   │               ├── {transformation_name}_dlt.py
│   │               └── {transformation_name}_sql.sql
```

**File-Based Structure** (if Neo4j disabled):
```
workspace/generated/
├── {transformation_name}/
│   ├── {transformation_name}_pyspark.py
│   ├── {transformation_name}_dlt.py
│   └── {transformation_name}_sql.sql
```

---

### Step 8: Review & Fix Code with AI

Review and fix generated code using AI:

```bash
make review
```

**What it does:**
- Finds all generated code files in `workspace/generated/`
- Reviews each file for issues
- Fixes code if issues are found
- Saves reviewed and fixed code to `workspace/generated_ai/`

**Output:**
- `workspace/generated_ai/{filename}` (fixed code files)
- `workspace/generated_ai/{filename}_review.json` (review results)
- `workspace/generated_ai/review_summary.json`

**Note**: Requires LLM configuration (OpenAI API key or similar).

---

### Step 9: Generate Diff Reports (Optional)

Generate diff reports comparing parsed vs enhanced and generated vs reviewed:

```bash
make diff
```

**What it does:**
- Compares `workspace/parsed/` vs `workspace/parse_ai/` (canonical models)
- Compares `workspace/generated/` vs `workspace/generated_ai/` (code)
- Generates HTML diff reports

**Output:**
- `workspace/diffs/index.html` (main diff report)
- `workspace/diffs/parsed_vs_enhanced.html` (canonical model diffs)
- `workspace/diffs/generated_vs_reviewed.html` (code diffs)

---

## Running All Steps

Run all steps in sequence:

```bash
make test-all
```

This will:
1. Clean `workspace/` directory
2. Upload files
3. Parse files
4. Enhance with AI
5. Generate hierarchy
6. Generate lineage
7. Generate canonical images
8. Generate code
9. Review and fix code
10. Generate diff reports

**Logs**: All output is logged to `workspace/exec_steps_logs.txt`

---

## Quick Reference

### Complete Setup and Run (First Time)

```bash
# 1. Setup Neo4j (if using graph store)
./scripts/setup/setup_neo4j.sh

# 2. Create Neo4j schema (IMPORTANT: deletes all existing data)
python scripts/schema/create_neo4j_schema.py

# 3. Run all steps
make test-all
```

### Subsequent Runs (Schema Already Created)

```bash
# Option 1: Run all steps (will clean workspace first)
make test-all

# Option 2: Run individual steps
make upload
make parse
make enhance
make code
make review
```

### Clean Start (Recreate Schema)

```bash
# 1. Recreate Neo4j schema (deletes all data)
python scripts/schema/create_neo4j_schema.py

# 2. Clean workspace directory
make clean-all

# 3. Run test flow
make test-all
```

---

## Directory Structure

After running the test flow, you'll have:

```
workspace/
├── staging/              # Uploaded XML files
├── parsed/               # Parsed canonical models (JSON)
├── parse_ai/            # AI-enhanced canonical models
├── generated/           # Generated code (PySpark/DLT/SQL)
├── generated_ai/        # AI-reviewed and fixed code
├── diagrams/            # Visualizations (hierarchy, lineage, canonical)
├── diffs/               # Diff reports (HTML)
└── exec_steps_logs.txt  # Execution logs
```

---

## Troubleshooting

### Neo4j Connection Issues

**Error**: `Neo4j connection failed`

**Solutions**:
1. Check if Neo4j is running:
   ```bash
   docker ps | grep neo4j
   ```

2. Verify credentials in `.env`:
   ```bash
   cat .env | grep NEO4J
   ```

3. Test connection:
   ```bash
   python -c "from graph.graph_store import GraphStore; GraphStore()"
   ```

### Schema Not Created

**Error**: `Index not found` or `Label not found`

**Solution**: Run schema creation script:
```bash
python scripts/schema/create_neo4j_schema.py
```

### Missing Files

**Error**: `File not found` or `No files to parse`

**Solution**: Ensure files are uploaded:
```bash
make upload FILES='path/to/your/files/*.xml'
```

### API Not Running

**Warning**: `API not available, using direct mode`

**Solution**: Start API server (optional):
```bash
./start_api.sh
```

---

## Environment Variables

Key environment variables (set in `.env` file):

```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Graph Store Configuration
ENABLE_GRAPH_STORE=true      # Enable Neo4j graph store
GRAPH_FIRST=true              # Prefer graph store over files

# API Configuration
API_URL=http://localhost:8000

# LLM Configuration (for AI enhancement and review)
OPENAI_API_KEY=your_api_key_here
```

---

## Related Documentation

- **Test Flow Guide**: `docs/testing/test_flow_guide.md`
- **Neo4j Setup**: `docs/getting-started/setup_neo4j.md`
- **Canonical Model**: `docs/modules/canonical_model.md`
- **Code Generation**: `docs/modules/code_generation.md`

