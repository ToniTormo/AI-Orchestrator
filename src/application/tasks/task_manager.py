"""
Task Management Service

Orchestrates task categorization, planning, and execution with comprehensive context.
Architecture Flow:
TaskManager receives AI recommendations with file paths -> creates tasks -> categorizes as frontend/backend -> prioritizes -> executes
"""

from typing import List, Dict, Any, Optional

from src.utils.exceptions_control import create_error, TaskManagerError
from src.config import settings

from src.infrastructure.services import AsyncServiceBase
from src.application.services.agent_manager import AgentManager
from src.infrastructure.execution_tests.test_service import AutomatedTestingService
from src.infrastructure.mocks.mock_service import MockService
from src.domain.models.task_model import Task
from .task_categorizer import TaskCategorizer
from .task_prioritizer import TaskPrioritizer

class TaskManager(AsyncServiceBase):
    """
    Task management service that processes AI recommendations into executable tasks.
    
    Receives AI recommendations with file paths and actions, categorizes them as frontend/backend,
    prioritizes them, and coordinates execution through agents.
    """
    
    def __init__(self, agent_manager: AgentManager, testing_service: AutomatedTestingService = None, 
                 mock_service: MockService = None):
        """
        Initialize TaskManager with service dependencies
        
        Args:
            agent_manager: AgentManager for task execution
            testing_service: Optional testing service
            mock_service: Optional mock service for testing
        """
        super().__init__("task.manager")
        
        # Core services
        self.agent_manager = agent_manager
        
        # Optional services
        self.testing_service = testing_service
        self.mock_service = mock_service
        
        # Task processing components
        self.task_categorizer = TaskCategorizer()
        self.task_prioritizer = TaskPrioritizer()
        
        self.logger.info("[TaskManager] Initialized with simplified dependencies")

    async def _initialize_impl(self):
        """Initialize the task manager implementation"""
        if self.testing_service:
            await self.testing_service.initialize()

    async def _shutdown_impl(self):
        """Shutdown the task manager implementation"""
        if self.testing_service:
            await self.testing_service.shutdown()

    async def execute_agent_tasks(self, repo_path: str, technologies: Dict[str, Any], 
                                 ai_recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute the complete task workflow: planning + execution + testing
        
        Args:
            repo_path: Repository path for the project
            technologies: Detected technologies and frameworks with tech_stack
            ai_recommendations: List of AnalysisTask objects from AgentAnalyzerOutput
            
        Returns:
            Dictionary with implementation results and test results
        """
        if not repo_path:
            raise create_error(TaskManagerError, "Repository path is required for task execution", "TaskManager")
        
        if not ai_recommendations:
            raise create_error(TaskManagerError, "AI recommendations (task steps) are required for task execution", "TaskManager")
        
        if not technologies:
            raise create_error(TaskManagerError, "Technologies are required for task execution", "TaskManager")
        
        self.logger.info(f"[TaskExecution] Starting workflow for: {repo_path} with {len(ai_recommendations)} AI recommendations")
        
        try:
            # Run health checks before starting the workflow
            await self.agent_manager.check_all_agents_health()

            # Create task plan from AI recommendations
            task_plan = await self._create_task_plan_from_ai_recommendations(technologies, ai_recommendations)
            
            self.logger.info(f"[TaskExecution] Created plan with {len(task_plan)} tasks")
            
            # Execute tasks using agents
            if settings.mock.enabled:
                mock_results = await self._execute_mock_tasks(task_plan)
                mock_results['task_plan'] = [task.model_dump() for task in task_plan]
                return mock_results
            
            # Pass repo_path and technologies to the real execution
            real_results = await self._execute_real_tasks(task_plan, repo_path, technologies)
            real_results['task_plan'] = [task.model_dump() for task in task_plan]
            return real_results
            
        except Exception as e:
            raise create_error(TaskManagerError, f"Task workflow execution failed: {str(e)}", "TaskManager")

    async def _create_task_plan_from_ai_recommendations(self, technologies: Dict[str, Any], 
                                                       ai_recommendations: List[Dict[str, Any]]) -> List[Task]:
        """
        Creates a task plan from AI recommendations
        
        Args:
            repo_path: Repository path
            technologies: Detected technologies with tech_stack
            ai_recommendations: List of AnalysisTask objects with id, file_path, specific_changes
            
        Returns:
            List of planned Task objects (Pydantic models)
        """
        
        self.logger.info(f"[TaskPlan] Creating plan from {len(ai_recommendations)} AI recommendations")
        
        try:
            tasks = []
            
            # Create tasks from AI recommendations
            for i, recommendation in enumerate(ai_recommendations):
                # Convert Pydantic model to dict if needed
                if not isinstance(recommendation, dict):
                    recommendation = recommendation.model_dump() if hasattr(recommendation, 'model_dump') else recommendation
                
                task = await self._create_task_from_recommendation(
                    recommendation, i, technologies
                )
                
                if task:
                    tasks.append(task)
            
            if not tasks:
                raise create_error(TaskManagerError, "No valid tasks created from AI recommendations", "TaskManager")
            
            # Sort tasks by priority: high → medium → low
            priority_map = {"high": 0, "medium": 1, "low": 2}
            sorted_tasks = sorted(tasks, key=lambda task: priority_map.get(task.priority, 1))
            
            self.logger.info(f"[TaskPlan] Created {len(sorted_tasks)} tasks sorted by priority")
            return sorted_tasks
            
        except Exception as e:
            raise create_error(TaskManagerError, f"Failed to create task plan: {str(e)}", "TaskManager")

    async def _create_task_from_recommendation(self, recommendation: Dict[str, Any], index: int, 
                                               tech_stack: Dict[str, Any]) -> Optional[Task]:
        """
        Create a single task from an AI recommendation
        
        Args:
            recommendation: AI recommendation dictionary containing id, file_path, specific_changes
            index: Recommendation index
            tech_stack: Analyzed tech stack
            
        Returns:
            Task object or None if creation fails
        """
        try:
            # Extract task information from AnalysisTask structure
            task_ai_id = recommendation.get('id')
            file_path = recommendation.get('file_path')
            specific_changes = recommendation.get('specific_changes')
            
            if not specific_changes:
                self.logger.warning(f"[TaskPlan] Skipping recommendation {index}: no specific_changes")
                return None
            
            if not file_path:
                self.logger.warning(f"[TaskPlan] Skipping recommendation {index}: no file_path")
                return None
            
            # Determine task category (frontend/backend) using task_categorizer
            category = self.task_categorizer.determine_task_category(specific_changes, tech_stack)
            
            task_priority = self.task_prioritizer.determine_priority(specific_changes)
            
            # Create Task using Pydantic model
            task = Task(
                id=task_ai_id,
                description=specific_changes,
                file_path=file_path,
                category=category,
                priority=task_priority
            )
            
            self.logger.debug(f"[TaskPlan] Created task: {task_ai_id} for file: {file_path}")
            return task
            
        except Exception as e:
            self.logger.error(f"[TaskPlan] Failed to create task from recommendation {index}: {str(e)}")
            return None

    async def _execute_real_tasks(self, task_plan: List[Task], repo_path: str, technologies: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tasks using real agents"""
        # Create a shared context for all tasks
        shared_context = {
            "repo_path": repo_path,
            "technologies": technologies
        }

        # Add context to each task before assignment
        tasks_with_context = []
        for task in task_plan:
            task_dict = task.model_dump()
            task_dict["context"] = shared_context
            tasks_with_context.append(task_dict)

        # Assign tasks to agents
        self.logger.info("[TaskManager] Assigning tasks to agents")
        assigned_tasks = await self.agent_manager.assign_tasks_to_agents(tasks_with_context)
        
        # Execute tasks
        execution_results = await self.agent_manager.execute_tasks_by_agent(assigned_tasks)
        
        # Run tests on implementation results
        implementation_results = execution_results.get("implementation_results")
        if implementation_results is None:
            raise create_error(TaskManagerError, "Agent execution did not return implementation results", "TaskManager")
        
        test_results = await self._run_tests(implementation_results)
        
        # Calculate success metrics and collect modified files
        total_tasks = len(task_plan)
        completed_tasks = 0
        modified_files = []
        
        for task_id, result in implementation_results.items():
            if result.get('status') == 'success':
                completed_tasks += 1
                # Collect modified files from successful tasks
                if 'result' in result and 'files_modified' in result['result']:
                    modified_files.extend(result['result']['files_modified'])
        
        success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Create summary of changes
        changes_summary = []
        if modified_files:
            changes_summary.append(f"Modified {len(modified_files)} files:")
            for file_info in modified_files:
                changes_summary.append(f"- {file_info['file']} ({file_info['action']})")
        
        results = {
            "tasks_completed": completed_tasks,
            "total_tasks": total_tasks,
            "success_rate": success_rate,
            "test_results": test_results,
            "modified_files": modified_files,
            "implementation_results": implementation_results,
        }
        
        self.logger.info(f"[TaskExecution] Workflow completed. Success rate: {success_rate:.1f}%")
        
        return results

    async def _run_tests(self, implementation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Run tests on implementation results"""
        if self.testing_service:
            self.logger.info("[TaskManager] Running tests on implementation results")
            try:
                test_results = await self.testing_service.run_implementation_tests(implementation_results)
                if test_results is None:
                    raise create_error(TaskManagerError, "Testing service returned None", "TaskManager")
                
                if "results" not in test_results or "all_passed" not in test_results:
                    raise create_error(TaskManagerError, "Testing service returned incomplete results", "TaskManager")

                return {
                    "results": test_results["results"],
                    "all_passed": test_results["all_passed"]
                }
            except Exception as e:
                self.logger.error(f"[TaskManager] Testing failed: {str(e)}")
                raise create_error(TaskManagerError, f"Test execution failed: {str(e)}", "TaskManager")
        else:
            self.logger.info("[TaskManager] No testing service available, skipping tests")
            return {"results": {}, "all_passed": False}

    async def _execute_mock_tasks(self, task_plan: List[Task]) -> Dict[str, Any]:
        """Execute tasks in mock mode"""
        if not self.mock_service:
            raise create_error(TaskManagerError, "Mock service not available for mock execution", "TaskManager")
        
        self.logger.info("[TaskExecution] Mock mode enabled")
        task_plan_dicts = [task.model_dump() for task in task_plan]
        mock_results = self.mock_service.get_mock_task_results(task_plan_dicts)
        
        if mock_results is None:
            raise create_error(TaskManagerError, "Mock service returned None", "TaskManager")
        
        # For mock tasks, we assume all tasks succeed
        total_tasks = len(task_plan)
        modified_files = [
            {
                "file": task.file_path,
                "action": "modified"
            }
            for task in task_plan
        ]
        
        # Create mock implementation results
        mock_implementation_results = {}
        for task in task_plan:
            mock_implementation_results[task.id] = {
                "status": "success",
                "component": task.category,
                "result": {
                    "task_id": task.id,
                    "output": f"Mock implementation completed for {task.file_path}",
                    "error": None,
                    "files_modified": [{"file": task.file_path, "action": "modified"}]
                }
            }
        
        results = {
            "tasks_completed": total_tasks,
            "total_tasks": total_tasks,
            "success_rate": 100.0,
            "test_results": {"results": {}, "all_passed": True},
            "modified_files": modified_files,
            "implementation_results": mock_implementation_results,
        }
        
        self.logger.info(f"[TaskExecution] Mock workflow completed. All {total_tasks} tasks succeeded")
        
        return results
