"""API Routes — Complete implementation of all endpoints."""
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
from datetime import datetime

from .models import (
    FileUploadResponse,
    ParseMappingRequest, ParseWorkflowRequest, ParseSessionRequest, ParseWorkletRequest, ParseMappletRequest,
    ParseResponse,
    GeneratePySparkRequest, GenerateDLTRequest, GenerateSQLRequest, GenerateSpecRequest,
    GenerateOrchestrationRequest,
    GenerateResponse,
    AnalyzeSummaryRequest, AnalyzeRisksRequest, AnalyzeSuggestionsRequest, ExplainExpressionRequest,
    AIAnalysisResponse,
    BuildDAGRequest, DAGResponse,
    ErrorResponse
)
from .file_manager import file_manager
from parser import MappingParser, WorkflowParser, SessionParser, WorkletParser, MappletParser
from normalizer import MappingNormalizer
from generators import (
    PySparkGenerator, DLTGenerator, SQLGenerator, SpecGenerator,
    OrchestrationGenerator, CodeQualityChecker
)
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

# Initialize graph store if enabled
graph_store = None
graph_queries = None
profiler = None
analyzer = None
wave_planner = None
report_generator = None
if settings.enable_graph_store:
    try:
        from src.graph.graph_store import GraphStore
        from src.graph.graph_queries import GraphQueries
        from src.assessment.profiler import Profiler
        from src.assessment.analyzer import Analyzer
        from src.assessment.wave_planner import WavePlanner
        from src.assessment.report_generator import ReportGenerator
        
        graph_store = GraphStore(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password
        )
        graph_queries = GraphQueries(graph_store)
        
        # Initialize assessment components
        profiler = Profiler(graph_store)
        analyzer = Analyzer(graph_store, profiler)
        wave_planner = WavePlanner(graph_store, profiler, analyzer)
        report_generator = ReportGenerator(graph_store, profiler, analyzer, wave_planner)
        
        # Update version store to use graph
        if settings.graph_first:
            version_store = VersionStore(
                path=settings.version_store_path,
                graph_store=graph_store,
                graph_first=True
            )
        else:
            version_store = VersionStore(
                path=settings.version_store_path,
                graph_store=graph_store,
                graph_first=False
            )
        
        logger.info("Graph store and assessment components initialized and enabled")
    except Exception as e:
        logger.warning(f"Failed to initialize graph store: {str(e)}")
        graph_store = None
        graph_queries = None
        profiler = None
        analyzer = None
        wave_planner = None
        report_generator = None


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


@router.post("/upload/directory", status_code=status.HTTP_201_CREATED)
async def upload_directory(files: list[UploadFile] = File(...)):
    """Upload multiple files from a directory (zip or multiple files).
    
    Args:
        files: List of XML files to upload
        
    Returns:
        Summary of uploaded files with metadata
    """
    try:
        logger.info(f"Directory upload requested: {len(files)} files")
        
        uploaded_files = []
        errors = []
        
        for file in files:
            try:
                # Read file content
                content = await file.read()
                
                # Save file
                metadata = file_manager.save_uploaded_file(content, file.filename)
                uploaded_files.append(metadata)
                
            except ValidationError as e:
                errors.append({
                    "filename": file.filename,
                    "error": str(e)
                })
                logger.warning(f"Failed to upload {file.filename}: {str(e)}")
            except Exception as e:
                errors.append({
                    "filename": file.filename,
                    "error": str(e)
                })
                logger.error(f"Failed to upload {file.filename}: {str(e)}")
        
        # Generate summary
        summary = {
            "total_files": len(files),
            "uploaded": len(uploaded_files),
            "failed": len(errors),
            "files": uploaded_files,
            "errors": errors
        }
        
        # Group by file type
        by_type = {}
        for file_meta in uploaded_files:
            file_type = file_meta.get("file_type", "unknown")
            if file_type not in by_type:
                by_type[file_type] = []
            by_type[file_type].append(file_meta)
        
        summary["by_type"] = by_type
        
        logger.info(f"Directory upload completed: {len(uploaded_files)}/{len(files)} files uploaded")
        
        return {
            "success": True,
            "summary": summary,
            "message": f"Uploaded {len(uploaded_files)}/{len(files)} files successfully"
        }
        
    except Exception as e:
        logger.error(f"Directory upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Directory upload failed: {str(e)}"
        )


@router.get("/files")
async def list_all_files(file_type: Optional[str] = None):
    """List all uploaded files.
    
    Args:
        file_type: Optional filter by file type (mapping, workflow, session, worklet, mapplet)
        
    Returns:
        List of file metadata
    """
    try:
        if file_type:
            files = file_manager.get_files_by_type(file_type)
        else:
            files = file_manager.list_all_files()
        
        # Group by type for summary
        by_type = {}
        for file_meta in files:
            ftype = file_meta.get("file_type", "unknown")
            if ftype not in by_type:
                by_type[ftype] = []
            by_type[ftype].append(file_meta)
        
        return {
            "success": True,
            "total": len(files),
            "files": files,
            "by_type": by_type
        }
    except Exception as e:
        logger.error(f"List files failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"List files failed: {str(e)}"
        )


@router.get("/hierarchy")
async def get_hierarchy(file_ids: Optional[str] = None):
    """Get Informatica component hierarchy graph.
    
    Args:
        file_ids: Optional comma-separated list of file IDs to include. If not provided, uses all files.
        
    Returns:
        Hierarchy graph with nodes and edges
    """
    try:
        from src.api.hierarchy_builder import HierarchyBuilder
        
        builder = HierarchyBuilder()
        
        # Parse file_ids if provided
        file_id_list = None
        if file_ids:
            file_id_list = [fid.strip() for fid in file_ids.split(",") if fid.strip()]
        
        hierarchy = builder.build_hierarchy_from_files(file_id_list)
        
        return {
            "success": True,
            "hierarchy": hierarchy
        }
    except Exception as e:
        logger.error(f"Hierarchy build failed: {str(e)}", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hierarchy build failed: {str(e)}"
        )


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
        
        # AI Enhancement (Part 1: Enhance canonical model)
        enhanced_model = canonical_model
        enhancement_applied = False
        if request.enhance_model:
            try:
                enhanced_result = agent_orchestrator.process_with_enhancement(
                    canonical_model,
                    enable_enhancement=True
                )
                enhanced_model = enhanced_result.get("canonical_model", canonical_model)
                enhancement_applied = enhanced_result.get("enhancement_applied", False)
                logger.info(f"AI enhancement applied: {enhancement_applied}")
            except Exception as e:
                logger.warning(f"AI enhancement failed, using original model: {str(e)}")
                enhanced_model = canonical_model
        
        # Store in version store (saves to graph if graph_first=True)
        mapping_name = enhanced_model.get("mapping_name", "unknown")
        version_store.save(mapping_name, enhanced_model)
        
        # Also store by file_id if available for easier lookup
        if request.file_id:
            version_store.save(request.file_id, enhanced_model)
        
        # Explicitly save to graph if graph store is enabled (redundant but ensures it's saved)
        if graph_store:
            try:
                graph_store.save_transformation(enhanced_model)
                logger.debug(f"Model explicitly saved to graph: {mapping_name}")
            except Exception as e:
                logger.warning(f"Failed to save to graph explicitly: {str(e)}")
        
        logger.info(f"Mapping parsed successfully: {mapping_name} (enhancement: {enhancement_applied})")
        
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


@router.post("/parse/mapplet", response_model=ParseResponse)
async def parse_mapplet(request: ParseMappletRequest):
    """Parse Informatica mapplet XML.
    
    Args:
        request: Parse request with file_id or file_path
        
    Returns:
        Parsed mapplet data
    """
    try:
        logger.info(f"Parsing mapplet: file_id={request.file_id}, file_path={request.file_path}")
        
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
        
        # Parse mapplet
        parser = MappletParser(file_path)
        mapplet_data = parser.parse()
        
        # Store in version store
        mapplet_id = mapplet_data.get("name", "unknown")
        version_store.save(mapplet_id, mapplet_data)
        
        logger.info(f"Mapplet parsed successfully: {mapplet_id}")
        
        return ParseResponse(
            success=True,
            data=mapplet_data,
            message="Mapplet parsed successfully"
        )
        
    except ParsingError as e:
        logger.error("Mapplet parsing failed", error=e)
        return ParseResponse(
            success=False,
            data={},
            message=f"Parsing failed: {str(e)}",
            errors=[str(e)]
        )
    except Exception as e:
        logger.error("Unexpected error during mapplet parsing", error=e)
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
    elif hasattr(request, 'mapping_id') and request.mapping_id:
        return version_store.load(request.mapping_id)
    elif hasattr(request, 'workflow_id') and request.workflow_id:
        # For workflows, we might need to aggregate multiple mappings
        # For now, return the workflow structure
        return version_store.load(request.workflow_id)
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
        
        # Quality check
        quality_checker = CodeQualityChecker()
        quality_result = quality_checker.check_code_quality(code, "pyspark", canonical_model)
        
        # Optional: Review code (if requested)
        review_result = None
        if hasattr(request, 'review_code') and request.review_code:
            try:
                review_result = agent_orchestrator.review_code(code, canonical_model)
                if review_result.get("needs_fix"):
                    # Auto-fix if high severity issues found
                    if review_result.get("severity") == "HIGH":
                        fix_result = agent_orchestrator.fix_code(
                            code, 
                            review_result.get("issues", []),
                            canonical_model
                        )
                        code = fix_result.get("fixed_code", code)
                        logger.info("Code auto-fixed based on review")
            except Exception as e:
                logger.warning(f"Code review failed: {str(e)}")
        
        logger.info("PySpark code generated successfully")
        
        return GenerateResponse(
            success=True,
            code=code,
            language="pyspark",
            message="PySpark code generated successfully",
            review=review_result,
            quality_check=quality_result
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


@router.post("/generate/orchestration", response_model=GenerateResponse)
async def generate_orchestration(request: GenerateOrchestrationRequest):
    """Generate workflow orchestration code (Airflow, Databricks, Prefect).
    
    Args:
        request: Orchestration generation request with workflow_id, workflow_data, or file_id
        
    Returns:
        Generated orchestration code
    """
    try:
        logger.info(f"Orchestration generation requested for platform: {request.platform}")
        
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
        
        # If graph store is available, enhance workflow structure
        if graph_store and graph_queries:
            workflow_name = workflow_data.get("name", "unknown")
            enhanced_structure = graph_queries.get_pipeline_structure(workflow_name)
            if enhanced_structure:
                workflow_data = enhanced_structure
        
        # Generate orchestration code
        generator = OrchestrationGenerator()
        
        if request.platform == "airflow":
            code = generator.generate_airflow_dag(workflow_data, schedule=request.schedule)
            language = "python"
        elif request.platform == "databricks":
            workflow_json = generator.generate_databricks_workflow(workflow_data, 
                                                                 schedule={"quartz_cron_expression": request.schedule or "0 0 0 * * ?"} if request.schedule else None)
            import json
            code = json.dumps(workflow_json, indent=2)
            language = "json"
        elif request.platform == "prefect":
            code = generator.generate_prefect_flow(workflow_data)
            language = "python"
        else:
            raise ValidationError(f"Unsupported platform: {request.platform}. Supported: airflow, databricks, prefect")
        
        # Quality check for Python code
        quality_result = None
        if language == "python":
            quality_checker = CodeQualityChecker()
            quality_result = quality_checker.check_code_quality(code, "python")
        
        logger.info(f"Orchestration code generated successfully for {request.platform}")
        
        return GenerateResponse(
            success=True,
            code=code,
            language=language,
            message=f"Orchestration code generated successfully for {request.platform}",
            quality_check=quality_result
        )
        
    except ValidationError as e:
        logger.error("Orchestration generation validation failed", error=e)
        return GenerateResponse(
            success=False,
            code="",
            language=request.platform,
            message=f"Validation failed: {str(e)}",
            errors=[str(e)]
        )
    except Exception as e:
        logger.error("Unexpected error during orchestration generation", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestration generation failed: {str(e)}"
        )


# ============================================================================
# AI Analysis Endpoints
# ============================================================================

def _get_mapping_for_analysis(request) -> dict:
    """Helper to get canonical model for AI analysis."""
    if request.canonical_model:
        if not isinstance(request.canonical_model, dict):
            raise ValidationError("canonical_model must be a dictionary")
        return request.canonical_model
    
    # Try file_id first (most common case)
    file_id = getattr(request, 'file_id', None) or getattr(request, 'mapping_id', None)
    
    if not file_id:
        raise ValidationError("Either canonical_model, mapping_id, or file_id must be provided")
    
    # First, try to load from version store by file_id (could be UUID or mapping_name)
    model = version_store.load(file_id)
    if model and isinstance(model, dict):
        logger.debug(f"Loaded mapping from version store: {file_id}")
        return model
    
    # If not found, try treating as file_id and parse the file
    file_path = file_manager.get_file_path(file_id)
    if file_path and os.path.exists(file_path):
        logger.info(f"Parsing file for analysis: {file_path}")
        try:
            parser = MappingParser(file_path)
            raw_mapping = parser.parse()
            canonical_model = normalizer.normalize(raw_mapping)
            
            if not canonical_model or not isinstance(canonical_model, dict):
                raise ValidationError("Failed to normalize mapping to canonical model")
            
            # Store it by both file_id and mapping_name for future use
            mapping_name = canonical_model.get("mapping_name", "unknown")
            version_store.save(file_id, canonical_model)  # Store by file_id
            version_store.save(mapping_name, canonical_model)  # Store by mapping_name
            logger.info(f"Mapping parsed and stored: {mapping_name} (file_id: {file_id})")
            return canonical_model
        except Exception as e:
            logger.error(f"Failed to parse file for analysis: {file_path}", error=e)
            raise ValidationError(f"Failed to parse file: {str(e)}")
    
    # If still not found, check if it's a mapping_name that was stored
    # (This handles the case where someone uses mapping_name as mapping_id)
    model = version_store.load(file_id)
    if model and isinstance(model, dict):
        logger.debug(f"Loaded mapping by name from version store: {file_id}")
        return model
    
    raise ValidationError(
        f"Mapping not found: {file_id}. "
        "Please ensure: 1) The file has been uploaded, 2) The file has been parsed, "
        "or 3) Provide the canonical_model directly."
    )


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
        
        # Get AI analysis using MappingSummaryAgent
        from ai_agents.mapping_summary_agent import MappingSummaryAgent
        summary_agent = MappingSummaryAgent()
        result = summary_agent.summarize(canonical_model)
        
        logger.info("Mapping summary generated successfully")
        
        return AIAnalysisResponse(
            success=True,
            result={"summary": result},
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
        
        # Get AI analysis using RiskDetectionAgent
        from ai_agents.risk_detection_agent import RiskDetectionAgent
        risk_agent = RiskDetectionAgent()
        result = risk_agent.detect_risks(canonical_model)
        
        logger.info("Risk analysis completed successfully")
        
        return AIAnalysisResponse(
            success=True,
            result={"risks": result},
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
        
        # Get AI analysis using TransformationSuggestionAgent
        from ai_agents.transformation_suggestion_agent import TransformationSuggestionAgent
        suggestion_agent = TransformationSuggestionAgent()
        result = suggestion_agent.suggest(canonical_model)
        
        logger.info("Suggestions generated successfully")
        
        return AIAnalysisResponse(
            success=True,
            result={"suggestions": result},
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
        
        # Get AI explanation using RuleExplainerAgent
        from ai_agents.rule_explainer_agent import RuleExplainerAgent
        explainer_agent = RuleExplainerAgent()
        
        field_name = request.context.get("field_name", "field") if request.context else "field"
        explanation = explainer_agent.explain_expression(
            request.expression,
            field_name,
            request.context
        )
        
        result = {
            "expression": request.expression,
            "field_name": field_name,
            "explanation": explanation,
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


# ============================================================================
# Graph Query Endpoints (Phase 3: Graph-First)
# ============================================================================

@router.get("/graph/mappings/using-table/{table_name}")
async def get_mappings_using_table(table_name: str, database: Optional[str] = None):
    """Get all mappings using a specific table.
    
    Args:
        table_name: Table name
        database: Optional database name
        
    Returns:
        List of mappings using the table
    """
    if not graph_store or not graph_queries:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph store not enabled. Set ENABLE_GRAPH_STORE=true"
        )
    
    try:
        mappings = graph_queries.find_transformations_using_table(table_name, database)
        
        return {
            "success": True,
            "table": table_name,
            "database": database,
            "mappings": mappings,
            "count": len(mappings)
        }
    except Exception as e:
        logger.error(f"Graph query failed: {str(e)}", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Graph query failed: {str(e)}"
        )


@router.get("/graph/mappings/{mapping_name}/dependencies")
async def get_dependencies(mapping_name: str):
    """Get all mappings that depend on this mapping.
    
    Args:
        mapping_name: Mapping name
        
    Returns:
        List of dependent mappings
    """
    if not graph_store or not graph_queries:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph store not enabled. Set ENABLE_GRAPH_STORE=true"
        )
    
    try:
        dependencies = graph_queries.find_dependent_transformations(mapping_name)
        
        return {
            "success": True,
            "mapping": mapping_name,
            "dependencies": dependencies,
            "count": len(dependencies)
        }
    except Exception as e:
        logger.error(f"Graph query failed: {str(e)}", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Graph query failed: {str(e)}"
        )


@router.get("/graph/lineage/trace")
async def trace_lineage(source_table: str, target_table: str, database: Optional[str] = None):
    """Trace data lineage from source to target.
    
    Args:
        source_table: Source table name
        target_table: Target table name
        database: Optional database name
        
    Returns:
        Lineage path
    """
    if not graph_store or not graph_queries:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph store not enabled. Set ENABLE_GRAPH_STORE=true"
        )
    
    try:
        lineage = graph_queries.trace_lineage(source_table, target_table, database)
        
        return {
            "success": True,
            "source": source_table,
            "target": target_table,
            "database": database,
            "lineage": lineage
        }
    except Exception as e:
        logger.error(f"Lineage trace failed: {str(e)}", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lineage trace failed: {str(e)}"
        )


@router.get("/graph/migration/order")
async def get_migration_order():
    """Get recommended migration order.
    
    Returns:
        List of mappings in migration order
    """
    if not graph_store or not graph_queries:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph store not enabled. Set ENABLE_GRAPH_STORE=true"
        )
    
    try:
        order = graph_queries.get_migration_order()
        
        return {
            "success": True,
            "migration_order": order,
            "count": len(order)
        }
    except Exception as e:
        logger.error(f"Migration order query failed: {str(e)}", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration order query failed: {str(e)}"
        )


@router.get("/graph/statistics")
async def get_graph_statistics():
    """Get overall statistics about mappings in graph.
    
    Returns:
        Statistics dictionary
    """
    if not graph_store or not graph_queries:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph store not enabled. Set ENABLE_GRAPH_STORE=true"
        )
    
    try:
        stats = graph_queries.get_transformation_statistics()
        
        return {
            "success": True,
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Statistics query failed: {str(e)}", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Statistics query failed: {str(e)}"
        )


@router.get("/graph/mappings/{mapping_name}/impact")
async def get_impact_analysis(mapping_name: str):
    """Get comprehensive impact analysis for a mapping.
    
    Args:
        mapping_name: Mapping name to analyze
        
    Returns:
        Impact analysis results
    """
    if not graph_store or not graph_queries:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph store not enabled. Set ENABLE_GRAPH_STORE=true"
        )
    
    try:
        impact = graph_queries.get_impact_analysis(mapping_name)
        
        return {
            "success": True,
            "mapping": mapping_name,
            "impact_analysis": impact
        }
    except Exception as e:
        logger.error(f"Impact analysis failed: {str(e)}", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Impact analysis failed: {str(e)}"
        )


@router.get("/graph/patterns/{pattern_type}")
async def find_pattern(pattern_type: str, pattern_value: str):
    """Find mappings using a specific pattern.
    
    Args:
        pattern_type: Type of pattern (expression, transformation, table)
        pattern_value: Pattern value to search for
        
    Returns:
        List of mappings using the pattern
    """
    if not graph_store or not graph_queries:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph store not enabled. Set ENABLE_GRAPH_STORE=true"
        )
    
    try:
        mappings = graph_queries.find_pattern_across_transformations(pattern_type, pattern_value)
        
        return {
            "success": True,
            "pattern_type": pattern_type,
            "pattern_value": pattern_value,
            "mappings": mappings,
            "count": len(mappings)
        }
    except Exception as e:
        logger.error(f"Pattern search failed: {str(e)}", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pattern search failed: {str(e)}"
        )


@router.get("/graph/migration/readiness")
async def get_migration_readiness():
    """Get migration readiness assessment for all mappings.
    
    Returns:
        List of mappings with readiness scores
    """
    if not graph_store or not graph_queries:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph store not enabled. Set ENABLE_GRAPH_STORE=true"
        )
    
    try:
        readiness = graph_queries.get_migration_readiness()
        
        return {
            "success": True,
            "readiness_assessment": readiness,
            "count": len(readiness)
        }
    except Exception as e:
        logger.error(f"Migration readiness assessment failed: {str(e)}", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration readiness assessment failed: {str(e)}"
        )


@router.get("/graph/mappings")
async def list_all_mappings():
    """List all mappings in the graph with metadata.
    
    Returns:
        List of mappings with metadata
    """
    if not graph_store or not graph_queries:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph store not enabled. Set ENABLE_GRAPH_STORE=true"
        )
    
    try:
        with graph_store.driver.session() as session:
            result = session.run("""
                MATCH (m:Mapping)
                OPTIONAL MATCH (m)-[:HAS_SOURCE]->(s:Source)
                OPTIONAL MATCH (m)-[:HAS_TARGET]->(t:Target)
                OPTIONAL MATCH (m)-[:HAS_TRANSFORMATION]->(trans:Transformation)
                RETURN m.name as name,
                       m.mapping_name as mapping_name,
                       m.complexity as complexity,
                       count(DISTINCT s) as source_count,
                       count(DISTINCT t) as target_count,
                       count(DISTINCT trans) as transformation_count
                ORDER BY m.name
            """)
            
            mappings = []
            for record in result:
                # Filter out invalid/unknown mappings
                mapping_name = record["name"]
                if not mapping_name or mapping_name.lower() == "unknown" or mapping_name == "":
                    continue
                    
                mappings.append({
                    "name": mapping_name,
                    "mapping_name": record["mapping_name"],
                    "complexity": record["complexity"],
                    "source_count": record["source_count"],
                    "target_count": record["target_count"],
                    "transformation_count": record["transformation_count"]
                })
        
        return {
            "success": True,
            "mappings": mappings,
            "count": len(mappings)
        }
    except Exception as e:
        logger.error(f"List mappings failed: {str(e)}", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"List mappings failed: {str(e)}"
        )


@router.get("/graph/workflows")
async def list_workflows():
    """List all workflows with sessions and mappings.
    
    Returns:
        List of workflows with their structure
    """
    if not graph_store or not graph_queries:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph store not enabled. Set ENABLE_GRAPH_STORE=true"
        )
    
    try:
        pipelines = graph_queries.list_pipelines()
        
        # Enhance with full structure
        enhanced_pipelines = []
        for pipeline in pipelines:
            pipeline_name = pipeline.get("name")
            if pipeline_name:
                structure = graph_queries.get_pipeline_structure(pipeline_name)
                if structure:
                    enhanced_pipelines.append(structure)
                else:
                    enhanced_pipelines.append(pipeline)
        
        return {
            "success": True,
            "pipelines": enhanced_pipelines,
            "workflows": enhanced_pipelines,  # Backward compatibility alias
            "count": len(enhanced_pipelines)
        }
    except Exception as e:
        logger.error(f"List workflows failed: {str(e)}", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"List workflows failed: {str(e)}"
        )


@router.get("/graph/workflows/{workflow_name}")
async def get_workflow_structure_endpoint(workflow_name: str):
    """Get complete workflow structure with tasks and transformations.
    
    Returns a generic canonical model representation:
    - Workflow contains Tasks (generic term for Informatica Sessions)
    - Tasks contain Transformations (generic term for Informatica Mappings)
    
    Args:
        workflow_name: Workflow name
        
    Returns:
        Workflow structure with tasks and transformations in canonical model format
        Structure: {
            "name": "...",
            "type": "...",
            "properties": {...},
            "tasks": [  # Generic term
                {
                    "name": "...",
                    "type": "...",
                    "properties": {...},
                    "transformations": [...]  # Generic term
                }
            ]
        }
    """
    if not graph_store or not graph_queries:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph store not enabled. Set ENABLE_GRAPH_STORE=true"
        )
    
    try:
        structure = graph_queries.get_pipeline_structure(workflow_name)
        
        if not structure:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow not found: {workflow_name}"
            )
        
        return {
            "success": True,
            "workflow": structure
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get workflow structure failed: {str(e)}", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Get workflow structure failed: {str(e)}"
        )


@router.get("/graph/components")
async def list_all_components():
    """List all components (workflows, sessions, worklets, mappings) with file metadata.
    
    Returns:
        Dictionary with all components grouped by type and counts
    """
    if not graph_store or not graph_queries:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph store not enabled. Set ENABLE_GRAPH_STORE=true"
        )
    
    try:
        # Get all components
        pipelines = graph_queries.list_pipelines()
        transformations = graph_store.list_all_mappings()  # Returns transformation names
        
        # Get tasks, sub pipelines, and reusable transformations
        with graph_store.driver.session() as session:
            tasks_result = session.run("""
                MATCH (t:Task)
                RETURN t.name as name, t.type as type, t.source_component_type as source_component_type, properties(t) as properties
                ORDER BY t.name
            """)
            tasks = [dict(record) for record in tasks_result]
            
            sub_pipelines_result = session.run("""
                MATCH (sp:SubPipeline)
                RETURN sp.name as name, sp.type as type, sp.source_component_type as source_component_type, properties(sp) as properties
                ORDER BY sp.name
            """)
            sub_pipelines = [dict(record) for record in sub_pipelines_result]
            
            reusable_transformations_result = session.run("""
                MATCH (rt:ReusableTransformation)
                RETURN rt.name as name, rt.type as type, rt.source_component_type as source_component_type, properties(rt) as properties
                ORDER BY rt.name
            """)
            reusable_transformations = [dict(record) for record in reusable_transformations_result]
        
        # Enhance with file metadata
        for pipeline in pipelines:
            file_meta = graph_queries.get_component_file_metadata(pipeline["name"], "Pipeline")
            if file_meta:
                pipeline["file_metadata"] = file_meta
        
        for task in tasks:
            file_meta = graph_queries.get_component_file_metadata(task["name"], "Task")
            if file_meta:
                task["file_metadata"] = file_meta
        
        for sub_pipeline in sub_pipelines:
            file_meta = graph_queries.get_component_file_metadata(sub_pipeline["name"], "SubPipeline")
            if file_meta:
                sub_pipeline["file_metadata"] = file_meta
        
        for reusable_transformation in reusable_transformations:
            file_meta = graph_queries.get_component_file_metadata(reusable_transformation["name"], "ReusableTransformation")
            if file_meta:
                reusable_transformation["file_metadata"] = file_meta
        
        # Get transformations with file metadata
        transformations_with_meta = []
        for transformation_name in transformations:
            transformation_info = {"name": transformation_name}
            file_meta = graph_queries.get_component_file_metadata(transformation_name, "Transformation")
            if file_meta:
                transformation_info["file_metadata"] = file_meta
            transformations_with_meta.append(transformation_info)
        
        # Return both new generic names and old Informatica-specific names for backward compatibility
        return {
            "success": True,
            # New generic names
            "pipelines": pipelines,
            "tasks": tasks,
            "sub_pipelines": sub_pipelines,
            "reusable_transformations": reusable_transformations,
            "transformations": transformations_with_meta,
            # Old Informatica-specific names (for backward compatibility with frontend)
            "workflows": pipelines,  # Alias for pipelines
            "sessions": tasks,  # Alias for tasks
            "worklets": sub_pipelines,  # Alias for sub_pipelines
            "mapplets": reusable_transformations,  # Alias for reusable_transformations
            "mappings": transformations_with_meta,  # Alias for transformations
            "counts": {
                # New generic counts
                "pipelines": len(pipelines),
                "tasks": len(tasks),
                "sub_pipelines": len(sub_pipelines),
                "reusable_transformations": len(reusable_transformations),
                "transformations": len(transformations),
                # Old Informatica-specific counts (for backward compatibility)
                "workflows": len(pipelines),
                "sessions": len(tasks),
                "worklets": len(sub_pipelines),
                "mapplets": len(reusable_transformations),
                "mappings": len(transformations)
            }
        }
    except Exception as e:
        logger.error(f"List components failed: {str(e)}", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"List components failed: {str(e)}"
        )


@router.get("/graph/files")
async def list_all_files():
    """List all source files with metadata.
    
    Returns:
        List of source files with metadata
    """
    if not graph_store or not graph_queries:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph store not enabled. Set ENABLE_GRAPH_STORE=true"
        )
    
    try:
        files = graph_queries.list_all_source_files()
        return {
            "success": True,
            "files": files,
            "count": len(files)
        }
    except Exception as e:
        logger.error(f"List files failed: {str(e)}", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"List files failed: {str(e)}"
        )


@router.get("/graph/files/{component_type}/{component_name}")
async def get_file_metadata(component_type: str, component_name: str):
    """Get file metadata for a specific component.
    
    Args:
        component_type: Type of component (Workflow, Session, Worklet, Mapping)
        component_name: Name of the component
        
    Returns:
        File metadata dictionary
    """
    if not graph_store or not graph_queries:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph store not enabled. Set ENABLE_GRAPH_STORE=true"
        )
    
    try:
        file_meta = graph_queries.get_component_file_metadata(component_name, component_type)
        if not file_meta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File metadata not found for {component_type}: {component_name}"
            )
        
        return {
            "success": True,
            "file_metadata": file_meta
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get file metadata failed: {str(e)}", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Get file metadata failed: {str(e)}"
        )


@router.get("/graph/source/repository")
async def get_source_repository():
    """Get repository tree structure of source files (staging directory).
    
    Returns:
        Tree structure of source files from staging directory
    """
    if not graph_store or not graph_queries:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph store not enabled. Set ENABLE_GRAPH_STORE=true"
        )
    
    try:
        tree = graph_queries.get_source_repository_structure()
        # Return empty structure if no source files exist yet
        if not tree or (isinstance(tree, dict) and len(tree) == 0):
            return {
                "success": True,
                "repository": {}
            }
        return {
            "success": True,
            "repository": tree
        }
    except Exception as e:
        logger.error(f"Get source repository failed: {str(e)}", error=e)
        # Return empty structure instead of error
        return {
            "success": True,
            "repository": {},
            "message": "No source files found in repository"
        }


@router.get("/graph/code/repository")
async def get_code_repository():
    """Get repository tree structure of generated code.
    
    Returns:
        Tree structure organized by workflow/session/mapping
    """
    if not graph_store or not graph_queries:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph store not enabled. Set ENABLE_GRAPH_STORE=true"
        )
    
    try:
        tree = graph_queries.get_code_repository_structure()
        # Return empty structure if no code files exist yet
        if not tree or (isinstance(tree, dict) and len(tree) == 0):
            return {
                "success": True,
                "repository": {
                    "review_summary.json": {"type": "file", "path": "review_summary.json"},
                    "workflows": {}
                }
            }
        return {
            "success": True,
            "repository": tree
        }
    except Exception as e:
        logger.error(f"Get code repository failed: {str(e)}", error=e)
        # Return empty structure instead of error
        return {
            "success": True,
            "repository": {
                "review_summary.json": {"type": "file", "path": "review_summary.json"},
                "workflows": {}
            },
            "message": "No code files found in repository"
        }


@router.get("/graph/code/{mapping_name}")
async def get_mapping_code(mapping_name: str):
    """Get code metadata for a mapping.
    
    Args:
        mapping_name: Name of the mapping
        
    Returns:
        List of code files with metadata
    """
    if not graph_store or not graph_queries:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph store not enabled. Set ENABLE_GRAPH_STORE=true"
        )
    
    try:
        code_files = graph_queries.get_transformation_code_files(mapping_name)
        # Filter out any None or invalid entries and ensure file_path is present
        code_files = [f for f in code_files if f and f.get("file_path")]
        
        # Log for debugging
        logger.debug(f"Found {len(code_files)} code file(s) for mapping: {mapping_name}")
        for f in code_files:
            logger.debug(f"  - {f.get('file_path')} (type: {f.get('code_type')})")
        
        return {
            "success": True,
            "mapping_name": mapping_name,
            "code_files": code_files,
            "count": len(code_files)
        }
    except Exception as e:
        logger.error(f"Get mapping code failed: {str(e)}", error=e)
        # Return empty list instead of error if code files don't exist yet
        return {
            "success": True,
            "mapping_name": mapping_name,
            "code_files": [],
            "count": 0,
            "message": "No code files found for this mapping"
        }


@router.get("/graph/source/file/{file_path:path}")
async def get_source_file(file_path: str):
    """Read actual source file content from filesystem.
    
    Args:
        file_path: Path to the source file (URL encoded, relative to staging directory)
        
    Returns:
        File content and metadata
    """
    import urllib.parse
    import os
    from pathlib import Path
    
    try:
        # Decode the file path
        decoded_path = urllib.parse.unquote(file_path)
        
        # Security check: ensure path is within project directory
        project_root = Path(__file__).parent.parent.parent
        
        # Handle both absolute and relative paths
        if os.path.isabs(decoded_path):
            # Absolute path provided - verify it's within project
            full_path = Path(decoded_path).resolve()
            if not str(full_path).startswith(str(project_root.resolve())):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: File path outside project directory"
                )
        else:
            # Relative path - resolve from staging directory
            full_path = (project_root / "test_log" / "staging" / decoded_path).resolve()
            
            if not str(full_path).startswith(str(project_root.resolve())):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: File path outside project directory"
                )
        
        if not full_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source file not found: {decoded_path}"
            )
        
        # Try to read as text, fallback to binary if needed
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
        except UnicodeDecodeError:
            # If UTF-8 fails, read as binary and encode
            with open(full_path, 'rb') as f:
                file_content = f.read()
                # Return as base64 or indicate binary
                import base64
                file_content = base64.b64encode(file_content).decode('ascii')
                return {
                    "success": True,
                    "file_path": decoded_path,
                    "content": file_content,
                    "is_binary": True,
                    "file_size": full_path.stat().st_size
                }
        
        return {
            "success": True,
            "file_path": decoded_path,
            "content": file_content,
            "is_binary": False,
            "file_size": full_path.stat().st_size
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Read source file failed: {str(e)}", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Read source file failed: {str(e)}"
        )


@router.get("/graph/code/file/{file_path:path}")
async def get_code_file(file_path: str):
    """Read actual code content from filesystem.
    
    Args:
        file_path: Path to the code file (URL encoded)
        
    Returns:
        Code content and metadata
    """
    import urllib.parse
    import os
    from pathlib import Path
    
    try:
        # Decode the file path
        decoded_path = urllib.parse.unquote(file_path)
        
        # Security check: ensure path is within project directory
        project_root = Path(__file__).parent.parent.parent
        
        # Handle both absolute and relative paths
        if os.path.isabs(decoded_path):
            # Absolute path provided - verify it's within project
            full_path = Path(decoded_path).resolve()
            if not str(full_path).startswith(str(project_root.resolve())):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: File path outside project directory"
                )
        else:
            # Relative path - try test_log/generated_ai first, then test_log/generated, then project root
            # Check if path starts with test_log/generated_ai or test_log/generated
            if decoded_path.startswith("test_log/generated_ai/"):
                full_path = (project_root / decoded_path).resolve()
            elif decoded_path.startswith("test_log/generated/"):
                full_path = (project_root / decoded_path).resolve()
            else:
                # Try generated_ai first, then fallback to generated
                full_path = (project_root / "test_log" / "generated_ai" / decoded_path).resolve()
                if not full_path.exists():
                    full_path = (project_root / "test_log" / "generated" / decoded_path).resolve()
            
            if not str(full_path).startswith(str(project_root.resolve())):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: File path outside project directory"
                )
        
        if not full_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Code file not found: {decoded_path}"
            )
        
        with open(full_path, 'r') as f:
            code_content = f.read()
        
        return {
            "success": True,
            "file_path": decoded_path,
            "code": code_content,
            "file_size": full_path.stat().st_size
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Read code file failed: {str(e)}", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Read code file failed: {str(e)}"
        )


@router.get("/graph/mappings/{mapping_name}/structure")
async def get_mapping_structure(mapping_name: str):
    """Get complete mapping structure for visualization.
    
    Args:
        mapping_name: Mapping name
        
    Returns:
        Mapping structure with nodes and edges for graph visualization
    """
    if not graph_store or not graph_queries:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph store not enabled. Set ENABLE_GRAPH_STORE=true"
        )
    
    try:
        # Load canonical model from graph
        canonical_model = graph_store.load_transformation(mapping_name)
        if not canonical_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mapping not found: {mapping_name}"
            )
        
        # Also query graph relationships directly to get all connections
        with graph_store.driver.session() as session:
            # Get all CONNECTS_TO relationships (Source->Trans, Trans->Trans, Trans->Target)
            all_conns = session.run("""
                MATCH (a)-[r:CONNECTS_TO]->(b)
                WHERE (a:Source OR a:Transformation OR a:Target) 
                  AND (b:Transformation OR b:Target)
                  AND ((a:Source AND a.transformation = $name) OR 
                       (a:Transformation AND a.transformation = $name) OR
                       (a:Target AND a.transformation = $name))
                  AND ((b:Transformation AND b.transformation = $name) OR
                       (b:Target AND b.transformation = $name))
                RETURN a.name as from, b.name as to, r.from_port as from_port, r.to_port as to_port
            """, name=mapping_name)
            
            # Add these to connectors if not already present
            existing_conns = {(c.get("from_transformation", ""), c.get("to_transformation", "")) 
                             for c in canonical_model.get("connectors", [])}
            
            for record in all_conns:
                from_trans = record["from"]
                to_trans = record["to"]
                if (from_trans, to_trans) not in existing_conns:
                    canonical_model.setdefault("connectors", []).append({
                        "from_transformation": from_trans,
                        "to_transformation": to_trans,
                        "from_port": record.get("from_port", ""),
                        "to_port": record.get("to_port", "")
                    })
            
            logger.info(f"Total connectors after graph query: {len(canonical_model.get('connectors', []))}")
        
        # Build graph structure for visualization
        nodes = []
        edges = []
        
        # Add mapping node
        nodes.append({
            "id": f"mapping_{mapping_name}",
            "type": "mapping",
            "label": canonical_model.get("mapping_name", mapping_name),
            "data": {
                "name": mapping_name,
                "complexity": canonical_model.get("complexity", "unknown"),
                "type": "mapping"
            }
        })
        
        # Add source nodes
        sources = canonical_model.get("sources", [])
        for idx, source in enumerate(sources):
            source_id = f"source_{mapping_name}_{idx}"
            nodes.append({
                "id": source_id,
                "type": "source",
                "label": source.get("name", f"Source {idx}"),
                "data": {
                    "name": source.get("name"),
                    "type": "source",
                    "table": source.get("table", {}).get("name") if isinstance(source.get("table"), dict) else None,
                    "database": source.get("table", {}).get("database") if isinstance(source.get("table"), dict) else None
                }
            })
            edges.append({
                "id": f"edge_{mapping_name}_to_{source_id}",
                "source": f"mapping_{mapping_name}",
                "target": source_id,
                "type": "has_source",
                "label": "HAS_SOURCE"
            })
        
        # Add target nodes
        targets = canonical_model.get("targets", [])
        for idx, target in enumerate(targets):
            target_id = f"target_{mapping_name}_{idx}"
            nodes.append({
                "id": target_id,
                "type": "target",
                "label": target.get("name", f"Target {idx}"),
                "data": {
                    "name": target.get("name"),
                    "type": "target",
                    "table": target.get("table", {}).get("name") if isinstance(target.get("table"), dict) else None,
                    "database": target.get("table", {}).get("database") if isinstance(target.get("table"), dict) else None
                }
            })
            edges.append({
                "id": f"edge_{mapping_name}_to_{target_id}",
                "source": f"mapping_{mapping_name}",
                "target": target_id,
                "type": "has_target",
                "label": "HAS_TARGET"
            })
        
        # Add transformation nodes and create name-to-id mapping
        transformation_map = {}  # transformation_name -> node_id
        transformations = canonical_model.get("transformations", [])
        for idx, trans in enumerate(transformations):
            trans_name = trans.get("name", f"Trans_{idx}")
            trans_id = f"trans_{mapping_name}_{trans_name}"
            transformation_map[trans_name] = trans_id
            
            nodes.append({
                "id": trans_id,
                "type": "transformation",
                "label": trans_name,
                "data": {
                    "name": trans_name,
                    "type": trans.get("type", "unknown"),
                    "transformation_type": trans.get("type", "unknown")
                }
            })
            edges.append({
                "id": f"edge_{mapping_name}_to_{trans_id}",
                "source": f"mapping_{mapping_name}",
                "target": trans_id,
                "type": "has_transformation",
                "label": "HAS_TRANSFORMATION"
            })
        
        # Build edges from connectors (actual data flow)
        connectors = canonical_model.get("connectors", [])
        source_map = {}  # source_name -> node_id
        target_map = {}  # target_name -> node_id
        
        # Create source name mapping
        for idx, source in enumerate(sources):
            source_name = source.get("name", f"Source_{idx}")
            source_id = f"source_{mapping_name}_{idx}"
            source_map[source_name] = source_id
        
        # Create target name mapping
        for idx, target in enumerate(targets):
            target_name = target.get("name", f"Target_{idx}")
            target_id = f"target_{mapping_name}_{idx}"
            target_map[target_name] = target_id
        
        # Process connectors to build data flow edges
        edge_set = set()  # Track edges to avoid duplicates
        
        logger.debug(f"Processing {len(connectors)} connectors for mapping {mapping_name}")
        
        for conn in connectors:
            from_trans = conn.get("from_transformation", "") or conn.get("from", "") or conn.get("frominstance", "")
            to_trans = conn.get("to_transformation", "") or conn.get("to", "") or conn.get("toinstance", "")
            from_port = conn.get("from_port", "") or conn.get("fromfield", "")
            to_port = conn.get("to_port", "") or conn.get("tofield", "")
            
            if not from_trans or not to_trans:
                logger.debug(f"Skipping connector with missing from/to: {conn}")
                continue
            
            logger.debug(f"Processing connector: {from_trans} -> {to_trans}")
            
            # Check if from_trans is a source
            if from_trans in source_map:
                source_id = source_map[from_trans]
                if to_trans in transformation_map:
                    trans_id = transformation_map[to_trans]
                    edge_id = f"edge_{source_id}_to_{trans_id}"
                    if edge_id not in edge_set:
                        edges.append({
                            "id": edge_id,
                            "source": source_id,
                            "target": trans_id,
                            "type": "flows_to",
                            "label": "FLOWS_TO"
                        })
                        edge_set.add(edge_id)
                        logger.debug(f"Added edge: {from_trans} -> {to_trans}")
            
            # Check if to_trans is a target
            elif to_trans in target_map:
                target_id = target_map[to_trans]
                if from_trans in transformation_map:
                    trans_id = transformation_map[from_trans]
                    edge_id = f"edge_{trans_id}_to_{target_id}"
                    if edge_id not in edge_set:
                        edges.append({
                            "id": edge_id,
                            "source": trans_id,
                            "target": target_id,
                            "type": "flows_to",
                            "label": "FLOWS_TO"
                        })
                        edge_set.add(edge_id)
                        logger.debug(f"Added edge: {from_trans} -> {to_trans}")
            
            # Transformation to transformation
            elif from_trans in transformation_map and to_trans in transformation_map:
                from_id = transformation_map[from_trans]
                to_id = transformation_map[to_trans]
                edge_id = f"edge_{from_id}_to_{to_id}"
                if edge_id not in edge_set:
                    edges.append({
                        "id": edge_id,
                        "source": from_id,
                        "target": to_id,
                        "type": "flows_to",
                        "label": "FLOWS_TO",
                        "data": {
                            "from_port": from_port,
                            "to_port": to_port
                        }
                    })
                    edge_set.add(edge_id)
                    logger.debug(f"Added edge: {from_trans} -> {to_trans}")
        
        logger.debug(f"Created {len(edges)} total edges (including structural edges)")
        
        # Also use lineage information if connectors are missing
        if not connectors and canonical_model.get("lineage"):
            lineage = canonical_model.get("lineage", {})
            transformation_lineage = lineage.get("transformation_level", [])
            
            for lineage_item in transformation_lineage:
                from_trans = lineage_item.get("from", "")
                to_trans = lineage_item.get("to", "")
                
                if from_trans in source_map:
                    source_id = source_map[from_trans]
                    if to_trans in transformation_map:
                        trans_id = transformation_map[to_trans]
                        edge_id = f"edge_{source_id}_to_{trans_id}"
                        if edge_id not in edge_set:
                            edges.append({
                                "id": edge_id,
                                "source": source_id,
                                "target": trans_id,
                                "type": "flows_to",
                                "label": "FLOWS_TO"
                            })
                            edge_set.add(edge_id)
                
                elif to_trans in target_map:
                    target_id = target_map[to_trans]
                    if from_trans in transformation_map:
                        trans_id = transformation_map[from_trans]
                        edge_id = f"edge_{trans_id}_to_{target_id}"
                        if edge_id not in edge_set:
                            edges.append({
                                "id": edge_id,
                                "source": trans_id,
                                "target": target_id,
                                "type": "flows_to",
                                "label": "FLOWS_TO"
                            })
                            edge_set.add(edge_id)
                
                elif from_trans in transformation_map and to_trans in transformation_map:
                    from_id = transformation_map[from_trans]
                    to_id = transformation_map[to_trans]
                    edge_id = f"edge_{from_id}_to_{to_id}"
                    if edge_id not in edge_set:
                        edges.append({
                            "id": edge_id,
                            "source": from_id,
                            "target": to_id,
                            "type": "flows_to",
                            "label": "FLOWS_TO"
                        })
                        edge_set.add(edge_id)
        
        # Fallback: Connect Source Qualifiers to sources (if no connectors)
        if not connectors:
            for idx, trans in enumerate(transformations):
                trans_name = trans.get("name", "")
                trans_type = trans.get("type", "")
                trans_id = transformation_map.get(trans_name)
                
                if trans_type == "SourceQualifier" and trans_id:
                    # Find associated source (usually by name pattern)
                    for source_idx, source in enumerate(sources):
                        source_name = source.get("name", "")
                        # Try to match source qualifier to source
                        if source_name.upper() in trans_name.upper() or trans_name.upper() in source_name.upper():
                            source_id = source_map.get(source_name)
                            if source_id:
                                edge_id = f"edge_{source_id}_to_{trans_id}"
                                if edge_id not in edge_set:
                                    edges.append({
                                        "id": edge_id,
                                        "source": source_id,
                                        "target": trans_id,
                                        "type": "flows_to",
                                        "label": "FLOWS_TO"
                                    })
                                    edge_set.add(edge_id)
        
        logger.info(f"Built graph structure: {len(nodes)} nodes, {len(edges)} edges for mapping {mapping_name}")
        
        return {
            "success": True,
            "mapping": mapping_name,
            "graph": {
                "nodes": nodes,
                "edges": edges
            },
            "canonical_model": canonical_model
        }
    except Exception as e:
        logger.error(f"Get mapping structure failed: {str(e)}", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Get mapping structure failed: {str(e)}"
        )


# ============================================================================
# Assessment Endpoints
# ============================================================================

@router.get("/assessment/profile")
async def get_assessment_profile():
    """Get repository profile statistics.
    
    Returns:
        Repository statistics including component counts and distributions
    """
    if not profiler:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Assessment module not available. Graph store must be enabled."
        )
    
    try:
        profile = profiler.profile_repository()
        return JSONResponse(content=profile)
    except Exception as e:
        logger.error(f"Error profiling repository: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to profile repository: {str(e)}"
        )


@router.get("/assessment/analyze")
async def get_assessment_analysis():
    """Run analysis and identify blockers.
    
    Returns:
        Analysis results including patterns, blockers, and effort estimates
    """
    if not analyzer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Assessment module not available. Graph store must be enabled."
        )
    
    try:
        patterns = analyzer.identify_patterns()
        blockers = analyzer.identify_blockers()
        effort = analyzer.estimate_migration_effort()
        dependencies = analyzer.find_dependencies()
        categorized = analyzer.categorize_by_complexity()
        
        analysis = {
            "patterns": patterns,
            "blockers": blockers,
            "effort_estimates": effort,
            "dependencies": dependencies,
            "categorized_components": categorized
        }
        
        return JSONResponse(content=analysis)
    except Exception as e:
        logger.error(f"Error analyzing repository: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze repository: {str(e)}"
        )


@router.get("/assessment/waves")
async def get_migration_waves(max_wave_size: int = 10):
    """Get migration wave recommendations.
    
    Args:
        max_wave_size: Maximum number of components per wave (default: 10)
    
    Returns:
        Migration wave plan with component groupings
    """
    if not wave_planner:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Assessment module not available. Graph store must be enabled."
        )
    
    try:
        wave_plan = report_generator.generate_wave_plan(max_wave_size=max_wave_size)
        return JSONResponse(content=wave_plan)
    except Exception as e:
        logger.error(f"Error generating migration waves: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate migration waves: {str(e)}"
        )


@router.get("/assessment/report")
async def get_assessment_report(format: str = "json"):
    """Generate assessment report.
    
    Args:
        format: Report format - "json" or "summary" (default: "json")
    
    Returns:
        Assessment report in requested format
    """
    if not report_generator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Assessment module not available. Graph store must be enabled."
        )
    
    try:
        if format == "summary":
            report = report_generator.generate_summary_report()
        else:
            report = report_generator.generate_detailed_report()
        
        return JSONResponse(content=report)
    except Exception as e:
        logger.error(f"Error generating assessment report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate assessment report: {str(e)}"
        )


@router.get("/assessment/tco")
async def get_tco_analysis(
    informatica_cost: Optional[float] = None,
    migration_cost: Optional[float] = None,
    current_runtime_hours: Optional[float] = None
):
    """Calculate TCO and ROI analysis.
    
    Args:
        informatica_cost: Annual Informatica licensing cost (optional)
        migration_cost: One-time migration cost for ROI calculation (optional)
        current_runtime_hours: Current total runtime in hours per day (optional)
    
    Returns:
        TCO and ROI analysis results
    """
    if not tco_calculator or not profiler:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="TCO calculator not available. Graph store must be enabled."
        )
    
    try:
        # Get repository metrics
        repository_metrics = profiler.profile_repository()
        
        # Calculate TCO
        tco_data = tco_calculator.calculate_tco(
            informatica_annual_cost=informatica_cost,
            repository_metrics=repository_metrics
        )
        
        # Calculate ROI if migration cost provided
        roi_data = None
        if migration_cost:
            annual_savings = tco_data.get('savings', {}).get('annual', 0)
            roi_data = tco_calculator.calculate_roi(
                migration_cost=migration_cost,
                annual_savings=annual_savings
            )
        
        # Estimate runtime improvements
        runtime_data = tco_calculator.estimate_runtime_improvement(
            repository_metrics=repository_metrics,
            current_runtime_hours=current_runtime_hours
        )
        
        # Generate comprehensive report
        report = tco_calculator.generate_cost_analysis_report(
            tco_data=tco_data,
            roi_data=roi_data,
            runtime_data=runtime_data
        )
        
        return JSONResponse(content=report)
    except Exception as e:
        logger.error(f"Error calculating TCO: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate TCO: {str(e)}"
        )


# ============================================================================
# Reconciliation Endpoints
# ============================================================================

@router.post("/reconciliation/mapping")
async def reconcile_mapping(request: Dict[str, Any]):
    """Reconcile a single mapping between source and target.
    
    Request body:
        - mapping_name: Name of the mapping
        - source_connection: Source connection details (Informatica)
        - target_connection: Target connection details (Databricks)
        - comparison_method: Method to use ('count', 'hash', 'threshold', 'sampling')
        - options: Optional comparison options
    
    Returns:
        Reconciliation results
    """
    if not reconciliation_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reconciliation engine not available."
        )
    
    try:
        mapping_name = request.get('mapping_name')
        source_connection = request.get('source_connection', {})
        target_connection = request.get('target_connection', {})
        comparison_method = request.get('comparison_method', 'count')
        options = request.get('options', {})
        
        if not mapping_name:
            raise ValidationError("mapping_name is required")
        
        result = reconciliation_engine.reconcile_mapping(
            mapping_name=mapping_name,
            source_connection=source_connection,
            target_connection=target_connection,
            comparison_method=comparison_method,
            options=options
        )
        
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error reconciling mapping: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reconciliation failed: {str(e)}"
        )


@router.post("/reconciliation/workflow")
async def reconcile_workflow(request: Dict[str, Any]):
    """Reconcile all mappings in a workflow.
    
    Request body:
        - workflow_name: Name of the workflow
        - source_connection: Source connection details
        - target_connection: Target connection details
        - comparison_method: Method to use
        - options: Optional comparison options
    
    Returns:
        Workflow reconciliation results
    """
    if not reconciliation_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reconciliation engine not available."
        )
    
    try:
        workflow_name = request.get('workflow_name')
        source_connection = request.get('source_connection', {})
        target_connection = request.get('target_connection', {})
        comparison_method = request.get('comparison_method', 'count')
        options = request.get('options', {})
        
        if not workflow_name:
            raise ValidationError("workflow_name is required")
        
        result = reconciliation_engine.reconcile_workflow(
            workflow_name=workflow_name,
            source_connection=source_connection,
            target_connection=target_connection,
            comparison_method=comparison_method,
            options=options
        )
        
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error reconciling workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow reconciliation failed: {str(e)}"
        )


@router.post("/reconciliation/incremental")
async def reconcile_incremental(request: Dict[str, Any]):
    """Reconcile incremental data (for phased migrations).
    
    Request body:
        - mapping_name: Name of the mapping
        - source_connection: Source connection details
        - target_connection: Target connection details
        - incremental_key: Key column for incremental comparison
        - start_value: Start value for incremental range
        - end_value: End value for incremental range
        - comparison_method: Method to use
        - options: Optional comparison options
    
    Returns:
        Incremental reconciliation results
    """
    if not reconciliation_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reconciliation engine not available."
        )
    
    try:
        mapping_name = request.get('mapping_name')
        source_connection = request.get('source_connection', {})
        target_connection = request.get('target_connection', {})
        incremental_key = request.get('incremental_key')
        start_value = request.get('start_value')
        end_value = request.get('end_value')
        comparison_method = request.get('comparison_method', 'count')
        options = request.get('options', {})
        
        if not mapping_name or not incremental_key:
            raise ValidationError("mapping_name and incremental_key are required")
        
        result = reconciliation_engine.reconcile_incremental(
            mapping_name=mapping_name,
            source_connection=source_connection,
            target_connection=target_connection,
            incremental_key=incremental_key,
            start_value=start_value,
            end_value=end_value,
            comparison_method=comparison_method,
            options=options
        )
        
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error in incremental reconciliation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Incremental reconciliation failed: {str(e)}"
        )


@router.post("/testing/generate-tests")
async def generate_tests(request: Dict[str, Any]):
    """Generate automated tests for generated code.
    
    Request body:
        - mapping_name: Name of the mapping
        - code_type: Type of code ('pyspark', 'sql')
        - generated_code: Generated code string
        - canonical_model: Canonical model
        - test_data: Optional test data
    
    Returns:
        Generated test code
    """
    try:
        from src.generators.test_generator import TestGenerator
        
        mapping_name = request.get('mapping_name')
        code_type = request.get('code_type', 'pyspark')
        generated_code = request.get('generated_code', '')
        canonical_model = request.get('canonical_model', {})
        test_data = request.get('test_data')
        
        if not mapping_name or not canonical_model:
            raise ValidationError("mapping_name and canonical_model are required")
        
        test_generator = TestGenerator()
        
        if code_type == 'pyspark':
            test_code = test_generator.generate_pyspark_tests(
                canonical_model=canonical_model,
                generated_code=generated_code,
                test_data=test_data
            )
        elif code_type == 'sql':
            test_code = test_generator.generate_sql_tests(
                canonical_model=canonical_model,
                generated_sql=generated_code,
                test_data=test_data
            )
        else:
            raise ValidationError(f"Unsupported code type: {code_type}")
        
        return JSONResponse(content={
            'success': True,
            'test_code': test_code,
            'mapping_name': mapping_name,
            'code_type': code_type
        })
        
    except Exception as e:
        logger.error(f"Error generating tests: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test generation failed: {str(e)}"
        )


@router.post("/testing/validate-test-data")
async def validate_test_data(request: Dict[str, Any]):
    """Validate test data against canonical model.
    
    Request body:
        - canonical_model: Canonical model
        - test_data: Test data to validate
        - expected_output: Expected output data
        - code_type: Type of code ('pyspark', 'sql')
    
    Returns:
        Validation results
    """
    try:
        from src.validation.test_data_validator import TestDataValidator
        
        canonical_model = request.get('canonical_model', {})
        test_data = request.get('test_data', [])
        expected_output = request.get('expected_output', [])
        code_type = request.get('code_type', 'pyspark')
        
        if not canonical_model or not test_data:
            raise ValidationError("canonical_model and test_data are required")
        
        validator = TestDataValidator()
        
        validation_result = validator.validate_transformation_logic(
            canonical_model=canonical_model,
            test_data=test_data,
            expected_output=expected_output,
            code_type=code_type
        )
        
        return JSONResponse(content={
            'success': True,
            'validation_result': validation_result
        })
        
    except Exception as e:
        logger.error(f"Error validating test data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test data validation failed: {str(e)}"
        )


@router.post("/testing/run-integration-tests")
async def run_integration_tests(request: Dict[str, Any]):
    """Run integration tests.
    
    Request body:
        - test_suite: Test suite definition
        - test_config: Optional test configuration
    
    Returns:
        Test results
    """
    try:
        from src.testing.integration_test_framework import IntegrationTestFramework
        
        test_suite = request.get('test_suite', {})
        test_config = request.get('test_config', {})
        
        if not test_suite:
            raise ValidationError("test_suite is required")
        
        framework = IntegrationTestFramework(test_config=test_config)
        results = framework.run_test_suite(test_suite)
        
        return JSONResponse(content={
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error running integration tests: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Integration test execution failed: {str(e)}"
        )


@router.post("/review/code")
async def review_code(request: Dict[str, Any]):
    """Review generated code for issues and improvements.
    
    Args:
        request: Dictionary with 'code' and optional 'canonical_model'
        
    Returns:
        Review results
    """
    try:
        code = request.get("code", "")
        canonical_model = request.get("canonical_model")
        
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Code is required"
            )
        
        review = agent_orchestrator.review_code(code, canonical_model)
        
        return {
            "success": True,
            "review": review
        }
    except Exception as e:
        logger.error(f"Code review failed: {str(e)}", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code review failed: {str(e)}"
        )
