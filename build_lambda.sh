#!/bin/bash
# Bash script to build Lambda package with Linux dependencies

set -e

echo "Building Lambda package with Linux dependencies..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Clean up old build
if [ -d "lambda_linux" ]; then
    echo "Removing old lambda_linux directory..."
    rm -rf lambda_linux
fi

# Create build directory
echo "Creating build directory..."
mkdir lambda_linux

# Copy Lambda source code
echo "Copying Lambda source files..."
cp lambda/*.py lambda_linux/

# Check if requirements file exists
if [ -f "lambda/requirements.txt" ]; then
    echo "Installing dependencies for Linux platform..."
    pip install \
        --platform manylinux2014_x86_64 \
        --target lambda_linux \
        --implementation cp \
        --python-version 3.12 \
        --only-binary=:all: \
        --upgrade \
        -r lambda/requirements.txt
else
    echo "No requirements.txt found, skipping dependency installation"
fi

echo "Lambda package built successfully in lambda_linux/"
echo "You can now deploy with: cdk deploy"
