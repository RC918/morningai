#!/bin/bash
# =============================================================================
# MorningAI Development Environment Setup Script
# =============================================================================
#
# This script sets up a clean development environment and ensures correct
# dependency installation, particularly handling the PyJWT/jwt package conflict.
#
# Usage:
#   ./scripts/setup-dev.sh
#
# =============================================================================

set -e

echo "=== MorningAI Development Environment Setup ==="
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.12"

if [ "$PYTHON_VERSION" != "$REQUIRED_VERSION" ]; then
    echo "Warning: Python $REQUIRED_VERSION is recommended, but found Python $PYTHON_VERSION"
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install root dev dependencies (pytest, flake8, etc.)
echo "Installing root dev dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

# IMPORTANT: Remove the wrong jwt package if installed
# The 'jwt' package (jwt 1.x) conflicts with 'PyJWT' (jwt 2.x)
# We need PyJWT for proper JWT handling
echo "Removing conflicting jwt package (if present)..."
pip uninstall -y jwt 2>/dev/null || true

# Install dependencies for api-backend
echo "Installing api-backend dependencies..."
if [ -f "handoff/20250928/40_App/api-backend/requirements.txt" ]; then
    pip install -r handoff/20250928/40_App/api-backend/requirements.txt
fi

# Install dependencies for orchestrator
echo "Installing orchestrator dependencies..."
if [ -f "handoff/20250928/40_App/orchestrator/requirements.txt" ]; then
    pip install -r handoff/20250928/40_App/orchestrator/requirements.txt
fi

# Install orchestrator as editable package
echo "Installing orchestrator package..."
if [ -f "handoff/20250928/40_App/orchestrator/setup.py" ] || [ -f "handoff/20250928/40_App/orchestrator/pyproject.toml" ]; then
    pip install -e handoff/20250928/40_App/orchestrator
fi

# IMPORTANT: Fix dirty environment where jwt 1.x and PyJWT coexist
# When both packages are installed, uninstalling jwt can leave PyJWT in a broken
# namespace package state. Force-reinstalling PyJWT after all installs ensures
# the jwt module is properly restored.
echo ""
echo "=== Fixing PyJWT Installation (dirty environment repair) ==="
pip uninstall -y jwt 2>/dev/null || true
pip install --force-reinstall PyJWT

# Verify PyJWT installation
echo ""
echo "=== Verifying PyJWT Installation ==="
python -c "import jwt; assert hasattr(jwt, 'decode'), 'Wrong jwt package installed - need PyJWT, not jwt'"
if pip list | grep -qE '^jwt[[:space:]]'; then
    echo "ERROR: Wrong jwt package detected!"
    echo "The 'jwt' package (1.x) is installed instead of 'PyJWT' (2.x)"
    echo "Please run: pip uninstall jwt && pip install PyJWT"
    exit 1
fi
echo "PyJWT verification passed!"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To activate the environment in future sessions:"
echo "  source .venv/bin/activate"
echo ""
echo "To run the api-backend:"
echo "  cd handoff/20250928/40_App/api-backend && python -m flask run"
echo ""
echo "To run the orchestrator worker:"
echo "  cd handoff/20250928/40_App/orchestrator && python redis_queue/worker.py"
echo ""
