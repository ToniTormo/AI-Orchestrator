"""
Technology Detector

Handles repository analysis and technology stack detection
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any
from src.utils.logging import setup_logger
from src.config import settings
from src.utils.exceptions_control import create_error
from src.domain.models import TechStackAnalysisInput

class TechDetector:
    """
    Specialized service for detecting technologies in repositories.
    Analyzes file structure, extensions, and content to identify tech stack.
    """
    
    def __init__(self):
        """Initialize the technology detector"""
        self.logger = setup_logger(
            "analysis.tech_detector",
            settings.logging.module_levels.get("analysis", settings.logging.level)
        )
        self.config = self._load_config()
        self.logger.info("[TechDetector] Initialized successfully")
        # ===== CONFIG LOADING =====
    
    def _load_config(self) -> Dict[str, Any]:
        """Load technology detection configuration"""
        try:
            config_path = Path(__file__).parent / "config" / "analysis_config.yaml"
            
            if not config_path.exists():
                raise create_error(FileNotFoundError, f"Config file not found at: {config_path}", "TechDetector._load_config")
            
            with open(config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                tech_detection_config = config.get('tech_detection')
                
                if not tech_detection_config:
                    raise create_error(ValueError, "'tech_detection' section not found in config file", "TechDetector._load_config")
                
                return tech_detection_config
                
        except Exception as e:
            raise create_error(Exception, f"Error loading config: {e}", "TechDetector._load_config")   
        
    # ===== PRIMARY ANALYSIS FUNCTIONS =====
    
    async def analyze_tech_stack(self, repo_path: str, file_list: List[str]) -> Dict[str, List[str]]:
        """
        Analyze the technology stack of a repository based on provided file list
        
        Args:
            repo_path: Path to the repository
            file_list: List of file paths to analyze (from git_service)
            
        Returns:
            Dictionary containing detected technologies by category
        """
        try:
            # Validate input using Pydantic
            input_data = TechStackAnalysisInput(repo_path=repo_path)
            
            self.logger.info(f"[TechDetector] Analyzing tech stack for: {input_data.repo_path}")
            self.logger.debug(f"[TechDetector] Processing {len(file_list)} files")
            
            tech_stack = self._initialize_tech_stack()
            
            # Analyze files from provided list
            await self._analyze_file_list(input_data.repo_path, file_list, tech_stack)
            
            # Clean up and sort results
            self._finalize_tech_stack(tech_stack)
            
            self.logger.info(f"[TechDetector] Detected tech stack: {tech_stack}")
            return tech_stack
            
        except Exception as e:
            raise create_error(Exception, f"Error analyzing tech stack: {e}", "TechDetector.analyze_tech_stack")
    
    # ===== HELPER METHODS FOR TECH STACK ANALYSIS =====
    
    def _initialize_tech_stack(self) -> Dict[str, List[str]]:
        """Initialize empty tech stack structure"""
        return {
            "frontend": [],
            "backend": [],
            "database": [],
            "devops": [],
            "testing": [],
            "other": []
        }
    
    async def _analyze_file_list(self, repo_path: str, file_list: List[str], tech_stack: Dict[str, List[str]]):
        """Analyze provided file list to detect technologies"""
        try:
            extensions_config = self.config['extensions']
            
            for file_path in file_list:
                file_name = os.path.basename(file_path)
                ext = os.path.splitext(file_name)[1].lower()
                
                # Categorize by extension
                for category, extensions in extensions_config.items():
                    if ext in extensions:
                        self._detect_technology_by_extension(tech_stack, category, ext, file_name)
        
        except Exception as e:
            self.logger.error(f"[TechDetector] Error analyzing file list: {e}")
    
    def _detect_technology_by_extension(self, tech_stack: Dict[str, List[str]], category: str, ext: str, file_name: str):
        """Detect technology based on file extension using YAML configuration"""
        try:
            # Get technology mappings from config
            technology_mappings = self.config.get('technology_mappings', {})
            category_mappings = technology_mappings.get(category, {})
            
            # Look up the technology for this extension
            if ext in category_mappings:
                technology = category_mappings[ext]
                
                # Map category to tech stack category
                tech_category_map = {
                    "frontend": "frontend",
                    "backend": "backend",
                    "config": "other",
                    "data": "other", 
                    "documentation": "other"
                }
                
                target_category = tech_category_map.get(category, "other")
                tech_stack[target_category].append(technology)
        
        except Exception as e:
            self.logger.error(f"[TechDetector] Error detecting technology by extension: {e}")
    
    def _finalize_tech_stack(self, tech_stack: Dict[str, List[str]]):
        """Remove duplicates and sort tech stack"""
        for category in tech_stack:
            tech_stack[category] = sorted(list(set(tech_stack[category])))