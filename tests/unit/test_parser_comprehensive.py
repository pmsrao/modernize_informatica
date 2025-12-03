"""Comprehensive unit tests for XML parsers."""
import pytest
import os
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from parser import MappingParser, WorkflowParser, SessionParser, WorkletParser, MappletParser
from utils.exceptions import ParsingError


class TestMappingParserComprehensive:
    """Comprehensive tests for MappingParser."""
    
    def test_parse_complex_mapping_with_all_transformations(self, tmp_path):
        """Test parsing a complex mapping with all transformation types."""
        xml_content = """<?xml version="1.0"?>
<MAPPING NAME="M_COMPLEX">
    <SOURCE NAME="SRC1" DESCRIPTION="Customer source">
        <TABLE NAME="customers"/>
        <FIELD NAME="customer_id" DATATYPE="number" DESCRIPTION="Customer ID"/>
        <FIELD NAME="customer_name" DATATYPE="string"/>
        <FIELD NAME="email" DATATYPE="string"/>
    </SOURCE>
    <SOURCE NAME="SRC2">
        <TABLE NAME="orders"/>
        <FIELD NAME="order_id" DATATYPE="number"/>
        <FIELD NAME="customer_id" DATATYPE="number"/>
        <FIELD NAME="order_date" DATATYPE="date/time"/>
        <FIELD NAME="amount" DATATYPE="decimal"/>
    </SOURCE>
    <TARGET NAME="TGT1" TABLE="customer_summary" DESCRIPTION="Summary target"/>
    <TARGET NAME="TGT2" TABLE="order_summary"/>
    
    <TRANSFORMATION NAME="SQ_SRC1" TYPE="SOURCE QUALIFIER">
        <TRANSFORMATIONEXTENSION NAME="SQ_SRC1" TYPE="SOURCE QUALIFIER"/>
        <CONNECTOR NAME="C1" FROMINSTANCE="SRC1" FROMFIELD="customer_id" TOINSTANCE="SQ_SRC1" TOFIELD="customer_id"/>
    </TRANSFORMATION>
    
    <TRANSFORMATION NAME="EXP1" TYPE="EXPRESSION">
        <TRANSFORMATIONEXTENSION NAME="EXP1" TYPE="EXPRESSION"/>
        <PORT NAME="customer_id" PORTTYPE="INPUT" DATATYPE="number"/>
        <PORT NAME="customer_name" PORTTYPE="INPUT" DATATYPE="string"/>
        <PORT NAME="email" PORTTYPE="INPUT" DATATYPE="string"/>
        <PORT NAME="email_upper" PORTTYPE="OUTPUT" DATATYPE="string" EXPRESSION="UPPER(email)"/>
        <PORT NAME="customer_key" PORTTYPE="OUTPUT" DATATYPE="string" EXPRESSION="CONCAT(TO_CHAR(customer_id), '_', customer_name)"/>
    </TRANSFORMATION>
    
    <TRANSFORMATION NAME="LKP1" TYPE="LOOKUP">
        <TRANSFORMATIONEXTENSION NAME="LKP1" TYPE="LOOKUP"/>
        <LOOKUPTABLE NAME="lkp_customers" CONNECTION="DB_CONN"/>
        <LOOKUPFIELD NAME="customer_id" DATATYPE="number"/>
        <LOOKUPFIELD NAME="customer_status" DATATYPE="string"/>
        <PORT NAME="customer_id" PORTTYPE="INPUT" DATATYPE="number"/>
        <PORT NAME="customer_status" PORTTYPE="OUTPUT" DATATYPE="string"/>
    </TRANSFORMATION>
    
    <TRANSFORMATION NAME="AGG1" TYPE="AGGREGATOR">
        <TRANSFORMATIONEXTENSION NAME="AGG1" TYPE="AGGREGATOR"/>
        <GROUP NAME="customer_id"/>
        <PORT NAME="customer_id" PORTTYPE="INPUT" DATATYPE="number"/>
        <PORT NAME="amount" PORTTYPE="INPUT" DATATYPE="decimal"/>
        <PORT NAME="total_amount" PORTTYPE="OUTPUT" DATATYPE="decimal" EXPRESSION="SUM(amount)"/>
        <PORT NAME="order_count" PORTTYPE="OUTPUT" DATATYPE="number" EXPRESSION="COUNT(*)"/>
    </TRANSFORMATION>
    
    <TRANSFORMATION NAME="JNR1" TYPE="JOINER">
        <TRANSFORMATIONEXTENSION NAME="JNR1" TYPE="JOINER"/>
        <JOINCONDITION JOINERNAME="JNR1" JOINERTYPE="NORMAL" MASTERTABLE="EXP1" DETAILTABLE="AGG1">
            <JOINKEY MASTERTABLE="EXP1" MASTERFIELD="customer_id" DETAILTABLE="AGG1" DETAILFIELD="customer_id"/>
        </JOINCONDITION>
    </TRANSFORMATION>
    
    <TRANSFORMATION NAME="FLT1" TYPE="FILTER">
        <TRANSFORMATIONEXTENSION NAME="FLT1" TYPE="FILTER"/>
        <FILTER CONDITION="total_amount &gt; 1000"/>
    </TRANSFORMATION>
    
    <TRANSFORMATION NAME="RTR1" TYPE="ROUTER">
        <TRANSFORMATIONEXTENSION NAME="RTR1" TYPE="ROUTER"/>
        <GROUP NAME="HIGH_VALUE" ORDER="1">
            <FILTER CONDITION="total_amount &gt; 5000"/>
        </GROUP>
        <GROUP NAME="MEDIUM_VALUE" ORDER="2">
            <FILTER CONDITION="total_amount &gt; 1000 AND total_amount &lt;= 5000"/>
        </GROUP>
    </TRANSFORMATION>
    
    <TRANSFORMATION NAME="SRT1" TYPE="SORTER">
        <TRANSFORMATIONEXTENSION NAME="SRT1" TYPE="SORTER"/>
        <SORTKEY NAME="total_amount" ORDER="DESCENDING"/>
    </TRANSFORMATION>
    
    <TRANSFORMATION NAME="RNK1" TYPE="RANK">
        <TRANSFORMATIONEXTENSION NAME="RNK1" TYPE="RANK"/>
        <RANKKEY NAME="total_amount" ORDER="DESCENDING"/>
    </TRANSFORMATION>
    
    <TRANSFORMATION NAME="UNN1" TYPE="UNION">
        <TRANSFORMATIONEXTENSION NAME="UNN1" TYPE="UNION"/>
    </TRANSFORMATION>
    
    <TRANSFORMATION NAME="UPD1" TYPE="UPDATE STRATEGY">
        <TRANSFORMATIONEXTENSION NAME="UPD1" TYPE="UPDATE STRATEGY"/>
        <ATTRIBUTE NAME="Update Strategy Expression" VALUE="DD_UPDATE"/>
    </TRANSFORMATION>
    
    <CONNECTOR NAME="C1" FROMINSTANCE="SRC1" FROMFIELD="customer_id" TOINSTANCE="EXP1" TOFIELD="customer_id"/>
    <CONNECTOR NAME="C2" FROMINSTANCE="EXP1" FROMFIELD="customer_key" TOINSTANCE="JNR1" TOFIELD="customer_key"/>
    <CONNECTOR NAME="C3" FROMINSTANCE="JNR1" FROMFIELD="total_amount" TOINSTANCE="FLT1" TOFIELD="total_amount"/>
    <CONNECTOR NAME="C4" FROMINSTANCE="FLT1" FROMFIELD="total_amount" TOINSTANCE="TGT1" TOFIELD="total_amount"/>
</MAPPING>"""
        
        xml_file = tmp_path / "complex_mapping.xml"
        xml_file.write_text(xml_content)
        
        parser = MappingParser(str(xml_file))
        result = parser.parse()
        
        assert result["name"] == "M_COMPLEX"
        assert result["source_component_type"] == "mapping"
        assert len(result["sources"]) == 2
        assert len(result["targets"]) == 2
        assert len(result["transformations"]) >= 10
        
        # Check transformation types
        trans_types = {t["type"] for t in result["transformations"]}
        assert "EXPRESSION" in trans_types
        assert "LOOKUP" in trans_types
        assert "AGGREGATOR" in trans_types
        assert "JOINER" in trans_types
        assert "FILTER" in trans_types
        assert "ROUTER" in trans_types
        assert "SORTER" in trans_types
        assert "RANK" in trans_types
        assert "UNION" in trans_types
        assert "UPDATE_STRATEGY" in trans_types
    
    def test_parse_mapping_with_ports_and_expressions(self, tmp_path):
        """Test parsing mapping with detailed ports and expressions."""
        xml_content = """<?xml version="1.0"?>
<MAPPING NAME="M_EXPRESSIONS">
    <SOURCE NAME="SRC1">
        <TABLE NAME="products"/>
        <FIELD NAME="product_id" DATATYPE="number"/>
        <FIELD NAME="price" DATATYPE="decimal"/>
        <FIELD NAME="quantity" DATATYPE="number"/>
    </SOURCE>
    <TARGET NAME="TGT1" TABLE="product_summary"/>
    
    <TRANSFORMATION NAME="EXP1" TYPE="EXPRESSION">
        <TRANSFORMATIONEXTENSION NAME="EXP1" TYPE="EXPRESSION"/>
        <PORT NAME="product_id" PORTTYPE="INPUT" DATATYPE="number"/>
        <PORT NAME="price" PORTTYPE="INPUT" DATATYPE="decimal"/>
        <PORT NAME="quantity" PORTTYPE="INPUT" DATATYPE="number"/>
        <PORT NAME="total_value" PORTTYPE="OUTPUT" DATATYPE="decimal" EXPRESSION="price * quantity"/>
        <PORT NAME="discounted_price" PORTTYPE="OUTPUT" DATATYPE="decimal" EXPRESSION="IIF(quantity &gt; 10, price * 0.9, price)"/>
        <PORT NAME="price_category" PORTTYPE="OUTPUT" DATATYPE="string" EXPRESSION="IIF(price &gt; 100, 'HIGH', IIF(price &gt; 50, 'MEDIUM', 'LOW'))"/>
    </TRANSFORMATION>
    
    <CONNECTOR NAME="C1" FROMINSTANCE="SRC1" FROMFIELD="product_id" TOINSTANCE="EXP1" TOFIELD="product_id"/>
    <CONNECTOR NAME="C2" FROMINSTANCE="EXP1" FROMFIELD="total_value" TOINSTANCE="TGT1" TOFIELD="total_value"/>
</MAPPING>"""
        
        xml_file = tmp_path / "expressions.xml"
        xml_file.write_text(xml_content)
        
        parser = MappingParser(str(xml_file))
        result = parser.parse()
        
        # Find EXP1 transformation
        exp1 = next((t for t in result["transformations"] if t["name"] == "EXP1"), None)
        assert exp1 is not None
        assert exp1["type"] == "EXPRESSION"
        
        # Check ports
        ports = exp1.get("ports", [])
        assert len(ports) >= 3
        
        # Check output ports have expressions
        output_ports = [p for p in ports if p.get("port_type") == "OUTPUT"]
        assert len(output_ports) >= 3
        assert any("price * quantity" in p.get("expression", "") for p in output_ports)
    
    def test_parse_mapping_with_aggregator(self, tmp_path):
        """Test parsing aggregator transformation with group by and aggregate functions."""
        xml_content = """<?xml version="1.0"?>
<MAPPING NAME="M_AGGREGATE">
    <SOURCE NAME="SRC1">
        <TABLE NAME="sales"/>
        <FIELD NAME="region" DATATYPE="string"/>
        <FIELD NAME="product" DATATYPE="string"/>
        <FIELD NAME="amount" DATATYPE="decimal"/>
        <FIELD NAME="quantity" DATATYPE="number"/>
    </SOURCE>
    <TARGET NAME="TGT1" TABLE="sales_summary"/>
    
    <TRANSFORMATION NAME="AGG1" TYPE="AGGREGATOR">
        <TRANSFORMATIONEXTENSION NAME="AGG1" TYPE="AGGREGATOR"/>
        <GROUP NAME="region"/>
        <GROUP NAME="product"/>
        <PORT NAME="region" PORTTYPE="INPUT" DATATYPE="string"/>
        <PORT NAME="product" PORTTYPE="INPUT" DATATYPE="string"/>
        <PORT NAME="amount" PORTTYPE="INPUT" DATATYPE="decimal"/>
        <PORT NAME="quantity" PORTTYPE="INPUT" DATATYPE="number"/>
        <PORT NAME="total_amount" PORTTYPE="OUTPUT" DATATYPE="decimal" EXPRESSION="SUM(amount)"/>
        <PORT NAME="avg_amount" PORTTYPE="OUTPUT" DATATYPE="decimal" EXPRESSION="AVG(amount)"/>
        <PORT NAME="max_amount" PORTTYPE="OUTPUT" DATATYPE="decimal" EXPRESSION="MAX(amount)"/>
        <PORT NAME="min_amount" PORTTYPE="OUTPUT" DATATYPE="decimal" EXPRESSION="MIN(amount)"/>
        <PORT NAME="total_quantity" PORTTYPE="OUTPUT" DATATYPE="number" EXPRESSION="SUM(quantity)"/>
        <PORT NAME="row_count" PORTTYPE="OUTPUT" DATATYPE="number" EXPRESSION="COUNT(*)"/>
    </TRANSFORMATION>
    
    <CONNECTOR NAME="C1" FROMINSTANCE="SRC1" FROMFIELD="region" TOINSTANCE="AGG1" TOFIELD="region"/>
    <CONNECTOR NAME="C2" FROMINSTANCE="AGG1" FROMFIELD="total_amount" TOINSTANCE="TGT1" TOFIELD="total_amount"/>
</MAPPING>"""
        
        xml_file = tmp_path / "aggregator.xml"
        xml_file.write_text(xml_content)
        
        parser = MappingParser(str(xml_file))
        result = parser.parse()
        
        agg1 = next((t for t in result["transformations"] if t["name"] == "AGG1"), None)
        assert agg1 is not None
        assert agg1["type"] == "AGGREGATOR"
        
        # Check group by fields
        groups = agg1.get("groups", [])
        assert "region" in groups
        assert "product" in groups
    
    def test_parse_mapping_with_joiner(self, tmp_path):
        """Test parsing joiner transformation."""
        xml_content = """<?xml version="1.0"?>
<MAPPING NAME="M_JOIN">
    <SOURCE NAME="SRC1">
        <TABLE NAME="customers"/>
        <FIELD NAME="customer_id" DATATYPE="number"/>
        <FIELD NAME="customer_name" DATATYPE="string"/>
    </SOURCE>
    <SOURCE NAME="SRC2">
        <TABLE NAME="orders"/>
        <FIELD NAME="order_id" DATATYPE="number"/>
        <FIELD NAME="customer_id" DATATYPE="number"/>
        <FIELD NAME="order_date" DATATYPE="date/time"/>
    </SOURCE>
    <TARGET NAME="TGT1" TABLE="customer_orders"/>
    
    <TRANSFORMATION NAME="JNR1" TYPE="JOINER">
        <TRANSFORMATIONEXTENSION NAME="JNR1" TYPE="JOINER"/>
        <JOINCONDITION JOINERNAME="JNR1" JOINERTYPE="NORMAL" MASTERTABLE="SRC1" DETAILTABLE="SRC2">
            <JOINKEY MASTERTABLE="SRC1" MASTERFIELD="customer_id" DETAILTABLE="SRC2" DETAILFIELD="customer_id"/>
        </JOINCONDITION>
    </TRANSFORMATION>
    
    <CONNECTOR NAME="C1" FROMINSTANCE="SRC1" FROMFIELD="customer_id" TOINSTANCE="JNR1" TOFIELD="customer_id"/>
    <CONNECTOR NAME="C2" FROMINSTANCE="SRC2" FROMFIELD="customer_id" TOINSTANCE="JNR1" TOFIELD="customer_id"/>
    <CONNECTOR NAME="C3" FROMINSTANCE="JNR1" FROMFIELD="customer_name" TOINSTANCE="TGT1" TOFIELD="customer_name"/>
</MAPPING>"""
        
        xml_file = tmp_path / "joiner.xml"
        xml_file.write_text(xml_content)
        
        parser = MappingParser(str(xml_file))
        result = parser.parse()
        
        jnr1 = next((t for t in result["transformations"] if t["name"] == "JNR1"), None)
        assert jnr1 is not None
        assert jnr1["type"] == "JOINER"
    
    def test_parse_mapping_with_filter(self, tmp_path):
        """Test parsing filter transformation."""
        xml_content = """<?xml version="1.0"?>
<MAPPING NAME="M_FILTER">
    <SOURCE NAME="SRC1">
        <TABLE NAME="orders"/>
        <FIELD NAME="order_id" DATATYPE="number"/>
        <FIELD NAME="amount" DATATYPE="decimal"/>
        <FIELD NAME="status" DATATYPE="string"/>
    </SOURCE>
    <TARGET NAME="TGT1" TABLE="high_value_orders"/>
    
    <TRANSFORMATION NAME="FLT1" TYPE="FILTER">
        <TRANSFORMATIONEXTENSION NAME="FLT1" TYPE="FILTER"/>
        <FILTER CONDITION="amount &gt; 1000 AND status = 'ACTIVE'"/>
    </TRANSFORMATION>
    
    <CONNECTOR NAME="C1" FROMINSTANCE="SRC1" FROMFIELD="amount" TOINSTANCE="FLT1" TOFIELD="amount"/>
    <CONNECTOR NAME="C2" FROMINSTANCE="FLT1" FROMFIELD="order_id" TOINSTANCE="TGT1" TOFIELD="order_id"/>
</MAPPING>"""
        
        xml_file = tmp_path / "filter.xml"
        xml_file.write_text(xml_content)
        
        parser = MappingParser(str(xml_file))
        result = parser.parse()
        
        flt1 = next((t for t in result["transformations"] if t["name"] == "FLT1"), None)
        assert flt1 is not None
        assert flt1["type"] == "FILTER"
        assert "filter_condition" in flt1 or "condition" in flt1
    
    def test_parse_mapping_with_router(self, tmp_path):
        """Test parsing router transformation."""
        xml_content = """<?xml version="1.0"?>
<MAPPING NAME="M_ROUTER">
    <SOURCE NAME="SRC1">
        <TABLE NAME="customers"/>
        <FIELD NAME="customer_id" DATATYPE="number"/>
        <FIELD NAME="total_purchases" DATATYPE="decimal"/>
    </SOURCE>
    <TARGET NAME="TGT1" TABLE="vip_customers"/>
    <TARGET NAME="TGT2" TABLE="regular_customers"/>
    
    <TRANSFORMATION NAME="RTR1" TYPE="ROUTER">
        <TRANSFORMATIONEXTENSION NAME="RTR1" TYPE="ROUTER"/>
        <GROUP NAME="VIP" ORDER="1">
            <FILTER CONDITION="total_purchases &gt; 10000"/>
        </GROUP>
        <GROUP NAME="REGULAR" ORDER="2">
            <FILTER CONDITION="total_purchases &lt;= 10000"/>
        </GROUP>
    </TRANSFORMATION>
    
    <CONNECTOR NAME="C1" FROMINSTANCE="SRC1" FROMFIELD="total_purchases" TOINSTANCE="RTR1" TOFIELD="total_purchases"/>
    <CONNECTOR NAME="C2" FROMINSTANCE="RTR1" FROMGROUP="VIP" TOINSTANCE="TGT1" TOFIELD="customer_id"/>
    <CONNECTOR NAME="C3" FROMINSTANCE="RTR1" FROMGROUP="REGULAR" TOINSTANCE="TGT2" TOFIELD="customer_id"/>
</MAPPING>"""
        
        xml_file = tmp_path / "router.xml"
        xml_file.write_text(xml_content)
        
        parser = MappingParser(str(xml_file))
        result = parser.parse()
        
        rtr1 = next((t for t in result["transformations"] if t["name"] == "RTR1"), None)
        assert rtr1 is not None
        assert rtr1["type"] == "ROUTER"
    
    def test_parse_source_qualifier_with_fallback_name(self, tmp_path):
        """Test parsing Source Qualifier when NAME attribute is missing."""
        xml_content = """<?xml version="1.0"?>
<MAPPING NAME="M_SQ_TEST">
    <SOURCE NAME="SRC1">
        <TABLE NAME="customers"/>
        <FIELD NAME="customer_id" DATATYPE="number"/>
    </SOURCE>
    <TRANSFORMATION TYPE="Source Qualifier">
        <PORT NAME="customer_id" PORTTYPE="OUTPUT" DATATYPE="number"/>
    </TRANSFORMATION>
</MAPPING>"""
        
        xml_file = tmp_path / "sq_fallback.xml"
        xml_file.write_text(xml_content)
        
        parser = MappingParser(str(xml_file))
        result = parser.parse()
        
        # Should create Source Qualifier with fallback name
        sqs = [t for t in result["transformations"] if t.get("type") == "SOURCE_QUALIFIER"]
        assert len(sqs) > 0
        assert sqs[0]["name"]  # Should have a name (either from XML or fallback)
    
    def test_parse_mapping_with_output_connectors(self, tmp_path):
        """Test parsing mapplet with OUTPUT connectors."""
        xml_content = """<?xml version="1.0"?>
<MAPPLET NAME="MPL_TEST">
    <INPUTPORT NAME="INPUT1" DATATYPE="string"/>
    <OUTPUTPORT NAME="OUTPUT1" DATATYPE="string"/>
    <TRANSFORMATION NAME="EXP1" TYPE="EXPRESSION">
        <PORT NAME="INPUT1" PORTTYPE="INPUT" DATATYPE="string"/>
        <PORT NAME="OUTPUT1" PORTTYPE="OUTPUT" DATATYPE="string" EXPRESSION="UPPER(INPUT1)"/>
    </TRANSFORMATION>
    <CONNECTOR FROMINSTANCE="EXP1" FROMFIELD="OUTPUT1" TOINSTANCE="OUTPUT" TOFIELD="OUTPUT1"/>
</MAPPLET>"""
        
        xml_file = tmp_path / "mapplet_output.xml"
        xml_file.write_text(xml_content)
        
        parser = MappletParser(str(xml_file))
        result = parser.parse()
        
        # Should parse OUTPUT connector
        connectors = result.get("connectors", [])
        output_connectors = [c for c in connectors if c.get("to_transformation") == "OUTPUT"]
        assert len(output_connectors) > 0
    
    def test_parse_expression_with_pipe_operator(self, tmp_path):
        """Test parsing expressions with || (string concatenation) operator."""
        xml_content = """<?xml version="1.0"?>
<MAPPING NAME="M_PIPE_TEST">
    <TRANSFORMATION NAME="EXP1" TYPE="EXPRESSION">
        <PORT NAME="FIELD1" PORTTYPE="INPUT" DATATYPE="string"/>
        <PORT NAME="FIELD2" PORTTYPE="INPUT" DATATYPE="string"/>
        <PORT NAME="CONCAT_FIELD" PORTTYPE="OUTPUT" DATATYPE="string" EXPRESSION="FIELD1 || ' ' || FIELD2"/>
    </TRANSFORMATION>
</MAPPING>"""
        
        xml_file = tmp_path / "pipe_operator.xml"
        xml_file.write_text(xml_content)
        
        parser = MappingParser(str(xml_file))
        result = parser.parse()
        
        exp1 = next((t for t in result["transformations"] if t["name"] == "EXP1"), None)
        assert exp1 is not None
        
        # Check expression contains || operator
        ports = exp1.get("ports", [])
        concat_port = next((p for p in ports if p.get("name") == "CONCAT_FIELD"), None)
        assert concat_port is not None
        assert "||" in concat_port.get("expression", "")
    
    def test_parse_mapping_with_connectors(self, tmp_path):
        """Test parsing connectors between transformations."""
        xml_content = """<?xml version="1.0"?>
<MAPPING NAME="M_CONNECTORS">
    <SOURCE NAME="SRC1">
        <TABLE NAME="customers"/>
        <FIELD NAME="customer_id" DATATYPE="number"/>
        <FIELD NAME="name" DATATYPE="string"/>
    </SOURCE>
    <TARGET NAME="TGT1" TABLE="output"/>
    
    <TRANSFORMATION NAME="EXP1" TYPE="EXPRESSION">
        <TRANSFORMATIONEXTENSION NAME="EXP1" TYPE="EXPRESSION"/>
        <PORT NAME="customer_id" PORTTYPE="INPUT" DATATYPE="number"/>
        <PORT NAME="name" PORTTYPE="INPUT" DATATYPE="string"/>
        <PORT NAME="name_upper" PORTTYPE="OUTPUT" DATATYPE="string" EXPRESSION="UPPER(name)"/>
    </TRANSFORMATION>
    
    <CONNECTOR NAME="C1" FROMINSTANCE="SRC1" FROMFIELD="customer_id" TOINSTANCE="EXP1" TOFIELD="customer_id"/>
    <CONNECTOR NAME="C2" FROMINSTANCE="SRC1" FROMFIELD="name" TOINSTANCE="EXP1" TOFIELD="name"/>
    <CONNECTOR NAME="C3" FROMINSTANCE="EXP1" FROMFIELD="name_upper" TOINSTANCE="TGT1" TOFIELD="name_upper"/>
</MAPPING>"""
        
        xml_file = tmp_path / "connectors.xml"
        xml_file.write_text(xml_content)
        
        parser = MappingParser(str(xml_file))
        result = parser.parse()
        
        assert len(result["connectors"]) == 3
        
        # Check connector structure
        c1 = result["connectors"][0]
        assert "from_instance" in c1 or "from_transformation" in c1
        assert "to_instance" in c1 or "to_transformation" in c1


class TestMappletParser:
    """Tests for MappletParser."""
    
    def test_parse_basic_mapplet(self, tmp_path):
        """Test parsing a basic mapplet."""
        xml_content = """<?xml version="1.0"?>
<MAPPLET NAME="MPL_TEST">
    <INPUTPORT NAME="input_customer_id" DATATYPE="number"/>
    <INPUTPORT NAME="input_customer_name" DATATYPE="string"/>
    <OUTPUTPORT NAME="output_customer_key" DATATYPE="string"/>
    
    <TRANSFORMATION NAME="EXP1" TYPE="EXPRESSION">
        <TRANSFORMATIONEXTENSION NAME="EXP1" TYPE="EXPRESSION"/>
        <PORT NAME="customer_id" PORTTYPE="INPUT" DATATYPE="number"/>
        <PORT NAME="customer_name" PORTTYPE="INPUT" DATATYPE="string"/>
        <PORT NAME="customer_key" PORTTYPE="OUTPUT" DATATYPE="string" EXPRESSION="CONCAT(TO_CHAR(customer_id), '_', customer_name)"/>
    </TRANSFORMATION>
    
    <CONNECTOR NAME="C1" FROMINSTANCE="INPUT" FROMFIELD="input_customer_id" TOINSTANCE="EXP1" TOFIELD="customer_id"/>
    <CONNECTOR NAME="C2" FROMINSTANCE="EXP1" FROMFIELD="customer_key" TOINSTANCE="OUTPUT" TOFIELD="output_customer_key"/>
</MAPPLET>"""
        
        xml_file = tmp_path / "test_mapplet.xml"
        xml_file.write_text(xml_content)
        
        parser = MappletParser(str(xml_file))
        result = parser.parse()
        
        assert result["name"] == "MPL_TEST"
        assert result.get("source_component_type") == "mapplet"
        assert len(result.get("input_ports", [])) == 2
        assert len(result.get("output_ports", [])) == 1
        assert len(result.get("transformations", [])) >= 1


class TestWorkflowParserComprehensive:
    """Comprehensive tests for WorkflowParser."""
    
    def test_parse_workflow_with_all_task_types(self, tmp_path):
        """Test parsing workflow with all task types."""
        xml_content = """<?xml version="1.0"?>
<WORKFLOW NAME="WF_COMPLEX">
    <TASKINSTANCE NAME="SESS1" TASKTYPE="Session" DESCRIPTION="Load customers"/>
    <TASKINSTANCE NAME="SESS2" TASKTYPE="Session" DESCRIPTION="Load orders"/>
    <TASKINSTANCE NAME="CMD1" TASKTYPE="Command" DESCRIPTION="Run script"/>
    <TASKINSTANCE NAME="EVT1" TASKTYPE="Event-Wait" DESCRIPTION="Wait for event"/>
    <TASKINSTANCE NAME="EVT2" TASKTYPE="Event-Raise" DESCRIPTION="Raise event"/>
    <TASKINSTANCE NAME="DEC1" TASKTYPE="Decision" DESCRIPTION="Check condition"/>
    <TASKINSTANCE NAME="ASG1" TASKTYPE="Assignment" DESCRIPTION="Set variable"/>
    
    <LINK FROMTASK="SESS1" TOTASK="SESS2"/>
    <LINK FROMTASK="SESS2" TOTASK="CMD1"/>
    <LINK FROMTASK="CMD1" TOTASK="DEC1"/>
    <LINK FROMTASK="DEC1" TOTASK="EVT1" LABEL="SUCCESS"/>
    <LINK FROMTASK="DEC1" TOTASK="EVT2" LABEL="FAILURE"/>
</WORKFLOW>"""
        
        xml_file = tmp_path / "complex_workflow.xml"
        xml_file.write_text(xml_content)
        
        parser = WorkflowParser(str(xml_file))
        result = parser.parse()
        
        assert result["name"] == "WF_COMPLEX"
        assert len(result["tasks"]) >= 7
        assert len(result["links"]) >= 5
        
        # Check task types
        task_types = {t.get("type") for t in result["tasks"]}
        assert "Session" in task_types
        assert "Command" in task_types
        assert "Event-Wait" in task_types or "Event-Raise" in task_types
    
    def test_parse_workflow_with_links(self, tmp_path):
        """Test parsing workflow links."""
        xml_content = """<?xml version="1.0"?>
<WORKFLOW NAME="WF_LINKS">
    <TASKINSTANCE NAME="TASK1" TASKTYPE="Session"/>
    <TASKINSTANCE NAME="TASK2" TASKTYPE="Session"/>
    <TASKINSTANCE NAME="TASK3" TASKTYPE="Command"/>
    
    <LINK FROMTASK="TASK1" TOTASK="TASK2"/>
    <LINK FROMTASK="TASK2" TOTASK="TASK3" LABEL="SUCCESS"/>
</WORKFLOW>"""
        
        xml_file = tmp_path / "workflow_links.xml"
        xml_file.write_text(xml_content)
        
        parser = WorkflowParser(str(xml_file))
        result = parser.parse()
        
        assert len(result["links"]) == 2
        
        # Check link structure
        link = result["links"][0]
        assert "from_task" in link or "from" in link
        assert "to_task" in link or "to" in link


class TestSessionParserComprehensive:
    """Comprehensive tests for SessionParser."""
    
    def test_parse_session_with_attributes(self, tmp_path):
        """Test parsing session with various attributes."""
        xml_content = """<?xml version="1.0"?>
<SESSION NAME="SESS_DETAILED" MAPPINGNAME="M_TEST" DESCRIPTION="Test session">
    <ATTRIBUTE NAME="SourceConnection" VALUE="DB_SOURCE"/>
    <ATTRIBUTE NAME="TargetConnection" VALUE="DB_TARGET"/>
    <ATTRIBUTE NAME="CommitInterval" VALUE="10000"/>
    <ATTRIBUTE NAME="StopOnErrors" VALUE="0"/>
    <ATTRIBUTE NAME="Override tracing" VALUE="Normal"/>
</SESSION>"""
        
        xml_file = tmp_path / "session_detailed.xml"
        xml_file.write_text(xml_content)
        
        parser = SessionParser(str(xml_file))
        result = parser.parse()
        
        assert result["name"] == "SESS_DETAILED"
        assert result["mapping"] == "M_TEST"
        assert "config" in result or "attributes" in result


class TestWorkletParserComprehensive:
    """Comprehensive tests for WorkletParser."""
    
    def test_parse_worklet_with_multiple_tasks(self, tmp_path):
        """Test parsing worklet with multiple tasks."""
        xml_content = """<?xml version="1.0"?>
<WORKLET NAME="WK_COMPLEX">
    <TASKINSTANCE NAME="SESS1" TASKTYPE="Session" DESCRIPTION="First session"/>
    <TASKINSTANCE NAME="SESS2" TASKTYPE="Session" DESCRIPTION="Second session"/>
    <TASKINSTANCE NAME="CMD1" TASKTYPE="Command" DESCRIPTION="Command task"/>
    <LINK FROMTASK="SESS1" TOTASK="SESS2"/>
    <LINK FROMTASK="SESS2" TOTASK="CMD1"/>
</WORKLET>"""
        
        xml_file = tmp_path / "worklet_complex.xml"
        xml_file.write_text(xml_content)
        
        parser = WorkletParser(str(xml_file))
        result = parser.parse()
        
        assert result["name"] == "WK_COMPLEX"
        assert len(result["tasks"]) == 3

