"""PySpark Generator — Production Version
Generates PySpark DataFrame code from canonical model.
"""
from typing import Dict, Any, List
from utils.logger import get_logger

logger = get_logger(__name__)


class PySparkGenerator:
    """Generates PySpark code from canonical mapping model."""
    
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
            model.get("mapping_name", "InformaticaMapping")))
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
        
        # Process transformations in order
        transformations = model.get("transformations", [])
        for trans in transformations:
            trans_type = trans.get("type", "")
            trans_name = trans.get("name", "")
            
            if trans_type == "EXPRESSION":
                lines.extend(self._generate_expression(trans))
            elif trans_type == "LOOKUP":
                lines.extend(self._generate_lookup(trans))
            elif trans_type == "JOINER":
                lines.extend(self._generate_joiner(trans))
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
        lines.append(f"lookup_df = spark.table('{table_name}')")
        
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
    
    def _generate_joiner(self, trans: Dict[str, Any]) -> List[str]:
        """Generate code for Joiner transformation."""
        lines = []
        lines.append(f"# Joiner: {trans.get('name', '')}")
        
        join_type = trans.get("join_type", "INNER").lower()
        conditions = trans.get("conditions", [])
        
        if conditions:
            join_condition = " && ".join([
                f"df1['{c.get('left_port', '')}'] == df2['{c.get('right_port', '')}']"
                for c in conditions
            ])
            lines.append(f"df = df1.join(df2, {join_condition}, '{join_type}')")
        
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
        
        # Build group by columns
        if group_by_ports:
            group_cols = [f"F.col('{p}')" for p in group_by_ports]
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
            else:
                # Global aggregate (no group by)
                lines.append(f"df = df.agg({', '.join(agg_exprs)})")
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
