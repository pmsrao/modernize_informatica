# Simple Test Files

This folder contains **simple, basic test files** for initial validation and learning.

## Purpose

Simple test files are used for:
- Initial validation of parsers
- Basic workflow testing
- Simple mapping transformations
- Single-session workflows
- Quick smoke tests
- Learning the system basics

## Files

### workflow_simple.xml
A basic workflow with:
- 2 sessions
- 1 worklet
- Simple sequential flow
- Basic success links

**Use Case**: Test basic workflow parsing and DAG building

### mapping_simple.xml
A simple mapping including:
- 1 Source Qualifier
- 1 Expression transformation
- 1 Lookup transformation
- 1 Aggregator transformation
- Basic connectors

**Use Case**: Test basic mapping parsing and code generation

### worklet_simple.xml
A simple worklet with:
- 2 sessions
- Basic connector flow

**Use Case**: Test worklet parsing and nested structure handling

### session_simple.xml
Basic session configuration:
- Simple connection details
- Basic tracing level

**Use Case**: Test session parser

### dag_simple.json
Simple DAG structure for testing

---

## When to Use Simple Files

- **Getting Started**: First time using the system
- **Quick Validation**: Verify parsers work after changes
- **Learning**: Understand basic concepts before moving to complex scenarios
- **CI/CD**: Fast smoke tests in automated pipelines

---

## Next Steps

Once comfortable with simple files, move to `samples/complex/` for:
- Multi-source mappings
- Complex transformations
- Nested worklets
- Enterprise-level workflows
- Advanced patterns (SCD2, incremental loads, etc.)
