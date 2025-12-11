# Deep Code - Quick Setup Guide

## Installation

### Step 1: Install Deep Code

```bash
cd /path/to/deep-code
pip install -e .
```

This installs:
- `deepcode` command
- `dc` command (short alias)

### Step 2: Set API Key

```bash
export DEEPSEEK_API_KEY=your_api_key_here
```

Or add to your `.env` file in the project directory:
```bash
echo "DEEPSEEK_API_KEY=your_api_key_here" > .env
```

### Step 3: Run Deep Code

```bash
deepcode
```

Or use the short alias:
```bash
dc
```

## That's It!

You now have Deep Code with:
- ✅ Modern UI (automatic if modules available)
- ✅ Fixed auto-execution workflow
- ✅ All security features
- ✅ Tool system with Read, Write, Edit, Glob, Grep, Bash, WebSearch, WebFetch
- ✅ Context management
- ✅ Comprehensive tests

## Verify Installation

```bash
# Check version
deepcode --version

# Or run directly
python deepcode.py
```

## UI Features

The modern UI will automatically activate if all modules are available:
- Structured panels for tool calls
- Color-coded output
- Professional design
- Better visual hierarchy

If any module is missing, it falls back gracefully to basic mode.

## Usage

### Start Interactive Chat
```bash
deepcode
```

### Start with a Question
```bash
deepcode "Analyze this project"
```

### Continue Last Session
```bash
deepcode -c
```

### Get Help
```bash
deepcode --help
```

## Troubleshooting

### "deepcode: command not found"

```bash
# Reinstall
pip install -e .

# Or run directly
python deepcode.py
```

### Missing Modules

If you see import errors:
```bash
pip install -r requirements.txt
```

### API Key Not Set

```bash
export DEEPSEEK_API_KEY=your_key
```

Or create `.env` file with your API key.

## All Features Work Out of the Box

- ✅ Auto-execution fixes applied
- ✅ Modern UI (when modules available)
- ✅ Security validation
- ✅ Context management
- ✅ Comprehensive tools
- ✅ Session management

## Optional: Add to Shell Profile

For permanent setup, add to `~/.bashrc` or `~/.zshrc`:

```bash
export DEEPSEEK_API_KEY=your_api_key_here
alias dc=deepcode
```

Then reload:
```bash
source ~/.bashrc  # or ~/.zshrc
```

## Done!

You're ready to use Deep Code:

```bash
$ deepcode
╭─────────────────────────────────────────────────────────╮
│  Deep Code - AI Coding Assistant                       │
│  Powered by DeepSeek                                   │
╰─────────────────────────────────────────────────────────╯

Tool Permissions
? HTTP requests (curl)? (Y/n)
? Shell commands (bash)? (Y/n)
? Web searches? (Y/n)

Type 'help' for commands, 'exit' to quit

❯ _
```

Enjoy! 🚀
