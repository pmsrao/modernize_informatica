# Canonical Model

## Purpose

The canonical model serves as a technology-neutral representation of Informatica mappings, transformations, and their relationships. It abstracts away Informatica-specific XML structures into a standardized format that can be used by all downstream components (generators, AI agents, lineage engines).

---

## Structure

The canonical model captures:

- **Mappings**: Sources, targets, transformations, and their connections
- **Transformations**: Types, ports, expressions, and configuration
- **Fields**: Names, data types, expressions, and lineage
- **Connections**: Data flow between transformations
- **Metadata**: Names, descriptions, and annotations

---

## Key Benefits

1. **Single Source of Truth**: All generators and agents work from the same model
2. **Technology Independence**: Model is not tied to Informatica or target platforms
3. **Regeneration**: Code can be regenerated without re-parsing XML
4. **Extensibility**: Easy to add new transformation types or metadata

---

## Model Components

### Mapping Structure
- Mapping name and metadata
- Source definitions
- Target definitions
- Transformation list
- Connection graph

### Transformation Structure
- Transformation type (EXPRESSION, LOOKUP, AGGREGATOR, etc.)
- Input ports
- Output ports
- Expressions and formulas
- Configuration parameters

### Lineage Structure
- Column-level lineage
- Transformation-level lineage
- Workflow-level lineage

---

## Usage

The canonical model is used by:

- **Code Generators**: Generate PySpark, DLT, SQL from the model
- **AI Agents**: Analyze and explain based on model structure
- **Lineage Engine**: Build lineage graphs from model connections
- **Documentation Generators**: Create specs from model metadata

---

**Next**: Learn about [Parsing & Normalization](parsing.md) that creates the canonical model.

