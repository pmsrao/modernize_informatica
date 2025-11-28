# Next Steps: Implementation Roadmap

## Overview

This document outlines the next steps for implementing and enhancing the Informatica Modernization Accelerator, focusing on completing the graph-first architecture and expanding capabilities.

---

## Current Status

### ✅ Completed

1. **Phase 1: Foundation**
   - ✅ Model Enhancement Agent (pattern-based)
   - ✅ Model Validation Agent
   - ✅ Agent Orchestrator integration
   - ✅ Unit tests for enhancement and validation

2. **Phase 3: Graph-First Implementation**
   - ✅ GraphStore class (Neo4j integration)
   - ✅ GraphSync for dual-write
   - ✅ GraphQueries for high-level queries
   - ✅ VersionStore with graph-first support
   - ✅ Graph query API endpoints
   - ✅ Migration scripts (for future use)
   - ✅ Architecture diagrams (two-part structure)

3. **Infrastructure**
   - ✅ Neo4j driver integration
   - ✅ Configuration setup
   - ✅ API endpoints for graph queries

---

## Immediate Next Steps (Priority 1)

### Step 1: Neo4j Setup & Validation (Week 1)

**Goal**: Get Neo4j running and validate graph-first storage

#### 1.1 Install and Configure Neo4j

```bash
# Option A: Docker (Recommended)
docker run \
    --name neo4j-modernize \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/password \
    -e NEO4J_PLUGINS='["apoc"]' \
    -v neo4j-data:/data \
    -v neo4j-logs:/logs \
    neo4j:5.15-community
```

#### 1.2 Configure Environment

Create/update `.env`:
```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Graph Store Configuration
ENABLE_GRAPH_STORE=true
GRAPH_FIRST=true
```

#### 1.3 Test Graph Store

```bash
# Test connection
python -c "from src.graph.graph_store import GraphStore; GraphStore()"

# Test save/load
python scripts/test_graph_store.py
```

**Deliverables**:
- [ ] Neo4j running and accessible
- [ ] Environment variables configured
- [ ] GraphStore connection verified
- [ ] Basic save/load test passing

---

### Step 2: Integrate Graph Store into Part 1 Flow (Week 1-2)

**Goal**: Ensure canonical models are saved to graph after enhancement

#### 2.1 Update API Routes

**File**: `src/api/routes.py`

Ensure that after AI enhancement, models are saved to graph:

```python
# In parse/mapping endpoint
enhanced_result = agent_orchestrator.process_with_enhancement(
    canonical_model,
    enable_enhancement=True
)
enhanced_model = enhanced_result["canonical_model"]

# Save to graph (primary storage)
if graph_store:
    graph_store.save_mapping(enhanced_model)

# Save to version store (which will also save to graph if graph_first=True)
version_store.save(mapping_name, enhanced_model)
```

#### 2.2 Test End-to-End Part 1 Flow

```bash
# Upload a mapping XML
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@samples/mapping_complex.xml"

# Parse and enhance
curl -X POST "http://localhost:8000/api/v1/parse/mapping" \
  -H "Content-Type: application/json" \
  -d '{"file_id": "..."}'

# Verify in Neo4j Browser
# http://localhost:7474
# MATCH (m:Mapping) RETURN m
```

**Deliverables**:
- [ ] Part 1 flow saves to graph
- [ ] Enhanced models visible in Neo4j
- [ ] End-to-end test passing

---

### Step 3: Verify Part 2 Reads from Graph (Week 2)

**Goal**: Ensure code generators read from graph

#### 3.1 Test Code Generation from Graph

```bash
# Generate code (should read from graph)
curl -X POST "http://localhost:8000/api/v1/generate/pyspark" \
  -H "Content-Type: application/json" \
  -d '{"mapping_id": "..."}'

# Verify model was loaded from graph (check logs)
```

#### 3.2 Add Graph-First Validation

**File**: `tests/integration/test_graph_integration.py`

```python
def test_code_generation_reads_from_graph():
    """Verify code generators read from graph."""
    # Save model to graph
    graph_store.save_mapping(canonical_model)
    
    # Generate code
    generator = PySparkGenerator()
    code = generator.generate(canonical_model)
    
    # Verify model was loaded from graph (check logs or mock)
    assert code is not None
```

**Deliverables**:
- [ ] Code generators read from graph
- [ ] Integration tests passing
- [ ] Logs confirm graph reads

---

## Short-Term Enhancements (Priority 2)

### Step 4: Enhance AI Agents with LLM Integration (Week 2-3)

**Goal**: Add LLM-based enhancements to Model Enhancement Agent

#### 4.1 Implement LLM Enhancements

**File**: `ai_agents/model_enhancement_agent.py`

```python
def _llm_enhancements(self, model: Dict[str, Any]) -> Dict[str, Any]:
    """LLM-based comprehensive enhancements."""
    prompt = self._build_enhancement_prompt(model)
    response = self.llm.generate(prompt)
    enhancements = self._parse_llm_response(response)
    
    # Apply enhancements
    enhanced = self._apply_llm_enhancements(model, enhancements)
    return enhanced
```

#### 4.2 Create Enhancement Prompt Templates

**File**: `src/llm/prompt_templates.py`

Add templates for:
- Model enhancement suggestions
- Optimization recommendations
- Data quality rules
- Performance hints

**Deliverables**:
- [ ] LLM-based enhancements implemented
- [ ] Prompt templates created
- [ ] Unit tests for LLM enhancements
- [ ] Integration tests with OpenAI/Azure

---

### Step 5: Add Code Review Agent (Week 3-4)

**Goal**: Implement AI code review after generation

#### 5.1 Create Code Review Agent

**File**: `ai_agents/code_review_agent.py` (New)

```python
class CodeReviewAgent:
    """Reviews generated code for issues and improvements."""
    
    def review(self, code: str, canonical_model: Dict[str, Any]) -> Dict[str, Any]:
        """Review generated code.
        
        Returns:
            {
                "issues": [...],
                "suggestions": [...],
                "needs_fix": bool,
                "severity": "LOW" | "MEDIUM" | "HIGH"
            }
        """
        # Pattern-based review
        issues = self._pattern_review(code)
        
        # LLM-based review
        if self.use_llm:
            llm_issues = self._llm_review(code, canonical_model)
            issues.extend(llm_issues)
        
        return {
            "issues": issues,
            "needs_fix": len([i for i in issues if i["severity"] in ["HIGH", "MEDIUM"]]) > 0,
            "severity": self._calculate_severity(issues)
        }
```

#### 5.2 Integrate into Generation Flow

**File**: `src/api/routes.py`

```python
# After code generation
code = generator.generate(canonical_model)

# Review code
if request.review_code:
    review = agent_orchestrator.review_agent.review(code, canonical_model)
    if review["needs_fix"]:
        fixed_code = agent_orchestrator.fix_code(code, review["issues"])
        code = fixed_code
```

**Deliverables**:
- [ ] CodeReviewAgent implemented
- [ ] Integrated into generation flow
- [ ] Unit tests
- [ ] API endpoint for code review

---

### Step 6: Graph Query Enhancements (Week 4)

**Goal**: Add more powerful graph queries

#### 6.1 Add Advanced Queries

**File**: `src/graph/graph_queries.py`

Add methods for:
- Pattern discovery across mappings
- Similar transformation detection
- Impact analysis (what breaks if table changes)
- Migration planning (optimal order)
- Dependency visualization

#### 6.2 Create Graph Visualization Endpoint

**File**: `src/api/routes.py`

```python
@router.get("/graph/visualize/{mapping_name}")
async def visualize_mapping_graph(mapping_name: str):
    """Visualize mapping as graph (D3.js format)."""
    # Query graph for mapping structure
    # Return nodes and edges in D3.js format
    pass
```

**Deliverables**:
- [ ] Advanced graph queries implemented
- [ ] Graph visualization endpoint
- [ ] Frontend integration (optional)

---

## Medium-Term Enhancements (Priority 3)

### Step 7: Extensibility Framework (Week 5-6)

**Goal**: Make it easy to add new target platforms

#### 7.1 Create Platform Abstraction

**File**: `src/generators/platform_base.py` (New)

```python
class PlatformGenerator(ABC):
    """Base class for platform-specific generators."""
    
    @abstractmethod
    def generate(self, canonical_model: Dict[str, Any]) -> str:
        """Generate platform-specific code."""
        pass
    
    @abstractmethod
    def get_supported_transformations(self) -> List[str]:
        """Return list of supported transformation types."""
        pass
```

#### 7.2 Implement Databricks Generator (Refactor)

**File**: `src/generators/databricks_generator.py` (New)

Refactor existing generators to extend `PlatformGenerator`:
- `PySparkGenerator` → `DatabricksPySparkGenerator`
- `DLTGenerator` → `DatabricksDLTGenerator`
- `SQLGenerator` → `DatabricksSQLGenerator`

#### 7.3 Create Platform Registry

**File**: `src/generators/platform_registry.py` (New)

```python
class PlatformRegistry:
    """Registry for platform generators."""
    
    def register(self, platform: str, generator: PlatformGenerator):
        """Register a platform generator."""
        pass
    
    def get_generator(self, platform: str) -> PlatformGenerator:
        """Get generator for platform."""
        pass
```

**Deliverables**:
- [ ] Platform abstraction created
- [ ] Databricks generators refactored
- [ ] Platform registry implemented
- [ ] Documentation for adding new platforms

---

### Step 8: Enhanced Lineage & Impact Analysis (Week 6-7)

**Goal**: Build comprehensive lineage and impact analysis

#### 8.1 Column-Level Lineage in Graph

**File**: `src/graph/graph_store.py`

Enhance `save_mapping()` to store column-level lineage:
- Field nodes with relationships
- `DERIVED_FROM` relationships between fields
- `FLOWS_TO` relationships across transformations

#### 8.2 Impact Analysis Agent

**File**: `ai_agents/impact_analysis_agent.py` (Enhance)

Use graph queries for:
- Find all mappings using a table
- Find dependent mappings
- Calculate impact score
- Suggest regression testing needs

**Deliverables**:
- [ ] Column-level lineage in graph
- [ ] Enhanced impact analysis
- [ ] Graph-based impact queries
- [ ] API endpoints for impact analysis

---

### Step 9: Pattern Discovery & Reuse (Week 7-8)

**Goal**: Discover and reuse patterns across mappings

#### 9.1 Pattern Detection

**File**: `src/graph/pattern_detector.py` (New)

```python
class PatternDetector:
    """Detect reusable patterns in graph."""
    
    def find_similar_transformations(self, transformation_type: str):
        """Find similar transformations across mappings."""
        # Use graph queries to find patterns
        pass
    
    def suggest_reuse(self, mapping: Dict[str, Any]):
        """Suggest reusable patterns for a mapping."""
        pass
```

#### 9.2 Pattern Library

**File**: `src/patterns/pattern_library.py` (New)

Store and manage reusable patterns:
- Common transformation patterns
- Optimization patterns
- Best practice patterns

**Deliverables**:
- [ ] Pattern detection implemented
- [ ] Pattern library created
- [ ] Pattern suggestion API
- [ ] Documentation

---

## Long-Term Enhancements (Priority 4)

### Step 10: Frontend Integration (Week 8-10)

**Goal**: Build frontend for visualization and interaction

#### 10.1 Graph Visualization

- D3.js or React Flow for graph visualization
- Interactive lineage diagrams
- Impact analysis visualization
- Pattern discovery UI

#### 10.2 Code Generation UI

- Upload XML files
- View canonical model
- Generate code with options
- Review AI suggestions
- Download generated code

**Deliverables**:
- [ ] Graph visualization component
- [ ] Code generation UI
- [ ] Integration with backend API
- [ ] User documentation

---

### Step 11: Testing & Quality Assurance (Ongoing)

**Goal**: Comprehensive testing coverage

#### 11.1 Integration Tests

- End-to-end tests (XML → Graph → Code)
- Graph query tests
- AI agent integration tests
- API endpoint tests

#### 11.2 Performance Tests

- Graph query performance
- Large mapping handling
- Concurrent request handling
- Memory usage optimization

**Deliverables**:
- [ ] Comprehensive test suite
- [ ] Performance benchmarks
- [ ] Load testing results
- [ ] Test coverage report

---

### Step 12: Documentation & Examples (Ongoing)

**Goal**: Complete documentation

#### 12.1 User Documentation

- Getting started guide
- API documentation
- Graph query examples
- Platform extension guide

#### 12.2 Developer Documentation

- Architecture deep dive
- Code generation guide
- AI agent development guide
- Testing guide

#### 12.3 Examples & Tutorials

- Sample mappings
- Common patterns
- Best practices
- Migration scenarios

**Deliverables**:
- [ ] User documentation
- [ ] Developer documentation
- [ ] Example mappings
- [ ] Tutorial videos (optional)

---

## Implementation Checklist

### Immediate (Week 1-2)
- [ ] Step 1: Neo4j Setup & Validation
- [ ] Step 2: Integrate Graph Store into Part 1 Flow
- [ ] Step 3: Verify Part 2 Reads from Graph

### Short-Term (Week 2-4)
- [ ] Step 4: Enhance AI Agents with LLM Integration
- [ ] Step 5: Add Code Review Agent
- [ ] Step 6: Graph Query Enhancements

### Medium-Term (Week 5-8)
- [ ] Step 7: Extensibility Framework
- [ ] Step 8: Enhanced Lineage & Impact Analysis
- [ ] Step 9: Pattern Discovery & Reuse

### Long-Term (Week 8+)
- [ ] Step 10: Frontend Integration
- [ ] Step 11: Testing & Quality Assurance
- [ ] Step 12: Documentation & Examples

---

## Success Criteria

### Phase 1: Graph-First Validation
- ✅ Neo4j running and accessible
- ✅ Canonical models saved to graph
- ✅ Code generators read from graph
- ✅ Graph queries working

### Phase 2: AI Enhancement
- ✅ LLM-based model enhancements working
- ✅ Code review agent functional
- ✅ AI suggestions integrated into flow

### Phase 3: Extensibility
- ✅ Platform abstraction in place
- ✅ Easy to add new target platforms
- ✅ Pattern discovery working

### Phase 4: Production Ready
- ✅ Comprehensive test coverage
- ✅ Performance optimized
- ✅ Documentation complete
- ✅ Frontend integrated (optional)

---

## Next Immediate Action

**Start with Step 1: Neo4j Setup & Validation**

1. Install Neo4j (Docker recommended)
2. Configure environment variables
3. Test GraphStore connection
4. Verify basic save/load operations

Once Step 1 is complete, proceed to Step 2 to integrate graph storage into the Part 1 flow.

---

## Notes

- **Graph-First**: Since we're starting fresh, we're implementing graph-first from the start (no migration needed)
- **Incremental**: Each step builds on the previous one
- **Test-Driven**: Write tests as you implement
- **Documentation**: Update docs as you go

---

This roadmap provides a clear path forward. Focus on immediate steps first, then gradually enhance capabilities.

