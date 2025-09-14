"""
Chunk System

System for handling token-based chunking of content for OpenAI models
"""

from typing import Dict, List
from src.config import settings
import tiktoken  

class ChunkSystem:
    """System for chunking content based on model token limits"""

    # Model context limits (prefix -> window size in tokens)
    MODEL_CONTEXT_LIMITS = {
        "gpt-3.5-turbo": 16384,
        "gpt-4o": 128000,
        "gpt-4o-mini": 128000,
        "gpt-4-turbo": 128000,
        "gpt-4-32k": 32768,
        "gpt-4": 8192,
        "gpt-4.1": 1000000,
        "gpt-5": 400000,
        "gpt-5-mini": 400000,
        "gpt-5-nano": 256000,
        "o1-preview": 128000,
        "o1-mini": 128000,
        "o1-pro": 200000,
        "o1": 200000,
        "o3-pro": 200000,
        "o3-mini": 200000,
        "o3": 200000
    }

    # Max response tokens by model family
    MODEL_MAX_RESPONSE_TOKENS = {
        "gpt-3.5-turbo": 4096,
        "gpt-4o": 4096,
        "gpt-4o-mini": 4096,
        "gpt-4-turbo": 4096,
        "gpt-4-32k": 4000,
        "gpt-4": 4000,
        "gpt-4.1": 32768,
        "gpt-5": 32768,
        "gpt-5-mini": 32768,
        "gpt-5-nano": 16384,
        "o1-preview": 32768,
        "o1-mini": 65536,
        "o1-pro": 32768,
        "o1": 32768,
        "o3-pro": 32768,
        "o3-mini": 32768,
        "o3": 32768
    }

    @classmethod
    def get_model_limits(cls, model_name: str = None) -> tuple[int, int]:
        """
        Get context limit and max response tokens for a model.
        
        Args:
            model_name: Model name (defaults to config model)
            
        Returns:
            Tuple of (context_limit, max_response_tokens)
        """
        model_name = model_name or settings.openai.model
        
        # Match by the longest prefix first to avoid generic prefixes (e.g., "gpt-4")
        # overriding more specific ones (e.g., "gpt-4.1-mini").
        sorted_ctx_limits = sorted(cls.MODEL_CONTEXT_LIMITS.items(), key=lambda kv: len(kv[0]), reverse=True)
        context_limit = next(
            (limit for pref, limit in sorted_ctx_limits if model_name.startswith(pref)), 8192
        )
        
        sorted_resp_limits = sorted(cls.MODEL_MAX_RESPONSE_TOKENS.items(), key=lambda kv: len(kv[0]), reverse=True)
        response_tokens = next(
            (tokens for pref, tokens in sorted_resp_limits if model_name.startswith(pref)), 4000
        )
        
        return context_limit, response_tokens
    
    @staticmethod
    def estimate_tokens(text: str, model_name: str = None) -> int:
        """Return token count for given text using tiktoken when available."""
        
        model_name = model_name or settings.openai.model
        try:
            encoder = tiktoken.encoding_for_model(model_name)
        except KeyError:
            # Fallback to default encoder for unknown models
            encoder = tiktoken.get_encoding("cl100k_base")
        return len(encoder.encode(text))

    @classmethod
    def estimate_formatting_overhead(cls, code_files: Dict[str, str]) -> int:
        """
        Estimate the token overhead added by prompt formatting (line numbers + file headers).
        
        Args:
            code_files: Dictionary of file_path -> content
            
        Returns:
            Approximate token overhead that will be added during formatting
        """
        
        total_overhead = 0
        
        for file_path, content in code_files.items():
            # Header overhead: "=== FILE: path/to/file.ext ===\n"
            header_overhead = 8 + len(file_path.split('/'))  # ~8-15 tokens per header
            
            # Line number overhead: "0001: " per line (6 tokens per line)
            line_count = content.count('\n') + 1
            line_number_overhead = line_count * 6
            
            total_overhead += header_overhead + line_number_overhead
        
        return total_overhead

    @classmethod
    def create_file_chunks(cls, files_content: Dict[str, str], max_tokens: int) -> List[Dict[str, str]]:
        """
        Group files into chunks so that each chunk respects max_tokens.
        Uses an optimized bin packing algorithm to minimize the number of chunks.
        
        Args:
            files_content: Dictionary of file_path -> content
            max_tokens: Maximum tokens per chunk
            
        Returns:
            List of chunks, each chunk is a dict of file_path -> content
        """

        # First, handle files that are too large and need splitting
        processed_files = {}
        split_count = 0
        
        for file_path, content in files_content.items():
            file_tokens = cls.estimate_tokens(content)
            
            if file_tokens > max_tokens:
                # Split large files
                sub_files = cls.split_large_file(file_path, content, max_tokens)
                processed_files.update(sub_files)
                split_count += len(sub_files) - 1
            else:
                processed_files[file_path] = content
        
        # Now pack all files (including split parts) optimally
        file_sizes = [(path, cls.estimate_tokens(content), content) 
                      for path, content in processed_files.items()]
        
        # Sort by size descending for better packing (First Fit Decreasing algorithm)
        file_sizes.sort(key=lambda x: x[1], reverse=True)
        
        # Initialize chunks
        chunks = []
        chunk_remaining_space = []
        
        for file_path, file_tokens, content in file_sizes:
            # Try to find an existing chunk that can fit this file
            placed = False
            
            for i, remaining_space in enumerate(chunk_remaining_space):
                if file_tokens <= remaining_space:
                    # File fits in this existing chunk
                    chunks[i][file_path] = content
                    chunk_remaining_space[i] = remaining_space - file_tokens
                    placed = True
                    break
            
            if not placed:
                # Need to create a new chunk
                new_chunk = {file_path: content}
                chunks.append(new_chunk)
                chunk_remaining_space.append(max_tokens - file_tokens)
        
        # Post-processing: try to merge small chunks if possible
        chunks = cls._merge_small_chunks(chunks, max_tokens)
        
        return chunks
    
    @classmethod
    def _merge_small_chunks(cls, chunks: List[Dict[str, str]], max_tokens: int) -> List[Dict[str, str]]:
        """
        Try to merge small chunks together to improve efficiency.
        
        Args:
            chunks: List of chunks to optimize
            max_tokens: Maximum tokens per chunk
            
        Returns:
            Optimized list of chunks
        """
        if len(chunks) <= 1:
            return chunks
        
        # Calculate size of each chunk
        chunk_sizes = [sum(cls.estimate_tokens(content) for content in chunk.values()) 
                      for chunk in chunks]
        
        merged_chunks = []
        used_chunks = set()
        
        for i, chunk in enumerate(chunks):
            if i in used_chunks:
                continue
                
            current_chunk = chunk.copy()
            current_size = chunk_sizes[i]
            used_chunks.add(i)
            
            # Try to merge with other unused chunks
            for j, other_chunk in enumerate(chunks[i+1:], i+1):
                if j in used_chunks:
                    continue
                    
                other_size = chunk_sizes[j]
                if current_size + other_size <= max_tokens:
                    # Can merge these chunks
                    current_chunk.update(other_chunk)
                    current_size += other_size
                    used_chunks.add(j)
            
            merged_chunks.append(current_chunk)
        
        return merged_chunks

    @classmethod
    def split_large_file(cls, path: str, content: str, max_tokens: int) -> Dict[str, str]:
        """
        Split a file into pieces that respect max_tokens.
        
        Args:
            path: File path
            content: File content
            max_tokens: Maximum tokens per piece
            
        Returns:
            Dictionary of sub_path -> content pieces
        """
        tokens = cls.estimate_tokens(content)
        if tokens <= max_tokens:
            return {path: content}

        parts: Dict[str, str] = {}
        current_part: List[str] = []
        current_tokens = 0
        idx = 1
        
        for line in content.splitlines(keepends=True):
            line_tokens = cls.estimate_tokens(line)
            if current_tokens + line_tokens > max_tokens and current_part:
                parts[f"{path}__part{idx}"] = ''.join(current_part)
                current_part = [line]
                current_tokens = line_tokens
                idx += 1
            else:
                current_part.append(line)
                current_tokens += line_tokens

        if current_part:
            parts[f"{path}__part{idx}"] = ''.join(current_part)

        return parts

