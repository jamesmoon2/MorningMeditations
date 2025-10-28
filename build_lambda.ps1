# PowerShell script to build Lambda package with Linux dependencies
Write-Host "Building Lambda package with Linux dependencies..." -ForegroundColor Green

# Get the script's directory and change to it
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Clean up old build
if (Test-Path "lambda_linux") {
    Remove-Item -Recurse -Force lambda_linux
}

# Create build directory
New-Item -ItemType Directory -Path lambda_linux | Out-Null

# Copy Lambda source code
Write-Host "Copying Lambda source files..." -ForegroundColor Yellow
Copy-Item lambda/*.py lambda_linux/

# Install dependencies for Linux platform
Write-Host "Installing dependencies for Linux platform..." -ForegroundColor Yellow
pip install --platform manylinux2014_x86_64 --target lambda_linux --implementation cp --python-version 3.12 --only-binary=:all: --upgrade -r lambda/requirements.txt

Write-Host "Lambda package built successfully in lambda_linux/" -ForegroundColor Green
Write-Host "You can now deploy with: cdk deploy" -ForegroundColor Cyan
