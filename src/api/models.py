"""Pydantic models for API requests and responses."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# File Upload Models
class FileUploadResponse(BaseModel):
    """Response model for file upload."""
    file_id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    file_type: str = Field(..., description="File type (mapping, workflow, session, worklet)")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    message: str = Field(default="File uploaded successfully")


# Parsing Models
class ParseMappingRequest(BaseModel):
    """Request model for parsing mapping XML."""
    file_id: Optional[str] = Field(None, description="File ID from upload")
    file_path: Optional[str] = Field(None, description="Direct file path (alternative to file_id)")


class ParseWorkflowRequest(BaseModel):
    """Request model for parsing workflow XML."""
    file_id: Optional[str] = Field(None, description="File ID from upload")
    file_path: Optional[str] = Field(None, description="Direct file path (alternative to file_id)")


class ParseSessionRequest(BaseModel):
    """Request model for parsing session XML."""
    file_id: Optional[str] = Field(None, description="File ID from upload")
    file_path: Optional[str] = Field(None, description="Direct file path (alternative to file_id)")


class ParseWorkletRequest(BaseModel):
    """Request model for parsing worklet XML."""
    file_id: Optional[str] = Field(None, description="File ID from upload")
    file_path: Optional[str] = Field(None, description="Direct file path (alternative to file_id)")


class ParseResponse(BaseModel):
    """Response model for parsing operations."""
    success: bool = Field(..., description="Whether parsing was successful")
    data: Dict[str, Any] = Field(..., description="Parsed data or canonical model")
    message: str = Field(default="Parsing completed successfully")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")


# Generation Models
class GeneratePySparkRequest(BaseModel):
    """Request model for PySpark code generation."""
    mapping_id: Optional[str] = Field(None, description="Mapping ID from version store")
    canonical_model: Optional[Dict[str, Any]] = Field(None, description="Canonical model directly")
    file_id: Optional[str] = Field(None, description="File ID to parse and generate from")


class GenerateDLTRequest(BaseModel):
    """Request model for DLT pipeline generation."""
    workflow_id: Optional[str] = Field(None, description="Workflow ID from version store")
    canonical_model: Optional[Dict[str, Any]] = Field(None, description="Canonical model directly")
    file_id: Optional[str] = Field(None, description="File ID to parse and generate from")


class GenerateSQLRequest(BaseModel):
    """Request model for SQL generation."""
    mapping_id: Optional[str] = Field(None, description="Mapping ID from version store")
    canonical_model: Optional[Dict[str, Any]] = Field(None, description="Canonical model directly")
    file_id: Optional[str] = Field(None, description="File ID to parse and generate from")


class GenerateSpecRequest(BaseModel):
    """Request model for mapping spec generation."""
    mapping_id: Optional[str] = Field(None, description="Mapping ID from version store")
    canonical_model: Optional[Dict[str, Any]] = Field(None, description="Canonical model directly")
    file_id: Optional[str] = Field(None, description="File ID to parse and generate from")


class GenerateResponse(BaseModel):
    """Response model for code generation."""
    success: bool = Field(..., description="Whether generation was successful")
    code: str = Field(..., description="Generated code")
    language: str = Field(..., description="Programming language (pyspark, dlt, sql, markdown)")
    message: str = Field(default="Code generated successfully")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")


# AI Analysis Models
class AnalyzeSummaryRequest(BaseModel):
    """Request model for mapping summary analysis."""
    mapping_id: Optional[str] = Field(None, description="Mapping ID from version store")
    canonical_model: Optional[Dict[str, Any]] = Field(None, description="Canonical model directly")


class AnalyzeRisksRequest(BaseModel):
    """Request model for risk analysis."""
    mapping_id: Optional[str] = Field(None, description="Mapping ID from version store")
    canonical_model: Optional[Dict[str, Any]] = Field(None, description="Canonical model directly")


class AnalyzeSuggestionsRequest(BaseModel):
    """Request model for transformation suggestions."""
    mapping_id: Optional[str] = Field(None, description="Mapping ID from version store")
    canonical_model: Optional[Dict[str, Any]] = Field(None, description="Canonical model directly")


class ExplainExpressionRequest(BaseModel):
    """Request model for expression explanation."""
    expression: str = Field(..., description="Informatica expression to explain")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class AIAnalysisResponse(BaseModel):
    """Response model for AI analysis operations."""
    success: bool = Field(..., description="Whether analysis was successful")
    result: Dict[str, Any] = Field(..., description="Analysis results")
    message: str = Field(default="Analysis completed successfully")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")


# DAG Models
class BuildDAGRequest(BaseModel):
    """Request model for DAG building."""
    workflow_id: Optional[str] = Field(None, description="Workflow ID from version store")
    workflow_data: Optional[Dict[str, Any]] = Field(None, description="Workflow data directly")
    file_id: Optional[str] = Field(None, description="File ID to parse and build DAG from")


class DAGResponse(BaseModel):
    """Response model for DAG operations."""
    success: bool = Field(..., description="Whether DAG building was successful")
    dag: Dict[str, Any] = Field(..., description="DAG structure")
    nodes: List[Dict[str, Any]] = Field(..., description="List of DAG nodes")
    edges: List[Dict[str, Any]] = Field(..., description="List of DAG edges")
    message: str = Field(default="DAG built successfully")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")


# Error Models
class ErrorResponse(BaseModel):
    """Standard error response model."""
    success: bool = Field(default=False)
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

