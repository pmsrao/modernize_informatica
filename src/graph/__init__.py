"""Graph storage module for Neo4j integration."""
from typing import Optional

# Lazy import to avoid requiring Neo4j if not configured
_graph_store: Optional[object] = None


def get_graph_store():
    """Get or create GraphStore instance (lazy initialization)."""
    global _graph_store
    if _graph_store is None:
        from src.graph.graph_store import GraphStore
        from src.config import settings
        
        if settings.enable_graph_store:
            _graph_store = GraphStore(
                uri=settings.neo4j_uri,
                user=settings.neo4j_user,
                password=settings.neo4j_password
            )
        else:
            _graph_store = None
    
    return _graph_store


__all__ = ["get_graph_store"]

