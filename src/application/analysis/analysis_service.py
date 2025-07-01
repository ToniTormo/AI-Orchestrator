"""
Analysis Service

Provides comprehensive analysis capabilities for projects including
technology detection and complexity assessment.
"""

from typing import Dict, List, Any
from src.utils.logging import setup_logger
from src.config import settings
from .tech_detector import TechDetector
from src.utils.exceptions_control import create_error
from src.domain.models import TechStackAnalysisInput

class AnalysisService:
    """Service for project analysis operations"""

    def __init__(self):
        """Initialize the analysis service"""
        self.logger = setup_logger(
            "analysis.service",
            settings.logging.module_levels.get("analysis", settings.logging.level)
        )
        
        # Initialize tech detector only
        self.tech_detector = TechDetector()
        
        self.logger.info("[AnalysisService] Initialized with tech detector")

    async def analyze_repository(self, repo_path: str, repo_structure) -> Dict[str, Any]:
        """
        Analyze repository for complexity and technologies (structure comes from git_service)
        
        Args:
            repo_path: Path to the repository
            repo_structure: GitRepositoryStructure from git_service
            
        Returns:
            Dictionary with analysis results including structure, complexity_score, technologies, estimated_hours
        """
        try:
            # Validate input using Pydantic
            input_data = TechStackAnalysisInput(repo_path=repo_path)
            
            self.logger.info(f"[AnalysisService] Starting repository analysis for: {input_data.repo_path}")
            
            # Convert repo_structure to dictionary format expected by coordinator
            structure_dict = self._convert_structure_to_dict(repo_structure)
            
            # Analyze technologies (this is our main job)
            technologies = await self.tech_detector.analyze_tech_stack(input_data.repo_path, repo_structure.files)
            
            # Calculate basic complexity score based on technologies and structure only
            complexity_score = self._calculate_repository_complexity(technologies, structure_dict)
            
            # Estimate development hours based on complexity and structure
            estimated_hours = self._estimate_development_hours(complexity_score, structure_dict)
            
            analysis_result = {
                "structure": structure_dict,
                "complexity_score": complexity_score,
                "technologies": technologies,
                "estimated_hours": estimated_hours
            }
            
            self.logger.info(f"[AnalysisService] Repository analysis completed - complexity: {complexity_score}")
            return analysis_result
            
        except Exception as e:
            raise create_error(Exception, f"Error analyzing repository: {e}", "AnalysisService.analyze_repository")

    def _convert_structure_to_dict(self, repo_structure) -> Dict[str, Any]:
        """Convert GitRepositoryStructure to dictionary format expected by coordinator"""
        try:
            return {
                "total_files": len(repo_structure.files),
                "total_directories": len(repo_structure.directories),
                "files": repo_structure.files,
                "directories": repo_structure.directories,
                "name": repo_structure.name
            }
        except Exception as e:
            raise create_error(Exception, f"Error converting structure to dict: {e}", "AnalysisService._convert_structure_to_dict")

    def _calculate_repository_complexity(self, technologies: Dict[str, List[str]], structure: Dict[str, Any]) -> float:
        """Calculate repository complexity score based on technologies and structure only"""
        try:
            # Calculate technology complexity
            total_techs = sum(len(techs) for techs in technologies.values())
            tech_complexity = min(total_techs / 10, 1.0)  # Normalize to 0-1
            
            # Calculate structure complexity
            file_complexity = min(structure.get("total_files", 0) / 100, 1.0)
            
            self.logger.info(f"[AnalysisService] tech_complexity: {tech_complexity} - file_complexity: {file_complexity}")
            
            # Weighted average (technology is more important than file count)
            complexity_score = (tech_complexity * 0.5) + (file_complexity * 0.5)
            
            return min(complexity_score, 1.0)
            
        except Exception as e:
            raise create_error(Exception, f"Error calculating complexity: {e}", "AnalysisService._calculate_repository_complexity")
    
    def _estimate_development_hours(self, complexity_score: float, structure: Dict[str, Any]) -> int:
        """Estimate development hours based on complexity and structure"""
        try:
            base_hours = 8  # Minimum hours
            complexity_hours = complexity_score * 50  # Max 50 hours from complexity
            file_hours = (structure.get("total_files", 0) / 10) * 2  # 2 hours per 10 files
            
            total_hours = base_hours + complexity_hours + file_hours
            return max(8, min(int(total_hours), 200))  # Between 8 and 200 hours
            
        except Exception as e:
            raise create_error(Exception, f"Error estimating hours: {e}", "AnalysisService._estimate_development_hours")
    
    async def analyze_basic_viability(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform basic viability analysis based on technical factors only
        
        Args:
            analysis_result: Repository analysis result
            
        Returns:
            Dictionary with basic viability analysis
        """
        try:
            self.logger.info("[AnalysisService] Starting basic viability analysis")
            
            complexity_score = analysis_result.complexity_score
            estimated_hours = analysis_result.estimated_hours
            
            # Simple viability checks
            technical_feasibility = 1.0 - complexity_score
            time_feasibility = self._assess_time_feasibility(estimated_hours)
            
            # Basic confidence calculation
            confidence_score = (technical_feasibility * 0.6) + (time_feasibility * 0.4)
            
            # Simple threshold check
            is_viable = confidence_score > 0.4 and technical_feasibility > 0.2 and time_feasibility > 0.2
            
            reasoning = f"Basic analysis: technical feasibility {technical_feasibility:.2f}, time feasibility {time_feasibility:.2f}"
            self.logger.info(f"[AnalysisService] Confidence score: {confidence_score * 100} - technical_feasibility: {technical_feasibility} - time_feasibility: {time_feasibility}")
            return {
                "is_viable": is_viable,
                "confidence_score": confidence_score * 100,
                "reasoning": reasoning
            }
            
        except Exception as e:
            raise create_error(Exception, f"Error analyzing basic viability: {e}", "AnalysisService.analyze_basic_viability")

    
    def _assess_time_feasibility(self, estimated_hours: int) -> float:
        """Assess project viability based on estimated development time"""
        try:
            if estimated_hours <= 40:
                return 1.0
            elif estimated_hours <= 100:
                return 0.8
            elif estimated_hours <= 150:
                return 0.5
            else:
                return 0.2
                
        except Exception as e:
            raise create_error(Exception, f"Error assessing time feasibility: {e}", "AnalysisService._assess_time_feasibility")
