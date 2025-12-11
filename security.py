#!/usr/bin/env python3
"""
Security utilities for Deep Code
Includes command validation, path sanitization, and permission management
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class SecurityConfig:
    """Security configuration"""
    allow_dangerous_commands: bool = False
    allow_file_writes: bool = True
    allow_file_deletes: bool = False
    allow_network_access: bool = True
    max_file_size_mb: int = 10
    allowed_directories: Optional[List[str]] = None  # None = all allowed
    blocked_directories: Optional[List[str]] = None


class SecurityValidator:
    """Validates operations for security"""

    # Extremely dangerous commands that should never run
    FORBIDDEN_COMMANDS = [
        ':(){:|:&};:',  # Fork bomb
        'rm -rf /',
        'rm -rf /*',
        'mkfs.',
        '> /dev/sd',
        'dd if=/dev/zero',
        'mv /* /dev/null',
        'chmod -R 777 /',
    ]

    # Dangerous patterns requiring extra confirmation
    DANGEROUS_PATTERNS = [
        r'rm\s+-[rf]+',  # rm with -r or -f flags
        r'rm\s+.*\*',  # rm with wildcards
        r'dd\s+if=',  # dd command
        r'mkfs\.',  # filesystem formatting
        r'format\s+',  # format command
        r'del(?:ete)?\s+/[sS]',  # Windows delete with /S flag
        r'>\s*/dev/',  # Writing to device files
        r'chmod\s+-R\s+777',  # Chmod 777 recursively
        r'chown\s+-R',  # Recursive chown (can be dangerous)
        r'wget.*\|\s*sh',  # Piping wget to shell
        r'curl.*\|\s*bash',  # Piping curl to bash
    ]

    # Sensitive file patterns
    SENSITIVE_FILES = [
        r'.*\.pem$',
        r'.*\.key$',
        r'.*\.crt$',
        r'.*\.p12$',
        r'.*\.pfx$',
        r'.*\.env$',
        r'.*\.env\..*$',
        r'.*credentials.*',
        r'.*secret.*',
        r'.*password.*',
        r'.*\.ssh/.*',
        r'.*\.aws/.*',
        r'.*\.gnupg/.*',
    ]

    def __init__(self, config: Optional[SecurityConfig] = None):
        """Initialize with security configuration"""
        self.config = config or SecurityConfig()

    def validate_command(self, command: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a bash command

        Returns:
            (is_safe, error_message)
        """
        # Check forbidden commands
        for forbidden in self.FORBIDDEN_COMMANDS:
            if forbidden in command:
                return False, f"Forbidden command detected: {forbidden}"

        # Check dangerous patterns
        if not self.config.allow_dangerous_commands:
            for pattern in self.DANGEROUS_PATTERNS:
                if re.search(pattern, command, re.IGNORECASE):
                    return False, f"Dangerous command pattern detected. Requires explicit permission: {command}"

        return True, None

    def validate_file_path(self, file_path: str, operation: str = 'read') -> Tuple[bool, Optional[str]]:
        """
        Validate file path for operation

        Args:
            file_path: Path to validate
            operation: 'read', 'write', or 'delete'

        Returns:
            (is_safe, error_message)
        """
        try:
            path = Path(file_path).expanduser().resolve()

            # Check if path exists for read operations
            if operation == 'read' and not path.exists():
                return False, f"Path does not exist: {path}"

            # Check allowed directories
            if self.config.allowed_directories:
                allowed = False
                for allowed_dir in self.config.allowed_directories:
                    allowed_path = Path(allowed_dir).expanduser().resolve()
                    try:
                        path.relative_to(allowed_path)
                        allowed = True
                        break
                    except ValueError:
                        continue

                if not allowed:
                    return False, f"Path outside allowed directories: {path}"

            # Check blocked directories
            if self.config.blocked_directories:
                for blocked_dir in self.config.blocked_directories:
                    blocked_path = Path(blocked_dir).expanduser().resolve()
                    try:
                        path.relative_to(blocked_path)
                        return False, f"Path in blocked directory: {path}"
                    except ValueError:
                        continue

            # Check system directories for write/delete
            if operation in ['write', 'delete']:
                system_dirs = ['/bin', '/sbin', '/usr/bin', '/usr/sbin', '/etc', '/sys', '/proc']
                for sys_dir in system_dirs:
                    try:
                        path.relative_to(sys_dir)
                        return False, f"Cannot {operation} system directory: {path}"
                    except ValueError:
                        continue

            # Check file permissions
            if operation == 'write' and not self.config.allow_file_writes:
                return False, "File writes are disabled by security policy"

            if operation == 'delete' and not self.config.allow_file_deletes:
                return False, "File deletes are disabled by security policy"

            # Check file size for writes
            if operation == 'read' and path.exists() and path.is_file():
                size_mb = path.stat().st_size / (1024 * 1024)
                if size_mb > self.config.max_file_size_mb:
                    return False, f"File too large: {size_mb:.1f}MB (max: {self.config.max_file_size_mb}MB)"

            # Check for sensitive files
            if self._is_sensitive_file(str(path)):
                if operation in ['write', 'delete']:
                    return False, f"Operation on sensitive file requires explicit confirmation: {path}"

            return True, None

        except Exception as e:
            return False, f"Path validation error: {str(e)}"

    def _is_sensitive_file(self, file_path: str) -> bool:
        """Check if file is sensitive"""
        file_path_lower = file_path.lower()
        for pattern in self.SENSITIVE_FILES:
            if re.match(pattern, file_path_lower):
                return True
        return False

    def validate_url(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Validate URL for network access

        Returns:
            (is_safe, error_message)
        """
        if not self.config.allow_network_access:
            return False, "Network access is disabled by security policy"

        # Check for local/private network access
        local_patterns = [
            r'https?://localhost',
            r'https?://127\.',
            r'https?://10\.',
            r'https?://192\.168\.',
            r'https?://172\.(1[6-9]|2[0-9]|3[0-1])\.',
            r'file://',
        ]

        for pattern in local_patterns:
            if re.match(pattern, url, re.IGNORECASE):
                return True, "Warning: Accessing local/private network"

        return True, None

    def sanitize_output(self, output: str, max_length: int = 50000) -> str:
        """
        Sanitize output for display

        Args:
            output: Output to sanitize
            max_length: Maximum output length
        """
        # Truncate long output
        if len(output) > max_length:
            output = output[:max_length] + f"\n\n... (truncated, total {len(output)} bytes)"

        # Remove potential ANSI escape codes that could be malicious
        # Keep common formatting but remove complex sequences
        output = re.sub(r'\x1b\[[0-9;]*[a-zA-Z&&[^mKH]]', '', output)

        return output


class PermissionManager:
    """Manages user permissions for operations"""

    def __init__(self):
        self.permissions = {
            'bash': False,
            'file_write': False,
            'file_delete': False,
            'web_access': False,
            'dangerous_commands': False,
        }
        self.auto_approve = {
            'bash': False,
            'file_write': False,
            'file_delete': False,
            'web_access': False,
        }

    def request_permission(self, operation: str, details: str = "") -> bool:
        """
        Request permission for operation

        Args:
            operation: Operation type
            details: Additional details about the operation
        """
        # Check if auto-approved
        if operation in self.auto_approve and self.auto_approve[operation]:
            return True

        # Check if permission already granted
        if operation in self.permissions and self.permissions[operation]:
            return True

        return False

    def grant_permission(self, operation: str, auto_approve: bool = False):
        """Grant permission for operation"""
        self.permissions[operation] = True
        if auto_approve:
            self.auto_approve[operation] = True

    def revoke_permission(self, operation: str):
        """Revoke permission for operation"""
        self.permissions[operation] = False
        self.auto_approve[operation] = False

    def get_permission_status(self) -> dict:
        """Get current permission status"""
        return {
            'permissions': self.permissions.copy(),
            'auto_approve': self.auto_approve.copy()
        }


# Global security validator instance
_default_validator = None


def get_security_validator(config: Optional[SecurityConfig] = None) -> SecurityValidator:
    """Get or create default security validator"""
    global _default_validator
    if _default_validator is None or config is not None:
        _default_validator = SecurityValidator(config)
    return _default_validator
