# Deep Code - Advanced Features

This document describes the advanced features and improvements made to Deep Code to match Claude Code's capabilities.

## New Features Overview

### 1. Structured Tool System

Deep Code now includes a comprehensive tool system with dedicated tool classes, similar to Claude Code:

#### Available Tools

- **ReadTool**: Read file contents with line numbers and range support
- **WriteTool**: Create new files or overwrite existing ones
- **EditTool**: Make precise edits using exact string matching
- **GlobTool**: Find files matching glob patterns
- **GrepTool**: Search file contents using regex patterns
- **BashTool**: Execute shell commands with safety checks
- **WebSearchTool**: Search the web using DuckDuckGo
- **WebFetchTool**: Make HTTP requests (GET, POST, PUT, DELETE)

#### Using Tools

Tools can be accessed through the `ToolRegistry`:

```python
from tools import ToolRegistry

registry = ToolRegistry()

# Read a file
result = registry.execute('read', file_path='path/to/file.py')

# Find Python files
result = registry.execute('glob', pattern='**/*.py')

# Search for pattern
result = registry.execute('grep', pattern=r'def \w+\(', path='.')

# Execute command
result = registry.execute('bash', command='git status')
```

### 2. Enhanced Security

#### Security Validator

The `SecurityValidator` class provides comprehensive security checks:

```python
from security import SecurityValidator, SecurityConfig

# Create validator with custom config
config = SecurityConfig(
    allow_dangerous_commands=False,
    allow_file_writes=True,
    allow_file_deletes=False,
    max_file_size_mb=10
)

validator = SecurityValidator(config)

# Validate command
is_safe, error = validator.validate_command("rm -rf /")
# Returns: (False, "Forbidden command detected...")

# Validate file operations
is_safe, error = validator.validate_file_path("/etc/passwd", operation='write')
# Returns: (False, "Cannot write system directory...")
```

#### Dangerous Command Detection

The security system detects and blocks:
- Fork bombs (`:(){:|:&};:`)
- Recursive deletions (`rm -rf /`)
- Filesystem formatting (`mkfs.`)
- Device writes (`> /dev/sd`)
- Piping to shell (`curl ... | bash`)
- And more...

#### Sensitive File Protection

Automatically detects sensitive files:
- Private keys (`.pem`, `.key`)
- Credentials (`.env`, `credentials.*`)
- SSH keys (`~/.ssh/*`)
- AWS credentials (`~/.aws/*`)

### 3. Context Management

#### Token Counting and Optimization

```python
from context_manager import ContextManager

manager = ContextManager(model='deepseek-chat', reserve_tokens=4000)

# Count tokens in text
token_count = manager.count_tokens("Hello, World!")

# Check if message fits in context
messages = [...]
can_fit = manager.can_fit_message(messages, "New message")

# Get token statistics
stats = manager.get_token_stats(messages)
print(f"Using {stats.percentage_used:.1f}% of context")

# Optimize context when needed
optimized = manager.optimize_context(messages, strategy='truncate')
```

#### Message Building Helpers

```python
from context_manager import MessageBuilder

# Create structured messages
messages = [
    MessageBuilder.system("You are a helpful assistant"),
    MessageBuilder.user("Hello!"),
    MessageBuilder.assistant("Hi there!")
]

# Format tool results
tool_result = MessageBuilder.format_tool_result(
    "Read",
    file_content,
    success=True
)

# Format file content with line numbers
content = MessageBuilder.format_file_content(
    "app.py",
    source_code,
    line_numbers=True
)
```

### 4. Improved Edit Tool

The Edit tool now works exactly like Claude Code's Edit tool:

#### Features
- **Exact string matching**: Must match exactly including whitespace
- **Unique match requirement**: Fails if string appears multiple times (unless `replace_all=True`)
- **Indentation preservation**: Maintains exact formatting
- **Clear error messages**: Tells you when string not found or not unique

#### Example Usage

```python
from tools import EditTool

editor = EditTool()

# Make a precise edit
result = editor.execute(
    file_path='app.py',
    old_string='def old_function():\n    pass',
    new_string='def new_function():\n    return True'
)

# Replace all occurrences
result = editor.execute(
    file_path='config.py',
    old_string='DEBUG = False',
    new_string='DEBUG = True',
    replace_all=True
)
```

### 5. Glob and Grep Tools

#### Glob Tool - Find Files

```python
from tools import GlobTool

glob = GlobTool()

# Find all Python files recursively
result = glob.execute(pattern='**/*.py', path='.')

# Find TypeScript files in src directory
result = glob.execute(pattern='*.ts', path='src')

# Custom ignore patterns
result = glob.execute(
    pattern='**/*',
    ignore_patterns=['**/test_*', '**/.git/**']
)
```

#### Grep Tool - Search Code

```python
from tools import GrepTool

grep = GrepTool()

# Search for pattern
result = grep.execute(pattern=r'def \w+\(', path='.')

# Case-insensitive search
result = grep.execute(
    pattern='TODO',
    path='.',
    ignore_case=True
)

# Search specific file types
result = grep.execute(
    pattern='import.*react',
    path='.',
    file_pattern='*.tsx'
)

# Show context lines
result = grep.execute(
    pattern='async def',
    context_lines=3
)
```

### 6. Enhanced System Prompt

The system prompt has been significantly improved to match Claude Code's behavior:

#### Key Improvements
- Clear tool descriptions and usage guidelines
- Emphasis on proactive tool usage
- Safety guidelines for dangerous operations
- File operation best practices
- Code formatting standards
- Response quality guidelines

#### Tool Usage Patterns

The AI now understands these patterns:
- `@read path/to/file` - Read a file
- `@grep "pattern"` - Search code
- `@glob "**/*.py"` - Find files
- `@bash command` - Execute command
- `@web query` - Web search
- `@curl URL` - HTTP request

### 7. Test Suite

Comprehensive test suite included in `test_tools.py`:

```bash
# Run all tests
python test_tools.py

# Run specific test class
python test_tools.py TestEditTool

# Run with verbose output
python -m unittest test_tools -v
```

Tests cover:
- All tool functionality
- Security validation
- Edge cases and error handling
- Tool registry operations

### 8. Permission Management

```python
from security import PermissionManager

manager = PermissionManager()

# Grant permissions
manager.grant_permission('bash', auto_approve=True)
manager.grant_permission('file_write')

# Check permission
if manager.request_permission('bash', details='git status'):
    # Execute operation
    pass

# Get permission status
status = manager.get_permission_status()
```

## Usage Examples

### Example 1: Safe File Editing

```python
from tools import ToolRegistry

registry = ToolRegistry()

# Read file first
read_result = registry.execute('read', file_path='config.py')
print(read_result.output)

# Make precise edit
edit_result = registry.execute(
    'edit',
    file_path='config.py',
    old_string='DEBUG = False',
    new_string='DEBUG = True'
)

if edit_result.success:
    print("✓ File updated successfully")
```

### Example 2: Finding and Searching Code

```python
from tools import ToolRegistry

registry = ToolRegistry()

# Find all Python test files
glob_result = registry.execute('glob', pattern='**/test_*.py')
print(f"Found {glob_result.metadata['count']} test files")

# Search for TODO comments
grep_result = registry.execute(
    'grep',
    pattern=r'#\s*TODO:',
    file_pattern='*.py'
)
print(grep_result.output)
```

### Example 3: Security-Aware Command Execution

```python
from tools import BashTool
from security import SecurityValidator

bash = BashTool()
validator = SecurityValidator()

command = "git status"

# Validate before execution
is_safe, error = validator.validate_command(command)

if is_safe:
    result = bash.execute(command)
    print(result.output)
else:
    print(f"Blocked: {error}")
```

## Configuration

### Security Configuration

Create a `.deepcode_security.yaml`:

```yaml
security:
  allow_dangerous_commands: false
  allow_file_writes: true
  allow_file_deletes: false
  max_file_size_mb: 10
  allowed_directories:
    - /home/user/projects
    - /tmp
  blocked_directories:
    - /etc
    - /usr/bin
```

### Context Management

Set in environment or code:

```bash
export DEEPCODE_MAX_CONTEXT_TOKENS=60000
export DEEPCODE_RESERVE_TOKENS=4000
export DEEPCODE_CONTEXT_STRATEGY=truncate  # or 'summarize'
```

## Best Practices

### 1. Always Read Before Edit

```python
# Good
read_result = registry.execute('read', file_path='app.py')
# ... analyze content ...
edit_result = registry.execute('edit', file_path='app.py', ...)

# Bad - editing without reading
edit_result = registry.execute('edit', file_path='app.py', ...)
```

### 2. Use Glob Before Grep

```python
# Find relevant files first
files = registry.execute('glob', pattern='src/**/*.py')

# Then search in specific locations
results = registry.execute('grep', pattern='async', path='src')
```

### 3. Validate Commands

```python
# Always validate before execution
validator = SecurityValidator()
is_safe, error = validator.validate_command(user_command)

if not is_safe:
    print(f"Command blocked: {error}")
    return

result = bash.execute(user_command)
```

### 4. Handle Tool Results Properly

```python
result = tool.execute(**params)

if result.success:
    print(f"✓ {result.output}")
    if result.metadata:
        print(f"Metadata: {result.metadata}")
else:
    print(f"✗ Error: {result.error}")
```

### 5. Manage Context Size

```python
context_manager = ContextManager()

# Check before adding large content
if context_manager.can_fit_message(messages, large_content):
    messages.append({"role": "user", "content": large_content})
else:
    # Optimize context first
    messages = context_manager.optimize_context(messages)
    messages.append({"role": "user", "content": large_content})
```

## Migration from Old Version

If you're upgrading from an older version:

1. **Install new dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Update imports**:
   ```python
   # Old
   from deepcode import execute_bash, web_search

   # New
   from tools import ToolRegistry
   registry = ToolRegistry()
   ```

3. **Update tool calls**:
   ```python
   # Old
   stdout, stderr, code = execute_bash("ls -la")

   # New
   result = registry.execute('bash', command='ls -la')
   if result.success:
       print(result.output)
   ```

## Performance Considerations

- **Token Counting**: Small overhead (~1-2ms per call)
- **Security Validation**: Minimal overhead (~0.1ms)
- **Tool Execution**: Same as direct execution
- **Context Management**: Efficient for conversations up to 60K tokens

## Troubleshooting

### Issue: "Tool not found"

```python
# Check available tools
registry = ToolRegistry()
print(registry.list_tools())
```

### Issue: "Command blocked by security"

```python
# Check security configuration
from security import get_security_validator

validator = get_security_validator()
config = validator.config
print(f"Dangerous commands allowed: {config.allow_dangerous_commands}")
```

### Issue: "Token limit exceeded"

```python
# Optimize context
manager = ContextManager()
stats = manager.get_token_stats(messages)
if stats.percentage_used > 90:
    messages = manager.optimize_context(messages, strategy='truncate')
```

## Contributing

When adding new tools:

1. Inherit from `Tool` base class
2. Implement `execute()` method
3. Return `ToolResult` object
4. Add security validation if needed
5. Write tests in `test_tools.py`
6. Update documentation

Example:

```python
from tools import Tool, ToolResult

class MyTool(Tool):
    def __init__(self):
        super().__init__("MyTool", "Description of my tool")

    def execute(self, param1: str, param2: int = 10) -> ToolResult:
        try:
            # Your implementation
            output = f"Processed {param1}"
            return ToolResult(
                success=True,
                output=output,
                metadata={'param2': param2}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e)
            )
```

## License

Same as Deep Code - MIT License
