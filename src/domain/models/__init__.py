"""
Domain models package

Contains all domain models used throughout the application
"""

# Import validation models from all modules
from .project_details_model import (
    ContextCreationInput,
    RepositoryAnalysisResult,
    ViabilityAnalysisResult, 
    TaskExecutionResults
)

from .analysis_models import (
    TechStackAnalysisInput,
    AnalysisTask,
    AgentAnalyzerInput,
    AgentAnalyzerOutput
)

from .agent_model import (
    AgentType,
    AgentTask,
    AgentResult,
    AgentStatus
)

from .git_models import (
    GitCloneInput,
    GitBranchInput,
    GitCommitInput,
    GitPushInput,
    GitMergeRequestInput,
    GitRepositoryStructure,
    GitMergeRequestResult,
    GitHubPullRequestInput,
    GitLabMergeRequestInput,
    GitAuthUrlInput,
    FileExclusionInput
)

from .task_model import (
    Task
)

# Export all models
__all__ = [
    # Project models
    'ContextCreationInput',
    'RepositoryAnalysisResult', 
    'ViabilityAnalysisResult',
    'TaskExecutionResults',
    
    # Analysis models  
    'TechStackAnalysisInput',
    'AnalysisTask',
    'AgentAnalyzerInput',
    'AgentAnalyzerOutput',
    
    # Agent models
    'AgentType',
    'AgentTask',
    'AgentResult',
    'AgentStatus',
    
    # Git models
    'GitCloneInput',
    'GitBranchInput',
    'GitCommitInput',
    'GitPushInput',
    'GitMergeRequestInput',
    'GitRepositoryStructure',
    'GitMergeRequestResult',
    'GitHubPullRequestInput',
    'GitLabMergeRequestInput',
    'GitAuthUrlInput',
    'FileExclusionInput',
    
    # Task models
    'Task'
] 