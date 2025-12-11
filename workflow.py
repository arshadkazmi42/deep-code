#!/usr/bin/env python3
"""
Workflow manager for Deep Code - Claude Code-like execution flow
Handles tool detection, confirmation, and execution in a structured manner
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class ExecutionMode(Enum):
    """Execution modes"""
    ASK_ALWAYS = "ask_always"  # Ask before each tool execution
    ASK_ONCE = "ask_once"  # Ask once per turn
    AUTO = "auto"  # Auto-execute without asking (original behavior)
    MANUAL = "manual"  # Never auto-execute


@dataclass
class ToolCall:
    """Represents a tool call"""
    name: str
    params: Dict[str, Any]
    source: str  # 'user_input' or 'ai_response'


@dataclass
class ToolResult:
    """Tool execution result"""
    success: bool
    output: str
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class WorkflowManager:
    """Manages the execution workflow"""

    def __init__(self, execution_mode: ExecutionMode = ExecutionMode.ASK_ONCE):
        self.execution_mode = execution_mode
        self.tool_executors: Dict[str, Callable] = {}
        self.execution_history: List[Dict[str, Any]] = []

    def register_tool_executor(self, tool_name: str, executor: Callable):
        """Register a tool executor function"""
        self.tool_executors[tool_name] = executor

    def parse_tool_calls_from_input(self, user_input: str) -> List[ToolCall]:
        """Parse tool calls from user input"""
        tools = []

        # Import the parsing function
        try:
            from deepcode import parse_tool_calls
            parsed = parse_tool_calls(user_input)

            # Convert to ToolCall objects
            if 'bash' in parsed:
                tools.append(ToolCall('bash', {'command': parsed['bash']}, 'user_input'))
            if 'web_search' in parsed:
                tools.append(ToolCall('web_search', {'query': parsed['web_search']}, 'user_input'))
            if 'curl' in parsed:
                tools.append(ToolCall('curl', {'url': parsed['curl']}, 'user_input'))
            if 'files' in parsed:
                for file_path in parsed['files']:
                    tools.append(ToolCall('read', {'file_path': file_path}, 'user_input'))

        except ImportError:
            pass

        return tools

    def parse_tool_calls_from_response(self, ai_response: str) -> List[ToolCall]:
        """Parse tool calls from AI response"""
        tools = []

        # Import the parsing function
        try:
            from deepcode import parse_tool_calls_from_response
            parsed = parse_tool_calls_from_response(ai_response)

            # Convert to ToolCall objects
            if 'bash' in parsed:
                tools.append(ToolCall('bash', {'command': parsed['bash']}, 'ai_response'))
            if 'web_search' in parsed:
                tools.append(ToolCall('web_search', {'query': parsed['web_search']}, 'ai_response'))
            if 'curl' in parsed:
                tools.append(ToolCall('curl', {'url': parsed['curl']}, 'ai_response'))

        except ImportError:
            pass

        return tools

    def should_ask_permission(self, tools: List[ToolCall], iteration: int = 0) -> bool:
        """Determine if we should ask for permission to execute tools"""
        if not tools:
            return False

        if self.execution_mode == ExecutionMode.MANUAL:
            return False  # Never execute automatically

        if self.execution_mode == ExecutionMode.ASK_ALWAYS:
            return True  # Always ask

        if self.execution_mode == ExecutionMode.ASK_ONCE:
            return iteration == 0  # Ask only on first iteration

        if self.execution_mode == ExecutionMode.AUTO:
            # Check if tools are dangerous
            return any(self._is_dangerous_tool(tool) for tool in tools)

        return True

    def _is_dangerous_tool(self, tool: ToolCall) -> bool:
        """Check if a tool call is potentially dangerous"""
        if tool.name == 'bash':
            command = tool.params.get('command', '')
            dangerous_patterns = ['rm -rf', 'rm -r', 'format', 'mkfs', 'dd if=']
            return any(pattern in command.lower() for pattern in dangerous_patterns)
        return False

    def execute_tool(self, tool: ToolCall) -> ToolResult:
        """Execute a single tool"""
        if tool.name not in self.tool_executors:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool executor not found: {tool.name}"
            )

        try:
            executor = self.tool_executors[tool.name]
            result = executor(**tool.params)

            # Record execution
            self.execution_history.append({
                'tool': tool.name,
                'params': tool.params,
                'success': True,
                'result': result
            })

            # Handle different result types
            if isinstance(result, tuple):
                # Legacy format (stdout, stderr, code)
                stdout, stderr, code = result
                return ToolResult(
                    success=code == 0,
                    output=stdout or stderr,
                    metadata={'return_code': code}
                )
            elif isinstance(result, str):
                return ToolResult(success=True, output=result)
            elif hasattr(result, 'success'):
                # ToolResult from new tools module
                return ToolResult(
                    success=result.success,
                    output=result.output,
                    error=result.error,
                    metadata=result.metadata
                )
            else:
                return ToolResult(success=True, output=str(result))

        except Exception as e:
            self.execution_history.append({
                'tool': tool.name,
                'params': tool.params,
                'success': False,
                'error': str(e)
            })
            return ToolResult(
                success=False,
                output="",
                error=f"Error executing {tool.name}: {str(e)}"
            )

    def execute_tools(self, tools: List[ToolCall]) -> List[ToolResult]:
        """Execute multiple tools"""
        results = []
        for tool in tools:
            result = self.execute_tool(tool)
            results.append(result)
        return results

    def format_tool_results(self, tools: List[ToolCall], results: List[ToolResult]) -> str:
        """Format tool results for adding to conversation"""
        parts = ["[Tool Execution Results]"]

        for tool, result in zip(tools, results):
            status = "✓" if result.success else "✗"
            parts.append(f"\n{status} {tool.name}:")

            if result.success:
                parts.append(result.output)
            else:
                parts.append(f"Error: {result.error}")

            if result.metadata:
                parts.append(f"Metadata: {result.metadata}")

        return '\n'.join(parts)

    def should_continue_iteration(self, tools: List[ToolCall], iteration: int, max_iterations: int) -> bool:
        """Determine if we should continue iterating"""
        if iteration >= max_iterations:
            return False

        if not tools:
            return False

        return True


class ConversationFlow:
    """Manages conversation flow with proper tool handling"""

    def __init__(self, workflow: WorkflowManager, ui_manager):
        self.workflow = workflow
        self.ui = ui_manager
        self.max_iterations = 3

    def handle_user_turn(self, user_input: str, messages: List[Dict]) -> List[Dict]:
        """
        Handle a single user turn:
        1. Parse tool calls from input
        2. Execute tools if needed
        3. Add results to messages
        4. Return updated messages
        """
        # Parse tools from user input
        tools = self.workflow.parse_tool_calls_from_input(user_input)

        # Execute tools from user input (these are explicit, so execute them)
        tool_results_text = ""
        if tools:
            for tool in tools:
                self.ui.show_tool_call(tool.name, tool.params)

            results = self.workflow.execute_tools(tools)

            for tool, result in zip(tools, results):
                self.ui.show_tool_result(tool.name, result.output, result.success)

            tool_results_text = self.workflow.format_tool_results(tools, results)

        # Build message content
        if tool_results_text:
            content = f"{user_input}\n\n{tool_results_text}"
        else:
            content = user_input

        messages.append({"role": "user", "content": content})
        return messages

    def handle_assistant_turn(
        self,
        messages: List[Dict],
        client,
        permissions: Dict[str, bool]
    ) -> tuple[List[Dict], str]:
        """
        Handle assistant turn with tool execution loop:
        1. Get AI response
        2. Parse tool calls
        3. Ask for permission (if mode requires)
        4. Execute approved tools
        5. Continue if tools were executed
        6. Return final messages and last response
        """
        iteration = 0
        last_response = ""

        while iteration < self.max_iterations:
            iteration += 1

            # Get AI response
            self.ui.show_assistant_thinking()
            response = client.chat(messages, stream=True)
            assistant_response = self._stream_response(response)
            last_response = assistant_response

            messages.append({"role": "assistant", "content": assistant_response})

            # Parse tool calls from response
            tools = self.workflow.parse_tool_calls_from_response(assistant_response)

            # Filter by permissions
            tools = [t for t in tools if permissions.get(t.name, False)]

            if not tools:
                break  # No tools to execute

            # Ask for permission if needed
            if self.workflow.should_ask_permission(tools, iteration - 1):
                tool_dicts = [{'name': t.name, 'params': t.params} for t in tools]
                if not self.ui.show_tool_execution_prompt(tool_dicts):
                    break  # User declined

            # Execute tools
            self.ui.console.print()
            for tool in tools:
                self.ui.show_tool_call(tool.name, tool.params)

            results = self.workflow.execute_tools(tools)

            for tool, result in zip(tools, results):
                self.ui.show_tool_result(tool.name, result.output, result.success)

            # Add results to messages
            tool_results_text = self.workflow.format_tool_results(tools, results)
            messages.append({"role": "user", "content": tool_results_text})

            # Continue to next iteration
            continue

        return messages, last_response

    def _stream_response(self, response) -> str:
        """Stream response and collect content"""
        collected = []
        self.ui.show_streaming_start()

        try:
            for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        content = delta.content
                        self.ui.show_streaming_chunk(content)
                        collected.append(content)
        except KeyboardInterrupt:
            self.ui.console.print("\n[yellow]⚠️ Interrupted[/yellow]")

        self.ui.show_streaming_end()
        return ''.join(collected)
