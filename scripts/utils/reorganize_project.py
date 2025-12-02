#!/usr/bin/env python3
"""
Project Reorganization Helper Script

This script helps reorganize the project structure according to the plan in
docs/reorganization_plan.md. It creates the new directory structure and
provides a dry-run mode to preview changes.

Usage:
    python scripts/utils/reorganize_project.py --dry-run    # Preview changes
    python scripts/utils/reorganize_project.py --execute     # Actually move files
"""

import os
import shutil
import argparse
from pathlib import Path
from typing import List, Tuple

# Define reorganization mappings: (source, destination, description)
REORGANIZATION_MAPPINGS = [
    # Root level markdown files → docs/
    ("canonical_model_deep_dive.md", "docs/modules/canonical_model_deep_dive.md", "Move canonical model doc"),
    ("informatica-to-databricks.md", "docs/reference/informatica-to-databricks.md", "Move reference doc"),
    ("solution.md", "docs/development/solution.md", "Move solution doc"),
    ("system_architecture.md", "docs/architecture/system_architecture.md", "Move architecture doc"),
    ("test_end_to_end.md", "docs/testing/test_end_to_end.md", "Move testing doc"),
    ("TESTING.md", "docs/testing/TESTING.md", "Move testing doc"),
    ("roadmap.md", "docs/reference/roadmap.md", "Move roadmap"),
    ("UI_Screen_Markups.pdf", "docs/reference/UI_Screen_Markups.pdf", "Move UI markups"),
    
    # Scripts → scripts/utils/
    ("scripts/cleanup.py", "scripts/utils/cleanup.py", "Move cleanup script"),
    ("scripts/check_neo4j_data.py", "scripts/utils/check_neo4j_data.py", "Move Neo4j check script"),
    ("scripts/check_neo4j_simple.py", "scripts/utils/check_neo4j_simple.py", "Move Neo4j simple check"),
    ("scripts/diagnose_neo4j.py", "scripts/utils/diagnose_neo4j.py", "Move Neo4j diagnose script"),
    ("scripts/generate_diff.py", "scripts/utils/generate_diff.py", "Move diff generator"),
    ("scripts/migrate_to_graph.py", "scripts/utils/migrate_to_graph.py", "Move migration script"),
    ("scripts/validate_graph_migration.py", "scripts/utils/validate_graph_migration.py", "Move validation script"),
    
    # Scripts → scripts/setup/
    ("scripts/setup_env.sh", "scripts/setup/setup_env.sh", "Move setup script"),
    ("scripts/setup_neo4j.sh", "scripts/setup/setup_neo4j.sh", "Move Neo4j setup"),
    
    # Scripts → scripts/dev/
    ("scripts/test_graph_store.py", "scripts/dev/test_graph_store.py", "Move graph store test"),
    ("scripts/test_llm_config.py", "scripts/dev/test_llm_config.py", "Move LLM config test"),
    ("scripts/test_frontend_integration.py", "scripts/dev/test_frontend_integration.py", "Move frontend test"),
    ("scripts/test_part1_part2_flow.py", "scripts/dev/test_part1_part2_flow.py", "Move flow test"),
    
    # Scripts → tests/e2e/
    ("scripts/test_ai_agents.py", "tests/e2e/test_ai_agents.py", "Move AI agents test"),
    ("scripts/test_samples.py", "tests/e2e/test_samples.py", "Move samples test"),
    # Note: test_flow.py stays in scripts/utils/ as it's a main workflow
    
    # Generated code → build/
    ("generated_code", "build/generated_code", "Move generated code"),
]

# Directories to create
NEW_DIRECTORIES = [
    "scripts/setup",
    "scripts/utils",
    "scripts/dev",
    "tests/e2e",
    "build",
    "build/generated_code",
    "docs/getting-started",
    "docs/api",
    "docs/modules",
    "docs/ai",
    "docs/deployment",
    "docs/development",
    "docs/testing",
    "docs/reference",
    "docs/archive",
]


def check_file_exists(filepath: str) -> bool:
    """Check if a file or directory exists."""
    return Path(filepath).exists()


def create_directories(dry_run: bool = True):
    """Create new directory structure."""
    print("\n📁 Creating new directories...")
    for dir_path in NEW_DIRECTORIES:
        if dry_run:
            print(f"   [DRY RUN] Would create: {dir_path}/")
        else:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            print(f"   ✅ Created: {dir_path}/")


def analyze_moves(dry_run: bool = True) -> Tuple[List[str], List[str]]:
    """Analyze what files would be moved."""
    missing_files = []
    existing_files = []
    
    print("\n📋 Analyzing files to move...")
    for source, dest, description in REORGANIZATION_MAPPINGS:
        if check_file_exists(source):
            existing_files.append((source, dest, description))
            if dry_run:
                print(f"   ✓ Found: {source} → {dest}")
        else:
            missing_files.append(source)
            if dry_run:
                print(f"   ⚠ Missing: {source}")
    
    return existing_files, missing_files


def move_files(existing_files: List[Tuple[str, str, str]], dry_run: bool = True):
    """Move files to new locations."""
    print("\n🚚 Moving files...")
    for source, dest, description in existing_files:
        source_path = Path(source)
        dest_path = Path(dest)
        
        # Create destination directory if needed
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        if dry_run:
            print(f"   [DRY RUN] Would move: {source} → {dest}")
        else:
            try:
                if source_path.is_dir():
                    shutil.move(str(source_path), str(dest_path))
                else:
                    shutil.move(str(source_path), str(dest_path))
                print(f"   ✅ Moved: {source} → {dest}")
            except Exception as e:
                print(f"   ❌ Failed to move {source}: {e}")


def reorganize_docs(dry_run: bool = True):
    """Reorganize documentation files."""
    print("\n📚 Reorganizing documentation...")
    
    # Docs reorganization mappings
    doc_moves = [
        ("docs/parsing.md", "docs/modules/parsing.md"),
        ("docs/canonical_model.md", "docs/modules/canonical_model.md"),
        ("docs/code_generators.md", "docs/modules/code_generators.md"),
        ("docs/expression_engine.md", "docs/modules/expression_engine.md"),
        ("docs/dag_engine.md", "docs/modules/dag_engine.md"),
        ("docs/code_generation_workflow.md", "docs/modules/code_generation_workflow.md"),
        ("docs/workflow_aware_code_generation.md", "docs/modules/workflow_aware_code_generation.md"),
        ("docs/ai_agents.md", "docs/ai/ai_agents.md"),
        ("docs/deployment.md", "docs/deployment/deployment.md"),
        ("docs/extensibility.md", "docs/deployment/extensibility.md"),
        ("docs/design_spec.md", "docs/development/design_spec.md"),
        ("docs/solution_process_details.md", "docs/development/solution_process_details.md"),
        ("docs/code_generation_fixes_summary.md", "docs/development/code_generation_fixes_summary.md"),
        ("docs/code_generation_issues_fixes.md", "docs/development/code_generation_issues_fixes.md"),
        ("docs/neo4j_persistence_fix.md", "docs/development/neo4j_persistence_fix.md"),
        ("docs/test_flow_guide.md", "docs/testing/test_flow_guide.md"),
        ("docs/phase1_phase2_testing_guide.md", "docs/testing/phase1_phase2_testing_guide.md"),
        ("docs/lakebridge_comparison.md", "docs/reference/lakebridge_comparison.md"),
        ("docs/implementation_summary.md", "docs/reference/implementation_summary.md"),
        ("docs/implementation_complete_summary.md", "docs/reference/implementation_complete_summary.md"),
        ("docs/next_steps_recommendations.md", "docs/reference/next_steps_recommendations.md"),
        ("docs/fix_graph_explorer_edges.md", "docs/archive/fix_graph_explorer_edges.md"),
        ("docs/graph_explorer_guide.md", "docs/archive/graph_explorer_guide.md"),
        ("docs/dag_json_format.md", "docs/archive/dag_json_format.md"),
        ("docs/neo4j_persistence_explanation.md", "docs/archive/neo4j_persistence_explanation.md"),
        ("docs/ui_enhancement_plan.md", "docs/archive/ui_enhancement_plan.md"),
        ("docs/ui_enhancement_implementation_plan.md", "docs/archive/ui_enhancement_implementation_plan.md"),
    ]
    
    for source, dest in doc_moves:
        if check_file_exists(source):
            if dry_run:
                print(f"   [DRY RUN] Would move: {source} → {dest}")
            else:
                try:
                    Path(dest).parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(source, dest)
                    print(f"   ✅ Moved: {source} → {dest}")
                except Exception as e:
                    print(f"   ❌ Failed to move {source}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Reorganize project structure according to reorganization plan"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without actually moving files"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually execute the reorganization (use with caution!)"
    )
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.execute:
        print("⚠️  Please specify --dry-run to preview or --execute to actually move files")
        parser.print_help()
        return
    
    dry_run = args.dry_run
    
    print("=" * 60)
    print("Project Reorganization Script")
    print("=" * 60)
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No files will be moved")
    else:
        print("\n⚠️  EXECUTE MODE - Files will be moved!")
        response = input("Are you sure you want to proceed? (yes/no): ")
        if response.lower() != "yes":
            print("❌ Cancelled.")
            return
    
    # Create new directories
    create_directories(dry_run=dry_run)
    
    # Analyze files
    existing_files, missing_files = analyze_moves(dry_run=dry_run)
    
    if missing_files:
        print(f"\n⚠️  Warning: {len(missing_files)} files not found (may have been moved already)")
    
    # Move files
    if existing_files:
        move_files(existing_files, dry_run=dry_run)
    
    # Reorganize docs
    reorganize_docs(dry_run=dry_run)
    
    print("\n" + "=" * 60)
    if dry_run:
        print("✅ Dry run complete. Review the changes above.")
        print("   Run with --execute to actually move files.")
    else:
        print("✅ Reorganization complete!")
        print("\n📝 Next steps:")
        print("   1. Update import paths in Python files")
        print("   2. Update references in documentation")
        print("   3. Update Makefile paths if needed")
        print("   4. Test that everything still works")
    print("=" * 60)


if __name__ == "__main__":
    main()

