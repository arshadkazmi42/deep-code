#!/usr/bin/env python3
"""
Structured tool system for Deep Code - similar to Claude Code's tools
Includes: Read, Write, Edit, Glob, Grep, Bash, WebSearch, WebFetch tools
"""

import os
import re
import subprocess
import glob as glob_module
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup
import json


@dataclass
class ToolResult:
    """Result from a tool execution"""
    success: bool
    output: str
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class Tool:
    """Base class for all tools"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters"""
        raise NotImplementedError


class ReadTool(Tool):
    """Read file contents with line numbers and range support"""

    def __init__(self):
        super().__init__(
            "Read",
            "Read file contents. Supports line ranges and shows line numbers."
        )

    def execute(self, file_path: str, start_line: Optional[int] = None,
                end_line: Optional[int] = None, max_lines: int = 10000) -> ToolResult:
        """
        Read file contents

        Args:
            file_path: Path to file to read
            start_line: Optional starting line number (1-indexed)
            end_line: Optional ending line number (1-indexed)
            max_lines: Maximum number of lines to read
        """
        try:
            path = Path(file_path).expanduser().resolve()

            if not path.exists():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"File not found: {path}"
                )

            if not path.is_file():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Not a file: {path}"
                )

            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            total_lines = len(lines)

            # Handle line range
            if start_line is not None:
                start_idx = max(0, start_line - 1)
            else:
                start_idx = 0

            if end_line is not None:
                end_idx = min(total_lines, end_line)
            else:
                end_idx = min(total_lines, start_idx + max_lines)

            # Format with line numbers
            output_lines = []
            for i in range(start_idx, end_idx):
                line_num = i + 1
                line_content = lines[i].rstrip('\n')
                output_lines.append(f"{line_num:6d}\t{line_content}")

            output = '\n'.join(output_lines)

            metadata = {
                'total_lines': total_lines,
                'lines_shown': end_idx - start_idx,
                'start_line': start_idx + 1,
                'end_line': end_idx
            }

            return ToolResult(
                success=True,
                output=output,
                metadata=metadata
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Error reading file: {str(e)}"
            )


class WriteTool(Tool):
    """Write content to a file (creates or overwrites)"""

    def __init__(self):
        super().__init__(
            "Write",
            "Write content to a file. Creates new file or overwrites existing."
        )

    def execute(self, file_path: str, content: str, create_dirs: bool = True) -> ToolResult:
        """
        Write content to file

        Args:
            file_path: Path to file to write
            content: Content to write
            create_dirs: Create parent directories if they don't exist
        """
        try:
            path = Path(file_path).expanduser().resolve()

            # Create parent directories if needed
            if create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)

            path.write_text(content, encoding='utf-8')

            return ToolResult(
                success=True,
                output=f"Successfully wrote {len(content)} bytes to {path}",
                metadata={'file_path': str(path), 'bytes_written': len(content)}
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Error writing file: {str(e)}"
            )


class EditTool(Tool):
    """Edit file by replacing exact string matches - like Claude Code's Edit tool"""

    def __init__(self):
        super().__init__(
            "Edit",
            "Edit file by replacing exact string matches. Must match exactly including whitespace."
        )

    def execute(self, file_path: str, old_string: str, new_string: str,
                replace_all: bool = False) -> ToolResult:
        """
        Edit file by replacing exact matches

        Args:
            file_path: Path to file to edit
            old_string: Exact string to find (must match exactly with indentation)
            new_string: String to replace with
            replace_all: If True, replace all occurrences. If False, must have exactly one match.
        """
        try:
            path = Path(file_path).expanduser().resolve()

            if not path.exists():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"File not found: {path}"
                )

            # Read file content
            content = path.read_text(encoding='utf-8')

            # Count occurrences
            count = content.count(old_string)

            if count == 0:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"String not found in file. Make sure to match exact indentation and whitespace."
                )

            if not replace_all and count > 1:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Found {count} occurrences. String must be unique or use replace_all=True."
                )

            # Perform replacement
            if replace_all:
                new_content = content.replace(old_string, new_string)
                replacements = count
            else:
                new_content = content.replace(old_string, new_string, 1)
                replacements = 1

            # Write back
            path.write_text(new_content, encoding='utf-8')

            return ToolResult(
                success=True,
                output=f"Successfully replaced {replacements} occurrence(s) in {path}",
                metadata={
                    'file_path': str(path),
                    'replacements': replacements
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Error editing file: {str(e)}"
            )


class GlobTool(Tool):
    """Find files matching glob patterns"""

    def __init__(self):
        super().__init__(
            "Glob",
            "Find files matching glob patterns (e.g., '**/*.py', 'src/**/*.js')"
        )

    def execute(self, pattern: str, path: str = ".",
                ignore_patterns: Optional[List[str]] = None,
                max_results: int = 1000) -> ToolResult:
        """
        Find files matching pattern

        Args:
            pattern: Glob pattern (e.g., '**/*.py')
            path: Base path to search from
            ignore_patterns: Patterns to ignore (e.g., ['**/__pycache__/**', '**/node_modules/**'])
            max_results: Maximum number of results to return
        """
        try:
            base_path = Path(path).expanduser().resolve()

            if not base_path.exists():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Path not found: {base_path}"
                )

            # Default ignore patterns
            if ignore_patterns is None:
                ignore_patterns = [
                    '**/__pycache__/**',
                    '**/node_modules/**',
                    '**/.git/**',
                    '**/venv/**',
                    '**/.venv/**',
                    '**/env/**',
                    '**/dist/**',
                    '**/build/**',
                    '**/.next/**',
                    '**/.pytest_cache/**',
                ]

            # Find matches
            matches = []
            for match in base_path.glob(pattern):
                # Check if match should be ignored
                should_ignore = False
                for ignore_pattern in ignore_patterns:
                    if match.match(ignore_pattern):
                        should_ignore = True
                        break

                if not should_ignore and match.is_file():
                    try:
                        rel_path = match.relative_to(Path.cwd())
                        matches.append(str(rel_path))
                    except ValueError:
                        matches.append(str(match))

                if len(matches) >= max_results:
                    break

            # Sort by modification time (most recent first)
            matches.sort(key=lambda x: Path(x).stat().st_mtime, reverse=True)

            if matches:
                output = '\n'.join(matches)
                return ToolResult(
                    success=True,
                    output=output,
                    metadata={'count': len(matches), 'truncated': len(matches) >= max_results}
                )
            else:
                return ToolResult(
                    success=True,
                    output=f"No files found matching pattern: {pattern}",
                    metadata={'count': 0}
                )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Error globbing files: {str(e)}"
            )


class GrepTool(Tool):
    """Search file contents using regex patterns"""

    def __init__(self):
        super().__init__(
            "Grep",
            "Search file contents using regex patterns. Like ripgrep/grep."
        )

    def execute(self, pattern: str, path: str = ".",
                file_pattern: Optional[str] = None,
                ignore_case: bool = False,
                max_results: int = 100,
                context_lines: int = 0) -> ToolResult:
        """
        Search for pattern in files

        Args:
            pattern: Regex pattern to search for
            path: Path to search in (file or directory)
            file_pattern: Optional glob pattern to filter files (e.g., '*.py')
            ignore_case: Case-insensitive search
            max_results: Maximum number of matches to return
            context_lines: Number of context lines to show around matches
        """
        try:
            search_path = Path(path).expanduser().resolve()

            if not search_path.exists():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Path not found: {search_path}"
                )

            # Compile regex
            flags = re.MULTILINE
            if ignore_case:
                flags |= re.IGNORECASE

            try:
                regex = re.compile(pattern, flags)
            except re.error as e:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Invalid regex pattern: {str(e)}"
                )

            # Determine files to search
            if search_path.is_file():
                files_to_search = [search_path]
            else:
                # Search directory
                if file_pattern:
                    files_to_search = list(search_path.glob(f"**/{file_pattern}"))
                else:
                    # Default: search common code files
                    extensions = ['*.py', '*.js', '*.ts', '*.jsx', '*.tsx', '*.java',
                                '*.go', '*.rs', '*.cpp', '*.c', '*.h', '*.rb', '*.php',
                                '*.sh', '*.md', '*.txt', '*.json', '*.yml', '*.yaml']
                    files_to_search = []
                    for ext in extensions:
                        files_to_search.extend(search_path.glob(f"**/{ext}"))

                # Filter out ignored directories
                ignore_patterns = ['__pycache__', 'node_modules', '.git', 'venv',
                                 '.venv', 'env', 'dist', 'build']
                files_to_search = [
                    f for f in files_to_search
                    if not any(ignore in str(f) for ignore in ignore_patterns)
                ]

            # Search files
            matches = []
            for file_path in files_to_search:
                if not file_path.is_file():
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()

                    for line_num, line in enumerate(lines, 1):
                        if regex.search(line):
                            # Get context lines
                            context_start = max(0, line_num - 1 - context_lines)
                            context_end = min(len(lines), line_num + context_lines)

                            match_info = {
                                'file': str(file_path),
                                'line_num': line_num,
                                'line': line.rstrip('\n'),
                                'context': [lines[i].rstrip('\n') for i in range(context_start, context_end)]
                            }
                            matches.append(match_info)

                            if len(matches) >= max_results:
                                break

                except Exception:
                    # Skip files that can't be read
                    continue

                if len(matches) >= max_results:
                    break

            # Format output
            if matches:
                output_parts = []
                for match in matches:
                    try:
                        rel_path = Path(match['file']).relative_to(Path.cwd())
                    except ValueError:
                        rel_path = Path(match['file'])

                    output_parts.append(f"{rel_path}:{match['line_num']}: {match['line']}")

                output = '\n'.join(output_parts)
                return ToolResult(
                    success=True,
                    output=output,
                    metadata={'count': len(matches), 'truncated': len(matches) >= max_results}
                )
            else:
                return ToolResult(
                    success=True,
                    output=f"No matches found for pattern: {pattern}",
                    metadata={'count': 0}
                )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Error searching files: {str(e)}"
            )


class BashTool(Tool):
    """Execute bash commands with safety checks"""

    # Dangerous commands that require confirmation
    DANGEROUS_COMMANDS = [
        'rm -rf', 'rm -fr', 'rm -r', 'rm -f',
        'mkfs', 'dd if=', 'format',
        ':(){:|:&};:', # fork bomb
        '> /dev/sd',
    ]

    def __init__(self):
        super().__init__(
            "Bash",
            "Execute bash commands. Dangerous commands require confirmation."
        )

    def execute(self, command: str, cwd: Optional[str] = None,
                timeout: int = 30, confirm_dangerous: bool = False) -> ToolResult:
        """
        Execute bash command

        Args:
            command: Command to execute
            cwd: Working directory
            timeout: Command timeout in seconds
            confirm_dangerous: If True, allows dangerous commands
        """
        try:
            # Check for dangerous commands
            is_dangerous = any(danger in command.lower() for danger in self.DANGEROUS_COMMANDS)

            if is_dangerous and not confirm_dangerous:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Dangerous command detected. Requires explicit confirmation: {command}"
                )

            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd or os.getcwd(),
                timeout=timeout,
                executable='/bin/bash'
            )

            output_parts = []
            if result.stdout:
                output_parts.append(f"STDOUT:\n{result.stdout}")
            if result.stderr:
                output_parts.append(f"STDERR:\n{result.stderr}")

            output = '\n'.join(output_parts) if output_parts else "(no output)"

            return ToolResult(
                success=result.returncode == 0,
                output=output,
                error=None if result.returncode == 0 else f"Command failed with exit code {result.returncode}",
                metadata={'return_code': result.returncode}
            )

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output="",
                error=f"Command timed out after {timeout} seconds"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Error executing command: {str(e)}"
            )


class WebSearchTool(Tool):
    """Search the web using DuckDuckGo"""

    def __init__(self):
        super().__init__(
            "WebSearch",
            "Search the web using DuckDuckGo"
        )

    def execute(self, query: str, num_results: int = 5) -> ToolResult:
        """
        Perform web search

        Args:
            query: Search query
            num_results: Number of results to return
        """
        try:
            url = "https://html.duckduckgo.com/html/"
            params = {"q": query}
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            results = []

            for result in soup.find_all('div', class_='result')[:num_results]:
                title_elem = result.find('a', class_='result__a')
                snippet_elem = result.find('a', class_='result__snippet')

                if title_elem:
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    results.append(f"**{title}**\n{link}\n{snippet}\n")

            if results:
                output = '\n'.join(results)
                return ToolResult(
                    success=True,
                    output=output,
                    metadata={'count': len(results)}
                )
            else:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"No results found for: {query}"
                )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Search error: {str(e)}"
            )


class WebFetchTool(Tool):
    """Fetch content from URLs (like curl)"""

    def __init__(self):
        super().__init__(
            "WebFetch",
            "Fetch content from URLs. Supports GET, POST, PUT, DELETE methods."
        )

    def execute(self, url: str, method: str = "GET",
                headers: Optional[Dict[str, str]] = None,
                data: Optional[str] = None,
                json_data: Optional[Dict] = None,
                timeout: int = 30) -> ToolResult:
        """
        Fetch URL content

        Args:
            url: URL to fetch
            method: HTTP method (GET, POST, PUT, DELETE)
            headers: Optional HTTP headers
            data: Optional request body (string)
            json_data: Optional JSON request body
            timeout: Request timeout in seconds
        """
        try:
            request_headers = headers or {}
            if json_data:
                request_headers['Content-Type'] = 'application/json'

            method = method.upper()

            # Make request
            if method == "GET":
                response = requests.get(url, headers=request_headers, timeout=timeout)
            elif method == "POST":
                if json_data:
                    response = requests.post(url, json=json_data, headers=request_headers, timeout=timeout)
                else:
                    response = requests.post(url, data=data, headers=request_headers, timeout=timeout)
            elif method == "PUT":
                if json_data:
                    response = requests.put(url, json=json_data, headers=request_headers, timeout=timeout)
                else:
                    response = requests.put(url, data=data, headers=request_headers, timeout=timeout)
            elif method == "DELETE":
                response = requests.delete(url, headers=request_headers, timeout=timeout)
            else:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Unsupported HTTP method: {method}"
                )

            # Format output
            output_parts = [
                f"Status: {response.status_code} {response.reason}",
                f"\nHeaders:",
                json.dumps(dict(response.headers), indent=2),
                f"\nBody:"
            ]

            # Try to parse as JSON
            try:
                body = json.dumps(response.json(), indent=2)
                output_parts.append(body[:5000])  # Limit body size
                if len(response.text) > 5000:
                    output_parts.append(f"\n... (truncated, total {len(response.text)} bytes)")
            except:
                body = response.text[:5000]
                output_parts.append(body)
                if len(response.text) > 5000:
                    output_parts.append(f"\n... (truncated, total {len(response.text)} bytes)")

            output = '\n'.join(output_parts)

            return ToolResult(
                success=response.status_code < 400,
                output=output,
                metadata={
                    'status_code': response.status_code,
                    'content_length': len(response.text)
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Request error: {str(e)}"
            )


class ToolRegistry:
    """Registry for all available tools"""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """Register all default tools"""
        self.register(ReadTool())
        self.register(WriteTool())
        self.register(EditTool())
        self.register(GlobTool())
        self.register(GrepTool())
        self.register(BashTool())
        self.register(WebSearchTool())
        self.register(WebFetchTool())

    def register(self, tool: Tool):
        """Register a tool"""
        self.tools[tool.name.lower()] = tool

    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self.tools.get(name.lower())

    def list_tools(self) -> List[str]:
        """List all available tools"""
        return list(self.tools.keys())

    def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool by name"""
        tool = self.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool not found: {tool_name}"
            )
        return tool.execute(**kwargs)
