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
        
        return transformations
    
    def _parse_source_qualifier(self) -> List[Dict[str, Any]]:
        """Parse Source Qualifier transformations."""
        sqs = []
        for sq in self.root.findall(".//TRANSFORMATION[@TYPE='Source Qualifier']"):
            ports = self._parse_ports(sq)
            sqs.append({
                "type": "SOURCE_QUALIFIER",
                "name": sq.get("NAME", ""),
                "ports": ports,
                "sql_query": get_text(sq, "SQLQUERY"),
                "filter": get_text(sq, "FILTER")
            })
        return sqs
    
    def _parse_expression(self) -> List[Dict[str, Any]]:
        """Parse Expression transformations."""
        expressions = []
        for exp in self.root.findall(".//TRANSFORMATION[@TYPE='Expression']"):
            ports = self._parse_ports(exp)
            expressions.append({
                "type": "EXPRESSION",
                "name": exp.get("NAME", ""),
                "ports": ports
            })
        return expressions
    
    def _parse_lookup(self) -> List[Dict[str, Any]]:
        """Parse Lookup transformations."""
        lookups = []
        for lkp in self.root.findall(".//TRANSFORMATION[@TYPE='Lookup']"):
            ports = self._parse_ports(lkp)
            lookup_type = "connected" if lkp.get("CONNECTED", "NO") == "YES" else "unconnected"
            cache_type = get_text(lkp, "CACHETYPE") or "none"
            
            # Parse lookup condition
            condition = None
            cond_elem = lkp.find(".//LOOKUPCONDITION")
            if cond_elem is not None:
                condition = {
                    "source_port": get_text(cond_elem, "SOURCEPORT"),
                    "lookup_port": get_text(cond_elem, "LOOKUPPORT"),
                    "operator": get_text(cond_elem, "OPERATOR")
                }
            
            lookups.append({
                "type": "LOOKUP",
                "name": lkp.get("NAME", ""),
                "lookup_type": lookup_type,
                "cache_type": cache_type,
                "ports": ports,
                "condition": condition,
                "table_name": get_text(lkp, "TABLENAME"),
                "connection": get_text(lkp, "CONNECTION")
            })
        return lookups
    
    def _parse_aggregator(self) -> List[Dict[str, Any]]:
        """Parse Aggregator transformations."""
        aggregators = []
        for agg in self.root.findall(".//TRANSFORMATION[@TYPE='Aggregator']"):
            ports = self._parse_ports(agg)
            
            # Parse group by ports
            group_by_ports = []
            for gb in agg.findall(".//GROUPBY"):
                group_by_ports.append(gb.get("NAME", ""))
            
            # Parse aggregate functions
            aggregate_functions = []
            for af in agg.findall(".//AGGREGATEFUNCTION"):
                aggregate_functions.append({
                    "port": af.get("NAME", ""),
                    "function": af.get("FUNCTION", ""),
                    "expression": get_text(af, "EXPRESSION")
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
            from_trans = get_text(conn, "FROMTRANSFORMATION")
            to_trans = get_text(conn, "TOTRANSFORMATION")
            from_port = get_text(conn, "FROMPORT")
            to_port = get_text(conn, "TOPORT")
            
            connectors.append({
                "from_transformation": from_trans,
                "to_transformation": to_trans,
                "from_port": from_port,
                "to_port": to_port
            })
        return connectors
