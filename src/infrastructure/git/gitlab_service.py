"""
GitLab Service

Service for GitLab-specific operations including merge request creation.
Uses clean code principles and Pydantic validation.
"""

import requests
from typing import Dict, Optional

from src.config import settings
from src.utils.logging import setup_logger
from src.utils.exceptions_control import create_error, GitServiceError
from src.infrastructure.mocks.mock_service import MockService
from src.domain.models import GitLabMergeRequestInput, GitAuthUrlInput

class GitLabService:
    """Helper service for GitLab-specific operations"""

    def __init__(self, mock_service: Optional[MockService] = None):
        """
        Initialize the GitLab service
        
        Args:
            mock_service: Optional mock service for testing
        """
        # Initialize logging with centralized configuration
        self.logger = setup_logger(
            "gitlab_service",
            settings.logging.module_levels.get("gitlab_service", settings.logging.level)
        )
        
        self.gitlab_token = settings.gitlab.api_token
        self.mock_service = mock_service or MockService()
        self.logger.info("[GitLabService] Initialized")

    # PRIMARY OPERATION 1: Create merge request
    async def create_merge_request(self, repo_url: str, source_branch: str, target_branch: str, title: str, description: str) -> Dict:
        """
        Create a merge request on GitLab
        
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
        mr_input = GitLabMergeRequestInput(
            repo_url=repo_url,
            source_branch=source_branch,
            target_branch=target_branch,
            title=title,
            description=description
        )

        try:
            if self.mock_service.is_enabled():
                self.logger.info("[GitLabService] Mock mode: Simulating successful merge request creation")
                return self.mock_service.get_mock_merge_request(mr_input.title, mr_input.description)
                
            if not self.gitlab_token:
                raise create_error(GitServiceError, "GitLab token not configured", "GitLabService")
            
            self.logger.info(f"[GitLabService] Creating merge request for: {mr_input.repo_url}")
            self.logger.info(f"[GitLabService] Source branch: {mr_input.source_branch}, Target branch: {mr_input.target_branch}")
            
            # Extract project path from URL
            project_path = self._extract_project_path(str(mr_input.repo_url))
            self.logger.info(f"[GitLabService] Extracted project path: {project_path}")
                
            # Create merge request using GitLab API
            headers = {
                "PRIVATE-TOKEN": self.gitlab_token,
                "Content-Type": "application/json"
            }
            
            data = {
                "source_branch": mr_input.source_branch,
                "target_branch": mr_input.target_branch,
                "title": mr_input.title,
                "description": mr_input.description
            }
            
            api_url = f"https://gitlab.com/api/v4/projects/{project_path.replace('/', '%2F')}/merge_requests"
            self.logger.info(f"[GitLabService] Making API call to: {api_url}")
            self.logger.debug(f"[GitLabService] Request data: {data}")
            
            response = requests.post(api_url, headers=headers, json=data)
            
            self.logger.info(f"[GitLabService] API Response status: {response.status_code}")
            self.logger.debug(f"[GitLabService] API Response headers: {dict(response.headers)}")
            
            if response.status_code == 201:
                result = response.json()
                self.logger.info(f"[GitLabService] Merge request created successfully: {result.get('web_url', 'No URL')}")
                return result
            else:
                self._handle_api_error(response, project_path)
                
        except Exception as e:
            raise create_error(GitServiceError, f"Failed to create merge request: {str(e)}", "GitLabService")

    # Helper methods for create_merge_request
    def _extract_project_path(self, repo_url: str) -> str:
        """
        Extract project path from repository URL, handling both clean and authenticated URLs
        
        Args:
            repo_url: Repository URL
            
        Returns:
            Project path for GitLab API
        """
        try:
            # Handle authenticated URLs like: https://oauth2:token@gitlab.com/user/repo.git
            if "@gitlab.com/" in repo_url:
                # Extract the part after @gitlab.com/
                parts = repo_url.split("@gitlab.com/")
                if len(parts) == 2:
                    project_path = parts[1].replace(".git", "")
                    self.logger.debug(f"[GitLabService] Extracted from authenticated URL: {project_path}")
                    return project_path
            
            # Handle clean URLs like: https://gitlab.com/user/repo.git
            if "gitlab.com/" in repo_url:
                project_path = repo_url.split("gitlab.com/")[1].replace(".git", "")
                self.logger.debug(f"[GitLabService] Extracted from clean URL: {project_path}")
                return project_path
            
            raise create_error(GitServiceError, f"Cannot extract project path from URL: {repo_url}", "GitLabService")
            
        except Exception as e:
            raise create_error(GitServiceError, f"Error extracting project path: {str(e)}", "GitLabService")

    def _handle_api_error(self, response: requests.Response, project_path: str) -> None:
        """
        Handle GitLab API error responses
        
        Args:
            response: HTTP response from GitLab API
            project_path: Project path for context in error messages
        """
        error_details = f"Status: {response.status_code}, Response: {response.text}"
        self.logger.error(f"[GitLabService] Failed to create merge request: {error_details}")
        
        # Check for specific error cases
        if response.status_code == 401:
            error_msg = "Authentication failed - check your GitLab token"
        elif response.status_code == 403:
            error_msg = "Permission denied - check your GitLab token permissions"
        elif response.status_code == 404:
            error_msg = f"Project not found - check project path: {project_path}"
        elif response.status_code == 409:
            error_msg = "Merge request may already exist"
        else:
            error_msg = f"Failed to create merge request: {error_details}"
        
        raise create_error(GitServiceError, error_msg, "GitLabService")

    # PRIMARY OPERATION 2: Get authentication URL
    async def get_auth_url(self, url: str) -> str:
        """
        Get authenticated URL for GitLab repository
        
        Args:
            url: Original repository URL
            
        Returns:
            Authenticated URL
        """
        # Validate input using Pydantic model
        auth_input = GitAuthUrlInput(url=url)

        try:
            if not self.gitlab_token:
                raise create_error(GitServiceError, "GitLab token not configured", "GitLabService")
                
            # Replace https:// with https://oauth2:{token}@
            auth_url = str(auth_input.url).replace("https://", f"https://oauth2:{self.gitlab_token}@")
            self.logger.debug(f"[GitLabService] Generated authenticated URL for GitLab repository")
            return auth_url
            
        except Exception as e:
            raise create_error(GitServiceError, f"Failed to get authenticated URL: {str(e)}", "GitLabService") 