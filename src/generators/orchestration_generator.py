"""Orchestration Generator - Generates workflow orchestration code.

This generator creates platform-specific orchestration code from Informatica
workflow structures, including Airflow DAGs, Databricks Workflows, and Prefect Flows.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from utils.logger import get_logger

logger = get_logger(__name__)


class OrchestrationGenerator:
    """Generates orchestration code for workflows."""
    
    def __init__(self):
        """Initialize orchestration generator."""
        pass
    
    def generate_airflow_dag(self, workflow_structure: Dict[str, Any], 
                             schedule: Optional[str] = None,
                             default_args: Optional[Dict[str, Any]] = None) -> str:
        """Generate Airflow DAG from workflow structure.
        
        Args:
            workflow_structure: Workflow structure from graph queries or parsed files
            schedule: Cron expression for schedule (e.g., "0 0 * * *")
            default_args: Default arguments for DAG
            
        Returns:
            Python code for Airflow DAG
        """
        workflow_name = workflow_structure.get("name", "unknown_workflow")
        
        # Handle both formats: sessions/mappings or tasks/links
        if "sessions" in workflow_structure:
            sessions = workflow_structure.get("sessions", [])
        elif "tasks" in workflow_structure:
            # Convert tasks to sessions format (simplified)
            sessions = []
            for task in workflow_structure.get("tasks", []):
                sessions.append({
                    "name": task.get("name", ""),
                    "type": task.get("type", "TASK"),
                    "mappings": []  # Would need to be populated from session files
                })
        else:
            sessions = []
        
        # Default arguments
        if default_args is None:
            default_args = {
                "owner": "data_engineering",
                "depends_on_past": False,
                "email_on_failure": True,
                "email_on_retry": False,
                "retries": 1,
                "retry_delay": timedelta(minutes=5)
            }
        
        # Default schedule
        if schedule is None:
            schedule = "0 0 * * *"  # Daily at midnight
        
        lines = [
            "from airflow import DAG",
            "from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator",
            "from airflow.operators.bash import BashOperator",
            "from airflow.operators.python import PythonOperator",
            "from datetime import datetime, timedelta",
            "",
            "",
            f"# DAG for Informatica Workflow: {workflow_name}",
            f"# Generated from canonical model",
            "",
            f"default_args = {self._format_dict(default_args)}",
            "",
            f"dag = DAG(",
            f'    "{workflow_name}",',
            f'    default_args=default_args,',
            f'    description="Migrated from Informatica workflow: {workflow_name}",',
            f'    schedule_interval="{schedule}",',
            f'    start_date=datetime(2024, 1, 1),',
            f'    catchup=False,',
            f'    tags=["informatica_migration", "etl"],',
            f")",
            "",
            "# Tasks for sessions",
        ]
        
        # Generate tasks for each session
        task_ids = []
        for session in sessions:
            session_name = session.get("name", "unknown_session")
            session_id = self._sanitize_task_id(session_name)
            task_ids.append(session_id)
            
            mappings = session.get("mappings", [])
            
            # If session has multiple mappings, create a task group
            if len(mappings) > 1:
                lines.extend([
                    f"# Session: {session_name}",
                    f"from airflow.utils.task_group import TaskGroup",
                    "",
                    f"with TaskGroup('{session_id}_group') as {session_id}_group:",
                ])
                
                for mapping in mappings:
                    mapping_name = mapping.get("name", "unknown_mapping")
                    mapping_id = self._sanitize_task_id(mapping_name)
                    
                    lines.extend([
                        f"    {mapping_id} = DatabricksSubmitRunOperator(",
                        f'        task_id="{mapping_id}",',
                        f'        databricks_conn_id="databricks_default",',
                        f'        notebook_task={{',
                        f'            "notebook_path": "/mappings/{mapping_name.lower()}"',
                        f'        }},',
                        f'        dag=dag,',
                        f"    )",
                        "",
                    ])
            else:
                # Single mapping in session
                mapping = mappings[0] if mappings else {}
                mapping_name = mapping.get("name", "unknown_mapping")
                
                lines.extend([
                    f"# Session: {session_name}",
                    f"{session_id} = DatabricksSubmitRunOperator(",
                    f'    task_id="{session_id}",',
                    f'    databricks_conn_id="databricks_default",',
                    f'    notebook_task={{',
                    f'        "notebook_path": "/mappings/{mapping_name.lower()}"',
                    f'    }},',
                    f'    dag=dag,',
                    f")",
                    "",
                ])
        
        # Add dependencies from workflow links if available
        links = workflow_structure.get("links", [])
        if links:
            lines.append("")
            lines.append("# Dependencies (from workflow links)")
            # Build dependency map from links
            dependencies = {}
            for link in links:
                from_task = self._sanitize_task_id(link.get("from", ""))
                to_task = self._sanitize_task_id(link.get("to", ""))
                if from_task in task_ids and to_task in task_ids:
                    if to_task not in dependencies:
                        dependencies[to_task] = []
                    dependencies[to_task].append(from_task)
            
            # Generate dependency expressions
            for to_task, from_tasks in dependencies.items():
                if from_tasks:
                    from_expr = " >> ".join(from_tasks) if len(from_tasks) == 1 else f"({', '.join(from_tasks)})"
                    lines.append(f"{from_expr} >> {to_task}")
        elif len(task_ids) > 1:
            # Fallback: sequential execution
            lines.append("")
            lines.append("# Dependencies (sequential)")
            for i in range(len(task_ids) - 1):
                lines.append(f"{task_ids[i]} >> {task_ids[i+1]}")
        
        return "\n".join(lines)
    
    def generate_databricks_workflow(self, workflow_structure: Dict[str, Any],
                                    schedule: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate Databricks Workflow JSON from workflow structure.
        
        Args:
            workflow_structure: Workflow structure from graph queries or parsed files
            schedule: Schedule configuration
            
        Returns:
            Databricks Workflow JSON structure
        """
        workflow_name = workflow_structure.get("name", "unknown_workflow")
        
        # Handle both formats: sessions/mappings or tasks/links
        if "sessions" in workflow_structure:
            sessions = workflow_structure.get("sessions", [])
        elif "tasks" in workflow_structure:
            # Convert tasks to sessions format (simplified)
            sessions = []
            for task in workflow_structure.get("tasks", []):
                sessions.append({
                    "name": task.get("name", ""),
                    "type": task.get("type", "TASK"),
                    "mappings": []  # Would need to be populated from session files
                })
        else:
            sessions = []
        
        # Default schedule
        if schedule is None:
            schedule = {
                "quartz_cron_expression": "0 0 0 * * ?",  # Daily at midnight
                "timezone_id": "UTC"
            }
        
        tasks = []
        task_dependencies = []
        
        for idx, session in enumerate(sessions):
            session_name = session.get("name", "unknown_session")
            session_id = self._sanitize_task_id(session_name)
            
            mappings = session.get("mappings", [])
            
            # Create task for each mapping
            for mapping in mappings:
                mapping_name = mapping.get("name", "unknown_mapping")
                mapping_id = self._sanitize_task_id(mapping_name)
                
                task = {
                    "task_key": mapping_id,
                    "description": f"Migrated from Informatica session: {session_name}, mapping: {mapping_name}",
                    "notebook_task": {
                        "notebook_path": f"/mappings/{mapping_name.lower()}",
                        "base_parameters": {}
                    },
                    "timeout_seconds": 3600,
                    "max_retries": 1,
                    "min_retry_interval_millis": 60000
                }
                
                tasks.append(task)
                
                # Add dependencies from workflow links if available
                links = workflow_structure.get("links", [])
                if links:
                    # Find dependencies for this task
                    task_deps = []
                    for link in links:
                        if link.get("to") == mapping_name:
                            from_task = link.get("from", "")
                            from_task_id = self._sanitize_task_id(from_task)
                            # Find corresponding mapping for the from_task
                            for prev_idx, prev_session in enumerate(sessions):
                                prev_mappings = prev_session.get("mappings", [])
                                if prev_mappings and prev_session.get("name") == from_task:
                                    prev_mapping_id = self._sanitize_task_id(prev_mappings[0].get("name", ""))
                                    task_deps.append({"task_key": prev_mapping_id})
                                    break
                    
                    if task_deps:
                        task["depends_on"] = task_deps
                elif idx > 0:
                    # Fallback: sequential execution
                    prev_mapping = sessions[idx - 1].get("mappings", [])
                    if prev_mapping:
                        prev_mapping_id = self._sanitize_task_id(prev_mapping[0].get("name", ""))
                        task["depends_on"] = [{"task_key": prev_mapping_id}]
        
        workflow = {
            "name": workflow_name,
            "email_notifications": {
                "on_failure": ["data-engineering@example.com"],
                "on_success": [],
                "no_alert_for_skipped_runs": False
            },
            "timeout_seconds": 0,
            "schedule": schedule,
            "max_concurrent_runs": 1,
            "tasks": tasks,
            "format": "MULTI_TASK",
            "access_control_list": [
                {
                    "user_name": "data-engineering@example.com",
                    "permission_level": "CAN_MANAGE"
                }
            ]
        }
        
        return workflow
    
    def generate_prefect_flow(self, workflow_structure: Dict[str, Any]) -> str:
        """Generate Prefect Flow code from workflow structure.
        
        Args:
            workflow_structure: Workflow structure from graph queries
            
        Returns:
            Python code for Prefect Flow
        """
        workflow_name = workflow_structure.get("name", "unknown_workflow")
        sessions = workflow_structure.get("sessions", [])
        
        lines = [
            "from prefect import flow, task",
            "from prefect_databricks import DatabricksJobRun",
            "from prefect_databricks.credentials import DatabricksCredentials",
            "",
            "",
            f"# Prefect Flow for Informatica Workflow: {workflow_name}",
            f"# Generated from canonical model",
            "",
            "@task",
            "def run_databricks_notebook(notebook_path: str):",
            '    """Run a Databricks notebook."""',
            "    # Implementation depends on your Databricks setup",
            "    pass",
            "",
            "",
            f"@flow(name='{workflow_name}')",
            f"def {self._sanitize_function_name(workflow_name)}():",
            f'    """Prefect flow for workflow: {workflow_name}"""',
            "",
        ]
        
        # Generate tasks for each session
        for session in sessions:
            session_name = session.get("name", "unknown_session")
            mappings = session.get("mappings", [])
            
            for mapping in mappings:
                mapping_name = mapping.get("name", "unknown_mapping")
                mapping_id = self._sanitize_function_name(mapping_name)
                
                lines.extend([
                    f"    # Session: {session_name}, Mapping: {mapping_name}",
                    f'    run_databricks_notebook("/mappings/{mapping_name.lower()}")',
                    "",
                ])
        
        return "\n".join(lines)
    
    def generate_workflow_documentation(self, workflow_structure: Dict[str, Any]) -> str:
        """Generate Markdown documentation for workflow.
        
        Args:
            workflow_structure: Workflow structure from graph queries
            
        Returns:
            Markdown documentation
        """
        workflow_name = workflow_structure.get("name", "unknown_workflow")
        sessions = workflow_structure.get("sessions", [])
        
        lines = [
            f"# Workflow: {workflow_name}",
            "",
            "## Overview",
            "",
            f"This workflow was migrated from Informatica and contains {len(sessions)} session(s).",
            "",
            "## Sessions",
            "",
        ]
        
        for session in sessions:
            session_name = session.get("name", "unknown_session")
            mappings = session.get("mappings", [])
            
            lines.extend([
                f"### {session_name}",
                "",
                f"**Mappings:** {len(mappings)}",
                "",
            ])
            
            for mapping in mappings:
                mapping_name = mapping.get("name", "unknown_mapping")
                complexity = mapping.get("complexity", "UNKNOWN")
                
                lines.extend([
                    f"- **{mapping_name}** (Complexity: {complexity})",
                    "",
                ])
        
        lines.extend([
            "## Generated Code",
            "",
            "The following orchestration code has been generated:",
            "",
            "- `airflow_dag.py` - Airflow DAG definition",
            "- `databricks_workflow.json` - Databricks Workflow configuration",
            "- `prefect_flow.py` - Prefect Flow definition (optional)",
            "",
            "## Migration Notes",
            "",
            "- Review and adjust schedule as needed",
            "- Update connection IDs and credentials",
            "- Test each session independently before full workflow execution",
            "- Monitor first few runs for performance issues",
            "",
        ])
        
        return "\n".join(lines)
    
    def _sanitize_task_id(self, name: str) -> str:
        """Sanitize name for use as task ID."""
        # Remove special characters, replace spaces with underscores
        sanitized = name.replace(" ", "_").replace("-", "_")
        sanitized = "".join(c for c in sanitized if c.isalnum() or c == "_")
        return sanitized.lower()
    
    def _sanitize_function_name(self, name: str) -> str:
        """Sanitize name for use as function name."""
        return self._sanitize_task_id(name)
    
    def _format_dict(self, d: Dict[str, Any], indent: int = 0) -> str:
        """Format dictionary for Python code."""
        if not d:
            return "{}"
        
        lines = ["{"]
        for key, value in d.items():
            if isinstance(value, str):
                lines.append(f'    "{key}": "{value}",')
            elif isinstance(value, (int, float, bool)):
                lines.append(f"    \"{key}\": {value},")
            elif isinstance(value, dict):
                lines.append(f'    "{key}": {self._format_dict(value, indent + 1)},')
            else:
                lines.append(f'    "{key}": {repr(value)},')
        lines.append("}")
        return "\n".join(lines)

