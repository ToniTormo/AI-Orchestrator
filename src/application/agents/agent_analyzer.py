"""
Agent Analyzer

Agent for analyzing projects and generating recommendations
"""

import json
import re
import uuid
from typing import Dict, List, Any

from src.config import settings
from src.utils.exceptions_control import create_error, AgentError
from src.domain.models.agent_model import AgentType
from src.domain.models.analysis_models import AgentAnalyzerInput, AgentAnalyzerOutput, AnalysisTask
from src.infrastructure.services import AsyncServiceBase
from src.infrastructure.openai.openai_service import OpenAIService
from .chunk_system import ChunkSystem
from .prompts_analyzer import get_analysis_prompt

class AgentAnalyzer(AsyncServiceBase):
    """Agent that analyzes projects with AI to generate specific code change recommendations"""

    def __init__(self, openai_service=None):
        """
        Initialize the agent analyzer
        
        Args:
            openai_service: Optional OpenAI service instance
        """
        super().__init__("agent.analyzer")
        self.agent_type = AgentType.ANALYZER
        self.ai_service = openai_service or OpenAIService()
        self.logger.info("[AgentAnalyzer] Initialized")

    async def _initialize_impl(self):
        """Default agent initialization implementation"""
        self.logger.info(f"[{self.agent_type.value}] Agent initialization completed")

    async def _shutdown_impl(self):
        """Default agent shutdown implementation"""
        self.logger.info(f"[{self.agent_type.value}] Agent shutdown completed")

    async def analyze_project(self, description: str, repo_path: str, structure: Dict[str, Any], 
                            technologies: Dict[str, Any], confidence_score: float) -> Dict[str, Any]:
        """
        Analyze a project using AI to generate specific code change recommendations
        
        Args:
            description: Project description/requirements
            repo_path: Path to the repository
            structure: Repository structure with files list
            technologies: Technologies used in the project
            confidence_score: Initial confidence score from basic analysis
            
        Returns:
            Dictionary with analysis results including viability score and specific tasks
        """
        try:
            # Validate input using Pydantic model
            input_data = AgentAnalyzerInput(
                description=description,
                repo_path=repo_path,
                structure=structure,
                technologies=technologies,
                confidence_score=confidence_score
            )
            
            # Extract project name from repo_path
            project_name = input_data.repo_path.split('/')[-1] or input_data.repo_path.split('\\')[-1]
            self.logger.info(f"[AgentAnalyzer] Starting analysis for: {project_name}")
            
            # Extract and process code files
            code_files = self._extract_code_files(input_data.repo_path, input_data.structure)
            total_files = input_data.structure.get("total_files", len(input_data.structure.get("files", [])))
            
            self.logger.info(f"[AgentAnalyzer] Processing {len(code_files)} code files from {total_files} total files")
            
            # Process analysis in chunks if needed
            analysis_results = await self._process_code_analysis(
                project_name, input_data.description, input_data.technologies, total_files, code_files
            )
            
            # Calculate average viability score from all chunks
            avg_viability = self._calculate_average_viability(analysis_results, input_data.confidence_score)
            
            # Collect and enrich all tasks with file paths and unique IDs
            enriched_tasks = self._enrich_tasks_with_metadata(analysis_results, input_data.repo_path)
            
            # Create and validate output using Pydantic model
            output_data = AgentAnalyzerOutput(
                viability_score=avg_viability,
                tasks=enriched_tasks
            )
            
            # Convert to dict for return
            result = output_data.model_dump()
            
            return result
            
        except json.JSONDecodeError as e:
            raise create_error(AgentError, f"Invalid JSON response from AI: {str(e)}", "AgentAnalyzer")
        except Exception as e:
            raise create_error(AgentError, f"Failed to analyze project: {str(e)}", "AgentAnalyzer")

    def _extract_code_files(self, repo_path: str, structure: Dict[str, Any]) -> Dict[str, str]:
        """Extract and read code files from repository structure"""
        code_files = {}
        files_list = structure.get('files', [])
        
        for file_path in files_list:
            try:
                full_path = f"{repo_path}/{file_path}"
                with open(full_path, 'r', encoding='utf-8') as f:
                    code_files[file_path] = f.read()
            except Exception as e:
                self.logger.warning(f"[AgentAnalyzer] Could not read file {file_path}: {e}")
                continue
                
        return code_files

    async def _process_code_analysis(self, project_name: str, description: str, 
                                   technologies: Dict[str, Any], total_files: int,
                                   code_files: Dict[str, str]) -> List[Dict[str, Any]]:
        """Process code analysis, handling large projects by chunking if necessary"""
        
        # 1. Calculate total tokens for complete analysis
        complete_prompt = get_analysis_prompt(
            project_name=project_name,
            description=description,
            technologies=technologies,
            total_files=total_files,
            code_files=code_files
        )
        total_tokens = ChunkSystem.estimate_tokens(complete_prompt)
        
        # 2. Get model limits
        context_limit, completion_tokens = ChunkSystem.get_model_limits()
        max_prompt_tokens = context_limit - completion_tokens
        
        # 3. Compare total tokens with maximum limit

        if total_tokens <= max_prompt_tokens:
            # 4a. If it fits: Single request
            self.logger.info(f"[AgentAnalyzer] Processing project in single request ({total_tokens} tokens)")
            result = await self._process_single_request(
                project_name, description, technologies, total_files, code_files, completion_tokens
            )
            result['chunk_files'] = list(code_files.keys())
            return [result]

        # 4b. If it doesn't fit: Divide into chunks
        self.logger.info(f"[AgentAnalyzer] Large project detected ({total_tokens} tokens), chunking with limit {max_prompt_tokens} tokens")
        return await self._process_chunked_request(
            project_name, description, technologies, total_files, code_files, max_prompt_tokens, completion_tokens
        )

    async def _process_single_request(self, project_name: str, description: str,
                                technologies: Dict[str, Any], total_files: int,
                                code_files: Dict[str, str], completion_tokens: int) -> Dict[str, Any]:
        """Analyze a single chunk of code files"""
        prompt = get_analysis_prompt(
            project_name=project_name,
            description=description,
            technologies=technologies,
            total_files=total_files,
            code_files=code_files
        )
        
        response = await self.ai_service.create_completion(
            prompt=prompt,
            model=settings.openai.model,
            temperature=settings.openai.temperature_analysis,
            max_tokens=completion_tokens
        )
        
        raw_content = response.choices[0].message.content.strip()
        return self._parse_json_response(raw_content)

    async def _process_chunked_request(self, project_name: str, description: str, 
                                     technologies: Dict[str, Any], total_files: int,
                                     code_files: Dict[str, str], max_prompt_tokens: int, 
                                     completion_tokens: int) -> List[Dict[str, Any]]:
        """Process a large project using chunking to preserve all content."""
        base_prompt = get_analysis_prompt(
            project_name=project_name,
            description=description,
            technologies=technologies,
            total_files=total_files,
            code_files={}  # Empty to get base size
        )
        base_tokens = ChunkSystem.estimate_tokens(base_prompt)
        
        # Estimate formatting overhead (line numbers + file headers) for all code
        formatting_overhead = ChunkSystem.estimate_formatting_overhead(code_files)
        
        # Calculate the maximum tokens available for RAW code content
        # We reserve space for: base_prompt + formatting_overhead
        max_content_tokens = max_prompt_tokens - base_tokens - formatting_overhead

        # Divide files into chunks that respect the limit
        file_chunks = ChunkSystem.create_file_chunks(code_files, max_content_tokens)

        chunk_results = []
        for i, chunk in enumerate(file_chunks):
            # Calculate detailed token breakdown for this chunk
            raw_content_tokens = sum(ChunkSystem.estimate_tokens(c) for c in chunk.values())
            chunk_formatting_overhead = ChunkSystem.estimate_formatting_overhead(chunk)
            total_chunk_tokens = base_tokens + raw_content_tokens + chunk_formatting_overhead
            
            self.logger.info(f"[AgentAnalyzer] Analyzing chunk {i+1}/{len(file_chunks)} (~{total_chunk_tokens} tokens)")
            
            result = await self._process_single_request(
                project_name, description, technologies, total_files, chunk, completion_tokens
            )
            result['chunk_files'] = list(chunk.keys())
            chunk_results.append(result)

        return chunk_results

    def _parse_json_response(self, content: str):
        """Safely parse JSON possibly containing invalid backslashes returned by the AI"""
        # Remove markdown code fences if present
        content = content.strip()
        if content.startswith('```'):
            # Remove leading and trailing ``` blocks (with optional json tag)
            content = re.sub(r'^```(?:json)?', '', content, flags=re.IGNORECASE).strip()
            if content.endswith('```'):
                content = content[:-3].strip()

        # First attempt to parse as-is
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Fix unescaped backslashes that are not valid JSON escapes
            # Replace single backslash not followed by [ " / b f n r t u ] with doubled backslash
            fixed = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', content)
            return json.loads(fixed)
    
    def _calculate_average_viability(self, analysis_results: List[Dict[str, Any]], 
                                   initial_confidence: float) -> int:
        """Calculate average viability score from all analysis chunks"""
        if not analysis_results:
            raise create_error(AgentError, "No analysis results provided by IA", "AgentAnalyzer")
        
        scores = []
        for result in analysis_results:
            score = result.get('viability_score')
            if score is not None:
                scores.append(score)
        
        if not scores:
            raise create_error(AgentError, "No viability scores provided by IA", "AgentAnalyzer")
        
        # Calculate weighted average
        ai_avg = sum(scores) / len(scores)
        
        self.logger.info(f"[AgentAnalyzer] AI viability score: {ai_avg}")
        
        weighted_avg = (ai_avg * 0.8) + (initial_confidence * 0.2)
        
        return int(weighted_avg)

    def _enrich_tasks_with_metadata(self, analysis_results: List[Dict[str, Any]], 
                                  repo_path: str) -> List[AnalysisTask]:
        """Collect all tasks from analysis results and enrich them with file paths and unique IDs"""
        # Dictionary to group tasks by file path
        tasks_by_file = {}
        
        for result in analysis_results:
            # The AI now returns a list of task objects, each with 'file_path' and 'specific_changes'
            tasks_from_ai = result.get('tasks', [])
            
            if isinstance(tasks_from_ai, list):
                for task_data in tasks_from_ai:
                    # Ensure the task_data is a dictionary with the required keys
                    if isinstance(task_data, dict) and 'file_path' in task_data and 'specific_changes' in task_data:
                        try:
                            # Resolve the full path for the file
                            file_path = self._resolve_file_path(task_data['file_path'], repo_path)
                            
                            # Group tasks by file path
                            if file_path not in tasks_by_file:
                                tasks_by_file[file_path] = []
                            
                            tasks_by_file[file_path].append(task_data['specific_changes'])
                            
                        except Exception as e:
                            self.logger.warning(f"[AgentAnalyzer] Skipping task due to validation error: {e}")
                    else:
                        self.logger.warning(f"[AgentAnalyzer] Skipping malformed task data: {task_data}")
            else:
                self.logger.warning(f"[AgentAnalyzer] Expected a list of tasks, but got: {type(tasks_from_ai)}")
        
        # Consolidate tasks for each file
        consolidated_tasks = []
        for file_path, changes_list in tasks_by_file.items():
            if len(changes_list) == 1:
                specific_changes = changes_list[0]
            else:
                specific_changes = "\n".join(changes_list)
            
            # Create a validated AnalysisTask using the Pydantic model
            task = AnalysisTask(
                id=str(uuid.uuid4()),
                file_path=file_path,
                specific_changes=specific_changes
            )
            consolidated_tasks.append(task)
        
        return consolidated_tasks

    def _resolve_file_path(self, relative_file: str, repo_path: str) -> str:
        """Resolve relative file path to absolute path"""
        if not relative_file:
            raise create_error(AgentError, "No file path provided", "AgentAnalyzer")
        
        # Normalize path separators
        relative_file = relative_file.replace("\\", "/")
        repo_path = repo_path.replace("\\", "/")
        
        # Construct full path
        if relative_file.startswith("/"):
            return f"{repo_path}{relative_file}"
        else:
            return f"{repo_path}/{relative_file}"
