#!/bin/bash

# ImageFox Tools Setup Script

echo "Setting up ImageFox tools environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "Creating requirements.txt..."
    cat > requirements.txt << EOF
requests==2.31.0
python-dotenv==1.0.0
click==8.1.7
colorama==0.4.6
tabulate==0.9.0
EOF
    pip install -r requirements.txt
fi

# Load environment variables from parent directory
if [ -f "../.env" ]; then
    echo "Found .env file in parent directory"
else
    echo "Warning: No .env file found in parent directory"
    echo "Please create one based on ../.env.example"
fi

# Create README if it doesn't exist
if [ ! -f "README.md" ]; then
    echo "Creating tools README..."
    cat > README.md << 'EOF'
# ImageFox Tools

This directory contains utility scripts for the ImageFox project.

## Setup
Run `bash setup.sh` to set up the virtual environment and install dependencies.

## Available Tools
- `test_apify.py` - Test Apify API connectivity
- `test_openrouter.py` - Test OpenRouter API
- `test_imagebb.py` - Test ImageBB upload
- `validate_config.py` - Validate environment configuration

## Usage
```bash
# Activate virtual environment
source venv/bin/activate

# Run a tool
python <tool_name>.py
```

## Adding New Tools
1. Create your tool script in this directory
2. Add any new dependencies to requirements.txt
3. Use python-dotenv to load the parent .env file
4. Document your tool in this README
EOF
fi

echo "Creating validate_config.py tool..."
cat > validate_config.py << 'EOF'
#!/usr/bin/env python3
"""Configuration validation tool for ImageFox."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from tabulate import tabulate
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Load environment variables from parent directory
parent_dir = Path(__file__).parent.parent
env_path = parent_dir / '.env'
load_dotenv(env_path)

def check_api_key(name, required=True):
    """Check if an API key is configured."""
    value = os.getenv(name)
    if value and value != f"your_{name.lower()}_here":
        return ("✓", Fore.GREEN + "Configured" + Style.RESET_ALL)
    elif required:
        return ("✗", Fore.RED + "Missing/Invalid" + Style.RESET_ALL)
    else:
        return ("○", Fore.YELLOW + "Optional" + Style.RESET_ALL)

def main():
    """Validate ImageFox configuration."""
    print("\n" + Fore.CYAN + "=" * 50)
    print("ImageFox Configuration Validator")
    print("=" * 50 + Style.RESET_ALL + "\n")

    # Check required API keys
    required_keys = [
        ("APIFY_API_KEY", "Apify (Google Images search)"),
        ("OPENROUTER_API_KEY", "OpenRouter (Vision LLMs)"),
        ("AIRTABLE_API_KEY", "Airtable (Metadata storage)"),
        ("IMAGEBB_API_KEY", "ImageBB (Image hosting)"),
    ]
    
    # Check optional API keys
    optional_keys = [
        ("SENTRY_DSN", "Sentry (Error monitoring)"),
        ("LINEAR_API_KEY", "Linear (Project management)"),
    ]
    
    results = []
    
    print(Fore.YELLOW + "Checking Required API Keys:" + Style.RESET_ALL)
    for key, description in required_keys:
        status, message = check_api_key(key, required=True)
        results.append([status, key, description, message])
    
    print(tabulate(results, headers=["", "Key", "Service", "Status"], tablefmt="grid"))
    
    results = []
    print("\n" + Fore.YELLOW + "Checking Optional API Keys:" + Style.RESET_ALL)
    for key, description in optional_keys:
        status, message = check_api_key(key, required=False)
        results.append([status, key, description, message])
    
    print(tabulate(results, headers=["", "Key", "Service", "Status"], tablefmt="grid"))
    
    # Check configuration values
    config_values = []
    print("\n" + Fore.YELLOW + "Configuration Values:" + Style.RESET_ALL)
    
    configs = [
        ("MAX_WORKERS", "3"),
        ("REQUEST_TIMEOUT", "30"),
        ("RETRY_ATTEMPTS", "3"),
        ("CACHE_TTL", "3600"),
        ("DEFAULT_VISION_MODEL", "openai/gpt-4-vision-preview"),
    ]
    
    for config, default in configs:
        value = os.getenv(config, default)
        config_values.append([config, value, default])
    
    print(tabulate(config_values, headers=["Setting", "Current", "Default"], tablefmt="grid"))
    
    # Summary
    print("\n" + Fore.CYAN + "=" * 50)
    
    # Check if all required keys are present
    all_valid = all(
        os.getenv(key) and os.getenv(key) != f"your_{key.lower()}_here"
        for key, _ in required_keys
    )
    
    if all_valid:
        print(Fore.GREEN + "✓ Configuration is valid and ready!" + Style.RESET_ALL)
        return 0
    else:
        print(Fore.RED + "✗ Configuration is incomplete. Please set missing API keys." + Style.RESET_ALL)
        print(Fore.YELLOW + "Copy .env.example to .env and fill in your API keys." + Style.RESET_ALL)
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF

chmod +x validate_config.py

echo ""
echo "✓ Setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To validate your configuration, run:"
echo "  python validate_config.py"
echo ""