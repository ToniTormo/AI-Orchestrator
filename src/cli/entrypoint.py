"""
CLI Entrypoint

Command-line interface for the AI Project Orchestration System.
This module defines the CLI commands and their interface, providing:
- Project orchestration command with full workflow
- Web interface launcher
- Testing commands for different test types
- Configuration validation on startup
"""

import asyncio
import subprocess
import typer
from pathlib import Path
from src.utils.logging import setup_logger
from src.config import settings
from src.cli.cli_runner import run_cli
from src.cli.cli_enrich import display_error
from src.utils.exceptions_control import create_error, ValidationError

# Initialize Typer app
app = typer.Typer(
    name="project",
    help="AI Project Orchestration System",
    add_completion=False
)

# Setup logger using configuration
logger = setup_logger(
    "cli.entrypoint",
    settings.logging.module_levels.get("cli", settings.logging.level)
)

@app.callback()
def callback():
    """
    AI Project Orchestration System
    
    A system for orchestrating AI-driven project implementation
    """
    logger.info("[CLI] Starting application with configuration validation...")
    
    # Check OpenAI configuration (unless mocks are enabled)
    if not settings.openai.api_key and not settings.mock.enabled:
        raise create_error(ValidationError, "OpenAI API key not configured and mocks disabled. Set OPENAI_API_KEY or enable USE_MOCKS=true", "CLI")
    
    logger.info("[CLI] Configuration validation completed successfully")

@app.command()
def run(
    repo_url: str = typer.Option(..., help="URL of the repository to clone"),
    branch: str = typer.Option("main", help="Branch to merge into"),
    description: str = typer.Option(..., help="Description of the requested changes"),
    email: str = typer.Option(..., help="E-mail address for review notifications")
):
    """
    Run the orchestration system in CLI mode.
    
    This command executes the complete orchestration workflow:
    1. Clone the specified repository
    2. Analyze project viability
    3. Create a feature branch
    4. Execute required tasks
    5. Run tests
    6. Create a merge request
    7. Send notification
    """
    asyncio.run(run_cli(repo_url, branch, description, email))

@app.command()
def web():
    """
    Launch the Streamlit web interface.
    
    This command starts the Streamlit web interface providing:
    - Interactive project details input
    - Real-time analysis results viewing
    - Task execution monitoring
    - Test results review interface
    """
    try:
        logger.info("[CLI.Web] Starting web interface...")
        with subprocess.Popen(["poetry", "run", "python", "-m", "src.frontend.run"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as process:
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                display_error(f"[CLI.Web] Failed to start web interface: {stderr}")
                raise typer.Exit(1)
    except Exception as e:
        display_error(f"[CLI.Web] Unexpected error starting web interface: {str(e)}")
        raise typer.Exit(1)

@app.command()
def test(
    type: str = typer.Option("all", help="Type of tests to run: all, unit, integration, e2e"),
    coverage: bool = typer.Option(False, help="Generate coverage report"),
    verbose: bool = typer.Option(False, help="Verbose output"),
    file: str = typer.Option(None, help="Run specific test file")
):
    """
    Run the test suite.
    
    Execute different types of tests:
    - unit: Unit tests for individual components
    - integration: Integration tests with mock services  
    - e2e: End-to-end CLI workflow tests
    - all: Run complete test suite
    """
    try:
        logger.info(f"[CLI.Test] Running {type} tests...")
        
        # Build pytest command with poetry
        cmd = ["poetry", "run", "python", "-m", "pytest"]
        
        # Add test directory based on type
        if file:
            if not Path(file).exists():
                display_error(f"[CLI.Test] Test file not found: {file}")
                raise typer.Exit(1)
            cmd.append(file)
        elif type == "unit":
            cmd.append("src/project_tests/unit/")
        elif type == "integration":
            cmd.append("src/project_tests/integration/")
        elif type == "e2e":
            cmd.append("src/project_tests/e2e/")
        elif type == "all":
            cmd.append("src/project_tests/")
        else:
            display_error(f"[CLI.Test] Invalid test type: {type}")
            raise typer.Exit(1)
        
        # Add options
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])
        
        # Add pytest configuration
        cmd.extend(["--tb=short"])
        
        logger.info(f"[CLI.Test] Executing: {' '.join(cmd)}")
        
        # Run tests
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Display output
        if result.stdout:
            typer.echo(result.stdout)
        
        if result.stderr:
            typer.echo(result.stderr, err=True)
        
        # Handle exit code
        if result.returncode == 0:
            logger.info(f"[CLI.Test] {type.capitalize()} tests completed successfully")
            if coverage:
                typer.echo("📊 Coverage report generated in htmlcov/index.html")
        else:
            display_error(f"[CLI.Test] Tests failed with exit code {result.returncode}")
            raise typer.Exit(result.returncode)
            
    except Exception as e:
        display_error(f"[CLI.Test] Unexpected error running tests: {str(e)}")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()