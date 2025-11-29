# Customer Orders ETL - Complex Sample Files

## Overview

This directory contains a complete, complex Informatica ETL pipeline for Customer Orders processing, demonstrating:

- **1 Workflow** with **4 Worklets**
- **Each Worklet** with **multiple Sessions**
- **Each Session** with **multiple Transformations**
- **Complete data flow**: Ingestion → Staging → Standardization → Dimensional Layer

## Architecture

```
WF_CUSTOMER_ORDERS_ETL (Workflow)
│
├── WK_INGEST_FROM_ORACLE (Worklet 1: Ingestion)
│   ├── S_M_INGEST_CUSTOMERS (Session)
│   │   └── M_INGEST_CUSTOMERS (Mapping)
│   │       ├── SQ_CUSTOMERS (SourceQualifier)
│   │       ├── EXP_ADD_METADATA (Expression)
│   │       └── STG_CUSTOMERS (Target)
│   ├── S_M_INGEST_ORDERS (Session)
│   ├── S_M_INGEST_PRODUCTS (Session)
│   ├── S_M_INGEST_PAYMENTS (Session)
│   └── S_M_INGEST_SHIPPING (Session)
│
├── WK_STAGE_DATA (Worklet 2: Staging)
│   ├── S_M_STAGE_CUSTOMERS (Session)
│   │   └── M_STAGE_CUSTOMERS (Mapping)
│   │       ├── SQ_STG_CUSTOMERS (SourceQualifier)
│   │       ├── EXP_VALIDATE (Expression)
│   │       ├── RTR_DATA_QUALITY (Router)
│   │       ├── UPD_STRATEGY (UpdateStrategy)
│   │       ├── STAGE_CUSTOMERS (Target)
│   │       └── REJECT_CUSTOMERS (Target)
│   ├── S_M_STAGE_ORDERS (Session)
│   │   └── M_STAGE_ORDERS (Mapping)
│   │       ├── SQ_ORDERS, SQ_ORDER_ITEMS (SourceQualifiers)
│   │       ├── JNR_ORDERS_ITEMS (Joiner)
│   │       ├── EXP_CALC_TOTALS (Expression)
│   │       ├── AGG_ORDER_SUMMARY (Aggregator)
│   │       ├── LK_CUSTOMER (Lookup)
│   │       ├── RTR_BY_STATUS (Router)
│   │       ├── FLT_COMPLETED (Filter)
│   │       └── STAGE_ORDERS (Target)
│   ├── S_M_STAGE_PRODUCTS (Session)
│   ├── S_M_STAGE_PAYMENTS (Session)
│   └── S_M_STAGE_SHIPPING (Session)
│
├── WK_STANDARDIZE_DATA (Worklet 3: Standardization)
│   ├── S_M_STD_CUSTOMER_DATA (Session)
│   │   └── M_STD_CUSTOMER_DATA (Mapping)
│   │       ├── SQ_STAGE_CUSTOMERS (SourceQualifier)
│   │       ├── LK_REGION (Lookup)
│   │       ├── EXP_ENRICH (Expression)
│   │       ├── JNR_CUSTOMER_HISTORY (Joiner)
│   │       ├── AGG_DEDUPE (Aggregator)
│   │       ├── RNK_LATEST (Rank)
│   │       ├── SRT_BY_KEY (Sorter)
│   │       └── STD_CUSTOMERS (Target)
│   ├── S_M_STD_ORDER_DATA (Session)
│   ├── S_M_STD_PRODUCT_DATA (Session)
│   └── S_M_DQ_VALIDATION (Session)
│
└── WK_LOAD_DIMENSIONS (Worklet 4: Dimensional Layer)
    ├── S_M_LOAD_CUSTOMER_DIM (Session)
    │   └── M_LOAD_CUSTOMER_DIM (Mapping)
    │       ├── SQ_STD_CUSTOMERS (SourceQualifier)
    │       ├── LK_DIM_CUSTOMER (Lookup)
    │       ├── EXP_SCD_LOGIC (Expression)
    │       ├── RTR_SCD_OPERATIONS (Router)
    │       ├── EXP_EXPIRE_OLD (Expression)
    │       ├── UPD_NEW_RECORDS (UpdateStrategy)
    │       ├── UPD_EXPIRE_OLD (UpdateStrategy)
    │       └── DIM_CUSTOMER (Target)
    ├── S_M_LOAD_PRODUCT_DIM (Session)
    ├── S_M_LOAD_DATE_DIM (Session)
    ├── S_M_LOAD_REGION_DIM (Session)
    └── S_M_LOAD_ORDER_FACT (Session)
        └── M_LOAD_ORDER_FACT (Mapping)
            ├── SQ_STD_ORDERS (SourceQualifier)
            ├── LK_CUSTOMER_DIM (Lookup)
            ├── LK_PRODUCT_DIM (Lookup)
            ├── LK_DATE_DIM (Lookup)
            ├── LK_REGION_DIM (Lookup)
            ├── EXP_FACT_MEASURES (Expression)
            ├── JNR_DIMENSIONS (Joiner)
            ├── AGG_FACT_AGGREGATION (Aggregator)
            ├── UPD_STRATEGY (UpdateStrategy)
            └── FACT_ORDERS (Target)
```

## Files Included

### Workflow
- `workflow_customer_orders.xml` - Main workflow with 4 worklets

### Worklets
- `worklet_ingestion.xml` - Ingestion worklet (5 sessions)
- `worklet_staging.xml` - Staging worklet (5 sessions with dependencies)
- `worklet_standardization.xml` - Standardization worklet (4 sessions)
- `worklet_dimensions.xml` - Dimensional worklet (5 sessions)

### Sessions
- `session_ingest_customers.xml` - Customer ingestion session

### Mappings (with complex transformations)
- `mapping_ingest_customers.xml` - Simple ingestion (SourceQualifier → Expression → Target)
- `mapping_stage_customers.xml` - Staging with validation (SourceQualifier → Expression → Router → UpdateStrategy → Targets)
- `mapping_std_customer_data.xml` - Standardization with enrichment (SourceQualifier → Lookup → Expression → Joiner → Aggregator → Rank → Sorter → Target)
- `mapping_stage_orders.xml` - Complex staging with joins (Multiple SourceQualifiers → Joiner → Expression → Aggregator → Lookup → Router → Filter → Target)
- `mapping_load_customer_dim.xml` - SCD Type 2 dimension load (SourceQualifier → Lookup → Expression → Router → UpdateStrategy → Target)
- `mapping_load_order_fact.xml` - Fact table with multiple dimension lookups (SourceQualifier → Multiple Lookups → Expression → Joiner → Aggregator → UpdateStrategy → Target)

## Transformation Types Covered

1. **SourceQualifier** - SQL-based source extraction
2. **Expression** - Business logic and calculations
3. **Filter** - Record filtering
4. **Router** - Conditional routing to multiple outputs
5. **Joiner** - Join multiple sources
6. **Lookup** - Reference data lookups
7. **Aggregator** - Aggregations and grouping
8. **Rank** - Ranking and top-N selection
9. **Sorter** - Data sorting
10. **UpdateStrategy** - Insert/Update/Delete handling
11. **Union** - (can be added)
12. **Sequence Generator** - (can be added)

## Data Flow Layers

### Layer 1: Ingestion (Oracle DB → Staging)
- Extract from Oracle source database
- Add ingestion metadata
- Load to initial staging tables

### Layer 2: Staging
- Data validation and quality checks
- Basic transformations
- Reject handling
- Referential integrity checks

### Layer 3: Standardization
- Data enrichment
- Business rule application
- Deduplication
- Data quality validation

### Layer 4: Dimensional Layer
- SCD Type 2 dimension loads
- Fact table loads with dimension lookups
- Historical tracking

## Usage

1. Upload all files using the File Browser (directory upload)
2. View the hierarchy in the Hierarchy tab
3. Parse mappings to see transformations
4. Generate code for Databricks
5. Visualize the complete flow in Graph Explorer

## Next Steps

To complete the sample set, you can add:
- More session files for other entities (orders, products, payments, shipping)
- More mapping files with additional transformation patterns
- More complex join scenarios
- Union transformations
- Sequence generators
- More SCD patterns

