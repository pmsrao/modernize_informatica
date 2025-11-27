"""Unit tests for XML parsers."""
import pytest
import os
from pathlib import Path
from parser import MappingParser, WorkflowParser, SessionParser, WorkletParser
from utils.exceptions import ParsingError


class TestMappingParser:
    """Tests for MappingParser."""
    
    def test_parse_basic_mapping(self, tmp_path):
        """Test parsing a basic mapping XML."""
        # Create a simple mapping XML
        xml_content = """<?xml version="1.0"?>
<MAPPING NAME="M_TEST">
    <SOURCE NAME="SRC1">
        <TABLE NAME="customers"/>
        <FIELD NAME="customer_id" DATATYPE="number"/>
        <FIELD NAME="customer_name" DATATYPE="string"/>
    </SOURCE>
    <TARGET NAME="TGT1" TABLE="customer_target"/>
    <TRANSFORMATION NAME="EXP1" TYPE="EXPRESSION">
        <PORT NAME="customer_id" PORTTYPE="INPUT" DATATYPE="number"/>
        <PORT NAME="customer_name_upper" PORTTYPE="OUTPUT" DATATYPE="string" EXPRESSION="UPPER(customer_name)"/>
    </TRANSFORMATION>
</MAPPING>"""
        
        xml_file = tmp_path / "test_mapping.xml"
        xml_file.write_text(xml_content)
        
        parser = MappingParser(str(xml_file))
        result = parser.parse()
        
        assert result["name"] == "M_TEST"
        assert len(result["sources"]) == 1
        assert result["sources"][0]["name"] == "SRC1"
        assert len(result["targets"]) == 1
        assert result["targets"][0]["name"] == "TGT1"
    
    def test_parse_invalid_xml(self, tmp_path):
        """Test parsing invalid XML raises ParsingError."""
        invalid_xml = tmp_path / "invalid.xml"
        invalid_xml.write_text("<INVALID>")
        
        with pytest.raises(ParsingError):
            parser = MappingParser(str(invalid_xml))
            parser.parse()
    
    def test_parse_nonexistent_file(self):
        """Test parsing nonexistent file raises ParsingError."""
        with pytest.raises(ParsingError):
            parser = MappingParser("/nonexistent/file.xml")
            parser.parse()
    
    def test_parse_all_transformation_types(self, tmp_path):
        """Test parsing all transformation types."""
        xml_content = """<?xml version="1.0"?>
<MAPPING NAME="M_ALL_TYPES">
    <TRANSFORMATION NAME="EXP1" TYPE="EXPRESSION"/>
    <TRANSFORMATION NAME="LKP1" TYPE="LOOKUP"/>
    <TRANSFORMATION NAME="AGG1" TYPE="AGGREGATOR"/>
    <TRANSFORMATION NAME="JNR1" TYPE="JOINER"/>
    <TRANSFORMATION NAME="RTR1" TYPE="ROUTER"/>
    <TRANSFORMATION NAME="FLT1" TYPE="FILTER"/>
    <TRANSFORMATION NAME="SRT1" TYPE="SORTER"/>
    <TRANSFORMATION NAME="RNK1" TYPE="RANK"/>
    <TRANSFORMATION NAME="UNN1" TYPE="UNION"/>
    <TRANSFORMATION NAME="UPD1" TYPE="UPDATE_STRATEGY"/>
</MAPPING>"""
        
        xml_file = tmp_path / "all_types.xml"
        xml_file.write_text(xml_content)
        
        parser = MappingParser(str(xml_file))
        result = parser.parse()
        
        assert len(result["transformations"]) == 10
        types = [t["type"] for t in result["transformations"]]
        assert "EXPRESSION" in types
        assert "LOOKUP" in types
        assert "AGGREGATOR" in types


class TestWorkflowParser:
    """Tests for WorkflowParser."""
    
    def test_parse_basic_workflow(self, tmp_path):
        """Test parsing a basic workflow XML."""
        xml_content = """<?xml version="1.0"?>
<WORKFLOW NAME="WF_TEST">
    <TASKINSTANCE NAME="TASK1" TASKTYPE="Session"/>
    <TASKINSTANCE NAME="TASK2" TASKTYPE="Command"/>
    <LINK FROMTASK="TASK1" TOTASK="TASK2"/>
</WORKFLOW>"""
        
        xml_file = tmp_path / "test_workflow.xml"
        xml_file.write_text(xml_content)
        
        parser = WorkflowParser(str(xml_file))
        result = parser.parse()
        
        assert result["name"] == "WF_TEST"
        assert len(result["tasks"]) == 2
        assert len(result["links"]) == 1


class TestSessionParser:
    """Tests for SessionParser."""
    
    def test_parse_basic_session(self, tmp_path):
        """Test parsing a basic session XML."""
        xml_content = """<?xml version="1.0"?>
<SESSION NAME="SESS_TEST" MAPPINGNAME="M_TEST">
    <ATTRIBUTE NAME="SourceConnection" VALUE="DB_CONN"/>
    <ATTRIBUTE NAME="TargetConnection" VALUE="DB_CONN"/>
</SESSION>"""
        
        xml_file = tmp_path / "test_session.xml"
        xml_file.write_text(xml_content)
        
        parser = SessionParser(str(xml_file))
        result = parser.parse()
        
        assert result["name"] == "SESS_TEST"
        assert result["mapping"] == "M_TEST"
        assert "config" in result


class TestWorkletParser:
    """Tests for WorkletParser."""
    
    def test_parse_basic_worklet(self, tmp_path):
        """Test parsing a basic worklet XML."""
        xml_content = """<?xml version="1.0"?>
<WORKLET NAME="WK_TEST">
    <TASKINSTANCE NAME="TASK1" TASKTYPE="Session"/>
</WORKLET>"""
        
        xml_file = tmp_path / "test_worklet.xml"
        xml_file.write_text(xml_content)
        
        parser = WorkletParser(str(xml_file))
        result = parser.parse()
        
        assert result["name"] == "WK_TEST"
        assert len(result["tasks"]) == 1
