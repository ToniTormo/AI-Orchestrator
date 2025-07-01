"""
Context Factory

Factory for creating and initializing all required services for CLI operations.
Handles the complete setup of components without unnecessary wrapper classes.
"""

from typing import Dict, Any, Optional
from pathlib import Path
from src.config import settings
from src.utils.logging import setup_logger
from src.utils.exceptions_control import create_error, OrchestrationError
from src.domain.models import ContextCreationInput
from src.application.tasks.task_manager import TaskManager
from src.infrastructure.git.git_service import GitService
from src.infrastructure.notification.email_service import EmailNotificationService
from src.application.analysis import AnalysisService
from src.application.services.agent_manager import AgentManager
from src.application.services.agent_health_service import AgentHealthService
from src.infrastructure.execution_tests.test_service import AutomatedTestingService
from src.infrastructure.mocks.mock_service import MockService
from src.infrastructure.mocks import is_mock_enabled, MockOpenAIService
from src.infrastructure.openai.openai_service import OpenAIService
from src.infrastructure.execution_tests.test_manager import TestManager

class CLIContextFactory:
    """
    Factory for creating and properly initializing all required services for CLI operations.
    Returns initialized services ready for use by ProjectCoordinator.
    """
    
    def __init__(self):
        """Initialize the factory with centralized logging"""
        self.logger = setup_logger(
            "cli.context_factory",
            settings.logging.module_levels.get("cli", settings.logging.level)
        )
    
    async def create_initialized_services(
        self,
        repo_url: str,
        branch: str,
        description: str,
        email: str,
        repos_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create and initialize all services with Pydantic validation
        
        Args:
            repo_url: URL of the repository to clone
            branch: Branch to merge into
            description: Description of the requested changes
            email: E-mail address for review notifications
            repos_path: Optional custom path for repositories
            
        Returns:
            Dict containing all initialized services and validated parameters
        """
        # Validate input parameters using Pydantic model
        validated_input = ContextCreationInput(
            repo_url=repo_url,
            branch=branch,
            description=description,
            email=email,
            repos_path=repos_path
        )
        
        self.logger.info("[ContextFactory] Creating and initializing services with validated parameters")
        
        try:
            # Create all services
            services = await self._create_and_initialize_services(validated_input)
            
            # Return services and parameters for ProjectCoordinator
            return {
                'services': services,
                'params': {
                    'repo_url': str(validated_input.repo_url),
                    'branch': validated_input.branch,
                    'description': validated_input.description,
                    'email': str(validated_input.email)
                }
            }
            
        except Exception as e:
            raise create_error(OrchestrationError, f"Service creation and initialization failed: {str(e)}", "CLIContextFactory")
    
    async def _create_and_initialize_services(self, validated_input: ContextCreationInput) -> Dict[str, Any]:
        """
        Create and initialize all required services
        
        Args:
            validated_input: Validated input parameters
            
        Returns:
            Dict containing all initialized services
        """
        try:
            # Step 1: Create core services
            core_services = self._create_core_services()
            
            # Step 2: Create OpenAI service (real or mock)
            openai_service = self._create_openai_service()
            
            # Step 3: Create git service
            git_service = self._create_git_service(validated_input.repos_path)
            
            # Step 4: Create agent services
            agent_manager = self._create_agent_services(core_services, openai_service)
            
            # Step 5: Create task management services
            task_manager = self._create_task_management(agent_manager, git_service, core_services)
            
            # Step 6: Create notification service
            notification_service = self._create_notification_service()
            
            # Step 7: Initialize async services in correct order
            await self._initialize_async_services(agent_manager, task_manager)
            
            self.logger.info("[ContextFactory] All services created and initialized successfully")
            
            return {
                'agent_manager': agent_manager,
                'task_manager': task_manager,
                'git_service': git_service,
                'analysis_service': core_services['analysis_service'],
                'notification_service': notification_service,
                # Private services for internal use
                '_agent_health_service': core_services['agent_health_service'],
                '_testing_service': core_services['testing_service'],
                '_mock_service': core_services['mock_service'],
                '_test_manager': core_services['test_manager']
            }

        except Exception as e:
            raise create_error(OrchestrationError, f"Service initialization failed: {str(e)}", "CLIContextFactory")
    
    def _create_core_services(self) -> Dict[str, Any]:
        """Create core shared services"""
        core_services = {
            'agent_health_service': AgentHealthService(),
            'testing_service': AutomatedTestingService(),
            'mock_service': MockService(),
            'test_manager': TestManager(),
            'analysis_service': AnalysisService()
        }
        
        self.logger.info("[ContextFactory] Core services created")
        return core_services
    
    def _create_openai_service(self):
        """Create OpenAI service (real or mock based on configuration)"""
        if is_mock_enabled():
            self.logger.info("[ContextFactory] Creating MockOpenAIService")
            return MockOpenAIService()
        else:
            self.logger.info("[ContextFactory] Creating real OpenAIService")
            return OpenAIService()
    
    def _compute_repositories_path(self) -> str:
        """
        Compute the absolute path for repositories
        
        Returns:
            Absolute path string for repositories directory
        """
        try:
            project_root = Path(__file__).parents[3]
            repos_path = project_root / "src" / "infrastructure" / "repositories"
            
            if not repos_path.exists():
                repos_path.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"[ContextFactory] Created repositories directory: {repos_path}")
            
            self.logger.info(f"[ContextFactory] Computed repositories path: {repos_path}")
            return str(repos_path)
            
        except Exception as e:
            raise create_error(OrchestrationError, f"Failed to compute repositories path: {str(e)}", "CLIContextFactory")
    
    def _create_git_service(self, repos_path: Optional[str]):
        """Create Git service with computed path"""
        # CRITICAL: Explicit validation - no automatic defaults that hide failures
        if repos_path is not None and repos_path.strip() == "":
            raise create_error(OrchestrationError, "Empty repos_path provided - explicit path required or use None", "CLIContextFactory")
        
        git_path = repos_path if repos_path is not None else self._compute_repositories_path()
        git_service = GitService(base_path=git_path)
        self.logger.info(f"[ContextFactory] Git service created with path: {git_path}")
        return git_service
    
    def _create_agent_services(self, core_services: Dict[str, Any], openai_service) -> AgentManager:
        """Create agent manager and related services"""
        agent_manager = AgentManager(
            agent_health_service=core_services['agent_health_service'],
            openai_service=openai_service
        )
        self.logger.info("[ContextFactory] Agent manager created")
        return agent_manager
    
    def _create_task_management(self, agent_manager: AgentManager, git_service: GitService, 
                              core_services: Dict[str, Any]) -> TaskManager:
        """Create task manager with all required dependencies"""
        # Update testing service to use shared test manager
        testing_service = AutomatedTestingService(core_services['test_manager'])
        
        # Create task manager with all dependencies
        task_manager = TaskManager(
            agent_manager=agent_manager,
            testing_service=testing_service,
            mock_service=core_services['mock_service']
        )
        self.logger.info("[ContextFactory] Task manager created")
        return task_manager
    
    def _create_notification_service(self) -> EmailNotificationService:
        """Create the notification service"""
        self.logger.info("[ContextFactory] Notification service created")
        return EmailNotificationService()
    
    async def _initialize_async_services(self, agent_manager: AgentManager, task_manager: TaskManager):
        """Initialize asynchronous services in the correct order"""
        # Initialize agent manager first (root dependency)
        await agent_manager.initialize()
        self.logger.info("[ContextFactory] Agent manager initialized successfully")
        
        # Initialize task manager (depends on agent manager)
        await task_manager.initialize()
        self.logger.info("[ContextFactory] Task manager initialized successfully")
    
    async def shutdown_services(self, services: Dict[str, Any]):
        """
        Shutdown all services in reverse order
        
        Args:
            services: Dict containing services to shutdown
        """
        try:
            self.logger.info("[ContextFactory] Starting services shutdown")
            
            # Shutdown in reverse order of initialization
            if 'task_manager' in services:
                await services['task_manager'].shutdown()
                self.logger.info("[ContextFactory] Task manager shut down successfully")
            
            if 'agent_manager' in services:
                await services['agent_manager'].shutdown()
                self.logger.info("[ContextFactory] Agent manager shut down successfully")
            
            self.logger.info("[ContextFactory] Services shutdown completed successfully")
            
        except Exception as e:
            # Use create_error for consistent error handling and logging
            raise create_error(OrchestrationError, f"Services shutdown failed: {str(e)}", "CLIContextFactory")
