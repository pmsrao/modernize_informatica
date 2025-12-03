# Directory Reorganization Plan

## Current Issues

1. **Root Level Clutter**: Multiple markdown files at root level
2. **Duplicate AI Modules**: `ai_agents/` at root vs `src/ai/` (different purposes but confusing)
3. **Mixed Scripts**: Utility scripts, test scripts, and setup scripts all in `scripts/`
4. **Documentation Scatter**: Many docs files at root and in `docs/`
5. **Generated Code**: `generated_code/` at root should be in build/output directory
6. **Test Files**: Some tests in `scripts/`, some in `tests/`

## Proposed Structure

```
modernize_informatica/
├── README.md                          # Main README (keep at root)
├── LICENSE                            # License file
├── .gitignore                         # Git ignore
├── requirements.txt                   # Python dependencies
├── requirements-dev.txt               # Dev dependencies
├── pytest.ini                        # Pytest config
├── Makefile                          # Build automation
│
├── src/                              # Main source code (KEEP AS IS)
│   ├── __init__.py
│   ├── config.py
│   ├── api/                          # API layer
│   ├── assessment/                   # Assessment module
│   ├── cli/                          # CLI module
│   ├── parser/                       # XML parsers
│   ├── normalizer/                   # Canonical model normalization
│   ├── translator/                   # Expression translation
│   ├── generators/                   # Code generators
│   ├── graph/                        # Neo4j graph operations
│   ├── dag/                          # DAG builder/visualizer
│   ├── llm/                          # LLM client abstractions
│   ├── ai/                           # AI utilities (rule extractor, risk analyzer)
│   ├── catalog/                      # Data catalog integrations
│   ├── connectors/                   # Storage connectors
│   ├── notifications/                 # Notification services
│   ├── utils/                        # Shared utilities
│   └── versioning/                   # Version management
│
├── ai_agents/                        # AI Agent implementations (KEEP - different from src/ai)
│   ├── __init__.py
│   ├── agent_orchestrator.py
│   ├── rule_explainer_agent.py
│   ├── mapping_summary_agent.py
│   ├── risk_detection_agent.py
│   ├── transformation_suggestion_agent.py
│   ├── code_fix_agent.py
│   ├── code_review_agent.py
│   ├── impact_analysis_agent.py
│   ├── mapping_reconstruction_agent.py
│   ├── workflow_simulation_agent.py
│   ├── model_enhancement_agent.py
│   ├── model_validation_agent.py
│   └── llm_*.py                      # LLM-based agents
│
├── frontend/                         # Frontend React app (KEEP AS IS)
│   ├── package.json
│   ├── src/
│   └── ...
│
├── tests/                            # All tests (CONSOLIDATE HERE)
│   ├── conftest.py
│   ├── fixtures/                     # Test fixtures
│   ├── unit/                         # Unit tests
│   ├── integration/                  # Integration tests
│   └── e2e/                          # End-to-end tests (NEW)
│       ├── test_flow.py              # Move from scripts/
│       ├── test_ai_agents.py         # Move from scripts/
│       └── test_samples.py           # Move from scripts/
│
├── scripts/                          # Utility and setup scripts (REORGANIZE)
│   ├── setup/                        # Setup scripts (NEW)
│   │   ├── setup_env.sh
│   │   └── setup_neo4j.sh
│   ├── utils/                        # Utility scripts (NEW)
│   │   ├── cleanup.py
│   │   ├── check_neo4j_data.py
│   │   ├── check_neo4j_simple.py
│   │   ├── diagnose_neo4j.py
│   │   ├── generate_diff.py
│   │   ├── migrate_to_graph.py
│   │   └── validate_graph_migration.py
│   └── dev/                          # Development scripts (NEW)
│       ├── test_graph_store.py       # Move from scripts/
│       ├── test_llm_config.py        # Move from scripts/
│       ├── test_frontend_integration.py  # Move from scripts/
│       └── test_part1_part2_flow.py  # Move from scripts/
│
├── docs/                             # Documentation (REORGANIZE)
│   ├── README.md                     # Documentation index
│   ├── getting-started/              # Getting started guides (NEW)
│   │   ├── introduction.md
│   │   ├── quick-start.md
│   │   └── setup_neo4j.md
│   ├── architecture/                 # Architecture docs (EXISTING)
│   │   ├── README.md
│   │   ├── architecture.md
│   │   ├── architecture_diagram.drawio
│   │   └── architecture_diagram.mermaid
│   ├── guides/                       # User guides (EXISTING)
│   │   ├── ai_agents_usage.md
│   │   ├── analysis_report.md
│   │   ├── llm_configuration.md
│   │   ├── llm_quick_reference.md
│   │   ├── test_flow_guide.md
│   │   └── next_steps.md
│   ├── api/                          # API documentation (NEW)
│   │   └── api_frontend.md
│   ├── modules/                      # Module documentation (NEW)
│   │   ├── parsing.md
│   │   ├── canonical_model.md
│   │   ├── code_generators.md
│   │   ├── expression_engine.md
│   │   ├── dag_engine.md
│   │   ├── code_generation_workflow.md
│   │   └── workflow_aware_code_generation.md
│   ├── ai/                           # AI/LLM documentation (NEW)
│   │   └── ai_agents.md
│   ├── deployment/                   # Deployment docs (NEW)
│   │   ├── deployment.md
│   │   └── extensibility.md
│   ├── development/                  # Development docs (NEW)
│   │   ├── design_spec.md
│   │   ├── solution_process_details.md
│   │   ├── code_generation_fixes_summary.md
│   │   ├── code_generation_issues_fixes.md
│   │   └── neo4j_persistence_fix.md
│   ├── testing/                      # Testing documentation (NEW)
│   │   ├── test/
│   │   │   ├── guide.md
│   │   │   ├── results.md
│   │   │   ├── frontend.md
│   │   │   └── troubleshooting.md
│   │   ├── phase1_phase2_testing_guide.md
│   │   └── test_flow_guide.md
│   ├── reference/                    # Reference materials (NEW)
│   │   ├── lakebridge_comparison.md
│   │   ├── implementation_summary.md
│   │   ├── implementation_complete_summary.md
│   │   └── next_steps_recommendations.md
│   └── archive/                      # Archived/legacy docs (NEW)
│       ├── fix_graph_explorer_edges.md
│       ├── graph_explorer_guide.md
│       ├── dag_json_format.md
│       ├── neo4j_persistence_explanation.md
│       ├── ui_enhancement_plan.md
│       └── ui_enhancement_implementation_plan.md
│
├── samples/                          # Sample Informatica files (KEEP AS IS)
│   ├── simple/
│   ├── complex/
│   └── super_complex/
│
├── deployment/                       # Deployment configs (KEEP AS IS)
│   ├── README.md
│   ├── docker-compose.yaml
│   ├── backend/
│   └── frontend/
│
├── enterprise/                       # Enterprise features (KEEP AS IS)
│   └── README.md
│
├── build/                           # Build outputs (NEW)
│   ├── generated_code/              # Move from root
│   ├── test_log/                    # Test outputs (keep structure)
│   ├── test_output/                  # Test outputs
│   └── dist/                         # Distribution packages
│
├── config/                          # Configuration files (NEW)
│   ├── .env.example                  # Example env file
│   └── config.yaml.example           # Example config
│
└── .github/                         # GitHub workflows (if using)
    └── workflows/

## Files to Move

### Root Level → docs/
- `canonical_model_deep_dive.md` → `docs/modules/canonical_model_deep_dive.md`
- `informatica-to-databricks.md` → `docs/reference/informatica-to-databricks.md`
- `solution.md` → `docs/development/solution.md`
- `system_architecture.md` → `docs/architecture/system_architecture.md`
- `test_end_to_end.md` → `docs/testing/test_end_to_end.md`
- `TESTING.md` → `docs/testing/TESTING.md`
- `roadmap.md` → `docs/reference/roadmap.md`
- `UI_Screen_Markups.pdf` → `docs/reference/UI_Screen_Markups.pdf`

### scripts/ → scripts/utils/ or scripts/dev/
- `cleanup.py` → `scripts/utils/cleanup.py`
- `check_neo4j_data.py` → `scripts/utils/check_neo4j_data.py`
- `check_neo4j_simple.py` → `scripts/utils/check_neo4j_simple.py`
- `diagnose_neo4j.py` → `scripts/utils/diagnose_neo4j.py`
- `generate_diff.py` → `scripts/utils/generate_diff.py`
- `migrate_to_graph.py` → `scripts/utils/migrate_to_graph.py`
- `validate_graph_migration.py` → `scripts/utils/validate_graph_migration.py`
- `test_graph_store.py` → `scripts/dev/test_graph_store.py`
- `test_llm_config.py` → `scripts/dev/test_llm_config.py`
- `test_frontend_integration.py` → `scripts/dev/test_frontend_integration.py`
- `test_part1_part2_flow.py` → `scripts/dev/test_part1_part2_flow.py`
- `test_ai_agents.py` → `tests/e2e/test_ai_agents.py`
- `test_samples.py` → `tests/e2e/test_samples.py`
- `test_flow.py` → `tests/e2e/test_flow.py` (or keep in scripts/utils as it's a main workflow)

### scripts/ → scripts/setup/
- `setup_env.sh` → `scripts/setup/setup_env.sh`
- `setup_neo4j.sh` → `scripts/setup/setup_neo4j.sh`

### Root → build/
- `generated_code/` → `build/generated_code/`

### docs/ → Reorganize
- Move files to appropriate subdirectories as shown above

## Import Path Updates Required

After reorganization, update imports in:
- `src/api/routes.py` - ai_agents imports (should still work)
- `scripts/test_flow.py` - ai_agents imports
- `tests/` - ai_agents imports
- Any other files importing from moved locations

## Benefits

1. **Clearer Separation**: Scripts organized by purpose (setup, utils, dev)
2. **Better Documentation**: Docs organized by topic and audience
3. **Cleaner Root**: Only essential files at root level
4. **Consolidated Tests**: All tests in one place
5. **Build Outputs**: Generated code in dedicated build directory
6. **Easier Navigation**: Logical grouping makes finding files easier

## Migration Steps

1. Create new directory structure
2. Move files to new locations
3. Update import paths in Python files
4. Update documentation references
5. Update .gitignore if needed
6. Update Makefile paths if needed
7. Update README.md with new structure
8. Test that everything still works

## Notes

- `ai_agents/` stays at root - it's a separate module from `src/ai/`
- `test_flow.py` could stay in `scripts/utils/` as it's a main workflow script
- Consider creating symlinks for backward compatibility during transition
- Update CI/CD pipelines if they reference old paths

