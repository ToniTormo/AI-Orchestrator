"""
Backend Agent Prompts

Contains implementation prompt for backend development agent
"""

from typing import Dict, Any

def get_implementation_prompt_backend(task: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    Generate the complete prompt for implementing server-side/backend changes
    
    Args:
        task: Task dictionary containing description, file_path(s), category, and priority
        context: Project context with repo_path and technologies
        
    Returns:
        Formatted implementation prompt with system context
    """
    
    # Extract task information
    task_description = task.get("description", "")
    file_paths = task.get("file_path", [])
    if isinstance(file_paths, str):
        file_paths = [file_paths]
    
    # Format file paths for display
    files_text = "\n".join([f"- {path}" for path in file_paths])
    
    # Extract context information
    technologies = context.get("technologies", [])
    
    # Get file contents if available
    key_files_content = context.get("key_files_content", {})
    code_content = _format_code_files(key_files_content) if key_files_content else "No file content available"
    
    return f"""You are a backend development specialist agent. Your role is to modify server-side code with precision. You understand server architecture, data processing, APIs, and security best practices.

        TASK: {task_description}
        FILES: {files_text}
        TECH_USED: {technologies}

        CURRENT CODE:
        {code_content}

        CAPABILITIES: Add, replace, delete code at any line. Follow task_description exactly.

        RULES:
        - Complete working code only - no placeholders
        - Match existing code style and patterns
        - Handle imports/dependencies correctly
        - Follow exact line numbers when specified
        - Implement proper error handling
        - Ensure data validation and security
        - Follow RESTful/API best practices
        - Handle database operations safely

        RESPONSE (JSON only) with the following format:
        {{
            "files_modified": [
                {{
                    "file": "path/to/your/file.ext",
                    "changes": [
                        {{
                            "type": "add|replace|delete",
                            "start_line": 5,
                            "end_line": 8,
                            "content": "code to append or replace. For 'delete', content can be empty"
                        }}
                    ]
                }}
            ]
        }}

        TYPES:
        - add: Add new lines of code starting at 'start_line'. 'end_line' is ignored.
        - replace: Replace the block of code from 'start_line' to 'end_line' with the new 'content'.
        - delete: Delete the block of code from 'start_line' to 'end_line'. 'content' is ignored.

        Execute precisely. JSON only."""

def _format_code_files(code_files: Dict[str, str]) -> str:
    """Format code files for inclusion in prompt with line numbers"""
    code_summary = []
    for file_path, content in code_files.items():
        # Add line numbers to help with precise change specifications
        lines = content.split('\n')
        numbered_lines = []
        for i, line in enumerate(lines, 1):
            numbered_lines.append(f"{i:4d}: {line}")
        
        numbered_content = '\n'.join(numbered_lines)
        code_summary.append(f"=== FILE: {file_path} ===\n{numbered_content}")
    
    return "\n\n".join(code_summary)