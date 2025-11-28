#!/usr/bin/env python3
"""Test script for frontend lineage visualization integration."""
import sys
import os
import requests
import json
import time
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000"
SAMPLES_DIR = "samples"
WORKFLOW_FILE = "samples/complex/workflow_complex.xml"
MAPPING_FILE = "samples/complex/mapping_complex.xml"


def check_api_health():
    """Check if API is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is running")
            return True
        else:
            print(f"❌ API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Is it running?")
        print(f"   Expected URL: {API_BASE_URL}")
        print("\n   To start the API, run:")
        print("   cd src && uvicorn api.app:app --reload --port 8000")
        return False
    except Exception as e:
        print(f"❌ Error checking API: {e}")
        return False


def upload_file(file_path, file_type="workflow"):
    """Upload a file to the API."""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return None
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'application/xml')}
            response = requests.post(f"{API_BASE_URL}/api/v1/upload", files=files)
        
        if response.status_code == 201:
            data = response.json()
            file_id = data.get('file_id')
            print(f"✅ File uploaded: {os.path.basename(file_path)}")
            print(f"   File ID: {file_id}")
            return file_id
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error uploading file: {e}")
        return None


def parse_workflow(file_id):
    """Parse workflow file."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/parse/workflow",
            json={"file_id": file_id}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Workflow parsed successfully")
            return data
        else:
            print(f"❌ Parse failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error parsing workflow: {e}")
        return None


def build_dag(file_id):
    """Build DAG from workflow."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/dag/build",
            json={"file_id": file_id}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ DAG built successfully")
                print(f"   Nodes: {len(data.get('nodes', []))}")
                print(f"   Edges: {len(data.get('edges', []))}")
                return data
            else:
                print(f"❌ DAG build failed: {data.get('message')}")
                return None
        else:
            print(f"❌ DAG build failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error building DAG: {e}")
        return None


def visualize_dag(file_id, format="json"):
    """Get DAG visualization."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/dag/visualize",
            params={"format": format, "include_metadata": "false"},
            json={"file_id": file_id}
        )
        
        if response.status_code == 200:
            if format == "json":
                data = response.json()
                print(f"✅ DAG visualization retrieved (JSON)")
                return data
            else:
                content = response.text
                print(f"✅ DAG visualization retrieved ({format})")
                print(f"   Content length: {len(content)} characters")
                return content
        else:
            print(f"❌ Visualization failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error getting visualization: {e}")
        return None


def test_all_endpoints():
    """Test all relevant endpoints."""
    print("\n" + "="*80)
    print("FRONTEND INTEGRATION TEST")
    print("="*80)
    
    # Check API health
    print("\n1. Checking API health...")
    if not check_api_health():
        return None
    
    # Upload workflow file
    print("\n2. Uploading workflow file...")
    workflow_file_id = upload_file(WORKFLOW_FILE)
    if not workflow_file_id:
        return None
    
    # Parse workflow
    print("\n3. Parsing workflow...")
    parse_result = parse_workflow(workflow_file_id)
    if not parse_result:
        return None
    
    # Build DAG
    print("\n4. Building DAG...")
    dag_result = build_dag(workflow_file_id)
    if not dag_result:
        return None
    
    # Get visualizations in different formats
    print("\n5. Getting DAG visualizations...")
    dag_json = visualize_dag(workflow_file_id, "json")
    dag_dot = visualize_dag(workflow_file_id, "dot")
    dag_mermaid = visualize_dag(workflow_file_id, "mermaid")
    
    # Save results for frontend testing
    test_data = {
        "file_id": workflow_file_id,
        "workflow_name": dag_result.get('dag', {}).get('workflow_name', 'Unknown'),
        "dag": dag_result.get('dag', {}),
        "visualizations": {
            "json": dag_json if isinstance(dag_json, dict) else None,
            "dot": dag_dot if isinstance(dag_dot, str) else None,
            "mermaid": dag_mermaid if isinstance(dag_mermaid, str) else None
        }
    }
    
    # Save to file for frontend
    os.makedirs("test_output", exist_ok=True)
    with open("test_output/frontend_test_data.json", "w") as f:
        json.dump(test_data, f, indent=2)
    
    print("\n✅ All API tests passed!")
    print(f"\n📁 Test data saved to: test_output/frontend_test_data.json")
    print(f"\n📋 Frontend Test Data:")
    print(f"   File ID: {workflow_file_id}")
    print(f"   Workflow: {test_data['workflow_name']}")
    print(f"   Nodes: {len(dag_result.get('nodes', []))}")
    print(f"   Edges: {len(dag_result.get('edges', []))}")
    
    return test_data


def create_frontend_test_page():
    """Create a simple HTML test page for frontend testing."""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lineage Visualization Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }
        .test-section {
            margin: 20px 0;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .success {
            color: #4CAF50;
        }
        .error {
            color: #f44336;
        }
        pre {
            background: #f5f5f5;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }
        button {
            padding: 10px 20px;
            background: #2196F3;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin: 5px;
        }
        button:hover {
            background: #1976D2;
        }
        #dag-container {
            border: 1px solid #ddd;
            padding: 20px;
            margin-top: 20px;
            min-height: 400px;
            background: #f9f9f9;
        }
    </style>
</head>
<body>
    <h1>Lineage Visualization Test</h1>
    
    <div class="test-section">
        <h2>API Connection Test</h2>
        <button onclick="testAPI()">Test API Connection</button>
        <div id="api-status"></div>
    </div>
    
    <div class="test-section">
        <h2>File Upload Test</h2>
        <input type="file" id="fileInput" accept=".xml">
        <button onclick="uploadFile()">Upload File</button>
        <div id="upload-status"></div>
    </div>
    
    <div class="test-section">
        <h2>DAG Visualization Test</h2>
        <input type="text" id="fileIdInput" placeholder="Enter File ID">
        <button onclick="loadDAG()">Load DAG</button>
        <div id="dag-status"></div>
        <div id="dag-container"></div>
    </div>
    
    <div class="test-section">
        <h2>Test Data</h2>
        <pre id="test-data"></pre>
    </div>
    
    <script>
        const API_BASE_URL = 'http://localhost:8000';
        
        async function testAPI() {
            const statusDiv = document.getElementById('api-status');
            try {
                const response = await fetch(`${API_BASE_URL}/health`);
                const data = await response.json();
                statusDiv.innerHTML = `<span class="success">✅ API is running</span><br>${JSON.stringify(data, null, 2)}`;
            } catch (error) {
                statusDiv.innerHTML = `<span class="error">❌ API connection failed: ${error.message}</span>`;
            }
        }
        
        async function uploadFile() {
            const fileInput = document.getElementById('fileInput');
            const statusDiv = document.getElementById('upload-status');
            
            if (!fileInput.files[0]) {
                statusDiv.innerHTML = '<span class="error">Please select a file</span>';
                return;
            }
            
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            
            try {
                const response = await fetch(`${API_BASE_URL}/api/v1/upload`, {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                if (response.ok) {
                    statusDiv.innerHTML = `<span class="success">✅ File uploaded</span><br>File ID: ${data.file_id}`;
                    document.getElementById('fileIdInput').value = data.file_id;
                } else {
                    statusDiv.innerHTML = `<span class="error">❌ Upload failed: ${data.detail || data.message}</span>`;
                }
            } catch (error) {
                statusDiv.innerHTML = `<span class="error">❌ Error: ${error.message}</span>`;
            }
        }
        
        async function loadDAG() {
            const fileId = document.getElementById('fileIdInput').value;
            const statusDiv = document.getElementById('dag-status');
            const container = document.getElementById('dag-container');
            
            if (!fileId) {
                statusDiv.innerHTML = '<span class="error">Please enter a File ID</span>';
                return;
            }
            
            try {
                // Build DAG
                const buildResponse = await fetch(`${API_BASE_URL}/api/v1/dag/build`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({file_id: fileId})
                });
                
                const buildData = await buildResponse.json();
                
                if (buildData.success) {
                    statusDiv.innerHTML = `<span class="success">✅ DAG loaded</span><br>Nodes: ${buildData.nodes.length}, Edges: ${buildData.edges.length}`;
                    
                    // Render simple visualization
                    renderDAG(buildData.dag, container);
                    
                    // Update test data
                    document.getElementById('test-data').textContent = JSON.stringify(buildData, null, 2);
                } else {
                    statusDiv.innerHTML = `<span class="error">❌ DAG build failed: ${buildData.message}</span>`;
                }
            } catch (error) {
                statusDiv.innerHTML = `<span class="error">❌ Error: ${error.message}</span>`;
            }
        }
        
        function renderDAG(dag, container) {
            const nodes = dag.nodes || [];
            const edges = dag.edges || [];
            
            let html = '<h3>DAG Visualization</h3>';
            html += '<svg width="800" height="400" style="border: 1px solid #ccc; background: white;">';
            
            // Simple node positioning
            const nodePositions = {};
            const levelWidth = 200;
            const nodeHeight = 80;
            const startY = 50;
            
            // Group nodes by execution level
            const levels = dag.execution_levels || [dag.topological_order || []];
            
            levels.forEach((level, levelIdx) => {
                level.forEach((nodeId, nodeIdx) => {
                    const node = nodes.find(n => (n.id || n.name) === nodeId);
                    if (node) {
                        nodePositions[nodeId] = {
                            x: levelIdx * levelWidth + 50,
                            y: startY + nodeIdx * (nodeHeight + 20)
                        };
                    }
                });
            });
            
            // Draw edges
            edges.forEach(edge => {
                const fromPos = nodePositions[edge.from];
                const toPos = nodePositions[edge.to];
                if (fromPos && toPos) {
                    html += `<line x1="${fromPos.x + 100}" y1="${fromPos.y + 40}" x2="${toPos.x}" y2="${toPos.y + 40}" stroke="#666" stroke-width="2" marker-end="url(#arrowhead)"/>`;
                }
            });
            
            // Draw nodes
            nodes.forEach(node => {
                const nodeId = node.id || node.name;
                const pos = nodePositions[nodeId] || {x: 50, y: 50};
                const nodeType = node.type || 'Unknown';
                const colors = {
                    'Session': '#dae8fc',
                    'Worklet': '#fff2cc',
                    'Mapping': '#d5e8d4',
                    'default': '#f5f5f5'
                };
                const color = colors[nodeType] || colors.default;
                
                html += `<rect x="${pos.x}" y="${pos.y}" width="120" height="80" fill="${color}" stroke="#333" stroke-width="2" rx="5"/>`;
                html += `<text x="${pos.x + 60}" y="${pos.y + 30}" text-anchor="middle" font-size="12" font-weight="bold">${node.name || nodeId}</text>`;
                html += `<text x="${pos.x + 60}" y="${pos.y + 50}" text-anchor="middle" font-size="10">${nodeType}</text>`;
            });
            
            // Arrow marker
            html += '<defs><marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><polygon points="0 0, 10 3, 0 6" fill="#666"/></marker></defs>';
            
            html += '</svg>';
            
            // Add execution levels info
            if (dag.execution_levels) {
                html += '<h4>Execution Levels:</h4><ul>';
                dag.execution_levels.forEach((level, idx) => {
                    html += `<li>Level ${idx + 1}: ${level.join(', ')}</li>`;
                });
                html += '</ul>';
            }
            
            container.innerHTML = html;
        }
        
        // Load test data if available
        window.addEventListener('load', async () => {
            try {
                const response = await fetch('test_output/frontend_test_data.json');
                if (response.ok) {
                    const data = await response.json();
                    document.getElementById('fileIdInput').value = data.file_id;
                    document.getElementById('test-data').textContent = JSON.stringify(data, null, 2);
                }
            } catch (e) {
                console.log('Test data not found, will need to upload file');
            }
        });
    </script>
</body>
</html>
"""
    
    os.makedirs("test_output", exist_ok=True)
    with open("test_output/frontend_test.html", "w") as f:
        f.write(html_content)
    
    print(f"\n📄 Frontend test page created: test_output/frontend_test.html")
    print(f"   Open this file in a browser to test the frontend integration")


def main():
    """Main test function."""
    print("\n" + "="*80)
    print("FRONTEND LINEAGE VISUALIZATION TEST")
    print("="*80)
    
    # Test API endpoints
    test_data = test_all_endpoints()
    
    if test_data:
        # Create frontend test page
        print("\n6. Creating frontend test page...")
        create_frontend_test_page()
        
        print("\n" + "="*80)
        print("TESTING COMPLETE")
        print("="*80)
        print("\n✅ All API tests passed!")
        print("\n📋 Next Steps:")
        print("   1. Ensure API is running: uvicorn api.app:app --reload --port 8000")
        print("   2. Open test_output/frontend_test.html in a browser")
        print("   3. Or start the React frontend: cd frontend && npm run dev")
        print("   4. Use File ID from above to test lineage visualization")
        print(f"\n   Test File ID: {test_data['file_id']}")
    else:
        print("\n❌ Some tests failed. Please check the API is running.")


if __name__ == "__main__":
    main()

