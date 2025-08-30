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
parent_dir = Path(__file__).resolve().parent.parent
env_path = parent_dir / '.env'
load_dotenv(env_path, override=True)

# Debug: Print loaded values
if os.getenv("DEBUG") == "true":
    print(f"Loaded from: {env_path}")
    print(f"OPENROUTER_API_KEY: {os.getenv('OPENROUTER_API_KEY')[:20] if os.getenv('OPENROUTER_API_KEY') else 'None'}")
    print(f"IMGBB_API_KEY: {os.getenv('IMGBB_API_KEY')}")

def check_api_key(name, required=True):
    """Check if an API key is configured."""
    value = os.getenv(name)
    # Check for various placeholder patterns
    placeholders = [
        f"your_{name.lower()}_here",
        "YOUR_FREE_API_KEY_HERE",
        "your_key_here"
    ]
    
    # Special handling for IMGBB demo key
    if name == "IMGBB_API_KEY" and value == "demo_key":
        return ("⚠", Fore.YELLOW + "Demo key (get real key from imgbb.com)" + Style.RESET_ALL)
    
    if value and value not in placeholders and len(value) > 10:
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
        ("IMGBB_API_KEY", "ImageBB (Image hosting)"),
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
    # Special handling for IMGBB demo key
    all_valid = all(
        os.getenv(key) and os.getenv(key) not in [
            f"your_{key.lower()}_here",
            "YOUR_FREE_API_KEY_HERE",
            "your_key_here"
        ] and (key != "IMGBB_API_KEY" or os.getenv(key) != "demo_key")
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
