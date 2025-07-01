"""
Agent Manager

Manages the lifecycle and execution of AI agents
"""

import asyncio
from typing import List, Dict, Any
from datetime import datetime

from src.infrastructure.services import AsyncServiceBase
from src.utils.exceptions_control import create_error, AgentError
from src.application.agents.agent_development import AgentDevelopment
from src.application.agents.agent_analyzer import AgentAnalyzer
from src.domain.models.agent_model import AgentStatus, AgentType
from src.application.services.agent_health_service import AgentHealthService

class AgentManager(AsyncServiceBase):
    """
    Manages available AI agents and their capabilities.
    Handles agent registration, availability checks, and capability matching.
    """

    def __init__(self, agent_health_service: AgentHealthService = None, openai_service=None):
        """
        Initialize the agent manager with all available agents and shared services
        
        Args:
            agent_health_service: The health service instance to use (optional, will create if not provided)
            openai_service: Optional OpenAI service instance to share among agents
        """
        super().__init__("agent.manager")
        
        try:
            self.agents: Dict[str, AsyncServiceBase] = {
                "frontend": AgentDevelopment(AgentType.FRONTEND, openai_service),
                "backend": AgentDevelopment(AgentType.BACKEND, openai_service),
                "analyzer": AgentAnalyzer(openai_service)
            }
            # Use provided health service or create new one (for backward compatibility)
            self.health_service = agent_health_service or AgentHealthService()
            self.logger.info("[AgentManager] Successfully initialized with frontend, backend, and analyzer agents")
        except Exception as e:
            raise create_error(AgentError, f"Failed to initialize agent manager: {e}", "AgentManager")

    async def _initialize_impl(self):
        """Initialize all agents implementation"""
        for name, agent in self.agents.items():
            try:
                await agent.initialize()
                
                # Create initial status
                status = AgentStatus(
                    registered_at=datetime.now(),
                    status="available",
                    last_health_check=datetime.now()
                )
                self.health_service.update_agent_status(name, status)
                
                self.logger.info(f"[AgentManager] Agent {name} initialized successfully")
            except Exception as e:
                status = AgentStatus(
                    registered_at=datetime.now(),
                    status="error",
                    last_health_check=datetime.now(),
                    error=str(e)
                )
                self.health_service.update_agent_status(name, status)
                raise create_error(AgentError, f"Failed to initialize agent {name}: {e}", "AgentManager")

    async def _shutdown_impl(self):
        """Shutdown all agents implementation"""
        for name, agent in self.agents.items():
            try:
                await agent.shutdown()
                
                # Update status
                status = self.health_service.get_agent_status(name)
                if status:
                    status.status = "shutdown"
                    status.shutdown_at = datetime.now()
                    self.health_service.update_agent_status(name, status)
                
                self.logger.info(f"[AgentManager] Agent {name} shut down successfully")
            except Exception as e:
                self.logger.error(f"[AgentManager] Error shutting down agent {name}: {e}")
                status = self.health_service.get_agent_status(name)
                if status:
                    status.status = "error"
                    status.error = str(e)
                    self.health_service.update_agent_status(name, status)
                # Continue with other agents even if one fails

    async def check_all_agents_health(self) -> None:
        """
        Run health checks on all registered agents to update their status.
        """
        for agent_id, agent in self.agents.items():
            await self.health_service.check_agent_health(agent_id, agent)

    async def assign_tasks_to_agents(self, task_plan: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Assigns tasks to appropriate agents based on technology and specialization
        
        Args:
            task_plan: List of planned tasks
            
        Returns:
            Tasks assigned to each agent type
        """
        self.logger.info("[AgentManager] Assigning tasks to specialized agents")
        
        # Structure to store assigned tasks
        assigned_tasks = {
            "frontend": [],
            "backend": []
        }
        
        # Assign each task to the appropriate agent
        for task in task_plan:
            category = task.get("category")
            if category in assigned_tasks and category in self.agents:
                assigned_tasks[category].append(task)
                self.logger.debug(f"[AgentManager] Assigned task {task.get('id')} to {category} agent")
            else:
                self.logger.warning(f"[AgentManager] Unknown category {category} for task {task.get('id')}")
        
        return assigned_tasks

    async def execute_tasks_by_agent(self, assigned_tasks: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Execute tasks assigned to each agent with automatic parallel execution detection
        
        The system automatically chooses the optimal execution mode:
        - **Parallel**: When multiple agents have tasks OR a single agent has multiple tasks
        - **Sequential**: When only one agent has a single task
        
        Args:
            assigned_tasks: Tasks assigned to each agent type
            
        Returns:
            Dictionary with execution results
        """
        # Automatically detect if parallel execution should be used
        agents_with_tasks = {agent_type: tasks for agent_type, tasks in assigned_tasks.items() if tasks and agent_type in self.agents}
        total_tasks = sum(len(tasks) for tasks in agents_with_tasks.values())
        
        # Use parallel execution if:
        # 1. There are multiple agents with tasks, OR
        # 2. A single agent has multiple tasks
        should_use_parallel = len(agents_with_tasks) > 1 or total_tasks > 1
        
        self.logger.info(f"[AgentManager] Executing {total_tasks} tasks across {len(agents_with_tasks)} agents ({'parallel' if should_use_parallel else 'sequential'})")
        
        results = {
            "implementation_results": {},
            "test_results": {
                "results": {},
                "all_passed": False
            }
        }
        
        if should_use_parallel:
            await self._execute_tasks_parallel(agents_with_tasks, results)
        else:
            await self._execute_tasks_sequential(agents_with_tasks, results)
        
        return results

    async def _execute_tasks_parallel(self, agents_with_tasks: Dict[str, List[Dict[str, Any]]], results: Dict[str, Any]):
        """Execute all tasks across all agents in parallel"""
        all_tasks = []
        task_metadata = []  # To track which task belongs to which agent
        
        for agent_type, tasks in agents_with_tasks.items():
            agent = self.agents[agent_type]
            for task in tasks:
                # Create async task for each individual task
                async_task = asyncio.create_task(
                    self._execute_single_task(agent, agent_type, task)
                )
                all_tasks.append(async_task)
                task_metadata.append({
                    'task_id': task['id'],
                    'agent_type': agent_type,
                    'task': task
                })
        
        if all_tasks:
            # Execute all tasks concurrently
            task_results = await asyncio.gather(*all_tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(task_results):
                metadata = task_metadata[i]
                task_id = metadata['task_id']
                agent_type = metadata['agent_type']
                task = metadata['task']
                
                # Handle normal task results (success or error from agent)
                if result.get('error'):
                    self.logger.error(f"[AgentManager] Task {task_id} failed: {result['error']}")
                    results["implementation_results"][task_id] = {
                        'status': 'failed',
                        'error': result['error'],
                        'component': agent_type
                    }
                else:
                    results["implementation_results"][task_id] = {
                        'status': 'success',
                        'result': result,
                        'component': agent_type
                    }

    async def _execute_tasks_sequential(self, agents_with_tasks: Dict[str, List[Dict[str, Any]]], results: Dict[str, Any]):
        """Execute tasks sequentially for single agent or single task scenarios"""
        for agent_type, tasks in agents_with_tasks.items():
            agent = self.agents[agent_type]
            for task in tasks:
                try:
                    self.logger.debug(f"[AgentManager] Executing task {task['id']}")
                    result = await agent.execute_task(task)
                    
                    # Check if there was an error in the result
                    if result.get('error'):
                        self.logger.error(f"[AgentManager] Task {task['id']} failed: {result['error']}")
                        results["implementation_results"][task['id']] = {
                            'status': 'failed',
                            'error': result['error'],
                            'component': agent_type
                        }
                    else:
                        results["implementation_results"][task['id']] = {
                            'status': 'success',
                            'result': result,
                            'component': agent_type
                        }
                except Exception as e:
                    self.logger.error(f"[AgentManager] Task {task['id']} failed with exception: {e}")
                    results["implementation_results"][task['id']] = {
                        'status': 'failed',
                        'error': str(e),
                        'component': agent_type
                    }

    async def _execute_single_task(self, agent: AsyncServiceBase, agent_type: str, task: Dict[str, Any]) -> Any:
        """
        Execute a single task and handle exceptions appropriately for parallel execution
        
        Args:
            agent: The agent to execute the task
            agent_type: Type of the agent
            task: Task to execute
            
        Returns:
            Task execution result from the agent containing:
            - task_id: ID of the executed task
            - output: Description of the execution result
            - error: Any error that occurred (None if successful)
            - files_modified: List of files that were modified
        """
        try:
            self.logger.debug(f"[AgentManager] Executing task {task['id']} on {agent_type} agent")
            return await agent.execute_task(task)
        except Exception as e:
            raise create_error(AgentError, f"Task {task['id']} on {agent_type} failed: {e}", "AgentManager") 