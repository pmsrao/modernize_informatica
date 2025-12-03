"""Tests for CLI module."""
import pytest
import sys
import tempfile
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from cli.config import Config
from cli.errors import CLIError, ValidationError, ConfigurationError
from cli.utils import format_output, print_success, print_error


def test_config_defaults():
    """Test default configuration."""
    config = Config()
    
    assert config.get("neo4j.uri") is not None
    assert config.get("output.dir") is not None


def test_config_get():
    """Test configuration get method."""
    config = Config()
    
    uri = config.get("neo4j.uri")
    assert uri is not None
    
    # Test non-existent key
    value = config.get("nonexistent.key", "default")
    assert value == "default"


def test_config_validation():
    """Test configuration validation."""
    config = Config()
    
    # Should not raise if valid
    try:
        config.validate()
    except ConfigurationError:
        pytest.fail("Configuration validation should not fail with defaults")


def test_format_output_json():
    """Test JSON output formatting."""
    data = {"key": "value", "number": 123}
    output = format_output(data, format_type="json")
    
    assert isinstance(output, str)
    parsed = json.loads(output)
    assert parsed == data


def test_format_output_human():
    """Test human-readable output formatting."""
    data = {"key": "value", "number": 123}
    output = format_output(data, format_type="human")
    
    assert isinstance(output, str)
    assert "key" in output
    assert "value" in output


def test_cli_error():
    """Test CLI error class."""
    error = CLIError("Test error message")
    
    assert str(error) == "Test error message"


def test_validation_error():
    """Test validation error class."""
    error = ValidationError("Validation failed", field="test_field")
    
    assert str(error) == "Validation failed"
    assert error.field == "test_field"


def test_configuration_error():
    """Test configuration error class."""
    error = ConfigurationError("Config error", config_path="/path/to/config")
    
    assert str(error) == "Config error"
    assert error.config_path == "/path/to/config"

