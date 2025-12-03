"""Runtime Configuration Normalizer

Structures free-form configuration attributes into normalized runtime configuration schemas.
"""
from typing import Dict, Any, List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class RuntimeConfigNormalizer:
    """Normalizes runtime configuration from free-form attributes to structured schemas."""
    
    def normalize_task_config(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize task (session) runtime configuration.
        
        Args:
            attributes: Free-form attribute dictionary from parser
            
        Returns:
            Structured task_runtime_config dictionary
        """
        config = {
            "connection_pools": [],
            "buffer_size": None,
            "commit_interval": None,
            "error_handling": {},
            "performance_tuning": {},
            "source_options": {},
            "target_options": {},
            "transformation_options": {}
        }
        
        # Connection pool settings
        connection_keys = [k for k in attributes.keys() if 'CONNECTION' in k.upper() or 'POOL' in k.upper()]
        for key in connection_keys:
            config["connection_pools"].append({
                "name": key,
                "value": attributes.get(key)
            })
        
        # Buffer and commit settings
        if "BUFFER_SIZE" in attributes or "BUFFERSIZE" in attributes:
            config["buffer_size"] = self._parse_int(attributes.get("BUFFER_SIZE") or attributes.get("BUFFERSIZE"))
        
        if "COMMIT_INTERVAL" in attributes or "COMMITINTERVAL" in attributes:
            config["commit_interval"] = self._parse_int(attributes.get("COMMIT_INTERVAL") or attributes.get("COMMITINTERVAL"))
        
        # Error handling settings
        error_keys = [k for k in attributes.keys() if 'ERROR' in k.upper() or 'REJECT' in k.upper()]
        for key in error_keys:
            config["error_handling"][key.lower()] = attributes.get(key)
        
        # Performance tuning settings
        perf_keys = [k for k in attributes.keys() if any(term in k.upper() for term in ['THREAD', 'PARTITION', 'CACHE', 'SORT'])]
        for key in perf_keys:
            config["performance_tuning"][key.lower()] = attributes.get(key)
        
        # Source-specific options
        source_keys = [k for k in attributes.keys() if 'SOURCE' in k.upper()]
        for key in source_keys:
            if key not in connection_keys:
                config["source_options"][key.lower()] = attributes.get(key)
        
        # Target-specific options
        target_keys = [k for k in attributes.keys() if 'TARGET' in k.upper()]
        for key in target_keys:
            if key not in connection_keys:
                config["target_options"][key.lower()] = attributes.get(key)
        
        # Transformation-specific options
        trans_keys = [k for k in attributes.keys() if any(term in k.upper() for term in ['TRANSFORMATION', 'LOOKUP', 'AGGREGATOR'])]
        for key in trans_keys:
            config["transformation_options"][key.lower()] = attributes.get(key)
        
        # Store any remaining attributes in a catch-all
        all_processed_keys = set(connection_keys + error_keys + perf_keys + source_keys + target_keys + trans_keys)
        all_processed_keys.add("BUFFER_SIZE")
        all_processed_keys.add("BUFFERSIZE")
        all_processed_keys.add("COMMIT_INTERVAL")
        all_processed_keys.add("COMMITINTERVAL")
        
        remaining = {k: v for k, v in attributes.items() if k not in all_processed_keys}
        if remaining:
            config["other_attributes"] = remaining
        
        return config
    
    def normalize_workflow_config(self, attributes: Dict[str, Any], tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Normalize workflow runtime configuration.
        
        Args:
            attributes: Free-form attribute dictionary from parser
            tasks: List of tasks in the workflow
            
        Returns:
            Structured workflow_runtime_config dictionary
        """
        config = {
            "scheduling": {},
            "retry_policy": {},
            "notification": {},
            "variables": [],
            "parameter_file": None,
            "log_level": None
        }
        
        # Scheduling settings
        schedule_keys = [k for k in attributes.keys() if any(term in k.upper() for term in ['SCHEDULE', 'CRON', 'FREQUENCY', 'INTERVAL'])]
        for key in schedule_keys:
            config["scheduling"][key.lower()] = attributes.get(key)
        
        # Retry policy settings
        retry_keys = [k for k in attributes.keys() if 'RETRY' in k.upper()]
        for key in retry_keys:
            config["retry_policy"][key.lower()] = attributes.get(key)
        
        # Notification settings
        notify_keys = [k for k in attributes.keys() if any(term in k.upper() for term in ['NOTIFY', 'EMAIL', 'ALERT'])]
        for key in notify_keys:
            config["notification"][key.lower()] = attributes.get(key)
        
        # Variables (extract from tasks and attributes)
        variable_keys = [k for k in attributes.keys() if 'VARIABLE' in k.upper() or 'PARAM' in k.upper()]
        for key in variable_keys:
            config["variables"].append({
                "name": key,
                "value": attributes.get(key),
                "type": "workflow"  # vs "task" level
            })
        
        # Parameter file
        if "PARAMETERFILE" in attributes or "PARAMETER_FILE" in attributes:
            config["parameter_file"] = attributes.get("PARAMETERFILE") or attributes.get("PARAMETER_FILE")
        
        # Log level
        if "LOGLEVEL" in attributes or "LOG_LEVEL" in attributes:
            config["log_level"] = attributes.get("LOGLEVEL") or attributes.get("LOG_LEVEL")
        
        # Extract variables from task attributes
        for task in tasks:
            task_attrs = task.get("attributes", {})
            for key, value in task_attrs.items():
                if 'VARIABLE' in key.upper() or 'PARAM' in key.upper():
                    config["variables"].append({
                        "name": key,
                        "value": value,
                        "type": "task",
                        "task": task.get("name")
                    })
        
        # Store remaining attributes
        all_processed_keys = set(schedule_keys + retry_keys + notify_keys + variable_keys)
        all_processed_keys.add("PARAMETERFILE")
        all_processed_keys.add("PARAMETER_FILE")
        all_processed_keys.add("LOGLEVEL")
        all_processed_keys.add("LOG_LEVEL")
        
        remaining = {k: v for k, v in attributes.items() if k not in all_processed_keys}
        if remaining:
            config["other_attributes"] = remaining
        
        return config
    
    def _parse_int(self, value: Any) -> Optional[int]:
        """Parse integer value, returning None if not parseable."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

