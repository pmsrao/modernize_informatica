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
        transformation_name = model.get("transformation_name", model.get("mapping_name", "Unknown"))
        logger.info(f"[DEBUG] Starting code generation for: {transformation_name}")
        logger.debug(f"[DEBUG] Model keys: {list(model.keys())}")
        logger.debug(f"[DEBUG] Sources count: {len(model.get('sources', []))}")
        logger.debug(f"[DEBUG] Targets count: {len(model.get('targets', []))}")
        logger.debug(f"[DEBUG] Transformations count: {len(model.get('transformations', []))}")
        
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
        sources = model.get("sources", [])
        logger.debug(f"[DEBUG] Processing {len(sources)} sources")
        lines.append("# Read source tables")
        for source in sources:
            source_name = source.get("name", "")
            table_name = source.get("table", "")
            database = source.get("database", "")
            logger.debug(f"[DEBUG] Source: name={source_name}, table={table_name}, database={database}")
            
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
        logger.debug(f"[DEBUG] Total transformations: {len(transformations)}")
        for trans in transformations:
            trans_type = trans.get("type", "UNKNOWN")
            trans_name = trans.get("name", "UNKNOWN")
            logger.debug(f"[DEBUG] Transformation: {trans_name} (type: {trans_type})")
            if trans.get("type") == "SOURCE_QUALIFIER":
                source_qualifiers.append(trans)
            else:
                other_transformations.append(trans)
        
        logger.debug(f"[DEBUG] Source qualifiers: {len(source_qualifiers)}, Other transformations: {len(other_transformations)}")
        
        # Process Source Qualifiers first
        for trans in source_qualifiers:
            trans_name = trans.get("name", "UNKNOWN")
            logger.debug(f"[DEBUG] Processing source qualifier: {trans_name}")
            sq_lines = self._generate_source_qualifier(trans)
            logger.debug(f"[DEBUG] Generated {len(sq_lines)} lines for source qualifier {trans_name}")
            if sq_lines:
                logger.debug(f"[DEBUG] Source qualifier code preview: {sq_lines[:3] if len(sq_lines) >= 3 else sq_lines}")
            lines.extend(sq_lines)
            lines.append("")
        
        # Set base DataFrame to first source qualifier if available
        if source_qualifiers:
            first_sq = source_qualifiers[0]
            sq_name = first_sq.get("name", "UNKNOWN")
            logger.debug(f"[DEBUG] Setting base DataFrame to: df_{sq_name}")
            lines.append("# Start with base DataFrame from first source qualifier")
            lines.append(f"df = df_{sq_name}")
            lines.append("")
        elif model.get("sources"):
            # Fallback to first source if no source qualifiers
            first_source = model["sources"][0]
            logger.debug(f"[DEBUG] Setting base DataFrame to first source: {first_source.get('name', 'source')}")
            lines.append("# Start with base DataFrame from first source")
            lines.append(f"df = df_{first_source.get('name', 'source')}")
            lines.append("")
        else:
            logger.warning(f"[DEBUG] No source qualifiers and no sources found for {transformation_name}")
        
        # Process other transformations in order
        logger.debug(f"[DEBUG] Processing {len(other_transformations)} other transformations")
        for trans in other_transformations:
            trans_type = trans.get("type", "")
            trans_name = trans.get("name", "")
            logger.debug(f"[DEBUG] Processing transformation: {trans_name} (type: {trans_type})")
            
            try:
                # Check if this is a reusable transformation
                if trans.get("is_reusable", False):
                    reusable_name = trans.get("reusable_name", trans_name)
                    reusable_transforms[reusable_name] = trans
                    # Generate as function on first encounter
                    trans_lines = self._generate_reusable_transformation_function(trans, reusable_name)
                    lines.extend(trans_lines)
                    lines.append("")
                
                trans_lines = []
                if trans_type == "MAPPLET_INSTANCE":
                    logger.debug(f"[DEBUG] Generating MAPPLET_INSTANCE: {trans_name}")
                    trans_lines = self._generate_mapplet_instance(trans, model)
                elif trans_type == "CUSTOM_TRANSFORMATION":
                    logger.debug(f"[DEBUG] Generating CUSTOM_TRANSFORMATION: {trans_name}")
                    trans_lines = self._generate_custom_transformation(trans)
                elif trans_type == "STORED_PROCEDURE":
                    logger.debug(f"[DEBUG] Generating STORED_PROCEDURE: {trans_name}")
                    trans_lines = self._generate_stored_procedure(trans)
                elif trans_type == "EXPRESSION":
                    logger.debug(f"[DEBUG] Generating EXPRESSION: {trans_name}")
                    # Check if reusable - if so, call function instead of generating inline
                    if trans.get("is_reusable", False):
                        reusable_name = trans.get("reusable_name", trans_name)
                        trans_lines = self._generate_reusable_transformation_call(trans, reusable_name)
                    else:
                        trans_lines = self._generate_expression(trans)
                elif trans_type == "LOOKUP":
                    logger.debug(f"[DEBUG] Generating LOOKUP: {trans_name}")
                    # Check if reusable
                    if trans.get("is_reusable", False):
                        reusable_name = trans.get("reusable_name", trans_name)
                        trans_lines = self._generate_reusable_transformation_call(trans, reusable_name)
                    else:
                        trans_lines = self._generate_lookup(trans, model)
                elif trans_type == "JOINER":
                    logger.debug(f"[DEBUG] Generating JOINER: {trans_name}")
                    trans_lines = self._generate_joiner(trans, model)
                elif trans_type == "AGGREGATOR":
                    logger.debug(f"[DEBUG] Generating AGGREGATOR: {trans_name}")
                    trans_lines = self._generate_aggregator(trans)
                elif trans_type == "FILTER":
                    logger.debug(f"[DEBUG] Generating FILTER: {trans_name}")
                    trans_lines = self._generate_filter(trans)
                elif trans_type == "ROUTER":
                    logger.debug(f"[DEBUG] Generating ROUTER: {trans_name}")
                    trans_lines = self._generate_router(trans)
                elif trans_type == "SORTER":
                    logger.debug(f"[DEBUG] Generating SORTER: {trans_name}")
                    trans_lines = self._generate_sorter(trans)
                elif trans_type == "RANK":
                    logger.debug(f"[DEBUG] Generating RANK: {trans_name}")
                    trans_lines = self._generate_rank(trans)
                elif trans_type == "UNION":
                    logger.debug(f"[DEBUG] Generating UNION: {trans_name}")
                    trans_lines = self._generate_union(trans)
                elif trans_type == "UPDATE_STRATEGY":
                    logger.debug(f"[DEBUG] Generating UPDATE_STRATEGY: {trans_name}")
                    trans_lines = self._generate_update_strategy(trans)
                elif trans_type == "SOURCE_QUALIFIER":
                    logger.debug(f"[DEBUG] Generating SOURCE_QUALIFIER: {trans_name}")
                    trans_lines = self._generate_source_qualifier(trans)
                else:
                    logger.warning(f"[DEBUG] Unknown transformation type: {trans_type} for {trans_name}")
                    trans_lines = [f"# TODO: Implement transformation {trans_name} (type: {trans_type})"]
                
                # Add transformation code if generated
                if trans_lines:
                    logger.debug(f"[DEBUG] Generated {len(trans_lines)} lines for {trans_name}")
                    lines.extend(trans_lines)
                    lines.append("")
                else:
                    logger.warning(f"[DEBUG] No code generated for transformation {trans_name} (type: {trans_type})")
                    lines.append(f"# TODO: Code generation failed for {trans_name} (type: {trans_type})")
                    lines.append("")
            except Exception as e:
                logger.error(f"[DEBUG] Error generating code for transformation {trans_name} (type: {trans_type}): {e}", exc_info=True)
                lines.append(f"# ERROR: Failed to generate code for {trans_name}: {str(e)}")
                lines.append("")
        
        # Write to target
        targets = model.get("targets", [])
        logger.debug(f"[DEBUG] Processing {len(targets)} targets")
        lines.append("# Write to target table")
        for target in targets:
            target_name = target.get("name", "")
            table_name = target.get("table", "")
            database = target.get("database", "")
            logger.debug(f"[DEBUG] Target: name={target_name}, table={table_name}, database={database}")
            
            if database:
                full_table = f"{database}.{table_name}"
            else:
                full_table = table_name if table_name else target_name
            
            # Check for SCD type
            scd_type = model.get("scd_type", "NONE")
            logger.debug(f"[DEBUG] SCD type: {scd_type}")
            if scd_type == "SCD2":
                lines.append(f"# SCD2 merge operation")
                lines.append(f"df.write.format('delta').mode('overwrite').saveAsTable('{full_table}')")
            else:
                lines.append(f"df.write.format('delta').mode('overwrite').saveAsTable('{full_table}')")
        
        result_code = "\n".join(lines)
        logger.info(f"[DEBUG] Code generation completed for {transformation_name}. Generated {len(result_code.split(chr(10)))} lines")
        logger.debug(f"[DEBUG] Generated code preview (first 10 lines):\n{chr(10).join(result_code.split(chr(10))[:10])}")
        return result_code
    
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
    
    def _generate_lookup(self, trans: Dict[str, Any], model: Dict[str, Any] = None) -> List[str]:
        """Generate code for Lookup transformation.
        
        Args:
            trans: Lookup transformation
            model: Optional canonical model to extract table name from connectors/attributes
        """
        lines = []
        trans_name = trans.get('name', '')
        lines.append(f"# Lookup: {trans_name}")
        
        lookup_type = trans.get("lookup_type", "connected")
        table_name = trans.get("table_name", "")
        condition = trans.get("condition", {})
        
        # Try to extract table name from transformation name pattern (LK_TABLENAME -> TABLENAME)
        if not table_name and trans_name.startswith("LK_"):
            # Common pattern: LK_CUSTOMER_KEY -> DIM_CUSTOMER or CUSTOMER
            potential_table = trans_name[3:]  # Remove "LK_" prefix
            # Try common dimension table patterns
            if "KEY" in potential_table:
                base_name = potential_table.replace("_KEY", "").replace("KEY", "")
                # Try dimension table naming: DIM_<name>
                table_name = f"DIM_{base_name}"
            else:
                table_name = potential_table
        
        # Try to extract from attributes or ports if available
        if not table_name:
            # Check for lookup table in attributes (from Informatica XML parsing)
            attrs = trans.get("attributes", {})
            if attrs:
                table_name = (attrs.get("Lookup Table") or 
                            attrs.get("lookup_table") or
                            attrs.get("table_name"))
        
        # Try to infer from connectors if model provided
        if not table_name and model:
            connectors = model.get("connectors", [])
            # Look for connectors that might indicate lookup table
            # This is a fallback - ideally table_name should be in transformation spec
            pass  # Connectors don't directly contain table names
        
        if not table_name:
            # Generate placeholder code with inferred table name
            inferred_table = f"DIM_{trans_name[3:] if trans_name.startswith('LK_') else 'LOOKUP_TABLE'}"
            if trans_name.startswith("LK_") and "_KEY" in trans_name:
                base_name = trans_name[3:].replace("_KEY", "").replace("KEY", "")
                inferred_table = f"DIM_{base_name}"
            
            lines.append(f"# Lookup table name inferred from transformation name: {trans_name} -> {inferred_table}")
            lines.append(f"# TODO: Verify table name matches actual lookup table in Informatica mapping")
            table_name = inferred_table
        
        # Broadcast join for lookup (both connected and unconnected can be joined)
        # Lookup tables are typically small and benefit from broadcast join
        lines.append(f"lookup_df_{trans_name} = spark.table('{table_name}')")
        lines.append(f"# Performance optimization: Using broadcast join for lookup table")
        lines.append(f"# Broadcast join is efficient for small lookup tables (< 100MB)")
        
        # Build join condition
        join_condition = None
        if condition:
            source_port = condition.get("source_port", "")
            lookup_port = condition.get("lookup_port", "")
            operator = condition.get("operator", "=")
            if source_port and lookup_port:
                if operator == "=":
                    join_condition = f"df['{source_port}'] == lookup_df_{trans_name}['{lookup_port}']"
                else:
                    join_condition = f"df['{source_port}'] {operator} lookup_df_{trans_name}['{lookup_port}']"
        
        # If no explicit condition, try to infer from transformation name pattern
        if not join_condition:
            # Common pattern: LK_CUSTOMER_KEY -> join on CUSTOMER_ID
            if trans_name.startswith("LK_") and "_KEY" in trans_name:
                base_name = trans_name[3:].replace("_KEY", "").replace("KEY", "")
                # Try common key patterns
                key_field = f"{base_name}_ID"
                join_condition = f"df['{key_field}'] == lookup_df_{trans_name}['{key_field}']"
                lines.append(f"# Join condition inferred from transformation name pattern")
                lines.append(f"# TODO: Verify join condition matches actual lookup condition")
            else:
                # Generic placeholder
                join_condition = "df['key'] == lookup_df_{trans_name}['key']"
                lines.append(f"# Join condition not specified - using placeholder")
                lines.append(f"# TODO: Update join condition based on actual lookup specification")
        
        # Generate join
        lines.append(f"df = df.join(F.broadcast(lookup_df_{trans_name}), {join_condition}, 'left')")
        
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
        join_conditions_from_connectors = []
        
        if model:
            connectors = model.get("connectors", [])
            # Find connectors that feed into this joiner
            input_connectors = [c for c in connectors if c.get("to_transformation") == trans_name]
            
            if len(input_connectors) >= 2:
                # Use first two input transformations as join sources
                df1_name = input_connectors[0].get("from_transformation", "")
                df2_name = input_connectors[1].get("from_transformation", "")
                
                # Extract join conditions from connectors
                # Look for matching ports between the two input connectors
                port1 = input_connectors[0].get("from_port", "")
                port2 = input_connectors[1].get("from_port", "")
                to_port1 = input_connectors[0].get("to_port", "")
                to_port2 = input_connectors[1].get("to_port", "")
                
                # If both connectors have the same to_port, that's the join key
                # Use from_port if available, otherwise use to_port
                if to_port1 and to_port1 == to_port2:
                    join_key = to_port1
                    left_port = port1 if port1 else join_key
                    right_port = port2 if port2 else join_key
                    join_conditions_from_connectors.append({
                        "left_port": left_port,
                        "right_port": right_port
                    })
                # If ports match, use them
                elif port1 and port2 and port1 == port2:
                    join_conditions_from_connectors.append({
                        "left_port": port1,
                        "right_port": port2
                    })
                # Otherwise, try to use available ports
                elif port1 and port2:
                    join_conditions_from_connectors.append({
                        "left_port": port1,
                        "right_port": port2
                    })
                elif to_port1 and to_port2:
                    # Use to_ports as fallback
                    join_conditions_from_connectors.append({
                        "left_port": to_port1,
                        "right_port": to_port2
                    })
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
        
        # Use conditions from transformation if available, otherwise use connectors
        if conditions and any(c.get("left_port") and c.get("right_port") for c in conditions):
            # Use transformation conditions if they have valid ports
            join_condition = " && ".join([
                f"{df1_var}['{c.get('left_port', '')}'] == {df2_var}['{c.get('right_port', '')}']"
                for c in conditions if c.get("left_port") and c.get("right_port")
            ])
        elif join_conditions_from_connectors:
            # Use conditions extracted from connectors
            join_condition = " && ".join([
                f"{df1_var}['{c.get('left_port', '')}'] == {df2_var}['{c.get('right_port', '')}']"
                for c in join_conditions_from_connectors if c.get("left_port") and c.get("right_port")
            ])
        else:
            join_condition = None
        
        if join_condition:
            if use_broadcast:
                lines.append(f"# Using broadcast join for small right table (optimization)")
                lines.append(f"{df2_var}_broadcast = F.broadcast({df2_var})")
                lines.append(f"df_{trans_name} = {df1_var}.join({df2_var}_broadcast, {join_condition}, '{join_type}')")
            else:
                lines.append(f"df_{trans_name} = {df1_var}.join({df2_var}, {join_condition}, '{join_type}')")
                lines.append(f"# Performance hint: Consider broadcast join if {df2_var} is small (< 100MB)")
        else:
            lines.append(f"# Join conditions not fully specified for {trans_name}")
            lines.append(f"# TODO: Extract join condition from connectors or transformation ports")
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
        
        logger.debug(f"[DEBUG] _generate_source_qualifier: {trans_name}")
        logger.debug(f"[DEBUG] SQL query: {sql_query[:100] if sql_query else 'None'}...")
        logger.debug(f"[DEBUG] Filter condition: {filter_condition}")
        
        # Priority 1: If SQL query exists, use it directly (most accurate)
        # This handles complex queries with WHERE clauses, JOINs, etc.
        if sql_query:
            logger.debug(f"[DEBUG] Using SQL query for source qualifier {trans_name}")
            lines.append(f"# Source Qualifier: {trans_name}")
            # Escape triple quotes in SQL query if present
            escaped_sql = sql_query.replace('"""', '\\"\\"\\"')
            lines.append(f"df_{trans_name} = spark.sql(\"\"\"{escaped_sql}\"\"\")")
            
            # Apply additional filter if present (rare, but possible)
            if filter_condition:
                lines.append(f"df_{trans_name} = df_{trans_name}.filter({filter_condition})")
            logger.debug(f"[DEBUG] Generated {len(lines)} lines for source qualifier {trans_name}")
            return lines
        
        # Priority 2: Try to extract table name from transformation name
        # Source Qualifiers often follow pattern: SQ_TABLENAME
        table_name = None
        if trans_name.startswith("SQ_"):
            # Try to extract table name from SQ_ prefix
            potential_table = trans_name[3:]  # Remove "SQ_" prefix
            table_name = potential_table
            logger.debug(f"[DEBUG] Extracted table name from transformation name: {table_name}")
        
        if table_name:
            # Generate DataFrame read from table
            logger.debug(f"[DEBUG] Using table name for source qualifier {trans_name}: {table_name}")
            lines.append(f"# Source Qualifier: {trans_name}")
            lines.append(f"df_{trans_name} = spark.table('{table_name}')")
            
            # Apply filter if present
            if filter_condition:
                lines.append(f"df_{trans_name} = df_{trans_name}.filter({filter_condition})")
        else:
            # Last resort: placeholder with warning
            logger.warning(f"[DEBUG] No SQL query or table name found for source qualifier {trans_name}")
            lines.append(f"# Source Qualifier: {trans_name}")
            lines.append(f"# TODO: Implement source qualifier for {trans_name}")
            lines.append(f"# No SQL query or table name found - please specify source")
            lines.append(f"df_{trans_name} = spark.table('UNKNOWN_TABLE')")
        
        logger.debug(f"[DEBUG] Final generated lines for source qualifier {trans_name}: {len(lines)}")
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
                lines.extend(self._generate_lookup(mapplet_trans, model))
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
    
    def generate_mapplet_function(self, mapplet_data: Dict[str, Any]) -> List[str]:
        """Generate standalone function for a mapplet (reusable transformation).
        
        Args:
            mapplet_data: Mapplet canonical model dictionary
            
        Returns:
            List of code lines for mapplet function
        """
        lines = []
        mapplet_name = mapplet_data.get("name", "unknown_mapplet")
        func_name = f"mapplet_{mapplet_name.lower().replace(' ', '_').replace('-', '_')}"
        
        # Function signature with input ports as parameters
        input_ports = mapplet_data.get("input_ports", [])
        if input_ports:
            # Create DataFrame from input ports
            port_params = [f"{port.get('name', '')}: str" for port in input_ports]
            lines.append(f"def {func_name}(df, **kwargs):")
        else:
            lines.append(f"def {func_name}(df):")
        
        lines.append(f'    """Mapplet: {mapplet_name}')
        lines.append(f'    ')
        if input_ports:
            lines.append(f'    Input ports: {", ".join([p.get("name", "") for p in input_ports])}')
        output_ports = mapplet_data.get("output_ports", [])
        if output_ports:
            lines.append(f'    Output ports: {", ".join([p.get("name", "") for p in output_ports])}')
        lines.append(f'    """')
        lines.append("")
        
        # Map input ports if needed
        if input_ports:
            lines.append("    # Map input ports from DataFrame")
            for port in input_ports:
                port_name = port.get("name", "")
                if port_name:
                    lines.append(f"    # Input port: {port_name}")
        
        # Generate transformations within mapplet
        transformations = mapplet_data.get("transformations", [])
        for trans in transformations:
            trans_type = trans.get("type", "")
            trans_name = trans.get("name", "")
            
            lines.append(f"    # Transformation: {trans_name} ({trans_type})")
            
            if trans_type == "EXPRESSION":
                trans_lines = self._generate_expression(trans)
                # Indent all lines
                lines.extend([f"    {line}" if line.strip() else "" for line in trans_lines])
            elif trans_type == "LOOKUP":
                trans_lines = self._generate_lookup(trans, mapplet_data)
                lines.extend([f"    {line}" if line.strip() else "" for line in trans_lines])
            elif trans_type == "JOINER":
                trans_lines = self._generate_joiner(trans, mapplet_data)
                lines.extend([f"    {line}" if line.strip() else "" for line in trans_lines])
            elif trans_type == "AGGREGATOR":
                trans_lines = self._generate_aggregator(trans)
                lines.extend([f"    {line}" if line.strip() else "" for line in trans_lines])
            elif trans_type == "FILTER":
                trans_lines = self._generate_filter(trans)
                lines.extend([f"    {line}" if line.strip() else "" for line in trans_lines])
            elif trans_type == "ROUTER":
                trans_lines = self._generate_router(trans)
                lines.extend([f"    {line}" if line.strip() else "" for line in trans_lines])
            elif trans_type == "SORTER":
                trans_lines = self._generate_sorter(trans)
                lines.extend([f"    {line}" if line.strip() else "" for line in trans_lines])
            elif trans_type == "RANK":
                trans_lines = self._generate_rank(trans)
                lines.extend([f"    {line}" if line.strip() else "" for line in trans_lines])
            elif trans_type == "UNION":
                trans_lines = self._generate_union(trans)
                lines.extend([f"    {line}" if line.strip() else "" for line in trans_lines])
            elif trans_type == "UPDATE_STRATEGY":
                trans_lines = self._generate_update_strategy(trans)
                lines.extend([f"    {line}" if line.strip() else "" for line in trans_lines])
            
            lines.append("")
        
        # Return DataFrame with output ports
        if output_ports:
            lines.append("    # Return DataFrame with output ports")
            output_cols = [f"F.col('{port.get('name', '')}')" for port in output_ports if port.get("name")]
            if output_cols:
                lines.append(f"    return df.select({', '.join(output_cols)})")
            else:
                lines.append("    return df")
        else:
            lines.append("    return df")
        
        lines.append("")
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
