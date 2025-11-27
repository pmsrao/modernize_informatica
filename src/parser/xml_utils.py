
"""XML Utils - Production Grade (Simplified)"""
def get_text(node, tag):
    child = node.find(tag)
    return child.text if child is not None else None
