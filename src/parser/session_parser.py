
"""Session Parser - Production Grade (Simplified)"""
import lxml.etree as ET

class SessionParser:
    def __init__(self, path):
        self.tree = ET.parse(path)
        self.root = self.tree.getroot()

    def parse(self):
        sess = self.root.find(".//SESSION")
        if sess is None:
            return {}
        return {
            "name": sess.get("NAME"),
            "mapping": sess.get("MAPPINGNAME"),
            "config": {a.get("NAME"): a.get("VALUE") for a in sess.findall(".//ATTRIBUTE")}
        }
