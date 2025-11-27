# Simple Test Files

This folder contains simple test files for basic validation of the Informatica Modernization Accelerator.

## Purpose

Simple test files are used for:
- Initial validation of parsers
- Basic workflow testing
- Simple mapping transformations
- Single-session workflows
- Quick smoke tests

## Adding Simple Test Files

Place your simple test XML files in this directory. The test script (`test_samples.py`) will automatically process them.

## File Naming Convention

- `workflow_*.xml` - Workflow files
- `mapping_*.xml` - Mapping files
- `session_*.xml` - Session files
- `worklet_*.xml` - Worklet files

## Example

```bash
# Add a simple workflow file
cp my_simple_workflow.xml samples/simple/workflow_simple.xml

# Run tests
python test_samples.py
```

