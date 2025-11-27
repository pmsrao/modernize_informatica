"""API Routes — Complete implementation of all endpoints."""
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime

from api.models import (
    FileUploadResponse,
    ParseMappingRequest, ParseWorkflowRequest, ParseSessionRequest, ParseWorkletRequest,
    ParseResponse,
    GeneratePySparkRequest, GenerateDLTRequest, GenerateSQLRequest, GenerateSpecRequest,
    GenerateResponse,
    AnalyzeSummaryRequest, AnalyzeRisksRequest, AnalyzeSuggestionsRequest, ExplainExpressionRequest,
    AIAnalysisResponse,
    BuildDAGRequest, DAGResponse,
    ErrorResponse
)
from api.file_manager import file_manager
from parser import MappingParser, WorkflowParser, SessionParser, WorkletParser
from normalizer import MappingNormalizer
from generators import PySparkGenerator, DLTGenerator, SQLGenerator, SpecGenerator
from dag import DAGBuilder, DAGVisualizer
from versioning.version_store import VersionStore
from config import settings
from utils.exceptions import (
    ParsingError, TranslationError, GenerationError, ValidationError,
    ModernizationError
)
from utils.logger import get_logger

# Import ai_agents with fallback for path issues
try:
    from ai_agents import AgentOrchestrator
except ImportError:
    # Try importing from parent directory
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from ai_agents import AgentOrchestrator

logger = get_logger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1", tags=["modernization"])

# Initialize components
version_store = VersionStore(path=settings.version_store_path)
normalizer = MappingNormalizer()
agent_orchestrator = AgentOrchestrator()


# ============================================================================
# File Upload Endpoints
# ============================================================================

@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...)):
    """Upload an Informatica XML file.
    
    Args:
        file: XML file to upload (mapping, workflow, session, or worklet)
        
    Returns:
        File metadata including file_id
    """
    try:
        logger.info(f"File upload requested: {file.filename}")
        
        # Read file content
        content = await file.read()
        
        # Save file
        metadata = file_manager.save_uploaded_file(content, file.filename)
        
        return FileUploadResponse(
            file_id=metadata["file_id"],
            filename=metadata["filename"],
            file_size=metadata["file_size"],
            file_type=metadata["file_type"],
            uploaded_at=datetime.fromisoformat(metadata["uploaded_at"]),
            message="File uploaded successfully"
        )
        
    except ValidationError as e:
        logger.error(f"File upload validation failed: {file.filename}", error=e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"File upload failed: {file.filename}", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )


@router.get("/files/{file_id}")
async def get_file_info(file_id: str):
    """Get file metadata by file ID.
    
    Args:
        file_id: File identifier
        
    Returns:
        File metadata
    """
    metadata = file_manager.get_file_metadata(file_id)
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {file_id}"
        )
    return metadata


# ============================================================================
# Parsing Endpoints
# ============================================================================

@router.post("/parse/mapping", response_model=ParseResponse)
async def parse_mapping(request: ParseMappingRequest):
    """Parse Informatica mapping XML.
    
    Args:
        request: Parse request with file_id or file_path
        
    Returns:
        Parsed mapping data (canonical model)
    """
    try:
        logger.info(f"Parsing mapping: file_id={request.file_id}, file_path={request.file_path}")
        
        # Get file path
        file_path = request.file_path
        if request.file_id:
            file_path = file_manager.get_file_path(request.file_id)
            if not file_path:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File not found: {request.file_id}"
                )
        
        if not file_path:
            raise ValidationError("Either file_id or file_path must be provided", field="file_id")
        
        # Parse mapping
        parser = MappingParser(file_path)
        raw_mapping = parser.parse()
        
        # Normalize to canonical model
        canonical_model = normalizer.normalize(raw_mapping)
        
        # Store in version store
        mapping_id = canonical_model.get("mapping_name", "unknown")
        version_store.save(mapping_id, canonical_model)
        
        logger.info(f"Mapping parsed successfully: {mapping_id}")
        
        return ParseResponse(
            success=True,
            data=canonical_model,
            message="Mapping parsed successfully"
        )
        
    except ParsingError as e:
        logger.error("Mapping parsing failed", error=e)
        return ParseResponse(
            success=False,
            data={},
            message=f"Parsing failed: {str(e)}",
            errors=[str(e)]
        )
    except Exception as e:
        logger.error("Unexpected error during mapping parsing", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Parsing failed: {str(e)}"
        )


@router.post("/parse/workflow", response_model=ParseResponse)
async def parse_workflow(request: ParseWorkflowRequest):
    """Parse Informatica workflow XML.
    
    Args:
        request: Parse request with file_id or file_path
        
    Returns:
        Parsed workflow data
    """
    try:
        logger.info(f"Parsing workflow: file_id={request.file_id}, file_path={request.file_path}")
        
        # Get file path
        file_path = request.file_path
        if request.file_id:
            file_path = file_manager.get_file_path(request.file_id)
            if not file_path:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File not found: {request.file_id}"
                )
        
        if not file_path:
            raise ValidationError("Either file_id or file_path must be provided", field="file_id")
        
        # Parse workflow
        parser = WorkflowParser(file_path)
        workflow_data = parser.parse()
        
        # Store in version store
        workflow_id = workflow_data.get("name", "unknown")
        version_store.save(workflow_id, workflow_data)
        
        logger.info(f"Workflow parsed successfully: {workflow_id}")
        
        return ParseResponse(
            success=True,
            data=workflow_data,
            message="Workflow parsed successfully"
        )
        
    except ParsingError as e:
        logger.error("Workflow parsing failed", error=e)
        return ParseResponse(
            success=False,
            data={},
            message=f"Parsing failed: {str(e)}",
            errors=[str(e)]
        )
    except Exception as e:
        logger.error("Unexpected error during workflow parsing", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Parsing failed: {str(e)}"
        )


@router.post("/parse/session", response_model=ParseResponse)
async def parse_session(request: ParseSessionRequest):
    """Parse Informatica session XML.
    
    Args:
        request: Parse request with file_id or file_path
        
    Returns:
        Parsed session data
    """
    try:
        logger.info(f"Parsing session: file_id={request.file_id}, file_path={request.file_path}")
        
        # Get file path
        file_path = request.file_path
        if request.file_id:
            file_path = file_manager.get_file_path(request.file_id)
            if not file_path:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File not found: {request.file_id}"
                )
        
        if not file_path:
            raise ValidationError("Either file_id or file_path must be provided", field="file_id")
        
        # Parse session
        parser = SessionParser(file_path)
        session_data = parser.parse()
        
        # Store in version store
        session_id = session_data.get("name", "unknown")
        version_store.save(session_id, session_data)
        
        logger.info(f"Session parsed successfully: {session_id}")
        
        return ParseResponse(
            success=True,
            data=session_data,
            message="Session parsed successfully"
        )
        
    except ParsingError as e:
        logger.error("Session parsing failed", error=e)
        return ParseResponse(
            success=False,
            data={},
            message=f"Parsing failed: {str(e)}",
            errors=[str(e)]
        )
    except Exception as e:
        logger.error("Unexpected error during session parsing", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Parsing failed: {str(e)}"
        )


@router.post("/parse/worklet", response_model=ParseResponse)
async def parse_worklet(request: ParseWorkletRequest):
    """Parse Informatica worklet XML.
    
    Args:
        request: Parse request with file_id or file_path
        
    Returns:
        Parsed worklet data
    """
    try:
        logger.info(f"Parsing worklet: file_id={request.file_id}, file_path={request.file_path}")
        
        # Get file path
        file_path = request.file_path
        if request.file_id:
            file_path = file_manager.get_file_path(request.file_id)
            if not file_path:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File not found: {request.file_id}"
                )
        
        if not file_path:
            raise ValidationError("Either file_id or file_path must be provided", field="file_id")
        
        # Parse worklet
        parser = WorkletParser(file_path)
        worklet_data = parser.parse()
        
        # Store in version store
        worklet_id = worklet_data.get("name", "unknown")
        version_store.save(worklet_id, worklet_data)
        
        logger.info(f"Worklet parsed successfully: {worklet_id}")
        
        return ParseResponse(
            success=True,
            data=worklet_data,
            message="Worklet parsed successfully"
        )
        
    except ParsingError as e:
        logger.error("Worklet parsing failed", error=e)
        return ParseResponse(
            success=False,
            data={},
            message=f"Parsing failed: {str(e)}",
            errors=[str(e)]
        )
    except Exception as e:
        logger.error("Unexpected error during worklet parsing", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Parsing failed: {str(e)}"
        )


# ============================================================================
# Generation Endpoints
# ============================================================================

def _get_canonical_model(request) -> dict:
    """Helper to get canonical model from request."""
    if request.canonical_model:
        return request.canonical_model
    elif request.mapping_id:
        return version_store.load(request.mapping_id)
    elif request.file_id:
        # Parse and normalize from file
        file_path = file_manager.get_file_path(request.file_id)
        if not file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {request.file_id}"
            )
        parser = MappingParser(file_path)
        raw_mapping = parser.parse()
        return normalizer.normalize(raw_mapping)
    else:
        raise ValidationError("Either canonical_model, mapping_id, or file_id must be provided")


@router.post("/generate/pyspark", response_model=GenerateResponse)
async def generate_pyspark(request: GeneratePySparkRequest):
    """Generate PySpark code from mapping.
    
    Args:
        request: Generation request with mapping_id, canonical_model, or file_id
        
    Returns:
        Generated PySpark code
    """
    try:
        logger.info("PySpark code generation requested")
        
        # Get canonical model
        canonical_model = _get_canonical_model(request)
        
        # Generate code
        generator = PySparkGenerator()
        code = generator.generate(canonical_model)
        
        logger.info("PySpark code generated successfully")
        
        return GenerateResponse(
            success=True,
            code=code,
            language="pyspark",
            message="PySpark code generated successfully"
        )
        
    except GenerationError as e:
        logger.error("PySpark generation failed", error=e)
        return GenerateResponse(
            success=False,
            code="",
            language="pyspark",
            message=f"Generation failed: {str(e)}",
            errors=[str(e)]
        )
    except Exception as e:
        logger.error("Unexpected error during PySpark generation", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(e)}"
        )


@router.post("/generate/dlt", response_model=GenerateResponse)
async def generate_dlt(request: GenerateDLTRequest):
    """Generate Delta Live Tables pipeline from workflow/mapping.
    
    Args:
        request: Generation request with workflow_id, canonical_model, or file_id
        
    Returns:
        Generated DLT pipeline code
    """
    try:
        logger.info("DLT pipeline generation requested")
        
        # Get canonical model
        canonical_model = _get_canonical_model(request)
        
        # Generate code
        generator = DLTGenerator()
        code = generator.generate(canonical_model)
        
        logger.info("DLT pipeline generated successfully")
        
        return GenerateResponse(
            success=True,
            code=code,
            language="dlt",
            message="DLT pipeline generated successfully"
        )
        
    except GenerationError as e:
        logger.error("DLT generation failed", error=e)
        return GenerateResponse(
            success=False,
            code="",
            language="dlt",
            message=f"Generation failed: {str(e)}",
            errors=[str(e)]
        )
    except Exception as e:
        logger.error("Unexpected error during DLT generation", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(e)}"
        )


@router.post("/generate/sql", response_model=GenerateResponse)
async def generate_sql(request: GenerateSQLRequest):
    """Generate SQL code from mapping.
    
    Args:
        request: Generation request with mapping_id, canonical_model, or file_id
        
    Returns:
        Generated SQL code
    """
    try:
        logger.info("SQL code generation requested")
        
        # Get canonical model
        canonical_model = _get_canonical_model(request)
        
        # Generate SQL code
        generator = SQLGenerator()
        code = generator.generate(canonical_model)
        
        logger.info("SQL code generated successfully")
        
        return GenerateResponse(
            success=True,
            code=code,
            language="sql",
            message="SQL code generated successfully"
        )
        
    except GenerationError as e:
        logger.error("SQL generation failed", error=e)
        return GenerateResponse(
            success=False,
            code="",
            language="sql",
            message=f"Generation failed: {str(e)}",
            errors=[str(e)]
        )
    except Exception as e:
        logger.error("Unexpected error during SQL generation", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(e)}"
        )


@router.post("/generate/spec", response_model=GenerateResponse)
async def generate_spec(request: GenerateSpecRequest):
    """Generate mapping specification document.
    
    Args:
        request: Generation request with mapping_id, canonical_model, or file_id
        
    Returns:
        Generated specification document (Markdown)
    """
    try:
        logger.info("Mapping spec generation requested")
        
        # Get canonical model
        canonical_model = _get_canonical_model(request)
        
        # Generate spec
        generator = SpecGenerator()
        spec = generator.generate(canonical_model)
        
        logger.info("Mapping spec generated successfully")
        
        return GenerateResponse(
            success=True,
            code=spec,
            language="markdown",
            message="Mapping specification generated successfully"
        )
        
    except GenerationError as e:
        logger.error("Spec generation failed", error=e)
        return GenerateResponse(
            success=False,
            code="",
            language="markdown",
            message=f"Generation failed: {str(e)}",
            errors=[str(e)]
        )
    except Exception as e:
        logger.error("Unexpected error during spec generation", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(e)}"
        )


# ============================================================================
# AI Analysis Endpoints
# ============================================================================

def _get_mapping_for_analysis(request) -> dict:
    """Helper to get canonical model for AI analysis."""
    if request.canonical_model:
        return request.canonical_model
    elif request.mapping_id:
        return version_store.load(request.mapping_id)
    else:
        raise ValidationError("Either canonical_model or mapping_id must be provided")


@router.post("/analyze/summary", response_model=AIAnalysisResponse)
async def analyze_summary(request: AnalyzeSummaryRequest):
    """Generate human-readable summary of mapping logic.
    
    Args:
        request: Analysis request with mapping_id or canonical_model
        
    Returns:
        AI-generated summary
    """
    try:
        logger.info("Mapping summary analysis requested")
        
        # Get canonical model
        canonical_model = _get_mapping_for_analysis(request)
        
        # Get AI analysis
        result = agent_orchestrator.run_all(canonical_model)
        
        logger.info("Mapping summary generated successfully")
        
        return AIAnalysisResponse(
            success=True,
            result={"summary": result.get("summary", {})},
            message="Summary generated successfully"
        )
        
    except Exception as e:
        logger.error("Summary analysis failed", error=e)
        return AIAnalysisResponse(
            success=False,
            result={},
            message=f"Analysis failed: {str(e)}",
            errors=[str(e)]
        )


@router.post("/analyze/risks", response_model=AIAnalysisResponse)
async def analyze_risks(request: AnalyzeRisksRequest):
    """Analyze mapping for potential risks and issues.
    
    Args:
        request: Analysis request with mapping_id or canonical_model
        
    Returns:
        Risk analysis results
    """
    try:
        logger.info("Risk analysis requested")
        
        # Get canonical model
        canonical_model = _get_mapping_for_analysis(request)
        
        # Get AI analysis
        result = agent_orchestrator.run_all(canonical_model)
        
        logger.info("Risk analysis completed successfully")
        
        return AIAnalysisResponse(
            success=True,
            result={"risks": result.get("risks", {})},
            message="Risk analysis completed successfully"
        )
        
    except Exception as e:
        logger.error("Risk analysis failed", error=e)
        return AIAnalysisResponse(
            success=False,
            result={},
            message=f"Analysis failed: {str(e)}",
            errors=[str(e)]
        )


@router.post("/analyze/suggestions", response_model=AIAnalysisResponse)
async def analyze_suggestions(request: AnalyzeSuggestionsRequest):
    """Get optimization and modernization suggestions.
    
    Args:
        request: Analysis request with mapping_id or canonical_model
        
    Returns:
        Transformation suggestions
    """
    try:
        logger.info("Transformation suggestions requested")
        
        # Get canonical model
        canonical_model = _get_mapping_for_analysis(request)
        
        # Get AI analysis
        result = agent_orchestrator.run_all(canonical_model)
        
        logger.info("Suggestions generated successfully")
        
        return AIAnalysisResponse(
            success=True,
            result={"suggestions": result.get("suggestions", {})},
            message="Suggestions generated successfully"
        )
        
    except Exception as e:
        logger.error("Suggestions analysis failed", error=e)
        return AIAnalysisResponse(
            success=False,
            result={},
            message=f"Analysis failed: {str(e)}",
            errors=[str(e)]
        )


@router.post("/analyze/explain", response_model=AIAnalysisResponse)
async def explain_expression(request: ExplainExpressionRequest):
    """Explain an Informatica expression in human-readable terms.
    
    Args:
        request: Expression explanation request
        
    Returns:
        Expression explanation
    """
    try:
        logger.info(f"Expression explanation requested: {request.expression[:50]}...")
        
        # Get AI explanation
        # TODO: Implement expression explanation agent
        result = {
            "expression": request.expression,
            "explanation": "Expression explanation not yet fully implemented",
            "context": request.context
        }
        
        logger.info("Expression explanation generated")
        
        return AIAnalysisResponse(
            success=True,
            result=result,
            message="Expression explanation generated"
        )
        
    except Exception as e:
        logger.error("Expression explanation failed", error=e)
        return AIAnalysisResponse(
            success=False,
            result={},
            message=f"Explanation failed: {str(e)}",
            errors=[str(e)]
        )


# ============================================================================
# DAG Endpoints
# ============================================================================

@router.post("/dag/build", response_model=DAGResponse)
async def build_dag(request: BuildDAGRequest):
    """Build execution DAG from workflow.
    
    Args:
        request: DAG build request with workflow_id, workflow_data, or file_id
        
    Returns:
        DAG structure with nodes and edges
    """
    try:
        logger.info("DAG building requested")
        
        # Get workflow data
        workflow_data = request.workflow_data
        if request.workflow_id:
            workflow_data = version_store.load(request.workflow_id)
        elif request.file_id:
            file_path = file_manager.get_file_path(request.file_id)
            if not file_path:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File not found: {request.file_id}"
                )
            parser = WorkflowParser(file_path)
            workflow_data = parser.parse()
        
        if not workflow_data:
            raise ValidationError("Either workflow_data, workflow_id, or file_id must be provided")
        
        # Build DAG
        dag_builder = DAGBuilder()
        # DAGBuilder now accepts workflow and optional sessions/mappings
        dag = dag_builder.build(workflow_data)
        
        # Convert to expected format
        if isinstance(dag, list):
            # Old format - convert to new format
            edges = dag
            nodes = []
            node_names = set()
            for edge in edges:
                node_names.add(edge.get("from"))
                node_names.add(edge.get("to"))
            nodes = [{"id": name, "name": name} for name in node_names]
            dag = {"nodes": nodes, "edges": edges}
        else:
            nodes = dag.get("nodes", [])
            edges = dag.get("edges", [])
        
        logger.info(f"DAG built successfully: {len(nodes)} nodes, {len(edges)} edges")
        
        return DAGResponse(
            success=True,
            dag=dag,
            nodes=nodes,
            edges=edges,
            message="DAG built successfully"
        )
        
    except Exception as e:
        logger.error("DAG building failed", error=e)
        return DAGResponse(
            success=False,
            dag={},
            nodes=[],
            edges=[],
            message=f"DAG building failed: {str(e)}",
            errors=[str(e)]
        )


@router.get("/dag/{dag_id}")
async def get_dag(dag_id: str):
    """Get DAG structure by ID.
    
    Args:
        dag_id: DAG identifier (workflow ID)
        
    Returns:
        DAG structure
    """
    try:
        workflow_data = version_store.load(dag_id)
        if not workflow_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow not found: {dag_id}"
            )
        
        dag_builder = DAGBuilder()
        dag = dag_builder.build(workflow_data)
        
        # Convert to expected format
        if isinstance(dag, list):
            edges = dag
            nodes = []
            node_names = set()
            for edge in edges:
                node_names.add(edge.get("from"))
                node_names.add(edge.get("to"))
            nodes = [{"id": name, "name": name} for name in node_names]
            dag = {"nodes": nodes, "edges": edges}
        
        return DAGResponse(
            success=True,
            dag=dag,
            nodes=dag.get("nodes", []),
            edges=dag.get("edges", []),
            message="DAG retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"DAG retrieval failed: {dag_id}", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DAG retrieval failed: {str(e)}"
        )


@router.post("/dag/visualize")
async def visualize_dag(request: BuildDAGRequest, format: str = "json", include_metadata: bool = False):
    """Visualize DAG in specified format.
    
    Args:
        request: DAG build request with workflow_id, workflow_data, or file_id
        format: Visualization format (dot, json, mermaid, svg)
        include_metadata: Whether to include node metadata
        
    Returns:
        Visualization string in requested format
    """
    try:
        logger.info(f"DAG visualization requested: format={format}")
        
        # Get workflow data
        workflow_data = request.workflow_data
        if request.workflow_id:
            workflow_data = version_store.load(request.workflow_id)
        elif request.file_id:
            file_path = file_manager.get_file_path(request.file_id)
            if not file_path:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File not found: {request.file_id}"
                )
            parser = WorkflowParser(file_path)
            workflow_data = parser.parse()
        
        if not workflow_data:
            raise ValidationError("Either workflow_data, workflow_id, or file_id must be provided")
        
        # Build DAG
        dag_builder = DAGBuilder()
        dag = dag_builder.build(workflow_data)
        
        # Convert to expected format if needed
        if isinstance(dag, list):
            edges = dag
            nodes = []
            node_names = set()
            for edge in edges:
                node_names.add(edge.get("from"))
                node_names.add(edge.get("to"))
            nodes = [{"id": name, "name": name} for name in node_names]
            dag = {"nodes": nodes, "edges": edges}
        
        # Visualize
        visualizer = DAGVisualizer()
        visualization = visualizer.visualize(dag, format=format, include_metadata=include_metadata)
        
        # Return appropriate content type
        from fastapi.responses import Response
        content_type = {
            "dot": "text/plain",
            "json": "application/json",
            "mermaid": "text/plain",
            "svg": "image/svg+xml"
        }.get(format.lower(), "text/plain")
        
        return Response(content=visualization, media_type=content_type)
        
    except ValueError as e:
        logger.error(f"Invalid visualization format: {format}", error=e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("DAG visualization failed", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DAG visualization failed: {str(e)}"
        )
