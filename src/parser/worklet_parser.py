
"""Worklet Parser - Production Grade (Simplified)"""
import lxml.etree as ET

class WorkletParser:
    def __init__(self, path):
        self.tree = ET.parse(path)
        self.root = self.tree.getroot()

    def parse(self):
        wk = self.root.find(".//WORKLET")
        if wk is None:
            return {}
        tasks = [{"name": t.get("NAME"), "type": t.get("TASKTYPE")} for t in wk.findall(".//TASKINSTANCE")]
        return {"name": wk.get("NAME"), "tasks": tasks}
