# Informatica to Databricks Mapping Guide

## Table of Contents

1. [Informatica Component Hierarchy](#informatica-component-hierarchy)
2. [Component Details](#component-details)
3. [Databricks Equivalents](#databricks-equivalents)
4. [Mapping Strategy](#mapping-strategy)
5. [Code Examples](#code-examples)
6. [Migration Patterns](#migration-patterns)

---

## Informatica Component Hierarchy

### Overview

Informatica PowerCenter uses a hierarchical structure to organize ETL logic:

```
Workflow (Top Level)
    ├── Worklet (Reusable Workflow Component)
    │   ├── Session (Execution Instance)
    │   │   └── Mapping (Data Transformation Logic)
    │   │       ├── Sources (Input Tables/Files)
    │   │       ├── Transformations (Business Logic)
    │   │       └── Targets (Output Tables/Files)
    │   └── Session
    │       └── Mapping
    └── Session
        └── Mapping
```

### Hierarchy Levels

#### 1. **Workflow** (Top Level)
- **Purpose**: Orchestrates the execution of multiple sessions and worklets
- **Responsibilities**:
  - Defines execution order and dependencies
  - Manages scheduling and triggers
  - Handles error handling and recovery
  - Controls parallel vs. sequential execution
- **XML Structure**: Contains `TASKINSTANCE` elements (sessions/worklets) and `CONNECTOR` elements (dependencies)

**Example Workflow XML:**
```xml
<WORKFLOW NAME="WF_CUSTOMER_DAILY">
  <TASKINSTANCE NAME="S_M_LOAD_CUSTOMER" TASKTYPE="Session"/>
  <TASKINSTANCE NAME="WK_DIM_BUILD" TASKTYPE="Worklet" WORKLETNAME="WK_BUILD_DIMS"/>
  <TASKINSTANCE NAME="S_M_LOAD_FACT" TASKTYPE="Session"/>

  <CONNECTOR FROMINSTANCE="S_M_LOAD_CUSTOMER" FROMLINK="Success" 
            TOINSTANCE="WK_DIM_BUILD" TOLINK="Start"/>
  <CONNECTOR FROMINSTANCE="WK_DIM_BUILD" FROMLINK="Success" 
            TOINSTANCE="S_M_LOAD_FACT" TOLINK="Start"/>
</WORKFLOW>
```

#### 2. **Worklet** (Reusable Workflow Component)
- **Purpose**: Reusable group of sessions that can be shared across workflows
- **Responsibilities**:
  - Encapsulates a set of related sessions
  - Promotes code reusability
  - Simplifies workflow management
- **XML Structure**: Similar to workflow but contained within a workflow

**Example Worklet XML:**
```xml
<WORKLET NAME="WK_BUILD_DIMS">
  <TASKINSTANCE NAME="S_M_DIM_REGION" TASKTYPE="Session"/>
  <TASKINSTANCE NAME="S_M_DIM_CATEGORY" TASKTYPE="Session"/>

  <CONNECTOR FROMINSTANCE="S_M_DIM_REGION" FROMLINK="Success" 
            TOINSTANCE="S_M_DIM_CATEGORY" TOLINK="Start"/>
</WORKLET>
```

#### 3. **Session** (Execution Instance)
- **Purpose**: Execution configuration for a mapping
- **Responsibilities**:
  - Defines connection information (source/target databases)
  - Sets commit intervals and batch sizes
  - Configures transformation-level settings
  - Manages error handling and recovery
- **XML Structure**: Contains mapping reference and session-specific attributes

**Example Session XML:**
```xml
<SESSION NAME="S_M_LOAD_CUSTOMER">
  <ATTRIBUTE NAME="Connection" VALUE="DB_CUSTOMER"/>
  <ATTRIBUTE NAME="CommitInterval" VALUE="1000"/>
  <SESSTRANSFORMATIONINST NAME="SQ_CUSTOMER" TRANSFORMATIONTYPE="SourceQualifier">
    <ATTRIBUTE NAME="TracingLevel" VALUE="Verbose"/>
  </SESSTRANSFORMATIONINST>
</SESSION>
```

#### 4. **Mapping** (Data Transformation Logic)
- **Purpose**: Defines the data transformation logic
- **Responsibilities**:
  - Defines source and target structures
  - Implements business logic through transformations
  - Manages data flow between components
- **XML Structure**: Contains sources, targets, transformations, and connectors

**Example Mapping XML:**
```xml
<MAPPING NAME="M_LOAD_CUSTOMER">
  <TRANSFORMATION NAME="SQ_CUSTOMER" TYPE="SourceQualifier">
    <ATTRIBUTE NAME="Sql Query" VALUE="SELECT * FROM CUSTOMER_SRC"/>
  </TRANSFORMATION>

  <TRANSFORMATION NAME="EXP_DERIVE" TYPE="Expression">
    <TRANSFORMFIELD NAME="FULL_NAME" EXPR="FIRST_NAME || ' ' || LAST_NAME"/>
    <TRANSFORMFIELD NAME="AGE_BUCKET" EXPR="IIF(AGE < 30, 'YOUNG', 'OTHER')"/>
  </TRANSFORMATION>

  <TRANSFORMATION NAME="LK_REGION" TYPE="Lookup">
    <LOOKUPTABLE NAME="REGION_DIM"/>
  </TRANSFORMATION>

  <TRANSFORMATION NAME="AGG_SALES" TYPE="Aggregator">
    <TRANSFORMFIELD NAME="TOTAL_SALES" EXPR="SUM(SALES_AMT)"/>
    <GROUPBYFIELD NAME="CUSTOMER_ID"/>
  </TRANSFORMATION>

  <CONNECTOR FROMINSTANCE="SQ_CUSTOMER" FROMFIELD="*" 
            TOINSTANCE="EXP_DERIVE" TOFIELD="*"/>
  <CONNECTOR FROMINSTANCE="EXP_DERIVE" FROMFIELD="REGION_ID" 
            TOINSTANCE="LK_REGION" TOFIELD="REGION_ID"/>
</MAPPING>
```

---

## Component Details

### Mapping Components

#### Sources
- **Types**: Database tables, flat files, XML files, web services
- **Purpose**: Define input data structures
- **Common Sources**:
  - `SourceQualifier`: SQL query against database
  - `FlatFile`: File-based sources
  - `XML`: XML file sources

#### Transformations
- **Expression**: Calculated fields, conditional logic (IIF, DECODE, NVL)
- **Lookup**: Reference data lookups (connected/unconnected)
- **Aggregator**: Group by, sum, count, average operations
- **Joiner**: Join multiple sources
- **Router**: Conditional routing to multiple targets
- **Filter**: Row-level filtering
- **Union**: Combine multiple data streams
- **Sorter**: Sort data
- **Rank**: Ranking operations
- **Sequence Generator**: Generate sequence numbers

#### Targets
- **Types**: Database tables, flat files, XML files
- **Purpose**: Define output data structures
- **Common Targets**:
  - `Target Table`: Database table
  - `Target File`: Flat file output

#### Connectors
- **Purpose**: Define data flow between transformations
- **Types**:
  - Field-to-field connections
  - Wildcard connections (`*`)
  - Conditional connections

### Workflow Components

#### Tasks
- **Session**: Executes a mapping
- **Worklet**: Executes a reusable workflow component
- **Command**: Executes shell commands
- **Email**: Sends email notifications
- **Timer**: Waits for specified time
- **Decision**: Conditional branching

#### Connectors
- **Success Link**: Executes on successful completion
- **Failure Link**: Executes on failure
- **Conditional Link**: Executes based on condition

---

## Databricks Equivalents

### Mapping Strategy

| Informatica Component | Databricks Equivalent | Notes |
|----------------------|----------------------|-------|
| **Workflow** | **Databricks Workflows/Jobs** | Orchestration layer |
| **Worklet** | **Workflow Task Group** | Nested tasks in workflow |
| **Session** | **Job Task** | Execution unit with configuration |
| **Mapping** | **Notebook or DLT Pipeline** | Data transformation logic |
| **Transformation** | **PySpark Code** | Business logic implementation |
| **Source** | **Table/File Read** | `spark.table()` or `spark.read` |
| **Target** | **Table/File Write** | `df.write.saveAsTable()` or `df.write.save()` |
| **Connector** | **DataFrame Operations** | Chained transformations |

### Detailed Mapping

#### 1. Workflow → Databricks Workflows

**Informatica Workflow:**
- Orchestrates multiple sessions/worklets
- Defines execution order
- Handles dependencies

**Databricks Workflow:**
- JSON/YAML workflow definition
- Tasks with dependencies
- Schedule and triggers

**Example Databricks Workflow:**
```json
{
  "name": "WF_CUSTOMER_DAILY",
  "tasks": [
    {
      "task_key": "S_M_LOAD_CUSTOMER",
      "notebook_task": {
        "notebook_path": "/mappings/M_LOAD_CUSTOMER"
      }
    },
    {
      "task_key": "WK_DIM_BUILD",
      "depends_on": [{"task_key": "S_M_LOAD_CUSTOMER"}],
      "pipeline_task": {
        "pipeline_id": "WK_BUILD_DIMS"
      }
    },
    {
      "task_key": "S_M_LOAD_FACT",
      "depends_on": [{"task_key": "WK_DIM_BUILD"}],
      "notebook_task": {
        "notebook_path": "/mappings/M_LOAD_FACT"
      }
    }
  ],
  "schedule": {
    "quartz_cron_expression": "0 0 2 * * ?",
    "timezone_id": "America/New_York"
  }
}
```

#### 2. Worklet → Databricks Workflow Task Group

**Informatica Worklet:**
- Reusable group of sessions
- Nested within workflow

**Databricks Equivalent:**
- Task group or separate workflow
- Can be called as a task in parent workflow

**Example:**
```json
{
  "task_key": "WK_DIM_BUILD",
  "depends_on": [{"task_key": "S_M_LOAD_CUSTOMER"}],
  "pipeline_task": {
    "pipeline_id": "WK_BUILD_DIMS_DLT"
  }
}
```

#### 3. Session → Databricks Job Task

**Informatica Session:**
- Execution configuration
- Connection settings
- Commit intervals

**Databricks Job Task:**
- Task configuration
- Cluster settings
- Notebook/DLT pipeline reference

**Example:**
```json
{
  "task_key": "S_M_LOAD_CUSTOMER",
  "notebook_task": {
    "notebook_path": "/mappings/M_LOAD_CUSTOMER",
    "base_parameters": {
      "source_db": "customer_db",
      "target_db": "lakehouse_db",
      "commit_interval": "1000"
    }
  },
  "new_cluster": {
    "spark_version": "13.3.x-scala2.12",
    "node_type_id": "i3.xlarge",
    "num_workers": 2
  }
}
```

#### 4. Mapping → Databricks Notebook or DLT Pipeline

**Option A: PySpark Notebook**

**Informatica Mapping:**
- Contains transformations, sources, targets
- Business logic in expressions

**Databricks Notebook:**
- PySpark code implementing same logic
- Structured as: Read → Transform → Write

**Example Notebook Structure:**
```python
# Databricks notebook source
# MAGIC %md
# MAGIC # M_LOAD_CUSTOMER Mapping
# MAGIC 
# MAGIC Loads and transforms customer data

# COMMAND ----------
# Read source
df_customer = spark.table("customer_db.customer_src")

# COMMAND ----------
# Expression Transformation: EXP_DERIVE
from pyspark.sql import functions as F

df_derived = df_customer.withColumn(
    "FULL_NAME",
    F.concat_ws(" ", F.col("FIRST_NAME"), F.col("LAST_NAME"))
).withColumn(
    "AGE_BUCKET",
    F.when(F.col("AGE") < 30, "YOUNG").otherwise("OTHER")
)

# COMMAND ----------
# Lookup Transformation: LK_REGION
df_region = spark.table("lakehouse_db.region_dim")
df_enriched = df_derived.join(
    F.broadcast(df_region),
    df_derived.REGION_ID == df_region.REGION_ID,
    "left"
).select(
    df_derived["*"],
    df_region.REGION_NAME.alias("REGION_NAME")
)

# COMMAND ----------
# Aggregator Transformation: AGG_SALES
df_aggregated = df_enriched.groupBy("CUSTOMER_ID").agg(
    F.sum("SALES_AMT").alias("TOTAL_SALES"),
    F.first("REGION_NAME").alias("REGION_NAME")
)

# COMMAND ----------
# Write target
df_aggregated.write.mode("overwrite").saveAsTable(
    "lakehouse_db.customer_agg"
)
```

**Option B: Delta Live Tables (DLT) Pipeline**

**Informatica Mapping:**
- ETL logic with transformations

**Databricks DLT:**
- Declarative pipeline definition
- Automatic dependency management
- Built-in data quality

**Example DLT Pipeline:**
```python
# Databricks notebook source
import dlt
from pyspark.sql import functions as F

@dlt.table(
    name="customer_derived",
    comment="Customer data with derived fields"
)
def customer_derived():
    df = spark.table("customer_db.customer_src")
    
    return df.withColumn(
        "FULL_NAME",
        F.concat_ws(" ", F.col("FIRST_NAME"), F.col("LAST_NAME"))
    ).withColumn(
        "AGE_BUCKET",
        F.when(F.col("AGE") < 30, "YOUNG").otherwise("OTHER")
    )

@dlt.table(
    name="customer_enriched",
    comment="Customer data enriched with region"
)
@dlt.expect("valid_region", "REGION_ID IS NOT NULL")
def customer_enriched():
    df_customer = dlt.read("customer_derived")
    df_region = spark.table("lakehouse_db.region_dim")
    
    return df_customer.join(
        F.broadcast(df_region),
        df_customer.REGION_ID == df_region.REGION_ID,
        "left"
    ).select(
        df_customer["*"],
        df_region.REGION_NAME.alias("REGION_NAME")
    )

@dlt.table(
    name="customer_agg",
    comment="Aggregated customer sales"
)
def customer_agg():
    df = dlt.read("customer_enriched")
    
    return df.groupBy("CUSTOMER_ID").agg(
        F.sum("SALES_AMT").alias("TOTAL_SALES"),
        F.first("REGION_NAME").alias("REGION_NAME")
    )
```

#### 5. Transformations → PySpark Code

| Informatica Transformation | PySpark Equivalent | Example |
|----------------------------|-------------------|---------|
| **Expression** | `withColumn()`, `select()` | `df.withColumn("full_name", F.concat_ws(" ", F.col("first"), F.col("last")))` |
| **Lookup** | `join()` with `broadcast()` | `df.join(F.broadcast(lookup_df), join_condition, "left")` |
| **Aggregator** | `groupBy().agg()` | `df.groupBy("id").agg(F.sum("amount").alias("total"))` |
| **Joiner** | `join()` | `df1.join(df2, join_condition, join_type)` |
| **Router** | `filter()` or `when().otherwise()` | `df.filter(F.col("status") == "ACTIVE")` |
| **Filter** | `filter()` | `df.filter(F.col("age") > 18)` |
| **Union** | `union()` or `unionByName()` | `df1.union(df2)` |
| **Sorter** | `orderBy()` | `df.orderBy(F.col("date").desc())` |
| **Rank** | Window functions | `F.rank().over(Window.partitionBy("dept").orderBy("salary"))` |
| **Sequence Generator** | `monotonically_increasing_id()` | `df.withColumn("seq", F.monotonically_increasing_id())` |

---

## Mapping Strategy

### Decision Matrix: Notebook vs. DLT

**Use PySpark Notebook when:**
- Simple, linear transformations
- Custom error handling needed
- Complex control flow
- One-time migrations
- Need fine-grained control

**Use DLT Pipeline when:**
- Multiple related tables
- Need automatic dependency management
- Want built-in data quality
- Incremental processing
- Production-grade pipelines

### Transformation Patterns

#### Pattern 1: Simple ETL (Notebook)
```
Source → Expression → Target
```

**PySpark:**
```python
df = spark.table("source")
df = df.withColumn("derived", F.expr("..."))
df.write.saveAsTable("target")
```

#### Pattern 2: Complex ETL (DLT)
```
Source → Expression → Lookup → Aggregator → Target
```

**DLT:**
```python
@dlt.table(name="step1")
def step1():
    return spark.table("source").withColumn(...)

@dlt.table(name="step2")
def step2():
    return dlt.read("step1").join(...)

@dlt.table(name="final")
def final():
    return dlt.read("step2").groupBy(...).agg(...)
```

#### Pattern 3: Workflow Orchestration
```
Session1 → Worklet → Session2
```

**Databricks Workflow:**
```json
{
  "tasks": [
    {"task_key": "session1", "notebook_task": {...}},
    {
      "task_key": "worklet",
      "depends_on": [{"task_key": "session1"}],
      "pipeline_task": {...}
    },
    {
      "task_key": "session2",
      "depends_on": [{"task_key": "worklet"}],
      "notebook_task": {...}
    }
  ]
}
```

---

## Code Examples

### Example 1: Complete Mapping Migration

**Informatica Mapping: M_LOAD_CUSTOMER**

```xml
<MAPPING NAME="M_LOAD_CUSTOMER">
  <TRANSFORMATION NAME="SQ_CUSTOMER" TYPE="SourceQualifier">
    <ATTRIBUTE NAME="Sql Query" VALUE="SELECT * FROM CUSTOMER_SRC"/>
  </TRANSFORMATION>
  <TRANSFORMATION NAME="EXP_DERIVE" TYPE="Expression">
    <TRANSFORMFIELD NAME="FULL_NAME" EXPR="FIRST_NAME || ' ' || LAST_NAME"/>
    <TRANSFORMFIELD NAME="AGE_BUCKET" EXPR="IIF(AGE < 30, 'YOUNG', 'OTHER')"/>
  </TRANSFORMATION>
  <TRANSFORMATION NAME="TGT_CUSTOMER" TYPE="Target">
    <TARGETTABLE NAME="CUSTOMER_TGT"/>
  </TRANSFORMATION>
</MAPPING>
```

**Databricks Notebook Equivalent:**

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # M_LOAD_CUSTOMER
# MAGIC Loads and transforms customer data

# COMMAND ----------
# Read source (SourceQualifier)
df_customer = spark.table("customer_db.customer_src")

# COMMAND ----------
# Expression transformation (EXP_DERIVE)
from pyspark.sql import functions as F

df_derived = df_customer.withColumn(
    "FULL_NAME",
    F.concat_ws(" ", F.col("FIRST_NAME"), F.col("LAST_NAME"))
).withColumn(
    "AGE_BUCKET",
    F.when(F.col("AGE") < 30, "YOUNG").otherwise("OTHER")
)

# COMMAND ----------
# Write target (TGT_CUSTOMER)
df_derived.write.mode("overwrite").saveAsTable("lakehouse_db.customer_tgt")
```

### Example 2: Workflow with Worklet

**Informatica Workflow:**

```xml
<WORKFLOW NAME="WF_CUSTOMER_DAILY">
  <TASKINSTANCE NAME="S_M_LOAD_CUSTOMER" TASKTYPE="Session"/>
  <TASKINSTANCE NAME="WK_DIM_BUILD" TASKTYPE="Worklet" WORKLETNAME="WK_BUILD_DIMS"/>
  <TASKINSTANCE NAME="S_M_LOAD_FACT" TASKTYPE="Session"/>

  <CONNECTOR FROMINSTANCE="S_M_LOAD_CUSTOMER" FROMLINK="Success" 
            TOINSTANCE="WK_DIM_BUILD" TOLINK="Start"/>
  <CONNECTOR FROMINSTANCE="WK_DIM_BUILD" FROMLINK="Success" 
            TOINSTANCE="S_M_LOAD_FACT" TOLINK="Start"/>
</WORKFLOW>
```

**Databricks Workflow JSON:**

```json
{
  "name": "WF_CUSTOMER_DAILY",
  "email_notifications": {
    "on_success": ["etl-team@company.com"],
    "on_failure": ["etl-team@company.com"]
  },
  "tasks": [
    {
      "task_key": "S_M_LOAD_CUSTOMER",
      "description": "Load customer data",
      "notebook_task": {
        "notebook_path": "/mappings/M_LOAD_CUSTOMER",
        "base_parameters": {
          "source_db": "customer_db",
          "target_db": "lakehouse_db"
        }
      },
      "timeout_seconds": 3600
    },
    {
      "task_key": "WK_DIM_BUILD",
      "description": "Build dimension tables",
      "depends_on": [
        {
          "task_key": "S_M_LOAD_CUSTOMER"
        }
      ],
      "pipeline_task": {
        "pipeline_id": "WK_BUILD_DIMS_DLT"
      }
    },
    {
      "task_key": "S_M_LOAD_FACT",
      "description": "Load fact table",
      "depends_on": [
        {
          "task_key": "WK_DIM_BUILD"
        }
      ],
      "notebook_task": {
        "notebook_path": "/mappings/M_LOAD_FACT",
        "base_parameters": {
          "source_db": "customer_db",
          "target_db": "lakehouse_db"
        }
      }
    }
  ],
  "schedule": {
    "quartz_cron_expression": "0 0 2 * * ?",
    "timezone_id": "America/New_York"
  },
  "max_concurrent_runs": 1
}
```

### Example 3: Complex Transformation

**Informatica Mapping with Multiple Transformations:**

```xml
<MAPPING NAME="M_SALES_ANALYTICS">
  <TRANSFORMATION NAME="SQ_ORDERS" TYPE="SourceQualifier"/>
  <TRANSFORMATION NAME="EXP_ENRICH" TYPE="Expression">
    <TRANSFORMFIELD NAME="ORDER_YEAR" EXPR="YEAR(ORDER_DATE)"/>
    <TRANSFORMFIELD NAME="ORDER_MONTH" EXPR="MONTH(ORDER_DATE)"/>
  </TRANSFORMATION>
  <TRANSFORMATION NAME="LK_CUSTOMER" TYPE="Lookup">
    <LOOKUPTABLE NAME="CUSTOMER_DIM"/>
  </TRANSFORMATION>
  <TRANSFORMATION NAME="AGG_SALES" TYPE="Aggregator">
    <GROUPBYFIELD NAME="CUSTOMER_ID"/>
    <GROUPBYFIELD NAME="ORDER_YEAR"/>
    <TRANSFORMFIELD NAME="TOTAL_AMOUNT" EXPR="SUM(ORDER_AMOUNT)"/>
    <TRANSFORMFIELD NAME="ORDER_COUNT" EXPR="COUNT(*)"/>
  </TRANSFORMATION>
  <TRANSFORMATION NAME="RT_ROUTER" TYPE="Router">
    <GROUP NAME="HIGH_VALUE" CONDITION="TOTAL_AMOUNT > 10000"/>
    <GROUP NAME="LOW_VALUE" CONDITION="TOTAL_AMOUNT <= 10000"/>
  </TRANSFORMATION>
</MAPPING>
```

**Databricks DLT Pipeline:**

```python
import dlt
from pyspark.sql import functions as F

@dlt.table(
    name="orders_enriched",
    comment="Orders with enriched date fields"
)
def orders_enriched():
    df = spark.table("source_db.orders")
    
    return df.withColumn(
        "ORDER_YEAR", F.year(F.col("ORDER_DATE"))
    ).withColumn(
        "ORDER_MONTH", F.month(F.col("ORDER_DATE"))
    )

@dlt.table(
    name="orders_with_customer",
    comment="Orders enriched with customer data"
)
def orders_with_customer():
    df_orders = dlt.read("orders_enriched")
    df_customer = spark.table("lakehouse_db.customer_dim")
    
    return df_orders.join(
        F.broadcast(df_customer),
        df_orders.CUSTOMER_ID == df_customer.CUSTOMER_ID,
        "left"
    ).select(
        df_orders["*"],
        df_customer.CUSTOMER_NAME.alias("CUSTOMER_NAME")
    )

@dlt.table(
    name="sales_aggregated",
    comment="Aggregated sales by customer and year"
)
def sales_aggregated():
    df = dlt.read("orders_with_customer")
    
    return df.groupBy("CUSTOMER_ID", "ORDER_YEAR").agg(
        F.sum("ORDER_AMOUNT").alias("TOTAL_AMOUNT"),
        F.count("*").alias("ORDER_COUNT")
    )

@dlt.table(
    name="high_value_customers",
    comment="High value customers (TOTAL_AMOUNT > 10000)"
)
def high_value_customers():
    df = dlt.read("sales_aggregated")
    return df.filter(F.col("TOTAL_AMOUNT") > 10000)

@dlt.table(
    name="low_value_customers",
    comment="Low value customers (TOTAL_AMOUNT <= 10000)"
)
def low_value_customers():
    df = dlt.read("sales_aggregated")
    return df.filter(F.col("TOTAL_AMOUNT") <= 10000)
```

---

## Migration Patterns

### Pattern 1: One-to-One Mapping

**Informatica:**
- 1 Mapping → 1 Session → 1 Workflow Task

**Databricks:**
- 1 Notebook/DLT → 1 Workflow Task

### Pattern 2: Worklet Consolidation

**Informatica:**
- Multiple Sessions in Worklet → Workflow

**Databricks:**
- DLT Pipeline (multiple tables) → Workflow Task

### Pattern 3: Parallel Execution

**Informatica:**
- Multiple Sessions without dependencies

**Databricks:**
- Multiple Workflow Tasks without `depends_on`

### Pattern 4: Conditional Execution

**Informatica:**
- Router transformation or Decision task

**Databricks:**
- `filter()` or conditional task execution

---

## Summary

### Key Mappings

| Informatica | Databricks | Implementation |
|------------|-----------|----------------|
| **Workflow** | **Workflow/Job** | JSON workflow definition |
| **Worklet** | **Task Group/Pipeline** | Nested tasks or DLT pipeline |
| **Session** | **Task** | Notebook or DLT task |
| **Mapping** | **Notebook/DLT** | PySpark code or DLT pipeline |
| **Transformation** | **PySpark Code** | DataFrame operations |
| **Source** | **Table/File** | `spark.table()` or `spark.read` |
| **Target** | **Table/File** | `df.write.saveAsTable()` |

### Best Practices

1. **Start with Notebooks**: For simple mappings, use PySpark notebooks
2. **Use DLT for Complex Pipelines**: When you have multiple related tables
3. **Preserve Workflow Structure**: Maintain execution order and dependencies
4. **Leverage Databricks Features**: Use Delta Lake, Unity Catalog, data quality
5. **Test Incrementally**: Migrate one mapping at a time

### Migration Checklist

- [ ] Parse Informatica XML files
- [ ] Generate canonical model
- [ ] Convert mappings to notebooks/DLT
- [ ] Convert workflows to Databricks workflows
- [ ] Test individual components
- [ ] Test end-to-end workflows
- [ ] Validate data quality
- [ ] Performance tuning
- [ ] Documentation

---

This guide provides a comprehensive mapping from Informatica components to Databricks equivalents, enabling a systematic migration approach.

