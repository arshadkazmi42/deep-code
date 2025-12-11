# Deep Code - Quick Reference Guide

## Installation

```bash
pip install -r requirements.txt
pip install -e .
export DEEPSEEK_API_KEY=your_api_key_here
deepcode
```

## Basic Commands

| Command | Description |
|---------|-------------|
| `deepcode` | Start interactive chat |
| `deepcode "query"` | Start with initial question |
| `deepcode -p "query"` | One-shot query (print mode) |
| `deepcode -c` | Continue last session |
| `deepcode -r SESSION_ID` | Resume specific session |

## Tool Syntax in Chat

### File Operations
```
@read path/to/file                    # Read file
@read path/to/file 10 20              # Read lines 10-20
@glob "**/*.py"                       # Find Python files
@glob "src/**/*.ts"                   # Find TypeScript in src
@grep "pattern"                       # Search for pattern
@grep "def \w+\(" --ignore-case      # Case-insensitive search
```

### Command Execution
```
@bash ls -la                          # List files
@bash git status                      # Git status
@run npm install                      # Install packages
@exec python test.py                  # Run Python script
```

### Web Access
```
@web latest Python features           # Search web
@search React hooks tutorial          # Alternative syntax
@curl https://api.github.com          # HTTP GET
@fetch https://example.com/api        # Alternative syntax
```

## Security Levels

### Safe (Auto-approved)
- Reading files
- Listing directories
- Searching code
- Web searches
- GET requests

### Requires Confirmation
- Writing files
- Executing commands
- POST/PUT/DELETE requests
- Deleting files

### Blocked by Default
- `rm -rf /`
- Fork bombs
- Filesystem formatting
- Writing to /etc, /bin
- Piping to shell
- Wildcard deletions

## Common Workflows

### 1. Understand Codebase
```
You: Analyze this project
AI: [Automatically reads README, key files, directory structure]

You: Find all API routes
AI: @glob "**/*routes*.py"
    @grep "app\.(get|post|put|delete)"
```

### 2. Fix Bug
```
You: Fix the authentication bug in auth.py
AI: @read auth.py
    [Analyzes code]
    @grep "authenticate" --context 5
    [Suggests fix with exact string replacement]
```

### 3. Add Feature
```
You: Add logging to all functions in utils.py
AI: @read utils.py
    [Suggests changes]
    @edit utils.py [exact replacements]
```

### 4. Run Tests
```
You: Run the test suite
AI: @bash pytest -v
    [Shows results]
    @bash pytest --cov
    [Shows coverage]
```

### 5. Debug Error
```
You: Check what's wrong with the server
AI: @bash cat server.log | tail -50
    @grep "ERROR" server.log
    [Analyzes errors]
```

## File Editing Patterns

### Small Changes (Use Edit)
```
You: Change DEBUG to True in config.py
AI: @read config.py
    @edit config.py
    OLD: DEBUG = False
    NEW: DEBUG = True
```

### New Files (Use Write)
```
You: Create a new API endpoint for users
AI: @write app/routes/users.py
    [Complete file content]
```

### Large Refactors
```
You: Refactor database.py to use async
AI: @read database.py
    [Analyzes structure]
    @write database.py
    [Complete rewritten file]
```

## Tips and Tricks

### 1. Be Specific with File Paths
```
Good: @read ./src/components/Button.tsx
Bad:  Read the button file
```

### 2. Use Glob Before Grep
```
# Find files first
@glob "**/test_*.py"

# Then search in them
@grep "def test_" test/
```

### 3. Check Before Deleting
```
# List what would be deleted
@bash ls target_dir

# Then delete if safe
@bash rm -r target_dir
```

### 4. Read Before Edit
```
# Always read to see current content
@read config.py

# Then edit with exact string
@edit config.py ...
```

### 5. Use Context for Better Results
```
# Provide context
You: In the UserService class in services/user.py,
     update the login method to add rate limiting

# Rather than
You: Add rate limiting
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+C` or `ESC` | Interrupt streaming response |
| `Ctrl+D` | Exit chat |
| `Ctrl+L` | Clear screen (terminal) |

## Command Modifiers

### Read Tool
```
@read file.py              # Read entire file
@read file.py 1 50         # Read lines 1-50
@read file.py 100          # Read from line 100
```

### Grep Tool
```
@grep pattern              # Basic search
@grep pattern -i           # Case-insensitive
@grep pattern -C 3         # 3 lines of context
@grep pattern *.py         # Only Python files
```

### Bash Tool
```
@bash command              # Execute command
@bash command --timeout 60 # Custom timeout
```

## Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| "String not found" | Edit tool can't find exact match | Check whitespace and formatting |
| "Not unique" | Edit string appears multiple times | Be more specific or use `replace_all` |
| "Command blocked" | Security blocked dangerous command | Add confirmation or adjust security config |
| "File not found" | Path doesn't exist | Check path and current directory |
| "Permission denied" | No write/execute permission | Check file permissions |

## Configuration

### Security Settings
Create `.deepcode_security.yaml`:
```yaml
security:
  allow_dangerous_commands: false
  allow_file_writes: true
  max_file_size_mb: 10
  blocked_directories:
    - /etc
    - /usr
```

### Environment Variables
```bash
export DEEPSEEK_API_KEY=your_key
export DEEPSEEK_API_BASE=https://api.deepseek.com
export DEEPSEEK_MODEL=deepseek-chat
export DEEPCODE_MAX_CONTEXT_TOKENS=60000
```

## Best Practices

### ✅ Do
- Read files before editing
- Use specific file paths
- Validate changes after edits
- Commit changes frequently
- Use Glob to find files
- Use Grep to search code

### ❌ Don't
- Edit without reading first
- Use vague file descriptions
- Run commands you don't understand
- Delete without checking first
- Ignore security warnings
- Commit secrets

## Advanced Usage

### Using as Library
```python
from tools import ToolRegistry
from context_manager import ContextManager

# Initialize tools
registry = ToolRegistry()

# Execute tool
result = registry.execute('read', file_path='app.py')
if result.success:
    print(result.output)

# Manage context
context = ContextManager()
stats = context.get_token_stats(messages)
```

### Custom Security Config
```python
from security import SecurityConfig, SecurityValidator

config = SecurityConfig(
    allow_dangerous_commands=False,
    allowed_directories=['/home/user/projects'],
    max_file_size_mb=10
)

validator = SecurityValidator(config)
```

### Token Management
```python
from context_manager import ContextManager

manager = ContextManager(model='deepseek-chat')

# Check token usage
stats = manager.get_token_stats(messages)
print(f"Using {stats.percentage_used:.1f}% of context")

# Optimize if needed
if stats.percentage_used > 90:
    messages = manager.optimize_context(messages)
```

## Troubleshooting

### Tool Not Working
```bash
# Check if tools are available
python -c "from tools import ToolRegistry; print(ToolRegistry().list_tools())"
```

### Token Limit Issues
```bash
# Reduce context
deepcode --system-prompt "You are a concise assistant"
```

### Security Blocks
```python
# Check what's blocked
from security import SecurityValidator
validator = SecurityValidator()
is_safe, error = validator.validate_command("your command")
print(error if not is_safe else "Safe")
```

### Performance Issues
```bash
# Use print mode for one-shot queries
deepcode -p "query" --output-format json

# Limit directory scanning
deepcode --system-prompt "Don't analyze directory"
```

## Getting Help

```
# In chat
help          # Show help
?             # Also shows help

# Check version
deepcode --version

# View documentation
cat FEATURES.md
cat README.md
```

## Examples

### Example 1: Code Review
```
You: Review auth.py for security issues
AI: @read auth.py
    [Analyzes code]
    @grep "password" auth.py
    [Identifies issues]
    Issues found:
    1. Plain text password comparison
    2. No rate limiting
    3. Missing input validation
```

### Example 2: Refactoring
```
You: Refactor utils.py to use type hints
AI: @read utils.py
    [Analyzes functions]
    @edit utils.py
    [Adds type hints to each function]
    @bash python -m mypy utils.py
    [Verifies types]
```

### Example 3: Debugging
```
You: Why is my API returning 500?
AI: @bash cat logs/error.log | tail -100
    @grep "Exception" logs/
    @read api/routes.py
    [Analyzes error]
    Found: Uncaught exception in route handler
```

### Example 4: Feature Addition
```
You: Add Redis caching to the user service
AI: @read services/user.py
    @read requirements.txt
    @edit requirements.txt
    ADD: redis>=4.0.0
    @edit services/user.py
    [Adds Redis caching code]
    @bash pip install redis
```

## Quick Win Patterns

### Pattern 1: Search and Replace Across Files
```
@grep "old_name"            # Find all occurrences
@glob "**/*.py"             # Get all Python files
# Then edit each file individually
```

### Pattern 2: Validate Before Execute
```
@bash python -m py_compile script.py   # Check syntax
@bash python script.py                  # Run if valid
```

### Pattern 3: Safe Deployment
```
@bash git status                        # Check changes
@bash pytest                            # Run tests
@bash git add .                         # Stage
@bash git commit -m "message"           # Commit
```

---

**For more details, see:**
- `FEATURES.md` - Comprehensive feature documentation
- `README.md` - Installation and overview
- `CHANGELOG.md` - Version history
- `test_tools.py` - Usage examples in tests
