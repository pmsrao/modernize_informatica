"""SQL Generator — Production Version
Generates SQL code from canonical model.
"""
from typing import Dict, Any, List, Optional
from translator.sql_translator import SQLTranslator
from translator.parser_engine import Parser
from translator.tokenizer import tokenize
from utils.logger import get_logger
from parser.reference_resolver import ReferenceResolver
from versioning.version_store import VersionStore

logger = get_logger(__name__)


class SQLGenerator:
    """Generates SQL code from canonical mapping model."""
    
    def __init__(self, reference_resolver: Optional[ReferenceResolver] = None):
        """Initialize SQL generator.
        
        Args:
            reference_resolver: Optional reference resolver for resolving mapplets
        """
        self.sql_translator = SQLTranslator()
        self.reference_resolver = reference_resolver or ReferenceResolver()
    
    def generate(self, model: Dict[str, Any]) -> str:
        """Generate SQL code from canonical model.
        
        Args:
            model: Canonical model dictionary
            
        Returns:
            Complete SQL code as string
        """
        lines = []
        
        # Generate SELECT statement
        lines.append(f"-- SQL for transformation: {model.get('transformation_name', model.get('mapping_name', 'unknown'))}")
        lines.append("")
        
        # Build SELECT clause
        select_cols = []
        
        # Get columns from transformations
        transformations = model.get("transformations", [])
        for trans in transformations:
            trans_type = trans.get("type", "")
            
            if trans_type == "MAPPLET_INSTANCE":
                # Inline mapplet transformations
                mapplet_cols = self._generate_mapplet_sql(trans, model)
                select_cols.extend(mapplet_cols)
            elif trans_type == "CUSTOM_TRANSFORMATION":
                select_cols.append(f"  -- MANUAL INTERVENTION REQUIRED: Custom Transformation {trans.get('name', '')}")
                select_cols.append(f"  NULL AS \"{trans.get('name', 'custom_col')}\"  -- TODO: Implement custom logic")
            elif trans_type == "STORED_PROCEDURE":
                select_cols.append(f"  -- MANUAL INTERVENTION REQUIRED: Stored Procedure {trans.get('procedure_name', '')}")
                select_cols.append(f"  NULL AS \"{trans.get('name', 'sp_col')}\"  -- TODO: Implement stored procedure logic")
            elif trans_type == "EXPRESSION":
                for port in trans.get("ports", []):
                    if port.get("port_type") == "OUTPUT":
                        port_name = port.get("name", "")
                        expression = port.get("expression", "")
                        if expression:
                            # Try to translate expression to SQL
                            try:
                                tokens = tokenize(expression)
                                parser = Parser(tokens)
                                ast = parser.parse()
                                sql_expr = self.sql_translator.visit(ast)
                                select_cols.append(f"  {sql_expr} AS \"{port_name}\"")
                            except Exception as e:
                                error_msg = str(e)
                                logger.warning(f"Could not translate expression to SQL: {expression} - {error_msg}")
                                select_cols.append(f"  {expression} AS \"{port_name}\"")
        
        # If no expressions, use source columns
        if not select_cols:
            sources = model.get("sources", [])
            for source in sources:
                for field in source.get("fields", []):
                    field_name = field.get("name", "")
                    select_cols.append(f'  "{field_name}"')
        
        # Build FROM clause
        sources = model.get("sources", [])
        if sources:
            first_source = sources[0]
            table_name = first_source.get("table", "")
            database = first_source.get("database", "")
            
            if database:
                from_clause = f"{database}.{table_name}"
            else:
                from_clause = table_name
        else:
            from_clause = "source_table"
        
        # Generate SELECT statement
        if select_cols:
            lines.append("SELECT")
            lines.append(",\n".join(select_cols))
            lines.append(f"FROM {from_clause}")
        else:
            lines.append(f"SELECT * FROM {from_clause}")
        
        # Add WHERE clause if filters exist
        filters = []
        for trans in transformations:
            if trans.get("type") == "FILTER":
                filter_condition = trans.get("filter_condition", "")
                if filter_condition:
                    filters.append(filter_condition)
        
        if filters:
            lines.append("WHERE")
            lines.append(" AND ".join(filters))
        
        # Add GROUP BY if aggregations exist
        group_by_cols = []
        for trans in transformations:
            if trans.get("type") == "AGGREGATOR":
                group_by_cols.extend(trans.get("group_by_ports", []))
        
        if group_by_cols:
            lines.append("GROUP BY")
            lines.append(", ".join([f'"{col}"' for col in group_by_cols]))
        
        # Add ORDER BY if sorter exists
        sort_cols = []
        for trans in transformations:
            if trans.get("type") == "SORTER":
                for key in trans.get("sort_keys", []):
                    port = key.get("port", "")
                    direction = key.get("direction", "ASC")
                    sort_cols.append(f'"{port}" {direction}')
        
        if sort_cols:
            lines.append("ORDER BY")
            lines.append(", ".join(sort_cols))
        
        return "\n".join(lines)
    
    def _generate_mapplet_sql(self, trans: Dict[str, Any], model: Dict[str, Any]) -> List[str]:
        """Generate SQL for mapplet instance by inlining transformations."""
        cols = []
        mapplet_ref = trans.get("mapplet_ref", "")
        
        # Resolve mapplet
        mapplet_data = self._resolve_mapplet(mapplet_ref)
        if not mapplet_data:
            cols.append(f"  -- ERROR: Mapplet '{mapplet_ref}' not found")
            return cols
        
        # Generate SQL for mapplet transformations
        mapplet_transformations = mapplet_data.get("transformations", [])
        for mapplet_trans in mapplet_transformations:
            if mapplet_trans.get("type") == "EXPRESSION":
                for port in mapplet_trans.get("ports", []):
                    if port.get("port_type") == "OUTPUT":
                        port_name = port.get("name", "")
                        expression = port.get("expression", "")
                        if expression:
                            try:
                                tokens = tokenize(expression)
                                parser = Parser(tokens)
                                ast = parser.parse()
                                sql_expr = self.sql_translator.visit(ast)
                                cols.append(f"  {sql_expr} AS \"{port_name}\"")
                            except Exception as e:
                                logger.warning(f"Could not translate mapplet expression to SQL: {expression}")
                                cols.append(f"  {expression} AS \"{port_name}\"")
        
        return cols
    
    def _resolve_mapplet(self, mapplet_ref: str) -> Optional[Dict[str, Any]]:
        """Resolve mapplet reference."""
        try:
            resolved_mapplets = self.reference_resolver.resolve_mapping_mapplets({
                "transformations": [{"type": "MAPPLET_INSTANCE", "mapplet_ref": mapplet_ref}]
            })
            if mapplet_ref in resolved_mapplets:
                return resolved_mapplets[mapplet_ref]
        except Exception as e:
            logger.warning(f"Could not resolve mapplet {mapplet_ref}: {e}")
        
        try:
            version_store = VersionStore()
            return version_store.load(mapplet_ref)
        except Exception:
            return None
    
    def generate_view(self, model: Dict[str, Any], view_name: Optional[str] = None) -> str:
        """Generate CREATE VIEW statement.
        
        Args:
            model: Canonical model dictionary
            view_name: Optional view name (defaults to mapping name)
            
        Returns:
            CREATE VIEW SQL statement
        """
        view_name = view_name or model.get("transformation_name", model.get("mapping_name", "transformation_view"))
        select_sql = self.generate(model)
        
        # Replace SELECT with CREATE VIEW
        lines = select_sql.split("\n")
        lines[0] = f"CREATE OR REPLACE VIEW {view_name} AS"
        lines.insert(1, select_sql.replace("SELECT", "SELECT").replace("--", ""))
        
        return "\n".join(lines)
    
    def generate_ctas(self, model: Dict[str, Any], table_name: Optional[str] = None) -> str:
        """Generate CREATE TABLE AS SELECT (CTAS) statement.
        
        Args:
            model: Canonical model dictionary
            table_name: Optional table name (defaults to mapping name)
            
        Returns:
            CREATE TABLE AS SELECT SQL statement
        """
        table_name = table_name or model.get("transformation_name", model.get("mapping_name", "transformation_table"))
        select_sql = self.generate(model)
        
        # Replace SELECT with CREATE TABLE AS SELECT
        lines = select_sql.split("\n")
        lines[0] = f"CREATE TABLE {table_name} AS"
        lines.insert(1, select_sql.replace("SELECT", "SELECT").replace("--", ""))
        
        return "\n".join(lines)

