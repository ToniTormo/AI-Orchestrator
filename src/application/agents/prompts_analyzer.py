"""
Code Analyzer Agent Prompts

Contains analysis prompt for the CodeAnalyzer
"""

from typing import Dict, Any


def get_analysis_prompt(project_name: str, description: str, technologies: Dict[str, Any], 
                       total_files: int, code_files: Dict[str, str]) -> str:
    """
    Create analysis prompt for AI to generate specific code changes
    
    Args:
        project_name: Name of the project
        description: Project description/requirements
        technologies: Technology stack used in the project
        total_files: Total number of files in project
        code_files: Code files to analyze with their content
        
    Returns:
        Formatted prompt for AI analysis focused on specific code changes
    """
    # Format code files for prompt
    code_content = _format_code_files(code_files)
    
    frontend_techs = ', '.join(technologies.get("frontend", []))
    backend_techs = ', '.join(technologies.get("backend", []))
    tech_summary = f"Frontend: {frontend_techs}, Backend: {backend_techs}" if frontend_techs or backend_techs else "Mixed/Unknown stack"
    
    return f"""You are an expert software developer and code analyst with deep knowledge of modern programming practices and technologies.

            Your task is to analyze the provided codebase and generate SPECIFIC, ACTIONABLE code changes to implement the requested requirements.

            PROJECT INFORMATION:
            - Project Name: {project_name}
            - Requirements: {description}
            - Technology Stack: {tech_summary}
            - Total Files: {total_files}
            - Files to Analyze: {len(code_files)}

            CODE TO ANALYZE:
            {code_content}

            ANALYSIS REQUIREMENTS:
            1. **Analyze the FEASIBILITY** of implementing the specific changes requested
            2. **Provide CONCRETE MODIFICATIONS** - specify what lines to change and how
            3. **Focus on PRACTICAL IMPLEMENTATION** - real code changes, not abstract suggestions
            4. **Consider existing code structure** and maintain compatibility
            5. **Specify exact locations** for each change

            SCORING GUIDELINES:
            - **90-100**: Very clear requirements, perfect tech match, simple implementation
            - **70-89**: Clear requirements, good tech match, moderate complexity
            - **50-69**: Somewhat clear requirements, adequate tech match, moderate complexity
            - **30-49**: Unclear requirements, partial tech match, high complexity
            - **0-29**: Very unclear requirements, poor tech match, very high complexity

            TASK GUIDELINES:
            - **ONLY CREATE TASKS FOR RELEVANT FILES**: Only generate tasks for files that actually need modifications to implement the requirements
            - **SPECIFIC_CHANGES**: Provide detailed instructions including:
            - Exact line numbers where changes should be made
            - What type of change (add, modify, delete)
            - Clear explanation of what code should be changed and why
            
            RESPONSE FORMAT:
            Respond with ONLY this JSON structure:

            {{
                "viability_score": <0-100 integer>,
                "tasks": [
                    {{
                        "file_path": "relative/path/to/file.ext",
                        "specific_changes": "Detailed description of what needs to be done in this file, including specific line numbers. Be very specific about which lines to modify and what the changes should be."
                    }}
                ]
            }}

            Generate tasks that span the complete implementation of the requested changes."""


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