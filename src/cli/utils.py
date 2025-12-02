"""CLI Utilities — Progress indicators, formatting, etc."""
import sys
import json
from pathlib import Path
from typing import Any, Optional, Dict, List
from datetime import datetime

# Try to import progress libraries
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    tqdm = None

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.table import Table
    from rich.panel import Panel
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    Console = None
    Progress = None
    Table = None
    Panel = None

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Global console instance
_console = None


def get_console():
    """Get or create Rich console instance."""
    global _console
    if _console is None and HAS_RICH:
        _console = Console()
    return _console


class ProgressIndicator:
    """Progress indicator wrapper."""
    
    def __init__(self, total: int, description: str = "Processing", use_rich: bool = True):
        """Initialize progress indicator.
        
        Args:
            total: Total number of items
            description: Description text
            use_rich: Whether to use Rich library if available
        """
        self.total = total
        self.description = description
        self.use_rich = use_rich and HAS_RICH
        self.progress = None
        self.task_id = None
        
        if self.use_rich:
            console = get_console()
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console
            )
            self.progress.start()
            self.task_id = self.progress.add_task(description, total=total)
        elif HAS_TQDM:
            self.progress = tqdm(total=total, desc=description, unit="item")
        else:
            # Fallback: simple print
            self.progress = None
            print(f"{description}: 0/{total}")
    
    def update(self, n: int = 1):
        """Update progress.
        
        Args:
            n: Number of items completed
        """
        if self.use_rich and self.progress and self.task_id is not None:
            self.progress.update(self.task_id, advance=n)
        elif HAS_TQDM and self.progress:
            self.progress.update(n)
        else:
            # Fallback: simple print
            current = getattr(self, '_current', 0) + n
            self._current = current
            print(f"{self.description}: {current}/{self.total}")
    
    def close(self):
        """Close progress indicator."""
        if self.use_rich and self.progress:
            self.progress.stop()
        elif HAS_TQDM and self.progress:
            self.progress.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def format_error(error: Exception, include_traceback: bool = False) -> str:
    """Format error message for display.
    
    Args:
        error: Exception instance
        include_traceback: Whether to include traceback
    
    Returns:
        Formatted error message
    """
    if HAS_RICH:
        console = get_console()
        if include_traceback:
            return console.print_exception()
        else:
            return f"[red]Error:[/red] {str(error)}"
    else:
        if include_traceback:
            import traceback
            return traceback.format_exc()
        else:
            return f"Error: {str(error)}"


def format_output(data: Any, format_type: str = "json", indent: int = 2) -> str:
    """Format output data.
    
    Args:
        data: Data to format
        format_type: Output format (json, table, human)
        indent: JSON indentation
    
    Returns:
        Formatted string
    """
    if format_type == "json":
        return json.dumps(data, indent=indent, ensure_ascii=False, default=str)
    elif format_type == "table" and HAS_RICH:
        return format_table(data)
    else:
        return format_human_readable(data)


def format_table(data: List[Dict[str, Any]]) -> str:
    """Format data as Rich table.
    
    Args:
        data: List of dictionaries
    
    Returns:
        Formatted table string
    """
    if not HAS_RICH or not data:
        return format_human_readable(data)
    
    console = get_console()
    table = Table(show_header=True, header_style="bold magenta")
    
    # Get column names from first item
    if isinstance(data, list) and len(data) > 0:
        columns = list(data[0].keys())
        for col in columns:
            table.add_column(col)
        
        for row in data:
            table.add_row(*[str(row.get(col, "")) for col in columns])
        
        with console.capture() as capture:
            console.print(table)
        return capture.get()
    else:
        return format_human_readable(data)


def format_human_readable(data: Any) -> str:
    """Format data in human-readable format.
    
    Args:
        data: Data to format
    
    Returns:
        Formatted string
    """
    if isinstance(data, dict):
        lines = []
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{key}:")
                lines.append(format_human_readable(value))
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)
    elif isinstance(data, list):
        lines = []
        for i, item in enumerate(data, 1):
            lines.append(f"{i}. {format_human_readable(item)}")
        return "\n".join(lines)
    else:
        return str(data)


def print_success(message: str):
    """Print success message.
    
    Args:
        message: Success message
    """
    if HAS_RICH:
        console = get_console()
        console.print(f"[green]✓[/green] {message}")
    else:
        print(f"✓ {message}")


def print_error(message: str):
    """Print error message.
    
    Args:
        message: Error message
    """
    if HAS_RICH:
        console = get_console()
        console.print(f"[red]✗[/red] {message}")
    else:
        print(f"✗ {message}")


def print_warning(message: str):
    """Print warning message.
    
    Args:
        message: Warning message
    """
    if HAS_RICH:
        console = get_console()
        console.print(f"[yellow]⚠[/yellow] {message}")
    else:
        print(f"⚠ {message}")


def print_info(message: str):
    """Print info message.
    
    Args:
        message: Info message
    """
    if HAS_RICH:
        console = get_console()
        console.print(f"[blue]ℹ[/blue] {message}")
    else:
        print(f"ℹ {message}")

