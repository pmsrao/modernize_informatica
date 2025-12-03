#!/usr/bin/env python3
"""
Sync Generated Code to Generated AI Directory

This script ensures that all code files from `generated/` are copied to `generated_ai/`
if they don't already exist there. This makes `generated_ai` the source of truth.

Files that don't need AI review should still be copied to `generated_ai` so that
the directory contains all generated code.

This script respects the naming convention used by the review process:
- Python files get `_pyspark.py` suffix
- DLT files get `_dlt.py` suffix  
- SQL files get `_sql.sql` suffix

Usage:
    python scripts/sync_generated_to_ai.py
"""

import os
import shutil
from pathlib import Path
from typing import List, Tuple

def detect_code_type(code_content: str, filename: str) -> str:
    """Detect code type from content.
    
    Args:
        code_content: Code file content
        filename: Filename
        
    Returns:
        Code type: 'python', 'dlt', or 'sql'
    """
    code_lower = code_content.lower()
    
    # Check for PySpark indicators
    pyspark_indicators = [
        "from pyspark",
        "import pyspark",
        "spark.createDataFrame",
        "spark.table(",
        "df.write",
        "spark.sql("
    ]
    
    # Check for DLT indicators
    dlt_indicators = [
        "@dlt.table",
        "import dlt",
        "dlt.read(",
        "dlt.table("
    ]
    
    # Check for SQL indicators
    sql_indicators = [
        "select ",
        "from ",
        "where ",
        "insert into",
        "create table"
    ]
    
    pyspark_count = sum(1 for indicator in pyspark_indicators if indicator in code_lower)
    dlt_count = sum(1 for indicator in dlt_indicators if indicator in code_lower)
    sql_count = sum(1 for indicator in sql_indicators if indicator in code_lower and 
                    not any(p in code_lower for p in pyspark_indicators))
    
    if dlt_count > 0:
        return "dlt"
    elif pyspark_count > 0 or filename.endswith('.py'):
        return "python"
    elif sql_count > 0 or filename.endswith('.sql'):
        return "sql"
    else:
        # Default to python for .py files
        return "python" if filename.endswith('.py') else "sql"

def get_output_filename(filename: str, code_type: str) -> str:
    """Get output filename with correct suffix based on code type.
    
    Args:
        filename: Original filename
        code_type: Detected code type
        
    Returns:
        Output filename with correct suffix
    """
    base_name = os.path.splitext(filename)[0]
    # Remove existing type suffix if present
    for suffix in ["_pyspark", "_dlt", "_sql"]:
        if base_name.endswith(suffix):
            base_name = base_name[:-len(suffix)]
            break
    
    if code_type == "python":
        return f"{base_name}_pyspark.py"
    elif code_type == "dlt":
        return f"{base_name}_dlt.py"
    elif code_type == "sql":
        return f"{base_name}_sql.sql"
    else:
        return filename

def find_code_files(directory: Path) -> List[Path]:
    """Find all code files in directory.
    
    Args:
        directory: Directory to search
        
    Returns:
        List of code file paths
    """
    code_files = []
    for ext in ["*.py", "*.sql"]:
        code_files.extend(directory.rglob(ext))
    return code_files

def sync_files(generated_dir: Path, generated_ai_dir: Path) -> Tuple[List[str], List[str], List[str]]:
    """Sync files from generated to generated_ai.
    
    Args:
        generated_dir: Source directory
        generated_ai_dir: Destination directory
        
    Returns:
        Tuple of (copied_files, skipped_files, removed_duplicates)
    """
    copied = []
    skipped = []
    removed = []
    
    # Find all code files in generated directory
    generated_files = find_code_files(generated_dir)
    
    print(f"📁 Found {len(generated_files)} code file(s) in {generated_dir}")
    
    for gen_file in generated_files:
        # Get relative path from generated directory
        rel_path = gen_file.relative_to(generated_dir)
        
        # Skip review JSON files
        if "_review.json" in str(rel_path):
            continue
        
        # Read file to detect code type
        try:
            with open(gen_file, 'r', encoding='utf-8') as f:
                code_content = f.read()
        except Exception as e:
            print(f"   ⚠️  Skipping {rel_path}: Failed to read file ({e})")
            continue
        
        # Detect code type
        code_type = detect_code_type(code_content, gen_file.name)
        
        # Get output filename with correct suffix
        output_filename = get_output_filename(gen_file.name, code_type)
        
        # Destination path in generated_ai (with correct filename)
        dest_dir = generated_ai_dir / rel_path.parent
        dest_file = dest_dir / output_filename
        
        # Check if file already exists in generated_ai (with correct name)
        if dest_file.exists():
            skipped.append(str(rel_path))
            continue
        
        # Check if original-named file exists (duplicate) and remove it
        original_dest = generated_ai_dir / rel_path
        if original_dest.exists() and original_dest != dest_file:
            # Remove the duplicate file with original name
            original_dest.unlink()
            removed.append(str(rel_path))
            print(f"   🗑️  Removed duplicate: {rel_path}")
        
        # Create destination directory if needed
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file with correct name
        shutil.copy2(gen_file, dest_file)
        copied.append(f"{rel_path} -> {output_filename}")
        print(f"   ✅ Copied: {rel_path} -> {output_filename}")
    
    return copied, skipped, removed

def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    generated_dir = project_root / "test_log" / "generated"
    generated_ai_dir = project_root / "test_log" / "generated_ai"
    
    if not generated_dir.exists():
        print(f"❌ Generated directory not found: {generated_dir}")
        return 1
    
    if not generated_ai_dir.exists():
        print(f"⚠️  Generated AI directory not found, creating: {generated_ai_dir}")
        generated_ai_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print("Syncing Generated Code to Generated AI")
    print(f"{'='*60}")
    print(f"Source: {generated_dir}")
    print(f"Destination: {generated_ai_dir}")
    print()
    
    copied, skipped, removed = sync_files(generated_dir, generated_ai_dir)
    
    print(f"\n📊 Summary:")
    print(f"   Files copied: {len(copied)}")
    print(f"   Files skipped (already exist): {len(skipped)}")
    print(f"   Duplicates removed: {len(removed)}")
    
    if copied:
        print(f"\n✅ Successfully synced {len(copied)} file(s) to generated_ai/")
    elif skipped:
        print(f"\n✅ All files already exist in generated_ai/")
    else:
        print(f"\n⚠️  No code files found in generated/")
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())

