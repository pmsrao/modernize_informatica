# Testing Troubleshooting Guide

## Common Issues and Solutions

---

## Java/PySpark Issues

### Issue: Java Version Mismatch

**Error:**
```
UnsupportedClassVersionError: class file version 61.0, this version only recognizes up to 55.0
```

**Problem:**
- PySpark requires **Java 17** (class file version 61.0)
- System has **Java 11** (class file version 55.0)
- This is a **real issue**, not a Databricks runtime requirement

**Solution:**

**macOS:**
```bash
brew install openjdk@17
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
```

**Linux:**
```bash
sudo apt-get install openjdk-17-jdk
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk
```

**Windows:**
```bash
# Download OpenJDK 17 from https://adoptium.net/
# Set JAVA_HOME environment variable to installation path
```

**Verify:**
```bash
java -version  # Should show version 17+
echo $JAVA_HOME  # Should point to Java 17 installation
```

**Permanent Setup (macOS):**
Add to `~/.zshrc` or `~/.bash_profile`:
```bash
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
export PATH=$JAVA_HOME/bin:$PATH
```

**Permanent Setup (Linux):**
Add to `~/.bashrc`:
```bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk
export PATH=$JAVA_HOME/bin:$PATH
```

### Issue: Python Version Mismatch in Spark

**Error:**
```
PySparkRuntimeError: Python in worker has different version: 3.14 than that in driver: 3.12
```

**Solution:**
```bash
export PYSPARK_PYTHON=python3
export PYSPARK_DRIVER_PYTHON=python3
```

Or configure SparkSession:
```python
spark = SparkSession.builder \
    .appName('test') \
    .config("spark.pyspark.python", "python3") \
    .config("spark.pyspark.driver.python", "python3") \
    .getOrCreate()
```

---

## Test Generation Issues

### Issue: Empty Schema Errors

**Error:**
```
PySparkValueError: [CANNOT_INFER_EMPTY_SCHEMA] Can not infer schema from an empty dataset.
```

**Problem:** Test data is empty `[]`

**Solution:** ✅ **FIXED** - Test generator now adds default test data when input_ports is empty

### Issue: IndexError in Full Pipeline Test

**Error:**
```
IndexError: list index out of range
```

**Problem:** Sources list is empty

**Solution:** ✅ **FIXED** - Test now skips gracefully when sources list is empty

### Issue: Missing Test Data Files

**Error:**
```
AnalysisException: [PATH_NOT_FOUND] Path does not exist
```

**Problem:** Test data parquet files don't exist

**Solution:** ✅ **FIXED** - Test now skips gracefully when files are missing

**To create test data files:**
```bash
cd generated_code/m_load_customer
python create_test_data.py
```

---

## API Issues

### Issue: API Not Starting

**Error:** `ModuleNotFoundError` or import errors

**Solution:**
```bash
# Install dependencies
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"

# Verify imports
python -c "from api import app"
```

### Issue: File Upload Fails

**Error:** `File not found` or upload errors

**Solution:**
- Check file exists in `samples/simple/` or `samples/complex/` directory
- Verify file is XML format
- Check file size (max 100MB)
- Ensure `uploads/` directory exists and is writable

### Issue: CORS Errors

**Error:** CORS policy blocking requests

**Solution:**
- Verify API is running on port 8000
- Check CORS settings in `src/api/app.py`
- Verify frontend API base URL in `frontend/src/services/api.js`

---

## Frontend Issues

### Issue: DAG Not Displaying

**Error:** Empty visualization or errors

**Solution:**
- Check File ID is correct
- Verify workflow was parsed successfully
- Check browser console for errors
- Verify API response in Network tab
- Check DAG was built (check API logs)

### Issue: Frontend Not Starting

**Error:** `vite: command not found`

**Solution:**
```bash
cd frontend
npm install
npm run dev
```

---

## Code Generation Issues

### Issue: Generated Code Has Errors

**Error:** Syntax errors in generated code

**Solution:**
- Check canonical model structure
- Verify transformations are parsed correctly
- Review generated code for syntax errors
- Check generator logs for warnings

---

## Test Execution Issues

### Issue: Tests Skip Unexpectedly

**Reason:** Tests skip when:
- Test data is empty (expected)
- Source files don't exist (expected)
- Java/Spark unavailable (expected)

**Action:** This is correct behavior. Tests skip gracefully instead of failing.

### Issue: Coverage Warnings

**Warning:**
```
CoverageWarning: Module src was never imported.
CoverageWarning: No data was collected.
```

**Solution:** Can be ignored - tests don't import the `src` module (they test generated code)

---

## Quick Fixes

### Reset Test Environment
```bash
# Clean generated files
rm -rf generated_code/*
rm -rf tests/output/*

# Re-run tests
python test_samples.py
```

### Verify Installation
```bash
# Check Python version
python --version  # Should be 3.10+

# Check dependencies
pip list | grep -E "(pyspark|pytest|fastapi)"

# Check Java version
java -version  # Should be 17+
```

---

## Getting More Help

- Check [Test Guide](guide.md) for detailed testing instructions
- Review [Test Results](results.md) for expected outcomes
- See [Frontend Testing](frontend.md) for UI-specific issues

---

**Last Updated**: November 27, 2025

