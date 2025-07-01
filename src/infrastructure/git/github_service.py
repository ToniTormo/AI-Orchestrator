"""
GitHub Service

Service for GitHub-specific operations including pull request creation.
Uses clean code principles and Pydantic validation.
"""

import requests
from typing import Dict, Optional

from src.config import settings
from src.utils.logging import setup_logger
from src.utils.exceptions_control import create_error, GitServiceError
from src.infrastructure.mocks.mock_service import MockService
from src.domain.models import GitHubPullRequestInput, GitAuthUrlInput

class GitHubService:
    """Helper service for GitHub-specific operations"""

    def __init__(self, mock_service: Optional[MockService] = None):
        """
        Initialize the GitHub service
        
        Args:
            mock_service: Optional mock service for testing
        """
        # Initialize logging with centralized configuration
        self.logger = setup_logger(
            "github_service",
            settings.logging.module_levels.get("github_service", settings.logging.level)
        )
        
        self.github_token = settings.github.api_token
        self.mock_service = mock_service or MockService()
        self.logger.info("[GitHubService] Initialized")

    # PRIMARY OPERATION 1: Create merge request
    async def create_merge_request(self, repo_url: str, source_branch: str, target_branch: str, title: str, description: str) -> Dict:
        """
        Create a merge request (pull request) on GitHub
        
        Args:
            repo_url: Repository URL
            source_branch: Source branch
            target_branch: Target branch
            title: Merge request title
            description: Merge request description
            
        Returns:
            Merge request information
        """
        # Validate input using Pydantic model
        pr_input = GitHubPullRequestInput(
            repo_url=repo_url,
            source_branch=source_branch,
            target_branch=target_branch,
            title=title,
            description=description
        )

        try:
            if self.mock_service.is_enabled():
                self.logger.info("[GitHubService] Mock mode: Simulating successful merge request creation")
                return self.mock_service.get_mock_merge_request(pr_input.title, pr_input.description)
                
            if not self.github_token:
                raise create_error(GitServiceError, "GitHub token not configured", "GitHubService")
                
            # Extract owner and repo from URL
            owner, repo = self._extract_repo_info(str(pr_input.repo_url))
            
            self.logger.info(f"[GitHubService] Creating merge request for {owner}/{repo}: {pr_input.source_branch} -> {pr_input.target_branch}")
            
            # Create merge request using GitHub API (pull request)
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            data = {
                "title": pr_input.title,
                "body": pr_input.description,
                "head": pr_input.source_branch,
                "base": pr_input.target_branch
            }
            
            url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 201:
                result = response.json()
                self.logger.info(f"[GitHubService] Merge request created successfully: {result.get('html_url', 'No URL')}")
                return result
            else:
                self._handle_api_error(response)
                
        except Exception as e:
            raise create_error(GitServiceError, f"Failed to create merge request: {str(e)}", "GitHubService")

    # Helper methods for create_merge_request
    def _extract_repo_info(self, repo_url: str) -> tuple[str, str]:
        """
        Extract owner and repository name from GitHub URL
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            Tuple of (owner, repo)
        """
        try:
            # Remove GitHub base URL and split
            parts = repo_url.replace("https://github.com/", "").split("/")
            if len(parts) != 2:
                raise create_error(GitServiceError, "Invalid GitHub repository URL format", "GitHubService")
                
            owner, repo = parts
            repo = repo.replace(".git", "")
            
            return owner, repo
            
        except Exception as e:
            raise create_error(GitServiceError, f"Failed to extract repository info: {str(e)}", "GitHubService")

    def _handle_api_error(self, response: requests.Response) -> None:
        """
        Handle GitHub API error responses
        
        Args:
            response: HTTP response from GitHub API
        """
        error_details = f"Status: {response.status_code}, Response: {response.text}"
        self.logger.error(f"[GitHubService] Failed to create merge request: {error_details}")
        
        # Check for specific error cases
        if response.status_code == 401:
            error_msg = "Authentication failed - check your GitHub token"
        elif response.status_code == 403:
            error_msg = "Permission denied - check your GitHub token permissions"
        elif response.status_code == 404:
            error_msg = f"Repository not found - check repository URL"
        elif response.status_code == 422:
            error_msg = "Validation failed - check branch names and parameters"
        else:
            error_msg = f"Failed to create merge request: {error_details}"
        
        raise create_error(GitServiceError, error_msg, "GitHubService")

    # PRIMARY OPERATION 2: Get authentication URL
    async def get_auth_url(self, url: str) -> str:
        """
        Get authenticated URL for GitHub repository
        
        Args:
            url: Original repository URL
            
        Returns:
            Authenticated URL
        """
        # Validate input using Pydantic model
        auth_input = GitAuthUrlInput(url=url)

        try:
            if not self.github_token:
                raise create_error(GitServiceError, "GitHub token not configured", "GitHubService")
                
            # Replace https:// with https://{token}@
            auth_url = str(auth_input.url).replace("https://", f"https://{self.github_token}@")
            self.logger.debug(f"[GitHubService] Generated authenticated URL for GitHub repository")
            return auth_url
            
        except Exception as e:
            raise create_error(GitServiceError, f"Failed to get authenticated URL: {str(e)}", "GitHubService") 