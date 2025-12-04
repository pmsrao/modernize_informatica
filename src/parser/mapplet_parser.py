"""Mapplet Parser - Production Grade
Parses Informatica Mapplet XML files into structured model.
Mapplets are reusable sets of transformations that can be embedded into multiple mappings.
"""
import lxml.etree as ET
from typing import Dict, List, Any, Optional
from parser.xml_utils import get_text
from utils.exceptions import ParsingError
from utils.logger import get_logger

logger = get_logger(__name__)


class MappletParser:
    """Parser for Informatica Mapplet XML files."""
    
    def __init__(self, path: str):
        """Initialize parser with XML file path."""
        logger.info(f"Initializing mapplet parser for file: {path}")
        try:
            # Use recover mode to handle malformed XML (e.g., unescaped < in attributes)
            parser = ET.XMLParser(recover=True)
            self.tree = ET.parse(path, parser=parser)
            self.root = self.tree.getroot()
            logger.debug(f"Successfully loaded XML file: {path}")
        except ET.XMLSyntaxError as e:
            logger.error(f"Invalid XML syntax in file: {path}", error=e)
            raise ParsingError(
                f"Invalid XML file: {e}",
                file_path=path
            ) from e
        except FileNotFoundError as e:
            logger.error(f"Mapplet file not found: {path}", error=e)
            raise ParsingError(
                f"Mapplet file not found: {path}",
                file_path=path
            ) from e
    
    def parse(self) -> Dict[str, Any]:
        """Parse mapplet XML and return structured model.
        
        Mapplets have:
        - Input ports (INPUT elements)
        - Output ports (OUTPUT elements)
        - Transformations (same as mappings)
        - Connectors between transformations
        
        Returns:
            Dictionary with mapplet structure
        """
        mapplet_elem = self.root if self.root.tag == "MAPPLET" else self.root.find(".//MAPPLET")
        
        if mapplet_elem is None:
            raise ParsingError("MAPPLET element not found in XML")
        
        mapplet_name = mapplet_elem.get("NAME", "")
        logger.info(f"Parsing mapplet: {mapplet_name}")
        
        try:
            # Parse input/output ports (these are the interface)
            input_ports = self._parse_input_ports(mapplet_elem)
            output_ports = self._parse_output_ports(mapplet_elem)
            
            # Parse transformations (reuse mapping parser logic)
            transformations = self._parse_transformations(mapplet_elem)
            
            # Parse connectors
            connectors = self._parse_connectors(mapplet_elem)
            
            mapplet = {
                "name": mapplet_name,
                "source_component_type": "mapplet",
                "type": "MAPPLET",
                "input_ports": input_ports,
                "output_ports": output_ports,
                "transformations": transformations,
                "connectors": connectors
            }
            
            logger.info(f"Successfully parsed mapplet: {mapplet_name} with {len(transformations)} transformations")
            return mapplet
            
        except Exception as e:
            logger.error(f"Error parsing mapplet: {mapplet_name}", error=e)
            raise
    
    def _parse_input_ports(self, element: ET.Element) -> List[Dict[str, Any]]:
        """Parse INPUT ports from mapplet."""
        ports = []
        for port in element.findall(".//INPUT"):
            ports.append({
                "name": port.get("NAME", ""),
                "datatype": port.get("DATATYPE", ""),
                "precision": port.get("PRECISION"),
                "scale": port.get("SCALE")
            })
        logger.debug(f"Parsed {len(ports)} input ports")
        return ports
    
    def _parse_output_ports(self, element: ET.Element) -> List[Dict[str, Any]]:
        """Parse OUTPUT ports from mapplet."""
        ports = []
        for port in element.findall(".//OUTPUT"):
            ports.append({
                "name": port.get("NAME", ""),
                "datatype": port.get("DATATYPE", ""),
                "precision": port.get("PRECISION"),
                "scale": port.get("SCALE")
            })
        logger.debug(f"Parsed {len(ports)} output ports")
        return ports
    
    def _parse_transformations(self, element: ET.Element) -> List[Dict[str, Any]]:
        """Parse transformations (reuse mapping parser methods).
        
        Mapplets contain the same transformation types as mappings.
        """
        transformations = []
        
        # Source Qualifier
        transformations.extend(self._parse_source_qualifier(element))
        
        # Expression
        transformations.extend(self._parse_expression(element))
        
        # Lookup
        transformations.extend(self._parse_lookup(element))
        
        # Aggregator
        transformations.extend(self._parse_aggregator(element))
        
        # Joiner
        transformations.extend(self._parse_joiner(element))
        
        # Router
        transformations.extend(self._parse_router(element))
        
        # Filter
        transformations.extend(self._parse_filter(element))
        
        # Sorter
        transformations.extend(self._parse_sorter(element))
        
        # Rank
        transformations.extend(self._parse_rank(element))
        
        # Union
        transformations.extend(self._parse_union(element))
        
        # Normalizer
        transformations.extend(self._parse_normalizer(element))
        
        # Update Strategy
        transformations.extend(self._parse_update_strategy(element))
        
        # Custom/Java transformations
        transformations.extend(self._parse_custom_transformation(element))
        
        return transformations
    
    def _parse_source_qualifier(self, element: ET.Element) -> List[Dict[str, Any]]:
        """Parse Source Qualifier transformations.
        
        Handles both 'Source Qualifier' (with space) and 'SourceQualifier' (no space) formats.
        """
        sqs = []
        # Try both formats: with space and without space
        for sq in element.findall(".//TRANSFORMATION[@TYPE='Source Qualifier']") + \
                   element.findall(".//TRANSFORMATION[@TYPE='SourceQualifier']"):
            ports = self._parse_ports(sq)
            
            # Get SQL query from ATTRIBUTE or SQLQUERY element
            sql_query = sq.get("Sql Query", "") or get_text(sq, "SQLQUERY")
            if not sql_query:
                # Try to get from ATTRIBUTE element
                attr_elem = sq.find(".//ATTRIBUTE[@NAME='Sql Query']")
                if attr_elem is not None:
                    sql_query = attr_elem.get("VALUE", "")
            
            sqs.append({
                "type": "SOURCE_QUALIFIER",
                "name": sq.get("NAME", ""),
                "ports": ports,
                "sql_query": sql_query,
                "filter": get_text(sq, "FILTER")
            })
        return sqs
    
    def _parse_expression(self, element: ET.Element) -> List[Dict[str, Any]]:
        """Parse Expression transformations."""
        expressions = []
        for exp in element.findall(".//TRANSFORMATION[@TYPE='Expression']"):
            ports = self._parse_ports(exp)
            
            # Also parse TRANSFORMFIELD elements
            for tf in exp.findall(".//TRANSFORMFIELD"):
                field_name = tf.get("NAME", "")
                field_expr = tf.get("EXPR", "")
                if field_name and field_expr:
                    existing_port = next((p for p in ports if p.get("name") == field_name), None)
                    if existing_port:
                        existing_port["expression"] = field_expr
                    else:
                        ports.append({
                            "name": field_name,
                            "port_type": "OUTPUT",
                            "expression": field_expr
                        })
            
            expressions.append({
                "type": "EXPRESSION",
                "name": exp.get("NAME", ""),
                "ports": ports
            })
        return expressions
    
    def _parse_lookup(self, element: ET.Element) -> List[Dict[str, Any]]:
        """Parse Lookup transformations."""
        lookups = []
        for lkp in element.findall(".//TRANSFORMATION[@TYPE='Lookup']"):
            ports = self._parse_ports(lkp)
            lookup_type = "connected" if lkp.get("CONNECTED", "NO") == "YES" else "unconnected"
            cache_type = get_text(lkp, "CACHETYPE") or "none"
            
            condition = None
            cond_elem = lkp.find(".//LOOKUPCONDITION")
            if cond_elem is not None:
                condition = {
                    "source_port": get_text(cond_elem, "SOURCEPORT"),
                    "lookup_port": get_text(cond_elem, "LOOKUPPORT"),
                    "operator": get_text(cond_elem, "OPERATOR")
                }
            
            table_name = get_text(lkp, "TABLENAME")
            if not table_name:
                lookup_table_elem = lkp.find(".//LOOKUPTABLE")
                if lookup_table_elem is not None:
                    table_name = lookup_table_elem.get("NAME", "")
            
            lookups.append({
                "type": "LOOKUP",
                "name": lkp.get("NAME", ""),
                "lookup_type": lookup_type,
                "cache_type": cache_type,
                "ports": ports,
                "condition": condition,
                "table_name": table_name or "",
                "connection": get_text(lkp, "CONNECTION")
            })
        return lookups
    
    def _parse_aggregator(self, element: ET.Element) -> List[Dict[str, Any]]:
        """Parse Aggregator transformations."""
        aggregators = []
        for agg in element.findall(".//TRANSFORMATION[@TYPE='Aggregator']"):
            ports = self._parse_ports(agg)
            
            group_by_ports = []
            for gb in agg.findall(".//GROUPBY"):
                group_by_ports.append(gb.get("NAME", ""))
            for gbf in agg.findall(".//GROUPBYFIELD"):
                field_name = gbf.get("NAME", "")
                if field_name and field_name not in group_by_ports:
                    group_by_ports.append(field_name)
            
            aggregate_functions = []
            for af in agg.findall(".//AGGREGATEFUNCTION"):
                aggregate_functions.append({
                    "port": af.get("NAME", ""),
                    "function": af.get("FUNCTION", ""),
                    "expression": get_text(af, "EXPRESSION")
                })
            
            for tf in agg.findall(".//TRANSFORMFIELD"):
                field_name = tf.get("NAME", "")
                field_expr = tf.get("EXPR", "")
                if field_name and field_expr:
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
    
    def _parse_joiner(self, element: ET.Element) -> List[Dict[str, Any]]:
        """Parse Joiner transformations."""
        joiners = []
        for join in element.findall(".//TRANSFORMATION[@TYPE='Joiner']"):
            ports = self._parse_ports(join)
            join_type = get_text(join, "JOINTYPE") or "INNER"
            
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
    
    def _parse_router(self, element: ET.Element) -> List[Dict[str, Any]]:
        """Parse Router transformations."""
        routers = []
        for router in element.findall(".//TRANSFORMATION[@TYPE='Router']"):
            ports = self._parse_ports(router)
            
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
    
    def _parse_filter(self, element: ET.Element) -> List[Dict[str, Any]]:
        """Parse Filter transformations."""
        filters = []
        for filt in element.findall(".//TRANSFORMATION[@TYPE='Filter']"):
            ports = self._parse_ports(filt)
            filter_condition = get_text(filt, "FILTERCONDITION")
            filters.append({
                "type": "FILTER",
                "name": filt.get("NAME", ""),
                "ports": ports,
                "filter_condition": filter_condition
            })
        return filters
    
    def _parse_sorter(self, element: ET.Element) -> List[Dict[str, Any]]:
        """Parse Sorter transformations."""
        sorters = []
        for sorter in element.findall(".//TRANSFORMATION[@TYPE='Sorter']"):
            ports = self._parse_ports(sorter)
            
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
    
    def _parse_rank(self, element: ET.Element) -> List[Dict[str, Any]]:
        """Parse Rank transformations."""
        ranks = []
        for rank in element.findall(".//TRANSFORMATION[@TYPE='Rank']"):
            ports = self._parse_ports(rank)
            top_bottom = get_text(rank, "TOPBOTTOM") or "TOP"
            rank_count = get_text(rank, "RANKCOUNT") or "1"
            
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
    
    def _parse_union(self, element: ET.Element) -> List[Dict[str, Any]]:
        """Parse Union transformations."""
        unions = []
        for union in element.findall(".//TRANSFORMATION[@TYPE='Union']"):
            ports = self._parse_ports(union)
            unions.append({
                "type": "UNION",
                "name": union.get("NAME", ""),
                "ports": ports
            })
        return unions
    
    def _parse_normalizer(self, element: ET.Element) -> List[Dict[str, Any]]:
        """Parse Normalizer transformations."""
        normalizers = []
        for norm in element.findall(".//TRANSFORMATION[@TYPE='Normalizer']"):
            ports = self._parse_ports(norm)
            normalizers.append({
                "type": "NORMALIZER",
                "name": norm.get("NAME", ""),
                "ports": ports
            })
        return normalizers
    
    def _parse_update_strategy(self, element: ET.Element) -> List[Dict[str, Any]]:
        """Parse Update Strategy transformations.
        
        Handles both 'Update Strategy' (with space) and 'UpdateStrategy' (no space) formats.
        """
        update_strategies = []
        # Try both formats: with space and without space
        for us in element.findall(".//TRANSFORMATION[@TYPE='Update Strategy']") + \
                   element.findall(".//TRANSFORMATION[@TYPE='UpdateStrategy']"):
            ports = self._parse_ports(us)
            
            # Get update strategy expression from ATTRIBUTE or UPDATESTRATEGYEXPRESSION element
            update_strategy_expr = get_text(us, "UPDATESTRATEGYEXPRESSION")
            if not update_strategy_expr:
                # Try to get from ATTRIBUTE element
                attr_elem = us.find(".//ATTRIBUTE[@NAME='Update Strategy Expression']")
                if attr_elem is not None:
                    update_strategy_expr = attr_elem.get("VALUE", "")
            
            update_strategies.append({
                "type": "UPDATE_STRATEGY",
                "name": us.get("NAME", ""),
                "ports": ports,
                "update_strategy_expression": update_strategy_expr
            })
        return update_strategies
    
    def _parse_custom_transformation(self, element: ET.Element) -> List[Dict[str, Any]]:
        """Parse Custom/Java transformations."""
        custom_transforms = []
        for custom in element.findall(".//TRANSFORMATION[@TYPE='Custom']"):
            ports = self._parse_ports(custom)
            custom_transforms.append({
                "type": "CUSTOM_TRANSFORMATION",
                "name": custom.get("NAME", ""),
                "ports": ports,
                "requires_manual_intervention": True,
                "manual_intervention_reason": "Custom transformation requires manual code review and migration",
                "custom_type": get_text(custom, "CUSTOMTYPE") or "Unknown",
                "code_reference": get_text(custom, "CODEREFERENCE") or None,
                "class_name": get_text(custom, "CLASSNAME") or None
            })
        
        # Also check for Java transformations
        for java in element.findall(".//TRANSFORMATION[@TYPE='Java']"):
            ports = self._parse_ports(java)
            custom_transforms.append({
                "type": "CUSTOM_TRANSFORMATION",
                "name": java.get("NAME", ""),
                "ports": ports,
                "requires_manual_intervention": True,
                "manual_intervention_reason": "Java transformation requires manual code review and migration",
                "custom_type": "Java",
                "code_reference": get_text(java, "CODEREFERENCE") or None,
                "class_name": get_text(java, "CLASSNAME") or None
            })
        
        return custom_transforms
    
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
            
            expr = get_text(port, "EXPRESSION")
            if expr:
                port_info["expression"] = expr
            
            ports.append(port_info)
        return ports
    
    def _parse_connectors(self, element: ET.Element) -> List[Dict[str, Any]]:
        """Parse connector definitions (data flow between transformations)."""
        connectors = []
        for conn in element.findall(".//CONNECTOR"):
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
        
        logger.debug(f"Parsed {len(connectors)} connectors")
        return connectors

