"""PySpark Generator — Production Version
Generates PySpark DataFrame code from canonical model.
"""
from typing import Dict, Any, List, Optional
from utils.logger import get_logger
from parser.reference_resolver import ReferenceResolver
from versioning.version_store import VersionStore

logger = get_logger(__name__)


class PySparkGenerator:
    """Generates PySpark code from canonical mapping model."""
    
    def __init__(self, reference_resolver: Optional[ReferenceResolver] = None):
        """Initialize PySpark generator.
        
        Args:
            reference_resolver: Optional reference resolver for resolving mapplets
        """
        self.reference_resolver = reference_resolver or ReferenceResolver()
    
    def generate(self, model: Dict[str, Any]) -> str:
        """Generate PySpark code from canonical model.
        
        Args:
            model: Canonical model dictionary
            
        Returns:
            Complete PySpark code as string
        """
        lines = []
        
        # Imports
        lines.append("from pyspark.sql import SparkSession, functions as F")
        lines.append("from pyspark.sql.types import *")
        lines.append("from pyspark.sql.window import Window")
        lines.append("")
        
        # Spark session initialization
        lines.append("# Initialize Spark Session")
        lines.append("spark = SparkSession.builder.appName('{}').getOrCreate()".format(
            model.get("transformation_name", model.get("mapping_name", "InformaticaTransformation"))))
        lines.append("")
        
        # Read sources
        lines.append("# Read source tables")
        for source in model.get("sources", []):
            source_name = source.get("name", "")
            table_name = source.get("table", "")
            database = source.get("database", "")
            
            if database:
                full_table = f"{database}.{table_name}"
            else:
                full_table = table_name
            
            lines.append(f"df_{source_name} = spark.table('{full_table}')")
        lines.append("")
        
        # Start with first source or create base DataFrame
        if model.get("sources"):
            first_source = model["sources"][0]
            lines.append(f"# Start with base DataFrame")
            lines.append(f"df = df_{first_source.get('name', 'source')}")
            lines.append("")
        
        # Track reusable transformations to generate as functions
        reusable_transforms = {}
        
        # Separate Source Qualifiers - they should be processed first
        source_qualifiers = []
        other_transformations = []
        
        transformations = model.get("transformations", [])
        for trans in transformations:
            if trans.get("type") == "SOURCE_QUALIFIER":
                source_qualifiers.append(trans)
            else:
                other_transformations.append(trans)
        
        # Process Source Qualifiers first
        for trans in source_qualifiers:
            lines.extend(self._generate_source_qualifier(trans))
            lines.append("")
        
        # Process other transformations in order
        for trans in other_transformations:
            trans_type = trans.get("type", "")
            trans_name = trans.get("name", "")
            
            # Check if this is a reusable transformation
            if trans.get("is_reusable", False):
                reusable_name = trans.get("reusable_name", trans_name)
                reusable_transforms[reusable_name] = trans
                # Generate as function on first encounter
                lines.extend(self._generate_reusable_transformation_function(trans, reusable_name))
                lines.append("")
            
            if trans_type == "MAPPLET_INSTANCE":
                lines.extend(self._generate_mapplet_instance(trans, model))
            elif trans_type == "CUSTOM_TRANSFORMATION":
                lines.extend(self._generate_custom_transformation(trans))
            elif trans_type == "STORED_PROCEDURE":
                lines.extend(self._generate_stored_procedure(trans))
            elif trans_type == "EXPRESSION":
                # Check if reusable - if so, call function instead of generating inline
                if trans.get("is_reusable", False):
                    reusable_name = trans.get("reusable_name", trans_name)
                    lines.extend(self._generate_reusable_transformation_call(trans, reusable_name))
                else:
                    lines.extend(self._generate_expression(trans))
            elif trans_type == "LOOKUP":
                # Check if reusable
                if trans.get("is_reusable", False):
                    reusable_name = trans.get("reusable_name", trans_name)
                    lines.extend(self._generate_reusable_transformation_call(trans, reusable_name))
                else:
                    lines.extend(self._generate_lookup(trans))
            elif trans_type == "JOINER":
                lines.extend(self._generate_joiner(trans, model))
            elif trans_type == "AGGREGATOR":
                lines.extend(self._generate_aggregator(trans))
            elif trans_type == "FILTER":
                lines.extend(self._generate_filter(trans))
            elif trans_type == "ROUTER":
                lines.extend(self._generate_router(trans))
            elif trans_type == "SORTER":
                lines.extend(self._generate_sorter(trans))
            elif trans_type == "RANK":
                lines.extend(self._generate_rank(trans))
            elif trans_type == "UNION":
                lines.extend(self._generate_union(trans))
            elif trans_type == "UPDATE_STRATEGY":
                lines.extend(self._generate_update_strategy(trans))
            elif trans_type == "SOURCE_QUALIFIER":
                lines.extend(self._generate_source_qualifier(trans))
            
            lines.append("")
        
        # Write to target
        lines.append("# Write to target table")
        for target in model.get("targets", []):
            target_name = target.get("name", "")
            table_name = target.get("table", "")
            database = target.get("database", "")
            
            if database:
                full_table = f"{database}.{table_name}"
            else:
                full_table = table_name
            
            # Check for SCD type
            scd_type = model.get("scd_type", "NONE")
            if scd_type == "SCD2":
                lines.append(f"# SCD2 merge operation")
                lines.append(f"df.write.format('delta').mode('overwrite').saveAsTable('{full_table}')")
            else:
                lines.append(f"df.write.format('delta').mode('overwrite').saveAsTable('{full_table}')")
        
        return "\n".join(lines)
    
    def _generate_expression(self, trans: Dict[str, Any]) -> List[str]:
        """Generate code for Expression transformation."""
        lines = []
        trans_name = trans.get('name', '')
        lines.append(f"# Expression: {trans_name}")
        
        # Check both output_ports (canonical model) and ports (legacy)
        output_ports = trans.get("output_ports", [])
        if not output_ports:
            # Fallback to ports with port_type check
            all_ports = trans.get("ports", [])
            output_ports = [p for p in all_ports if p.get("port_type") == "OUTPUT"]
        
        if not output_ports:
            lines.append(f"# No output ports found for {trans_name}")
            return lines
        
        # Translate expressions to PySpark
        try:
            from translator import Parser, tokenize
            from translator.pyspark_translator import PySparkTranslator
            translator = PySparkTranslator()
            use_translator = True
        except ImportError:
            use_translator = False
        
        for port in output_ports:
            port_name = port.get("name", "")
            expression = port.get("expression", "")
            if expression:
                try:
                    if use_translator:
                        # Translate Informatica expression to PySpark
                        tokens = tokenize(expression)
                        parser = Parser(tokens)
                        ast = parser.parse()
                        pyspark_expr = translator.visit(ast)
                        lines.append(f"df = df.withColumn('{port_name}', {pyspark_expr})")
                    else:
                        # Simple translation: replace Informatica operators with PySpark
                        pyspark_expr = self._translate_expression_simple(expression)
                        lines.append(f"df = df.withColumn('{port_name}', {pyspark_expr})")
                except Exception as e:
                    # Fallback: simple string replacement
                    logger.warning(f"Could not translate expression {expression}: {e}")
                    pyspark_expr = self._translate_expression_simple(expression)
                    lines.append(f"df = df.withColumn('{port_name}', {pyspark_expr})")
        
        return lines
    
    def _generate_lookup(self, trans: Dict[str, Any]) -> List[str]:
        """Generate code for Lookup transformation."""
        lines = []
        trans_name = trans.get('name', '')
        lines.append(f"# Lookup: {trans_name}")
        
        lookup_type = trans.get("lookup_type", "connected")
        table_name = trans.get("table_name", "")
        condition = trans.get("condition", {})
        
        if not table_name:
            # Try to get from LOOKUPTABLE in ports or other attributes
            lines.append(f"# Lookup table name not found for {trans_name}")
            lines.append(f"# lookup_df = spark.table('LOOKUP_TABLE_NAME')")
            lines.append(f"# df = df.join(F.broadcast(lookup_df), join_condition, 'left')")
            return lines
        
        # Broadcast join for lookup (both connected and unconnected can be joined)
        # Lookup tables are typically small and benefit from broadcast join
        lines.append(f"lookup_df = spark.table('{table_name}')")
        lines.append(f"# Performance optimization: Using broadcast join for lookup table")
        lines.append(f"# Broadcast join is efficient for small lookup tables (< 100MB)")
        
        if condition:
            source_port = condition.get("source_port", "")
            lookup_port = condition.get("lookup_port", "")
            if source_port and lookup_port:
                lines.append(f"df = df.join(F.broadcast(lookup_df), "
                           f"df['{source_port}'] == lookup_df['{lookup_port}'], 'left')")
            else:
                # Try to infer from common port names
                lines.append(f"# Join condition not fully specified for {trans_name}")
                lines.append(f"# df = df.join(F.broadcast(lookup_df), join_condition, 'left')")
        else:
            # No explicit condition - might need to infer from connectors or use common key
            # For now, generate a placeholder
            lines.append(f"# No explicit join condition found for {trans_name}")
            lines.append(f"# Infer join condition from connectors or use common key pattern")
            lines.append(f"# df = df.join(F.broadcast(lookup_df), df['key'] == lookup_df['key'], 'left')")
        
        return lines
    
    def _generate_joiner(self, trans: Dict[str, Any], model: Dict[str, Any] = None) -> List[str]:
        """Generate code for Joiner transformation.
        
        Args:
            trans: Joiner transformation
            model: Optional canonical model to find connectors
        """
        lines = []
        trans_name = trans.get('name', '')
        lines.append(f"# Joiner: {trans_name}")
        
        join_type = trans.get("join_type", "INNER").lower()
        conditions = trans.get("conditions", [])
        
        # Find source DataFrames from connectors
        df1_name = None
        df2_name = None
        
        if model:
            connectors = model.get("connectors", [])
            # Find connectors that feed into this joiner
            input_connectors = [c for c in connectors if c.get("to_transformation") == trans_name]
            
            if len(input_connectors) >= 2:
                # Use first two input transformations as join sources
                df1_name = input_connectors[0].get("from_transformation", "")
                df2_name = input_connectors[1].get("from_transformation", "")
            elif len(input_connectors) == 1:
                # Only one input - use it as df1, need to infer df2
                df1_name = input_connectors[0].get("from_transformation", "")
                df2_name = "df2"  # Fallback
        
        # Default to df1/df2 if not found from connectors
        if not df1_name:
            df1_name = "df1"
        if not df2_name:
            df2_name = "df2"
        
        # Use df_ prefix for transformation names
        if df1_name and not df1_name.startswith("df_"):
            df1_var = f"df_{df1_name}"
        else:
            df1_var = df1_name
        
        if df2_name and not df2_name.startswith("df_"):
            df2_var = f"df_{df2_name}"
        else:
            df2_var = df2_name
        
        # Check if we should use broadcast join for small tables
        use_broadcast = trans.get("_optimization_hint") == "broadcast_join" or \
                       trans.get("right_table_size", "unknown") == "small"
        
        if conditions:
            join_condition = " && ".join([
                f"{df1_var}['{c.get('left_port', '')}'] == {df2_var}['{c.get('right_port', '')}']"
                for c in conditions
            ])
            
            if use_broadcast:
                lines.append(f"# Using broadcast join for small right table (optimization)")
                lines.append(f"{df2_var}_broadcast = F.broadcast({df2_var})")
                lines.append(f"df_{trans_name} = {df1_var}.join({df2_var}_broadcast, {join_condition}, '{join_type}')")
            else:
                lines.append(f"df_{trans_name} = {df1_var}.join({df2_var}, {join_condition}, '{join_type}')")
                lines.append(f"# Performance hint: Consider broadcast join if {df2_var} is small (< 100MB)")
        else:
            lines.append(f"# Join conditions not fully specified for {trans_name}")
            lines.append(f"# df_{trans_name} = {df1_var}.join({df2_var}, join_condition, '{join_type}')")
        
        # Update main df to point to joiner result
        lines.append(f"df = df_{trans_name}")
        
        return lines
    
    def _generate_aggregator(self, trans: Dict[str, Any]) -> List[str]:
        """Generate code for Aggregator transformation."""
        lines = []
        trans_name = trans.get('name', '')
        lines.append(f"# Aggregator: {trans_name}")
        
        group_by_ports = trans.get("group_by_ports", [])
        aggregate_functions = trans.get("aggregate_functions", [])
        
        if not group_by_ports and not aggregate_functions:
            lines.append(f"# No group by or aggregate functions found for {trans_name}")
            return lines
        
        # Check for optimization hints
        use_partitioning = trans.get("_optimization_hint") == "partition_by_group_by"
        
        # Build group by columns
        if group_by_ports:
            group_cols = [f"F.col('{p}')" for p in group_by_ports]
            if use_partitioning:
                lines.append(f"# Performance optimization: Partitioning by group-by columns")
                lines.append(f"# Consider repartitioning before aggregation if data is skewed:")
                lines.append(f"# df = df.repartition(*[{', '.join(group_cols)}])")
        else:
            # If no explicit group by, might be a global aggregate
            group_cols = []
        
        # Build aggregate expressions
        agg_exprs = []
        for af in aggregate_functions:
            func_name = af.get("function", "").upper()
            port_name = af.get("port", "")
            expr = af.get("expression", "")
            
            if func_name:
                # Extract column name from expression if needed
                if expr:
                    # Expression might be like "SUM(SALES_AMT)" - extract SALES_AMT
                    import re
                    col_match = re.search(r'\(([^)]+)\)', expr)
                    if col_match:
                        col_name = col_match.group(1).strip()
                        agg_exprs.append(f"F.{func_name.lower()}(F.col('{col_name}')).alias('{port_name}')")
                    else:
                        agg_exprs.append(f"F.{func_name.lower()}(F.expr('{expr}')).alias('{port_name}')")
                else:
                    agg_exprs.append(f"F.{func_name.lower()}(F.col('{port_name}')).alias('{port_name}')")
        
        if agg_exprs:
            if group_cols:
                lines.append(f"df = df.groupBy({', '.join(group_cols)}).agg({', '.join(agg_exprs)})")
                # Add performance hint for large datasets
                lines.append(f"# Performance hint: For large datasets, consider using window functions or")
                lines.append(f"# caching intermediate results if this aggregation is reused")
            else:
                # Global aggregate (no group by)
                lines.append(f"df = df.agg({', '.join(agg_exprs)})")
                lines.append(f"# Performance hint: Global aggregation processes all data - consider filtering early")
        elif group_cols:
            # Only group by, no aggregates
            lines.append(f"df = df.groupBy({', '.join(group_cols)})")
        
        return lines
    
    def _generate_filter(self, trans: Dict[str, Any]) -> List[str]:
        """Generate code for Filter transformation."""
        lines = []
        lines.append(f"# Filter: {trans.get('name', '')}")
        
        filter_condition = trans.get("filter_condition", "")
        if filter_condition:
            lines.append(f"df = df.filter({filter_condition})")
        
        return lines
    
    def _generate_router(self, trans: Dict[str, Any]) -> List[str]:
        """Generate code for Router transformation."""
        lines = []
        lines.append(f"# Router: {trans.get('name', '')}")
        
        groups = trans.get("groups", [])
        for group in groups:
            group_name = group.get("name", "")
            filter_cond = group.get("filter_condition", "")
            lines.append(f"df_{group_name} = df.filter({filter_cond})")
        
        return lines
    
    def _generate_sorter(self, trans: Dict[str, Any]) -> List[str]:
        """Generate code for Sorter transformation."""
        lines = []
        lines.append(f"# Sorter: {trans.get('name', '')}")
        
        sort_keys = trans.get("sort_keys", [])
        if sort_keys:
            order_cols = []
            for key in sort_keys:
                direction = "asc" if key.get("direction", "ASC").upper() == "ASC" else "desc"
                order_cols.append(f"F.col('{key.get('port', '')}').{direction}()")
            lines.append(f"df = df.orderBy({', '.join(order_cols)})")
        
        return lines
    
    def _generate_rank(self, trans: Dict[str, Any]) -> List[str]:
        """Generate code for Rank transformation."""
        lines = []
        lines.append(f"# Rank: {trans.get('name', '')}")
        
        rank_keys = trans.get("rank_keys", [])
        rank_count = int(trans.get("rank_count", "1"))
        top_bottom = trans.get("top_bottom", "TOP").upper()
        
        if rank_keys:
            partition_cols = [f"F.col('{k.get('port', '')}')" for k in rank_keys]
            order_cols = partition_cols  # Use same columns for ordering
            lines.append(f"window = Window.partitionBy({', '.join(partition_cols)}).orderBy({', '.join(order_cols)})")
            lines.append(f"df = df.withColumn('rank', F.rank().over(window))")
            if top_bottom == "TOP":
                lines.append(f"df = df.filter(F.col('rank') <= {rank_count})")
            else:
                lines.append(f"df = df.filter(F.col('rank') >= F.max('rank').over(window) - {rank_count} + 1)")
        else:
            lines.append(f"# No rank keys found for {trans.get('name', '')}")
        
        return lines
    
    def _generate_union(self, trans: Dict[str, Any]) -> List[str]:
        """Generate code for Union transformation."""
        lines = []
        lines.append(f"# Union: {trans.get('name', '')}")
        lines.append("# Union operations should be performed on DataFrames with matching schemas")
        lines.append("# df = df1.union(df2)")
        return lines
    
    def _generate_update_strategy(self, trans: Dict[str, Any]) -> List[str]:
        """Generate code for Update Strategy transformation."""
        lines = []
        lines.append(f"# Update Strategy: {trans.get('name', '')}")
        lines.append("# Update strategy logic (DD_INSERT, DD_UPDATE, DD_DELETE, DD_REJECT)")
        lines.append("# This typically requires Delta merge operations")
        return lines
    
    def _generate_source_qualifier(self, trans: Dict[str, Any]) -> List[str]:
        """Generate code for source qualifier transformation.
        
        Source Qualifiers read from source tables. They should create a DataFrame
        that can be used by downstream transformations.
        
        Args:
            trans: Source qualifier transformation
            
        Returns:
            List of code lines
        """
        lines = []
        trans_name = trans.get("name", "UNKNOWN")
        sql_query = trans.get("sql_query", "")
        filter_condition = trans.get("filter", "")
        
        # Extract table name from SQL query if available
        # Format: "SELECT * FROM TABLE_NAME" or "SELECT * FROM DATABASE.TABLE_NAME"
        table_name = None
        if sql_query:
            # Try to extract table name from SQL
            import re
            match = re.search(r'FROM\s+([\w\.]+)', sql_query, re.IGNORECASE)
            if match:
                table_name = match.group(1)
        
        # If no table name found, try to infer from transformation name
        # Source Qualifiers often follow pattern: SQ_TABLENAME
        if not table_name and trans_name.startswith("SQ_"):
            # Try to extract table name from SQ_ prefix
            potential_table = trans_name[3:]  # Remove "SQ_" prefix
            table_name = potential_table
        
        if table_name:
            # Generate DataFrame read
            lines.append(f"# Source Qualifier: {trans_name}")
            lines.append(f"df_{trans_name} = spark.table('{table_name}')")
            
            # Apply filter if present
            if filter_condition:
                lines.append(f"df_{trans_name} = df_{trans_name}.filter({filter_condition})")
        else:
            # Fallback: use SQL query directly if available
            if sql_query:
                lines.append(f"# Source Qualifier: {trans_name}")
                lines.append(f"df_{trans_name} = spark.sql(\"\"\"{sql_query}\"\"\")")
                if filter_condition:
                    lines.append(f"df_{trans_name} = df_{trans_name}.filter({filter_condition})")
            else:
                # Last resort: placeholder
                lines.append(f"# Source Qualifier: {trans_name}")
                lines.append(f"# TODO: Implement source qualifier for {trans_name}")
                lines.append(f"df_{trans_name} = spark.table('UNKNOWN_TABLE')")
        
        return lines
    
    def _translate_expression_simple(self, expression: str) -> str:
        """Simple expression translation for common Informatica patterns.
        
        Args:
            expression: Informatica expression string
            
        Returns:
            PySpark expression string
        """
        import re
        
        # Replace HTML entities
        expr = expression.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
        
        # Handle string concatenation: || -> concat(...)
        # Pattern: match || with spaces around it, but not inside quotes
        # Simple approach: replace || with + for string concatenation
        # But need to handle cases like: FIRST_NAME || ' ' || LAST_NAME
        # This should become: F.concat(F.col('FIRST_NAME'), F.lit(' '), F.col('LAST_NAME'))
        
        # For now, use a simpler approach: replace || with + and wrap in F.expr
        # But first, let's try to handle common patterns
        
        # Handle IIF(condition, true_value, false_value) -> F.when(condition, true_value).otherwise(false_value)
        iif_pattern = r'IIF\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\)'
        def replace_iif(match):
            condition = match.group(1).strip()
            true_val = match.group(2).strip()
            false_val = match.group(3).strip()
            # Handle nested IIF
            if 'IIF' in false_val:
                false_val = self._translate_expression_simple(false_val)
            return f"F.when({condition}, {true_val}).otherwise({false_val})"
        
        expr = re.sub(iif_pattern, replace_iif, expr, flags=re.IGNORECASE)
        
        # Handle string concatenation with ||
        # Replace || with + but need to be careful with quotes and spacing
        # Use regex to replace || with single space + single space, then clean up
        expr = re.sub(r'\s*\|\|\s*', ' + ', expr)
        # Clean up any double spaces that might have been created
        expr = re.sub(r'\s+', ' ', expr)
        
        # Handle common Informatica functions
        expr = re.sub(r'\bUPPER\s*\(', 'F.upper(', expr, flags=re.IGNORECASE)
        expr = re.sub(r'\bLOWER\s*\(', 'F.lower(', expr, flags=re.IGNORECASE)
        expr = re.sub(r'\bTRIM\s*\(', 'F.trim(', expr, flags=re.IGNORECASE)
        expr = re.sub(r'\bLTRIM\s*\(', 'F.ltrim(', expr, flags=re.IGNORECASE)
        expr = re.sub(r'\bRTRIM\s*\(', 'F.rtrim(', expr, flags=re.IGNORECASE)
        expr = re.sub(r'\bLENGTH\s*\(', 'F.length(', expr, flags=re.IGNORECASE)
        expr = re.sub(r'\bSUBSTR\s*\(', 'F.substring(', expr, flags=re.IGNORECASE)
        
        # Wrap column references in F.col() if they're not already wrapped
        # Simple heuristic: if it's an identifier (starts with letter, contains letters/numbers/underscore)
        # and not already in F.col() or F.lit(), wrap it
        # This is complex, so for now we'll use F.expr() which can handle most cases
        
        # Return as F.expr() string for safety
        return f"F.expr('{expr}')"
    
    def _generate_mapplet_instance(self, trans: Dict[str, Any], model: Dict[str, Any]) -> List[str]:
        """Generate code for mapplet instance by inlining transformations.
        
        Args:
            trans: Mapplet instance transformation
            model: Full canonical model
            
        Returns:
            List of code lines for inlined mapplet
        """
        lines = []
        mapplet_ref = trans.get("mapplet_ref", "")
        instance_name = trans.get("name", "")
        input_port_mappings = trans.get("input_port_mappings", {})
        output_port_mappings = trans.get("output_port_mappings", {})
        
        logger.info(f"Inlining mapplet {mapplet_ref} for instance {instance_name}")
        
        # Resolve mapplet reference
        mapplet_data = self._resolve_mapplet(mapplet_ref)
        if not mapplet_data:
            lines.append(f"# ERROR: Mapplet '{mapplet_ref}' not found - manual intervention required")
            lines.append(f"# Placeholder for mapplet instance: {instance_name}")
            return lines
        
        lines.append(f"# Inline mapplet: {mapplet_ref} (instance: {instance_name})")
        
        # Map input ports: create a temporary DataFrame with mapplet input columns
        if input_port_mappings:
            lines.append(f"# Map input ports to mapplet")
            mapplet_input_cols = []
            for mapplet_input_port, mapping_info in input_port_mappings.items():
                from_trans = mapping_info.get("from_transformation", "")
                from_port = mapping_info.get("from_port", "")
                if from_trans and from_port:
                    # Use the column from the source transformation
                    col_expr = f"F.col('{from_port}').alias('{mapplet_input_port}')"
                    mapplet_input_cols.append(col_expr)
            
            if mapplet_input_cols:
                lines.append(f"df_mapplet_input = df.select({', '.join(mapplet_input_cols)})")
                lines.append("df = df_mapplet_input")
        
        # Inline mapplet transformations
        mapplet_transformations = mapplet_data.get("transformations", [])
        for mapplet_trans in mapplet_transformations:
            mapplet_trans_type = mapplet_trans.get("type", "")
            
            if mapplet_trans_type == "EXPRESSION":
                lines.extend(self._generate_expression(mapplet_trans))
            elif mapplet_trans_type == "LOOKUP":
                lines.extend(self._generate_lookup(mapplet_trans))
            elif mapplet_trans_type == "JOINER":
                lines.extend(self._generate_joiner(mapplet_trans))
            elif mapplet_trans_type == "AGGREGATOR":
                lines.extend(self._generate_aggregator(mapplet_trans))
            elif mapplet_trans_type == "FILTER":
                lines.extend(self._generate_filter(mapplet_trans))
            elif mapplet_trans_type == "ROUTER":
                lines.extend(self._generate_router(mapplet_trans))
            elif mapplet_trans_type == "SORTER":
                lines.extend(self._generate_sorter(mapplet_trans))
            elif mapplet_trans_type == "RANK":
                lines.extend(self._generate_rank(mapplet_trans))
            elif mapplet_trans_type == "UNION":
                lines.extend(self._generate_union(mapplet_trans))
            elif mapplet_trans_type == "UPDATE_STRATEGY":
                lines.extend(self._generate_update_strategy(mapplet_trans))
        
        # Map output ports: select only the output ports that are connected
        if output_port_mappings:
            lines.append(f"# Map mapplet output ports to target")
            output_cols = []
            for mapplet_output_port, mapping_info in output_port_mappings.items():
                to_trans = mapping_info.get("to_transformation", "")
                to_port = mapping_info.get("to_port", "")
                if to_trans and to_port:
                    # Rename mapplet output to target port name
                    output_cols.append(f"F.col('{mapplet_output_port}').alias('{to_port}')")
            
            if output_cols:
                # Keep all columns and add renamed output columns
                lines.append(f"df = df.select(*[c for c in df.columns if c not in {[p for p in output_port_mappings.keys()]}], "
                           f"{', '.join(output_cols)})")
        
        return lines
    
    def _generate_reusable_transformation_function(self, trans: Dict[str, Any], reusable_name: str) -> List[str]:
        """Generate function definition for reusable transformation.
        
        Args:
            trans: Reusable transformation data
            reusable_name: Name of the reusable transformation
            
        Returns:
            List of code lines for function definition
        """
        lines = []
        trans_type = trans.get("type", "")
        func_name = f"reusable_{reusable_name.lower().replace(' ', '_')}"
        
        lines.append(f"# Reusable Transformation Function: {reusable_name}")
        lines.append(f"def {func_name}(df):")
        lines.append(f'    """Reusable transformation: {reusable_name}"""')
        
        # Generate transformation logic based on type
        if trans_type == "EXPRESSION":
            lines.append("    # Expression transformation logic")
            for port in trans.get("ports", []):
                if port.get("port_type") == "OUTPUT":
                    port_name = port.get("name", "")
                    expression = port.get("expression", "")
                    if expression:
                        lines.append(f'    df = df.withColumn("{port_name}", {expression})')
        elif trans_type == "LOOKUP":
            lines.append("    # Lookup transformation logic")
            lines.append(f'    # TODO: Implement lookup logic for {reusable_name}')
        
        lines.append("    return df")
        lines.append("")
        
        return lines
    
    def _generate_reusable_transformation_call(self, trans: Dict[str, Any], reusable_name: str) -> List[str]:
        """Generate function call for reusable transformation.
        
        Args:
            trans: Transformation instance that uses reusable
            reusable_name: Name of the reusable transformation
            
        Returns:
            List of code lines for function call
        """
        func_name = f"reusable_{reusable_name.lower().replace(' ', '_')}"
        return [
            f"# Call reusable transformation: {reusable_name}",
            f"df = {func_name}(df)",
            ""
        ]
    
    def _resolve_mapplet(self, mapplet_ref: str) -> Optional[Dict[str, Any]]:
        """Resolve mapplet reference.
        
        Args:
            mapplet_ref: Mapplet name to resolve
            
        Returns:
            Mapplet data or None if not found
        """
        # Try to resolve from reference resolver
        try:
            # Register mapping to resolver context if needed
            resolved_mapplets = self.reference_resolver.resolve_mapping_mapplets({
                "transformations": [{"type": "MAPPLET_INSTANCE", "mapplet_ref": mapplet_ref}]
            })
            if mapplet_ref in resolved_mapplets:
                return resolved_mapplets[mapplet_ref]
        except Exception as e:
            logger.warning(f"Could not resolve mapplet {mapplet_ref} from resolver: {e}")
        
        # Try to load from version store
        try:
            version_store = VersionStore()
            mapplet_data = version_store.load(mapplet_ref)
            if mapplet_data:
                return mapplet_data
        except Exception as e:
            logger.warning(f"Could not load mapplet {mapplet_ref} from version store: {e}")
        
        return None
    
    def _generate_custom_transformation(self, trans: Dict[str, Any]) -> List[str]:
        """Generate placeholder code for custom transformation.
        
        Args:
            trans: Custom transformation data
            
        Returns:
            List of code lines with placeholder
        """
        lines = []
        trans_name = trans.get("name", "")
        custom_type = trans.get("custom_type", "Unknown")
        class_name = trans.get("class_name")
        code_reference = trans.get("code_reference") or trans.get("jar_file")
        
        lines.append(f"# ============================================================================")
        lines.append(f"# MANUAL INTERVENTION REQUIRED: Custom Transformation")
        lines.append(f"# ============================================================================")
        lines.append(f"# Transformation: {trans_name}")
        lines.append(f"# Type: {custom_type}")
        if class_name:
            lines.append(f"# Class: {class_name}")
        if code_reference:
            lines.append(f"# Code Reference: {code_reference}")
        lines.append(f"#")
        lines.append(f"# This custom transformation requires manual migration.")
        lines.append(f"# Please review the custom code and implement equivalent logic in PySpark.")
        lines.append(f"#")
        lines.append(f"# Placeholder:")
        lines.append(f"# df = df  # TODO: Implement custom transformation logic for {trans_name}")
        lines.append(f"# ============================================================================")
        
        return lines
    
    def _generate_stored_procedure(self, trans: Dict[str, Any]) -> List[str]:
        """Generate placeholder code for stored procedure.
        
        Args:
            trans: Stored procedure transformation data
            
        Returns:
            List of code lines with placeholder
        """
        lines = []
        trans_name = trans.get("name", "")
        procedure_name = trans.get("procedure_name", "")
        connection = trans.get("connection")
        parameters = trans.get("parameters", [])
        sql_query = trans.get("sql_query")
        
        lines.append(f"# ============================================================================")
        lines.append(f"# MANUAL INTERVENTION REQUIRED: Stored Procedure")
        lines.append(f"# ============================================================================")
        lines.append(f"# Transformation: {trans_name}")
        lines.append(f"# Procedure: {procedure_name}")
        if connection:
            lines.append(f"# Connection: {connection}")
        if parameters:
            lines.append(f"# Parameters: {parameters}")
        if sql_query:
            lines.append(f"# SQL Query: {sql_query}")
        lines.append(f"#")
        lines.append(f"# This stored procedure requires database-specific handling.")
        lines.append(f"# Please review the procedure logic and implement equivalent functionality.")
        lines.append(f"#")
        lines.append(f"# Option 1: Use JDBC to call stored procedure")
        lines.append(f"# df = spark.read.format('jdbc').option('url', 'jdbc:...').option('dbtable', 'CALL {procedure_name}(...)').load()")
        lines.append(f"#")
        lines.append(f"# Option 2: Implement equivalent logic in PySpark")
        lines.append(f"# df = df  # TODO: Implement stored procedure logic for {procedure_name}")
        lines.append(f"# ============================================================================")
        
        return lines
