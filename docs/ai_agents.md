# AI & LLM Agents

## Purpose

The AI layer is designed to augment human understanding and decision-making, not to replace deterministic parsing and generation.

It answers questions like:

- "What does this mapping actually do?"
- "Which transformations are risky or brittle?"
- "What is a simpler way to express this logic?"
- "What is the impact of changing this column?"
- "Given partial clues, what might the original mapping have been?"

---

## LLM Layer

The LLM Manager abstracts away providers:

- OpenAI (standard GPT models)
- Azure OpenAI
- Local LLM (llama.cpp, vLLM, etc.)

Selection is controlled by configuration (e.g., an environment variable `LLM_PROVIDER`).

Prompt templates are centralized so that:

- Expression explanation
- Mapping summarization
- Risk analysis
- Suggestion generation
- Code fixing
- Reconstruction

…all follow consistent patterns.

---

## Core AI Agents

### 1. Rule Explainer Agent
- **Input**: field name, original Informatica expression, AST / canonical context
- **Output**: human-readable explanation of the rule
- **Example**: "AGE_BUCKET classifies customers as 'YOUNG' when AGE is less than 30, and 'OTHER' otherwise."

### 2. Mapping Summary Agent
- **Input**: canonical mapping model
- **Output**: narrative summary of what the mapping does, which tables it reads from, and what outputs it produces.

### 3. Risk Detection Agent
Scans expressions and transformation patterns to identify:
- risky casts
- suspicious default values
- potential data loss
- complex nested logic that might be fragile

### 4. Suggestion Agent
Offers optimization ideas:
- simplification of expressions
- more idiomatic use of Spark functions
- splitting very complex transformations

---

## Advanced AI Agents

### 1. Code Fix Agent
- **Input**: generated PySpark code + error hints (optional)
- **Output**: corrected version of the code, preserving semantics where possible

### 2. Mapping Reconstruction Agent
- **Input**: partial XML, log fragments, lineage clues, target table definitions
- **Output**: a hypothesized canonical mapping model or at least a structured description

### 3. Impact Analysis Agent
- **Given**: a mapping, column, or transformation
- **Produces**: descriptions of which downstream elements depend on it, prioritization of what must be regression-tested

### 4. Workflow Simulation Agent
- **Uses**: DAG model, metadata about tasks
- **To**: simulate expected run sequences, highlight bottlenecks or single points of failure

---

**Next**: Learn about [API & Frontend](api_frontend.md) for user interaction.

