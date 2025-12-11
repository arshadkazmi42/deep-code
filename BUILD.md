# Building Deep Code Release Binaries

This guide explains how to build release binaries for Deep Code on all platforms.

## Quick Build (Current Platform)

The easiest way to build for your current platform:

```bash
# Make scripts executable (first time only)
chmod +x build.sh

# Build binary for current platform
./build.sh
```

This will:
1. Install PyInstaller if needed
2. Build the binary for your platform
3. Create a distribution package
4. Place everything in `./dist/`

## Platform-Specific Builds

### 🪟 Windows

```bash
# On Windows (PowerShell or Git Bash)
python build_release.py windows
```

Or use the shell script:
```bash
./build.sh
```

Output: `dist/deepcode-2.0.0-windows-x64.zip`

### 🍎 macOS (Intel)

```bash
# On macOS Intel
python build_release.py macos-intel
```

Or:
```bash
./build.sh
```

Output: `dist/deepcode-2.0.0-macos-intel.tar.gz`

### 🍎 macOS (Apple Silicon)

```bash
# On macOS M1/M2
python build_release.py macos-arm
```

Or:
```bash
./build.sh
```

Output: `dist/deepcode-2.0.0-macos-arm.tar.gz`

### 🐧 Linux

```bash
# On Linux
python build_release.py linux
```

Or:
```bash
./build.sh
```

Output: `dist/deepcode-2.0.0-linux-x64.tar.gz`

## Automated Builds (GitHub Actions)

The repository includes GitHub Actions workflow for automated multi-platform builds.

### Trigger Build on Tag

```bash
# Create and push a tag
git tag v2.0.0
git push origin v2.0.0
```

This automatically:
1. Builds binaries for all platforms
2. Creates a GitHub Release
3. Uploads all binaries
4. Generates release notes

### Manual Workflow Dispatch

Via GitHub UI:
1. Go to Actions tab
2. Select "Build Release Binaries"
3. Click "Run workflow"
4. Enter version number
5. Run!

## Build Scripts

### `build.sh` (Quick Build)

Simple bash script for quick local builds.

**Features:**
- Auto-detects platform
- Installs dependencies
- Creates single binary
- Packages distribution
- Tests binary

**Usage:**
```bash
./build.sh
```

### `build_release.py` (Advanced)

Python script for more control.

**Features:**
- Build specific platforms
- Cross-platform support
- Clean builds
- Custom configurations

**Usage:**
```bash
# Build current platform
python build_release.py

# Build specific platform
python build_release.py windows
python build_release.py macos-intel
python build_release.py macos-arm
python build_release.py linux

# Build all (current platform only, warns about cross-compilation)
python build_release.py all

# Clean build artifacts
python build_release.py clean
```

## Requirements

### Dependencies

```bash
pip install pyinstaller
pip install -r requirements.txt
```

### Platform Requirements

| Platform | Requirements |
|----------|-------------|
| Windows | Python 3.8+, PyInstaller |
| macOS | Python 3.8+, PyInstaller, Xcode CLI tools |
| Linux | Python 3.8+, PyInstaller, build-essential |

## Build Output

### Directory Structure

```
dist/
├── deepcode-2.0.0-windows-x64.zip
├── deepcode-2.0.0-macos-intel.tar.gz
├── deepcode-2.0.0-macos-arm.tar.gz
└── deepcode-2.0.0-linux-x64.tar.gz
```

### Package Contents

Each package includes:
- Binary executable
- README_BINARY.txt
- README.md
- FEATURES.md
- QUICK_REFERENCE.md
- SETUP.md
- LICENSE (if exists)

## Testing Builds

### Test Binary

```bash
# Extract package
tar -xzf dist/deepcode-2.0.0-linux-x64.tar.gz  # Linux/macOS
# or
unzip dist/deepcode-2.0.0-windows-x64.zip      # Windows

# Set API key
export DEEPSEEK_API_KEY=your_key

# Test binary
./deepcode-2.0.0-linux-x64 --help
./deepcode-2.0.0-linux-x64 "test query"
```

### Verify Package

Check that package includes:
- ✅ Executable runs without Python
- ✅ All dependencies bundled
- ✅ Documentation included
- ✅ Reasonable file size (< 100MB)

## Distribution

### GitHub Releases

1. **Automated (Recommended)**:
   ```bash
   git tag v2.0.0
   git push origin v2.0.0
   ```

2. **Manual**:
   - Go to GitHub → Releases
   - Create new release
   - Upload binaries from `dist/`
   - Add release notes

### Download Links

After release, binaries available at:
```
https://github.com/your-org/deep-code/releases/download/v2.0.0/deepcode-2.0.0-windows-x64.zip
https://github.com/your-org/deep-code/releases/download/v2.0.0/deepcode-2.0.0-macos-intel.tar.gz
https://github.com/your-org/deep-code/releases/download/v2.0.0/deepcode-2.0.0-macos-arm.tar.gz
https://github.com/your-org/deep-code/releases/download/v2.0.0/deepcode-2.0.0-linux-x64.tar.gz
```

## Troubleshooting

### PyInstaller Issues

**Problem**: Import errors in binary

**Solution**: Add hidden imports to build script
```python
--hidden-import=module_name
```

**Problem**: Binary too large

**Solution**: Exclude unnecessary modules
```python
--exclude-module matplotlib
--exclude-module numpy
```

### Platform Issues

**macOS: "Cannot be opened because the developer cannot be verified"**

Solution:
```bash
xattr -cr deepcode-2.0.0-macos-intel
```

Or right-click → Open → Open anyway

**Linux: "Permission denied"**

Solution:
```bash
chmod +x deepcode-2.0.0-linux-x64
```

**Windows: "Windows protected your PC"**

Solution: Click "More info" → "Run anyway"

### Build Errors

**Problem**: Module not found during build

**Solution**:
```bash
pip install --upgrade -r requirements.txt
```

**Problem**: Build fails on macOS

**Solution**: Install Xcode command line tools
```bash
xcode-select --install
```

## Advanced Configuration

### Custom Build Options

Edit `build_release.py` or `build.sh`:

```python
# Change binary name
BINARY_NAME = "my-custom-name"

# Add icon
--icon=assets/icon.ico  # Windows
--icon=assets/icon.icns # macOS

# UPX compression
--upx-dir=/path/to/upx

# Strip symbols
--strip
```

### Optimize Binary Size

```bash
# Use UPX compression
pyinstaller ... --upx-dir=/usr/local/bin

# Exclude unnecessary modules
--exclude-module tkinter
--exclude-module PIL
--exclude-module matplotlib
```

### Code Signing (macOS)

```bash
# Sign binary
codesign --sign "Developer ID" --force --deep deepcode

# Verify
codesign --verify --deep --strict deepcode
```

### Notarization (macOS)

```bash
# Create ZIP
ditto -c -k --keepParent deepcode deepcode.zip

# Notarize
xcrun notarytool submit deepcode.zip \
  --apple-id your@email.com \
  --team-id TEAMID \
  --password APP_PASSWORD

# Staple
xcrun stapler staple deepcode
```

## CI/CD Integration

### GitHub Actions (Included)

See `.github/workflows/build-release.yml`

- ✅ Multi-platform builds
- ✅ Automatic releases
- ✅ Artifact uploads
- ✅ Release notes generation

### Other CI Systems

**GitLab CI**:
```yaml
build:
  script:
    - python build_release.py
  artifacts:
    paths:
      - dist/
```

**CircleCI**:
```yaml
jobs:
  build:
    steps:
      - run: python build_release.py
      - store_artifacts:
          path: dist/
```

## Version Management

Update version in:
1. `build_release.py` → `VERSION = "2.0.0"`
2. `build.sh` → `VERSION="2.0.0"`
3. `setup.py` → `version="2.0.0"`
4. Create git tag: `git tag v2.0.0`

## Summary

### Quick Commands

```bash
# Local build
./build.sh

# Clean
python build_release.py clean

# Release (automated)
git tag v2.0.0 && git push origin v2.0.0
```

### Checklist

- [ ] Update version numbers
- [ ] Test locally
- [ ] Build for all platforms
- [ ] Test binaries
- [ ] Create release
- [ ] Upload binaries
- [ ] Update documentation
- [ ] Announce release

---

**Questions?** Check:
- PyInstaller docs: https://pyinstaller.org/
- GitHub Actions: https://docs.github.com/actions
- This project's issues: GitHub Issues
