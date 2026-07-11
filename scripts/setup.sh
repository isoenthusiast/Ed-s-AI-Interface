#!/usr/bin/env bash
# =============================================================================
# 🚀 Setup Script for "Ed's AI Interface" — macOS / Linux
# =============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "🧠 Setting up Ed's AI Interface..."
echo "============================================"

# Step 1: Check Python
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "❌ Python is not installed. Install Python 3.10+ from https://python.org"
    exit 1
fi

echo "✅ Python: $($PYTHON --version)"

# Step 2: Create virtual environment
VENV_PATH="$PROJECT_ROOT/.venv"
if [ ! -d "$VENV_PATH" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON -m venv "$VENV_PATH"
    echo "✅ Virtual environment created at .venv"
else
    echo "✅ Virtual environment already exists"
fi

# Step 3: Activate and install dependencies
PIP="$VENV_PATH/bin/pip"
echo "📥 Installing dependencies..."
$PIP install --upgrade pip -q
$PIP install -r "$PROJECT_ROOT/requirements.txt" -q
echo "✅ Dependencies installed"

# Step 4: Check .secrets file
SECRETS_PATH="$PROJECT_ROOT/.secrets"
EXAMPLE_PATH="$PROJECT_ROOT/.secrets.example"
if [ ! -f "$SECRETS_PATH" ]; then
    echo "⚠️  No .secrets file found."
    if [ -f "$EXAMPLE_PATH" ]; then
        cp "$EXAMPLE_PATH" "$SECRETS_PATH"
        echo "📄 Created .secrets from .secrets.example"
        echo "✏️  Edit .secrets and add your DeepSeek API key!"
    fi
else
    echo "✅ .secrets file exists"
fi

# Step 5: Git init (if not already)
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo "📁 Initializing Git repository..."
    cd "$PROJECT_ROOT"
    git init
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already exists"
fi

# Done
echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .secrets with your DeepSeek API key"
echo "  2. Run: source .venv/bin/activate"
echo "  3. Run: python main.py"
echo ""
