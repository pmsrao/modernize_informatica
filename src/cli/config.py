"""CLI Configuration Management."""
import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(project_root / "src") not in sys.path:
    sys.path.insert(0, str(project_root / "src"))

try:
    import yaml
except ImportError:
    yaml = None

from cli.errors import ConfigurationError
from utils.logger import get_logger

logger = get_logger(__name__)


class Config:
    """CLI configuration manager."""
    
    DEFAULT_CONFIG_PATH = Path.home() / ".informatica-modernize" / "config.yaml"
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = Path(config_path) if config_path else self.DEFAULT_CONFIG_PATH
        self.config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file or environment variables."""
        # Start with defaults
        self.config = {
            "neo4j": {
                "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                "user": os.getenv("NEO4J_USER", "neo4j"),
                "password": os.getenv("NEO4J_PASSWORD", "password")
            },
            "staging": {
                "dir": os.getenv("STAGING_DIR", "test_log/staging")
            },
            "output": {
                "dir": os.getenv("OUTPUT_DIR", "test_log"),
                "generated_dir": os.getenv("GENERATED_DIR", "test_log/generated")
            },
            "api": {
                "url": os.getenv("API_URL", "http://localhost:8000")
            },
            "llm": {
                "provider": os.getenv("LLM_PROVIDER", "openai"),
                "api_key": os.getenv("OPENAI_API_KEY", os.getenv("AZURE_OPENAI_KEY", ""))
            }
        }
        
        # Load from file if it exists
        if self.config_path.exists():
            try:
                file_config = self._load_config_file(self.config_path)
                # Merge file config with defaults (file takes precedence)
                self._merge_config(self.config, file_config)
                logger.info(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config file {self.config_path}: {str(e)}")
        
        # Environment variables override everything
        self._apply_env_overrides()
    
    def _load_config_file(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from file.
        
        Args:
            config_path: Path to configuration file
        
        Returns:
            Configuration dictionary
        
        Raises:
            ConfigurationError: If file cannot be loaded
        """
        suffix = config_path.suffix.lower()
        
        if suffix == ".yaml" or suffix == ".yml":
            if yaml is None:
                raise ConfigurationError(
                    "PyYAML not installed. Install with: pip install pyyaml"
                )
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        elif suffix == ".json":
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            raise ConfigurationError(
                f"Unsupported config file format: {suffix}. Use .yaml, .yml, or .json"
            )
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]):
        """Recursively merge configuration dictionaries.
        
        Args:
            base: Base configuration
            override: Configuration to merge in
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides."""
        # Neo4j settings
        if os.getenv("NEO4J_URI"):
            self.config["neo4j"]["uri"] = os.getenv("NEO4J_URI")
        if os.getenv("NEO4J_USER"):
            self.config["neo4j"]["user"] = os.getenv("NEO4J_USER")
        if os.getenv("NEO4J_PASSWORD"):
            self.config["neo4j"]["password"] = os.getenv("NEO4J_PASSWORD")
        
        # Staging directory
        if os.getenv("STAGING_DIR"):
            self.config["staging"]["dir"] = os.getenv("STAGING_DIR")
        
        # Output directories
        if os.getenv("OUTPUT_DIR"):
            self.config["output"]["dir"] = os.getenv("OUTPUT_DIR")
        if os.getenv("GENERATED_DIR"):
            self.config["output"]["generated_dir"] = os.getenv("GENERATED_DIR")
        
        # API URL
        if os.getenv("API_URL"):
            self.config["api"]["url"] = os.getenv("API_URL")
        
        # LLM settings
        if os.getenv("LLM_PROVIDER"):
            self.config["llm"]["provider"] = os.getenv("LLM_PROVIDER")
        if os.getenv("OPENAI_API_KEY"):
            self.config["llm"]["api_key"] = os.getenv("OPENAI_API_KEY")
        elif os.getenv("AZURE_OPENAI_KEY"):
            self.config["llm"]["api_key"] = os.getenv("AZURE_OPENAI_KEY")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated key.
        
        Args:
            key: Dot-separated key (e.g., "neo4j.uri")
            default: Default value if key not found
        
        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def validate(self) -> bool:
        """Validate configuration.
        
        Returns:
            True if valid
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Validate Neo4j settings
        if not self.config.get("neo4j", {}).get("uri"):
            raise ConfigurationError("Neo4j URI is required")
        
        # Validate output directories exist or can be created
        output_dir = self.config.get("output", {}).get("dir")
        if output_dir:
            try:
                Path(output_dir).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ConfigurationError(f"Cannot create output directory {output_dir}: {str(e)}")
        
        return True
    
    def save(self, output_path: Optional[str] = None):
        """Save configuration to file.
        
        Args:
            output_path: Optional output path (defaults to config_path)
        """
        save_path = Path(output_path) if output_path else self.config_path
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        suffix = save_path.suffix.lower()
        
        if suffix == ".yaml" or suffix == ".yml":
            if yaml is None:
                raise ConfigurationError("PyYAML not installed")
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
        elif suffix == ".json":
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        else:
            raise ConfigurationError(f"Unsupported config file format: {suffix}")

