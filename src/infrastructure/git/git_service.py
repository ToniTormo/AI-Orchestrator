"""
Git Service

Manages Git operations including cloning, branching, committing, and merge requests.
Uses hexagonal architecture principles for clean separation of concerns.
"""

import os
from typing import Optional, Dict
from pathlib import Path
from git import Repo

from src.config import settings
from src.utils.logging import setup_logger
from src.utils.exceptions_control import create_error, GitServiceError

from src.infrastructure.mocks.mock_service import MockService
from src.infrastructure.git.github_service import GitHubService
from src.infrastructure.git.gitlab_service import GitLabService
from src.infrastructure.git.file_exclusion import FileExclusion

from src.domain.models import (
    GitCloneInput,
    GitBranchInput,
    GitCommitInput,
    GitPushInput,
    GitMergeRequestInput,
    GitRepositoryStructure,
    GitMergeRequestResult
)

class GitService:
    """
    Git service for repository management operations
    """

    def __init__(self, base_path: str = "src/infrastructure/repositories", mock_service: Optional[MockService] = None):
        """Initialize GitService with configuration"""
        self.logger = setup_logger(
            "git_service",
            settings.logging.module_levels.get("git_service", settings.logging.level)
        )
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.current_repo_path: Optional[str] = None
        self.mock_service = mock_service or MockService()
        
        # Initialize platform-specific services
        self.github_service = GitHubService(mock_service)
        self.gitlab_service = GitLabService(mock_service)
        
        self.logger.info(f"[GitService] Initialized with base path: {self.base_path}")

    # PRIMARY OPERATION 1: Clone repository
    async def clone_repository(self, url: str, branch: Optional[str] = None) -> str:
        """
        Clone a Git repository or pull latest changes if it already exists
        
        Args:
            url: Repository URL
            branch: Branch to clone (optional)
            
        Returns:
            Path to cloned repository
        """
        # Validate input using Pydantic model
        clone_input = GitCloneInput(url=url, branch=branch)

        try:
            # Generate repository name from URL
            repo_name = str(clone_input.url).split("/")[-1].replace(".git", "")
            repo_path = self.base_path / repo_name
            
            # Check if a valid repository exists
            is_valid_repo = False
            if repo_path.exists():
                Repo(repo_path)
                is_valid_repo = True

            if is_valid_repo:
                await self._update_existing_repository(repo_path, str(clone_input.url), clone_input.branch)
            else:
                await self._clone_new_repository(repo_path, str(clone_input.url), clone_input.branch)
            
            # Store current repository path
            self.current_repo_path = str(repo_path)
            
            self.logger.info(f"[GitService] Repository ready at: {repo_path}")
            return str(repo_path)
            
        except Exception as e:
            raise create_error(GitServiceError, f"Repository operation failed: {str(e)}", "GitService")

    # Helper methods for clone_repository
    async def _update_existing_repository(self, repo_path: Path, url: str, branch: Optional[str] = None) -> Repo:
        """
        Update existing repository to latest changes
        
        Args:
            repo_path: Path to existing repository
            url: Repository URL
            branch: Branch to checkout (optional)
            
        Returns:
            Updated repository object
        """
        try:
            self.logger.info(f"[GitService] Updating existing repository at: {repo_path}")
            repo = Repo(repo_path)
            
            # Use bash for git commands
            git = repo.git
            git.update_environment(GIT_SSH_COMMAND='bash')
            
            # Fetch latest changes
            git.fetch('origin')
            
            # Checkout specified branch or stay on current
            if branch:
                try:
                    git.checkout(branch)
                except Exception:
                    # Branch might not exist locally, try to create it from origin
                    git.checkout(b=branch, track=f'origin/{branch}')
            
            # Pull latest changes
            git.pull()
            
            self.logger.info(f"[GitService] Successfully updated repository")
            return repo
            
        except Exception as e:
            raise create_error(GitServiceError, f"Failed to update repository: {str(e)}", "GitService")

    async def _clone_new_repository(self, repo_path: Path, url: str, branch: Optional[str] = None) -> Repo:
        """
        Clone a new repository
        
        Args:
            repo_path: Path where repository should be cloned
            url: Repository URL
            branch: Branch to clone (optional)
            
        Returns:
            Cloned repository object
        """
        try:
            self.logger.info(f"[GitService] Cloning repository from {url} to {repo_path}")
            
            # Get authenticated URL  
            if "github.com" in url:
                auth_url = await self.github_service.get_auth_url(url)
            elif "gitlab.com" in url:
                auth_url = await self.gitlab_service.get_auth_url(url)
            else:
                auth_url = url
            
            # Clone repository
            clone_kwargs = {}
            if branch:
                clone_kwargs['branch'] = branch
                
            repo = Repo.clone_from(auth_url, repo_path, **clone_kwargs)
            
            self.logger.info(f"[GitService] Successfully cloned repository")
            return repo
            
        except Exception as e:
            raise create_error(GitServiceError, f"Failed to clone repository: {str(e)}", "GitService")

    # PRIMARY OPERATION 2: Analyze repository structure
    async def analyze_repository_structure(self, directory_path: str = None) -> GitRepositoryStructure:
        """
        Analyze the structure of the current repository or a specified directory
        
        Args:
            directory_path: Optional path to analyze. If None, uses current_repo_path
        
        Returns:
            GitRepositoryStructure containing repository/directory structure information
        """
        # Use provided path or current repo path
        target_path = directory_path or self.current_repo_path
        
        if not target_path:
            raise create_error(GitServiceError, "No repository has been cloned yet and no directory path provided", "GitService")

        try:
            self.logger.info(f"[GitService] Analyzing structure at: {target_path}")
            
            if not os.path.exists(target_path):
                raise create_error(GitServiceError, f"Path not found: {target_path}", "GitService")
            
            # Initialize structure data
            structure_data = {
                "name": os.path.basename(target_path),
                "files": [],
                "directories": []
            }
            
            # Try to get Git info if it's a Git repository
            if os.path.exists(os.path.join(target_path, '.git')):
                try:
                    repo = Repo(target_path)
                    structure_data.update({
                        "branch": repo.active_branch.name,
                        "commit": repo.head.commit.hexsha,
                        "remote_url": repo.remotes.origin.url if repo.remotes else None
                    })
                except Exception:
                    # Not a valid Git repo, continue without Git info
                    pass
            
            # Get .gitignore patterns and analyze structure
            gitignore_patterns = FileExclusion.get_gitignore_patterns(target_path)
            
            for root, dirs, files in os.walk(target_path):
                # Get relative path
                rel_path = os.path.relpath(root, target_path)
                if rel_path == ".":
                    rel_path = ""
                
                # Filter directories
                dirs[:] = [d for d in dirs if not FileExclusion.should_exclude(os.path.join(rel_path, d), gitignore_patterns)]
                
                # Add valid directories
                for dir_name in dirs:
                    dir_path = os.path.join(rel_path, dir_name)
                    structure_data["directories"].append(dir_path)
                
                # Add valid files
                for file_name in files:
                    file_path = os.path.join(rel_path, file_name)
                    if not FileExclusion.should_exclude(file_path, gitignore_patterns):
                        structure_data["files"].append(file_path)
            
            # Create and validate structure using Pydantic model
            structure = GitRepositoryStructure(**structure_data)
            
            self.logger.info(f"[GitService] Found {len(structure.files)} files and {len(structure.directories)} directories")
            return structure
            
        except Exception as e:
            raise create_error(GitServiceError, f"Error analyzing structure: {str(e)}", "GitService")

    # PRIMARY OPERATION 3: Create branch
    async def create_branch(self, repo_path: str, branch_name: str) -> bool:
        """
        Create a new branch in the repository
        
        Args:
            repo_path: Path to repository
            branch_name: Name of new branch
            
        Returns:
            True if successful
        """
        # Validate input using Pydantic model
        branch_input = GitBranchInput(repo_path=repo_path, branch_name=branch_name)

        try:
            self.logger.info(f"[GitService] Creating branch '{branch_input.branch_name}' in repository: {branch_input.repo_path}")
            repo = Repo(branch_input.repo_path)
            
            # Use bash for git commands
            git = repo.git
            git.update_environment(GIT_SSH_COMMAND='bash')
            
            # Create and checkout new branch
            git.checkout(b=branch_input.branch_name)
            
            self.logger.info(f"[GitService] Successfully created and checked out branch: {branch_input.branch_name}")
            return True
            
        except Exception as e:
            raise create_error(GitServiceError, f"Failed to create branch: {str(e)}", "GitService")

    # PRIMARY OPERATION 4: Commit changes
    async def commit_changes(self, repo_path: str, message: str) -> bool:
        """
        Commit changes in the repository
        
        Args:
            repo_path: Path to the repository
            message: Commit message
            
        Returns:
            True if successful
        """
        # Validate input using Pydantic model
        commit_input = GitCommitInput(repo_path=repo_path, message=message)

        try:
            self.logger.info(f"[GitService] Committing changes in {commit_input.repo_path}")
            
            if self.mock_service.is_enabled():
                self.logger.info("[GitService] Mock mode: Simulating successful commit")
                return self.mock_service.get_mock_commit_result()
                
            repo = Repo(commit_input.repo_path)
            
            # Use bash for git commands
            git = repo.git
            git.update_environment(GIT_SSH_COMMAND='bash')
            
            # Check if there are changes to commit
            status = git.status()
            if "nothing to commit" in status:
                self.logger.info("[GitService] No changes to commit")
                return True
            
            # Add all changes
            git.add(A=True)
            
            # Commit changes
            git.commit(m=commit_input.message)
            
            self.logger.info(f"[GitService] Successfully committed changes")
            return True
        except Exception as e:
            raise create_error(GitServiceError, f"Failed to commit changes: {str(e)}", "GitService")

    # PRIMARY OPERATION 5: Push changes
    async def push_changes(self, repo_path: str, branch: str) -> bool:
        """
        Push changes to remote repository
        
        Args:
            repo_path: Path to the repository
            branch: Branch to push to
            
        Returns:
            True if successful
        """
        # Validate input using Pydantic model
        push_input = GitPushInput(repo_path=repo_path, branch=branch)

        try:
            self.logger.info(f"[GitService] Pushing changes to branch {push_input.branch} in {push_input.repo_path}")
            
            if self.mock_service.is_enabled():
                self.logger.info("[GitService] Mock mode: Simulating successful push")
                return self.mock_service.get_mock_push_result()
                
            repo = Repo(push_input.repo_path)
            
            # Use bash for git commands
            git = repo.git
            git.update_environment(GIT_SSH_COMMAND='bash')
            
            # Push changes
            git.push('origin', push_input.branch)
            
            self.logger.info(f"[GitService] Successfully pushed changes to branch {push_input.branch}")
            return True
        except Exception as e:
            raise create_error(GitServiceError, f"Failed to push changes: {str(e)}", "GitService")

    # PRIMARY OPERATION 6: Create merge request workflow
    async def create_merge_request_with_changes(
        self, 
        repo_path: str,
        repo_url: str,
        feature_branch: str, 
        target_branch: str, 
        commit_message: str, 
        description: str
    ) -> GitMergeRequestResult:
        """
        Complete workflow: commit changes, push, and create merge request
        
        Args:
            repo_path: Path to the repository
            repo_url: The remote URL of the repository for the merge request.
            feature_branch: Source branch name
            target_branch: Target branch name
            commit_message: Commit message
            description: PR/MR description
            
        Returns:
            GitMergeRequestResult containing status and URL
        """
        # Validate input using Pydantic model
        mr_input = GitMergeRequestInput(
            repo_path=repo_path,
            feature_branch=feature_branch,
            target_branch=target_branch,
            commit_message=commit_message,
            description=description
        )

        try:
            # 1. Commit changes
            self.logger.info(f"[GitService] Starting merge request workflow for branch {mr_input.feature_branch}")
            await self.commit_changes(mr_input.repo_path, mr_input.commit_message)
            
            # 2. Push changes
            await self.push_changes(mr_input.repo_path, mr_input.feature_branch)
            
            # 3. Create merge request using the provided repo_url
            mr_result = await self._create_platform_merge_request(
                repo_url=repo_url,
                source_branch=mr_input.feature_branch,
                target_branch=mr_input.target_branch,
                title=mr_input.commit_message,
                description=mr_input.description
            )
            
            # 4. Handle result
            if "html_url" in mr_result:
                self.logger.info(f"[GitService] Merge request created: {mr_result['html_url']}")
                return GitMergeRequestResult(status="created", url=mr_result["html_url"])
            elif "web_url" in mr_result:
                self.logger.info(f"[GitService] Merge request created: {mr_result['web_url']}")
                return GitMergeRequestResult(status="created", url=mr_result["web_url"])
            
            raise create_error(GitServiceError, "No merge request URL returned from platform", "GitService")
                
        except Exception as e:
            # Handle specific error patterns
            error_str = str(e).lower()
            if "no commits between" in error_str or "no changes" in error_str:
                self.logger.info("[GitService] No changes to create pull request for")
                return GitMergeRequestResult(status="no_changes", url=None)
            elif "pull request already exists" in error_str or "already exists" in error_str:
                self.logger.info("[GitService] Pull request already exists")
                return GitMergeRequestResult(status="already_exists", url=None)
            
            self.logger.error(f"[GitService] Failed to create merge request: {e}")
            return GitMergeRequestResult(status="failed", url=None)

    # Helper method for create_merge_request_with_changes
    async def _create_platform_merge_request(self, repo_url: str, source_branch: str, target_branch: str, title: str, description: str) -> Dict:
        """
        Create merge request on the appropriate platform (GitHub/GitLab)
        
        Args:
            repo_url: Repository URL
            source_branch: Source branch
            target_branch: Target branch  
            title: MR/PR title
            description: MR/PR description
            
        Returns:
            Platform response with merge request details
        """
        try:
            if "github.com" in repo_url:
                return await self.github_service.create_merge_request(
                    repo_url=repo_url,
                    source_branch=source_branch,
                    target_branch=target_branch,
                    title=title,
                    description=description
                )
            elif "gitlab.com" in repo_url:
                return await self.gitlab_service.create_merge_request(
                    repo_url=repo_url,
                    source_branch=source_branch,
                    target_branch=target_branch,
                    title=title,
                    description=description
                )
            else:
                raise create_error(GitServiceError, f"Unsupported Git platform for URL: {repo_url}", "GitService")
                
        except Exception as e:
            raise create_error(GitServiceError, f"Failed to create platform merge request: {str(e)}", "GitService")