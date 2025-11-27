# Testing Guide

## Overview

This is the main testing documentation for the Informatica Modernization Accelerator. It provides links to detailed testing guides, results, and troubleshooting information.

---

## Quick Start

### Run All Tests
```bash
python test_samples.py
```

This processes all XML files in `samples/simple/` and `samples/complex/` directories.

### Run Generated Tests
```bash
cd generated_code/m_load_customer
pytest generated_tests.py -v
```

---

## Documentation

### 📖 [Comprehensive Testing Guide](docs/test/guide.md)
Complete step-by-step guide for testing with and without the frontend, including validation checklists.

### 📊 [Test Results](docs/test/results.md)
Detailed test results for simple and complex workflows, including generated code validation.

### 🔧 [Troubleshooting](docs/test/troubleshooting.md)
Common issues and solutions, including Java requirements and test fixes.

### 🎨 [Frontend Testing](docs/test/frontend.md)
Guide for testing the frontend lineage visualization and UI components.

---

## Test Organization

### Sample Files
- **`samples/simple/`** - Basic test files for initial validation
- **`samples/complex/`** - Complex workflows with multiple sessions, worklets, and transformations

### Test Scripts
- **`test_samples.py`** - Main test script that processes all sample files
- **`test_frontend_integration.py`** - Frontend API integration tests

### Generated Tests
- **`generated_code/<mapping_name>/generated_tests.py`** - Auto-generated pytest test suites

---

## Test Types

1. **Parser Tests** - Validate XML parsing for workflows, mappings, sessions, worklets
2. **DAG Tests** - Validate DAG building and visualization
3. **Code Generation Tests** - Validate PySpark, DLT, SQL code generation
4. **Test Generation Tests** - Validate auto-generated test suites
5. **Frontend Tests** - Validate UI and lineage visualization
6. **Integration Tests** - End-to-end pipeline testing

---

## Current Status

✅ **All core tests passing**
- 5 tests PASSED
- 3 tests SKIPPED (expected - missing test data files)

See [Test Results](docs/test/results.md) for detailed status.

---

## Getting Help

- **Issues?** Check [Troubleshooting](docs/test/troubleshooting.md)
- **Frontend?** See [Frontend Testing](docs/test/frontend.md)
- **Details?** Read [Comprehensive Guide](docs/test/guide.md)

---

**Last Updated**: November 27, 2025

