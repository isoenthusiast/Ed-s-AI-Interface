# =============================================================================
# 🚀 Setup Script for "Ed's AI Interface" — Windows (PowerShell)
# =============================================================================
param(
    [switch]$NoInstall
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent

Write-Host "🧠 Setting up Ed's AI Interface..." -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# Step 1: Check Python
try {
    $pyVersion = python --version 2>&1
    Write-Host "✅ Python: $pyVersion" -ForegroundColor Green
}
catch {
    Write-Host "❌ Python is not installed. Install Python 3.10+ from https://python.org" -ForegroundColor Red
    exit 1
}

# Step 2: Create virtual environment
$venvPath = Join-Path $ProjectRoot ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $venvPath
    Write-Host "✅ Virtual environment created at .venv" -ForegroundColor Green
}
else {
    Write-Host "✅ Virtual environment already exists" -ForegroundColor Green
}

# Step 3: Activate and install dependencies
$pip = Join-Path $venvPath "Scripts\pip.exe"
if (-not $NoInstall) {
    Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
    & $pip install --upgrade pip -q
    & $pip install -r (Join-Path $ProjectRoot "requirements.txt") -q
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
}

# Step 4: Check .secrets file
$secretsPath = Join-Path $ProjectRoot ".secrets"
$examplePath = Join-Path $ProjectRoot ".secrets.example"
if (-not (Test-Path $secretsPath)) {
    Write-Host "⚠️  No .secrets file found." -ForegroundColor Yellow
    if (Test-Path $examplePath) {
        Copy-Item $examplePath $secretsPath
        Write-Host "📄 Created .secrets from .secrets.example" -ForegroundColor Green
        Write-Host "✏️  Edit .secrets and add your DeepSeek API key!" -ForegroundColor Yellow
    }
}
else {
    Write-Host "✅ .secrets file exists" -ForegroundColor Green
}

# Step 5: Git init (if not already)
if (-not (Test-Path (Join-Path $ProjectRoot ".git"))) {
    Write-Host "📁 Initializing Git repository..." -ForegroundColor Yellow
    Set-Location $ProjectRoot
    git init
    Write-Host "✅ Git repository initialized" -ForegroundColor Green
}
else {
    Write-Host "✅ Git repository already exists" -ForegroundColor Green
}

# Done
Write-Host ""
Write-Host "🎉 Setup complete!" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Edit .secrets with your DeepSeek API key" -ForegroundColor Yellow
Write-Host "  2. Run: .\.venv\Scripts\activate" -ForegroundColor Yellow
Write-Host "  3. Run: python main.py" -ForegroundColor Yellow
Write-Host ""
