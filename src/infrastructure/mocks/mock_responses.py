"""
Mock Responses

Predefined mock responses for testing and development
"""

MOCK_RESPONSES = {
    "analyze_project": {
        "viability_score": 85,
        "tasks": [
            {
                "file_path": "src/components/MainComponent.tsx",
                "specific_changes": "Refactor the main component to use the new useDataFetching hook for improved state management. Replace lines 25-45 with the new hook implementation and update the return statement to use the new data structure."
            },
            {
                "file_path": "src/styles/main.css", 
                "specific_changes": "Add new CSS classes for improved styling. Add .data-container class starting at line 120 with flexbox layout properties and responsive design breakpoints."
            },
            {
                "file_path": "src/hooks/useDataFetching.ts",
                "specific_changes": "Create new custom hook for data fetching logic. Implement error handling, loading states, and caching mechanisms. Include TypeScript interfaces for proper type safety."
            }
        ]
    },
    "filter_files": {
        "relevant_files": [0, 1, 2],  # Default indices, will be replaced dynamically
        "explanation": "These files are most relevant based on the project description and analysis context."
    }
} 