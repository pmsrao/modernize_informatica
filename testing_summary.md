# Testing Summary - Quick Answers

## a) Does `python test_samples.py` process all files in the samples folder?

**✅ YES** - The script now processes **all XML files** in the `samples/` directory.

### What it does:

1. **Scans `samples/` folder** for all `.xml` files
2. **Automatically detects file type**:
   - `*workflow*.xml` → WorkflowParser
   - `*mapping*.xml` → MappingParser  
   - `*session*.xml` → SessionParser
   - `*worklet*.xml` → WorkletParser

3. **Processes each file**:
   - Parses the XML
   - Builds DAGs (for workflows)
   - Generates code (for mappings)
   - Creates visualizations

4. **Organizes output**:
   - DAGs saved to `test_output/dags/<workflow_name>/`
   - Code saved to `generated_code/<mapping_name>/`

### Example Output:

```
📁 Found 4 XML file(s) in samples directory:
   - mapping_complex.xml
   - session_complex.xml
   - workflow_complex.xml
   - worklet_complex.xml

Processing: workflow_complex.xml
✅ Workflow parsed: WF_CUSTOMER_DAILY
✅ DAG visualizations saved to: test_output/dags/wf_customer_daily/

Processing: mapping_complex.xml
✅ Mapping parsed: M_LOAD_CUSTOMER
✅ Code generated to: generated_code/m_load_customer/
```

---

## b) Where can we see the DAGs and visualizations?

### File Locations:

1. **Main DAG** (from first workflow processed):
   - `test_output/dag.dot`
   - `test_output/dag.json`
   - `test_output/dag.mermaid`

2. **All Workflow DAGs** (organized by workflow name):
   - `test_output/dags/<workflow_name>/dag.dot`
   - `test_output/dags/<workflow_name>/dag.json`
   - `test_output/dags/<workflow_name>/dag.mermaid`

### How to View:

#### Option 1: Command Line

```bash
# View JSON structure
cat test_output/dag.json | python -m json.tool

# View DOT format
cat test_output/dag.dot

# View Mermaid format
cat test_output/dag.mermaid
```

#### Option 2: Online Viewers

**DOT Format:**
- Copy content from `dag.dot`
- Paste to: https://dreampuf.github.io/GraphvizOnline/
- Or: https://edotor.net/

**Mermaid Format:**
- Copy content from `dag.mermaid`
- Paste to: https://mermaid.live/
- Or use in GitHub/GitLab (native support)

**JSON Format:**
- Use any JSON viewer
- Or: `cat test_output/dag.json | jq '.'`

#### Option 3: Render as Image (DOT)

```bash
# Install Graphviz first
brew install graphviz  # macOS
# or
apt-get install graphviz  # Linux

# Render to PNG
dot -Tpng test_output/dag.dot -o dag.png
open dag.png  # macOS
```

#### Option 4: Frontend Visualization

**HTML Test Page:**
```bash
# After running test_frontend_integration.py
open test_output/frontend_test.html
```

**React Frontend:**
```bash
cd frontend && npm run dev
# Open http://localhost:5173
# Navigate to Lineage page
```

---

## c) Comprehensive Testing Document

**See: `testing_guide.md`** for complete step-by-step instructions.

### Quick Reference:

#### Testing Without Frontend:

```bash
# 1. Run test script
python test_samples.py

# 2. Check generated files
ls -la test_output/
ls -la generated_code/

# 3. View DAG visualizations
cat test_output/dag.json | python -m json.tool

# 4. Review generated code
cat generated_code/m_load_customer/pyspark_code.py
```

#### Testing With Frontend:

```bash
# Terminal 1: Start API
./start_api.sh

# Terminal 2: Run integration test
python test_frontend_integration.py
# Copy the File ID from output

# Terminal 3: Start frontend
cd frontend && npm run dev

# Browser: Open http://localhost:5173
# Enter File ID and test visualization
```

### Validation Steps:

**Backend:**
- [ ] All sample files processed
- [ ] DAGs generated for all workflows
- [ ] Code generated for all mappings
- [ ] Files saved to correct directories

**Frontend:**
- [ ] API server running
- [ ] File upload works
- [ ] DAG visualization displays
- [ ] Node interaction works
- [ ] Export functionality works

**See `testing_guide.md` for detailed validation checklist.**

---

## File Structure After Testing

```
test_output/
├── dag.dot                    # Main workflow DAG (DOT)
├── dag.json                   # Main workflow DAG (JSON)
├── dag.mermaid                # Main workflow DAG (Mermaid)
└── dags/
    └── <workflow_name>/
        ├── dag.dot
        ├── dag.json
        └── dag.mermaid

generated_code/
└── <mapping_name>/
    ├── pyspark_code.py
    ├── dlt_pipeline.py
    ├── sql_queries.sql
    ├── mapping_spec.md
    ├── generated_tests.py
    └── test_data_generator.py
```

---

## Quick Commands

```bash
# Process all samples
python test_samples.py

# View DAG JSON
cat test_output/dag.json | python -m json.tool

# List all generated mappings
ls generated_code/

# View PySpark code
cat generated_code/m_load_customer/pyspark_code.py

# Test with frontend
./start_api.sh  # Terminal 1
python test_frontend_integration.py  # Terminal 2
cd frontend && npm run dev  # Terminal 3
```

---

**For detailed instructions, see `testing_guide.md`** 📚

