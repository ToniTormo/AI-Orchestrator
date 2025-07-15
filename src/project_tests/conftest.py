"""
Global pytest configuration and shared fixtures for the testing suite

OPTIMIZED FIXTURE USAGE:
=========================
This conftest.py provides shared fixtures to reduce code duplication across tests.
Tests should use these fixtures when possible instead of creating their own instances.

AVAILABLE FIXTURES:
===================
• Basic Fixtures: temp_dir, project_root, project_src_path, sample_py_files, actual_py_files
• Model Fixtures: valid_context_input, valid_repository_analysis, valid_viability_analysis, valid_task_execution_results  
• Service Fixtures: mock_service, mock_openai_service, mock_git_service, analysis_service, integrated_mocks
• Integration Fixtures: project_coordinator, agent_analyzer, task_manager, testing_service
• Configuration: patch_settings, event_loop, async_test_wrapper

USAGE EXAMPLES:
===============
# Instead of creating fixtures in each test file:
@pytest.fixture
def analysis_service(self):
    return AnalysisService()

# Use the shared fixture from conftest:
def test_something(self, analysis_service):  # Fixture auto-injected
    assert analysis_service is not None

# Tests can run individually or as part of the suite
# pytest src/project_tests/unit/test_models.py::TestClass::test_method
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Generator
from unittest.mock import Mock, AsyncMock

# Import project components
from src.config import settings
from src.infrastructure.mocks.mock_service import MockService
from src.infrastructure.mocks.mock_openai import MockOpenAIService
from src.infrastructure.git.git_service import GitService
from src.application.analysis.analysis_service import AnalysisService
from src.application.project_coordinator import ProjectCoordinator
from src.application.agents.agent_analyzer import AgentAnalyzer
from src.application.tasks.task_manager import TaskManager
from src.application.services.agent_manager import AgentManager
from infrastructure.execution_tests.test_service import AutomatedTestingService
from src.domain.models.project_details_model import (
    ContextCreationInput, RepositoryAnalysisResult, 
    ViabilityAnalysisResult, TaskExecutionResults
)
# Configure pytest-asyncio
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# ==================== BASIC FIXTURES ====================

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)

@pytest.fixture
def project_root():
    """Get the root path of the current project."""
    return Path(".")

@pytest.fixture
def project_src_path():
    """Get the src directory path."""
    return Path("src")

@pytest.fixture
def project_config_file():
    """Get config file path."""
    return Path("src/config.py")

@pytest.fixture
def sample_py_files():
    """Get list of Python files to test analysis on."""
    return [
        "src/main.py",
        "src/config.py",
        "src/application/project_coordinator.py",
        "src/infrastructure/git/git_service.py",
        "src/application/analysis/analysis_service.py"
    ]

@pytest.fixture
def actual_py_files(project_root):
    """Get actual Python files that exist in the project."""
    py_files = list(project_root.glob("**/*.py"))
    return [str(f) for f in py_files if not str(f).startswith('.') and 'test' not in str(f)]

@pytest.fixture
def real_project_structure(project_root):
    """Get real project structure for testing."""
    py_files = list(project_root.glob("**/*.py"))
    directories = list(set([str(f.parent) for f in py_files if f.parent != Path('.')]))
    
    mock_structure = Mock()
    mock_structure.name = "AI-Orchestrator"
    mock_structure.files = [str(f) for f in py_files[:20]]  # Limit for performance
    mock_structure.directories = directories[:15]  # Limit for performance
    
    return mock_structure

# ==================== MODEL FIXTURES ====================

@pytest.fixture
def valid_context_input():
    """Valid ContextCreationInput for testing."""
    return ContextCreationInput(
        repo_url="https://github.com/test/repo.git",
        branch="main",
        description="Test description with more than 10 characters",
        email="test@example.com",
        repos_path="/tmp/repos"
    )

@pytest.fixture  
def valid_repository_analysis():
    """Valid RepositoryAnalysisResult for testing."""
    return RepositoryAnalysisResult(
        repo_path="/tmp/test-repo",
        structure={
            "name": "test-repo",
            "files": ["README.md", "src/main.py"],
            "directories": ["src"],
            "total_files": 2,
            "total_directories": 1
        },
        complexity_score=0.6,
        technologies={"languages": ["Python"], "frameworks": ["FastAPI"]},
        estimated_hours=24
    )

@pytest.fixture
def valid_viability_analysis():
    """Valid ViabilityAnalysisResult for testing."""
    return ViabilityAnalysisResult(
        is_viable=True,
        confidence_score=85.5,
        reasoning="Project is technically feasible",
        tasks_steps=[
            {"id": "task_001", "description": "Update API endpoints"}
        ]
    )

@pytest.fixture
def valid_task_execution_results():
    """Valid TaskExecutionResults for testing."""
    return TaskExecutionResults(
        tasks_completed=3,
        total_tasks=3,
        success_rate=100.0,
        test_results={
            "all_passed": True,
            "results": {"frontend": {"passed": 2, "failed": 0}}
        },
        changes_summary="Successfully implemented all requested changes"
    )

# ==================== SERVICE FIXTURES ====================

@pytest.fixture
def mock_service(patch_settings):
    """Mock service instance with settings patched."""
    return MockService()

@pytest.fixture
def integrated_mocks(mock_service, mock_openai_service):
    """Integrate all mock services together."""
    return {
        'mock_service': mock_service,
        'openai_service': mock_openai_service
    }

@pytest.fixture
def mock_openai_service():
    """Real mock OpenAI service from infrastructure layer."""
    return MockOpenAIService()

@pytest.fixture
def mock_git_service():
    """Mock Git service."""
    mock = AsyncMock(spec=GitService)
    mock.clone_repository.return_value = "/tmp/test-repo"
    mock.analyze_repository_structure.return_value = Mock(
        name="test-repo",
        files=["README.md", "src/main.py"],
        directories=["src"]
    )
    return mock

@pytest.fixture
def analysis_service():
    """Analysis service instance."""
    return AnalysisService()

@pytest.fixture
def agent_analyzer(mock_openai_service):
    """Agent analyzer mock for testing."""
    agent = AsyncMock(spec=AgentAnalyzer)
    agent.initialize.return_value = None
    agent.openai_service = mock_openai_service
    return agent

@pytest.fixture
def mock_agent_manager():
    """Mock agent manager."""
    mock = AsyncMock(spec=AgentManager)
    mock.check_all_agents_health.return_value = True
    mock.agents = {"frontend": Mock(), "backend": Mock()}
    mock.initialize.return_value = None  # Mock async method
    return mock

@pytest.fixture
def task_manager(mock_agent_manager, testing_service, mock_service):
    """Create TaskManager mock for testing."""
    manager = AsyncMock(spec=TaskManager)
    manager.agent_manager = mock_agent_manager
    manager.testing_service = testing_service
    manager.mock_service = mock_service
    manager.initialize.return_value = None
    manager.shutdown.return_value = None
    return manager

@pytest.fixture
def testing_service():
    """Create AutomatedTestingService mock for testing."""
    service = AsyncMock(spec=AutomatedTestingService)
    service.initialize.return_value = None
    service.shutdown.return_value = None
    return service

# ==================== INTEGRATION FIXTURES ====================

@pytest.fixture
def project_coordinator():
    """Create ProjectCoordinator instance for testing."""
    return ProjectCoordinator()

@pytest.fixture  
def patch_settings():
    """Patch settings to enable mock mode for testing."""
    original_mock_enabled = settings.mock.enabled
    settings.mock.enabled = True
    yield settings
    settings.mock.enabled = original_mock_enabled

# ==================== HELPERS ====================

@pytest.fixture
def async_test_wrapper():
    """Helper for running async functions in tests."""
    def _wrapper(async_func, *args, **kwargs):
        return asyncio.run(async_func(*args, **kwargs))
    return _wrapper

# ==================== MARKERS ====================

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "mock: mark test as using mocks") 