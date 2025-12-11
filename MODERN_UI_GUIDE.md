# Deep Code Modern - UI/UX Guide

## Overview

Deep Code Modern (`deepcode-modern` or `dcm`) is the enhanced version with Claude Code-like workflow and modern terminal UI. It provides a cleaner, more structured interface with better visual hierarchy and workflow control.

## Key Differences from Original

| Feature | Original (`deepcode`) | Modern (`deepcode-modern`) |
|---------|---------------------|---------------------------|
| **UI Style** | Basic output | Structured panels & boxes |
| **Tool Display** | Inline text | Dedicated tool blocks |
| **Execution** | Auto-execute | Ask before executing (configurable) |
| **Visual Design** | Simple | Modern with color coding |
| **Workflow** | Continuous loop | Structured turn-based |
| **Feedback** | Basic text | Rich formatted output |

## Installation

```bash
# Install/update Deep Code
pip install -e .

# Now you have both commands:
# - deepcode (original)
# - deepcode-modern (new UI)
```

## Usage

### Basic Usage

```bash
# Start modern interface
deepcode-modern

# Or use the short alias
dcm

# Start with a query
deepcode-modern "Analyze this project"

# Continue last session
deepcode-modern -c
```

### Execution Modes

Deep Code Modern offers 4 execution modes:

#### 1. Ask Once (Default) - Recommended
```bash
deepcode-modern --mode once
```
- Asks for permission once per turn
- Allows reviewing all tools before execution
- **Best for most users**

#### 2. Ask Always
```bash
deepcode-modern --mode ask
```
- Asks before every tool execution
- Maximum control
- Good for sensitive operations

#### 3. Auto
```bash
deepcode-modern --mode auto
```
- Auto-executes safe tools
- Asks only for dangerous operations
- Like the original deepcode

#### 4. Manual
```bash
deepcode-modern --mode manual
```
- Never auto-executes
- Only explicit user commands run
- Maximum safety

## Visual Interface

### Welcome Screen

```
╭─────────────────────────────────────────────────────────╮
│                                                         │
│  Deep Code - AI Coding Assistant                       │
│  Powered by DeepSeek                                   │
│                                                         │
╰─────────────────────────────────────────────────────────╯

📁 Working Directory: /Users/you/project
   + Additional: /Users/you/shared

Tool Permissions
Allow automatic execution of:
? Shell commands (bash)? (Y/n)
? Web searches? (Y/n)
? HTTP requests (curl)? (Y/n)
```

### User Input

```
❯ You
  Check the git status and explain what files have changed
```

### Tool Display

When tools are detected, they're shown in structured blocks:

```
╭─────────────────────────────────────────────────────────╮
│ Tool: bash                                              │
│                                                         │
│   command: git status                                   │
╰─────────────────────────────────────────────────────────╯

? Execute these tools? (Y/n)
```

### Tool Results

```
╭─────────────────────────────────────────────────────────╮
│ ✓ bash                                                  │
│                                                         │
│ On branch main                                          │
│ Changes not staged for commit:                         │
│   modified:   README.md                                 │
│   modified:   src/app.py                                │
╰─────────────────────────────────────────────────────────╯
```

### Assistant Response

```
◆ Assistant

Based on the git status, you have two modified files:

1. README.md - Documentation changes
2. src/app.py - Application code changes

Neither file is staged for commit yet. You can:
- Use git diff to see specific changes
- Use git add to stage them
- Use git commit to save changes
```

## Color Scheme

The modern UI uses a professional color scheme:

- **User Input**: Bright Cyan (`❯`)
- **Assistant**: Bright Green (`◆`)
- **Tools**: Magenta
- **Success**: Green (`✓`)
- **Error**: Red (`✗`)
- **Warning**: Yellow (`⚠`)
- **Muted**: Gray (for less important info)

## Workflow Example

### Complete Interaction Flow

```bash
$ dcm "Review the authentication code"

╭─────────────────────────────────────────────────────────╮
│  Deep Code - AI Coding Assistant                       │
╰─────────────────────────────────────────────────────────╯

📁 Working Directory: /Users/you/project

Loading workspace context...
──────────────────────────────────────────────────────────

❯ You
  Review the authentication code

Tools Ready to Execute:
  1. glob(**/*auth*.py)
  2. read(src/auth.py)

? Execute these tools? (Y/n) y

╭─────────────────────────────────────────────────────────╮
│ Tool: glob                                              │
│   pattern: **/*auth*.py                                 │
╰─────────────────────────────────────────────────────────╯

╭─────────────────────────────────────────────────────────╮
│ ✓ glob                                                  │
│                                                         │
│ src/auth.py                                             │
│ tests/test_auth.py                                      │
╰─────────────────────────────────────────────────────────╯

╭─────────────────────────────────────────────────────────╮
│ Tool: read                                              │
│   file_path: src/auth.py                                │
╰─────────────────────────────────────────────────────────╯

╭─────────────────────────────────────────────────────────╮
│ ✓ read                                                  │
│                                                         │
│ [file contents shown with syntax highlighting]         │
╰─────────────────────────────────────────────────────────╯

◆ Assistant (thinking...)

◆ Assistant

I've reviewed your authentication code. Here are my findings:

## Security Issues Found

1. **Password Storage**: Passwords are hashed but using MD5
   - Recommendation: Switch to bcrypt or Argon2

2. **Session Management**: Sessions don't expire
   - Recommendation: Add timeout mechanism

## Positive Aspects

✓ Input validation on username
✓ SQL injection protection with parameterized queries
✓ HTTPS enforcement

Would you like me to suggest specific code improvements?

──────────────────────────────────────────────────────────

❯ _
```

## Advanced Features

### 1. Structured Tool Confirmation

Before executing tools, you see exactly what will run:

```
Tools Ready to Execute:
  1. bash(git log --oneline -10)
  2. bash(git diff HEAD~1)
  3. web_search(git best practices 2024)

? Execute these tools? (Y/n)
```

### 2. Clear Error Messages

Errors are shown in styled panels:

```
╭─────────────────────────────────────────────────────────╮
│ Error                                                   │
│                                                         │
│ File not found: /path/to/missing.py                    │
│                                                         │
│ Please check the file path and try again.              │
╰─────────────────────────────────────────────────────────╯
```

### 3. Help System

Type `help` for formatted commands:

```
╭─────────────────────────────────────────────────────────╮
│ Available Commands                                      │
│                                                         │
│  @read <file>      Read file contents                  │
│  @write <file>     Write to file                       │
│  @edit <file>      Edit file (exact string match)      │
│  @glob <pattern>   Find files matching pattern         │
│  @grep <pattern>   Search code with regex              │
│  @bash <cmd>       Execute shell command               │
│  @web <query>      Search the web                      │
│  @curl <url>       Make HTTP request                   │
│                                                         │
│  exit, quit, q     Exit Deep Code                      │
│  clear             Clear conversation                   │
│  help, ?           Show this help                      │
╰─────────────────────────────────────────────────────────╯
```

### 4. Session Information

```
Session: a7f3e2b1... | Messages: 12
```

### 5. Token Usage (Coming Soon)

```
Tokens: ███████████░░░░░░░ 15,234/64,000 (23.8%)
```

## Command Reference

### Available Commands

| Command | Action |
|---------|--------|
| `help` or `?` | Show help |
| `clear` | Clear conversation history |
| `exit`, `quit`, `q` | Exit Deep Code |
| `Ctrl+C` | Interrupt operation |

### Tool Syntax

Same as original Deep Code:
- `@read path/to/file`
- `@write path/to/file`
- `@edit path/to/file`
- `@glob **/*.py`
- `@grep "pattern"`
- `@bash command`
- `@web search query`
- `@curl https://api.example.com`

## Configuration

### Environment Variables

```bash
# API Configuration
export DEEPSEEK_API_KEY=your_key
export DEEPSEEK_API_BASE=https://api.deepseek.com
export DEEPSEEK_MODEL=deepseek-chat

# UI Configuration (Coming Soon)
export DEEPCODE_THEME=dark  # or light
export DEEPCODE_COLOR_SCHEME=claude  # or custom
```

### Command Line Options

```bash
deepcode-modern [options] [query]

Options:
  --mode {ask,once,auto,manual}
                        Tool execution mode (default: once)
  --add-dir DIR         Add additional directory
  --model MODEL         Specify model
  -c, --continue        Continue last session
  -h, --help           Show help
```

## Best Practices

### 1. Use "Ask Once" Mode for Interactive Work
```bash
dcm --mode once
```
- Review tools before execution
- Maintain control
- Avoid surprises

### 2. Use "Auto" Mode for Trusted Workflows
```bash
dcm --mode auto "Run tests and fix any issues"
```
- Faster iteration
- Good for routine tasks
- Still asks for dangerous operations

### 3. Use "Ask Always" for Learning
```bash
dcm --mode ask
```
- See every tool call
- Understand AI's reasoning
- Educational

### 4. Use "Manual" for Maximum Safety
```bash
dcm --mode manual
```
- Production environments
- Sensitive operations
- Complete control

## Comparison with Other AI CLIs

### vs Claude Code
- ✅ Similar workflow (show tools before execution)
- ✅ Structured tool display
- ✅ Clean visual design
- ✅ Turn-based interaction
- ➕ Multiple execution modes
- ➕ Customizable permissions

### vs Original Deep Code
- ✅ Better visual hierarchy
- ✅ Clearer tool execution
- ✅ More control over automation
- ✅ Professional appearance
- ➕ Structured panels
- ➕ Error handling

### vs GitHub Copilot CLI
- ✅ Full conversation context
- ✅ Multi-tool execution
- ✅ Code analysis
- ➕ More flexible
- ➕ Session management

## Troubleshooting

### "deepcode-modern: command not found"

```bash
# Reinstall
pip install -e .

# Or run directly
python deepcode_modern.py
```

### Tools Not Executing

1. Check permissions were granted during setup
2. Verify execution mode: `--mode once` (default)
3. Confirm tools when prompted

### Display Issues

1. Check terminal supports colors
2. Update Rich: `pip install --upgrade rich`
3. Try different terminal (iTerm2, Windows Terminal)

## Migration from Original

### Quick Start

Just use `deepcode-modern` instead of `deepcode`:

```bash
# Before
deepcode "analyze project"

# After
deepcode-modern "analyze project"
```

### Both Versions Available

You can use both:
- `deepcode` - Original (faster, auto-exec)
- `deepcode-modern` - New UI (cleaner, more control)

Choose based on your needs:
- Quick tasks? → `deepcode`
- Interactive work? → `deepcode-modern`

## Future Enhancements

Planned features:
- [ ] Customizable color themes
- [ ] Token usage display
- [ ] Execution history view
- [ ] Tool execution replay
- [ ] Custom tool definitions
- [ ] Multi-pane layout option
- [ ] Syntax highlighting themes
- [ ] Export conversations
- [ ] Screenshot/share feature

## Feedback

The modern UI is under active development. Feedback welcome!

---

**Version**: 2.0.0
**Status**: Beta
**Recommended For**: Interactive development, code review, exploratory analysis
**Try It**: `deepcode-modern` or `dcm`
