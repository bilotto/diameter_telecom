#!/bin/bash

# Setup script for diameter_telecom documentation
# This script installs all necessary dependencies for building documentation

echo "Setting up diameter_telecom documentation..."

# Install python-diameter from GitHub
echo "Installing python-diameter from GitHub..."
pip install git+https://github.com/mensonen/diameter.git

# Install documentation dependencies
echo "Installing documentation dependencies..."
pip install mkdocs mkdocs-material mkdocstrings[python] mkdocs-autorefs pymdown-extensions

# Install diameter_telecom in editable mode
echo "Installing diameter_telecom in editable mode..."
pip install -e .

echo "Setup complete! You can now run:"
echo "  mkdocs serve    # Serve documentation locally"
echo "  mkdocs build   # Build documentation"


