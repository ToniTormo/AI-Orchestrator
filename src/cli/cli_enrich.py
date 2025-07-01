"""
CLI Enrichment Module

CLI enhancement utilities that provide rich user interface functions for the command-line interface:
- Rich console output with colors and formatting
- Error, success, and info message display
- User confirmation prompts
- Structured results display for orchestration outputs
- Viability assessment result presentation

This module enhances the basic CLI with visually appealing and informative output
using the Rich library for better user experience.
"""

import typer
from rich.console import Console
from typing import Dict, Any, List

# Initialize console for UI
console = Console()

# Basic UI functions
def display_error(message: str):
    """Display an error message in red"""
    console.print(f"[red]Error: {message}[/red]")

def display_success(message: str):
    """Display a success message in green"""
    console.print(f"[green]{message}[/green]")

def display_info(message: str):
    """Display an info message in blue"""
    console.print(f"[blue]{message}[/blue]")

def confirm_action(message: str) -> bool:
    """Prompt user for confirmation"""
    return typer.confirm(message)

# Specialized display functions
def display_viability_result(score: int, recommendations: list):
    """Display viability assessment results"""
    console.print(f"\n[bold]Viability Assessment Results:[/bold]")
    console.print(f"Score: {score}%")
    if recommendations:
        console.print("\nRecommendations:")
        for rec in recommendations:
            console.print(f"- {rec}")

def display_results_summary(results: Dict[str, Any], show_details: bool = False):
    """
    Display a summary of orchestration results
    
    Args:
        results: Dictionary containing all orchestration data
        show_details: Whether to show detailed information
    """
    try:
        console.print("\n[bold cyan]Orchestration Results Summary[/bold cyan]")
        
        _display_viability_section(results.get('viability_result', {}))
        _display_task_plan_section(results.get('task_plan', []), show_details)
        _display_implementation_section(results.get('implementation_results', {}), show_details)
        _display_test_section(results.get('test_results', {}), show_details)
        _display_overall_status(results.get('success', False))
        
        if show_details and results.get('execution_metadata'):
            _display_execution_metadata(results.get('execution_metadata', {}))
        console.print("\n")
        
    except Exception as e:
        console.print(f"[red]Failed to display results summary: {str(e)}[/red]")
        raise 

def _display_viability_section(viability: Dict[str, Any]):
    """Display viability assessment section"""
    console.print("\n[bold]Viability Assessment[/bold]")
    console.print(f"[green]Status:[/green] {viability.get('status')}")
    console.print(f"[green]Client Accepted:[/green] {viability.get('client_accepted')}")
    console.print(f"[green]Score:[/green] {viability.get('score')}%")

def _display_task_plan_section(task_plan: List[Dict[str, Any]], show_details: bool):
    """Display task plan section"""
    console.print("\n[bold]Task Plan[/bold]")
    console.print(f"[green]Total Tasks:[/green] {len(task_plan)}")
    
    if show_details:
        for task in task_plan:
            console.print(f"\n[blue]Task:[/blue] {task.get('name', task.get('id'))}")
            console.print(f"[blue]Category:[/blue] {task.get('category')}")
            console.print(f"[blue]Priority:[/blue] {task.get('priority')}")
            console.print(f"[blue]Description:[/blue] {task.get('description')}")

def _display_implementation_section(impl_results: Dict[str, Any], show_details: bool):
    """Display implementation results section"""
    console.print("\n[bold]Implementation Results[/bold]")
    console.print(f"[green]Total Tasks Completed:[/green] {len(impl_results)}")
    
    if show_details:
        for task_id, result in impl_results.items():
            if isinstance(result, dict):
                status = result.get('status')
                status_color = "green" if status == 'success' else "red"
                console.print(f"\n[blue]Task ID:[/blue] {task_id}")
                console.print(f"[blue]Status:[/blue] [{status_color}]{status}[/{status_color}]")
                console.print(f"[blue]Component:[/blue] {result.get('component')}")
                
                files_modified = []
                if 'result' in result and result['result']:
                    files_modified = result['result'].get('files_modified', [])
                
                console.print(f"[blue]Files Modified:[/blue] {len(files_modified)}")
                
                if files_modified:
                    console.print("[blue]Modified Files:[/blue]")
                    for file_info in files_modified:
                        if isinstance(file_info, dict):
                            file_name = file_info.get('file', 'Unknown')
                            action = file_info.get('action', 'modified')
                            console.print(f"  - {file_name} ({action})")

def _display_test_section(test_results: Dict[str, Any], show_details: bool):
    """Display test results section"""
    console.print("\n[bold]Test Results[/bold]")
    
    results = test_results.get('results')
    if results:
        for component, component_results in results.items():
            console.print(f"\n[blue]{component.title()}:[/blue]")
            if isinstance(component_results, dict):
                console.print(f"[green]Total Tests:[/green] {component_results.get('total')}")
                console.print(f"[green]Passed:[/green] {component_results.get('passed')}")
                console.print(f"[green]Failed:[/green] {component_results.get('failed')}")
                
                if show_details and component_results.get('failed_tests'):
                    console.print("\n[red]Failed Tests:[/red]")
                    for test in component_results.get('failed_tests'):
                        console.print(f"[red]- {test}[/red]")
    else:
        console.print("\n[yellow]No test results available[/yellow]")

def _display_overall_status(success: bool):
    """Display overall execution status"""
    status_text = '[green]Yes[/green]' if success else '[red]No[/red]'
    console.print(f"\n[bold]Overall Success:[/bold] {status_text}")

def _display_execution_metadata(metadata: Dict[str, Any]):
    """Display execution metadata section"""
    console.print("\n[bold]Execution Metadata[/bold]")
    for key, value in metadata.items():
        console.print(f"[blue]{key}:[/blue] {value}") 