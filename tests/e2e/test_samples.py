#!/usr/bin/env python3
"""Test script for sample workflow and mapping files."""
import sys
import os
from pathlib import Path

# Add project root and src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

from parser import WorkflowParser, MappingParser, SessionParser, WorkletParser
from normalizer import MappingNormalizer
from dag import DAGBuilder, DAGVisualizer
from generators import TestsGenerator, PySparkGenerator, DLTGenerator, SQLGenerator, SpecGenerator
from utils.logger import get_logger

logger = get_logger(__name__)


def test_workflow_parsing():
    """Test parsing workflow_complex.xml."""
    print("\n" + "="*80)
    print("TEST 1: Workflow Parsing")
    print("="*80)
    
    workflow_file = "samples/complex/workflow_complex.xml"
    if not os.path.exists(workflow_file):
        print(f"❌ File not found: {workflow_file}")
        return None
    
    try:
        parser = WorkflowParser(workflow_file)
        workflow_data = parser.parse()
        
        print(f"✅ Workflow parsed successfully!")
        print(f"   Name: {workflow_data.get('name', 'Unknown')}")
        print(f"   Tasks: {len(workflow_data.get('tasks', []))}")
        print(f"   Links: {len(workflow_data.get('links', []))}")
        
        # Print task details
        for task in workflow_data.get('tasks', []):
            print(f"   - Task: {task.get('name')} (Type: {task.get('type')})")
        
        # Print link details
        for link in workflow_data.get('links', []):
            print(f"   - Link: {link.get('from')} -> {link.get('to')}")
        
        return workflow_data
    except Exception as e:
        print(f"❌ Error parsing workflow: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_dag_building(workflow_data):
    """Test building DAG from workflow data."""
    print("\n" + "="*80)
    print("TEST 2: DAG Building")
    print("="*80)
    
    if not workflow_data:
        print("❌ No workflow data provided")
        return None
    
    try:
        dag_builder = DAGBuilder()
        dag = dag_builder.build(workflow_data)
        
        print(f"✅ DAG built successfully!")
        print(f"   Nodes: {len(dag.get('nodes', []))}")
        print(f"   Edges: {len(dag.get('edges', []))}")
        print(f"   Topological Order: {' -> '.join(dag.get('topological_order', []))}")
        print(f"   Execution Levels: {len(dag.get('execution_levels', []))}")
        
        # Print execution levels
        for i, level in enumerate(dag.get('execution_levels', [])):
            print(f"   Level {i+1}: {', '.join(level)}")
        
        return dag
    except Exception as e:
        print(f"❌ Error building DAG: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_dag_visualization(dag):
    """Test DAG visualization in different formats."""
    print("\n" + "="*80)
    print("TEST 3: DAG Visualization")
    print("="*80)
    
    if not dag:
        print("❌ No DAG data provided")
        return
    
    try:
        visualizer = DAGVisualizer()
        
        # Test DOT format
        print("\n📊 DOT Format:")
        dot_output = visualizer.visualize(dag, format="dot")
        print(dot_output[:500] + "..." if len(dot_output) > 500 else dot_output)
        
        # Test JSON format
        print("\n📊 JSON Format:")
        json_output = visualizer.visualize(dag, format="json")
        print(json_output[:500] + "..." if len(json_output) > 500 else json_output)
        
        # Test Mermaid format
        print("\n📊 Mermaid Format:")
        mermaid_output = visualizer.visualize(dag, format="mermaid")
        print(mermaid_output[:500] + "..." if len(mermaid_output) > 500 else mermaid_output)
        
        # Export to files
        print("\n💾 Exporting visualizations to files...")
        visualizer.export(dag, "dot", "test_output/dag")
        visualizer.export(dag, "json", "test_output/dag")
        visualizer.export(dag, "mermaid", "test_output/dag")
        print("✅ Visualizations exported to test_output/ directory")
        
    except Exception as e:
        print(f"❌ Error visualizing DAG: {e}")
        import traceback
        traceback.print_exc()


def test_mapping_parsing():
    """Test parsing mapping_complex.xml."""
    print("\n" + "="*80)
    print("TEST 4: Mapping Parsing")
    print("="*80)
    
    mapping_file = "samples/complex/mapping_complex.xml"
    if not os.path.exists(mapping_file):
        print(f"❌ File not found: {mapping_file}")
        return None
    
    try:
        parser = MappingParser(mapping_file)
        mapping_data = parser.parse()
        
        print(f"✅ Mapping parsed successfully!")
        print(f"   Name: {mapping_data.get('name', 'Unknown')}")
        print(f"   Transformations: {len(mapping_data.get('transformations', []))}")
        
        # Print transformation details
        for trans in mapping_data.get('transformations', []):
            trans_name = trans.get('name', 'Unknown')
            trans_type = trans.get('type', 'Unknown')
            print(f"   - {trans_name} ({trans_type})")
        
        return mapping_data
    except Exception as e:
        print(f"❌ Error parsing mapping: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_mapping_normalization(mapping_data):
    """Test normalizing mapping to canonical model."""
    print("\n" + "="*80)
    print("TEST 5: Mapping Normalization")
    print("="*80)
    
    if not mapping_data:
        print("❌ No mapping data provided")
        return None
    
    try:
        normalizer = MappingNormalizer()
        canonical_model = normalizer.normalize(mapping_data)
        
        print(f"✅ Mapping normalized successfully!")
        print(f"   Mapping Name: {canonical_model.get('mapping_name', 'Unknown')}")
        print(f"   Sources: {len(canonical_model.get('sources', []))}")
        print(f"   Targets: {len(canonical_model.get('targets', []))}")
        print(f"   Transformations: {len(canonical_model.get('transformations', []))}")
        print(f"   SCD Type: {canonical_model.get('scd_type', 'NONE')}")
        
        return canonical_model
    except Exception as e:
        print(f"❌ Error normalizing mapping: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_code_generation(canonical_model):
    """Test generating target architecture code from canonical model."""
    print("\n" + "="*80)
    print("TEST 6: Code Generation (PySpark, DLT, SQL)")
    print("="*80)
    
    if not canonical_model:
        print("❌ No canonical model provided")
        return
    
    try:
        mapping_name = canonical_model.get("mapping_name", "unknown").lower().replace(" ", "_")
        output_dir = f"generated_code/{mapping_name}"
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n📁 Output directory: {output_dir}")
        
        # Generate PySpark code
        print("\n📝 Generating PySpark code...")
        pyspark_generator = PySparkGenerator()
        pyspark_code = pyspark_generator.generate(canonical_model)
        pyspark_file = f"{output_dir}/pyspark_code.py"
        with open(pyspark_file, "w") as f:
            f.write(pyspark_code)
        print(f"✅ PySpark code generated ({len(pyspark_code)} characters)")
        print(f"   Saved to: {pyspark_file}")
        
        # Generate DLT code
        print("\n📝 Generating DLT code...")
        dlt_generator = DLTGenerator()
        dlt_code = dlt_generator.generate(canonical_model)
        dlt_file = f"{output_dir}/dlt_pipeline.py"
        with open(dlt_file, "w") as f:
            f.write(dlt_code)
        print(f"✅ DLT code generated ({len(dlt_code)} characters)")
        print(f"   Saved to: {dlt_file}")
        
        # Generate SQL code
        print("\n📝 Generating SQL code...")
        sql_generator = SQLGenerator()
        sql_code = sql_generator.generate(canonical_model)
        sql_file = f"{output_dir}/sql_queries.sql"
        with open(sql_file, "w") as f:
            f.write(sql_code)
        print(f"✅ SQL code generated ({len(sql_code)} characters)")
        print(f"   Saved to: {sql_file}")
        
        # Generate Spec/Markdown
        print("\n📝 Generating mapping specification...")
        spec_generator = SpecGenerator()
        spec_code = spec_generator.generate(canonical_model)
        spec_file = f"{output_dir}/mapping_spec.md"
        with open(spec_file, "w") as f:
            f.write(spec_code)
        print(f"✅ Mapping spec generated ({len(spec_code)} characters)")
        print(f"   Saved to: {spec_file}")
        
        # Show previews
        print("\n📄 PySpark Preview (first 300 chars):")
        print(pyspark_code[:300] + "...")
        print("\n📄 SQL Preview (first 300 chars):")
        print(sql_code[:300] + "...")
        
    except Exception as e:
        print(f"❌ Error generating code: {e}")
        import traceback
        traceback.print_exc()


def test_test_generation(canonical_model):
    """Test generating tests from canonical model."""
    print("\n" + "="*80)
    print("TEST 7: Test Generation")
    print("="*80)
    
    if not canonical_model:
        print("❌ No canonical model provided")
        return
    
    try:
        mapping_name = canonical_model.get("mapping_name", "unknown").lower().replace(" ", "_")
        output_dir = f"generated_code/{mapping_name}"
        os.makedirs(output_dir, exist_ok=True)
        
        test_generator = TestsGenerator()
        
        # Generate all tests
        print("\n📝 Generating all tests...")
        all_tests = test_generator.generate(canonical_model, test_type="all")
        
        # Save to file
        test_file = f"{output_dir}/generated_tests.py"
        with open(test_file, "w") as f:
            f.write(all_tests)
        print(f"✅ All tests generated ({len(all_tests)} characters)")
        print(f"   Saved to: {test_file}")
        
        # Generate test data
        print("\n📝 Generating test data...")
        test_data = test_generator.generate_test_data(canonical_model, num_rows=10)
        test_data_file = f"{output_dir}/test_data_generator.py"
        with open(test_data_file, "w") as f:
            f.write(test_data)
        print(f"✅ Test data generator created")
        print(f"   Saved to: {test_data_file}")
        
        # Show preview
        print("\n📄 Preview (first 500 chars):")
        print(all_tests[:500] + "...")
        
    except Exception as e:
        print(f"❌ Error generating tests: {e}")
        import traceback
        traceback.print_exc()


def test_worklet_parsing():
    """Test parsing worklet_complex.xml."""
    print("\n" + "="*80)
    print("TEST 8: Worklet Parsing")
    print("="*80)
    
    worklet_file = "samples/complex/worklet_complex.xml"
    if not os.path.exists(worklet_file):
        print(f"❌ File not found: {worklet_file}")
        return None
    
    try:
        parser = WorkletParser(worklet_file)
        worklet_data = parser.parse()
        
        print(f"✅ Worklet parsed successfully!")
        print(f"   Name: {worklet_data.get('name', 'Unknown')}")
        print(f"   Tasks: {len(worklet_data.get('tasks', []))}")
        
        return worklet_data
    except Exception as e:
        print(f"❌ Error parsing worklet: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_session_parsing():
    """Test parsing session_complex.xml."""
    print("\n" + "="*80)
    print("TEST 9: Session Parsing")
    print("="*80)
    
    session_file = "samples/complex/session_complex.xml"
    if not os.path.exists(session_file):
        print(f"❌ File not found: {session_file}")
        return None
    
    try:
        parser = SessionParser(session_file)
        session_data = parser.parse()
        
        print(f"✅ Session parsed successfully!")
        print(f"   Name: {session_data.get('name', 'Unknown')}")
        print(f"   Mapping: {session_data.get('mapping', 'Unknown')}")
        
        return session_data
    except Exception as e:
        print(f"❌ Error parsing session: {e}")
        import traceback
        traceback.print_exc()
        return None


def process_all_sample_files():
    """Process all XML files in samples directory (including simple/ and complex/ subfolders)."""
    print("\n" + "="*80)
    print("PROCESSING ALL SAMPLE FILES")
    print("="*80)
    
    samples_dir = Path("samples")
    if not samples_dir.exists():
        print(f"❌ Samples directory not found: {samples_dir}")
        return
    
    # Find all XML files recursively (in samples/ and subdirectories)
    xml_files = list(samples_dir.rglob("*.xml"))
    
    if not xml_files:
        print("❌ No XML files found in samples directory")
        return
    
    print(f"\n📁 Found {len(xml_files)} XML file(s) in samples directory:")
    for xml_file in xml_files:
        # Show relative path from samples/
        rel_path = xml_file.relative_to(samples_dir)
        print(f"   - {rel_path}")
    
    results = {
        "workflows": [],
        "mappings": [],
        "sessions": [],
        "worklets": []
    }
    
    # Process each file
    for xml_file in xml_files:
        filename = xml_file.name.lower()
        file_path = str(xml_file)
        
        print(f"\n{'='*80}")
        print(f"Processing: {xml_file.name}")
        print(f"{'='*80}")
        
        try:
            if "workflow" in filename:
                parser = WorkflowParser(file_path)
                data = parser.parse()
                results["workflows"].append({"file": xml_file.name, "data": data})
                print(f"✅ Workflow parsed: {data.get('name', 'Unknown')}")
                
                # Build DAG for this workflow
                dag_builder = DAGBuilder()
                dag = dag_builder.build(data)
                
                # Generate visualization for this workflow
                workflow_name = data.get('name', 'unknown').lower().replace(" ", "_")
                dag_dir = f"test_output/dags/{workflow_name}"
                os.makedirs(dag_dir, exist_ok=True)
                
                visualizer = DAGVisualizer()
                visualizer.export(dag, "dot", f"{dag_dir}/dag")
                visualizer.export(dag, "json", f"{dag_dir}/dag")
                visualizer.export(dag, "mermaid", f"{dag_dir}/dag")
                print(f"✅ DAG visualizations saved to: {dag_dir}/")
                
            elif "mapping" in filename:
                parser = MappingParser(file_path)
                data = parser.parse()
                results["mappings"].append({"file": xml_file.name, "data": data})
                print(f"✅ Mapping parsed: {data.get('name', 'Unknown')}")
                
                # Normalize and generate code
                normalizer = MappingNormalizer()
                canonical_model = normalizer.normalize(data)
                
                # Generate all code
                test_code_generation(canonical_model)
                test_test_generation(canonical_model)
                
            elif "session" in filename:
                parser = SessionParser(file_path)
                data = parser.parse()
                results["sessions"].append({"file": xml_file.name, "data": data})
                print(f"✅ Session parsed: {data.get('name', 'Unknown')}")
                
            elif "worklet" in filename:
                parser = WorkletParser(file_path)
                data = parser.parse()
                results["worklets"].append({"file": xml_file.name, "data": data})
                print(f"✅ Worklet parsed: {data.get('name', 'Unknown')}")
                
        except Exception as e:
            print(f"❌ Error processing {xml_file.name}: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print(f"\n{'='*80}")
    print("PROCESSING SUMMARY")
    print(f"{'='*80}")
    print(f"✅ Workflows processed: {len(results['workflows'])}")
    print(f"✅ Mappings processed: {len(results['mappings'])}")
    print(f"✅ Sessions processed: {len(results['sessions'])}")
    print(f"✅ Worklets processed: {len(results['worklets'])}")
    
    return results


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("SAMPLE FILES TESTING")
    print("="*80)
    print("\nTesting with sample Informatica XML files...")
    
    # Create output directories
    os.makedirs("test_output", exist_ok=True)
    os.makedirs("test_output/dags", exist_ok=True)
    os.makedirs("generated_code", exist_ok=True)
    
    # Process all sample files
    all_results = process_all_sample_files()
    
    # Also run individual tests for detailed output
    print("\n" + "="*80)
    print("DETAILED INDIVIDUAL TESTS")
    print("="*80)
    
    # Test 1: Workflow parsing
    workflow_data = test_workflow_parsing()
    
    # Test 2: DAG building
    dag = test_dag_building(workflow_data)
    
    # Test 3: DAG visualization
    if dag:
        test_dag_visualization(dag)
    
    # Test 4: Mapping parsing
    mapping_data = test_mapping_parsing()
    
    # Test 5: Mapping normalization
    canonical_model = test_mapping_normalization(mapping_data)
    
    # Test 6: Code generation (PySpark, DLT, SQL)
    if canonical_model:
        test_code_generation(canonical_model)
    
    # Test 7: Test generation
    if canonical_model:
        test_test_generation(canonical_model)
    
    # Test 8: Worklet parsing
    test_worklet_parsing()
    
    # Test 9: Session parsing
    test_session_parsing()
    
    print("\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)
    print("\n✅ All tests completed!")
    print("\n📁 Generated files:")
    print("\n  DAG Visualizations:")
    print("    - test_output/dag.* (Main workflow)")
    print("    - test_output/dags/<workflow_name>/dag.* (All workflows)")
    print("\n  Target Architecture Code (generated_code/):")
    if canonical_model:
        mapping_name = canonical_model.get("mapping_name", "unknown").lower().replace(" ", "_")
        print(f"    - {mapping_name}/pyspark_code.py")
        print(f"    - {mapping_name}/dlt_pipeline.py")
        print(f"    - {mapping_name}/sql_queries.sql")
        print(f"    - {mapping_name}/mapping_spec.md")
        print(f"    - {mapping_name}/generated_tests.py")
        print(f"    - {mapping_name}/test_data_generator.py")
    
    print("\n📊 To view DAG visualizations:")
    print("    - DOT: Use Graphviz or online viewer (https://dreampuf.github.io/GraphvizOnline/)")
    print("    - JSON: cat test_output/dag.json | python -m json.tool")
    print("    - Mermaid: Copy to https://mermaid.live/")
    print("    - Frontend: Open test_output/frontend_test.html or React app")


if __name__ == "__main__":
    main()

