"""
Progress display module using rich library.
Hiển thị progress bars và status trong terminal.
"""
import logging
from typing import Optional
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    MofNCompleteColumn
)
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

logger = logging.getLogger(__name__)

# Console instance cho rich output
console = Console()


class TranslationProgress:
    """
    Class quản lý hiển thị progress cho translation workflow.
    
    Attributes:
        progress: Rich Progress instance
        task_id: ID của main task
        patch_tasks: Dict mapping patch index -> task ID
    """
    
    def __init__(self, total_patches: int):
        """
        Initialize progress tracker.
        
        Args:
            total_patches: Tổng số patches cần dịch
        """
        self.total_patches = total_patches
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            console=console
        )
        self.task_id = None
        self.patch_tasks = {}
        self.live = None
    
    def start(self):
        """Bắt đầu hiển thị progress."""
        self.task_id = self.progress.add_task(
            "[cyan]Translating patches...",
            total=self.total_patches
        )
        self.live = Live(self.progress, console=console, refresh_per_second=4)
        self.live.start()
    
    def update(self, completed: int):
        """
        Cập nhật progress.
        
        Args:
            completed: Số patches đã hoàn thành
        """
        if self.task_id is not None:
            self.progress.update(self.task_id, completed=completed)
    
    def stop(self, success: bool = True):
        """
        Dừng progress display.
        
        Args:
            success: True nếu thành công, False nếu thất bại
        """
        if self.live:
            self.live.stop()
        
        if success:
            console.print("✅ [bold green]Translation completed successfully!")
        else:
            console.print("❌ [bold red]Translation failed!")
    
    def print_summary(self, stats: dict):
        """
        In summary table sau khi hoàn thành.
        
        Args:
            stats: Dictionary chứa thống kê
        """
        table = Table(title="Translation Summary", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        
        table.add_row("Total Entries", str(stats.get('total_entries', 0)))
        table.add_row("Total Patches", str(stats.get('total_patches', 0)))
        table.add_row("Successful Patches", str(stats.get('successful_patches', 0)))
        table.add_row("Failed Patches", str(stats.get('failed_patches', 0)))
        table.add_row("Execution Time", f"{stats.get('execution_time', 0):.2f}s")
        
        console.print(table)


def print_header(workflow_type: str, loc_filename: str):
    """
    In header cho application.
    
    Args:
        workflow_type: Loại workflow (sequence/full_parallel)
        loc_filename: Tên file localization
    """
    header = Text()
    header.append("🚀 ", style="bold red")
    header.append("AI Agent Vietnamese Translator\n", style="bold cyan")
    header.append(f"   Workflow: {workflow_type}\n", style="yellow")
    header.append(f"   File: {loc_filename}\n", style="yellow")
    
    panel = Panel(header, border_style="blue", padding=(1, 2))
    console.print(panel)


def print_error(message: str):
    """
    In error message.
    
    Args:
        message: Error message
    """
    console.print(f"❌ [bold red]Error: {message}")


def print_success(message: str):
    """
    In success message.
    
    Args:
        message: Success message
    """
    console.print(f"✅ [bold green]{message}")


def print_warning(message: str):
    """
    In warning message.
    
    Args:
        message: Warning message
    """
    console.print(f"⚠️  [bold yellow]{message}")


def print_info(message: str):
    """
    In info message.
    
    Args:
        message: Info message
    """
    console.print(f"ℹ️  [bold blue]{message}")
