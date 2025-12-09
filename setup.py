#!/usr/bin/env python3
"""Setup script for Deep Code CLI"""

from setuptools import setup

try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "CLI tool powered by DeepSeek API - similar to Claude Code"

setup(
    name="deep-code",
    version="1.0.0",
    author="Deep Code CLI",
    description="CLI tool powered by DeepSeek API - similar to Claude Code",
    long_description=long_description,
    long_description_content_type="text/markdown",
    py_modules=["deepcode"],
    install_requires=[
        "openai>=1.12.0",
        "python-dotenv>=1.0.0",
        "rich>=13.7.0",
        "pyyaml>=6.0.1",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
    ],
    entry_points={
        "console_scripts": [
            "deepcode=deepcode:main",
            "dc=deepcode:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)

