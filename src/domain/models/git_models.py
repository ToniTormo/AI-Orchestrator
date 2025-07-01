"""
Git Models

Pydantic models for Git operations validation
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, HttpUrl
from src.utils.exceptions_control import create_error, ValidationError

# Helper validator functions for reuse
def validate_repo_path(v: str, model_name: str) -> str:
    """Common validator for repository paths"""
    v = v.strip()
    if not v:
        raise create_error(ValidationError, "Repository path cannot be empty", model_name)
    return v

def validate_branch_name(v: str, model_name: str) -> str:
    """Common validator for branch names"""
    v = v.strip()
    if not v:
        raise create_error(ValidationError, "Branch name cannot be empty", model_name)
    if v.startswith('-'):
        raise create_error(ValidationError, "Branch name cannot start with hyphen", model_name)
    return v

def validate_commit_message(v: str, model_name: str) -> str:
    """Common validator for commit messages"""
    v = v.strip()
    if not v:
        raise create_error(ValidationError, "Commit message cannot be empty", model_name)
    if len(v) < 3:
        raise create_error(ValidationError, "Commit message must be at least 3 characters long", model_name)
    return v

def validate_git_platform_url(v: HttpUrl, model_name: str) -> HttpUrl:
    """Common validator for Git platform URLs"""
    url_str = str(v)
    if not any(platform in url_str for platform in ['github.com', 'gitlab.com']):
        raise create_error(ValidationError, "Only GitHub and GitLab repositories are supported", model_name)
    return v

class GitCloneInput(BaseModel):
    """Model for validating git clone parameters"""
    url: HttpUrl = Field(..., description="Repository URL to clone")
    branch: Optional[str] = Field(None, description="Branch to clone (optional)")
    
    @field_validator('url')
    def validate_url(cls, v: HttpUrl) -> HttpUrl:
        return validate_git_platform_url(v, "GitCloneInput")
    
    @field_validator('branch')
    def validate_branch(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_branch_name(v, "GitCloneInput")
        return v

class GitBranchInput(BaseModel):
    """Model for validating git branch creation parameters"""
    repo_path: str = Field(..., min_length=1, description="Path to the repository")
    branch_name: str = Field(..., min_length=1, description="Name of the new branch")
    
    @field_validator('repo_path')
    def validate_repo_path(cls, v: str) -> str:
        return validate_repo_path(v, "GitBranchInput")
    
    @field_validator('branch_name')
    def validate_branch_name(cls, v: str) -> str:
        v = validate_branch_name(v, "GitBranchInput")
        if any(char in v for char in [' ', '\t', '\n']):
            raise create_error(ValidationError, "Branch name cannot contain whitespace", "GitBranchInput")
        return v

class GitCommitInput(BaseModel):
    """Model for validating git commit parameters"""
    repo_path: str = Field(..., min_length=1, description="Path to the repository")
    message: str = Field(..., min_length=3, description="Commit message")
    
    @field_validator('repo_path')
    def validate_repo_path(cls, v: str) -> str:
        return validate_repo_path(v, "GitCommitInput")
    
    @field_validator('message')
    def validate_message(cls, v: str) -> str:
        return validate_commit_message(v, "GitCommitInput")

class GitPushInput(BaseModel):
    """Model for validating git push parameters"""
    repo_path: str = Field(..., min_length=1, description="Path to the repository")
    branch: str = Field(..., min_length=1, description="Branch to push")
    
    @field_validator('repo_path')
    def validate_repo_path(cls, v: str) -> str:
        return validate_repo_path(v, "GitPushInput")
    
    @field_validator('branch')
    def validate_branch(cls, v: str) -> str:
        return validate_branch_name(v, "GitPushInput")

class GitMergeRequestInput(BaseModel):
    """Model for validating merge request creation parameters"""
    repo_path: str = Field(..., min_length=1, description="Path to the repository")
    feature_branch: str = Field(..., min_length=1, description="Source branch name")
    target_branch: str = Field(..., min_length=1, description="Target branch name")
    commit_message: str = Field(..., min_length=3, description="Commit message")
    description: str = Field(..., min_length=10, description="Pull/Merge request description")
    
    @field_validator('repo_path')
    def validate_repo_path(cls, v: str) -> str:
        return validate_repo_path(v, "GitMergeRequestInput")
    
    @field_validator('feature_branch', 'target_branch')
    def validate_branch(cls, v: str) -> str:
        return validate_branch_name(v, "GitMergeRequestInput")
    
    @field_validator('commit_message')
    def validate_commit_message(cls, v: str) -> str:
        return validate_commit_message(v, "GitMergeRequestInput")
    
    @field_validator('description')
    def validate_description(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise create_error(ValidationError, "Description cannot be empty", "GitMergeRequestInput")
        return v

class GitRepositoryStructure(BaseModel):
    """Model for representing repository structure"""
    name: str = Field(..., min_length=1, description="Repository name")
    files: list[str] = Field(default_factory=list, description="List of files")
    directories: list[str] = Field(default_factory=list, description="List of directories")
    branch: Optional[str] = Field(None, description="Current branch")
    commit: Optional[str] = Field(None, description="Current commit hash")
    remote_url: Optional[str] = Field(None, description="Remote repository URL")
    
    @field_validator('name')
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise create_error(ValidationError, "Repository name cannot be empty", "GitRepositoryStructure")
        return v

class GitMergeRequestResult(BaseModel):
    """Model for merge request operation result"""
    status: str = Field(..., description="Status of the operation")
    url: Optional[str] = Field(None, description="URL of the created merge request")
    
    @field_validator('status')
    def validate_status(cls, v: str) -> str:
        valid_statuses = {"created", "no_changes", "already_exists", "failed"}
        if v not in valid_statuses:
            raise create_error(ValidationError, f"Invalid status. Must be one of: {valid_statuses}", "GitMergeRequestResult")
        return v
    
    @field_validator('url')
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise create_error(ValidationError, "URL cannot be empty string", "GitMergeRequestResult")
        return v

class GitHubPullRequestInput(BaseModel):
    """Model for validating GitHub pull request creation parameters"""
    repo_url: HttpUrl = Field(..., description="GitHub repository URL")
    source_branch: str = Field(..., min_length=1, description="Source branch name")
    target_branch: str = Field(..., min_length=1, description="Target branch name")
    title: str = Field(..., min_length=3, description="Pull request title")
    description: str = Field(..., min_length=1, description="Pull request description")
    
    @field_validator('repo_url')
    def validate_github_url(cls, v: HttpUrl) -> HttpUrl:
        url_str = str(v)
        if 'github.com' not in url_str:
            raise create_error(ValidationError, "URL must be a GitHub repository", "GitHubPullRequestInput")
        return v
    
    @field_validator('source_branch', 'target_branch')
    def validate_branch(cls, v: str) -> str:
        return validate_branch_name(v, "GitHubPullRequestInput")
    
    @field_validator('title')
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise create_error(ValidationError, "Pull request title cannot be empty", "GitHubPullRequestInput")
        return v
    
    @field_validator('description')
    def validate_description(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise create_error(ValidationError, "Pull request description cannot be empty", "GitHubPullRequestInput")
        return v

class GitLabMergeRequestInput(BaseModel):
    """Model for validating GitLab merge request creation parameters"""
    repo_url: HttpUrl = Field(..., description="GitLab repository URL")
    source_branch: str = Field(..., min_length=1, description="Source branch name")
    target_branch: str = Field(..., min_length=1, description="Target branch name")
    title: str = Field(..., min_length=3, description="Merge request title")
    description: str = Field(..., min_length=1, description="Merge request description")
    
    @field_validator('repo_url')
    def validate_gitlab_url(cls, v: HttpUrl) -> HttpUrl:
        url_str = str(v)
        if 'gitlab.com' not in url_str:
            raise create_error(ValidationError, "URL must be a GitLab repository", "GitLabMergeRequestInput")
        return v
    
    @field_validator('source_branch', 'target_branch')
    def validate_branch(cls, v: str) -> str:
        return validate_branch_name(v, "GitLabMergeRequestInput")
    
    @field_validator('title')
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise create_error(ValidationError, "Merge request title cannot be empty", "GitLabMergeRequestInput")
        return v
    
    @field_validator('description')
    def validate_description(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise create_error(ValidationError, "Merge request description cannot be empty", "GitLabMergeRequestInput")
        return v

class GitAuthUrlInput(BaseModel):
    """Model for validating Git authentication URL input"""
    url: HttpUrl = Field(..., description="Repository URL to authenticate")
    
    @field_validator('url')
    def validate_url(cls, v: HttpUrl) -> HttpUrl:
        return validate_git_platform_url(v, "GitAuthUrlInput")

class FileExclusionInput(BaseModel):
    """Model for validating file exclusion check parameters"""
    path: str = Field(..., min_length=1, description="File path to check for exclusion")
    repo_path: Optional[str] = Field(None, min_length=1, description="Repository path for .gitignore patterns")
    
    @field_validator('path')
    def validate_path(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise create_error(ValidationError, "Path cannot be empty for exclusion check", "FileExclusionInput")
        return v
    
    @field_validator('repo_path')
    def validate_repo_path(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_repo_path(v, "FileExclusionInput")
        return v 