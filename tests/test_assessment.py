"""Tests for assessment module."""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

from graph.graph_store import GraphStore
from assessment.profiler import Profiler
from assessment.analyzer import Analyzer
from assessment.wave_planner import WavePlanner
from assessment.report_generator import ReportGenerator


@pytest.fixture
def graph_store():
    """Create graph store fixture."""
    return GraphStore(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="password"
    )


@pytest.fixture
def profiler(graph_store):
    """Create profiler fixture."""
    return Profiler(graph_store)


@pytest.fixture
def analyzer(graph_store, profiler):
    """Create analyzer fixture."""
    return Analyzer(graph_store, profiler)


@pytest.fixture
def wave_planner(graph_store, profiler, analyzer):
    """Create wave planner fixture."""
    return WavePlanner(graph_store, profiler, analyzer)


@pytest.fixture
def report_generator(graph_store, profiler, analyzer, wave_planner):
    """Create report generator fixture."""
    return ReportGenerator(graph_store, profiler, analyzer, wave_planner)


def test_profiler_profile_repository(profiler):
    """Test repository profiling."""
    profile = profiler.profile_repository()
    
    assert isinstance(profile, dict)
    assert "total_workflows" in profile
    assert "total_mappings" in profile
    assert "total_transformations" in profile


def test_profiler_profile_workflows(profiler):
    """Test workflow profiling."""
    workflows = profiler.profile_workflows()
    
    assert isinstance(workflows, list)
    for workflow in workflows:
        assert "name" in workflow
        assert "complexity_score" in workflow


def test_profiler_profile_mappings(profiler):
    """Test mapping profiling."""
    mappings = profiler.profile_mappings()
    
    assert isinstance(mappings, list)
    for mapping in mappings:
        assert "name" in mapping
        assert "complexity_score" in mapping


def test_analyzer_identify_patterns(analyzer):
    """Test pattern identification."""
    patterns = analyzer.identify_patterns()
    
    assert isinstance(patterns, dict)
    assert "lookup_cache_patterns" in patterns
    assert "common_transformation_patterns" in patterns


def test_analyzer_identify_blockers(analyzer):
    """Test blocker identification."""
    blockers = analyzer.identify_blockers()
    
    assert isinstance(blockers, list)
    for blocker in blockers:
        assert "component_name" in blocker
        assert "blocker_type" in blocker
        assert "severity" in blocker


def test_analyzer_estimate_effort(analyzer):
    """Test effort estimation."""
    effort = analyzer.estimate_migration_effort()
    
    assert isinstance(effort, dict)
    assert "mapping_effort" in effort
    assert "workflow_effort" in effort
    assert "total_effort_days" in effort


def test_wave_planner_plan_waves(wave_planner):
    """Test migration wave planning."""
    waves = wave_planner.plan_migration_waves(max_wave_size=10)
    
    assert isinstance(waves, list)
    for wave in waves:
        assert "wave_number" in wave
        assert "components" in wave
        assert "total_effort_days" in wave


def test_report_generator_summary(report_generator):
    """Test summary report generation."""
    summary = report_generator.generate_summary_report()
    
    assert isinstance(summary, dict)
    assert "repository_statistics" in summary
    assert "overall_complexity" in summary
    assert "total_effort_days" in summary


def test_report_generator_detailed(report_generator):
    """Test detailed report generation."""
    detailed = report_generator.generate_detailed_report()
    
    assert isinstance(detailed, dict)
    assert "repository_profile" in detailed
    assert "workflow_profiles" in detailed
    assert "mapping_profiles" in detailed


def test_report_generator_wave_plan(report_generator):
    """Test wave plan generation."""
    wave_plan = report_generator.generate_wave_plan(max_wave_size=10)
    
    assert isinstance(wave_plan, dict)
    assert "waves" in wave_plan
    assert "total_waves" in wave_plan
    assert "total_effort_days" in wave_plan

