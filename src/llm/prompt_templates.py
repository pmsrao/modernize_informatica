"""Centralized Prompt Templates for LLM Agents

This module provides structured prompt templates with few-shot examples
for all AI agent use cases. Templates are designed to produce consistent,
high-quality LLM responses.
"""
from typing import Dict, Any
import json


# ============================================================================
# Rule Explanation Templates
# ============================================================================

def get_rule_explanation_prompt(field_name: str, expression: str, context: Dict[str, Any] = None) -> str:
    """Generate prompt for explaining Informatica expressions in business terms.
    
    Args:
        field_name: Name of the field being explained
        expression: Informatica expression to explain
        context: Optional context about the transformation or mapping
        
    Returns:
        Formatted prompt string
    """
    context_str = ""
    if context:
        context_str = f"\nContext: {json.dumps(context, indent=2)}"
    
    return f"""You are an expert data engineer explaining Informatica ETL expressions in simple business terms.

Your task is to explain what the following Informatica expression does in clear, non-technical language that business users can understand.

Field Name: {field_name}
Expression: {expression}{context_str}

Examples of good explanations:

Example 1:
Field: AGE_BUCKET
Expression: IIF(AGE < 30, 'YOUNG', 'OTHER')
Explanation: "This field classifies customers into age groups. If the customer's age is less than 30, they are classified as 'YOUNG', otherwise they are classified as 'OTHER'."

Example 2:
Field: FULL_NAME
Expression: FIRST_NAME || ' ' || LAST_NAME
Explanation: "This field combines the first name and last name into a single full name, separated by a space."

Example 3:
Field: DISCOUNT_AMOUNT
Expression: UNIT_PRICE * QUANTITY * (DISCOUNT_PCT / 100)
Explanation: "This field calculates the total discount amount by multiplying the unit price by quantity, then applying the discount percentage."

Example 4:
Field: IS_VALID_EMAIL
Expression: IIF(INSTR(EMAIL, '@') > 0 AND INSTR(EMAIL, '.') > INSTR(EMAIL, '@'), 1, 0)
Explanation: "This field validates email addresses. It returns 1 (true) if the email contains an '@' symbol and a '.' after the '@' symbol, otherwise returns 0 (false)."

Now explain the expression above in the same clear, business-friendly style. Focus on:
- What the expression does (not how it does it technically)
- The business logic or rule it implements
- Any conditions or classifications it creates
- Keep it concise (2-3 sentences maximum)

Explanation:"""


# ============================================================================
# Mapping Summary Templates
# ============================================================================

def get_mapping_summary_prompt(canonical_model: Dict[str, Any]) -> str:
    """Generate prompt for summarizing mapping logic.
    
    Args:
        canonical_model: Canonical mapping model structure
        
    Returns:
        Formatted prompt string
    """
    mapping_json = json.dumps(canonical_model, indent=2)
    
    return f"""You are an expert data engineer summarizing Informatica ETL mappings.

Your task is to create a clear, comprehensive summary of what this mapping does, written for both technical and business audiences.

Mapping Structure:
{mapping_json}

Provide a summary that includes:

1. **Purpose**: What business process does this mapping support?
2. **Data Flow**: Which source tables/files feed into this mapping, and what target tables/files does it produce?
3. **Key Transformations**: What are the main data transformations (joins, lookups, aggregations, calculations)?
4. **Business Logic**: What are the key business rules implemented (filters, classifications, calculations)?
5. **Data Quality**: Are there any data quality checks or validations?

Format your response as a structured narrative (not bullet points) that tells the story of the data flow.

Example Summary Format:

"This mapping processes customer order data to create a sales fact table and customer dimension. It reads from three source tables: CUSTOMER_SRC (customer master data), ORDER_SRC (transactional order data), and PRODUCT_SRC (product catalog). The mapping enriches customer data by calculating full names and customer segments based on region. It joins customer and order data, then applies product lookups to get category information. Orders are classified by value (high, medium, low) using a router transformation. The mapping aggregates sales by customer, region, and time period, and ranks customers by total sales. Finally, it filters for valid records and writes to three targets: a sales fact table, a customer dimension table (with SCD2 support), and a product performance summary table. The mapping implements business rules for discount calculation, order classification, and customer segmentation."

Now provide a similar comprehensive summary for the mapping above:

Summary:"""


# ============================================================================
# Risk Analysis Templates
# ============================================================================

def get_risk_analysis_prompt(canonical_model: Dict[str, Any]) -> str:
    """Generate prompt for analyzing mapping risks.
    
    Args:
        canonical_model: Canonical mapping model structure
        
    Returns:
        Formatted prompt string
    """
    mapping_json = json.dumps(canonical_model, indent=2)
    
    return f"""You are an expert data engineer analyzing Informatica ETL mappings for potential risks and issues.

Your task is to identify risks, anti-patterns, and potential problems in this mapping that could lead to:
- Data quality issues
- Performance problems
- Maintenance difficulties
- Migration challenges
- Runtime errors

Mapping Structure:
{mapping_json}

Analyze the mapping and identify risks in these categories:

1. **Data Quality Risks**:
   - Missing null handling
   - Type casting issues
   - Data loss potential
   - Invalid default values

2. **Performance Risks**:
   - Inefficient joins
   - Large data scans
   - Missing filters
   - Complex nested expressions

3. **Maintainability Risks**:
   - Overly complex expressions
   - Hard-coded values
   - Unclear business logic
   - Tight coupling

4. **Migration Risks**:
   - Informatica-specific functions
   - Complex nested IIF statements
   - Non-standard patterns
   - Platform dependencies

Return your analysis as a JSON array with this structure:
[
  {{
    "category": "Data Quality|Performance|Maintainability|Migration",
    "severity": "High|Medium|Low",
    "location": "transformation_name/field_name",
    "risk": "Description of the risk",
    "impact": "What could go wrong",
    "recommendation": "How to mitigate"
  }}
]

Example:
[
  {{
    "category": "Data Quality",
    "severity": "High",
    "location": "EXP_CALCULATIONS/AGE_BUCKET",
    "risk": "Expression 'IIF(AGE < 30, 'YOUNG', 'OTHER')' does not handle NULL values in AGE field",
    "impact": "NULL ages will be classified as 'OTHER', which may not be the intended behavior",
    "recommendation": "Add null check: IIF(ISNULL(AGE), 'UNKNOWN', IIF(AGE < 30, 'YOUNG', 'OTHER'))"
  }}
]

Risk Analysis:"""


# ============================================================================
# Transformation Suggestion Templates
# ============================================================================

def get_transformation_suggestion_prompt(canonical_model: Dict[str, Any], target_platform: str = "PySpark") -> str:
    """Generate prompt for suggesting transformation optimizations.
    
    Args:
        canonical_model: Canonical mapping model structure
        target_platform: Target platform (PySpark, SQL, etc.)
        
    Returns:
        Formatted prompt string
    """
    mapping_json = json.dumps(canonical_model, indent=2)
    
    return f"""You are an expert data engineer suggesting optimizations for Informatica ETL mappings being migrated to {target_platform}.

Your task is to identify opportunities to:
- Simplify complex expressions
- Use more idiomatic {target_platform} functions
- Improve performance
- Split overly complex transformations
- Modernize patterns

Mapping Structure:
{mapping_json}

Analyze the mapping and provide optimization suggestions. For each suggestion, include:

1. **Current Pattern**: What the current implementation does
2. **Suggested Improvement**: How to improve it
3. **Benefits**: Why this is better (performance, readability, maintainability)
4. **Implementation**: Show the improved code/expression

Return your suggestions as a JSON array:
[
  {{
    "transformation": "transformation_name",
    "field": "field_name (optional)",
    "current_pattern": "Description of current implementation",
    "suggestion": "Description of suggested improvement",
    "benefits": ["benefit1", "benefit2"],
    "improved_code": "Example of improved {target_platform} code",
    "priority": "High|Medium|Low"
  }}
]

Example:
[
  {{
    "transformation": "EXP_CALCULATIONS",
    "field": "FULL_NAME",
    "current_pattern": "Uses string concatenation: FIRST_NAME || ' ' || LAST_NAME",
    "suggestion": "Use {target_platform} concat_ws function for better null handling",
    "benefits": ["Handles nulls gracefully", "More readable", "Better performance"],
    "improved_code": "F.concat_ws(' ', F.col('FIRST_NAME'), F.col('LAST_NAME'))",
    "priority": "Medium"
  }}
]

Optimization Suggestions:"""


# ============================================================================
# Code Fix Templates
# ============================================================================

def get_code_fix_prompt(pyspark_code: str, error_message: str = None, error_type: str = None) -> str:
    """Generate prompt for fixing PySpark code errors.
    
    Args:
        pyspark_code: The PySpark code that needs fixing
        error_message: Optional error message from execution
        error_type: Optional error type (syntax, runtime, logic)
        
    Returns:
        Formatted prompt string
    """
    error_context = ""
    if error_message:
        error_context = f"\n\nError Message:\n{error_message}"
    if error_type:
        error_context += f"\nError Type: {error_type}"
    
    return f"""You are an expert PySpark developer fixing code errors while preserving the original business logic.

Your task is to fix errors in the following PySpark code. Maintain the semantic meaning and business logic while correcting technical issues.

PySpark Code:
```python
{pyspark_code}{error_context}

Guidelines:
1. Fix syntax errors, type mismatches, and runtime issues
2. Preserve the original business logic and calculations
3. Use idiomatic PySpark patterns
4. Add proper null handling if missing
5. Ensure column references are correct
6. Fix import statements if needed
7. Add comments explaining any significant changes

Return the fixed code wrapped in a code block, followed by a brief explanation of what was fixed.

Fixed Code:"""


# ============================================================================
# Impact Analysis Templates
# ============================================================================

def get_impact_analysis_prompt(mapping_model: Dict[str, Any], change_target: str, change_description: str) -> str:
    """Generate prompt for analyzing impact of changes.
    
    Args:
        mapping_model: Canonical mapping model
        change_target: What is being changed (field, transformation, etc.)
        change_description: Description of the proposed change
        
    Returns:
        Formatted prompt string
    """
    mapping_json = json.dumps(mapping_model, indent=2)
    
    return f"""You are an expert data engineer performing impact analysis for ETL mapping changes.

Your task is to identify all downstream impacts of a proposed change to this mapping.

Mapping Structure:
{mapping_json}

Proposed Change:
Target: {change_target}
Description: {change_description}

Analyze the impact and identify:

1. **Direct Dependencies**: Fields, transformations, or targets that directly use the changed element
2. **Indirect Dependencies**: Fields that depend on fields that depend on the change (transitive dependencies)
3. **Downstream Targets**: Which target tables/views will be affected
4. **Data Quality Impact**: How data quality might be affected
5. **Regression Testing Needs**: What needs to be tested

Return your analysis as JSON:
{{
  "change_target": "{change_target}",
  "direct_dependencies": [
    {{
      "element": "transformation_name/field_name",
      "impact": "Description of how it's affected",
      "severity": "High|Medium|Low"
    }}
  ],
  "indirect_dependencies": [
    {{
      "element": "transformation_name/field_name",
      "impact": "Description of transitive impact",
      "severity": "High|Medium|Low"
    }}
  ],
  "affected_targets": ["target1", "target2"],
  "data_quality_concerns": ["concern1", "concern2"],
  "testing_priority": ["test1", "test2"],
  "overall_risk": "High|Medium|Low"
}}

Impact Analysis:"""


# ============================================================================
# Mapping Reconstruction Templates
# ============================================================================

def get_mapping_reconstruction_prompt(clues: Dict[str, Any]) -> str:
    """Generate prompt for reconstructing mappings from partial information.
    
    Args:
        clues: Dictionary containing partial XML, logs, lineage, target definitions
        
    Returns:
        Formatted prompt string
    """
    clues_json = json.dumps(clues, indent=2)
    
    return f"""You are an expert data engineer reconstructing Informatica mappings from partial information.

Your task is to infer the most likely mapping structure based on available clues.

Available Clues:
{clues_json}

Reconstruct the mapping by:

1. Analyzing target table structures to infer required transformations
2. Using lineage information to determine data flow
3. Examining log fragments for transformation patterns
4. Inferring missing transformations based on business logic
5. Suggesting likely expressions based on field names and types

Return a canonical mapping model structure (JSON) that represents the most likely mapping:

{{
  "mapping_name": "inferred_name",
  "sources": [
    {{
      "name": "source_name",
      "type": "table|file",
      "fields": [...]
    }}
  ],
  "targets": [
    {{
      "name": "target_name",
      "type": "table",
      "fields": [...]
    }}
  ],
  "transformations": [
    {{
      "name": "transformation_name",
      "type": "EXPRESSION|LOOKUP|AGGREGATOR|etc",
      "input_ports": [...],
      "output_ports": [...],
      "expressions": [...]
    }}
  ],
  "connectors": [...],
  "confidence": "High|Medium|Low",
  "assumptions": ["assumption1", "assumption2"]
}}

Reconstructed Mapping:"""


# ============================================================================
# Workflow Simulation Templates
# ============================================================================

def get_workflow_simulation_prompt(dag_model: Dict[str, Any]) -> str:
    """Generate prompt for simulating workflow execution.
    
    Args:
        dag_model: DAG structure with nodes, edges, execution levels
        
    Returns:
        Formatted prompt string
    """
    dag_json = json.dumps(dag_model, indent=2)
    
    return f"""You are an expert data engineer simulating ETL workflow execution.

Your task is to simulate the execution of this workflow, identify execution paths, bottlenecks, and potential issues.

Workflow DAG:
{dag_json}

Simulate the workflow execution and provide:

1. **Execution Sequence**: Step-by-step execution order
2. **Parallel Execution Groups**: Which tasks can run simultaneously
3. **Critical Path**: The longest path that determines total execution time
4. **Bottlenecks**: Tasks that could slow down the workflow
5. **Single Points of Failure**: Tasks that, if they fail, would stop the entire workflow
6. **Resource Requirements**: Estimated resource needs for each execution level
7. **Optimization Opportunities**: Suggestions for improving execution time

Return your simulation as JSON:
{{
  "execution_sequence": [
    {{
      "level": 1,
      "tasks": ["task1", "task2"],
      "execution_type": "parallel|sequential",
      "estimated_duration": "duration_estimate",
      "dependencies": []
    }}
  ],
  "critical_path": ["task1", "task2", "task3"],
  "bottlenecks": [
    {{
      "task": "task_name",
      "reason": "Why it's a bottleneck",
      "impact": "Impact on overall execution"
    }}
  ],
  "single_points_of_failure": ["task1", "task2"],
  "resource_requirements": {{
    "level_1": "resource_estimate",
    "level_2": "resource_estimate"
  }},
  "optimization_suggestions": [
    {{
      "suggestion": "Description",
      "benefit": "Expected improvement",
      "priority": "High|Medium|Low"
    }}
  ]
}}

Workflow Simulation:"""


# ============================================================================
# Legacy Simple Templates (for backward compatibility)
# ============================================================================

RULE_EXPLANATION_PROMPT = """
Explain the following Informatica expression in simple business terms:
{expr}
"""

MAPPING_SUMMARY_PROMPT = """
Summarize this mapping logic:
{mapping_json}
"""

RISK_ANALYSIS_PROMPT = """
Analyze the following mapping for potential risks:
{mapping_json}
"""

TRANSFORMATION_SUGGESTION_PROMPT = """
Suggest transformation optimizations for the expression:
{expr}
"""
