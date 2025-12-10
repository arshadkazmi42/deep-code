# Deep Code - CLI Tool powered by DeepSeek API

A command-line tool **exactly like Claude Code**, powered by DeepSeek's API. **Everything happens in interactive chat mode** - analyze code, search web, run commands, read files - all in one conversational interface.

## Features

- 💬 **Interactive Chat Mode** - Everything happens here! (Default mode)
- 🤖 **Auto Tool Detection** - Automatically reads files, executes commands, searches web when you ask
- 🔍 **Automatic Directory Analysis** - Current directory context loaded automatically
- 📄 **Smart File Reading** - Just mention a file and it reads it
- 🌐 **Web Search Integration** - Search the web with `@web` or naturally in conversation
- 🌍 **HTTP Requests** - Make API calls with `@curl` or mention URLs
- 🖥️ **Bash Execution** - Run commands naturally: "run git status" or "@bash git status"
- 📚 **Session Management** - Conversations persist automatically
- 🔄 **Pipe Support** - `cat file | deepcode -p` for quick queries
- ⚡ **Streaming Responses** - Real-time AI responses
- 🎨 **Beautiful Terminal UI** - Rich formatting and syntax highlighting

## Installation

### Quick Install (Recommended)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install the package (installs 'deepcode' command globally)
pip install -e .

# 3. Set your API key
export DEEPSEEK_API_KEY=your_api_key_here
```

### Alternative: Direct Usage (No Installation)

```bash
# Just install dependencies
pip install -r requirements.txt

# Set API key
export DEEPSEEK_API_KEY=your_api_key_here

# Run directly
python3 deepcode.py
```

### Troubleshooting

**If you get "No module named 'setuptools'" error:**
```bash
pip install setuptools wheel
```

**If you get "deepcode: command not found":**
- Make sure you ran `pip install -e .`
- Or use `python3 deepcode.py` instead

**Configuration via .env file:**
Create a `.env` file in the project directory:
```
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

See [INSTALL.md](INSTALL.md) for detailed installation instructions.

## Usage

### Interactive Chat Mode (Default - Everything Happens Here!)

```bash
# Start interactive chat - automatically loads current directory context
deepcode

# Start chat with initial question
deepcode "explain this project"

# With additional directories
deepcode --add-dir ../app --add-dir ../lib

# Everything is accessible in chat:
# - "Read app.py" → Automatically reads the file
# - "What does this project do?" → Uses directory context
# - "Run git status" → Executes the command
# - "Search for Python async best practices" → Searches web
# - "@curl https://api.github.com/users/octocat" → Makes HTTP request
```

### Print Mode (Non-Interactive)

```bash
# Query via SDK, then exit
deepcode -p "explain this function"

# Process piped content
cat file.txt | deepcode -p "explain"
cat log.txt | deepcode -p "analyze errors"

# JSON output
deepcode -p "query" --output-format json
```

### Session Management

```bash
# Continue most recent conversation
deepcode -c

# Continue with new query (non-interactive)
deepcode -c -p "check for type errors"

# Resume specific session by ID
deepcode -r "session-id" "query"

# Resume in interactive mode
deepcode -r "session-id"
```

### Directory Analysis

```bash
# Automatically analyzes current directory
deepcode "what does this project do?"

# Add additional directories
deepcode --add-dir ../shared --add-dir ../utils "review codebase"

# Works in print mode too
deepcode -p --add-dir ../lib "analyze dependencies"
```

### Custom System Prompts

```bash
# Replace entire system prompt
deepcode --system-prompt "You are a Python expert" "review code"

# Append to default prompt
deepcode --append-system-prompt "Always use TypeScript" "generate component"
```

### Natural Language in Chat Mode

In interactive chat mode, you can ask naturally - tools are used automatically:

```bash
deepcode
> What does this project do?
> Read app.py
> Analyze the main function
> Run git status
> Search for latest Python async features
> Check https://api.github.com/repos/octocat/Hello-World
> Show me the README file
```

### Explicit Tool Commands (Optional)

You can also use explicit commands:

- `@web <query>` or `@search <query>` - Perform web search
- `@curl <url>` - Make HTTP request  
- `@bash <command>` or `@exec <command>` - Execute bash command

Examples in chat:
```bash
deepcode
> @web latest Python async features
> @bash git status
> @curl https://api.github.com/users/octocat
```

### Model Selection

```bash
# Use specific model (default is deepseek-chat)
deepcode --model deepseek-chat "query"

# Override to use chat model
deepcode --model deepseek-chat "query"
```

## Examples

```bash
# Interactive session
deepcode "explain this codebase"

# Quick query
deepcode -p "write a Python function to reverse a string"

# Analyze piped content
cat requirements.txt | deepcode -p "analyze dependencies"

# Continue previous conversation
deepcode -c

# Resume specific session
deepcode -r "abc123" "finish this PR"

# With custom prompt
deepcode --append-system-prompt "Use best practices" "review my code"
```

## Command Reference

| Command | Description |
|---------|-------------|
| `deepcode` | Start interactive REPL |
| `deepcode "query"` | Start REPL with initial prompt |
| `deepcode -p "query"` | Query via SDK, then exit |
| `cat file \| deepcode -p "query"` | Process piped content |
| `deepcode -c` | Continue most recent conversation |
| `deepcode -c -p "query"` | Continue via SDK |
| `deepcode -r "session-id" "query"` | Resume session by ID |

## Flags

| Flag | Description |
|------|-------------|
| `-p, --print` | Print response without interactive mode |
| `-c, --continue` | Load most recent conversation |
| `-r, --resume SESSION_ID` | Resume specific session |
| `--add-dir DIR` | Add additional working directory (repeatable) |
| `--model MODEL` | Set model for current session |
| `--system-prompt TEXT` | Replace entire system prompt |
| `--append-system-prompt TEXT` | Append to default system prompt |
| `--output-format FORMAT` | Output format: text or json |

## Session Storage

Sessions are automatically saved to `~/.deepcode/sessions.db`. Each session is associated with a directory, allowing you to continue conversations contextually.

## Configuration

The tool uses DeepSeek API endpoints. Make sure you have a valid API key from [DeepSeek](https://platform.deepseek.com/).

Environment variables:
- `DEEPSEEK_API_KEY` - Your API key (required)
- `DEEPSEEK_API_BASE` - API base URL (default: https://api.deepseek.com)
- `DEEPSEEK_MODEL` - Default model (default: deepseek-chat - conversational chat model)

Note: The default model is `deepseek-chat` which is optimized for conversational interactions. You can override this by setting `DEEPSEEK_MODEL` or using the `--model` flag.
