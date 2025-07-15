"""
Agent Development

Generic agent for development tasks that receives analysis and uses type-specific prompts
"""

from typing import Dict, Any, List
import json
import os
import re

from src.config import settings
from src.utils.exceptions_control import create_error, AgentError
from src.domain.models.agent_model import AgentType
from src.infrastructure.services import AsyncServiceBase
from src.infrastructure.openai.openai_service import OpenAIService
from .chunk_system import ChunkSystem

from .prompts_frontend import get_implementation_prompt_frontend
from .prompts_backend import get_implementation_prompt_backend

class AgentDevelopment(AsyncServiceBase):
    """Generic agent for development tasks (frontend/backend) that receives pre-computed analysis"""

    def __init__(self, agent_type: AgentType, ai_service=None):
        """
        Initialize the agent development
        
        Args:
            agent_type: Type of agent (FRONTEND or BACKEND)
            ai_service: Optional AI service instance
        """
        super().__init__(f"agent.{agent_type.value}")
        self.agent_type = agent_type

        # Import prompts based on agent type
        if agent_type == AgentType.FRONTEND:
            self.get_implementation_prompt = get_implementation_prompt_frontend
        elif agent_type == AgentType.BACKEND:
            self.get_implementation_prompt = get_implementation_prompt_backend
        else:
            raise create_error(AgentError, f"Unsupported agent type: {agent_type}", "AgentDevelopment")
        
        # Use provided ai_service or create a new one
        self.ai_service = ai_service or OpenAIService()
        
        self.logger.info(f"[AgentDevelopment] Initialized {agent_type.value} agent")

    async def _initialize_impl(self):
        """Default agent initialization implementation"""
        self.logger.info(f"[{self.agent_type.value}] Agent initialization completed")

    async def _shutdown_impl(self):
        """Default agent shutdown implementation"""
        self.logger.info(f"[{self.agent_type.value}] Agent shutdown completed")

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a development task
        
        Args:
            task: Task dictionary containing description, file_path, and context.
            
        Returns:
            Dictionary with task execution results containing:
            - task_id: ID of the executed task
            - output: Description of the execution result
            - error: Any error that occurred (None if successful)
            - files_modified: List of files that were modified
        """
        task_id = task.get('id', 'unknown')
        self.logger.info(f"[AgentDevelopment] [{self.agent_type.value}] Starting task execution: {task_id}")
        
        try:
            context = task.get('context', {})
            repo_path = context.get('repo_path')
            if not repo_path:
                return {
                    "task_id": task_id,
                    "output": None,
                    "error": "Repository path not found in task context",
                    "files_modified": []
                }

            # Read file content if file_path is provided
            file_path = task.get('file_path')
            if file_path:
                file_content = self._read_file_content(repo_path, file_path)
                # Add file content to context
                context['key_files_content'] = {file_path: file_content}

            # 1. Get AI-driven implementation
            implementation_prompt = self.get_implementation_prompt(task, context)
            ai_response = await self._get_ai_response(implementation_prompt, task)
            
            # 2. Apply changes to the filesystem
            files_modified = self._apply_file_modifications(repo_path, ai_response.get("files_modified", []))
            
            # 3. Return result
            return {
                "task_id": task_id,
                "output": f"Successfully completed {self.agent_type.value} task with {len(files_modified)} file modifications",
                "error": None,
                "files_modified": files_modified
            }
            
        except Exception as e:
            error_msg = f"Task execution failed: {str(e)}"
            self.logger.error(f"[AgentDevelopment] [{self.agent_type.value}] {error_msg}")
            return {
                "task_id": task_id,
                "output": None,
                "error": error_msg,
                "files_modified": []
            }
    
    def _read_file_content(self, repo_path: str, file_path: str) -> str:
        "Read the content of a file from the repository"""
        try:
            full_path = os.path.join(repo_path, file_path.lstrip('/').replace("/", os.sep))
            if not os.path.exists(full_path):
                self.logger.warning(f"[AgentDevelopment] File not found: {full_path}")
                return ""
                
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"[AgentDevelopment] Error reading file {file_path}: {str(e)}")
            return ""
    
    async def _get_ai_response(self, prompt: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get the implementation response from the AI service with chunking support."""
        try:
            total_tokens = ChunkSystem.estimate_tokens(prompt)
            
            context_limit, completion_tokens = ChunkSystem.get_model_limits()
            max_prompt_tokens = context_limit - completion_tokens
            
            if total_tokens <= max_prompt_tokens:
                # If it fits: Single request
                self.logger.info(f"[AgentDevelopment] Processing prompt ({total_tokens} tokens)")
                return await self._process_single_request(prompt, completion_tokens)
            else:
                # If it doesn't fit: Divide into chunks
                self.logger.info(f"[AgentDevelopment] Large prompt detected ({total_tokens} tokens), chunking with limit {max_prompt_tokens} tokens")
                return await self._process_chunked_request(task, max_prompt_tokens, completion_tokens)
            
        except Exception as e:
            raise create_error(AgentError, f"Failed to get AI implementation: {str(e)}", "AgentDevelopment")

    async def _process_single_request(self, prompt: str, completion_tokens: int) -> Dict[str, Any]:
        """Process a single AI request (same pattern as agent_analyzer)"""
        response = await self.ai_service.create_completion(
            prompt=prompt,
            model=settings.openai.model,
            temperature=settings.openai.temperature_development,
            max_tokens=completion_tokens
        )

        content = response.choices[0].message.content.strip()
        if not content:
            raise create_error(AgentError, "Empty content from AI response", "AgentDevelopment")
        
        return self._parse_ai_response(content)

    async def _process_chunked_request(self, task: Dict[str, Any], max_prompt_tokens: int, completion_tokens: int) -> Dict[str, Any]:
        """Process a large task using chunking to preserve all content (following agent_analyzer pattern)."""
        context = task.get('context', {})
        key_files_content = context.get('key_files_content', {})
        
        if not key_files_content:
            raise create_error(AgentError, "No file content available for chunking", "AgentDevelopment")
        
        # Calculate base prompt size (without file content)
        base_prompt = self.get_implementation_prompt(task, {**context, 'key_files_content': {}})
        base_tokens = ChunkSystem.estimate_tokens(base_prompt)
        
        # Estimate formatting overhead (line numbers + file headers) for all code
        formatting_overhead = ChunkSystem.estimate_formatting_overhead(key_files_content)
        
        # Calculate the maximum tokens available for RAW code content
        # We reserve space for: base_prompt + formatting_overhead
        max_content_tokens = max_prompt_tokens - base_tokens - formatting_overhead
        
        # Divide files into chunks that respect the limit
        file_chunks = ChunkSystem.create_file_chunks(key_files_content, max_content_tokens)

        chunk_results = []
        accumulated_files_dict = {}  
        
        for i, chunk in enumerate(file_chunks):
            # Calculate detailed token breakdown for this chunk
            raw_content_tokens = sum(ChunkSystem.estimate_tokens(c) for c in chunk.values())
            chunk_formatting_overhead = ChunkSystem.estimate_formatting_overhead(chunk)
            total_chunk_tokens = base_tokens + raw_content_tokens + chunk_formatting_overhead
            
            self.logger.info(f"[AgentDevelopment] Processing chunk {i+1}/{len(file_chunks)} (~{total_chunk_tokens} tokens)")
            
            # Create context with this chunk's files
            chunk_context = {**context, 'key_files_content': chunk}
            chunk_prompt = self.get_implementation_prompt(task, chunk_context)
            
            result = await self._process_single_request(chunk_prompt, completion_tokens)
            result['chunk_files'] = list(chunk.keys())
            chunk_results.append(result)
            
            # Properly merge file modifications from all chunks
            if 'files_modified' in result:
                for file_mod in result['files_modified']:
                    file_path = file_mod.get('file')
                    if file_path:
                        if file_path in accumulated_files_dict:
                            # Merge changes for the same file
                            accumulated_files_dict[file_path]['changes'].extend(file_mod.get('changes', []))
                        else:
                            # First time seeing this file
                            accumulated_files_dict[file_path] = file_mod

        # Convert back to list format
        accumulated_files = list(accumulated_files_dict.values())
        
        # Return merged result
        return {'files_modified': accumulated_files}

    def _parse_ai_response(self, content: str) -> Dict[str, Any]:
        """Parse the JSON response from the AI, with fallbacks for common errors."""
        # Remove markdown code fences if present
        content = content.strip()
        if content.startswith('```'):
            # Remove leading and trailing ``` blocks (with optional json tag)
            content = re.sub(r'^```(?:json)?', '', content, flags=re.IGNORECASE).strip()
            if content.endswith('```'):
                content = content[:-3].strip()
        
        # Find JSON object boundaries
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            raise create_error(AgentError, f"No JSON object found in AI response: {content}", "AgentDevelopment")
            
        json_content = content[json_start:json_end]
        
        # First attempt to parse as-is
        try:
            return json.loads(json_content)
        except json.JSONDecodeError as e:
            self.logger.warning(f"[AgentDevelopment] JSON parsing failed, attempting fixes: {str(e)}")
            try:
                # Fix unescaped backslashes that are not valid JSON escapes
                # Replace single backslash not followed by [ " / b f n r t u ] with doubled backslash
                fixed_content = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', json_content)
                return json.loads(fixed_content)
            except json.JSONDecodeError as fix_error:
                # Additional fixes for common JSON errors
                try:
                    # Remove trailing commas before closing braces/brackets
                    fixed_content = re.sub(r',(\s*[}\]])', r'\1', json_content)
                    # Fix unescaped quotes in strings
                    fixed_content = re.sub(r'(?<!\\)"(?![,}\]:\s])', r'\\"', fixed_content)
                    return json.loads(fixed_content)
                except Exception as final_error:
                    raise create_error(AgentError, f"Failed to parse JSON after multiple fixes. Original: {str(e)}, Fix attempts: {str(fix_error)}, Final: {str(final_error)}", "AgentDevelopment")

    def _apply_file_modifications(self, repo_path: str, files_to_modify: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply file modifications based on the repo path"""
        if not isinstance(files_to_modify, list):
            raise create_error(AgentError, f"Invalid 'files_modified' format. Expected a list, got: {type(files_to_modify)}", "AgentDevelopment")

        files_modified_summary = []
        for file_change in files_to_modify:
            file_path = file_change.get("file")
            changes = file_change.get("changes")

            if not file_path or not changes or not isinstance(changes, list):
                self.logger.error("[AgentDevelopment] Invalid file change format - missing 'file' or 'changes'")
                continue

            try:
                full_path = os.path.join(repo_path, file_path.lstrip('/').replace("/", os.sep))
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                action = "created" if not os.path.exists(full_path) else "modified"

                current_content = []
                if os.path.exists(full_path):
                    with open(full_path, 'r', encoding='utf-8') as f:
                        current_content = f.readlines()

                # Sort changes by start_line in reverse order to avoid index shifting issues
                changes.sort(key=lambda c: c.get('start_line', 0), reverse=True)

                for change in changes:
                    change_type = change.get("type")
                    start_line = change.get("start_line", 1) - 1  # 0-indexed
                    end_line = change.get("end_line", start_line + 1) - 1 # 0-indexed
                    
                    # Handle content that might be a string or a list
                    content = change.get("content", "")
                    if isinstance(content, list):
                        if all(isinstance(item, str) for item in content):
                            content_lines = content
                        else:
                            content_lines = [str(item) for item in content]
                    else:
                        content_lines = content.splitlines(True) or [""]

                    if change_type == "add":
                        current_content[start_line:start_line] = content_lines
                    elif change_type == "replace":
                         # Pad if start_line is out of bounds
                        if start_line >= len(current_content):
                            current_content.extend(['\n'] * (start_line - len(current_content) + 1))
                        
                        # Ensure end_line is within bounds
                        end_line = min(end_line, len(current_content) -1)
                        current_content[start_line:end_line + 1] = content_lines
                    elif change_type == "delete":
                        if start_line < len(current_content):
                            end_line = min(end_line, len(current_content) -1)
                            del current_content[start_line:end_line + 1]

                with open(full_path, 'w', encoding='utf-8') as f:
                    f.writelines(current_content)

                files_modified_summary.append({
                    "file": file_path.replace(os.sep, "/"),
                    "action": action,
                })
                self.logger.info(f"[AgentDevelopment] {action.capitalize()}: {file_path}")

            except Exception as e:
                raise create_error(AgentError, f"Failed to modify file {file_path}: {str(e)}", "AgentDevelopment")
        
        return files_modified_summary
