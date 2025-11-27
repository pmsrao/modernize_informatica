"""DAG Visualizer — Enhanced with multiple output formats."""
from typing import Dict, List, Any, Optional
import json
from utils.logger import get_logger

logger = get_logger(__name__)


class DAGVisualizer:
    """Visualizes DAG in multiple formats: DOT, JSON, Mermaid."""
    
    # Color schemes for different node types
    NODE_COLORS = {
        "Session": "#dae8fc",
        "Worklet": "#fff2cc",
        "Mapping": "#d5e8d4",
        "Command": "#ffe6cc",
        "Event": "#f8cecc",
        "Timer": "#e1d5e7",
        "default": "#f5f5f5"
    }
    
    # Node shapes for different types
    NODE_SHAPES = {
        "Session": "box",
        "Worklet": "ellipse",
        "Mapping": "box",
        "Command": "diamond",
        "Event": "hexagon",
        "Timer": "octagon",
        "default": "box"
    }
    
    def visualize(self, dag: Dict[str, Any], format: str = "dot", 
                  include_metadata: bool = False) -> str:
        """Visualize DAG in specified format.
        
        Args:
            dag: DAG structure from DAGBuilder
            format: Output format - 'dot', 'json', 'mermaid', or 'svg'
            include_metadata: Whether to include node metadata in output
            
        Returns:
            Visualization string in requested format
        """
        if format.lower() == "dot":
            return self._to_dot(dag, include_metadata)
        elif format.lower() == "json":
            return self._to_json(dag, include_metadata)
        elif format.lower() == "mermaid":
            return self._to_mermaid(dag, include_metadata)
        elif format.lower() == "svg":
            return self._to_svg(dag, include_metadata)
        else:
            raise ValueError(f"Unsupported format: {format}. Supported: dot, json, mermaid, svg")
    
    def _to_dot(self, dag: Dict[str, Any], include_metadata: bool = False) -> str:
        """Generate Graphviz DOT format.
        
        Args:
            dag: DAG structure
            include_metadata: Include node metadata
            
        Returns:
            DOT format string
        """
        lines = ["digraph G {"]
        lines.append("  rankdir=LR;")
        lines.append("  node [shape=box, style=rounded, fontname=Arial];")
        lines.append("  edge [fontname=Arial];")
        lines.append("")
        
        # Add nodes
        nodes = dag.get("nodes", [])
        for node in nodes:
            node_id = node.get("id", node.get("name", ""))
            node_name = node.get("name", node_id)
            node_type = node.get("type", "default")
            
            # Get color and shape
            color = self.NODE_COLORS.get(node_type, self.NODE_COLORS["default"])
            shape = self.NODE_SHAPES.get(node_type, self.NODE_SHAPES["default"])
            
            # Build label
            label = f"{node_name}\\n({node_type})"
            if include_metadata and node.get("metadata"):
                metadata_str = self._format_metadata(node["metadata"])
                label += f"\\n{metadata_str}"
            
            # Escape quotes in label
            label = label.replace('"', '\\"')
            
            lines.append(f'  "{node_id}" [label="{label}", fillcolor="{color}", shape={shape}];')
        
        lines.append("")
        
        # Add edges
        edges = dag.get("edges", [])
        for edge in edges:
            from_node = edge.get("from", "")
            to_node = edge.get("to", "")
            condition = edge.get("condition")
            
            edge_label = ""
            if condition:
                edge_label = f' [label="{condition}"]'
            
            lines.append(f'  "{from_node}" -> "{to_node}"{edge_label};')
        
        # Add execution levels as subgraphs
        execution_levels = dag.get("execution_levels", [])
        if execution_levels:
            lines.append("")
            lines.append("  // Execution Levels (can run in parallel)")
            for i, level in enumerate(execution_levels):
                if len(level) > 1:
                    lines.append(f"  subgraph cluster_level_{i} {{")
                    lines.append(f'    label="Level {i+1}";')
                    lines.append("    style=dashed;")
                    for node_id in level:
                        lines.append(f'    "{node_id}";')
                    lines.append("  }")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def _to_json(self, dag: Dict[str, Any], include_metadata: bool = False) -> str:
        """Generate JSON format.
        
        Args:
            dag: DAG structure
            include_metadata: Include node metadata
            
        Returns:
            JSON string
        """
        output = {
            "workflow_name": dag.get("workflow_name", ""),
            "nodes": [],
            "edges": dag.get("edges", []),
            "topological_order": dag.get("topological_order", []),
            "execution_levels": dag.get("execution_levels", []),
            "has_cycle": dag.get("has_cycle", False)
        }
        
        # Process nodes
        nodes = dag.get("nodes", [])
        for node in nodes:
            node_data = {
                "id": node.get("id", node.get("name", "")),
                "name": node.get("name", ""),
                "type": node.get("type", ""),
                "color": self.NODE_COLORS.get(node.get("type", "default"), self.NODE_COLORS["default"]),
                "shape": self.NODE_SHAPES.get(node.get("type", "default"), self.NODE_SHAPES["default"])
            }
            if include_metadata and node.get("metadata"):
                node_data["metadata"] = node["metadata"]
            output["nodes"].append(node_data)
        
        return json.dumps(output, indent=2)
    
    def _to_mermaid(self, dag: Dict[str, Any], include_metadata: bool = False) -> str:
        """Generate Mermaid format.
        
        Args:
            dag: DAG structure
            include_metadata: Include node metadata
            
        Returns:
            Mermaid format string
        """
        lines = ["graph LR"]
        
        # Add nodes
        nodes = dag.get("nodes", [])
        node_styles = {}
        for node in nodes:
            node_id = node.get("id", node.get("name", ""))
            node_name = node.get("name", node_id)
            node_type = node.get("type", "default")
            
            # Mermaid node syntax
            label = f"{node_name}({node_type})"
            lines.append(f'    {node_id}["{label}"]')
            
            # Store style info
            color = self.NODE_COLORS.get(node_type, self.NODE_COLORS["default"])
            node_styles[node_id] = {"color": color, "type": node_type}
        
        lines.append("")
        
        # Add edges
        edges = dag.get("edges", [])
        for edge in edges:
            from_node = edge.get("from", "")
            to_node = edge.get("to", "")
            condition = edge.get("condition")
            
            edge_label = f'|"{condition}"|' if condition else ""
            lines.append(f"    {from_node} -->{edge_label} {to_node}")
        
        # Add styling
        lines.append("")
        lines.append("    %% Styling")
        for node_id, style in node_styles.items():
            color_hex = style["color"].lstrip("#")
            lines.append(f'    style {node_id} fill:#{color_hex}')
        
        return "\n".join(lines)
    
    def _to_svg(self, dag: Dict[str, Any], include_metadata: bool = False) -> str:
        """Generate SVG format (basic structure).
        
        Note: Full SVG generation would require graph layout algorithm.
        This provides a basic structure that can be enhanced.
        
        Args:
            dag: DAG structure
            include_metadata: Include node metadata
            
        Returns:
            SVG format string
        """
        nodes = dag.get("nodes", [])
        edges = dag.get("edges", [])
        
        # Calculate dimensions
        width = max(800, len(nodes) * 150)
        height = max(600, len(nodes) * 100)
        
        lines = [
            f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
            '  <defs>',
            '    <style>',
            '      .node { fill: #f5f5f5; stroke: #666; stroke-width: 2; }',
            '      .edge { stroke: #333; stroke-width: 2; fill: none; }',
            '      .label { font-family: Arial; font-size: 12px; }',
            '    </style>',
            '  </defs>'
        ]
        
        # Add edges first (so they appear behind nodes)
        for i, edge in enumerate(edges):
            from_node = edge.get("from", "")
            to_node = edge.get("to", "")
            # Simple positioning (would need proper layout algorithm)
            x1 = 50 + (i % 10) * 80
            y1 = 50 + (i // 10) * 60
            x2 = x1 + 100
            y2 = y1 + 50
            lines.append(f'  <line class="edge" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>')
        
        # Add nodes
        for i, node in enumerate(nodes):
            node_id = node.get("id", node.get("name", ""))
            node_name = node.get("name", node_id)
            node_type = node.get("type", "default")
            color = self.NODE_COLORS.get(node_type, self.NODE_COLORS["default"])
            
            x = 100 + (i % 5) * 150
            y = 100 + (i // 5) * 120
            
            lines.append(f'  <rect class="node" x="{x}" y="{y}" width="120" height="60" fill="{color}"/>')
            lines.append(f'  <text class="label" x="{x+60}" y="{y+30}" text-anchor="middle">{node_name}</text>')
            lines.append(f'  <text class="label" x="{x+60}" y="{y+45}" text-anchor="middle" font-size="10">{node_type}</text>')
        
        lines.append("</svg>")
        
        return "\n".join(lines)
    
    def _format_metadata(self, metadata: Dict[str, Any]) -> str:
        """Format metadata for display.
        
        Args:
            metadata: Node metadata dictionary
            
        Returns:
            Formatted metadata string
        """
        parts = []
        for key, value in metadata.items():
            if key not in ["name", "type"] and value:
                if isinstance(value, (str, int, float, bool)):
                    parts.append(f"{key}: {value}")
                elif isinstance(value, list) and len(value) > 0:
                    parts.append(f"{key}: {len(value)} items")
        
        return " | ".join(parts[:3])  # Limit to 3 items
    
    def get_visualization_formats(self) -> List[str]:
        """Get list of supported visualization formats.
        
        Returns:
            List of format names
        """
        return ["dot", "json", "mermaid", "svg"]
    
    def export(self, dag: Dict[str, Any], format: str, filename: Optional[str] = None) -> str:
        """Export DAG visualization to file.
        
        Args:
            dag: DAG structure
            format: Output format
            filename: Optional filename (without extension)
            
        Returns:
            Visualization string
        """
        visualization = self.visualize(dag, format)
        
        if filename:
            filepath = f"{filename}.{format}"
            with open(filepath, "w") as f:
                f.write(visualization)
            logger.info(f"DAG visualization exported to {filepath}")
        
        return visualization
