#!/usr/bin/env python3
"""
Build release binaries for Deep Code
Generates executables for Windows, macOS, and Linux
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

# Version info
VERSION = "2.0.0"
APP_NAME = "deepcode"

# Build configurations
BUILDS = {
    "windows": {
        "name": f"{APP_NAME}-{VERSION}-windows-x64.exe",
        "platform": "Windows",
        "icon": "assets/icon.ico" if Path("assets/icon.ico").exists() else None
    },
    "macos-intel": {
        "name": f"{APP_NAME}-{VERSION}-macos-intel",
        "platform": "Darwin",
        "arch": "x86_64",
        "icon": "assets/icon.icns" if Path("assets/icon.icns").exists() else None
    },
    "macos-arm": {
        "name": f"{APP_NAME}-{VERSION}-macos-arm",
        "platform": "Darwin",
        "arch": "arm64",
        "icon": "assets/icon.icns" if Path("assets/icon.icns").exists() else None
    },
    "linux": {
        "name": f"{APP_NAME}-{VERSION}-linux-x64",
        "platform": "Linux",
    }
}


def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        return True
    except ImportError:
        return False


def install_pyinstaller():
    """Install PyInstaller"""
    print("📦 Installing PyInstaller...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    print("✅ PyInstaller installed!")


def get_current_platform():
    """Detect current platform"""
    system = platform.system()
    machine = platform.machine().lower()

    if system == "Windows":
        return "windows"
    elif system == "Darwin":
        if machine in ["arm64", "aarch64"]:
            return "macos-arm"
        else:
            return "macos-intel"
    elif system == "Linux":
        return "linux"
    else:
        return None


def create_spec_file(build_type):
    """Create PyInstaller spec file for build"""
    config = BUILDS[build_type]

    # Base imports
    imports = [
        "openai",
        "rich",
        "requests",
        "bs4",
        "dotenv",
        "tiktoken",
        "yaml",
        "pathlib",
        "sqlite3",
    ]

    # Hidden imports
    hidden_imports = [
        "tiktoken_ext.openai_public",
        "tiktoken_ext",
        "rich.markdown",
        "rich.syntax",
        "rich.console",
    ]

    # Data files
    datas = [
        ("README.md", "."),
        ("FEATURES.md", "."),
        ("QUICK_REFERENCE.md", "."),
    ]

    # Build spec content
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['deepcode.py'],
    pathex=[],
    binaries=[],
    datas={datas},
    hiddenimports={hidden_imports},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy', 'PIL'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{config["name"]}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    {'icon=' + repr(config.get("icon")) + ',' if config.get("icon") else ''}
)
"""

    spec_file = f"deepcode_{build_type}.spec"
    with open(spec_file, "w") as f:
        f.write(spec_content)

    return spec_file


def build_binary(build_type):
    """Build binary for specified platform"""
    print(f"\n{'='*60}")
    print(f"🔨 Building for {build_type.upper()}")
    print(f"{'='*60}\n")

    # Create spec file
    spec_file = create_spec_file(build_type)

    try:
        # Run PyInstaller
        cmd = [
            "pyinstaller",
            "--clean",
            "--noconfirm",
            spec_file
        ]

        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

        # Clean up spec file
        if Path(spec_file).exists():
            Path(spec_file).unlink()

        print(f"\n✅ Build successful for {build_type}!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed for {build_type}: {e}")
        return False


def create_distribution_package(build_type):
    """Create distribution package with all necessary files"""
    config = BUILDS[build_type]
    binary_name = config["name"]

    # Create dist directory if it doesn't exist
    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)

    # Create package directory
    package_name = f"{APP_NAME}-{VERSION}-{build_type}"
    package_dir = dist_dir / package_name

    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True)

    # Copy binary
    binary_src = dist_dir / binary_name
    if binary_src.exists():
        shutil.copy(binary_src, package_dir / binary_name)

    # Copy documentation
    docs = ["README.md", "FEATURES.md", "QUICK_REFERENCE.md", "SETUP.md", "LICENSE"]
    for doc in docs:
        if Path(doc).exists():
            shutil.copy(doc, package_dir)

    # Create README for binary
    binary_readme = f"""# Deep Code {VERSION} - Binary Distribution

## Quick Start

1. Extract this archive
2. Set your API key:
   ```
   export DEEPSEEK_API_KEY=your_api_key_here
   ```
3. Run Deep Code:
   ```
   ./{binary_name}
   ```

## What's Included

- {binary_name} - Deep Code executable
- Documentation files

## System Requirements

- {config['platform']} operating system
{f"- {config.get('arch', 'x64')} architecture" if 'arch' in config else ""}
- Internet connection for API calls

## Getting Your API Key

Get your DeepSeek API key from: https://platform.deepseek.com/

## Usage

```bash
# Start interactive mode
./{binary_name}

# Start with a question
./{binary_name} "What does this project do?"

# Get help
./{binary_name} --help
```

## Documentation

- README.md - Full documentation
- FEATURES.md - Feature guide
- QUICK_REFERENCE.md - Command reference

## Support

For issues or questions, visit:
https://github.com/anthropics/deep-code

---

Version: {VERSION}
Platform: {build_type}
"""

    with open(package_dir / "README_BINARY.txt", "w") as f:
        f.write(binary_readme)

    # Create archive
    archive_name = f"{package_name}"

    if config["platform"] == "Windows":
        # Create ZIP for Windows
        shutil.make_archive(
            str(dist_dir / archive_name),
            "zip",
            package_dir
        )
        print(f"📦 Created: {archive_name}.zip")
    else:
        # Create tar.gz for Unix
        shutil.make_archive(
            str(dist_dir / archive_name),
            "gztar",
            package_dir
        )
        print(f"📦 Created: {archive_name}.tar.gz")

    # Clean up package directory
    shutil.rmtree(package_dir)


def build_current_platform():
    """Build for current platform only"""
    current = get_current_platform()

    if not current:
        print("❌ Unsupported platform")
        return False

    print(f"\n🎯 Building for current platform: {current}")

    if build_binary(current):
        create_distribution_package(current)
        return True

    return False


def build_all_platforms():
    """Build for all platforms (requires cross-platform tools)"""
    print("\n⚠️  Building for all platforms requires cross-compilation tools")
    print("This will only build for the current platform.")
    print("For cross-platform builds, use CI/CD or platform-specific machines.\n")

    return build_current_platform()


def clean_build_files():
    """Clean up build artifacts"""
    print("\n🧹 Cleaning build artifacts...")

    dirs_to_clean = ["build", "__pycache__"]
    files_to_clean = ["*.spec"]

    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            print(f"  Removed: {dir_name}/")

    for pattern in files_to_clean:
        for file in Path(".").glob(pattern):
            file.unlink()
            print(f"  Removed: {file}")

    print("✅ Cleanup complete!")


def main():
    """Main build script"""
    print(f"""
╭─────────────────────────────────────────────────────────╮
│                                                         │
│  Deep Code v{VERSION} - Release Builder                    │
│                                                         │
╰─────────────────────────────────────────────────────────╯
""")

    # Check PyInstaller
    if not check_pyinstaller():
        print("⚠️  PyInstaller not found")
        install_pyinstaller()

    # Parse command line
    if len(sys.argv) > 1:
        if sys.argv[1] == "clean":
            clean_build_files()
            return
        elif sys.argv[1] == "all":
            success = build_all_platforms()
        elif sys.argv[1] in BUILDS:
            build_type = sys.argv[1]
            if build_binary(build_type):
                create_distribution_package(build_type)
                success = True
            else:
                success = False
        else:
            print(f"❌ Unknown build type: {sys.argv[1]}")
            print(f"Available: {', '.join(BUILDS.keys())}, all, clean")
            return
    else:
        # Build current platform by default
        success = build_current_platform()

    if success:
        print(f"\n{'='*60}")
        print("✅ Build Complete!")
        print(f"{'='*60}")
        print(f"\n📁 Binaries location: ./dist/")
        print("\nNext steps:")
        print("1. Test the binary: ./dist/<binary-name>")
        print("2. Upload to releases: GitHub, website, etc.")
        print("3. Share with users!")
    else:
        print(f"\n{'='*60}")
        print("❌ Build Failed")
        print(f"{'='*60}")
        sys.exit(1)


if __name__ == "__main__":
    main()
