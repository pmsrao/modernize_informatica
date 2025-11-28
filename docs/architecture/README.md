# Architecture Diagrams

This directory contains architecture diagrams for the Informatica Modernization Accelerator.

## Files

- `architecture_diagram.drawio` - Draw.io format diagram (for editing in draw.io)
- `architecture_diagram.mermaid` - Mermaid format diagram (for viewing in Markdown/GitHub)

## Viewing the Diagrams

### Draw.io Format
1. Open [draw.io](https://app.diagrams.net/) in your browser
2. File → Open → Select `architecture_diagram.drawio`
3. Or use the Draw.io desktop app

### Mermaid Format
The Mermaid diagram can be viewed:
- In GitHub: It will render automatically in Markdown files
- In VS Code: Install the "Markdown Preview Mermaid Support" extension
- Online: Use [Mermaid Live Editor](https://mermaid.live/)

## Diagram Components

### Color Coding
- **Gray**: Deterministic components (Parsers, Normalizers, Generators)
- **Purple**: AI/LLM components (Enhancement Agents, Review Agents, LLM Manager)
- **Green**: Graph storage components (Version Store, Graph Store)

### Key Flows

1. **Main Processing Flow**:
   ```
   XML → Parse → Canonical Model → AI Enhancement → Enhanced Model → 
   Code Generation → AI Review → Final Code
   ```

2. **Storage Flow**:
   ```
   Enhanced Model → Version Store (JSON + Graph) → Graph Store (Neo4j)
   ```

3. **API Flow**:
   ```
   All Components → REST API → Frontend UI
   ```

## Troubleshooting

If the draw.io file doesn't open:
1. Try opening it in [draw.io web app](https://app.diagrams.net/)
2. Use the Mermaid version instead (easier to view/edit)
3. Check that the file is not corrupted (should be valid XML)

## Updates

When updating the architecture:
1. Update both draw.io and Mermaid versions
2. Keep them in sync
3. Update this README if structure changes significantly

