"""API Routes — Complete implementation of all endpoints."""
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
from datetime import datetime

from .models import (
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
from .file_manager import file_manager
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

# Initialize graph store if enabled
graph_store = None
graph_queries = None
if settings.enable_graph_store:
    try:
        from src.graph.graph_store import GraphStore
        from src.graph.graph_queries import GraphQueries
        
        graph_store = GraphStore(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password
        )
        graph_queries = GraphQueries(graph_store)
        
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
        
        logger.info("Graph store initialized and enabled")
    except Exception as e:
        logger.warning(f"Failed to initialize graph store: {str(e)}")
        graph_store = None
        graph_queries = None


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
        file_type: Optional filter by file type (mapping, workflow, session, worklet)
        
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
                graph_store.save_mapping(enhanced_model)
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
            review=review_result
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
        mappings = graph_queries.find_mappings_using_table(table_name, database)
        
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
        dependencies = graph_queries.find_dependent_mappings(mapping_name)
        
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
        stats = graph_queries.get_mapping_statistics()
        
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
        mappings = graph_queries.find_pattern_across_mappings(pattern_type, pattern_value)
        
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
                mappings.append({
                    "name": record["name"],
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
        canonical_model = graph_store.load_mapping(mapping_name)
        if not canonical_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mapping not found: {mapping_name}"
            )
        
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
            from_trans = conn.get("from_transformation", "") or conn.get("from", "")
            to_trans = conn.get("to_transformation", "") or conn.get("to", "")
            from_port = conn.get("from_port", "") or conn.get("from_port", "")
            to_port = conn.get("to_port", "") or conn.get("to_port", "")
            
            if not from_trans or not to_trans:
                continue
            
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
