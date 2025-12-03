#!/usr/bin/env python3
"""
Generate HTML diff reports comparing:
1. Parsed vs Enhanced canonical models
2. Generated code vs Reviewed/Fixed code
"""
import argparse
import json
import os
import sys
import glob
from pathlib import Path
from typing import Dict, Any, List, Optional
from difflib import unified_diff, HtmlDiff
import html
from datetime import datetime

# Add project root to path
# generate_diff.py is in scripts/utils/, so we need to go up 2 levels to get to project root
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))


class DiffGenerator:
    """Generate HTML diff reports for parsed vs enhanced models and code."""
    
    def __init__(self, workspace_dir: str = "workspace"):
        self.workspace_dir = workspace_dir
        # generate_diff.py is in scripts/utils/, so we need to go up 2 levels to get to project root
        self.project_root = Path(__file__).parent.parent.parent
        
    def generate_all_diffs(self, output_dir: str) -> Dict[str, Any]:
        """Generate all diff reports in HTML format.
        
        Args:
            output_dir: Directory to save diff reports
            
        Returns:
            Dictionary with diff results
        """
        print(f"\n{'='*60}")
        print("Generating HTML Diff Reports")
        print(f"{'='*60}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        results = {
            "model_diffs": [],
            "code_diffs": [],
            "summary": {}
        }
        
        # 1. Compare parsed vs enhanced canonical models
        print("\n📊 Comparing Parsed vs Enhanced Canonical Models...")
        model_diffs = self._diff_canonical_models_html(output_dir)
        results["model_diffs"] = model_diffs
        
        # 2. Compare generated vs reviewed code
        print("\n💻 Comparing Generated vs Reviewed Code...")
        code_diffs = self._diff_code_files_html(output_dir)
        results["code_diffs"] = code_diffs
        
        # Generate summary
        results["summary"] = {
            "model_diffs_count": len(model_diffs),
            "code_diffs_count": len(code_diffs),
            "models_with_changes": len([d for d in model_diffs if d.get("has_changes")]),
            "code_files_with_changes": len([d for d in code_diffs if d.get("has_changes")])
        }
        
        # Generate main HTML index
        self._generate_html_index(output_dir, results)
        
        # Save summary JSON
        summary_file = os.path.join(output_dir, "diff_summary.json")
        with open(summary_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📊 Diff Summary:")
        print(f"   Model diffs: {results['summary']['model_diffs_count']}")
        print(f"   Models with changes: {results['summary']['models_with_changes']}")
        print(f"   Code diffs: {results['summary']['code_diffs_count']}")
        print(f"   Code files with changes: {results['summary']['code_files_with_changes']}")
        print(f"📁 HTML Reports saved to: {output_dir}")
        print(f"📄 Main index: {os.path.join(output_dir, 'index.html')}")
        
        return results
    
    def _generate_html_index(self, output_dir: str, results: Dict[str, Any]):
        """Generate main HTML index page.
        
        Args:
            output_dir: Output directory
            results: Diff results dictionary
        """
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Diff Reports - Informatica Modernization</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4A90E2;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
        }}
        .section {{
            margin: 20px 0;
            padding: 15px;
            background: #f9f9f9;
            border-left: 4px solid #4A90E2;
        }}
        .file-list {{
            list-style: none;
            padding: 0;
        }}
        .file-item {{
            padding: 10px;
            margin: 5px 0;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        .file-item a {{
            text-decoration: none;
            color: #4A90E2;
            font-weight: bold;
        }}
        .file-item a:hover {{
            text-decoration: underline;
        }}
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
        }}
        .badge-changes {{
            background: #ff9800;
            color: white;
        }}
        .badge-no-changes {{
            background: #4caf50;
            color: white;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .summary-card {{
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 8px;
            text-align: center;
        }}
        .summary-card h3 {{
            margin: 0;
            font-size: 32px;
        }}
        .summary-card p {{
            margin: 5px 0 0 0;
            opacity: 0.9;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Diff Reports</h1>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary">
            <div class="summary-card">
                <h3>{results['summary']['model_diffs_count']}</h3>
                <p>Model Comparisons</p>
            </div>
            <div class="summary-card">
                <h3>{results['summary']['models_with_changes']}</h3>
                <p>Models with Changes</p>
            </div>
            <div class="summary-card">
                <h3>{results['summary']['code_diffs_count']}</h3>
                <p>Code Comparisons</p>
            </div>
            <div class="summary-card">
                <h3>{results['summary']['code_files_with_changes']}</h3>
                <p>Code Files with Changes</p>
            </div>
        </div>
        
        <div class="section">
            <h2>📋 A) Parse vs Enhance - Canonical Models</h2>
            <p>Comparison of parsed canonical models vs AI-enhanced models</p>
            <ul class="file-list">
"""
        
        for diff in results["model_diffs"]:
            mapping = diff.get("mapping", "unknown")
            has_changes = diff.get("has_changes", False)
            badge_class = "badge-changes" if has_changes else "badge-no-changes"
            badge_text = "Has Changes" if has_changes else "No Changes"
            changes_count = diff.get("changes_count", 0)
            
            if diff.get("diff_file"):
                html_content += f"""
                <li class="file-item">
                    <a href="{os.path.basename(diff['diff_file'])}">{mapping}</a>
                    <span class="badge {badge_class}">{badge_text}</span>
                    {f'<span style="color: #666; margin-left: 10px;">({changes_count} changes)</span>' if changes_count > 0 else ''}
                </li>
"""
            else:
                html_content += f"""
                <li class="file-item">
                    {mapping}
                    <span class="badge {badge_class}">{badge_text}</span>
                    <span style="color: #999; margin-left: 10px;">({diff.get('status', 'N/A')})</span>
                </li>
"""
        
        html_content += """
            </ul>
        </div>
        
        <div class="section">
            <h2>💻 B) Code vs Review - Generated Code</h2>
            <p>Comparison of generated code vs AI-reviewed and fixed code</p>
            <ul class="file-list">
"""
        
        for diff in results["code_diffs"]:
            file_path = diff.get("file", "unknown")
            has_changes = diff.get("has_changes", False)
            badge_class = "badge-changes" if has_changes else "badge-no-changes"
            badge_text = "Has Changes" if has_changes else "No Changes"
            additions = diff.get("additions", 0)
            deletions = diff.get("deletions", 0)
            
            if diff.get("diff_file"):
                html_content += f"""
                <li class="file-item">
                    <a href="{os.path.basename(diff['diff_file'])}">{file_path}</a>
                    <span class="badge {badge_class}">{badge_text}</span>
                    {f'<span style="color: #666; margin-left: 10px;">(+{additions} -{deletions} lines)</span>' if has_changes else ''}
                </li>
"""
            else:
                html_content += f"""
                <li class="file-item">
                    {file_path}
                    <span class="badge {badge_class}">{badge_text}</span>
                    <span style="color: #999; margin-left: 10px;">({diff.get('status', 'N/A')})</span>
                </li>
"""
        
        html_content += """
            </ul>
        </div>
    </div>
</body>
</html>
"""
        
        index_file = os.path.join(output_dir, "index.html")
        with open(index_file, 'w') as f:
            f.write(html_content)
    
    def _diff_canonical_models_html(self, output_dir: str) -> List[Dict[str, Any]]:
        """Compare parsed vs enhanced canonical models and generate HTML.
        
        Args:
            output_dir: Directory to save diff reports
            
        Returns:
            List of diff results
        """
        parsed_dir = os.path.join(self.project_root, self.workspace_dir, "parsed")
        enhanced_dir = os.path.join(self.project_root, self.workspace_dir, "parse_ai")
        
        # Debug: Show paths being used
        print(f"   🔍 Looking in parsed_dir: {parsed_dir}")
        print(f"   🔍 Looking in enhanced_dir: {enhanced_dir}")
        print(f"   🔍 Project root: {self.project_root}")
        print(f"   🔍 Workspace dir: {self.workspace_dir}")
        
        # Debug: Check if directories exist
        if not os.path.exists(parsed_dir):
            print(f"   ⚠️  Parsed directory does not exist: {parsed_dir}")
            return []
        if not os.path.exists(enhanced_dir):
            print(f"   ⚠️  Enhanced directory does not exist: {enhanced_dir}")
            return []
        
        diffs = []
        
        # Find all parsed models (only canonical models: mappings and mapplets)
        # Skip workflows, sessions, worklets, and summary files
        parsed_files = glob.glob(os.path.join(parsed_dir, "*.json"))
        print(f"   🔍 Found {len(parsed_files)} total JSON file(s) in parsed directory")
        
        # Filter: keep mappings and mapplets, exclude workflows/sessions/worklets/summaries
        parsed_files = [f for f in parsed_files 
                       if not os.path.basename(f).endswith("_summary.json")
                       and not os.path.basename(f).endswith("_workflow.json")
                       and not os.path.basename(f).endswith("_session.json")
                       and not os.path.basename(f).endswith("_worklet.json")
                       and not os.path.basename(f) == "parse_summary.json"]
        
        print(f"   📁 Found {len(parsed_files)} parsed model(s) to compare (after filtering)")
        if parsed_files:
            print(f"   📄 Files: {[os.path.basename(f) for f in parsed_files]}")
        
        for parsed_file in parsed_files:
            filename = os.path.basename(parsed_file)
            mapping_name = filename.replace(".json", "")
            enhanced_file = os.path.join(enhanced_dir, f"{mapping_name}_enhanced.json")
            
            if not os.path.exists(enhanced_file):
                print(f"   ⚠️  No enhanced version for {mapping_name} (looking for: {os.path.basename(enhanced_file)})")
                diffs.append({
                    "mapping": mapping_name,
                    "has_changes": False,
                    "status": "no_enhanced_version"
                })
                continue
            
            try:
                # Load both models
                with open(parsed_file, 'r') as f:
                    parsed_model = json.load(f)
                
                with open(enhanced_file, 'r') as f:
                    enhanced_model = json.load(f)
                
                # Compare models
                diff_result = self._compare_json_models(parsed_model, enhanced_model, mapping_name)
                
                # Generate HTML diff
                html_content = self._generate_model_diff_html(
                    mapping_name, parsed_model, enhanced_model, diff_result
                )
                
                # Save HTML diff report
                diff_file = os.path.join(output_dir, f"{mapping_name}_model_diff.html")
                with open(diff_file, 'w') as f:
                    f.write(html_content)
                
                print(f"   ✅ Compared {mapping_name}: {diff_result['changes_count']} changes detected")
                
                diffs.append({
                    "mapping": mapping_name,
                    "has_changes": diff_result["has_changes"],
                    "changes_count": diff_result["changes_count"],
                    "diff_file": diff_file,
                    "changes": diff_result["changes"]
                })
                
            except Exception as e:
                print(f"   ❌ Failed to diff {mapping_name}: {e}")
                diffs.append({
                    "mapping": mapping_name,
                    "has_changes": False,
                    "status": "error",
                    "error": str(e)
                })
        
        return diffs
    
    def _generate_model_diff_html(self, mapping_name: str, parsed: Dict, enhanced: Dict, diff_result: Dict) -> str:
        """Generate HTML diff for canonical models.
        
        Args:
            mapping_name: Name of the mapping
            parsed: Parsed canonical model
            enhanced: Enhanced canonical model
            diff_result: Diff comparison result
            
        Returns:
            HTML content
        """
        sections_html = []
        
        # Compare sections
        sections_to_compare = [
            ("sources", "Sources", "Source definitions"),
            ("targets", "Targets", "Target definitions"),
            ("transformations", "Transformations", "Transformation logic"),
            ("connectors", "Connectors", "Data flow connections"),
            ("lineage", "Lineage", "Data lineage information")
        ]
        
        for section_key, section_name, section_desc in sections_to_compare:
            parsed_section = parsed.get(section_key, [])
            enhanced_section = enhanced.get(section_key, [])
            
            if parsed_section != enhanced_section:
                sections_html.append(f"""
                <div class="section-diff">
                    <h3>{section_name}</h3>
                    <p class="section-desc">{section_desc}</p>
                    <div class="comparison">
                        <div class="side">
                            <h4>Parsed</h4>
                            <pre>{html.escape(json.dumps(parsed_section, indent=2, default=str))}</pre>
                        </div>
                        <div class="side">
                            <h4>Enhanced</h4>
                            <pre>{html.escape(json.dumps(enhanced_section, indent=2, default=str))}</pre>
                        </div>
                    </div>
                </div>
""")
        
        # Check for enhancement metadata
        enhancement_keys = ["_optimization_hint", "_data_quality_rules", "_performance_metadata", "_provenance"]
        enhancements_html = []
        
        for key in enhancement_keys:
            if key in enhanced:
                if key not in parsed:
                    enhancements_html.append(f"""
                    <div class="enhancement-new">
                        <h4>✨ New: {key}</h4>
                        <pre>{html.escape(json.dumps(enhanced[key], indent=2, default=str))}</pre>
                    </div>
""")
                elif enhanced[key] != parsed[key]:
                    enhancements_html.append(f"""
                    <div class="enhancement-changed">
                        <h4>🔄 Updated: {key}</h4>
                        <div class="comparison">
                            <div class="side">
                                <h5>Before</h5>
                                <pre>{html.escape(json.dumps(parsed[key], indent=2, default=str))}</pre>
                            </div>
                            <div class="side">
                                <h5>After</h5>
                                <pre>{html.escape(json.dumps(enhanced[key], indent=2, default=str))}</pre>
                            </div>
                        </div>
                    </div>
""")
        
        if enhancements_html:
            sections_html.append(f"""
                <div class="section-diff enhancements">
                    <h3>🤖 AI Enhancements</h3>
                    {''.join(enhancements_html)}
                </div>
""")
        
        if not sections_html:
            sections_html.append("""
                <div class="no-changes">
                    <p>✅ No changes detected between parsed and enhanced models.</p>
                </div>
""")
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Model Diff: {mapping_name}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4A90E2;
            padding-bottom: 10px;
        }}
        .section-diff {{
            margin: 30px 0;
            padding: 20px;
            background: #f9f9f9;
            border-left: 4px solid #4A90E2;
            border-radius: 4px;
        }}
        .section-diff h3 {{
            margin-top: 0;
            color: #4A90E2;
        }}
        .section-desc {{
            color: #666;
            font-style: italic;
            margin-bottom: 15px;
        }}
        .comparison {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 15px;
        }}
        .side {{
            background: white;
            padding: 15px;
            border-radius: 4px;
            border: 1px solid #ddd;
        }}
        .side h4, .side h5 {{
            margin-top: 0;
            color: #555;
        }}
        pre {{
            background: #f5f5f5;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
            font-size: 12px;
            line-height: 1.4;
        }}
        .enhancement-new {{
            background: #e8f5e9;
            padding: 15px;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .enhancement-changed {{
            background: #fff3e0;
            padding: 15px;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .no-changes {{
            text-align: center;
            padding: 40px;
            color: #4caf50;
            font-size: 18px;
        }}
        .back-link {{
            display: inline-block;
            margin-bottom: 20px;
            color: #4A90E2;
            text-decoration: none;
        }}
        .back-link:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <a href="index.html" class="back-link">← Back to Index</a>
        <h1>📊 Model Diff: {mapping_name}</h1>
        <p><strong>Comparison:</strong> Parsed vs Enhanced Canonical Model</p>
        <p><strong>Changes:</strong> {diff_result['changes_count']} detected</p>
        
        {''.join(sections_html)}
    </div>
</body>
</html>
"""
        
        return html_content
    
    def _compare_json_models(self, parsed: Dict, enhanced: Dict, name: str) -> Dict[str, Any]:
        """Compare two JSON models and generate diff.
        
        Args:
            parsed: Parsed canonical model
            enhanced: Enhanced canonical model
            name: Model name
            
        Returns:
            Dictionary with diff information
        """
        changes = []
        has_changes = False
        
        # Compare key sections
        sections_to_compare = [
            ("sources", "Sources"),
            ("targets", "Targets"),
            ("transformations", "Transformations"),
            ("connectors", "Connectors"),
            ("lineage", "Lineage")
        ]
        
        for section_key, section_name in sections_to_compare:
            parsed_section = parsed.get(section_key, [])
            enhanced_section = enhanced.get(section_key, [])
            
            if parsed_section != enhanced_section:
                has_changes = True
                
                # Count differences
                if isinstance(parsed_section, list):
                    parsed_count = len(parsed_section)
                    enhanced_count = len(enhanced_section)
                    if parsed_count != enhanced_count:
                        changes.append(f"{section_name}: count changed ({parsed_count} → {enhanced_count})")
                    else:
                        changes.append(f"{section_name}: structure changed")
                else:
                    changes.append(f"{section_name}: structure changed")
        
        # Check for enhancement metadata
        enhancement_keys = ["_optimization_hint", "_data_quality_rules", "_performance_metadata", "_provenance"]
        for key in enhancement_keys:
            if key in enhanced and key not in parsed:
                has_changes = True
                changes.append(f"Added: {key}")
            elif key in enhanced and key in parsed and enhanced[key] != parsed[key]:
                has_changes = True
                changes.append(f"Updated: {key}")
        
        return {
            "has_changes": has_changes,
            "changes_count": len(changes),
            "changes": changes
        }
    
    def _diff_code_files_html(self, output_dir: str) -> List[Dict[str, Any]]:
        """Compare generated vs reviewed code files and generate HTML.
        
        Args:
            output_dir: Directory to save diff reports
            
        Returns:
            List of diff results
        """
        generated_dir = os.path.join(self.project_root, self.workspace_dir, "generated")
        reviewed_dir = os.path.join(self.project_root, self.workspace_dir, "generated_ai")
        
        diffs = []
        
        # Find all generated code files
        code_extensions = ["*.py", "*.sql"]
        generated_files = []
        for ext in code_extensions:
            generated_files.extend(glob.glob(os.path.join(generated_dir, "**", ext), recursive=True))
        
        # Also find all reviewed code files for reverse lookup
        reviewed_files = []
        for ext in code_extensions:
            reviewed_files.extend(glob.glob(os.path.join(reviewed_dir, "**", ext), recursive=True))
        
        # Create a map of reviewed files by their base name (for matching)
        reviewed_files_map = {}
        for reviewed_file in reviewed_files:
            base_name = os.path.basename(reviewed_file)
            # Remove common suffixes like _pyspark, _fixed, _reviewed
            base_name_clean = base_name.replace("_pyspark", "").replace("_fixed", "").replace("_reviewed", "")
            if base_name_clean not in reviewed_files_map:
                reviewed_files_map[base_name_clean] = []
            reviewed_files_map[base_name_clean].append(reviewed_file)
        
        for generated_file in generated_files:
            rel_path = os.path.relpath(generated_file, generated_dir)
            # Preserve directory structure when looking for reviewed file
            reviewed_file = os.path.join(reviewed_dir, rel_path)
            
            # Also check flat structure (backward compatibility)
            if not os.path.exists(reviewed_file):
                reviewed_file_flat = os.path.join(reviewed_dir, os.path.basename(generated_file))
                if os.path.exists(reviewed_file_flat):
                    reviewed_file = reviewed_file_flat
            
            # Check for renamed files (AI review may rename files, e.g., airflow_dag.py -> airflow_dag_pyspark.py)
            if not os.path.exists(reviewed_file):
                base_name = os.path.basename(generated_file)
                base_name_no_ext, ext = os.path.splitext(base_name)
                dir_path = os.path.dirname(os.path.join(reviewed_dir, rel_path))
                
                # Try common rename patterns
                rename_patterns = [
                    f"{base_name_no_ext}_pyspark{ext}",
                    f"{base_name_no_ext}_fixed{ext}",
                    f"{base_name_no_ext}_reviewed{ext}",
                ]
                
                for pattern in rename_patterns:
                    renamed_file = os.path.join(dir_path, pattern)
                    if os.path.exists(renamed_file):
                        reviewed_file = renamed_file
                        break
                
                # Also try in flat structure
                if not os.path.exists(reviewed_file):
                    for pattern in rename_patterns:
                        renamed_file_flat = os.path.join(reviewed_dir, pattern)
                        if os.path.exists(renamed_file_flat):
                            reviewed_file = renamed_file_flat
                            break
                
                # Use reverse lookup map to find reviewed file by base name (cleaned)
                base_name_clean = base_name.replace("_pyspark", "").replace("_fixed", "").replace("_reviewed", "")
                if not os.path.exists(reviewed_file) and base_name_clean in reviewed_files_map:
                    # Find the reviewed file in the same directory structure if possible
                    for candidate in reviewed_files_map[base_name_clean]:
                        candidate_rel = os.path.relpath(candidate, reviewed_dir)
                        # Check if directory structure matches
                        if os.path.dirname(candidate_rel) == os.path.dirname(rel_path):
                            reviewed_file = candidate
                            break
                    # If no match in same directory, use first available
                    if not os.path.exists(reviewed_file) and reviewed_files_map[base_name_clean]:
                        reviewed_file = reviewed_files_map[base_name_clean][0]
            
            if not os.path.exists(reviewed_file):
                # Check if there's a review JSON instead (preserve structure)
                review_json = os.path.join(reviewed_dir, rel_path.replace(".py", "_review.json").replace(".sql", "_review.json"))
                if not os.path.exists(review_json):
                    # Try flat structure
                    review_json = os.path.join(reviewed_dir, os.path.basename(generated_file).replace(".py", "_review.json").replace(".sql", "_review.json"))
                if os.path.exists(review_json):
                    # Code was reviewed but not fixed
                    diffs.append({
                        "file": rel_path,
                        "has_changes": False,
                        "status": "reviewed_but_not_fixed"
                    })
                continue
            
            try:
                # Read both files
                with open(generated_file, 'r') as f:
                    generated_code = f.read()
                
                with open(reviewed_file, 'r') as f:
                    reviewed_code = f.read()
                
                # Generate unified diff for counting
                generated_lines = generated_code.splitlines(keepends=True)
                reviewed_lines = reviewed_code.splitlines(keepends=True)
                
                diff_lines = list(unified_diff(
                    generated_lines,
                    reviewed_lines,
                    fromfile=f"generated/{rel_path}",
                    tofile=f"reviewed/{os.path.basename(reviewed_file)}",
                    lineterm=''
                ))
                
                has_changes = len(diff_lines) > 0
                
                if has_changes:
                    # Generate HTML diff using HtmlDiff
                    html_diff = HtmlDiff(wrapcolumn=80)
                    html_content = html_diff.make_file(
                        generated_lines,
                        reviewed_lines,
                        fromdesc=f"Generated: {rel_path}",
                        todesc=f"Reviewed: {os.path.basename(reviewed_file)}",
                        context=True,
                        numlines=3
                    )
                    
                    # Add back link and styling improvements
                    html_content = html_content.replace(
                        '<body>',
                        '''<body>
    <div style="padding: 10px; background: #f5f5f5; border-bottom: 1px solid #ddd;">
        <a href="index.html" style="color: #4A90E2; text-decoration: none;">← Back to Index</a>
    </div>'''
                    )
                    
                    # Save HTML diff
                    diff_file_name = rel_path.replace("/", "_").replace("\\", "_") + "_code_diff.html"
                    diff_file = os.path.join(output_dir, diff_file_name)
                    
                    with open(diff_file, 'w') as f:
                        f.write(html_content)
                    
                    # Count changes
                    additions = len([l for l in diff_lines if l.startswith('+') and not l.startswith('+++')])
                    deletions = len([l for l in diff_lines if l.startswith('-') and not l.startswith('---')])
                    
                    print(f"   ✅ HTML diff generated: {rel_path} (+{additions} -{deletions} lines)")
                    
                    diffs.append({
                        "file": rel_path,
                        "has_changes": True,
                        "additions": additions,
                        "deletions": deletions,
                        "diff_file": diff_file
                    })
                else:
                    diffs.append({
                        "file": rel_path,
                        "has_changes": False,
                        "status": "no_changes"
                    })
                
            except Exception as e:
                print(f"   ❌ Failed to diff {rel_path}: {e}")
                diffs.append({
                    "file": rel_path,
                    "has_changes": False,
                    "status": "error",
                    "error": str(e)
                })
        
        return diffs


def main():
    parser = argparse.ArgumentParser(description="Generate HTML diff reports for parsed vs enhanced models and code")
    parser.add_argument("--workspace-dir", default="workspace", help="Workspace directory")
    parser.add_argument("--output-dir", default="test_log/diffs", help="Output directory for diff reports")
    
    args = parser.parse_args()
    
    generator = DiffGenerator(workspace_dir=args.workspace_dir)
    generator.generate_all_diffs(args.output_dir)


if __name__ == "__main__":
    main()
