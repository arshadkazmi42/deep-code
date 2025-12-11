#!/usr/bin/env python3
"""
Context and token management for Deep Code
Helps manage conversation context and stay within token limits
"""

import tiktoken
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class TokenStats:
    """Token usage statistics"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    max_tokens: int
    percentage_used: float


class ContextManager:
    """Manages conversation context and token limits"""

    # Model token limits (approximate)
    MODEL_LIMITS = {
        'deepseek-chat': 64000,  # DeepSeek chat model context window
        'deepseek-coder': 16000,  # DeepSeek coder model
        'gpt-4': 8192,
        'gpt-4-32k': 32768,
        'gpt-3.5-turbo': 4096,
        'gpt-3.5-turbo-16k': 16384,
    }

    def __init__(self, model: str = 'deepseek-chat', reserve_tokens: int = 4000):
        """
        Initialize context manager

        Args:
            model: Model name
            reserve_tokens: Tokens to reserve for response
        """
        self.model = model
        self.reserve_tokens = reserve_tokens
        self.max_tokens = self.MODEL_LIMITS.get(model, 64000)

        # Try to get appropriate tokenizer
        try:
            # Use cl100k_base for DeepSeek (similar to GPT-4)
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except:
            # Fallback to simple approximation
            self.encoding = None

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            # Rough approximation: 1 token ≈ 4 characters
            return len(text) // 4

    def count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Count tokens in message list"""
        total = 0
        for message in messages:
            # Account for message structure overhead (~4 tokens per message)
            total += 4
            total += self.count_tokens(message.get('content', ''))
            total += self.count_tokens(message.get('role', ''))
        return total

    def get_token_stats(self, messages: List[Dict[str, str]],
                       completion_tokens: int = 0) -> TokenStats:
        """Get token usage statistics"""
        prompt_tokens = self.count_messages_tokens(messages)
        total_tokens = prompt_tokens + completion_tokens
        percentage_used = (total_tokens / self.max_tokens) * 100

        return TokenStats(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            max_tokens=self.max_tokens,
            percentage_used=percentage_used
        )

    def can_fit_message(self, messages: List[Dict[str, str]], new_message: str) -> bool:
        """Check if a new message will fit in context"""
        current_tokens = self.count_messages_tokens(messages)
        new_tokens = self.count_tokens(new_message)
        total = current_tokens + new_tokens + self.reserve_tokens
        return total <= self.max_tokens

    def truncate_messages(self, messages: List[Dict[str, str]],
                         target_tokens: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Truncate messages to fit within token limit
        Preserves system message and most recent messages

        Args:
            messages: Message list
            target_tokens: Target token count (default: max_tokens - reserve_tokens)
        """
        if target_tokens is None:
            target_tokens = self.max_tokens - self.reserve_tokens

        current_tokens = self.count_messages_tokens(messages)

        if current_tokens <= target_tokens:
            return messages

        # Always keep system message (first message)
        if not messages:
            return []

        system_message = messages[0] if messages[0]['role'] == 'system' else None
        other_messages = messages[1:] if system_message else messages

        # Calculate system message tokens
        system_tokens = self.count_messages_tokens([system_message]) if system_message else 0
        available_tokens = target_tokens - system_tokens

        # Keep most recent messages that fit
        truncated = []
        current_size = 0

        for message in reversed(other_messages):
            message_tokens = self.count_messages_tokens([message])
            if current_size + message_tokens <= available_tokens:
                truncated.insert(0, message)
                current_size += message_tokens
            else:
                break

        # Reconstruct with system message
        result = []
        if system_message:
            result.append(system_message)
        result.extend(truncated)

        return result

    def summarize_old_messages(self, messages: List[Dict[str, str]],
                               keep_recent: int = 10) -> List[Dict[str, str]]:
        """
        Summarize old messages to save tokens
        Keeps system message and recent messages, summarizes middle ones

        Args:
            messages: Message list
            keep_recent: Number of recent messages to keep unsummarized
        """
        if len(messages) <= keep_recent + 1:  # +1 for system message
            return messages

        system_message = messages[0] if messages and messages[0]['role'] == 'system' else None
        start_idx = 1 if system_message else 0

        # Messages to summarize
        to_summarize = messages[start_idx:-keep_recent]
        recent = messages[-keep_recent:]

        if not to_summarize:
            return messages

        # Create summary
        summary_parts = []
        for msg in to_summarize:
            role = msg['role']
            content = msg['content'][:200]  # First 200 chars
            summary_parts.append(f"{role}: {content}...")

        summary_message = {
            'role': 'system',
            'content': f"[Previous conversation summary]\n" + "\n".join(summary_parts)
        }

        # Reconstruct
        result = []
        if system_message:
            result.append(system_message)
        result.append(summary_message)
        result.extend(recent)

        return result

    def optimize_context(self, messages: List[Dict[str, str]],
                        strategy: str = 'truncate') -> List[Dict[str, str]]:
        """
        Optimize context to fit within limits

        Args:
            messages: Message list
            strategy: 'truncate' or 'summarize'
        """
        current_tokens = self.count_messages_tokens(messages)
        target_tokens = self.max_tokens - self.reserve_tokens

        if current_tokens <= target_tokens:
            return messages

        if strategy == 'truncate':
            return self.truncate_messages(messages, target_tokens)
        elif strategy == 'summarize':
            return self.summarize_old_messages(messages)
        else:
            return self.truncate_messages(messages, target_tokens)


class MessageBuilder:
    """Helper for building well-structured messages"""

    @staticmethod
    def system(content: str) -> Dict[str, str]:
        """Create system message"""
        return {'role': 'system', 'content': content}

    @staticmethod
    def user(content: str) -> Dict[str, str]:
        """Create user message"""
        return {'role': 'user', 'content': content}

    @staticmethod
    def assistant(content: str) -> Dict[str, str]:
        """Create assistant message"""
        return {'role': 'assistant', 'content': content}

    @staticmethod
    def format_tool_result(tool_name: str, result: str, success: bool = True) -> str:
        """Format tool execution result"""
        status = "✓" if success else "✗"
        return f"[{status} {tool_name} Tool]\n{result}"

    @staticmethod
    def format_file_content(file_path: str, content: str, line_numbers: bool = True) -> str:
        """Format file content for context"""
        if line_numbers:
            return f"File: {file_path}\n```\n{content}\n```"
        else:
            lines = content.split('\n')
            numbered = [f"{i+1:4d} | {line}" for i, line in enumerate(lines)]
            return f"File: {file_path}\n```\n" + '\n'.join(numbered) + "\n```"

    @staticmethod
    def format_directory_tree(tree_output: str) -> str:
        """Format directory tree"""
        return f"Directory Structure:\n```\n{tree_output}\n```"

    @staticmethod
    def format_command_output(command: str, output: str, return_code: int) -> str:
        """Format command output"""
        status = "✓" if return_code == 0 else "✗"
        return f"[{status} Command: {command}]\nExit Code: {return_code}\n{output}"
