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
        # Convert to tasks format for consistent processing
        if "tasks" in workflow_structure:
            tasks = workflow_structure.get("tasks", [])
        elif "sessions" in workflow_structure:
            # Convert sessions to tasks format
            tasks = []
            for session in workflow_structure.get("sessions", []):
                tasks.append({
                    "name": session.get("name", ""),
                    "type": session.get("type", "Session"),
                    "mappings": session.get("mappings", [])
                })
        else:
            tasks = []
        
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
            "from airflow.operators.email import EmailOperator",
            "from airflow.operators.empty import EmptyOperator",
            "from airflow.sensors.filesystem import FileSensor",
            "from airflow.sensors.python import PythonSensor",
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
            "# Tasks",
        ]
        
        # Generate tasks for each task in workflow
        task_ids = []
        for task in tasks:
            task_name = task.get("name", "unknown_task")
            task_type = task.get("type", "TASK")
            task_id = self._sanitize_task_id(task_name)
            task_ids.append(task_id)
            
            # Generate task based on type
            if task_type == "Session":
                lines.extend(self._generate_session_task(task, task_id))
            elif task_type == "Worklet":
                lines.extend(self._generate_worklet_task(task, task_id))
            elif task_type == "Command":
                lines.extend(self._generate_command_task(task, task_id))
            elif task_type == "Email":
                lines.extend(self._generate_email_task(task, task_id))
            elif task_type == "Timer":
                lines.extend(self._generate_timer_task(task, task_id))
            elif task_type == "Decision":
                lines.extend(self._generate_decision_task(task, task_id))
            elif task_type in ["Event-Wait", "Event-Raise"]:
                lines.extend(self._generate_event_task(task, task_id))
            elif task_type == "Assignment":
                lines.extend(self._generate_assignment_task(task, task_id))
            elif task_type == "Control":
                lines.extend(self._generate_control_task(task, task_id))
            else:
                # Unknown task type - create placeholder
                lines.extend([
                    f"# Unknown task type: {task_type}",
                    f"{task_id} = EmptyOperator(",
                    f'    task_id="{task_id}",',
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
    
    def _generate_session_task(self, task: Dict[str, Any], task_id: str) -> List[str]:
        """Generate Airflow task for Session."""
        task_name = task.get("name", "")
        # Handle both mappings and transformations keys
        mappings = task.get("mappings", []) or task.get("transformations", [])
        
        # If mappings is a list of strings, convert to list of dicts
        if mappings and isinstance(mappings[0], str):
            mappings = [{"name": m} for m in mappings]
        
        if len(mappings) > 1:
            lines = [
                f"# Session: {task_name}",
                f"from airflow.utils.task_group import TaskGroup",
                "",
                f"with TaskGroup('{task_id}_group') as {task_id}_group:",
            ]
            for mapping in mappings:
                mapping_name = mapping.get("transformation_name") or mapping.get("name", "unknown_transformation")
                mapping_id = self._sanitize_task_id(mapping_name)
                lines.extend([
                    f"    {mapping_id} = DatabricksSubmitRunOperator(",
                    f'        task_id="{mapping_id}",',
                    f'        databricks_conn_id="databricks_default",',
                    f'        notebook_task={{',
                    f'            "notebook_path": "/transformations/{mapping_name.lower()}"',
                    f'        }},',
                    f'        dag=dag,',
                    f"    )",
                    "",
                ])
            return lines
        else:
            mapping = mappings[0] if mappings else {}
            mapping_name = mapping.get("transformation_name") or mapping.get("name", "unknown_transformation")
            return [
                f"# Session: {task_name}",
                f"{task_id} = DatabricksSubmitRunOperator(",
                f'    task_id="{task_id}",',
                f'    databricks_conn_id="databricks_default",',
                f'    notebook_task={{',
                f'        "notebook_path": "/mappings/{mapping_name.lower()}"',
                f'    }},',
                f'    dag=dag,',
                f")",
                "",
            ]
    
    def _generate_worklet_task(self, task: Dict[str, Any], task_id: str) -> List[str]:
        """Generate Airflow task for Worklet."""
        worklet_name = task.get("worklet_name", task.get("name", ""))
        return [
            f"# Worklet: {worklet_name}",
            f"# Worklets are expanded inline - tasks from worklet should be generated separately",
            f"{task_id} = EmptyOperator(",
            f'    task_id="{task_id}",',
            f'    dag=dag,',
            f")",
            "",
        ]
    
    def _generate_command_task(self, task: Dict[str, Any], task_id: str) -> List[str]:
        """Generate Airflow task for Command."""
        command = task.get("command", "")
        working_directory = task.get("working_directory", "")
        return [
            f"# Command Task: {task.get('name', '')}",
            f"{task_id} = BashOperator(",
            f'    task_id="{task_id}",',
            f'    bash_command="{command}",',
            f'    cwd="{working_directory}" if "{working_directory}" else None,',
            f'    dag=dag,',
            f")",
            "",
        ]
    
    def _generate_email_task(self, task: Dict[str, Any], task_id: str) -> List[str]:
        """Generate Airflow task for Email."""
        recipients = task.get("recipients", [])
        subject = task.get("subject", "")
        body = task.get("body", "")
        return [
            f"# Email Task: {task.get('name', '')}",
            f"{task_id} = EmailOperator(",
            f'    task_id="{task_id}",',
            f'    to={recipients},',
            f'    subject="{subject}",',
            f'    html_content="{body}",',
            f'    dag=dag,',
            f")",
            "",
        ]
    
    def _generate_timer_task(self, task: Dict[str, Any], task_id: str) -> List[str]:
        """Generate Airflow task for Timer."""
        wait_type = task.get("wait_type", "Duration")
        wait_value = task.get("wait_value", "0")
        
        if wait_type == "File":
            file_path = task.get("file_path", "")
            return [
                f"# Timer Task (File Wait): {task.get('name', '')}",
                f"{task_id} = FileSensor(",
                f'    task_id="{task_id}",',
                f'    filepath="{file_path}",',
                f'    dag=dag,',
                f")",
                "",
            ]
        elif wait_type == "Event":
            # Use PythonSensor for event wait
            event_name = task.get("event_name", "")
            return [
                f"# Timer Task (Event Wait): {task.get('name', '')}",
                f"def wait_for_event():",
                f"    # TODO: Implement event wait logic for {event_name}",
                f"    return True",
                f"",
                f"{task_id} = PythonSensor(",
                f'    task_id="{task_id}",',
                f'    python_callable=wait_for_event,',
                f'    dag=dag,',
                f")",
                "",
            ]
        else:
            # Duration wait - use time.sleep in PythonOperator
            try:
                wait_seconds = int(wait_value)
            except (ValueError, TypeError):
                wait_seconds = 0
            return [
                f"# Timer Task (Duration): {task.get('name', '')}",
                f"import time",
                f"",
                f"def wait_duration():",
                f"    time.sleep({wait_seconds})",
                f"",
                f"{task_id} = PythonOperator(",
                f'    task_id="{task_id}",',
                f'    python_callable=wait_duration,',
                f'    dag=dag,',
                f")",
                "",
            ]
    
    def _generate_decision_task(self, task: Dict[str, Any], task_id: str) -> List[str]:
        """Generate Airflow task for Decision."""
        condition = task.get("condition", "")
        branches = task.get("branches", [])
        return [
            f"# Decision Task: {task.get('name', '')}",
            f"# Condition: {condition}",
            f"# Decision tasks require branching logic - using EmptyOperator as placeholder",
            f"{task_id} = EmptyOperator(",
            f'    task_id="{task_id}",',
            f'    dag=dag,',
            f")",
            f"# TODO: Implement decision branching logic with BranchPythonOperator",
            "",
        ]
    
    def _generate_event_task(self, task: Dict[str, Any], task_id: str) -> List[str]:
        """Generate Airflow task for Event (Wait or Raise)."""
        event_type = task.get("event_type", "WAIT")
        event_name = task.get("event_name", "")
        
        if event_type == "WAIT":
            return [
                f"# Event Wait Task: {task.get('name', '')}",
                f"def wait_for_event():",
                f"    # TODO: Implement event wait logic for {event_name}",
                f"    return True",
                f"",
                f"{task_id} = PythonSensor(",
                f'    task_id="{task_id}",',
                f'    python_callable=wait_for_event,',
                f'    dag=dag,',
                f")",
                "",
            ]
        else:  # RAISE
            return [
                f"# Event Raise Task: {task.get('name', '')}",
                f"def raise_event():",
                f"    # TODO: Implement event raise logic for {event_name}",
                f"    pass",
                f"",
                f"{task_id} = PythonOperator(",
                f'    task_id="{task_id}",',
                f'    python_callable=raise_event,',
                f'    dag=dag,',
                f")",
                "",
            ]
    
    def _generate_assignment_task(self, task: Dict[str, Any], task_id: str) -> List[str]:
        """Generate Airflow task for Assignment."""
        assignments = task.get("assignments", [])
        return [
            f"# Assignment Task: {task.get('name', '')}",
            f"def assign_variables(**context):",
            f"    # Assign variables",
        ] + [
            f"    context['ti'].xcom_push(key='{a.get('variable', '')}', value='{a.get('value', '')}')"
            for a in assignments
        ] + [
            f"",
            f"{task_id} = PythonOperator(",
            f'    task_id="{task_id}",',
            f'    python_callable=assign_variables,',
            f'    dag=dag,',
            f")",
            "",
        ]
    
    def _generate_control_task(self, task: Dict[str, Any], task_id: str) -> List[str]:
        """Generate Airflow task for Control (Abort/Stop)."""
        control_type = task.get("control_type", "CONTROL")
        error_message = task.get("error_message", "")
        
        if control_type == "ABORT":
            return [
                f"# Control Task (Abort): {task.get('name', '')}",
                f"def abort_workflow(**context):",
                f"    raise Exception('Workflow aborted: {error_message}')",
                f"",
                f"{task_id} = PythonOperator(",
                f'    task_id="{task_id}",',
                f'    python_callable=abort_workflow,',
                f'    dag=dag,',
                f")",
                "",
            ]
        else:  # STOP
            return [
                f"# Control Task (Stop): {task.get('name', '')}",
                f"# Stop tasks typically skip remaining tasks",
                f"{task_id} = EmptyOperator(",
                f'    task_id="{task_id}",',
                f'    dag=dag,',
                f")",
                f"# TODO: Implement stop logic to skip downstream tasks",
                "",
            ]
    
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
        # Convert to tasks format for consistent processing
        if "tasks" in workflow_structure:
            tasks = workflow_structure.get("tasks", [])
        elif "sessions" in workflow_structure:
            # Legacy format - convert sessions to tasks
            tasks = []
            for session in workflow_structure.get("sessions", []):
                tasks.append({
                    "name": session.get("name", ""),
                    "type": "Session",
                    "mappings": session.get("mappings", [])
                })
        else:
            tasks = []
        
        # Default schedule
        if schedule is None:
            schedule = {
                "quartz_cron_expression": "0 0 0 * * ?",  # Daily at midnight
                "timezone_id": "UTC"
            }
        
        task_dependencies = []
        
        for idx, task in enumerate(tasks):
            task_name = task.get("name", "unknown_task")
            task_id = self._sanitize_task_id(task_name)
            
            # Get mappings/transformations from task
            mappings = task.get("mappings", []) or task.get("transformations", [])
            
            # Create task for each mapping
            for mapping in mappings:
                mapping_name = mapping.get("transformation_name") or mapping.get("name", "unknown_transformation")
                mapping_id = self._sanitize_task_id(mapping_name)
                
                task_def = {
                    "task_key": mapping_id,
                    "description": f"Migrated from Informatica task: {task_name}, transformation: {mapping_name}",
                    "notebook_task": {
                        "notebook_path": f"/transformations/{mapping_name.lower()}",
                        "base_parameters": {}
                    },
                    "timeout_seconds": 3600,
                    "max_retries": 1,
                    "min_retry_interval_millis": 60000
                }
                
                tasks.append(task_def)
                
                # Add dependencies from workflow links if available
                links = workflow_structure.get("links", [])
                if links:
                    # Find dependencies for this task
                    task_deps = []
                    for link in links:
                        if link.get("to") == mapping_name or link.get("to") == task_name:
                            from_task = link.get("from", "")
                            from_task_id = self._sanitize_task_id(from_task)
                            # Find corresponding mapping for the from_task
                            for prev_idx, prev_task in enumerate(tasks):
                                prev_mappings = prev_task.get("mappings", []) or prev_task.get("transformations", [])
                                if prev_mappings and (prev_task.get("name") == from_task or prev_task.get("name") == from_task):
                                    prev_mapping_id = self._sanitize_task_id(prev_mappings[0].get("name", ""))
                                    task_deps.append({"task_key": prev_mapping_id})
                                    break
                    
                    if task_deps:
                        task_def["depends_on"] = task_deps
                elif idx > 0:
                    # Fallback: sequential execution
                    prev_task = tasks[idx - 1]
                    prev_mappings = prev_task.get("mappings", []) or prev_task.get("transformations", [])
                    if prev_mappings:
                        prev_mapping_id = self._sanitize_task_id(prev_mappings[0].get("name", ""))
                        task_def["depends_on"] = [{"task_key": prev_mapping_id}]
        
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
        
        # Handle both formats: sessions/mappings or tasks/transformations
        if "tasks" in workflow_structure:
            tasks = workflow_structure.get("tasks", [])
        elif "sessions" in workflow_structure:
            tasks = workflow_structure.get("sessions", [])
        else:
            tasks = []
        
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
        
        # Generate tasks for each task/session
        for task in tasks:
            task_name = task.get("name", "unknown_task")
            mappings = task.get("mappings", []) or task.get("transformations", [])
            
            for mapping in mappings:
                mapping_name = mapping.get("name", "unknown_mapping")
                mapping_id = self._sanitize_function_name(mapping_name)
                
                lines.extend([
                    f"    # Task: {task_name}, Mapping: {mapping_name}",
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
        
        # Handle both formats: sessions/mappings or tasks/transformations
        if "tasks" in workflow_structure:
            tasks = workflow_structure.get("tasks", [])
        elif "sessions" in workflow_structure:
            tasks = workflow_structure.get("sessions", [])
        else:
            tasks = []
        
        lines = [
            f"# Workflow: {workflow_name}",
            "",
            "## Overview",
            "",
            f"This workflow was migrated from Informatica and contains {len(tasks)} task(s).",
            "",
            "## Tasks",
            "",
        ]
        
        for task in tasks:
            task_name = task.get("name", "unknown_task")
            mappings = task.get("mappings", []) or task.get("transformations", [])
            
            lines.extend([
                f"### {task_name}",
                "",
                f"**Mappings/Transformations:** {len(mappings)}",
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

