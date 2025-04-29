#!/bin/bash

# Prevent direct execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Error: This script must be sourced, not executed directly."
    echo "Usage: source setup.sh"
    exit 1
fi

# Exit on error
set -e

# Function to print error messages
error() {
    echo "Error: $1" >&2
    return 1
}

# Function to check if a command exists
check_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        error "$1 is required but not installed"
        return 1
    fi
}

# Check required commands
check_command python || return 1
check_command pip || return 1

# Create virtual environment
echo "Creating virtual environment..."
if ! python -m venv venv; then
    error "Failed to create virtual environment"
    return 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
# shellcheck source=/dev/null
if ! source venv/bin/activate; then
    error "Failed to activate virtual environment"
    return 1
fi

# Install dependencies
echo "Installing dependencies..."
if ! pip install -r requirements.txt; then
    error "Failed to install dependencies"
    return 1
fi

# Create configuration file if it doesn't exist
if [ ! -f "transaction_config.json" ]; then
    echo "Creating configuration file from template..."
    if [ ! -f "transaction_config.example.json" ]; then
        error "Example configuration file not found"
        return 1
    fi
    if ! cp "transaction_config.example.json" "transaction_config.json"; then
        error "Failed to create configuration file"
        return 1
    fi
    echo "Please edit transaction_config.json to customize your settings"
fi

echo "Setup complete! The virtual environment is now active."
echo "You can run the tool with: python ccs_extract.py [pdf_file]"
echo ""
echo "To deactivate the virtual environment when done:"
echo "deactivate" 