#!/usr/bin/env python3
"""
Deep Code - CLI tool powered by DeepSeek API
Exact replica of Claude Code CLI but using DeepSeek's API
"""

import os
import sys
import argparse
import json
import subprocess
import shlex
import re
import uuid
import sqlite3
import signal
import threading
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Prompt, Confirm
from rich.live import Live
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.layout import Layout
from rich.align import Align
import openai
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Import utils for file editing
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from utils import extract_code_blocks, detect_file_edit_request, apply_code_changes
except ImportError:
    # Fallback if utils.py not available - define inline
    def extract_code_blocks(text: str):
        """Extract code blocks from markdown text"""
        pattern = r'```(?:(?:(\w+))?(?::\s*(.+?))?\n)?(.*?)```'
        matches = re.finditer(pattern, text, re.DOTALL | re.MULTILINE)
        blocks = []
        for match in matches:
            language = match.group(1) or ""
            file_path = match.group(2) or ""
            code = match.group(3) or ""
            if file_path:
                file_path = file_path.strip()
                for prefix in ['File:', 'file:', 'Path:', 'path:']:
                    if file_path.startswith(prefix):
                        file_path = file_path[len(prefix):].strip()
            if code.strip():
                blocks.append({'language': language, 'file_path': file_path, 'code': code})
        return blocks
    
    def detect_file_edit_request(user_input: str, response: str):
        """Detect if user wants to edit a file"""
        edit_keywords = ['edit', 'modify', 'update', 'change', 'fix', 'add', 'remove', 'replace', 'insert', 'delete', 'write', 'create', 'implement']
        if not any(keyword in user_input.lower() for keyword in edit_keywords):
            return None
        file_patterns = [
            r'(?:in|to|from|file|the)\s+([^\s]+\.(?:py|js|ts|jsx|tsx|java|go|rs|cpp|c|h|rb|php|sh|md|txt|json|yml|yaml|html|css))',
            r'["\']([^"\']+\.\w+)["\']',
            r'([a-zA-Z0-9_/\.]+\.\w+)',
        ]
        file_path = None
        for pattern in file_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                file_path = match.group(1)
                break
        code_blocks = extract_code_blocks(response)
        if file_path or code_blocks:
            return {'file_path': file_path, 'code_blocks': code_blocks, 'full_response': response}
        return None
    
    def apply_code_changes(file_path: str, new_code: str, mode: str = 'replace'):
        """Apply code changes to a file"""
        try:
            path = Path(file_path).expanduser().resolve()
            path.write_text(new_code, encoding='utf-8')
            return (True, f"✓ Updated {path}")
        except Exception as e:
            return (False, f"✗ Error updating file: {str(e)}")

# Load environment variables
load_dotenv()

console = Console()

# Global interrupt flag
interrupt_flag = threading.Event()

# Default DeepSeek API configuration
DEFAULT_API_BASE = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-reasoner"  # Research model for step-by-step reasoning

# Session storage
SESSION_DB = Path.home() / ".deepcode" / "sessions.db"
SESSION_DIR = Path.home() / ".deepcode"
SESSION_DIR.mkdir(parents=True, exist_ok=True)


class SessionManager:
    """Manage conversation sessions"""
    
    def __init__(self):
        self._init_db()
    
    def _init_db(self):
        """Initialize session database"""
        conn = sqlite3.connect(SESSION_DB)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                directory TEXT,
                created_at TEXT,
                updated_at TEXT,
                messages TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def get_recent_session(self, directory: str = None) -> Optional[str]:
        """Get most recent session ID"""
        conn = sqlite3.connect(SESSION_DB)
        cursor = conn.cursor()
        
        if directory:
            cursor.execute("""
                SELECT session_id FROM sessions 
                WHERE directory = ? 
                ORDER BY updated_at DESC 
                LIMIT 1
            """, (directory,))
        else:
            cursor.execute("""
                SELECT session_id FROM sessions 
                ORDER BY updated_at DESC 
                LIMIT 1
            """)
        
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def save_session(self, session_id: str, directory: str, messages: List[Dict]):
        """Save session"""
        conn = sqlite3.connect(SESSION_DB)
        conn.execute("""
            INSERT OR REPLACE INTO sessions (session_id, directory, created_at, updated_at, messages)
            VALUES (?, ?, COALESCE((SELECT created_at FROM sessions WHERE session_id = ?), ?), ?, ?)
        """, (session_id, directory, session_id, datetime.now().isoformat(), datetime.now().isoformat(), json.dumps(messages)))
        conn.commit()
        conn.close()
    
    def load_session(self, session_id: str) -> Optional[List[Dict]]:
        """Load session messages"""
        conn = sqlite3.connect(SESSION_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT messages FROM sessions WHERE session_id = ?", (session_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        return None
    
    def update_session(self, session_id: str, messages: List[Dict]):
        """Update session"""
        conn = sqlite3.connect(SESSION_DB)
        conn.execute("""
            UPDATE sessions SET updated_at = ?, messages = ? WHERE session_id = ?
        """, (datetime.now().isoformat(), json.dumps(messages), session_id))
        conn.commit()
        conn.close()


class DeepSeekClient:
    """Client for interacting with DeepSeek API"""
    
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.api_base = api_base or os.getenv("DEEPSEEK_API_BASE", DEFAULT_API_BASE)
        self.model = model or os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL)
        
        if not self.api_key:
            console.print("[red]Error: DEEPSEEK_API_KEY not found. Please set it in your environment or .env file.[/red]")
            sys.exit(1)
        
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.api_base
        )
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = True,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ):
        """Send a chat request to DeepSeek API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=stream,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response
        except Exception as e:
            console.print(f"[red]Error calling DeepSeek API: {str(e)}[/red]")
            sys.exit(1)


def load_file_context(file_path: str, max_lines: int = 10000) -> str:
    """Load file content for context"""
    try:
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            return ""
        
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        if len(lines) > max_lines:
            lines = lines[:max_lines]
        
        content = ''.join(lines)
        return f"File: {path}\n```\n{content}\n```"
    except Exception as e:
        return ""


def load_directory_context(dir_path: str = ".", max_files: int = 100, max_file_size: int = 100000) -> str:
    """Load directory structure and key files for context"""
    try:
        path = Path(dir_path).expanduser().resolve()
        if not path.exists():
            return ""
        
        if not path.is_dir():
            return load_file_context(str(path))
        
        context_parts = [f"# Directory: {path}\n\n"]
        
        # Get directory structure
        try:
            tree_output = subprocess.run(
                ["tree", "-L", "3", "-I", "__pycache__|*.pyc|node_modules|.git|venv|env|.venv|dist|build"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if tree_output.returncode == 0:
                context_parts.append("## Directory Structure\n```\n")
                context_parts.append(tree_output.stdout[:3000])
                context_parts.append("```\n\n")
        except:
            pass
        
        # Get file structure
        code_extensions = [
            '*.py', '*.js', '*.ts', '*.jsx', '*.tsx', '*.java', '*.go', '*.rs', 
            '*.cpp', '*.c', '*.h', '*.hpp', '*.rb', '*.php', '*.swift', '*.kt',
            '*.sh', '*.bash', '*.zsh', '*.fish', '*.ps1', '*.bat', '*.yml', 
            '*.yaml', '*.json', '*.xml', '*.html', '*.css', '*.scss', '*.sql',
            '*.md', '*.txt', '*.env', '*.config', '*.conf', '*.toml'
        ]
        
        files = []
        for ext in code_extensions:
            files.extend(path.rglob(ext))
        
        # Filter out common ignore patterns
        ignore_patterns = ['__pycache__', '.git', 'node_modules', 'venv', 'env', '.venv', 
                          '.pytest_cache', 'dist', 'build', '.next', '.nuxt', 'target']
        files = [f for f in files if not any(ignore in str(f) for ignore in ignore_patterns)]
        files = files[:max_files]
        
        # Key files first
        key_files = [
            'README.md', 'README.txt', 'README', 'package.json', 'requirements.txt', 
            'setup.py', 'pyproject.toml', 'Cargo.toml', 'go.mod', 'pom.xml', 'build.gradle',
            'Makefile', 'docker-compose.yml', '.env.example', 'Dockerfile', 
            'composer.json', 'Gemfile', 'Pipfile'
        ]
        
        context_parts.append("## Key Files\n\n")
        for key_file in key_files:
            key_path = path / key_file
            if key_path.exists():
                try:
                    size = key_path.stat().st_size
                    if size < max_file_size:
                        content = key_path.read_text(encoding='utf-8', errors='ignore')[:5000]
                        context_parts.append(f"### {key_file}\n```\n{content}\n```\n\n")
                except:
                    pass
        
        # Sample code files
        code_files = [f for f in files if f.suffix in ['.py', '.js', '.ts', '.go', '.rs', '.java', '.cpp', '.c', '.rb', '.php']]
        context_parts.append("## Sample Code Files\n\n")
        for f in code_files[:15]:
            try:
                size = f.stat().st_size
                if size < max_file_size:
                    content = f.read_text(encoding='utf-8', errors='ignore')[:5000]
                    rel_path = f.relative_to(path)
                    context_parts.append(f"### {rel_path}\n```\n{content}\n```\n\n")
            except:
                pass
        
        return ''.join(context_parts)
    except Exception as e:
        return ""


def execute_bash(command: str, cwd: Optional[str] = None, timeout: int = 30) -> Tuple[str, str, int]:
    """Execute a bash command"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd or os.getcwd(),
            timeout=timeout,
            executable='/bin/bash'
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 124
    except Exception as e:
        return "", str(e), 1


def web_search(query: str, num_results: int = 5) -> str:
    """Perform a web search"""
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
                results.append(f"Title: {title}\nLink: {link}\nSnippet: {snippet}\n")
        
        if results:
            return "\n".join(results)
        else:
            return f"Web search performed for: {query}"
    except Exception as e:
        return f"Web search attempted for: {query} (Failed: {str(e)})"


def curl_request(url: str, method: str = "GET", headers: Dict[str, str] = None, data: str = None, json_data: Dict = None) -> str:
    """Perform an HTTP request"""
    try:
        request_headers = headers or {}
        if json_data:
            request_headers['Content-Type'] = 'application/json'
        
        method = method.upper()
        
        if method == "GET":
            response = requests.get(url, headers=request_headers, timeout=30)
        elif method == "POST":
            if json_data:
                response = requests.post(url, json=json_data, headers=request_headers, timeout=30)
            else:
                response = requests.post(url, data=data, headers=request_headers, timeout=30)
        elif method == "PUT":
            if json_data:
                response = requests.put(url, json=json_data, headers=request_headers, timeout=30)
            else:
                response = requests.put(url, data=data, headers=request_headers, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, headers=request_headers, timeout=30)
        else:
            return f"Unsupported HTTP method: {method}"
        
        result = f"Status Code: {response.status_code}\n"
        result += f"Headers:\n{json.dumps(dict(response.headers), indent=2)}\n\n"
        
        try:
            result += f"Response Body (JSON):\n{json.dumps(response.json(), indent=2)}\n"
        except:
            text_response = response.text[:10000]
            result += f"Response Body (Text):\n{text_response}\n"
            if len(response.text) > 10000:
                result += f"\n... (truncated, total {len(response.text)} characters)\n"
        
        return result
    except Exception as e:
        return f"Error performing request: {str(e)}"


def format_response_with_syntax(text: str) -> None:
    """Format response with proper syntax highlighting and structure"""
    # Split into code blocks and text
    code_block_pattern = r'```(\w+)?\n(.*?)```'
    parts = []
    last_end = 0
    
    for match in re.finditer(code_block_pattern, text, re.DOTALL):
        # Text before code block
        if match.start() > last_end:
            text_before = text[last_end:match.start()].strip()
            if text_before:
                parts.append(('text', text_before))
        
        # Code block
        language = match.group(1) or 'text'
        code = match.group(2)
        parts.append(('code', language, code))
        last_end = match.end()
    
    # Remaining text
    if last_end < len(text):
        remaining = text[last_end:].strip()
        if remaining:
            parts.append(('text', remaining))
    
    # If no code blocks found, print as markdown
    if not parts:
        console.print(Markdown(text))
        return
    
    # Print formatted parts
    for part in parts:
        if part[0] == 'text':
            console.print(Markdown(part[1]))
        elif part[0] == 'code':
            language = part[1]
            code = part[2]
            console.print(Panel(
                Syntax(code, language, theme="monokai", line_numbers=True),
                title=f"[bold]{language}[/bold]",
                border_style="blue"
            ))


def stream_response(response, show_progress: bool = True) -> str:
    """Stream and display response from API with progress indicator"""
    collected_content = []
    
    if hasattr(response, '__iter__'):
        # Show progress while streaming
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("[cyan]Generating response...", total=None)
            
            for chunk in response:
                if interrupt_flag.is_set():
                    console.print("\n[yellow]Response interrupted by user[/yellow]")
                    break
                    
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        collected_content.append(delta.content)
                        console.print(delta.content, end="")
        
        console.print()  # New line after streaming
        return ''.join(collected_content)
    else:
        content = response.choices[0].message.content
        format_response_with_syntax(content)
        return content


def parse_tool_calls(user_input: str, current_dir: str = None) -> Dict[str, Any]:
    """Parse user input for tool calls - both explicit and implicit"""
    tools = {}
    
    # Explicit tool calls
    if '@web' in user_input.lower() or '@search' in user_input.lower():
        match = re.search(r'@(?:web|search)\s+(.+)', user_input, re.IGNORECASE)
        if match:
            tools['web_search'] = match.group(1).strip()
    
    if '@curl' in user_input.lower() or '@request' in user_input.lower():
        match = re.search(r'@(?:curl|request)\s+(.+)', user_input, re.IGNORECASE)
        if match:
            tools['curl'] = match.group(1).strip()
    
    if '@bash' in user_input.lower() or '@exec' in user_input.lower() or '@run' in user_input.lower():
        match = re.search(r'@(?:bash|exec|run)\s+(.+)', user_input, re.IGNORECASE)
        if match:
            tools['bash'] = match.group(1).strip()
    
    # Implicit file reading - detect file paths in query
    file_patterns = [
        r'file\s+([^\s]+)',  # "file path/to/file"
        r'read\s+([^\s]+)',  # "read path/to/file"
        r'analyze\s+([^\s]+\.\w+)',  # "analyze file.py"
        r'([^\s]+\.(py|js|ts|jsx|tsx|java|go|rs|cpp|c|h|rb|php|sh|md|txt|json|yml|yaml))\b',  # File extensions
        r'["\']([^"\']+\.\w+)["\']',  # Quoted file paths
    ]
    
    for pattern in file_patterns:
        matches = re.findall(pattern, user_input, re.IGNORECASE)
        for match in matches:
            file_path = match if isinstance(match, str) else match[0] if match else None
            if file_path:
                # Resolve relative paths
                if current_dir:
                    full_path = Path(current_dir) / file_path
                    if full_path.exists():
                        tools.setdefault('files', []).append(str(full_path))
                else:
                    test_path = Path(file_path)
                    if test_path.exists():
                        tools.setdefault('files', []).append(file_path)
    
    # Implicit bash commands - detect command-like queries
    bash_patterns = [
        r'(?:run|execute|run the command)\s+(.+?)(?:\.|$|and)',
        r'(?:git|npm|pip|python|node|docker)\s+([^\s]+(?:\s+[^\s]+)*)',
    ]
    
    if not tools.get('bash'):  # Only if no explicit @bash
        for pattern in bash_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                potential_cmd = match.group(1).strip()
                # Don't auto-execute dangerous commands
                dangerous = ['rm -rf', 'delete', 'format', 'mkfs']
                if not any(d in potential_cmd.lower() for d in dangerous):
                    tools['bash'] = potential_cmd
                    break
    
    # Implicit web search - detect questions needing web info
    web_indicators = ['latest', 'current', 'recent', 'what is', 'how to', 'tutorial', 'documentation']
    if not tools.get('web_search') and any(indicator in user_input.lower() for indicator in web_indicators):
        # Extract the search query
        tools['web_search'] = user_input[:100]  # Use part of query as search
    
    return tools


def build_system_prompt(add_dirs: List[str] = None, system_prompt: str = None, append_system_prompt: str = None) -> str:
    """Build system prompt"""
    base_prompt = """You are a helpful coding assistant with access to various tools that you can use automatically based on user requests:

TOOLS AVAILABLE:
1. FILE OPERATIONS: You can read, analyze, and understand files. When users mention files, automatically read them.
2. DIRECTORY ANALYSIS: You have access to the current directory structure and codebase. Use this context automatically.
3. WEB SEARCH: Use @web or @search followed by a query to search the web when you need current information.
4. HTTP REQUESTS: Use @curl or @request followed by a URL to make HTTP requests when users ask for API calls or web data.
5. BASH EXECUTION: Use @bash, @exec, or @run followed by a command to execute shell commands when users want to run code, git operations, or system commands.

BEHAVIOR:
- Automatically use tools when appropriate - don't wait for explicit permission
- If user mentions a file path, automatically read it using the file system
- If user asks about code in the current directory, use the directory context provided
- If user asks for web information, use @web to search
- If user wants to run a command, use @bash to execute it
- If user asks to edit/modify/update/fix a file, provide the complete updated code in a code block with the file path
- When providing code changes, format as: ```language:path/to/file\n[complete code]\n```
- Always explain what you're doing before executing potentially destructive commands
- Show tool outputs clearly and use them to answer questions
- When editing files, provide the complete file content, not just the changed portion (unless it's a very large file)

Provide clear, concise, and accurate responses. When showing code, use proper syntax highlighting with file paths in code blocks."""
    
    if system_prompt:
        return system_prompt
    
    if append_system_prompt:
        base_prompt += "\n\n" + append_system_prompt
    
    return base_prompt


def build_messages(
    query: str = None,
    piped_input: str = None,
    current_dir: str = None,
    add_dirs: List[str] = None,
    system_prompt: str = None,
    append_system_prompt: str = None
) -> List[Dict[str, str]]:
    """Build messages with context"""
    messages = []
    
    # System message
    sys_msg = build_system_prompt(add_dirs, system_prompt, append_system_prompt)
    messages.append({"role": "system", "content": sys_msg})
    
    # Add current directory context (automatic)
    if current_dir:
        dir_context = load_directory_context(current_dir)
        if dir_context:
            messages.append({
                "role": "user",
                "content": f"Here is the current directory context:\n\n{dir_context}"
            })
    
    # Add additional directories
    if add_dirs:
        for add_dir in add_dirs:
            dir_context = load_directory_context(add_dir)
            if dir_context:
                messages.append({
                    "role": "user",
                    "content": f"Here is additional directory context from {add_dir}:\n\n{dir_context}"
                })
    
    # Add piped input if any
    if piped_input:
        messages.append({
            "role": "user",
            "content": f"Here is piped input:\n\n```\n{piped_input}\n```"
        })
    
    # Add user query with automatic tool execution
    if query:
        # Check for tool calls (both explicit and implicit)
        tools = parse_tool_calls(query, current_dir)
        tool_results = []
        
        # Read files automatically
        if 'files' in tools:
            for file_path in tools['files']:
                file_content = load_file_context(file_path)
                if file_content:
                    tool_results.append(f"File Content ({file_path}):\n{file_content}\n\n")
        
        # Web search
        if 'web_search' in tools:
            console.print(f"[dim]🔍 Searching web...[/dim]")
            search_result = web_search(tools['web_search'])
            tool_results.append(f"Web Search Result:\n{search_result}\n")
        
        # HTTP requests
        if 'curl' in tools:
            console.print(f"[dim]🌐 Making HTTP request...[/dim]")
            curl_result = curl_request(tools['curl'])
            tool_results.append(f"Curl Request Result:\n{curl_result}\n")
        
        # Bash execution
        if 'bash' in tools:
            console.print(f"[dim]⚙️  Executing command...[/dim]")
            stdout, stderr, code = execute_bash(tools['bash'], cwd=current_dir)
            tool_results.append(f"Bash Command Result:\nCommand: {tools['bash']}\nReturn Code: {code}\nStdout:\n{stdout}\nStderr:\n{stderr}\n")
        
        if tool_results:
            query = f"{query}\n\n[Tool Execution Results]\n{''.join(tool_results)}"
        
        messages.append({"role": "user", "content": query})
    
    return messages


def _handle_file_edit(edit_info: Dict, current_dir: str, console: Console):
    """Handle file editing from detected edit requests"""
    code_blocks = edit_info.get('code_blocks', [])
    file_path = edit_info.get('file_path')
    
    if not code_blocks:
        return
    
    # Find code block with file path or use first one
    target_block = None
    for block in code_blocks:
        if block.get('file_path'):
            target_block = block
            file_path = block['file_path']
            break
    
    if not target_block and code_blocks:
        target_block = code_blocks[0]
    
    if not target_block:
        return
    
    # Resolve file path - try multiple strategies
    resolved_file_path = None
    
    if file_path:
        resolved_file_path = file_path
    elif target_block.get('file_path'):
        resolved_file_path = target_block['file_path']
    
    # Resolve relative paths
    if resolved_file_path:
        if not Path(resolved_file_path).is_absolute():
            # Try relative to current directory
            test_path = Path(current_dir) / resolved_file_path
            if test_path.exists():
                resolved_file_path = str(test_path.resolve())
            else:
                resolved_file_path = str(test_path.resolve())
        else:
            resolved_file_path = str(Path(resolved_file_path).resolve())
        file_path = resolved_file_path
    else:
        # No file path found, skip
        return
    
    # Ask for confirmation
    console.print(f"\n[cyan]📝 Detected file edit request for: {file_path}[/cyan]")
    if Confirm.ask("Apply changes to file?", default=True):
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            progress.add_task(f"[cyan]Applying changes to {Path(file_path).name}...", total=None)
            success, message = apply_code_changes(file_path, target_block['code'])
            if success:
                console.print(f"[green]{message}[/green]")
            else:
                console.print(f"[red]{message}[/red]")


def interactive_mode(
    client: DeepSeekClient,
    session_id: str,
    session_manager: SessionManager,
    current_dir: str,
    add_dirs: List[str] = None,
    system_prompt: str = None,
    append_system_prompt: str = None,
    initial_query: str = None
):
    """Interactive REPL mode - Everything happens here in chat"""
    # Start with directory context loaded
    messages = build_messages(
        query=None,  # Don't add query yet, just context
        current_dir=current_dir,
        add_dirs=add_dirs,
        system_prompt=system_prompt,
        append_system_prompt=append_system_prompt
    )
    
    # Show welcome with context info
    console.print(Panel(
        "[bold cyan]Deep Code - Interactive Chat Mode[/bold cyan]\n\n"
        f"[dim]Current directory: {current_dir}[/dim]\n"
        + (f"[dim]Additional directories: {', '.join(add_dirs)}[/dim]\n" if add_dirs else "") +
        "[dim]Type 'exit' or 'quit' to end, 'clear' to clear context, 'help' for commands[/dim]\n"
        "[yellow]💡 Tip: Press Ctrl+C during operations to interrupt and return to chat[/yellow]",
        title="Deep Code",
        border_style="cyan"
    ))
    console.print()
    
    # Handle initial query if provided
    if initial_query:
        console.print(f"[bold blue]You:[/bold blue] {initial_query}\n")
        
        # Auto-execute tools if needed
        tools = parse_tool_calls(initial_query, current_dir)
        tool_results = []
        
        if 'files' in tools:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("[cyan]Reading files...", total=None)
                for file_path in tools['files']:
                    file_content = load_file_context(file_path)
                    if file_content:
                        tool_results.append(f"File Content ({file_path}):\n{file_content}\n\n")
        
        if 'web_search' in tools:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                progress.add_task("[cyan]🔍 Searching web...", total=None)
                search_result = web_search(tools['web_search'])
                tool_results.append(f"Web Search Result:\n{search_result}\n")
        
        if 'curl' in tools:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                progress.add_task("[cyan]🌐 Making HTTP request...", total=None)
                curl_result = curl_request(tools['curl'])
                tool_results.append(f"Curl Request Result:\n{curl_result}\n")
        
        if 'bash' in tools:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                progress.add_task(f"[cyan]⚙️  Executing: {tools['bash']}...", total=None)
                stdout, stderr, code = execute_bash(tools['bash'], cwd=current_dir)
                tool_results.append(f"Bash Command Result:\nCommand: {tools['bash']}\nReturn Code: {code}\nStdout:\n{stdout}\nStderr:\n{stderr}\n")
        
        if tool_results:
            initial_query = f"{initial_query}\n\n[Tool Execution Results]\n{''.join(tool_results)}"
        
        messages.append({"role": "user", "content": initial_query})
        console.print("[bold green]DeepSeek:[/bold green]\n")
        response = client.chat(messages, stream=True)
        assistant_response = stream_response(response, show_progress=True)
        messages.append({"role": "assistant", "content": assistant_response})
        
        # Check if this was a file edit request
        edit_info = detect_file_edit_request(initial_query, assistant_response)
        if edit_info and edit_info.get('code_blocks'):
            _handle_file_edit(edit_info, current_dir, console)
        
        session_manager.update_session(session_id, messages)
    
    # Main interactive loop
    while True:
        try:
            user_input = Prompt.ask("\n[bold blue]You[/bold blue]")
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                console.print("[yellow]Goodbye![/yellow]")
                break
            
            if user_input.lower() == 'clear':
                # Keep system message and directory context
                messages = messages[:1] if messages else []
                # Reload directory context
                if current_dir:
                    dir_context = load_directory_context(current_dir)
                    if dir_context:
                        messages.append({
                            "role": "user",
                            "content": f"Here is the current directory context:\n\n{dir_context}"
                        })
                console.print("[green]Context cleared (directory context reloaded)[/green]")
                continue
            
            if user_input.lower() in ['help', '?']:
                console.print(Panel("""
[bold]Available Commands:[/bold]
  • Just ask questions naturally - I'll automatically use tools when needed
  • @web <query> - Explicitly search the web
  • @curl <url> - Make HTTP request
  • @bash <command> - Execute bash command
  • clear - Clear conversation context
  • exit/quit - Exit chat

[bold]File Editing:[/bold]
  • "Edit file.py to add X" - I'll modify the file automatically
  • "Update app.js with new function" - I'll update the file
  • "Fix the bug in utils.py" - I'll fix and save the file

[bold]Examples:[/bold]
  • "What does this project do?" - I'll analyze the directory
  • "Read app.py" - I'll read the file
  • "Run git status" - I'll execute the command
  • "Search for Python async best practices" - I'll search the web
  • "Add error handling to main.py" - I'll edit and save the file

[yellow]💡 Interrupt: Press Ctrl+C during any operation to stop and return to chat[/yellow]
                """, title="Help", border_style="blue"))
                continue
            
            if not user_input.strip():
                continue
            
            # Auto-detect and execute tools
            tools = parse_tool_calls(user_input, current_dir)
            tool_results = []
            
            # Read files automatically
            if 'files' in tools:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                    transient=True
                ) as progress:
                    task = progress.add_task("[cyan]📄 Reading files...", total=None)
                    for file_path in tools['files']:
                        file_content = load_file_context(file_path)
                        if file_content:
                            tool_results.append(f"File Content ({file_path}):\n{file_content}\n\n")
            
            # Web search
            if 'web_search' in tools:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                    transient=True
                ) as progress:
                    progress.add_task("[cyan]🔍 Searching web...", total=None)
                    search_result = web_search(tools['web_search'])
                    tool_results.append(f"Web Search Result:\n{search_result}\n")
            
            # HTTP requests
            if 'curl' in tools:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                    transient=True
                ) as progress:
                    progress.add_task("[cyan]🌐 Making HTTP request...", total=None)
                    curl_result = curl_request(tools['curl'])
                    tool_results.append(f"Curl Request Result:\n{curl_result}\n")
            
            # Bash execution
            if 'bash' in tools:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                    transient=True
                ) as progress:
                    progress.add_task(f"[cyan]⚙️  Executing: {tools['bash']}...", total=None)
                    stdout, stderr, code = execute_bash(tools['bash'], cwd=current_dir)
                    tool_results.append(f"Bash Command Result:\nCommand: {tools['bash']}\nReturn Code: {code}\nStdout:\n{stdout}\nStderr:\n{stderr}\n")
            
            if tool_results:
                user_input = f"{user_input}\n\n[Tool Execution Results]\n{''.join(tool_results)}"
            
            messages.append({"role": "user", "content": user_input})
            
            console.print("[bold green]DeepSeek:[/bold green]\n")
            interrupt_flag.clear()  # Reset interrupt flag
            try:
                response = client.chat(messages, stream=True)
                assistant_response = stream_response(response, show_progress=True)
                
                # Check if this was a file edit request
                edit_info = detect_file_edit_request(user_input, assistant_response)
                if edit_info and edit_info.get('code_blocks'):
                    _handle_file_edit(edit_info, current_dir, console)
                
                messages.append({"role": "assistant", "content": assistant_response})
                session_manager.update_session(session_id, messages)
            except KeyboardInterrupt:
                interrupt_flag.set()
                console.print("\n[yellow]⚠️  Operation interrupted. Returning to chat...[/yellow]")
                continue
            
        except KeyboardInterrupt:
            if interrupt_flag.is_set():
                # Operation was interrupted, continue chat
                continue
            console.print("\n[yellow]Interrupted. Goodbye![/yellow]")
            break
        except EOFError:
            console.print("\n[yellow]Goodbye![/yellow]")
            break


def print_mode(
    client: DeepSeekClient,
    query: str,
    piped_input: str = None,
    current_dir: str = None,
    add_dirs: List[str] = None,
    system_prompt: str = None,
    append_system_prompt: str = None,
    output_format: str = "text"
):
    """Print mode (non-interactive)"""
    messages = build_messages(
        query=query,
        piped_input=piped_input,
        current_dir=current_dir,
        add_dirs=add_dirs,
        system_prompt=system_prompt,
        append_system_prompt=append_system_prompt
    )
    
    response = client.chat(messages, stream=(output_format == "text"))
    
    if output_format == "json":
        result = {
            "response": stream_response(response) if hasattr(response, '__iter__') else response.choices[0].message.content
        }
        print(json.dumps(result, indent=2))
    else:
        stream_response(response)


def main():
    parser = argparse.ArgumentParser(
        description="Deep Code - CLI tool powered by DeepSeek API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  deepcode                    # Start interactive REPL
  deepcode "explain this project"  # Start REPL with initial prompt
  deepcode -p "query"         # Query via SDK, then exit
  cat file.txt | deepcode -p "explain"  # Process piped content
  deepcode -c                 # Continue most recent conversation
  deepcode -c -p "query"      # Continue via SDK
  deepcode -r "session-id" "query"  # Resume session by ID
        """
    )
    
    # Main arguments
    parser.add_argument('query', nargs='?', help='Query string (optional for interactive mode)')
    
    # Mode flags
    parser.add_argument('-p', '--print', action='store_true', 
                       help='Print response without interactive mode')
    parser.add_argument('-c', '--continue', dest='continue_session', action='store_true',
                       help='Load the most recent conversation in the current directory')
    parser.add_argument('-r', '--resume', dest='resume_session', metavar='SESSION_ID',
                       help='Resume a specific session by ID')
    
    # Configuration flags
    parser.add_argument('--add-dir', action='append', dest='add_dirs',
                       help='Add additional working directories (repeatable)')
    parser.add_argument('--model', help='Set the model for the current session')
    parser.add_argument('--system-prompt', help='Replace the entire system prompt')
    parser.add_argument('--append-system-prompt', help='Append custom text to the end of the default system prompt')
    parser.add_argument('--output-format', choices=['text', 'json'], default='text',
                       help='Specify output format for print mode')
    
    args = parser.parse_args()
    
    # Get current directory
    current_dir = os.getcwd()
    
    # Initialize client
    client = DeepSeekClient(model=args.model)
    
    # Initialize session manager
    session_manager = SessionManager()
    
    # Handle session management
    session_id = str(uuid.uuid4())
    if args.continue_session:
        existing_id = session_manager.get_recent_session(current_dir)
        if existing_id:
            session_id = existing_id
            messages = session_manager.load_session(session_id)
            if messages and args.query:
                # Continue with new query
                if args.print:
                    messages.append({"role": "user", "content": args.query})
                    response = client.chat(messages, stream=(args.output_format == "text"))
                    if args.output_format == "json":
                        result = {"response": stream_response(response) if hasattr(response, '__iter__') else response.choices[0].message.content}
                        print(json.dumps(result, indent=2))
                    else:
                        assistant_response = stream_response(response)
                        messages.append({"role": "assistant", "content": assistant_response})
                        session_manager.update_session(session_id, messages)
                else:
                    interactive_mode(client, session_id, session_manager, current_dir,
                                   args.add_dirs, args.system_prompt, args.append_system_prompt, args.query)
                return
    elif args.resume_session:
        session_id = args.resume_session
        messages = session_manager.load_session(session_id)
        if not messages:
            console.print(f"[red]Session {session_id} not found[/red]")
            sys.exit(1)
        if args.query:
            messages.append({"role": "user", "content": args.query})
            if args.print:
                response = client.chat(messages, stream=(args.output_format == "text"))
                if args.output_format == "json":
                    result = {"response": stream_response(response) if hasattr(response, '__iter__') else response.choices[0].message.content}
                    print(json.dumps(result, indent=2))
                else:
                    assistant_response = stream_response(response)
                    messages.append({"role": "assistant", "content": assistant_response})
                    session_manager.update_session(session_id, messages)
            else:
                interactive_mode(client, session_id, session_manager, current_dir,
                               args.add_dirs, args.system_prompt, args.append_system_prompt, args.query)
            return
    
    # Check for piped input
    piped_input = None
    if not sys.stdin.isatty():
        piped_input = sys.stdin.read()
    
    # Initialize new session
    session_manager.save_session(session_id, current_dir, [])
    
    # Handle print mode (non-interactive)
    if args.print:
        if not args.query and not piped_input:
            console.print("[red]Error: Query required in print mode (or provide piped input)[/red]")
            sys.exit(1)
        print_mode(client, args.query or "", piped_input, current_dir, args.add_dirs,
                  args.system_prompt, args.append_system_prompt, args.output_format)
    else:
        # DEFAULT: Interactive mode - everything happens in chat
        interactive_mode(client, session_id, session_manager, current_dir,
                        args.add_dirs, args.system_prompt, args.append_system_prompt, args.query)


if __name__ == '__main__':
    main()
