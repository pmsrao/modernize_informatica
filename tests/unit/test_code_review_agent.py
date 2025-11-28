"""Unit tests for CodeReviewAgent."""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from ai_agents.code_review_agent import CodeReviewAgent
from src.utils.exceptions import ModernizationError


@pytest.fixture
def review_agent():
    """Create CodeReviewAgent instance."""
    return CodeReviewAgent(use_llm=False)  # Use pattern-based only for tests


def test_review_empty_code(review_agent):
    """Test review of empty code."""
    result = review_agent.review("")
    
    assert result["needs_fix"] is True
    assert result["severity"] == "HIGH"
    assert len(result["issues"]) > 0
    assert any("empty" in i["issue"].lower() for i in result["issues"])


def test_review_valid_code(review_agent):
    """Test review of valid code."""
    code = """
from pyspark.sql import functions as F
from pyspark.sql.types import *

df = spark.read.table("source_table")
result = df.select(F.col("id"), F.col("name"))
result.write.mode("overwrite").saveAsTable("target_table")
"""
    
    result = review_agent.review(code)
    
    assert result["needs_fix"] is False or result["severity"] == "LOW"
    assert result["score"] >= 70  # Should have decent score


def test_review_missing_imports(review_agent):
    """Test review detects missing imports."""
    code = """
df = spark.read.table("source_table")
result = df.select(F.col("id"))
"""
    
    result = review_agent.review(code)
    
    assert any("import" in i["issue"].lower() for i in result["issues"])


def test_review_hardcoded_values(review_agent):
    """Test review detects hardcoded sensitive values."""
    code = """
df = spark.read.format("jdbc").option("url", "jdbc:postgresql://localhost:5432/db")
    .option("user", "admin").option("password", "secret123").load()
"""
    
    result = review_agent.review(code)
    
    assert any("hardcoded" in i["issue"].lower() or "password" in i["issue"].lower() 
               for i in result["issues"])


def test_calculate_severity(review_agent):
    """Test severity calculation."""
    high_issues = [{"severity": "HIGH"}]
    medium_issues = [{"severity": "MEDIUM"}]
    low_issues = [{"severity": "LOW"}]
    
    assert review_agent._calculate_severity(high_issues) == "HIGH"
    assert review_agent._calculate_severity(medium_issues * 3) == "MEDIUM"
    assert review_agent._calculate_severity(low_issues) == "LOW"
    assert review_agent._calculate_severity([]) == "LOW"


def test_calculate_score(review_agent):
    """Test quality score calculation."""
    no_issues = []
    low_issues = [{"severity": "LOW"}]
    medium_issues = [{"severity": "MEDIUM"}]
    high_issues = [{"severity": "HIGH"}]
    
    assert review_agent._calculate_score(no_issues, []) == 100
    assert review_agent._calculate_score(low_issues, []) < 100
    assert review_agent._calculate_score(medium_issues, []) < 95
    assert review_agent._calculate_score(high_issues, []) < 90


def test_review_with_canonical_model(review_agent):
    """Test review with canonical model context."""
    code = "df = spark.read.table('test')"
    canonical_model = {
        "mapping_name": "M_TEST",
        "sources": [],
        "targets": []
    }
    
    result = review_agent.review(code, canonical_model)
    
    assert "review" in result
    assert "score" in result

