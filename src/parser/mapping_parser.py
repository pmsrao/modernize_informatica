"""Mapping Parser - Production Grade
Parses Informatica mapping XML into structured model with all transformation types.
"""
import lxml.etree as ET
from typing import Dict, List, Any, Optional
from parser.xml_utils import get_text
from utils.exceptions import ParsingError
from utils.logger import get_logger

logger = get_logger(__name__)


class MappingParser:
    """Parser for Informatica Mapping XML files."""
    
    def __init__(self, path: str):
        """Initialize parser with XML file path."""
        logger.info(f"Initializing mapping parser for file: {path}")
        try:
            self.tree = ET.parse(path)
            self.root = self.tree.getroot()
            logger.debug(f"Successfully loaded XML file: {path}")
        except ET.XMLSyntaxError as e:
            logger.error(f"Invalid XML syntax in file: {path}", error=e)
            raise ParsingError(
                f"Invalid XML file: {e}",
                file_path=path
            ) from e
        except FileNotFoundError as e:
            logger.error(f"Mapping file not found: {path}", error=e)
            raise ParsingError(
                f"Mapping file not found: {path}",
                file_path=path
            ) from e
    
    def parse(self) -> Dict[str, Any]:
        """Parse mapping XML and return structured model."""
        logger.info(f"Parsing mapping: {self.root.get('NAME', 'unknown')}")
        
        try:
            mapping = {
                "name": self.root.get("NAME", ""),
                "source_component_type": "mapping",
                "sources": [],
                "targets": [],
                "transformations": [],
                "connectors": []
            }
            
            # Parse sources
            mapping["sources"] = self._parse_sources()
            logger.debug(f"Parsed {len(mapping['sources'])} sources")
            
            # Parse targets
            mapping["targets"] = self._parse_targets()
            logger.debug(f"Parsed {len(mapping['targets'])} targets")
            
            # Parse all transformation types
            mapping["transformations"] = self._parse_transformations()
            logger.debug(f"Parsed {len(mapping['transformations'])} transformations")
            
            # Parse connectors (data flow connections)
            mapping["connectors"] = self._parse_connectors()
            logger.debug(f"Parsed {len(mapping['connectors'])} connectors")
            
            logger.info(f"Successfully parsed mapping: {mapping['name']}")
            return mapping
            
        except Exception as e:
            logger.error(f"Error parsing mapping XML", error=e)
            raise ParsingError(
                f"Failed to parse mapping: {str(e)}",
                file_path=getattr(self, 'path', None)
            ) from e
    
    def _parse_sources(self) -> List[Dict[str, Any]]:
        """Parse source definitions."""
        sources = []
        for src in self.root.findall(".//SOURCE"):
            table_elem = src.find(".//TABLE")
            fields = []
            for field in src.findall(".//FIELD"):
                fields.append({
                    "name": field.get("NAME", ""),
                    "datatype": field.get("DATATYPE", ""),
                    "precision": field.get("PRECISION"),
                    "scale": field.get("SCALE")
                })
            sources.append({
                "name": src.get("NAME", ""),
                "table": table_elem.get("NAME", "") if table_elem is not None else "",
                "database": get_text(src, "DATABASENAME"),
                "fields": fields
            })
        return sources
    
    def _parse_targets(self) -> List[Dict[str, Any]]:
        """Parse target definitions."""
        targets = []
        for tgt in self.root.findall(".//TARGET"):
            table_elem = tgt.find(".//TABLE")
            fields = []
            for field in tgt.findall(".//FIELD"):
                fields.append({
                    "name": field.get("NAME", ""),
                    "datatype": field.get("DATATYPE", ""),
                    "precision": field.get("PRECISION"),
                    "scale": field.get("SCALE")
                })
            targets.append({
                "name": tgt.get("NAME", ""),
                "table": table_elem.get("NAME", "") if table_elem is not None else "",
                "database": get_text(tgt, "DATABASENAME"),
                "fields": fields
            })
        return targets
    
    def _parse_transformations(self) -> List[Dict[str, Any]]:
        """Parse all transformation types."""
        transformations = []
        
        # Mapplet instances (must be parsed first to detect them)
        transformations.extend(self._parse_mapplet_instance())
        
        # Source Qualifier
        transformations.extend(self._parse_source_qualifier())
        
        # Expression
        transformations.extend(self._parse_expression())
        
        # Lookup
        transformations.extend(self._parse_lookup())
        
        # Aggregator
        transformations.extend(self._parse_aggregator())
        
        # Joiner
        transformations.extend(self._parse_joiner())
        
        # Router
        transformations.extend(self._parse_router())
        
        # Filter
        transformations.extend(self._parse_filter())
        
        # Sorter
        transformations.extend(self._parse_sorter())
        
        # Rank
        transformations.extend(self._parse_rank())
        
        # Union
        transformations.extend(self._parse_union())
        
        # Normalizer
        transformations.extend(self._parse_normalizer())
        
        # Update Strategy
        transformations.extend(self._parse_update_strategy())
        
        # Custom/Java transformations
        transformations.extend(self._parse_custom_transformation())
        
        # Stored procedures
        transformations.extend(self._parse_stored_procedure())
        
        return transformations
    
    def _parse_source_qualifier(self) -> List[Dict[str, Any]]:
        """Parse Source Qualifier transformations."""
        sqs = []
        for sq in self.root.findall(".//TRANSFORMATION[@TYPE='Source Qualifier']"):
            ports = self._parse_ports(sq)
            sq_name = sq.get("NAME", "")
            # If NAME is empty, try to derive from source name or use default
            if not sq_name:
                # Try to find associated source
                source_name = sq.get("SOURCE", "") or get_text(sq, "SOURCE")
                if source_name:
                    sq_name = f"SQ_{source_name}"
                else:
                    sq_name = f"SQ_{len(sqs) + 1}"
                logger.warning(f"Source Qualifier missing NAME attribute, using: {sq_name}")
            
            sqs.append({
                "type": "SOURCE_QUALIFIER",
                "name": sq_name,
                "ports": ports,
                "sql_query": get_text(sq, "SQLQUERY"),
                "filter": get_text(sq, "FILTER")
            })
            logger.debug(f"Parsed Source Qualifier: {sq_name}")
        return sqs
    
    def _parse_expression(self) -> List[Dict[str, Any]]:
        """Parse Expression transformations."""
        expressions = []
        for exp in self.root.findall(".//TRANSFORMATION[@TYPE='Expression']"):
            ports = self._parse_ports(exp)
            
            # Check if transformation is reusable
            is_reusable = exp.get("REUSABLE", "NO") == "YES"
            reusable_name = exp.get("REUSABLENAME", "") if is_reusable else None
            
            # Also parse TRANSFORMFIELD elements (used in Expression transformations)
            for tf in exp.findall(".//TRANSFORMFIELD"):
                field_name = tf.get("NAME", "")
                field_expr = tf.get("EXPR", "")
                if field_name and field_expr:
                    # Add as output port with expression
                    port_info = {
                        "name": field_name,
                        "port_type": "OUTPUT",
                        "expression": field_expr
                    }
                    # Check if port already exists (from PORT element)
                    existing_port = next((p for p in ports if p.get("name") == field_name), None)
                    if existing_port:
                        existing_port["expression"] = field_expr
                    else:
                        ports.append(port_info)
            
            expr_dict = {
                "type": "EXPRESSION",
                "name": exp.get("NAME", ""),
                "ports": ports
            }
            
            # Add reusable transformation metadata
            if is_reusable:
                expr_dict["is_reusable"] = True
                expr_dict["reusable_name"] = reusable_name or exp.get("NAME", "")
                logger.debug(f"Found reusable transformation: {expr_dict['reusable_name']}")
            
            expressions.append(expr_dict)
        return expressions
    
    def _parse_lookup(self) -> List[Dict[str, Any]]:
        """Parse Lookup transformations."""
        lookups = []
        for lkp in self.root.findall(".//TRANSFORMATION[@TYPE='Lookup']"):
            ports = self._parse_ports(lkp)
            lookup_type = "connected" if lkp.get("CONNECTED", "NO") == "YES" else "unconnected"
            cache_type = get_text(lkp, "CACHETYPE") or "none"
            
            # Check if transformation is reusable
            is_reusable = lkp.get("REUSABLE", "NO") == "YES"
            reusable_name = lkp.get("REUSABLENAME", "") if is_reusable else None
            
            # Parse lookup condition
            condition = None
            cond_elem = lkp.find(".//LOOKUPCONDITION")
            if cond_elem is not None:
                condition = {
                    "source_port": get_text(cond_elem, "SOURCEPORT"),
                    "lookup_port": get_text(cond_elem, "LOOKUPPORT"),
                    "operator": get_text(cond_elem, "OPERATOR")
                }
            
            # Get lookup table name from LOOKUPTABLE element or TABLENAME attribute
            table_name = get_text(lkp, "TABLENAME")
            if not table_name:
                lookup_table_elem = lkp.find(".//LOOKUPTABLE")
                if lookup_table_elem is not None:
                    table_name = lookup_table_elem.get("NAME", "")
            
            lookup_dict = {
                "type": "LOOKUP",
                "name": lkp.get("NAME", ""),
                "lookup_type": lookup_type,
                "cache_type": cache_type,
                "ports": ports,
                "condition": condition,
                "table_name": table_name or "",
                "connection": get_text(lkp, "CONNECTION")
            }
            
            # Add reusable transformation metadata
            if is_reusable:
                lookup_dict["is_reusable"] = True
                lookup_dict["reusable_name"] = reusable_name or lkp.get("NAME", "")
                logger.debug(f"Found reusable lookup transformation: {lookup_dict['reusable_name']}")
            
            lookups.append(lookup_dict)
        return lookups
    
    def _parse_aggregator(self) -> List[Dict[str, Any]]:
        """Parse Aggregator transformations."""
        aggregators = []
        for agg in self.root.findall(".//TRANSFORMATION[@TYPE='Aggregator']"):
            ports = self._parse_ports(agg)
            
            # Parse group by ports - check both GROUPBY and GROUPBYFIELD elements
            group_by_ports = []
            for gb in agg.findall(".//GROUPBY"):
                group_by_ports.append(gb.get("NAME", ""))
            # Also check GROUPBYFIELD elements
            for gbf in agg.findall(".//GROUPBYFIELD"):
                field_name = gbf.get("NAME", "")
                if field_name and field_name not in group_by_ports:
                    group_by_ports.append(field_name)
            
            # Parse aggregate functions - check both AGGREGATEFUNCTION and TRANSFORMFIELD
            aggregate_functions = []
            for af in agg.findall(".//AGGREGATEFUNCTION"):
                aggregate_functions.append({
                    "port": af.get("NAME", ""),
                    "function": af.get("FUNCTION", ""),
                    "expression": get_text(af, "EXPRESSION")
                })
            
            # Also parse TRANSFORMFIELD elements for aggregate expressions (e.g., SUM(SALES_AMT))
            for tf in agg.findall(".//TRANSFORMFIELD"):
                field_name = tf.get("NAME", "")
                field_expr = tf.get("EXPR", "")
                if field_name and field_expr:
                    # Extract function name from expression (e.g., SUM, AVG, COUNT, etc.)
                    expr_upper = field_expr.upper()
                    func_name = None
                    for func in ["SUM", "AVG", "COUNT", "MAX", "MIN", "STDDEV", "VARIANCE"]:
                        if expr_upper.startswith(func + "("):
                            func_name = func
                            break
                    
                    if func_name:
                        aggregate_functions.append({
                            "function": func_name,
                            "port": field_name,
                            "expression": field_expr
                        })
            
            aggregators.append({
                "type": "AGGREGATOR",
                "name": agg.get("NAME", ""),
                "ports": ports,
                "group_by_ports": group_by_ports,
                "aggregate_functions": aggregate_functions
            })
        return aggregators
    
    def _parse_joiner(self) -> List[Dict[str, Any]]:
        """Parse Joiner transformations."""
        joiners = []
        for join in self.root.findall(".//TRANSFORMATION[@TYPE='Joiner']"):
            ports = self._parse_ports(join)
            join_type = get_text(join, "JOINTYPE") or "INNER"
            
            # Parse join conditions
            conditions = []
            for cond in join.findall(".//JOINCONDITION"):
                conditions.append({
                    "left_port": get_text(cond, "LEFTPORT"),
                    "right_port": get_text(cond, "RIGHTPORT"),
                    "operator": get_text(cond, "OPERATOR")
                })
            
            joiners.append({
                "type": "JOINER",
                "name": join.get("NAME", ""),
                "join_type": join_type,
                "ports": ports,
                "conditions": conditions
            })
        return joiners
    
    def _parse_router(self) -> List[Dict[str, Any]]:
        """Parse Router transformations."""
        routers = []
        for router in self.root.findall(".//TRANSFORMATION[@TYPE='Router']"):
            ports = self._parse_ports(router)
            
            # Parse router groups (output groups)
            groups = []
            for group in router.findall(".//ROUTERGROUP"):
                filter_condition = get_text(group, "FILTERCONDITION")
                groups.append({
                    "name": group.get("NAME", ""),
                    "filter_condition": filter_condition
                })
            
            routers.append({
                "type": "ROUTER",
                "name": router.get("NAME", ""),
                "ports": ports,
                "groups": groups
            })
        return routers
    
    def _parse_filter(self) -> List[Dict[str, Any]]:
        """Parse Filter transformations."""
        filters = []
        for filt in self.root.findall(".//TRANSFORMATION[@TYPE='Filter']"):
            ports = self._parse_ports(filt)
            filter_condition = get_text(filt, "FILTERCONDITION")
            filters.append({
                "type": "FILTER",
                "name": filt.get("NAME", ""),
                "ports": ports,
                "filter_condition": filter_condition
            })
        return filters
    
    def _parse_sorter(self) -> List[Dict[str, Any]]:
        """Parse Sorter transformations."""
        sorters = []
        for sorter in self.root.findall(".//TRANSFORMATION[@TYPE='Sorter']"):
            ports = self._parse_ports(sorter)
            
            # Parse sort keys
            sort_keys = []
            for key in sorter.findall(".//SORTKEY"):
                sort_keys.append({
                    "port": key.get("NAME", ""),
                    "direction": key.get("DIRECTION", "ASC")
                })
            
            sorters.append({
                "type": "SORTER",
                "name": sorter.get("NAME", ""),
                "ports": ports,
                "sort_keys": sort_keys
            })
        return sorters
    
    def _parse_rank(self) -> List[Dict[str, Any]]:
        """Parse Rank transformations."""
        ranks = []
        for rank in self.root.findall(".//TRANSFORMATION[@TYPE='Rank']"):
            ports = self._parse_ports(rank)
            top_bottom = get_text(rank, "TOPBOTTOM") or "TOP"
            rank_count = get_text(rank, "RANKCOUNT") or "1"
            
            # Parse rank keys
            rank_keys = []
            for key in rank.findall(".//RANKKEY"):
                rank_keys.append({
                    "port": key.get("NAME", ""),
                    "direction": key.get("DIRECTION", "ASC")
                })
            
            ranks.append({
                "type": "RANK",
                "name": rank.get("NAME", ""),
                "ports": ports,
                "top_bottom": top_bottom,
                "rank_count": rank_count,
                "rank_keys": rank_keys
            })
        return ranks
    
    def _parse_union(self) -> List[Dict[str, Any]]:
        """Parse Union transformations."""
        unions = []
        for union in self.root.findall(".//TRANSFORMATION[@TYPE='Union']"):
            ports = self._parse_ports(union)
            unions.append({
                "type": "UNION",
                "name": union.get("NAME", ""),
                "ports": ports
            })
        return unions
    
    def _parse_normalizer(self) -> List[Dict[str, Any]]:
        """Parse Normalizer transformations."""
        normalizers = []
        for norm in self.root.findall(".//TRANSFORMATION[@TYPE='Normalizer']"):
            ports = self._parse_ports(norm)
            normalizers.append({
                "type": "NORMALIZER",
                "name": norm.get("NAME", ""),
                "ports": ports
            })
        return normalizers
    
    def _parse_update_strategy(self) -> List[Dict[str, Any]]:
        """Parse Update Strategy transformations."""
        update_strategies = []
        for us in self.root.findall(".//TRANSFORMATION[@TYPE='Update Strategy']"):
            ports = self._parse_ports(us)
            update_strategy_expr = get_text(us, "UPDATESTRATEGYEXPRESSION")
            update_strategies.append({
                "type": "UPDATE_STRATEGY",
                "name": us.get("NAME", ""),
                "ports": ports,
                "update_strategy_expression": update_strategy_expr
            })
        return update_strategies
    
    def _parse_ports(self, transformation: ET.Element) -> List[Dict[str, Any]]:
        """Parse input/output ports from a transformation."""
        ports = []
        for port in transformation.findall(".//PORT"):
            port_info = {
                "name": port.get("NAME", ""),
                "datatype": port.get("DATATYPE", ""),
                "precision": port.get("PRECISION"),
                "scale": port.get("SCALE"),
                "port_type": port.get("PORTTYPE", "INPUT/OUTPUT")
            }
            
            # Get expression if it exists
            expr = get_text(port, "EXPRESSION")
            if expr:
                port_info["expression"] = expr
            
            ports.append(port_info)
        return ports
    
    def _parse_connectors(self) -> List[Dict[str, Any]]:
        """Parse connector definitions (data flow between transformations)."""
        connectors = []
        for conn in self.root.findall(".//CONNECTOR"):
            # Try FROMINSTANCE/TOINSTANCE first (Informatica format)
            from_trans = conn.get("FROMINSTANCE") or get_text(conn, "FROMTRANSFORMATION") or get_text(conn, "FROMINSTANCE")
            to_trans = conn.get("TOINSTANCE") or get_text(conn, "TOTRANSFORMATION") or get_text(conn, "TOINSTANCE")
            from_port = conn.get("FROMFIELD") or get_text(conn, "FROMPORT") or get_text(conn, "FROMFIELD")
            to_port = conn.get("TOFIELD") or get_text(conn, "TOPORT") or get_text(conn, "TOFIELD")
            
            if from_trans and to_trans:
                connectors.append({
                    "from_transformation": from_trans,
                    "to_transformation": to_trans,
                    "from_port": from_port,
                    "to_port": to_port
                })
                logger.debug(f"Parsed connector: {from_trans} -> {to_trans}")
        
        logger.info(f"Parsed {len(connectors)} connectors")
        return connectors
    
    def _parse_mapplet_instance(self) -> List[Dict[str, Any]]:
        """Parse mapplet instances in mapping.
        
        Mapplet instances are INSTANCE elements with MAPPLETNAME attribute.
        They reference reusable mapplets that need to be resolved and inlined.
        """
        instances = []
        for inst in self.root.findall(".//INSTANCE[@MAPPLETNAME]"):
            mapplet_name = inst.get("MAPPLETNAME", "")
            instance_name = inst.get("NAME", "")
            
            # Parse input port connections
            input_connections = {}
            for input_conn in inst.findall(".//MAPPLETINPUTINSTANCE"):
                input_port = input_conn.get("PORTNAME", "")
                from_trans = input_conn.get("FROMINSTANCE", "")
                from_port = input_conn.get("FROMFIELD", "")
                if input_port and from_trans:
                    input_connections[input_port] = {
                        "from_transformation": from_trans,
                        "from_port": from_port
                    }
            
            # Parse output port connections
            output_connections = {}
            for output_conn in inst.findall(".//MAPPLETOUTPUTINSTANCE"):
                output_port = output_conn.get("PORTNAME", "")
                to_trans = output_conn.get("TOINSTANCE", "")
                to_port = output_conn.get("TOFIELD", "")
                if output_port and to_trans:
                    output_connections[output_port] = {
                        "to_transformation": to_trans,
                        "to_port": to_port
                    }
            
            instances.append({
                "type": "MAPPLET_INSTANCE",
                "name": instance_name,
                "mapplet_ref": mapplet_name,
                "input_port_mappings": input_connections,
                "output_port_mappings": output_connections
            })
            logger.debug(f"Parsed mapplet instance: {instance_name} referencing {mapplet_name}")
        
        return instances
    
    def _parse_custom_transformation(self) -> List[Dict[str, Any]]:
        """Parse Custom/Java transformations.
        
        These require manual intervention as they contain custom code
        that cannot be automatically translated.
        """
        custom_transforms = []
        
        # Custom transformations
        for custom in self.root.findall(".//TRANSFORMATION[@TYPE='Custom']"):
            ports = self._parse_ports(custom)
            custom_transforms.append({
                "type": "CUSTOM_TRANSFORMATION",
                "name": custom.get("NAME", ""),
                "ports": ports,
                "requires_manual_intervention": True,
                "manual_intervention_reason": "Custom transformation requires manual code review and migration",
                "custom_type": get_text(custom, "CUSTOMTYPE") or "Unknown",
                "code_reference": get_text(custom, "CODEREFERENCE") or None,
                "class_name": get_text(custom, "CLASSNAME") or None,
                "jar_file": get_text(custom, "JARFILE") or None
            })
            logger.warning(f"Found custom transformation: {custom.get('NAME', '')} - requires manual intervention")
        
        # Java transformations
        for java in self.root.findall(".//TRANSFORMATION[@TYPE='Java']"):
            ports = self._parse_ports(java)
            custom_transforms.append({
                "type": "CUSTOM_TRANSFORMATION",
                "name": java.get("NAME", ""),
                "ports": ports,
                "requires_manual_intervention": True,
                "manual_intervention_reason": "Java transformation requires manual code review and migration",
                "custom_type": "Java",
                "code_reference": get_text(java, "CODEREFERENCE") or None,
                "class_name": get_text(java, "CLASSNAME") or None,
                "jar_file": get_text(java, "JARFILE") or None
            })
            logger.warning(f"Found Java transformation: {java.get('NAME', '')} - requires manual intervention")
        
        return custom_transforms
    
    def _parse_stored_procedure(self) -> List[Dict[str, Any]]:
        """Parse stored procedure calls.
        
        Stored procedures may appear in:
        - Source Qualifier SQL queries (CALL statements)
        - Expression transformations (procedure calls)
        - Dedicated Stored Procedure transformations
        
        These require database-specific handling and may need manual intervention.
        """
        stored_procs = []
        
        # Check for Stored Procedure transformation type
        for sp in self.root.findall(".//TRANSFORMATION[@TYPE='Stored Procedure']"):
            ports = self._parse_ports(sp)
            procedure_name = get_text(sp, "PROCEDURENAME") or sp.get("NAME", "")
            connection = get_text(sp, "CONNECTION") or get_text(sp, "CONNECTIONNAME")
            
            # Parse parameters
            parameters = []
            for param in sp.findall(".//PARAMETER"):
                parameters.append({
                    "name": param.get("NAME", ""),
                    "data_type": param.get("DATATYPE", ""),
                    "direction": param.get("DIRECTION", "INPUT"),  # INPUT, OUTPUT, INPUTOUTPUT
                    "value": get_text(param, "VALUE")
                })
            
            stored_procs.append({
                "type": "STORED_PROCEDURE",
                "name": sp.get("NAME", ""),
                "ports": ports,
                "requires_manual_intervention": True,
                "manual_intervention_reason": "Stored procedure requires database-specific handling and may need manual migration",
                "procedure_name": procedure_name,
                "connection": connection,
                "parameters": parameters,
                "return_type": get_text(sp, "RETURNTYPE") or "resultset"
            })
            logger.warning(f"Found stored procedure: {procedure_name} - may require manual intervention")
        
        # Also check Source Qualifier for CALL statements in SQL
        for sq in self.root.findall(".//TRANSFORMATION[@TYPE='Source Qualifier']"):
            sql_query = get_text(sq, "SQLQUERY")
            if sql_query and ("CALL" in sql_query.upper() or "EXEC" in sql_query.upper() or "EXECUTE" in sql_query.upper()):
                # Extract procedure name from SQL
                import re
                call_match = re.search(r'(?:CALL|EXEC|EXECUTE)\s+(\w+)', sql_query, re.IGNORECASE)
                if call_match:
                    procedure_name = call_match.group(1)
                    stored_procs.append({
                        "type": "STORED_PROCEDURE",
                        "name": f"{sq.get('NAME', 'SQ')}_SP_CALL",
                        "ports": self._parse_ports(sq),
                        "requires_manual_intervention": True,
                        "manual_intervention_reason": "Stored procedure call in Source Qualifier SQL requires database-specific handling",
                        "procedure_name": procedure_name,
                        "connection": get_text(sq, "CONNECTION"),
                        "sql_query": sql_query,
                        "source_transformation": sq.get("NAME", "")
                    })
                    logger.warning(f"Found stored procedure call in Source Qualifier: {procedure_name} - may require manual intervention")
        
        return stored_procs
