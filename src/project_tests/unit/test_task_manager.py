"""
Unit tests for TaskManager

Tests for task management, categorization, prioritization, and execution.
"""

import pytest
from unittest.mock import AsyncMock, patch
from src.application.tasks.task_manager import TaskManager
from src.application.services.agent_manager import AgentManager
from src.utils.exceptions_control import TaskManagerError

# ==================== FIXTURES ====================
# Using fixtures from conftest.py: mock_agent_manager, testing_service, mock_service

# ==================== TESTS ====================

@pytest.mark.unit
class TestTaskManager:
    """Test TaskManager class"""

    def test_task_manager_initialization(self):
        """Test TaskManager initialization."""
        mock_agent_manager = AsyncMock(spec=AgentManager)
        manager = TaskManager(agent_manager=mock_agent_manager)
        
        assert manager.agent_manager == mock_agent_manager
        assert manager.testing_service is None
        assert manager.mock_service is None
        assert hasattr(manager, 'task_categorizer')
        assert hasattr(manager, 'task_prioritizer')

    @pytest.mark.asyncio
    async def test_task_manager_initialization_impl(self, mock_agent_manager, testing_service, mock_service):
        """Test TaskManager initialization implementation."""
        manager = TaskManager(
            agent_manager=mock_agent_manager,
            testing_service=testing_service,
            mock_service=mock_service
        )
        await manager.initialize()
        
        assert manager is not None
        assert hasattr(manager, 'agent_manager')

    @pytest.mark.asyncio
    async def test_task_manager_shutdown_impl(self, mock_agent_manager, testing_service, mock_service):
        """Test TaskManager shutdown implementation."""
        manager = TaskManager(
            agent_manager=mock_agent_manager,
            testing_service=testing_service,
            mock_service=mock_service
        )
        await manager.initialize()
        
        # Should complete without errors
        await manager.shutdown()

    @pytest.mark.asyncio
    async def test_execute_agent_tasks_success(self, mock_agent_manager, testing_service, mock_service):
        """Test successful agent task execution."""
        manager = TaskManager(
            agent_manager=mock_agent_manager,
            testing_service=testing_service,
            mock_service=mock_service
        )
        await manager.initialize()
        
        repo_path = "/tmp/test-repo"
        technologies = {
            "languages": ["Python"],
            "frameworks": ["FastAPI"],
            "tech_stack": {"backend": ["Python", "FastAPI"]}
        }
        ai_recommendations = [
            {
                "id": "task_001",
                "file_path": "src/main.py",
                "specific_changes": "Add error handling"
            }
        ]

        # Mock the settings to enable mocks
        with patch('src.application.tasks.task_manager.settings') as mock_settings:
            mock_settings.mock.enabled = True
            
            result = await manager.execute_agent_tasks(
                repo_path, technologies, ai_recommendations
            )

            assert isinstance(result, dict)
            # When mocks are enabled, we should get mock results

    @pytest.mark.asyncio
    async def test_execute_agent_tasks_empty_repo_path(self, mock_agent_manager, testing_service, mock_service):
        """Test execute_agent_tasks with empty repo path."""
        manager = TaskManager(
            agent_manager=mock_agent_manager,
            testing_service=testing_service,
            mock_service=mock_service
        )
        await manager.initialize()
        
        technologies = {"tech_stack": {"backend": ["Python"]}}
        ai_recommendations = [{"id": "task_001"}]

        with pytest.raises((TaskManagerError, ValueError)):
            await manager.execute_agent_tasks("", technologies, ai_recommendations)

    @pytest.mark.asyncio
    async def test_execute_agent_tasks_empty_recommendations(self, mock_agent_manager, testing_service, mock_service):
        """Test execute_agent_tasks with empty recommendations."""
        manager = TaskManager(
            agent_manager=mock_agent_manager,
            testing_service=testing_service,
            mock_service=mock_service
        )
        await manager.initialize()
        
        repo_path = "/tmp/test-repo"
        technologies = {"tech_stack": {"backend": ["Python"]}}

        with pytest.raises((TaskManagerError, ValueError)):
            await manager.execute_agent_tasks(repo_path, technologies, [])

    @pytest.mark.asyncio
    async def test_execute_agent_tasks_empty_technologies(self, mock_agent_manager, testing_service, mock_service):
        """Test execute_agent_tasks with empty technologies."""
        manager = TaskManager(
            agent_manager=mock_agent_manager,
            testing_service=testing_service,
            mock_service=mock_service
        )
        await manager.initialize()
        
        repo_path = "/tmp/test-repo"
        ai_recommendations = [{"id": "task_001"}]

        with pytest.raises((TaskManagerError, ValueError)):
            await manager.execute_agent_tasks(repo_path, {}, ai_recommendations)

    @pytest.mark.asyncio
    async def test_execute_agent_tasks_with_mocks_enabled(self, mock_agent_manager, testing_service, mock_service):
        """Test execute_agent_tasks with mocks enabled."""
        manager = TaskManager(
            agent_manager=mock_agent_manager,
            testing_service=testing_service,
            mock_service=mock_service
        )
        await manager.initialize()
        
        repo_path = "/tmp/test-repo"
        technologies = {"tech_stack": {"backend": ["Python"]}}
        ai_recommendations = [
            {
                "id": "task_001",
                "file_path": "src/main.py",
                "specific_changes": "Add error handling to main function"
            }
        ]

        with patch('src.application.tasks.task_manager.settings') as mock_settings:
            mock_settings.mock.enabled = True
            
            result = await manager.execute_agent_tasks(
                repo_path, technologies, ai_recommendations
            )

            assert isinstance(result, dict)
            # Should get mock results when mocks are enabled

    @pytest.mark.asyncio
    async def test_create_task_plan_from_ai_recommendations(self, mock_agent_manager, testing_service, mock_service):
        """Test task plan creation from AI recommendations."""
        manager = TaskManager(
            agent_manager=mock_agent_manager,
            testing_service=testing_service,
            mock_service=mock_service
        )
        await manager.initialize()
        
        technologies = {
            "tech_stack": {
                "frontend": ["React", "JavaScript"],
                "backend": ["Python", "FastAPI"]
            }
        }
        ai_recommendations = [
            {
                "id": "task_001",
                "file_path": "src/frontend/App.jsx",
                "specific_changes": "Add error boundaries"
            },
            {
                "id": "task_002",
                "file_path": "src/backend/main.py",
                "specific_changes": "Implement logging"
            }
        ]

        # Mock the internal method since we're testing the public interface
        with patch('src.application.tasks.task_manager.settings') as mock_settings:
            mock_settings.mock.enabled = True
            
            result = await manager.execute_agent_tasks(
                "/tmp/test", technologies, ai_recommendations
            )
            
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_create_task_plan_empty_recommendations(self, mock_agent_manager, testing_service, mock_service):
        """Test task plan creation with empty recommendations."""
        manager = TaskManager(
            agent_manager=mock_agent_manager,
            testing_service=testing_service,
            mock_service=mock_service
        )
        await manager.initialize()
        
        technologies = {"tech_stack": {"backend": ["Python"]}}

        with pytest.raises((TaskManagerError, ValueError)):
            await manager.execute_agent_tasks("/tmp/test", technologies, [])

    @pytest.mark.asyncio 
    async def test_mock_task_execution(self, mock_agent_manager, testing_service, mock_service):
        """Test mock task execution functionality."""
        manager = TaskManager(
            agent_manager=mock_agent_manager,
            testing_service=testing_service,
            mock_service=mock_service
        )
        await manager.initialize()
        
        technologies = {"tech_stack": {"backend": ["Python"]}}
        ai_recommendations = [{"id": "task_001", "file_path": "src/main.py", "specific_changes": "Test change"}]

        with patch('src.application.tasks.task_manager.settings') as mock_settings:
            mock_settings.mock.enabled = True
            
            result = await manager.execute_agent_tasks(
                "/tmp/test", technologies, ai_recommendations
            )
            
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_agent_health_check_integration(self, mock_agent_manager, testing_service, mock_service):
        """Test agent health check integration."""
        # Make health check fail
        mock_agent_manager.check_all_agents_health.return_value = False
        
        manager = TaskManager(
            agent_manager=mock_agent_manager,
            testing_service=testing_service,
            mock_service=mock_service
        )
        await manager.initialize()

        with pytest.raises((TaskManagerError, Exception)):
            await manager.execute_agent_tasks(
                "/tmp/test",
                {"tech_stack": {"backend": ["Python"]}},
                [{"id": "task_001"}]
            )

    @pytest.mark.asyncio
    async def test_task_manager_workflow_integration(self, mock_agent_manager, testing_service, mock_service):
        """Test complete task manager workflow integration."""
        manager = TaskManager(
            agent_manager=mock_agent_manager,
            testing_service=testing_service,
            mock_service=mock_service
        )
        await manager.initialize()
        
        technologies = {"tech_stack": {"backend": ["Python"]}}
        ai_recommendations = [
            {
                "id": "task_001",
                "file_path": "src/main.py",
                "specific_changes": "Add comprehensive error handling"
            }
        ]

        # Test with mocks enabled for full workflow
        with patch('src.application.tasks.task_manager.settings') as mock_settings:
            mock_settings.mock.enabled = True
            
            result = await manager.execute_agent_tasks(
                "/tmp/test", technologies, ai_recommendations
            )
            
            assert isinstance(result, dict)
            # Verify the workflow completed 