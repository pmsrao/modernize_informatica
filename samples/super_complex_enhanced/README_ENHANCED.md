# Enhanced Super Complex Sample - New Components

## Overview

This directory contains an **enhanced version** of the super_complex sample that demonstrates all newly added Informatica components:

- **Mapplets** (reusable transformation sets)
- **Mapplet Instances** (using mapplets in mappings)
- **Reusable Transformations** (transformations marked as reusable)
- **Custom Transformations** (flagged for manual intervention)
- **Stored Procedures** (flagged for manual intervention)
- **New Workflow Task Types** (Command, Email, Timer, Decision, Event, Assignment, Control)

## Architecture

```
WF_ENHANCED_ETL_PIPELINE (Workflow)
│
├── Pre-Processing Phase
│   ├── CMD_CLEANUP_TEMP (Command Task)
│   ├── TIMER_WAIT_SOURCE (Timer Task - File Wait)
│   └── ASSIGN_VARIABLES (Assignment Task)
│
├── Data Ingestion Phase
│   ├── S_M_STAGE_CUSTOMERS_ENHANCED (Session)
│   │   └── M_STAGE_CUSTOMERS_ENHANCED (Mapping)
│   │       ├── MPL_CLEANSE_INST (Mapplet Instance)
│   │       ├── EXP_CUSTOMER_ENRICH (Reusable Expression)
│   │       ├── CUSTOM_FRAUD_CHECK (Custom Transformation)
│   │       └── SP_GET_CREDIT_SCORE (Stored Procedure)
│   ├── S_M_PROCESS_ORDERS_ENHANCED (Session)
│   │   └── M_PROCESS_ORDERS_ENHANCED (Mapping)
│   │       ├── MPL_TOTALS_INST (Mapplet Instance)
│   │       └── LK_PRODUCT_INFO (Reusable Lookup)
│   └── EVT_INGESTION_COMPLETE (Event-Raise Task)
│
├── Data Validation Phase
│   ├── DEC_DATA_QUALITY_CHECK (Decision Task)
│   └── EMAIL_LOW_QUALITY (Email Task)
│
├── Processing Phase
│   ├── EVT_WAIT_VALIDATION (Event-Wait Task)
│   ├── S_M_LOAD_DIMENSIONS (Session)
│   └── S_M_LOAD_FACTS (Session)
│
└── Post-Processing Phase
    ├── CMD_ARCHIVE_FILES (Command Task)
    ├── EMAIL_COMPLETION (Email Task)
    └── CTRL_STOP_ON_ERROR (Control Task)
```

## Files Included

### Mapplets (Reusable Transformation Sets)

1. **`mapplet_data_cleansing.xml`** - `MPL_DATA_CLEANSING`
   - Cleanses addresses, phones, emails, zip codes
   - Contains 4 Expression transformations
   - Used in customer staging mappings

2. **`mapplet_calculate_totals.xml`** - `MPL_CALCULATE_TOTALS`
   - Calculates order line totals, discounts, tax, grand total
   - Contains 2 Expression transformations
   - Used in order processing mappings

### Mappings with New Components

1. **`mapping_stage_customers_enhanced.xml`** - `M_STAGE_CUSTOMERS_ENHANCED`
   - **Mapplet Instance**: `MPL_CLEANSE_INST` (uses `MPL_DATA_CLEANSING`)
   - **Reusable Transformation**: `EXP_CUSTOMER_ENRICH` (marked as reusable)
   - **Custom Transformation**: `CUSTOM_FRAUD_CHECK` (Java-based, requires manual intervention)
   - **Stored Procedure**: `SP_GET_CREDIT_SCORE` (requires manual intervention)
   - Demonstrates: Mapplet usage, reusable transformations, manual intervention flags

2. **`mapping_process_orders_enhanced.xml`** - `M_PROCESS_ORDERS_ENHANCED`
   - **Mapplet Instance**: `MPL_TOTALS_INST` (uses `MPL_CALCULATE_TOTALS`)
   - **Reusable Lookup**: `LK_PRODUCT_INFO` (marked as reusable)
   - Demonstrates: Mapplet usage in order processing, reusable lookups

### Workflow with New Task Types

**`workflow_enhanced_etl.xml`** - `WF_ENHANCED_ETL_PIPELINE`

Contains all new workflow task types:

1. **Command Tasks**:
   - `CMD_CLEANUP_TEMP` - Cleanup temporary files
   - `CMD_ARCHIVE_FILES` - Archive processed files

2. **Timer Task**:
   - `TIMER_WAIT_SOURCE` - Wait for source system ready flag file

3. **Assignment Task**:
   - `ASSIGN_VARIABLES` - Set workflow variables (RUN_DATE, BATCH_ID, SOURCE_SYSTEM)

4. **Event Tasks**:
   - `EVT_INGESTION_COMPLETE` - Event-Raise (signal ingestion completion)
   - `EVT_WAIT_VALIDATION` - Event-Wait (wait for validation event)

5. **Decision Task**:
   - `DEC_DATA_QUALITY_CHECK` - Conditional branching based on data quality score

6. **Email Tasks**:
   - `EMAIL_LOW_QUALITY` - Send alert on low data quality
   - `EMAIL_COMPLETION` - Send completion notification

7. **Control Task**:
   - `CTRL_STOP_ON_ERROR` - Stop workflow on critical errors

### Sessions

1. **`session_stage_customers_enhanced.xml`** - Session for enhanced customer staging
2. **`session_process_orders_enhanced.xml`** - Session for enhanced order processing

## New Component Types Demonstrated

### 1. Mapplets

**Purpose**: Reusable sets of transformations that can be embedded into multiple mappings.

**Example**: `MPL_DATA_CLEANSING`
- Input ports: RAW_ADDRESS, RAW_PHONE, RAW_EMAIL, RAW_ZIP_CODE
- Internal transformations: 4 Expression transformations for cleansing
- Output ports: Cleaned data fields with validation flags

**Usage**: Mapplet instances are referenced in mappings using `TYPE="Mapplet"` and `MAPPLETNAME` attribute.

### 2. Reusable Transformations

**Purpose**: Transformations marked as reusable can be defined once and reused across mappings.

**Example**: `EXP_CUSTOMER_ENRICH`
- Marked with `REUSABLE="YES"` and `REUSABLENAME="EXP_CUSTOMER_ENRICH"`
- Contains customer enrichment logic (full name, customer type, segment)
- Can be referenced in multiple mappings

**Example**: `LK_PRODUCT_INFO`
- Reusable lookup transformation
- Can be used in multiple order processing mappings

### 3. Custom Transformations

**Purpose**: User-defined transformations (often Java-based) that require manual re-implementation.

**Example**: `CUSTOM_FRAUD_CHECK`
- Type: `Custom Transformation`
- Custom Code: `com.company.fraud.FraudDetectionEngine`
- **Flagged for Manual Intervention**: Requires re-implementation in PySpark

### 4. Stored Procedures

**Purpose**: Database stored procedures called from Informatica mappings.

**Example**: `SP_GET_CREDIT_SCORE`
- Type: `Stored Procedure`
- Procedure Name: `GET_CUSTOMER_CREDIT_SCORE`
- Connection: `CREDIT_DB_CONNECTION`
- **Flagged for Manual Intervention**: May need database-specific handling

### 5. New Workflow Task Types

#### Command Tasks
- Execute shell commands or scripts
- Properties: `command`, `working_directory`, `success_codes`, `failure_codes`, `timeout`

#### Timer Tasks
- Wait for duration, file, or event
- Properties: `wait_type` (Duration/File/Event), `wait_value`, `file_path`, `event_name`

#### Assignment Tasks
- Set workflow variables
- Properties: `assignments` (list of variable assignments)

#### Event Tasks
- **Event-Raise**: Signal an event
- **Event-Wait**: Wait for an event
- Properties: `event_type` (RAISE/WAIT), `event_name`, `wait_timeout`

#### Decision Tasks
- Conditional branching based on conditions
- Properties: `condition`, `branches` (list of branches), `default_branch`

#### Email Tasks
- Send email notifications
- Properties: `recipients`, `subject`, `body`, `attachments`, `mail_server`

#### Control Tasks
- Control workflow execution (Abort/Stop)
- Properties: `control_type` (ABORT/STOP), `error_message`

## Usage

1. **Upload Files**: Upload all files using the File Browser
   - Mapplets first (they are referenced by mappings)
   - Mappings
   - Sessions
   - Workflow

2. **Parse Components**: Parse in this order:
   - Mapplets
   - Mappings (will resolve mapplet references)
   - Sessions
   - Workflow

3. **View in Graph**: Use Graph Explorer to see:
   - Mapplet nodes and their internal transformations
   - Mapplet instances in mappings (USES_MAPPLET relationships)
   - Reusable transformations
   - Custom transformations and stored procedures (flagged for manual intervention)
   - All workflow task types

4. **Generate Code**: Generate code to see:
   - Mapplet inlining in generated code
   - Reusable transformation functions
   - Manual intervention placeholders for custom transformations and stored procedures
   - All workflow task types converted to appropriate Airflow operators

## Key Features Demonstrated

### Mapplet Inlining
- Mapplets are inlined into generated code (transformations embedded directly)
- Input/output port mappings are handled correctly

### Reusable Transformations
- Reusable transformations are generated as functions
- Subsequent uses call the function instead of generating inline code

### Manual Intervention Flags
- Custom transformations and stored procedures are clearly flagged
- Generated code includes TODO comments and placeholders
- Assessment reports identify these as migration blockers

### Workflow Task Types
- All task types are parsed with their specific properties
- Generated Airflow DAG includes appropriate operators:
  - Command → BashOperator
  - Email → EmailOperator
  - Timer → FileSensor/PythonSensor/PythonOperator
  - Decision → BranchPythonOperator (placeholder)
  - Event → PythonSensor (wait) / PythonOperator (raise)
  - Assignment → PythonOperator with XCom
  - Control → PythonOperator (abort) / EmptyOperator (stop)

## Testing Scenarios

1. **Mapplet Parsing**: Verify mapplets are parsed correctly with ports and transformations
2. **Mapplet Resolution**: Verify mapplet instances resolve to their mapplet definitions
3. **Reusable Transformation Detection**: Verify reusable transformations are detected and tracked
4. **Manual Intervention Flags**: Verify custom transformations and stored procedures are flagged
5. **Workflow Task Parsing**: Verify all new task types are parsed with their properties
6. **Code Generation**: Verify mapplet inlining, reusable function generation, and manual intervention placeholders
7. **Graph Storage**: Verify all components are stored in Neo4j with correct relationships

## Next Steps

To extend this sample:
- Add more mapplets for different business domains
- Add more reusable transformations
- Add more complex custom transformation scenarios
- Add more stored procedure examples
- Add more workflow task type combinations
- Add nested worklets with new task types

