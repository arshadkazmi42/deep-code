#!/usr/bin/env python3
"""
Deep Code Modern - Enhanced CLI with Claude Code-like workflow and modern UI
This is the improved version with better UX and workflow
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import modules
from rich.console import Console
from ui import ModernUI, get_ui
from workflow import WorkflowManager, ExecutionMode, ConversationFlow
from deepcode import (
    DeepSeekClient,
    SessionManager,
    load_directory_context,
    execute_bash,
    web_search,
    curl_request,
    load_file_context,
)

# Load environment
load_dotenv()


def setup_workflow(execution_mode: ExecutionMode) -> WorkflowManager:
    """Setup workflow with tool executors"""
    workflow = WorkflowManager(execution_mode)

    # Register tool executors
    workflow.register_tool_executor('bash', lambda command, cwd=None: execute_bash(command, cwd or os.getcwd()))
    workflow.register_tool_executor('web_search', web_search)
    workflow.register_tool_executor('curl', curl_request)
    workflow.register_tool_executor('read', load_file_context)

    return workflow


def interactive_mode_modern(
    client: DeepSeekClient,
    session_id: str,
    session_manager: SessionManager,
    current_dir: str,
    add_dirs: Optional[List[str]] = None,
    execution_mode: ExecutionMode = ExecutionMode.ASK_ONCE,
    initial_query: Optional[str] = None
):
    """Modern interactive mode with Claude Code-like interface"""

    # Initialize UI and workflow
    console = Console()
    ui = ModernUI(console)
    workflow = setup_workflow(execution_mode)
    flow = ConversationFlow(workflow, ui)

    # Show welcome
    ui.show_welcome(current_dir, add_dirs)

    # Request permissions
    console.print(f"[{ui.colors['primary']}]Tool Permissions[/{ui.colors['primary']}]")
    console.print(f"[{ui.colors['muted']}]Allow automatic execution of:[/{ui.colors['muted']}]")
    console.print()

    permissions = {
        'bash': ui.confirm("  Shell commands (bash)?", default=True),
        'web_search': ui.confirm("  Web searches?", default=True),
        'curl': ui.confirm("  HTTP requests (curl)?", default=True),
        'read': True,  # Always allow reading
    }

    console.print()
    console.print(f"[{ui.colors['muted']}]Type 'help' for commands, 'exit' to quit, Ctrl+C to interrupt[/{ui.colors['muted']}]")

    # Build initial messages
    messages = []

    # System message
    from deepcode import build_system_prompt
    system_prompt = build_system_prompt()
    messages.append({"role": "system", "content": system_prompt})

    # Load directory context
    ui.console.print()
    ui.console.print(f"[{ui.colors['muted']}]Loading workspace context...[/{ui.colors['muted']}]")

    dir_context = load_directory_context(current_dir)
    if dir_context:
        messages.append({
            "role": "user",
            "content": f"Here is the current directory context:\n\n{dir_context}"
        })

    if add_dirs:
        for add_dir in add_dirs:
            dir_context = load_directory_context(add_dir)
            if dir_context:
                messages.append({
                    "role": "user",
                    "content": f"Additional directory context from {add_dir}:\n\n{dir_context}"
                })

    ui.show_divider()

    # Handle initial query
    if initial_query:
        ui.show_user_input(initial_query)

        # Handle user turn
        messages = flow.handle_user_turn(initial_query, messages)

        # Handle assistant turn
        messages, response = flow.handle_assistant_turn(messages, client, permissions)
        ui.show_assistant_response(response)

        ui.show_divider()

        # Save session
        session_manager.update_session(session_id, messages)

    # Main interactive loop
    while True:
        try:
            # Get user input
            user_input = ui.prompt_input()

            # Handle commands
            if user_input.lower() in ['exit', 'quit', 'q']:
                ui.show_goodbye()
                break

            if user_input.lower() == 'clear':
                # Keep system message and directory context
                system_msg = messages[0] if messages and messages[0]['role'] == 'system' else None
                messages = [system_msg] if system_msg else []

                # Reload directory context
                dir_context = load_directory_context(current_dir)
                if dir_context:
                    messages.append({
                        "role": "user",
                        "content": f"Here is the current directory context:\n\n{dir_context}"
                    })

                ui.show_success("Conversation cleared")
                continue

            if user_input.lower() in ['help', '?']:
                ui.show_help()
                continue

            if not user_input.strip():
                continue

            # Show user input
            ui.show_user_input(user_input)

            # Handle user turn (parse and execute user's explicit tool calls)
            messages = flow.handle_user_turn(user_input, messages)

            # Handle assistant turn (get AI response and execute AI's tool calls)
            messages, response = flow.handle_assistant_turn(messages, client, permissions)

            # Show assistant response
            ui.show_assistant_response(response)

            # Show divider
            ui.show_divider()

            # Save session
            session_manager.update_session(session_id, messages)

        except KeyboardInterrupt:
            console.print()
            console.print(f"[{ui.colors['warning']}]⚠️ Interrupted. Press Ctrl+C again to exit or continue chatting.[/{ui.colors['warning']}]")
            continue
        except EOFError:
            ui.show_goodbye()
            break
        except Exception as e:
            ui.show_error(f"Unexpected error: {str(e)}", "Error")
            continue


def main():
    """Main entry point for modern Deep Code"""
    parser = argparse.ArgumentParser(
        description="Deep Code Modern - Enhanced AI coding assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('query', nargs='?', help='Initial query')
    parser.add_argument('--add-dir', action='append', dest='add_dirs',
                       help='Add additional directories')
    parser.add_argument('--model', help='Model to use')
    parser.add_argument('--mode', choices=['ask', 'once', 'auto', 'manual'],
                       default='once', help='Tool execution mode')
    parser.add_argument('-c', '--continue', dest='continue_session',
                       action='store_true', help='Continue last session')

    args = parser.parse_args()

    # Map mode to ExecutionMode
    mode_map = {
        'ask': ExecutionMode.ASK_ALWAYS,
        'once': ExecutionMode.ASK_ONCE,
        'auto': ExecutionMode.AUTO,
        'manual': ExecutionMode.MANUAL
    }
    execution_mode = mode_map[args.mode]

    # Initialize
    current_dir = os.getcwd()
    client = DeepSeekClient(model=args.model)
    session_manager = SessionManager()

    # Session handling
    import uuid
    session_id = str(uuid.uuid4())

    if args.continue_session:
        existing_id = session_manager.get_recent_session(current_dir)
        if existing_id:
            session_id = existing_id
            # Load messages (handled in interactive mode)

    # Save session
    session_manager.save_session(session_id, current_dir, [])

    # Run interactive mode
    interactive_mode_modern(
        client=client,
        session_id=session_id,
        session_manager=session_manager,
        current_dir=current_dir,
        add_dirs=args.add_dirs,
        execution_mode=execution_mode,
        initial_query=args.query
    )


if __name__ == '__main__':
    main()
