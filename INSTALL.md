# Installation Guide

## Quick Install

### Option 1: Install using pip (Recommended)

```bash
# Install dependencies
pip install -r requirements.txt

# Install the package (installs deepcode command globally)
pip install -e .
```

This will install `deepcode` and `dc` commands that you can use from anywhere.

### Option 2: Direct Usage (No Installation)

```bash
# Install dependencies only
pip install -r requirements.txt

# Run directly
python3 deepcode.py
# or
python3 deepcode.py "your query"
```

### Option 3: Install using setup.py

```bash
# Make sure setuptools is installed
pip install setuptools wheel

# Install the package
pip install -e .
# or
python3 setup.py install
```

## Setup API Key

After installation, set your DeepSeek API key:

```bash
export DEEPSEEK_API_KEY=your_api_key_here
```

Or create a `.env` file in the project directory:

```bash
echo "DEEPSEEK_API_KEY=your_api_key_here" > .env
```

## Verify Installation

After installation, you should be able to run:

```bash
deepcode --help
# or
dc --help
```

## Troubleshooting

### Error: "No module named 'setuptools'"

```bash
pip install setuptools wheel
```

### Error: "deepcode: command not found"

If using `pip install -e .`, make sure your Python bin directory is in your PATH:
```bash
# Add to ~/.zshrc or ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"
```

Or use the direct method:
```bash
python3 deepcode.py
```

### Error: "DEEPSEEK_API_KEY not found"

Make sure you've set the API key:
```bash
export DEEPSEEK_API_KEY=your_key_here
```

