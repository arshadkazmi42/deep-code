#!/bin/bash
# Quick build script for Deep Code binaries

set -e

VERSION="2.0.0"
APP_NAME="deepcode"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}╭─────────────────────────────────────────────────────────╮${NC}"
echo -e "${CYAN}│                                                         │${NC}"
echo -e "${CYAN}│  ${GREEN}Deep Code v${VERSION} - Quick Build${NC}                    ${CYAN}│${NC}"
echo -e "${CYAN}│                                                         │${NC}"
echo -e "${CYAN}╰─────────────────────────────────────────────────────────╯${NC}"
echo ""

# Check if PyInstaller is installed
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo -e "${YELLOW}📦 PyInstaller not found. Installing...${NC}"
    pip3 install pyinstaller
    echo -e "${GREEN}✅ PyInstaller installed!${NC}"
fi

# Detect platform
OS=$(uname -s)
ARCH=$(uname -m)

case "$OS" in
    Darwin)
        if [ "$ARCH" = "arm64" ]; then
            PLATFORM="macos-arm"
            BINARY_NAME="${APP_NAME}-${VERSION}-macos-arm"
        else
            PLATFORM="macos-intel"
            BINARY_NAME="${APP_NAME}-${VERSION}-macos-intel"
        fi
        ;;
    Linux)
        PLATFORM="linux"
        BINARY_NAME="${APP_NAME}-${VERSION}-linux-x64"
        ;;
    MINGW*|MSYS*|CYGWIN*)
        PLATFORM="windows"
        BINARY_NAME="${APP_NAME}-${VERSION}-windows-x64.exe"
        ;;
    *)
        echo -e "${RED}❌ Unsupported platform: $OS${NC}"
        exit 1
        ;;
esac

echo -e "${BLUE}🎯 Building for: ${PLATFORM} (${ARCH})${NC}"
echo ""

# Clean previous builds
echo -e "${YELLOW}🧹 Cleaning previous builds...${NC}"
rm -rf build dist *.spec

# Build binary
echo -e "${CYAN}🔨 Building binary...${NC}"

pyinstaller \
    --name="$BINARY_NAME" \
    --onefile \
    --console \
    --clean \
    --noconfirm \
    --hidden-import=tiktoken_ext.openai_public \
    --hidden-import=tiktoken_ext \
    --hidden-import=rich.markdown \
    --hidden-import=rich.syntax \
    --collect-data tiktoken \
    --exclude-module matplotlib \
    --exclude-module numpy \
    --exclude-module pandas \
    deepcode.py

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Build successful!${NC}"
    echo ""
    echo -e "${CYAN}📁 Binary location:${NC} ./dist/${BINARY_NAME}"

    # Make executable
    chmod +x "./dist/${BINARY_NAME}"

    # Test binary
    echo ""
    echo -e "${YELLOW}🧪 Testing binary...${NC}"
    "./dist/${BINARY_NAME}" --version 2>/dev/null || echo -e "${GREEN}Binary created successfully!${NC}"

    # Create distribution package
    echo ""
    echo -e "${CYAN}📦 Creating distribution package...${NC}"

    DIST_DIR="dist/${APP_NAME}-${VERSION}-${PLATFORM}"
    mkdir -p "$DIST_DIR"

    # Copy binary
    cp "./dist/${BINARY_NAME}" "$DIST_DIR/"

    # Copy docs
    for doc in README.md FEATURES.md QUICK_REFERENCE.md SETUP.md LICENSE; do
        [ -f "$doc" ] && cp "$doc" "$DIST_DIR/"
    done

    # Create README for binary distribution
    cat > "$DIST_DIR/README_BINARY.txt" << EOF
# Deep Code ${VERSION} - Binary Distribution

## Quick Start

1. Extract this archive
2. Set your API key:
   export DEEPSEEK_API_KEY=your_api_key_here
3. Run Deep Code:
   ./${BINARY_NAME}

## Platform

- OS: ${OS}
- Architecture: ${ARCH}
- Platform: ${PLATFORM}

## Usage

# Start interactive mode
./${BINARY_NAME}

# Start with a question
./${BINARY_NAME} "What does this project do?"

# Get help
./${BINARY_NAME} --help

## Get API Key

Get your DeepSeek API key from: https://platform.deepseek.com/

---
Version: ${VERSION}
Built on: $(date)
EOF

    # Create archive
    cd dist
    if [ "$PLATFORM" = "windows" ]; then
        zip -r "${APP_NAME}-${VERSION}-${PLATFORM}.zip" "${APP_NAME}-${VERSION}-${PLATFORM}"
        echo -e "${GREEN}✅ Created: ${APP_NAME}-${VERSION}-${PLATFORM}.zip${NC}"
    else
        tar -czf "${APP_NAME}-${VERSION}-${PLATFORM}.tar.gz" "${APP_NAME}-${VERSION}-${PLATFORM}"
        echo -e "${GREEN}✅ Created: ${APP_NAME}-${VERSION}-${PLATFORM}.tar.gz${NC}"
    fi
    cd ..

    echo ""
    echo -e "${GREEN}╭─────────────────────────────────────────────────────────╮${NC}"
    echo -e "${GREEN}│                                                         │${NC}"
    echo -e "${GREEN}│  ✅ Build Complete!                                     │${NC}"
    echo -e "${GREEN}│                                                         │${NC}"
    echo -e "${GREEN}╰─────────────────────────────────────────────────────────╯${NC}"
    echo ""
    echo -e "${CYAN}Next steps:${NC}"
    echo -e "  1. Test: ${YELLOW}./dist/${BINARY_NAME}${NC}"
    echo -e "  2. Upload to GitHub releases"
    echo -e "  3. Share with users!"
    echo ""

else
    echo ""
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
fi
