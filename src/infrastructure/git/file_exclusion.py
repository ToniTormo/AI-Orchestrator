"""
File Exclusion Logic

Utility class for handling file exclusion logic in Git operations.
Uses clean code principles and Pydantic validation.
"""

import os
import fnmatch
from typing import Set

from src.config import settings
from src.utils.logging import setup_logger
from src.utils.exceptions_control import create_error, GitServiceError
from src.domain.models import FileExclusionInput
from .common_exclusions import COMMON_EXCLUSIONS

class FileExclusion:
    """Class to handle file exclusion logic for Git operations"""
    
    # PRIMARY OPERATION 1: Check if file should be excluded
    @staticmethod
    def should_exclude(path: str, gitignore_patterns: Set[str] = None) -> bool:
        """
        Check if a path should be excluded based on .gitignore patterns and common exclusions
        
        Args:
            path: Path to check
            gitignore_patterns: Set of patterns from .gitignore (optional)
            
        Returns:
            True if path should be excluded
        """
        # Validate input using Pydantic model (just for path validation)
        exclusion_input = FileExclusionInput(path=path)
        validated_path = exclusion_input.path

        try:
            # Check against common exclusions
            if FileExclusion._matches_common_exclusions(validated_path):
                return True
                    
            # Check against .gitignore patterns if provided
            if gitignore_patterns:
                if FileExclusion._matches_gitignore_patterns(validated_path, gitignore_patterns):
                    return True
                    
            return False
            
        except Exception as e:
            raise create_error(GitServiceError, f"Error checking file exclusion: {str(e)}", "FileExclusion")

    # Helper methods for should_exclude
    @staticmethod
    def _matches_common_exclusions(path: str) -> bool:
        """
        Check if path matches common exclusion patterns
        
        Args:
            path: Path to check
            
        Returns:
            True if path matches common exclusions
        """
        try:
            for pattern in COMMON_EXCLUSIONS:
                if fnmatch.fnmatch(path, pattern) or pattern in path.split(os.sep):
                    return True
            return False
            
        except Exception as e:
            raise create_error(GitServiceError, f"Error checking common exclusions: {str(e)}", "FileExclusion")

    @staticmethod
    def _matches_gitignore_patterns(path: str, gitignore_patterns: Set[str]) -> bool:
        """
        Check if path matches .gitignore patterns
        
        Args:
            path: Path to check
            gitignore_patterns: Set of patterns from .gitignore
            
        Returns:
            True if path matches gitignore patterns
        """
        try:
            for pattern in gitignore_patterns:
                if fnmatch.fnmatch(path, pattern):
                    return True
            return False
            
        except Exception as e:
            raise create_error(GitServiceError, f"Error checking gitignore patterns: {str(e)}", "FileExclusion")

    # PRIMARY OPERATION 2: Get gitignore patterns
    @staticmethod
    def get_gitignore_patterns(repo_path: str) -> Set[str]:
        """
        Get patterns from .gitignore file
        
        Args:
            repo_path: Path to repository
            
        Returns:
            Set of patterns from .gitignore
        """
        # Validate input using Pydantic model 
        exclusion_input = FileExclusionInput(path="dummy", repo_path=repo_path)
        validated_repo_path = exclusion_input.repo_path

        # Initialize logger for static method
        logger = setup_logger(
            "file_exclusion",
            settings.logging.module_levels.get("file_exclusion", settings.logging.level)
        )

        patterns = set()
        gitignore_path = os.path.join(validated_repo_path, '.gitignore')
        
        try:
            if os.path.exists(gitignore_path):
                logger.debug(f"[FileExclusion] Reading .gitignore from: {gitignore_path}")
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            patterns.add(line)
                            
                logger.debug(f"[FileExclusion] Loaded {len(patterns)} .gitignore patterns")
            else:
                logger.debug(f"[FileExclusion] No .gitignore file found at: {gitignore_path}")
                
        except Exception as e:
            # Log warning but don't fail - continue without .gitignore patterns
            logger.warning(f"[FileExclusion] Failed to read .gitignore: {str(e)}")
                
        return patterns 