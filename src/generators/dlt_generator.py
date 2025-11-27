"""DLT Generator — Production Version
Generates Delta Live Tables pipeline code from canonical model.
"""
from typing import Dict, Any, List


class DLTGenerator:
    """Generates Delta Live Tables pipeline code."""
    
    def generate(self, model: Dict[str, Any]) -> str:
        """Generate DLT pipeline code from canonical model.
        
        Args:
            model: Canonical model dictionary
            
        Returns:
            Complete DLT pipeline code as string
        """
        lines = []
        
        # Imports
        lines.append("import dlt")
        lines.append("from pyspark.sql import functions as F")
        lines.append("from pyspark.sql.types import *")
        lines.append("")
        
        # Generate source tables
        for source in model.get("sources", []):
            lines.extend(self._generate_source_table(source))
            lines.append("")
        
        # Generate transformation tables
        transformations = model.get("transformations", [])
        for trans in transformations:
            trans_type = trans.get("type", "")
            if trans_type in ["EXPRESSION", "AGGREGATOR", "JOINER", "LOOKUP"]:
                lines.extend(self._generate_transformation_table(trans, model))
                lines.append("")
        
        # Generate target tables
        for target in model.get("targets", []):
            lines.extend(self._generate_target_table(target, model))
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_source_table(self, source: Dict[str, Any]) -> List[str]:
        """Generate DLT source table definition."""
        lines = []
        table_name = source.get("table", "").lower()
        source_name = source.get("name", "").lower()
        
        lines.append(f"@dlt.table(name='{table_name}_source')")
        lines.append(f"def {source_name}_source():")
        lines.append(f"    return spark.table('{source.get('table', '')}')")
        
        return lines
    
    def _generate_transformation_table(self, trans: Dict[str, Any], model: Dict[str, Any]) -> List[str]:
        """Generate DLT transformation table."""
        lines = []
        trans_name = trans.get("name", "").lower()
        trans_type = trans.get("type", "")
        
        # Determine if incremental
        is_incremental = len(model.get("incremental_keys", [])) > 0
        
        if is_incremental:
            lines.append(f"@dlt.table(name='{trans_name}')")
            lines.append(f"@dlt.expect_or_drop('valid_key', 'incremental_key IS NOT NULL')")
            lines.append(f"def {trans_name}():")
        else:
            lines.append(f"@dlt.table(name='{trans_name}')")
            lines.append(f"def {trans_name}():")
        
        # Build transformation logic
        if trans_type == "EXPRESSION":
            lines.append("    df = dlt.read('source_table')")
            for port in trans.get("ports", []):
                if port.get("port_type") == "OUTPUT":
                    port_name = port.get("name", "")
                    expression = port.get("expression", "")
                    if expression:
                        lines.append(f"    df = df.withColumn('{port_name}', {expression})")
        
        elif trans_type == "AGGREGATOR":
            lines.append("    df = dlt.read('source_table')")
            group_by_ports = trans.get("group_by_ports", [])
            aggregate_functions = trans.get("aggregate_functions", [])
            if group_by_ports:
                group_cols = [f"F.col('{p}')" for p in group_by_ports]
                agg_exprs = []
                for af in aggregate_functions:
                    func_name = af.get("function", "").upper()
                    port_name = af.get("port", "")
                    agg_exprs.append(f"F.{func_name.lower()}(F.col('{port_name}')).alias('{port_name}')")
                lines.append(f"    df = df.groupBy({', '.join(group_cols)}).agg({', '.join(agg_exprs)})")
        
        elif trans_type == "JOINER":
            lines.append("    df1 = dlt.read('source_table_1')")
            lines.append("    df2 = dlt.read('source_table_2')")
            join_type = trans.get("join_type", "INNER").lower()
            conditions = trans.get("conditions", [])
            if conditions:
                join_condition = " && ".join([
                    f"df1['{c.get('left_port', '')}'] == df2['{c.get('right_port', '')}']"
                    for c in conditions
                ])
                lines.append(f"    df = df1.join(df2, {join_condition}, '{join_type}')")
        
        lines.append("    return df")
        
        return lines
    
    def _generate_target_table(self, target: Dict[str, Any], model: Dict[str, Any]) -> List[str]:
        """Generate DLT target table with expectations."""
        lines = []
        table_name = target.get("table", "").lower()
        target_name = target.get("name", "").lower()
        
        scd_type = model.get("scd_type", "NONE")
        
        # Add table expectations
        lines.append(f"@dlt.table(name='{table_name}')")
        
        # Add expectations based on SCD type
        if scd_type == "SCD2":
            lines.append(f"@dlt.expect('valid_effective_dates', 'effective_from <= effective_to')")
            lines.append(f"@dlt.expect_or_drop('valid_keys', 'business_key IS NOT NULL')")
        
        # Add incremental expectations
        incremental_keys = model.get("incremental_keys", [])
        if incremental_keys:
            for key in incremental_keys:
                lines.append(f"@dlt.expect_or_drop('valid_{key.lower()}', '{key} IS NOT NULL')")
        
        lines.append(f"def {target_name}():")
        
        # Determine source (last transformation or direct source)
        if model.get("transformations"):
            last_trans = model["transformations"][-1]
            lines.append(f"    return dlt.read('{last_trans.get('name', '').lower()}')")
        else:
            first_source = model.get("sources", [{}])[0]
            lines.append(f"    return dlt.read('{first_source.get('name', '').lower()}_source')")
        
        return lines
