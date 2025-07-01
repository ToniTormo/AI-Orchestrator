"""
CLI Runner

Handles the execution logic for CLI commands.
This module contains the core business logic for running the orchestration system,
implementing the complete workflow from repository cloning to result notification.
"""

import typer
from src.utils.logging import setup_logger
from src.config import settings
from src.application.project_coordinator import ProjectCoordinator
from src.utils.exceptions_control import UserAbortError
from src.cli.cli_enrich import display_error, display_info

# Setup logger using configuration
logger = setup_logger(
    "cli.runner",
    settings.logging.module_levels.get("cli", settings.logging.level)
)

async def run_cli(
    repo_url: str,
    branch: str,
    description: str,
    email: str
):
    """
    Run the orchestration system in CLI mode following the complete workflow:
    1. Initialize services via factory
    2. Analyze repository and viability  
    3. Create feature branch
    4. Execute tasks
    5. Run tests
    6. Create merge request
    7. Send notification
    
    Args:
        repo_url: Repository URL to process
        branch: Target branch for merge
        description: Description of requested changes
        email: Email for notifications
    """
    current_description = description
    retry_count = 0
    project_coordinator = None
    
    try:
        while True:
            try:
                logger.info(f"[CLI.Run] Starting orchestration for repository: {repo_url} (attempt {retry_count + 1})")

                # Create project coordinator and execute complete workflow
                if project_coordinator is None:
                    project_coordinator = ProjectCoordinator()
                
                success = await project_coordinator.execute_project(
                    repo_url=repo_url,
                    branch=branch,
                    description=current_description,
                    email=email
                )
                
                # If execution was successful or user confirmed, we're done
                if success is not False:  # None (completed) or True (success)
                    logger.info("[CLI.Run] Project orchestration completed successfully")
                    return
                
                # User declined the current implementation plan
                retry_count += 1
                display_info(f"\n🔄 No problem! Let's try a different approach.")
                display_info("You can:")
                display_info("• Provide a more specific description")
                display_info("• Focus on a particular aspect of the project") 
                display_info("• Try a different implementation strategy")
                display_info("")
                
                new_description = typer.prompt("💭 Enter a new description for the project (or type 'quit' to exit)")
                
                if not new_description.strip():
                    display_error("Empty description provided. Exiting.")
                    break
                
                # Allow user to quit
                if new_description.strip().lower() in ['quit', 'exit', 'q', 'salir']:
                    display_info("👋 Goodbye! Thanks for using AI Project Orchestrator.")
                    break
                    
                current_description = new_description.strip()
                display_info(f"🚀 Reanalyzing with new description: '{current_description}'\n")
                
            except UserAbortError as e:
                display_error(f"[CLI.Run] User aborted operation: {str(e)}")
                break
            except Exception as e:
                display_error(f"[CLI.Run] Error during orchestration: {str(e)}")
                raise typer.Exit(1)
                
    finally:
        # Cleanup services if we have a coordinator with active services
        if project_coordinator and hasattr(project_coordinator, 'services') and project_coordinator.services:
            logger.info("[CLI.Run] Cleaning up services before exit")
            await project_coordinator.cleanup_services()
            
    # Exit cleanly
    raise typer.Exit(0) 