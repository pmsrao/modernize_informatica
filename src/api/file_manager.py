"""File management utilities for API."""
import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from config import settings
from utils.exceptions import ValidationError
from utils.logger import get_logger

logger = get_logger(__name__)


class FileManager:
    """Manages file uploads and storage."""
    
    def __init__(self):
        """Initialize file manager."""
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.file_registry: Dict[str, Dict[str, Any]] = {}
    
    def save_uploaded_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Save uploaded file and return metadata.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            
        Returns:
            Dictionary with file_id, file_path, and metadata
            
        Raises:
            ValidationError: If file validation fails
        """
        # Validate file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in settings.allowed_file_extensions:
            raise ValidationError(
                f"File extension {file_ext} not allowed. Allowed: {settings.allowed_file_extensions}",
                field="filename"
            )
        
        # Validate file size
        file_size = len(file_content)
        if file_size > settings.max_upload_size:
            raise ValidationError(
                f"File size {file_size} exceeds maximum {settings.max_upload_size} bytes",
                field="file_size"
            )
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Determine file type from extension or content
        file_type = self._detect_file_type(filename, file_content)
        
        # Save file
        file_path = self.upload_dir / f"{file_id}{file_ext}"
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Store metadata
        metadata = {
            "file_id": file_id,
            "filename": filename,
            "file_path": str(file_path),
            "file_size": file_size,
            "file_type": file_type,
            "uploaded_at": datetime.utcnow().isoformat()
        }
        self.file_registry[file_id] = metadata
        
        logger.info(f"File uploaded: {filename} (ID: {file_id}, Size: {file_size} bytes)")
        
        return metadata
    
    def get_file_path(self, file_id: str) -> Optional[str]:
        """Get file path by file ID.
        
        Args:
            file_id: File identifier
            
        Returns:
            File path or None if not found
        """
        if file_id in self.file_registry:
            return self.file_registry[file_id]["file_path"]
        return None
    
    def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get file metadata by file ID.
        
        Args:
            file_id: File identifier
            
        Returns:
            File metadata or None if not found
        """
        return self.file_registry.get(file_id)
    
    def delete_file(self, file_id: str) -> bool:
        """Delete file by file ID.
        
        Args:
            file_id: File identifier
            
        Returns:
            True if deleted, False if not found
        """
        if file_id not in self.file_registry:
            return False
        
        metadata = self.file_registry[file_id]
        file_path = Path(metadata["file_path"])
        
        if file_path.exists():
            file_path.unlink()
        
        del self.file_registry[file_id]
        logger.info(f"File deleted: {file_id}")
        return True
    
    def _detect_file_type(self, filename: str, content: bytes) -> str:
        """Detect file type from filename or content.
        
        Args:
            filename: Original filename
            content: File content
            
        Returns:
            File type (mapping, workflow, session, worklet, unknown)
        """
        filename_lower = filename.lower()
        
        # Check filename patterns
        if "mapping" in filename_lower or "map" in filename_lower:
            return "mapping"
        elif "workflow" in filename_lower or "wf" in filename_lower:
            return "workflow"
        elif "session" in filename_lower or "sess" in filename_lower:
            return "session"
        elif "worklet" in filename_lower:
            return "worklet"
        
        # Try to detect from XML content
        try:
            content_str = content[:1000].decode('utf-8', errors='ignore')
            if '<MAPPING' in content_str or '<Mapping' in content_str:
                return "mapping"
            elif '<WORKFLOW' in content_str or '<Workflow' in content_str:
                return "workflow"
            elif '<SESSION' in content_str or '<Session' in content_str:
                return "session"
            elif '<WORKLET' in content_str or '<Worklet' in content_str:
                return "worklet"
        except Exception:
            pass
        
        return "unknown"
    
    def list_all_files(self) -> list:
        """List all uploaded files with metadata.
        
        Returns:
            List of file metadata dictionaries
        """
        return list(self.file_registry.values())
    
    def get_files_by_type(self, file_type: str) -> list:
        """Get all files of a specific type.
        
        Args:
            file_type: File type (mapping, workflow, session, worklet)
            
        Returns:
            List of file metadata dictionaries
        """
        return [f for f in self.file_registry.values() if f.get("file_type") == file_type]


# Global file manager instance
file_manager = FileManager()

