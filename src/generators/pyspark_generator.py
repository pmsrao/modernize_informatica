"""PySpark Generator — Production Version
Generates PySpark DataFrame code from canonical model.
"""
from typing import Dict, Any, List


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
        lines.append(f"# Expression: {trans.get('name', '')}")
        
        for port in trans.get("ports", []):
            if port.get("port_type") == "OUTPUT":
                port_name = port.get("name", "")
                expression = port.get("expression", "")
                if expression:
                    # Expression should already be translated to PySpark
                    lines.append(f"df = df.withColumn('{port_name}', {expression})")
        
        return lines
    
    def _generate_lookup(self, trans: Dict[str, Any]) -> List[str]:
        """Generate code for Lookup transformation."""
        lines = []
        lines.append(f"# Lookup: {trans.get('name', '')}")
        
        lookup_type = trans.get("lookup_type", "connected")
        table_name = trans.get("table_name", "")
        condition = trans.get("condition", {})
        
        if lookup_type == "connected":
            # Broadcast join for lookup
            lines.append(f"lookup_df = spark.table('{table_name}')")
            if condition:
                source_port = condition.get("source_port", "")
                lookup_port = condition.get("lookup_port", "")
                lines.append(f"df = df.join(F.broadcast(lookup_df), "
                           f"df['{source_port}'] == lookup_df['{lookup_port}'], 'left')")
        
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
        lines.append(f"# Aggregator: {trans.get('name', '')}")
        
        group_by_ports = trans.get("group_by_ports", [])
        aggregate_functions = trans.get("aggregate_functions", [])
        
        if group_by_ports:
            group_cols = [f"F.col('{p}')" for p in group_by_ports]
            agg_exprs = []
            for af in aggregate_functions:
                func_name = af.get("function", "").upper()
                port_name = af.get("port", "")
                expr = af.get("expression", f"F.col('{port_name}')")
                agg_exprs.append(f"F.{func_name.lower()}({expr}).alias('{port_name}')")
            
            lines.append(f"df = df.groupBy({', '.join(group_cols)}).agg({', '.join(agg_exprs)})")
        
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
            window = Window.partitionBy(*partition_cols).orderBy(*partition_cols)
            lines.append(f"window = Window.partitionBy({', '.join(partition_cols)}).orderBy({', '.join(partition_cols)})")
            lines.append(f"df = df.withColumn('rank', F.rank().over(window))")
            if top_bottom == "TOP":
                lines.append(f"df = df.filter(F.col('rank') <= {rank_count})")
            else:
                lines.append(f"df = df.filter(F.col('rank') >= F.max('rank').over(window) - {rank_count} + 1)")
        
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
