# CLI Usage Guide

This guide covers all command-line interface (CLI) tools available in the Informatica Modernization Accelerator.

---

## Table of Contents

1. [Main CLI Tool](#main-cli-tool)
2. [Validation Scripts](#validation-scripts)
3. [Test Flow Script](#test-flow-script)
4. [Utility Scripts](#utility-scripts)
5. [Setup Scripts](#setup-scripts)
6. [Environment Configuration](#environment-configuration)

---

## Main CLI Tool

The main CLI tool (`informatica-modernize`) provides high-level commands for assessment, reconciliation, and configuration management.

### Installation

The CLI is available as a Python module. Run commands from the project root:

**Method 1: Use wrapper script (Easiest)**
```bash
./scripts/imod <command> [options]
```

**Method 2: Set PYTHONPATH (Recommended for shell sessions)**
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd):$(pwd)/src"
python -m cli.main <command> [options]
```

**Method 3: Use PYTHONPATH inline**
```bash
PYTHONPATH="$(pwd)/src:$PYTHONPATH" python -m cli.main <command> [options]
```

**Method 4: Create an alias**
```bash
alias informatica-modernize="PYTHONPATH=\"\$(pwd)/src:\$PYTHONPATH\" python -m cli.main"
# Or use the wrapper script
alias informatica-modernize="./scripts/imod"
# Or create a shorter alias
alias imod="./scripts/imod"
```

**Note**: The CLI module is located in `src/cli/`, so `src` must be in your `PYTHONPATH` for the module to be found. The wrapper script (`scripts/imod`) automatically sets the PYTHONPATH for you.

### Commands Overview

```
informatica-modernize
├── upload          # Upload Informatica XML files
├── parse           # Parse XML files to canonical models
├── enhance         # Enhance canonical models with AI
├── generate-code   # Generate code from canonical models
├── review          # Review generated code with AI
├── fix             # Fix code issues
├── assess          # Assessment commands
│   ├── profile     # Profile repository
│   ├── analyze     # Analyze components and identify blockers
│   ├── waves       # Generate migration wave plan
│   ├── report      # Generate assessment report
│   └── tco         # Calculate TCO and ROI
├── reconcile       # Reconciliation commands
│   ├── mapping     # Reconcile a mapping
│   └── workflow    # Reconcile a workflow
└── config          # Configuration commands
    ├── show        # Show current configuration
    └── validate    # Validate configuration
```

### Migration Flow Commands

These commands drive the complete modernization flow from upload to code generation.

#### Upload Files

Upload Informatica XML files (mappings, workflows, sessions, worklets, mapplets) to the system.

```bash
python -m cli.main upload <file|directory> [OPTIONS]
```

**Arguments**:
- `<file|directory>`: Path to file or directory to upload

**Options**:
- `--recursive`: Recursively upload files from directory
- `--session-id <id>`: Session ID to group uploads (auto-generated if not provided)
- `--workspace-dir <dir>`: Workspace directory (default: `workspace`)
- `--json`: Output results as JSON
- `--verbose`: Verbose logging

**Features**:
- Returns `session_id` and `file_ids` for referencing in subsequent commands
- Supports single files or entire directories
- Auto-detects XML files when uploading directories

**Examples**:
```bash
# Upload single file
python -m cli.main upload samples/mapping1.xml

# Upload directory with session
python -m cli.main upload samples/ --recursive --session-id my-migration

# Upload with JSON output
python -m cli.main upload samples/ --recursive --json
```

**Output**: Returns session metadata including:
- `session_id`: Session identifier for referencing uploaded files
- `file_ids`: List of file identifiers
- `count`: Number of files uploaded
- `files`: List of uploaded filenames

#### Parse Files

Parse Informatica XML files into canonical models.

```bash
python -m cli.main parse [<type>] <target> [OPTIONS]
```

**Arguments**:
- `<target>`: File ID, file path, directory, or use `--session-id`
- `<type>`: Optional file type (`mapping`, `workflow`, `session`, `worklet`, `mapplet`, `all`)

**Options**:
- `--type <type>`: File type (auto-detected if not specified)
- `--session-id <id>`: Parse all files from an upload session
- `--enhance`: Enhance canonical models with AI after parsing
- `--recursive`: Recursively parse directory
- `--output <dir>`: Output directory for parsed models
- `--workspace-dir <dir>`: Workspace directory (default: `workspace`)
- `--json`: Output results as JSON
- `--verbose`: Verbose logging

**Features**:
- **Auto-detection**: Automatically detects file type if not specified
- **Session support**: Parse all files from an upload session
- **Multiple input methods**: Use `session_id`, `file_id`, `file_path`, or `directory`
- **AI enhancement**: Optional AI enhancement during parsing

**Examples**:
```bash
# Parse from session (auto-detect each file type)
python -m cli.main parse --session-id my-migration

# Parse directory (auto-detect all files)
python -m cli.main parse samples/ --recursive --enhance

# Parse specific file (auto-detect type)
python -m cli.main parse samples/mapping1.xml

# Parse with type specified
python -m cli.main parse mapping --session-id my-migration

# Parse directory with enhancement
python -m cli.main parse samples/ --recursive --enhance --json
```

**Output**: Returns parse results including:
- `canonical_model`: Parsed canonical model (for single file)
- `mapping_name`: Name of the mapping/transformation
- `file_type`: Detected or specified file type
- `parsed`: List of successfully parsed files (for batch operations)
- `failed`: List of failed files with errors (for batch operations)

#### Enhance Canonical Model

Enhance a canonical model with AI insights and improvements.

```bash
python -m cli.main enhance <mapping_name> [OPTIONS]
```

**Arguments**:
- `<mapping_name>`: Mapping name or ID to enhance

**Options**:
- `--output <dir>`: Output directory for enhanced models
- `--workspace-dir <dir>`: Workspace directory (default: `workspace`)
- `--json`: Output results as JSON
- `--verbose`: Verbose logging

**Features**:
- Uses AI agents to enhance canonical models
- Updates existing models in version store
- Adds semantic tags, complexity metrics, and improvements

**Examples**:
```bash
# Enhance a mapping
python -m cli.main enhance M_CUSTOMER_LOAD

# Enhance with JSON output
python -m cli.main enhance M_CUSTOMER_LOAD --json
```

**Output**: Returns enhancement results including:
- `mapping_name`: Name of the enhanced mapping
- `enhanced`: Boolean indicating if enhancement was applied
- `model`: Enhanced canonical model

#### Generate Code

Generate code from canonical models (PySpark, DLT, SQL, orchestration).

```bash
python -m cli.main generate-code <mapping_name> [OPTIONS]
```

**Arguments**:
- `<mapping_name>`: Mapping name or ID

**Options**:
- `--type <type>`: Code type - `pyspark`, `dlt`, `sql`, `orchestration`, or `all` (default: `pyspark`)
- `--output <dir>`: Output directory (default: `workspace/generated`)
- `--review`: Review generated code with AI after generation
- `--workspace-dir <dir>`: Workspace directory (default: `workspace`)
- `--json`: Output results as JSON
- `--verbose`: Verbose logging

**Features**:
- Generates code in multiple formats
- Optional AI review after generation
- Saves code metadata to Neo4j (if graph store enabled)
- Quality scoring and validation

**Examples**:
```bash
# Generate PySpark code
python -m cli.main generate-code M_CUSTOMER_LOAD

# Generate all code types
python -m cli.main generate-code M_CUSTOMER_LOAD --type all

# Generate with AI review
python -m cli.main generate-code M_CUSTOMER_LOAD --type pyspark --review

# Generate DLT code
python -m cli.main generate-code M_CUSTOMER_LOAD --type dlt
```

**Output**: Returns generation results including:
- Code type results (e.g., `pyspark`, `dlt`, `sql`)
- `file`: Path to generated code file
- `quality_score`: Code quality score
- `review`: AI review results (if `--review` was used)

#### Review Code

Review generated code with AI to identify issues and improvements.

```bash
python -m cli.main review <file_path> [OPTIONS]
```

**Arguments**:
- `<file_path>`: Path to code file to review

**Options**:
- `--fix`: Auto-fix issues found during review
- `--output <dir>`: Output directory for reviewed/fixed code
- `--workspace-dir <dir>`: Workspace directory (default: `workspace`)
- `--json`: Output results as JSON
- `--verbose`: Verbose logging

**Features**:
- AI-powered code review
- Identifies issues, improvements, and best practices
- Optional auto-fix capability
- Updates AI review status in Neo4j

**Examples**:
```bash
# Review code
python -m cli.main review workspace/generated/m_customer_load.py

# Review and fix
python -m cli.main review workspace/generated/m_customer_load.py --fix

# Review with JSON output
python -m cli.main review workspace/generated/m_customer_load.py --json
```

**Output**: Returns review results including:
- `file`: Path to reviewed file
- `review`: Review details with issues and score
- `fixed`: Boolean indicating if fixes were applied
- `fixed_file`: Path to fixed code file (if `--fix` was used)

#### Fix Code

Fix code issues identified during review.

```bash
python -m cli.main fix <file_path> [OPTIONS]
```

**Arguments**:
- `<file_path>`: Path to code file to fix

**Options**:
- `--output <path>`: Output path for fixed code (default: overwrites with `_fixed` suffix)
- `--workspace-dir <dir>`: Workspace directory (default: `workspace`)
- `--json`: Output results as JSON
- `--verbose`: Verbose logging

**Features**:
- Automatically fixes issues found in code review
- Uses AI agents to apply fixes
- Updates AI fix status in Neo4j

**Examples**:
```bash
# Fix code issues
python -m cli.main fix workspace/generated/m_customer_load.py

# Fix with custom output
python -m cli.main fix workspace/generated/m_customer_load.py --output fixed_code.py
```

**Output**: Returns fix results including:
- `file`: Path to original file
- `fixed`: Boolean indicating if fixes were applied
- `fixed_file`: Path to fixed code file

#### Cleanup (Optional)

Clean up workspace directories and Neo4j data. **⚠️ WARNING: This will delete data permanently!**

**Note**: Currently, cleanup is performed using the utility script. A native CLI cleanup command is planned for future releases.

**Using Utility Script** (Current Method):
```bash
python scripts/utils/cleanup.py [OPTIONS]
```

**Options**:
- `--workspace` or `--files`: Clean up workspace directory (removes uploaded, parsed, generated files)
- `--neo4j`: Delete all data from Neo4j graph database
- `--component <type>`: Delete specific component type from Neo4j (use with `--neo4j`)
  - Available types: `Transformation`, `ReusableTransformation`, `Pipeline`, `Task`, `GeneratedCode`, `Mapping`, `Workflow`, `Session`, `Worklet`, `Source`, `Target`, `Table`, `SourceFile`, `all`
- `--all`: Clean up everything (workspace + Neo4j)
- `--yes`: Skip confirmation prompt (use with caution!)

**⚠️ WARNING**: 
- Cleanup operations are **irreversible**
- Always backup important data before cleanup
- Use `--yes` flag only when you're certain you want to delete data
- Neo4j cleanup will remove all graph data including relationships

**Examples**:
```bash
# Clean workspace directory (with confirmation)
python scripts/utils/cleanup.py --workspace

# Clean Neo4j data (with confirmation)
python scripts/utils/cleanup.py --neo4j

# Clean specific component type from Neo4j
python scripts/utils/cleanup.py --neo4j --component Transformation

# Clean everything (with confirmation)
python scripts/utils/cleanup.py --all

# Clean everything without confirmation (⚠️ DANGEROUS)
python scripts/utils/cleanup.py --all --yes

# Clean workspace without confirmation
python scripts/utils/cleanup.py --workspace --yes
```

**What gets cleaned**:

**Workspace cleanup** (`--workspace` or `--files`):
- `workspace/staging/` - Uploaded XML files
- `workspace/parsed/` - Parsed canonical models
- `workspace/parse_ai/` - AI-enhanced models
- `workspace/generated/` - Generated code files
- `workspace/generated_ai/` - AI-reviewed code files
- `workspace/versions/` - Version store JSON files
- `workspace/diagrams/` - Generated diagrams
- `workspace/logs/` - Log files

**Neo4j cleanup** (`--neo4j`):
- All nodes and relationships in the graph database
- Component metadata
- Code metadata
- Lineage relationships
- Assessment data

**Component-specific cleanup** (`--component`):
- Only deletes nodes of the specified type and their relationships
- Available types: `Transformation`, `ReusableTransformation`, `Pipeline`, `Task`, `GeneratedCode`, `Mapping`, `Workflow`, `Session`, `Worklet`, `Source`, `Target`, `Table`, `SourceFile`, `all`

**Manual Cleanup** (Alternative):

If you prefer manual cleanup:

```bash
# Clean workspace directory manually
rm -rf workspace/staging workspace/parsed workspace/parse_ai workspace/generated workspace/generated_ai workspace/versions workspace/diagrams workspace/logs

# Clean Neo4j manually (using cypher-shell or Neo4j Browser)
# Run: MATCH (n) DETACH DELETE n
```

### Complete Migration Flow Example

```bash
# 1. Upload files
python -m cli.main upload samples/ --recursive --session-id migration-001

# 2. Parse all files from session (auto-detect types)
python -m cli.main parse --session-id migration-001 --enhance

# 3. Generate code for a mapping
python -m cli.main generate-code M_CUSTOMER_LOAD --type pyspark --review

# 4. Review generated code
python -m cli.main review workspace/generated/m_customer_load.py --fix

# 5. Assess repository
python -m cli.main assess profile
```

### Hybrid Mode Support

The CLI supports two modes:

**Direct Mode (default)**:
- Calls Python modules directly
- No HTTP overhead
- Works offline
- Uses workspace directory

**HTTP Mode (optional)**:
- Makes HTTP requests to API endpoints
- Requires API server running
- Enable with `--api-url` flag

**Examples**:
```bash
# Direct mode (default)
python -m cli.main upload samples/ --recursive

# HTTP mode
python -m cli.main --api-url http://localhost:8000 upload samples/ --recursive
```

### Session Management

The CLI uses session management to track uploaded files:

1. **Upload** returns `session_id` and `file_ids`
2. **Subsequent commands** can reference files using:
   - `--session-id`: Process all files from a session
   - `file_id`: Process a specific file
   - `file_path`: Process a file by path
   - `directory`: Process all files in a directory

**Example workflow**:
```bash
# Upload creates a session
python -m cli.main upload samples/ --recursive --session-id my-migration
# Output: {"session_id": "my-migration", "file_ids": [...], "count": 10}

# Parse all files from session
python -m cli.main parse --session-id my-migration

# Generate code for specific mapping
python -m cli.main generate-code M_CUSTOMER_LOAD
```

### Assessment Commands

#### Profile Repository

Analyze and profile the Informatica repository to gather statistics and metrics.

```bash
python -m cli.main assess profile
```

**Output**: JSON with repository statistics including:
- Component counts (mappings, workflows, sessions, etc.)
- Transformation types distribution
- Complexity metrics
- Dependency information

**Example**:
```bash
python -m cli.main assess profile
```

#### Analyze Components

Identify patterns, blockers, and estimate migration effort.

```bash
python -m cli.main assess analyze
```

**Output**: JSON with:
- Identified patterns (SCD types, aggregation patterns, etc.)
- Migration blockers
- Effort estimates per component

**Example**:
```bash
python -m cli.main assess analyze
```

#### Generate Migration Waves

Create a migration wave plan based on dependencies and complexity.

```bash
python -m cli.main assess waves [--max-wave-size N]
```

**Options**:
- `--max-wave-size`: Maximum components per wave (default: 10)

**Example**:
```bash
python -m cli.main assess waves --max-wave-size 15
```

#### Generate Assessment Report

Generate comprehensive assessment reports in various formats.

```bash
python -m cli.main assess report [--format FORMAT] [--output FILE]
```

**Options**:
- `--format`: Report format - `json`, `html`, or `summary` (default: `json`)
- `--output`: Output file path (optional, prints to stdout if not specified)

**Examples**:
```bash
# Generate JSON report
python -m cli.main assess report --format json --output assessment.json

# Generate HTML report
python -m cli.main assess report --format html --output assessment.html

# Generate summary report
python -m cli.main assess report --format summary
```

#### Calculate TCO and ROI

Calculate Total Cost of Ownership and Return on Investment.

```bash
python -m cli.main assess tco [OPTIONS]
```

**Options**:
- `--informatica-cost`: Annual Informatica cost (required)
- `--migration-cost`: One-time migration cost for ROI calculation (optional)
- `--runtime-hours`: Current runtime hours per day (optional)
- `--output`: Output file path (optional)

**Example**:
```bash
python -m cli.main assess tco \
  --informatica-cost 500000 \
  --migration-cost 200000 \
  --runtime-hours 8 \
  --output tco_analysis.json
```

### Reconciliation Commands

#### Reconcile Mapping

Compare source and target data for a mapping to validate migration.

```bash
python -m cli.main reconcile mapping --mapping-name NAME [OPTIONS]
```

**Required Options**:
- `--mapping-name`: Name of the mapping to reconcile

**Optional Options**:
- `--source-connection`: Source connection JSON or file path
- `--target-connection`: Target connection JSON or file path
- `--method`: Comparison method - `count`, `hash`, `threshold`, or `sampling` (default: `count`)
- `--output`: Output file path (optional)

**Example**:
```bash
python -m cli.main reconcile mapping \
  --mapping-name M_CUSTOMER_LOAD \
  --source-connection '{"type": "database", "host": "source-db", "database": "source_db"}' \
  --target-connection '{"type": "database", "host": "target-db", "database": "target_db"}' \
  --method hash \
  --output reconciliation_results.json
```

#### Reconcile Workflow

Compare source and target execution results for a workflow.

```bash
python -m cli.main reconcile workflow --workflow-name NAME [OPTIONS]
```

**Required Options**:
- `--workflow-name`: Name of the workflow to reconcile

**Optional Options**: Same as `reconcile mapping`

**Example**:
```bash
python -m cli.main reconcile workflow \
  --workflow-name WF_DAILY_LOAD \
  --method sampling \
  --output workflow_reconciliation.json
```

### Configuration Commands

#### Show Configuration

Display current configuration settings.

```bash
python -m cli.main config show
```

**Example**:
```bash
python -m cli.main config show
```

#### Validate Configuration

Validate configuration settings for correctness.

```bash
python -m cli.main config validate
```

**Example**:
```bash
python -m cli.main config validate
```

---

## Validation Scripts

### Validate Generated Code

Validates generated code files for syntax, structure, and completeness.

```bash
python scripts/validate_generated_code.py [OPTIONS]
```

**Options**:
- `--strict`: Treat warnings as errors
- `--verbose` or `-v`: Verbose output
- `--json`: Output results as JSON
- `--no-canonical`: Skip canonical model validation

**What it validates**:
- Code files exist for all mappings
- Code files are syntactically valid (Python/SQL)
- Code files have proper structure (imports, functions)
- Canonical model completeness (if enabled)

**Examples**:
```bash
# Basic validation
python scripts/validate_generated_code.py

# Strict validation with verbose output
python scripts/validate_generated_code.py --strict --verbose

# JSON output
python scripts/validate_generated_code.py --json > validation_results.json

# Skip canonical model validation
python scripts/validate_generated_code.py --no-canonical
```

**Output**: Summary report with:
- Total mappings and code files
- Valid/invalid files count
- Syntax errors, missing imports, missing functions
- Canonical model validation results (if enabled)

### Validate Canonical Models

Validates canonical model JSON files for completeness and correctness.

```bash
python scripts/validate_canonical_model.py [OPTIONS]
```

**Options**:
- `--path PATH`: Path to directory containing canonical model JSON files (default: checks `versions/`, `test_log/parsed/`, `test_log/parse_ai/`)
- `--strict`: Treat warnings as errors
- `--verbose` or `-v`: Verbose output
- `--json`: Output results as JSON

**What it validates**:
- Required fields are present
- Transformations are properly defined
- Connectors reference valid transformations
- Expression syntax is correct
- No circular dependencies
- No orphaned transformations

**Examples**:
```bash
# Validate models in default directories
python scripts/validate_canonical_model.py

# Validate models in specific directory
python scripts/validate_canonical_model.py --path versions/

# Strict validation
python scripts/validate_canonical_model.py --strict --verbose

# JSON output
python scripts/validate_canonical_model.py --json > canonical_validation.json
```

**Output**: Summary report with:
- Total models validated
- Invalid models count
- Transformation and connector statistics
- Circular dependencies detected
- Expression errors
- Detailed error and warning lists

### Validate Canonical Model Enhancements

Validates that canonical model enhancements are working correctly. Use the `--enhancements` flag with the main validation script.

```bash
python scripts/validate_canonical_model.py --enhancements
```

**What it validates**:
- Basic canonical model validation (structure, connectors, expressions, etc.)
- Field and Port nodes in Neo4j
- Field-level lineage
- Complexity metrics
- Semantic tags
- Structured runtime configuration
- Enhanced SCD structure
- Control task node types

**Example**:
```bash
# Basic validation only
python scripts/validate_canonical_model.py

# With enhancement validation
python scripts/validate_canonical_model.py --enhancements

# Verbose output with enhancements
python scripts/validate_canonical_model.py --enhancements --verbose
```

**Output**: Real-time validation status and summary report saved to `workspace/canonical_model_validation.json` (when using `--enhancements`)

---

## Test Flow Script

The test flow script provides step-by-step execution of the modernization pipeline.

```bash
python scripts/test_flow.py <command> [OPTIONS]
```

### Commands

#### Upload Files

Upload XML files to the system.

```bash
python scripts/test_flow.py upload --files "path/to/file1.xml path/to/file2.xml"
```

**Options**:
- `--files`: Space-separated list of file paths or glob patterns
- `--staging-dir`: Staging directory (default: `test_log/staging`)
- `--api-url`: API URL (default: `http://localhost:8000`)
- `--no-api`: Don't use API, use direct Python calls

**Example**:
```bash
python scripts/test_flow.py upload --files "samples/*.xml"
```

#### Parse Mappings

Parse uploaded XML files into structured models.

```bash
python scripts/test_flow.py parse
```

**Options**:
- `--staging-dir`: Staging directory (default: `test_log/staging`)
- `--parsed-dir`: Parsed models directory (default: `test_log/parsed`)
- `--api-url`: API URL (default: `http://localhost:8000`)
- `--no-api`: Don't use API

**Example**:
```bash
python scripts/test_flow.py parse
```

#### Enhance with AI

Enhance parsed models using AI agents.

```bash
python scripts/test_flow.py enhance
```

**Options**:
- `--parsed-dir`: Parsed models directory (default: `test_log/parsed`)
- `--output-dir`: Output directory (default: `test_log`)
- `--api-url`: API URL (default: `http://localhost:8000`)
- `--no-api`: Don't use API

**Example**:
```bash
python scripts/test_flow.py enhance
```

#### Generate Hierarchy

Generate component hierarchy visualization.

```bash
python scripts/test_flow.py hierarchy
```

**Options**:
- `--output-dir`: Output directory (default: `test_log`)

**Example**:
```bash
python scripts/test_flow.py hierarchy
```

#### Generate Lineage

Generate data lineage visualization.

```bash
python scripts/test_flow.py lineage
```

**Options**:
- `--output-dir`: Output directory (default: `test_log`)
- `--staging-dir`: Staging directory (default: `test_log/staging`)

**Example**:
```bash
python scripts/test_flow.py lineage
```

#### Generate Canonical Images

Generate canonical model visualization images.

```bash
python scripts/test_flow.py canonical
```

**Options**:
- `--output-dir`: Output directory (default: `test_log`)

**Example**:
```bash
python scripts/test_flow.py canonical
```

#### Generate Code

Generate PySpark/DLT/SQL code from canonical models.

```bash
python scripts/test_flow.py code
```

**Options**:
- `--output-dir`: Output directory (default: `test_log`)
- `--generated-dir`: Generated code directory (default: `test_log/generated`)

**Example**:
```bash
python scripts/test_flow.py code
```

#### Review Code

Review and fix generated code using AI.

```bash
python scripts/test_flow.py review
```

**Options**:
- `--generated-dir`: Generated code directory (default: `test_log/generated`)
- `--output-dir`: Output directory (default: `test_log`)

**Example**:
```bash
python scripts/test_flow.py review
```

#### Assess

Run assessment after parsing.

```bash
python scripts/test_flow.py assess
```

**Example**:
```bash
python scripts/test_flow.py assess
```

### Complete Workflow Example

```bash
# Step 1: Upload files
python scripts/test_flow.py upload --files "samples/mapping1.xml samples/mapping2.xml"

# Step 2: Parse mappings
python scripts/test_flow.py parse

# Step 3: Enhance with AI
python scripts/test_flow.py enhance

# Step 4: Generate code
python scripts/test_flow.py code

# Step 5: Review code
python scripts/test_flow.py review

# Step 6: Validate
python scripts/validate_generated_code.py --strict
```

---

## Utility Scripts

### Cleanup Utility

Clean up Neo4j data, uploaded files, version store, and assessment reports.

```bash
python scripts/utils/cleanup.py [OPTIONS]
```

**Options**:
- `--neo4j`: Clean up Neo4j graph database
- `--component TYPE`: Clean up specific component type from Neo4j (use with `--neo4j`)
  - Available types: `Mapping`, `Workflow`, `Session`, `Worklet`, `Transformation`, `Source`, `Target`, `Table`, `SourceFile`, `GeneratedCode`
- `--files` or `--uploads`: Clean up uploaded XML files
- `--version-store`: Clean up version store JSON files
- `--assessment`: Clean up assessment report files
- `--all`: Clean up everything
- `--yes`: Skip confirmation prompt

**Examples**:
```bash
# Clean up everything (with confirmation)
python scripts/utils/cleanup.py --all

# Clean up everything (skip confirmation)
python scripts/utils/cleanup.py --all --yes

# Clean up only Neo4j
python scripts/utils/cleanup.py --neo4j --yes

# Clean up only mappings from Neo4j
python scripts/utils/cleanup.py --neo4j --component Mapping --yes

# Clean up only uploaded files
python scripts/utils/cleanup.py --files --yes
```

### Sync Generated to AI

Sync generated code files to AI-reviewed directory.

```bash
python scripts/sync_generated_to_ai.py [OPTIONS]
```

**Options**:
- `--source-dir`: Source directory (default: `test_log/generated`)
- `--target-dir`: Target directory (default: `test_log/generated_ai`)
- `--dry-run`: Show what would be synced without actually syncing

**Example**:
```bash
python scripts/sync_generated_to_ai.py --dry-run
```

### Check Neo4j

Simple Neo4j connection and data check.

```bash
python scripts/utils/check_neo4j_simple.py
```

**Example**:
```bash
python scripts/utils/check_neo4j_simple.py
```

### Diagnose Neo4j

Comprehensive Neo4j diagnostics.

```bash
python scripts/utils/diagnose_neo4j.py
```

**Example**:
```bash
python scripts/utils/diagnose_neo4j.py
```

### Check Neo4j Data

Check Neo4j data counts and structure.

```bash
python scripts/utils/check_neo4j_data.py
```

**Example**:
```bash
python scripts/utils/check_neo4j_data.py
```

### Migrate to Graph

Migrate canonical models from JSON to Neo4j graph.

```bash
python scripts/utils/migrate_to_graph.py [OPTIONS]
```

**Options**:
- `--source-dir`: Source directory with JSON files (default: `versions/`)
- `--dry-run`: Show what would be migrated without actually migrating

**Example**:
```bash
python scripts/utils/migrate_to_graph.py --dry-run
```

### Validate Graph Migration

Validate that graph migration was successful.

```bash
python scripts/utils/validate_graph_migration.py
```

**Example**:
```bash
python scripts/utils/validate_graph_migration.py
```

### Generate Diff

Generate diff between two versions or directories.

```bash
python scripts/utils/generate_diff.py [OPTIONS]
```

**Example**:
```bash
python scripts/utils/generate_diff.py --old-dir old_versions/ --new-dir versions/
```

### Reorganize Project

Reorganize project structure (development tool).

```bash
python scripts/utils/reorganize_project.py [OPTIONS]
```

**Example**:
```bash
python scripts/utils/reorganize_project.py --dry-run
```

---

## Setup Scripts

### Setup Neo4j

Set up Neo4j database using Docker.

```bash
./scripts/setup/setup_neo4j.sh
```

**What it does**:
- Checks if Docker/Colima is running
- Removes existing Neo4j container (if any)
- Creates and starts a new Neo4j container
- Sets default password
- Waits for Neo4j to be ready

**Example**:
```bash
./scripts/setup/setup_neo4j.sh
```

**Note**: Make sure Docker or Colima is running before executing this script.

### Setup Environment

Set up Python environment and install dependencies.

```bash
./scripts/setup/setup_env.sh
```

**What it does**:
- Creates virtual environment (if not exists)
- Activates virtual environment
- Installs dependencies from `requirements.txt`

**Example**:
```bash
./scripts/setup/setup_env.sh
```

### Create Neo4j Schema

Create Neo4j schema and indexes.

```bash
python scripts/schema/create_neo4j_schema.py
```

**Example**:
```bash
python scripts/schema/create_neo4j_schema.py
```

---

## Environment Configuration

### Environment Variables

Most CLI tools use environment variables for configuration. Set these in your `.env` file or export them:

```bash
# Neo4j Configuration
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=password

# Graph Store Configuration
export ENABLE_GRAPH_STORE=true
export GRAPH_FIRST=false

# LLM Configuration
export LLM_PROVIDER=local  # or 'openai', 'azure'
export OPENAI_API_KEY=your_key_here  # if using OpenAI
export AZURE_OPENAI_KEY=your_key_here  # if using Azure OpenAI
export OLLAMA_URL=http://localhost:11434  # if using local LLM
export OLLAMA_MODEL=llama3  # if using local LLM
export USE_MOCK_LLM=false  # for testing

# Version Store Configuration
export VERSION_STORE_PATH=./versions
```

### Configuration File

The main CLI tool can use a configuration file:

```bash
python -m cli.main --config config.yaml assess profile
```

Configuration file format (YAML or JSON):

```yaml
neo4j:
  uri: bolt://localhost:7687
  user: neo4j
  password: password

graph_store:
  enabled: true
  graph_first: false

llm:
  provider: local
  model: llama3

version_store:
  path: ./versions
```

---

## Common Workflows

### Complete Modernization Workflow

**Using CLI (Recommended)**:
```bash
# 1. Setup environment
./scripts/setup/setup_neo4j.sh
python scripts/schema/create_neo4j_schema.py

# Optional: Clean up previous runs (⚠️ WARNING: Deletes data!)
# python scripts/utils/cleanup.py --all --yes

# 2. Upload and parse files
python -m cli.main upload samples/ --recursive --session-id migration-001
python -m cli.main parse --session-id migration-001 --enhance

# 3. Generate code
python -m cli.main generate-code M_CUSTOMER_LOAD --type pyspark --review

# 4. Review and fix code
python -m cli.main review workspace/generated/m_customer_load.py --fix

# 5. Validate everything
python scripts/validate_canonical_model.py --strict
python scripts/validate_generated_code.py --strict

# 6. Run assessment
python -m cli.main assess profile
python -m cli.main assess analyze
python -m cli.main assess report --format html --output assessment.html

# Optional: Clean up after completion (⚠️ WARNING: Deletes data!)
# python scripts/utils/cleanup.py --workspace --yes  # Clean workspace only
# python scripts/utils/cleanup.py --neo4j --yes      # Clean Neo4j only
# python scripts/utils/cleanup.py --all --yes        # Clean everything
```

**Using Test Flow Script (Alternative)**:
```bash
# 1. Setup environment
./scripts/setup/setup_neo4j.sh
python scripts/schema/create_neo4j_schema.py

# 2. Upload and parse files
python scripts/test_flow.py upload --files "samples/*.xml"
python scripts/test_flow.py parse

# 3. Enhance with AI
python scripts/test_flow.py enhance

# 4. Generate code
python scripts/test_flow.py code

# 5. Review and fix code
python scripts/test_flow.py review

# 6. Validate everything
python scripts/validate_canonical_model.py --strict
python scripts/validate_generated_code.py --strict

# 7. Run assessment
python -m cli.main assess profile
python -m cli.main assess analyze
python -m cli.main assess report --format html --output assessment.html
```

### Validation Workflow

```bash
# Validate canonical models
python scripts/validate_canonical_model.py --strict --verbose

# Validate generated code
python scripts/validate_generated_code.py --strict --verbose

# Validate canonical model enhancements
python scripts/validate_canonical_model.py --enhancements
```

### Assessment Workflow

```bash
# Profile repository
python -m cli.main assess profile

# Analyze components
python -m cli.main assess analyze

# Generate migration waves
python -m cli.main assess waves --max-wave-size 15

# Generate report
python -m cli.main assess report --format html --output assessment.html

# Calculate TCO
python -m cli.main assess tco \
  --informatica-cost 500000 \
  --migration-cost 200000 \
  --output tco_analysis.json
```

### Cleanup Workflow

**Using CLI (Recommended)**:
```bash
# Clean up workspace directory (with confirmation)
python -m cli.main cleanup --workspace

# Clean up Neo4j data (with confirmation)
python -m cli.main cleanup --neo4j

# Clean up specific component type from Neo4j
python -m cli.main cleanup --neo4j --neo4j-component Transformation

# Clean up everything (with confirmation)
python -m cli.main cleanup --all

# Clean up everything without confirmation (⚠️ DANGEROUS)
python -m cli.main cleanup --all --yes
```

**Using Utility Script (Alternative)**:
```bash
# Clean up everything
python scripts/utils/cleanup.py --all --yes

# Clean up only Neo4j mappings
python scripts/utils/cleanup.py --neo4j --component Mapping --yes

# Clean up only uploaded files
python scripts/utils/cleanup.py --files --yes
```

---

## Troubleshooting

### Common Issues

1. **Neo4j Connection Error**
   - Check if Neo4j is running: `docker ps | grep neo4j`
   - Verify connection settings in `.env` file
   - Run: `python scripts/utils/check_neo4j_simple.py`

2. **Import Errors**
   - Make sure you're running from project root
   - Check PYTHONPATH: `export PYTHONPATH="${PYTHONPATH}:$(pwd):$(pwd)/src"`
   - Verify dependencies: `pip install -r requirements.txt`

3. **Configuration Errors**
   - Validate configuration: `python -m cli.main config validate`
   - Check `.env` file exists and has correct values
   - Verify environment variables are exported

4. **Graph Store Not Enabled**
   - Set `ENABLE_GRAPH_STORE=true` in `.env`
   - Restart API server if running

### Getting Help

- Check script help: `python <script> --help`
- Check main CLI help: `python -m cli.main --help`
- Review logs in `test_log/` directory
- Check documentation in `docs/` directory

---

## Best Practices

1. **Always validate before proceeding**: Run validation scripts after each major step
2. **Use dry-run options**: Test scripts with `--dry-run` before actual execution
3. **Keep backups**: Backup Neo4j and version store before cleanup operations
4. **Use version control**: Commit canonical models and generated code to version control
5. **Monitor logs**: Check logs in `test_log/` directory for detailed information
6. **Test incrementally**: Test with small datasets before processing large repositories
7. **Use strict mode**: Use `--strict` flag for validation in production environments

---

## Quick Reference

### Main CLI Commands

```bash
# Migration Flow
python -m cli.main upload samples/ --recursive --session-id migration-001
python -m cli.main parse --session-id migration-001 --enhance
python -m cli.main enhance M_CUSTOMER_LOAD
python -m cli.main generate-code M_CUSTOMER_LOAD --type pyspark --review
python -m cli.main review workspace/generated/m_customer_load.py --fix
python -m cli.main fix workspace/generated/m_customer_load.py

# Cleanup (⚠️ WARNING: Deletes data! - Uses utility script)
python scripts/utils/cleanup.py --workspace          # Clean workspace only
python scripts/utils/cleanup.py --neo4j              # Clean Neo4j only
python scripts/utils/cleanup.py --all                # Clean everything
python scripts/utils/cleanup.py --neo4j --component Transformation  # Clean specific component

# Assessment
python -m cli.main assess profile
python -m cli.main assess analyze
python -m cli.main assess waves --max-wave-size 15
python -m cli.main assess report --format html --output report.html
python -m cli.main assess tco --informatica-cost 500000 --migration-cost 200000

# Reconciliation
python -m cli.main reconcile mapping --mapping-name M_NAME --method hash
python -m cli.main reconcile workflow --workflow-name WF_NAME --method count

# Configuration
python -m cli.main config show
python -m cli.main config validate
```

### Validation Commands

```bash
# Validate generated code
python scripts/validate_generated_code.py --strict --verbose

# Validate canonical models
python scripts/validate_canonical_model.py --path versions/ --strict

# Validate enhancements
python scripts/validate_canonical_model.py --enhancements
```

### Test Flow Commands

```bash
# Complete workflow
python scripts/test_flow.py upload --files "samples/*.xml"
python scripts/test_flow.py parse
python scripts/test_flow.py enhance
python scripts/test_flow.py code
python scripts/test_flow.py review
```

### Utility Commands

```bash
# Cleanup
python scripts/utils/cleanup.py --all --yes

# Check Neo4j
python scripts/utils/check_neo4j_simple.py
python scripts/utils/diagnose_neo4j.py

# Migrate to graph
python scripts/utils/migrate_to_graph.py --dry-run
```

---

## Additional Resources

- [API Documentation](http://localhost:8000/docs) - When API server is running
- [Architecture Documentation](../architecture/system_architecture.md)
- [System Architecture](../architecture/system_architecture.md)
- [Graph Explorer Guide](../graph_explorer_guide.md)

