#!/usr/bin/env python3
"""
Modern UI/UX module for Deep Code - Claude Code-like interface
Provides structured, clean, and professional display for CLI interactions
"""

from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.box import ROUNDED, MINIMAL, SIMPLE
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
import re


class ModernUI:
    """Modern UI manager for Deep Code"""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

        # Color scheme matching Claude Code
        self.colors = {
            'primary': 'bright_cyan',
            'secondary': 'cyan',
            'success': 'green',
            'warning': 'yellow',
            'error': 'red',
            'muted': 'bright_black',
            'text': 'white',
            'highlight': 'bright_white',
            'tool': 'magenta',
            'user': 'bright_cyan',
            'assistant': 'bright_green',
        }

    def show_welcome(self, directory: str, additional_dirs: Optional[List[str]] = None):
        """Show welcome screen"""
        self.console.print()
        self.console.print("╭─────────────────────────────────────────────────────────╮", style=self.colors['muted'])
        self.console.print("│                                                         │", style=self.colors['muted'])
        self.console.print("│  [bold bright_cyan]Deep Code[/bold bright_cyan] - AI Coding Assistant                    │")
        self.console.print("│  [dim]Powered by DeepSeek[/dim]                                  │")
        self.console.print("│                                                         │", style=self.colors['muted'])
        self.console.print("╰─────────────────────────────────────────────────────────╯", style=self.colors['muted'])
        self.console.print()

        self.console.print(f"[{self.colors['muted']}]📁 Working Directory:[/{self.colors['muted']}] {directory}")
        if additional_dirs:
            for dir in additional_dirs:
                self.console.print(f"[{self.colors['muted']}]   + Additional:[/{self.colors['muted']}] {dir}")
        self.console.print()

    def show_help(self):
        """Show help panel"""
        help_table = Table(show_header=False, box=SIMPLE, padding=(0, 2))
        help_table.add_column("Command", style=self.colors['primary'])
        help_table.add_column("Description", style=self.colors['muted'])

        help_table.add_row("@read <file>", "Read file contents")
        help_table.add_row("@write <file>", "Write to file")
        help_table.add_row("@edit <file>", "Edit file (exact string match)")
        help_table.add_row("@glob <pattern>", "Find files matching pattern")
        help_table.add_row("@grep <pattern>", "Search code with regex")
        help_table.add_row("@bash <cmd>", "Execute shell command")
        help_table.add_row("@web <query>", "Search the web")
        help_table.add_row("@curl <url>", "Make HTTP request")
        help_table.add_row("", "")
        help_table.add_row("exit, quit, q", "Exit Deep Code")
        help_table.add_row("clear", "Clear conversation")
        help_table.add_row("help, ?", "Show this help")

        panel = Panel(
            help_table,
            title="[bold]Available Commands[/bold]",
            border_style=self.colors['primary'],
            box=ROUNDED
        )
        self.console.print(panel)
        self.console.print()

    def show_user_input(self, text: str):
        """Display user input"""
        self.console.print()
        self.console.print(f"[{self.colors['user']}]❯ You[/{self.colors['user']}]")
        self.console.print(f"  {text}")
        self.console.print()

    def show_assistant_thinking(self):
        """Show thinking indicator"""
        self.console.print(f"[{self.colors['assistant']}]◆ Assistant[/{self.colors['assistant']}]", end="")
        self.console.print(f" [{self.colors['muted']}](thinking...)[/{self.colors['muted']}]")

    def show_tool_call(self, tool_name: str, params: Dict[str, Any], index: int = 0):
        """Display a tool call in structured format"""
        # Create parameter display
        param_lines = []
        for key, value in params.items():
            if isinstance(value, str) and len(value) > 60:
                value_display = value[:57] + "..."
            else:
                value_display = str(value)
            param_lines.append(f"  [dim]{key}:[/dim] {value_display}")

        param_text = "\n".join(param_lines) if param_lines else "  [dim]no parameters[/dim]"

        # Create panel
        content = f"[{self.colors['tool']}]Tool:[/{self.colors['tool']}] [bold]{tool_name}[/bold]\n\n{param_text}"

        panel = Panel(
            content,
            border_style=self.colors['tool'],
            box=MINIMAL,
            padding=(0, 1)
        )
        self.console.print(panel)

    def show_tool_result(self, tool_name: str, result: Any, success: bool = True):
        """Display tool execution result"""
        status = "✓" if success else "✗"
        status_color = self.colors['success'] if success else self.colors['error']

        # Format result
        if isinstance(result, str):
            if len(result) > 2000:
                result_display = result[:2000] + f"\n\n[dim]... (truncated, total {len(result)} chars)[/dim]"
            else:
                result_display = result
        else:
            result_display = str(result)

        content = f"[{status_color}]{status}[/{status_color}] [bold]{tool_name}[/bold]\n\n{result_display}"

        panel = Panel(
            content,
            border_style=status_color,
            box=MINIMAL,
            padding=(0, 1)
        )
        self.console.print(panel)

    def show_assistant_response(self, text: str):
        """Display assistant response with proper formatting"""
        self.console.print()
        self.console.print(f"[{self.colors['assistant']}]◆ Assistant[/{self.colors['assistant']}]")
        self.console.print()

        # Parse and format markdown properly
        self._format_markdown_response(text)
        self.console.print()

    def _format_markdown_response(self, text: str):
        """Format markdown response with syntax highlighting"""
        lines = text.split('\n')
        i = 0
        in_code_block = False
        code_lines = []
        code_language = ""

        while i < len(lines):
            line = lines[i]

            # Handle code blocks
            if line.strip().startswith('```'):
                if in_code_block:
                    # End code block
                    if code_lines:
                        code_content = '\n'.join(code_lines)
                        try:
                            syntax = Syntax(
                                code_content,
                                code_language or "text",
                                theme="monokai",
                                line_numbers=False,
                                word_wrap=True,
                                background_color="default"
                            )
                            self.console.print(syntax)
                        except:
                            self.console.print(code_content)
                        self.console.print()
                    in_code_block = False
                    code_lines = []
                    code_language = ""
                else:
                    # Start code block
                    in_code_block = True
                    code_language = line.strip()[3:].strip()
                i += 1
                continue

            if in_code_block:
                code_lines.append(line)
                i += 1
                continue

            # Handle headings
            if line.strip().startswith('#'):
                level = 0
                stripped = line.strip()
                while level < len(stripped) and stripped[level] == '#':
                    level += 1
                heading_text = stripped[level:].strip()
                if heading_text:
                    if level == 1:
                        self.console.print(f"\n[bold {self.colors['highlight']}]{heading_text}[/bold {self.colors['highlight']}]")
                    elif level == 2:
                        self.console.print(f"\n[bold {self.colors['primary']}]{heading_text}[/bold {self.colors['primary']}]")
                    else:
                        self.console.print(f"\n[bold]{heading_text}[/bold]")
                i += 1
                continue

            # Handle lists
            if re.match(r'^(\s*)[-*•]\s+', line):
                indent_match = re.match(r'^(\s*)[-*•]\s+(.+)', line)
                if indent_match:
                    indent, content = indent_match.groups()
                    self.console.print(f"{indent}• {content}")
                i += 1
                continue

            if re.match(r'^(\s*)\d+[\.)]\s+', line):
                num_match = re.match(r'^(\s*)(\d+)[\.)]\s+(.+)', line)
                if num_match:
                    indent, num, content = num_match.groups()
                    self.console.print(f"{indent}{num}. {content}")
                i += 1
                continue

            # Regular text
            if line.strip():
                self.console.print(line)
            else:
                self.console.print()

            i += 1

    def show_error(self, message: str, title: Optional[str] = None):
        """Display error message"""
        panel = Panel(
            f"[{self.colors['error']}]{message}[/{self.colors['error']}]",
            title=f"[bold {self.colors['error']}]{title or 'Error'}[/bold {self.colors['error']}]",
            border_style=self.colors['error'],
            box=ROUNDED
        )
        self.console.print(panel)

    def show_warning(self, message: str, title: Optional[str] = None):
        """Display warning message"""
        panel = Panel(
            f"[{self.colors['warning']}]{message}[/{self.colors['warning']}]",
            title=f"[bold {self.colors['warning']}]{title or 'Warning'}[/bold {self.colors['warning']}]",
            border_style=self.colors['warning'],
            box=ROUNDED
        )
        self.console.print(panel)

    def show_info(self, message: str, title: Optional[str] = None):
        """Display info message"""
        panel = Panel(
            f"[{self.colors['primary']}]{message}[/{self.colors['primary']}]",
            title=f"[bold {self.colors['primary']}]{title or 'Info'}[/bold {self.colors['primary']}]",
            border_style=self.colors['primary'],
            box=ROUNDED
        )
        self.console.print(panel)

    def show_success(self, message: str, title: Optional[str] = None):
        """Display success message"""
        self.console.print(f"[{self.colors['success']}]✓[/{self.colors['success']}] {message}")

    def show_divider(self, style: str = 'thin'):
        """Show a divider line"""
        if style == 'thick':
            self.console.print(f"[{self.colors['muted']}]{'━' * 70}[/{self.colors['muted']}]")
        else:
            self.console.print(f"[{self.colors['muted']}]{'─' * 70}[/{self.colors['muted']}]")

    def prompt_input(self, prompt: str = "❯") -> str:
        """Get user input with styled prompt"""
        self.console.print(f"[{self.colors['user']}]{prompt}[/{self.colors['user']}] ", end="")
        return input()

    def confirm(self, message: str, default: bool = True) -> bool:
        """Ask for user confirmation"""
        default_str = "Y/n" if default else "y/N"
        self.console.print(f"[{self.colors['warning']}]?[/{self.colors['warning']}] {message} [{default_str}] ", end="")
        response = input().strip().lower()

        if not response:
            return default
        return response in ['y', 'yes']

    def show_streaming_start(self):
        """Show streaming start indicator"""
        self.console.print()
        self.console.print(f"[{self.colors['assistant']}]◆ Assistant[/{self.colors['assistant']}]")
        self.console.print()

    def show_streaming_chunk(self, chunk: str):
        """Display a chunk during streaming"""
        self.console.print(chunk, end="")

    def show_streaming_end(self):
        """Show streaming end"""
        self.console.print()

    def show_session_info(self, session_id: str, message_count: int):
        """Display session information"""
        info_text = f"Session: {session_id[:8]}... | Messages: {message_count}"
        self.console.print(f"[{self.colors['muted']}]{info_text}[/{self.colors['muted']}]")

    def show_token_usage(self, used: int, total: int, percentage: float):
        """Display token usage"""
        bar_width = 30
        filled = int(bar_width * (percentage / 100))
        bar = "█" * filled + "░" * (bar_width - filled)

        color = self.colors['success'] if percentage < 70 else \
                self.colors['warning'] if percentage < 90 else \
                self.colors['error']

        self.console.print(
            f"[{self.colors['muted']}]Tokens:[/{self.colors['muted']}] "
            f"[{color}]{bar}[/{color}] "
            f"{used:,}/{total:,} ({percentage:.1f}%)"
        )

    def show_tool_execution_prompt(self, tools: List[Dict[str, Any]]) -> bool:
        """Show tools that will be executed and ask for confirmation"""
        self.console.print()
        self.console.print(f"[{self.colors['tool']}]Tools Ready to Execute:[/{self.colors['tool']}]")
        self.console.print()

        for i, tool in enumerate(tools, 1):
            tool_name = tool.get('name', 'Unknown')
            params = tool.get('params', {})

            # Create compact display
            param_str = ", ".join([f"{k}={v}" for k, v in params.items()])
            if len(param_str) > 60:
                param_str = param_str[:57] + "..."

            self.console.print(f"  {i}. [{self.colors['tool']}]{tool_name}[/{self.colors['tool']}]({param_str})")

        self.console.print()
        return self.confirm("Execute these tools?", default=True)

    def show_goodbye(self):
        """Show goodbye message"""
        self.console.print()
        self.console.print(f"[{self.colors['primary']}]👋 Goodbye![/{self.colors['primary']}]")
        self.console.print()


# Global UI instance
_ui_instance: Optional[ModernUI] = None


def get_ui(console: Optional[Console] = None) -> ModernUI:
    """Get or create global UI instance"""
    global _ui_instance
    if _ui_instance is None:
        _ui_instance = ModernUI(console)
    return _ui_instance
