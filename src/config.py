"""Configuration management using environment variables and Pydantic Settings."""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from src.utils.exceptions import ConfigurationError


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    api_title: str = "Informatica Modernization Accelerator API"
    api_version: str = "0.1.0"
    
    # LLM Configuration
    llm_provider: str = "openai"  # Options: openai, azure, local
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    azure_openai_endpoint: Optional[str] = None
    azure_openai_key: Optional[str] = None
    azure_openai_deployment: Optional[str] = None
    local_llm_path: Optional[str] = None
    vllm_server_url: Optional[str] = None
    ollama_url: Optional[str] = None
    ollama_model: str = "llama3"
    
    # Databricks Configuration
    databricks_host: Optional[str] = None
    databricks_token: Optional[str] = None
    databricks_workspace_path: Optional[str] = None
    
    # Storage Configuration
    upload_dir: str = "./uploads"
    max_upload_size: int = 100 * 1024 * 1024  # 100MB
    allowed_file_extensions: list = [".xml"]
    
    # Logging Configuration
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    log_file: Optional[str] = None  # If None, logs to console only
    log_format: str = "json"  # json or text
    
    # Version Store Configuration
    version_store_path: str = "./versions"
    
    # Neo4j Configuration
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "password")
    enable_graph_store: bool = os.getenv("ENABLE_GRAPH_STORE", "false").lower() == "true"
    graph_first: bool = os.getenv("GRAPH_FIRST", "false").lower() == "true"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"
    
    def validate(self):
        """Validate configuration settings."""
        errors = []
        
        # Validate LLM provider settings
        if self.llm_provider == "openai" and not self.openai_api_key:
            errors.append("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        
        if self.llm_provider == "azure":
            if not self.azure_openai_endpoint:
                errors.append("AZURE_OPENAI_ENDPOINT is required when LLM_PROVIDER=azure")
            if not self.azure_openai_key:
                errors.append("AZURE_OPENAI_KEY is required when LLM_PROVIDER=azure")
        
        if self.llm_provider == "local" and not self.local_llm_path:
            errors.append("LOCAL_LLM_PATH is required when LLM_PROVIDER=local")
        
        if errors:
            raise ConfigurationError(
                f"Configuration validation failed: {'; '.join(errors)}"
            )
        
        # Create directories if they don't exist
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.version_store_path, exist_ok=True)
        
        return True


# Global settings instance
settings = Settings()

# Validate on import (optional - can be deferred)
try:
    settings.validate()
except ConfigurationError:
    # Allow import even if validation fails (for CLI tools that might set env vars later)
    pass

