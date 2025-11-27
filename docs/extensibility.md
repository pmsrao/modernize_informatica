# Extensibility & Regeneration

## Extensibility

Areas you can extend:

- **Transformations**:
  - Support additional Informatica transformation types
  - Add new canonical types or subtypes
- **Target Technologies**:
  - Add generators for:
    - dbt models
    - native Snowflake SQL
    - other orchestration frameworks
- **AI Agents**:
  - Define new prompt templates
  - Implement new agent classes for specialized analyses
- **LLM Providers**:
  - Implement wrappers for other hosted or on-prem LLMs
  - Plug them into the LLM Manager interface

---

## Regeneration Using Design Specs

Two main documents act as source-of-truth:

- `design_spec.md` — formal architectural & component-centric design
- `docs/` — conceptual documentation (this directory)

With these, you can instruct Cursor (or any AI coding assistant) to:

- Regenerate a specific module (e.g., PySpark generator) based on updated design
- Refactor AST rules to add new functions
- Introduce new transformation patterns while keeping tests aligned

A typical regeneration workflow:

1. Update `design_spec.md` to reflect new design decisions.
2. Use a prompt like:
   "Based on design_spec.md section 'Expression Engine' and 'Code Generators', regenerate expression_engine/translator_pyspark.py to support the additional DATE_DIFF function and ensure tests are updated accordingly."
3. Run test suite.
4. Commit updated modules and version snapshots.

---

## Adding New Components

### Adding a New Generator

1. Create generator class in `src/generators/`
2. Implement `generate(model)` method
3. Add to `src/generators/__init__.py`
4. Add API endpoint in `src/api/routes.py`
5. Update documentation

### Adding a New Parser

1. Create parser class in `src/parser/`
2. Implement `parse()` method
3. Add to `src/parser/__init__.py`
4. Update `test_samples.py` to handle new file type
5. Update documentation

### Adding a New AI Agent

1. Create agent class in `ai_agents/`
2. Implement agent logic with LLM integration
3. Add prompt templates to `src/llm/prompt_templates.py`
4. Register with `AgentOrchestrator`
5. Add API endpoint if needed

---

**See [Documentation Index](index.md) for navigation.**

