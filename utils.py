#!/usr/bin/env python3
"""Utility functions for file editing and code parsing"""

import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict

def extract_code_blocks(text: str) -> List[Dict[str, str]]:
    """Extract code blocks from markdown text
    
    Supports formats:
    - ```language:path/to/file\ncode\n```
    - ```language\ncode\n``` (no file path)
    - ```path/to/file\ncode\n``` (no language)
    """
    # Pattern: ```language:path/to/file\ncode\n``` or ```language\ncode\n```
    # Match both : separator and newline separator formats
    pattern = r'```(?:(?:(\w+))?(?::\s*([^\n]+))?)?\n(.*?)```'
    matches = re.finditer(pattern, text, re.DOTALL | re.MULTILINE)
    
    blocks = []
    for match in matches:
        language = match.group(1) or ""
        file_path = match.group(2) or ""
        code = match.group(3) or ""
        
        # Clean up file path
        if file_path:
            file_path = file_path.strip()
            # Remove common prefixes
            for prefix in ['File:', 'file:', 'Path:', 'path:']:
                if file_path.startswith(prefix):
                    file_path = file_path[len(prefix):].strip()
        
        # Also check if first line of code is a file path
        if not file_path and code:
            lines = code.split('\n')
            first_line = lines[0].strip()
            # Check if first line looks like a file path
            if any(ext in first_line for ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.cpp', '.c', '.h', '.rb', '.php', '.sh', '.md', '.txt', '.json', '.yml', '.yaml', '.html', '.css']):
                if '/' in first_line or '\\' in first_line or first_line.startswith('.'):
                    file_path = first_line
                    code = '\n'.join(lines[1:])
        
        if code.strip():
            blocks.append({
                'language': language,
                'file_path': file_path,
                'code': code.strip()
            })
    
    return blocks


def detect_file_edit_request(user_input: str, response: str) -> Optional[Dict]:
    """Detect if user wants to edit a file based on input and response"""
    edit_keywords = [
        'edit', 'modify', 'update', 'change', 'fix', 'add', 'remove',
        'replace', 'insert', 'delete', 'write', 'create', 'implement'
    ]
    
    # Check if user mentioned editing a file
    user_lower = user_input.lower()
    if not any(keyword in user_lower for keyword in edit_keywords):
        return None
    
    # Extract file path from user input
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
    
    # Extract code blocks from response
    code_blocks = extract_code_blocks(response)
    
    if file_path or code_blocks:
        return {
            'file_path': file_path,
            'code_blocks': code_blocks,
            'full_response': response
        }
    
    return None


def apply_code_changes(file_path: str, new_code: str, mode: str = 'replace') -> Tuple[bool, str]:
    """Apply code changes to a file
    
    Args:
        file_path: Path to the file
        new_code: New code content
        mode: 'replace' (replace entire file) or 'patch' (apply as patch)
    
    Returns:
        (success, message)
    """
    try:
        path = Path(file_path).expanduser().resolve()
        
        if mode == 'replace':
            # Replace entire file
            path.write_text(new_code, encoding='utf-8')
            return True, f"✓ Updated {path}"
        else:
            # Try to apply as patch (simple implementation)
            # This is a basic version - could be enhanced with proper diff/patch
            path.write_text(new_code, encoding='utf-8')
            return True, f"✓ Applied changes to {path}"
            
    except Exception as e:
        return False, f"✗ Error updating file: {str(e)}"

