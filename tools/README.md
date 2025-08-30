# ImageFox Tools

This directory contains utility scripts for the ImageFox project.

## Setup
Run `bash setup.sh` to set up the virtual environment and install dependencies.

## Available Tools

### Testing & Validation
- `validate_config.py` - Validate environment configuration
- `test_apify.py` - Test Apify API connectivity (to be created)
- `test_openrouter.py` - Test OpenRouter API (to be created)
- `test_imagebb.py` - Test ImageBB upload (to be created)

### Project Management
- `create_linear_project.py` - Create Linear project for ImageFox
- `manage_linear_subscribers.py` - Manage Linear issue subscribers
- `link_issues_to_project.py` - Link Linear issues to a project

## Usage

### General Usage
```bash
# Activate virtual environment
source venv/bin/activate

# Run a tool
python <tool_name>.py
```

### Linear Subscriber Management
```bash
# Add subscriber to all ImageFox project issues
./venv/bin/python manage_linear_subscribers.py add \
  --project-id a84c6a45-1304-45d5-8d46-d9c926248ec1 \
  --user sbulaev

# Remove subscriber from issues
./venv/bin/python manage_linear_subscribers.py remove \
  --project-id a84c6a45-1304-45d5-8d46-d9c926248ec1 \
  --user sbulaev

# List known users
./venv/bin/python manage_linear_subscribers.py add --list-users

# Use email or direct user ID
./venv/bin/python manage_linear_subscribers.py add \
  --project-id PROJECT_ID \
  --user user@example.com
```

### Link Issues to Project
```bash
# Link specific issues to a project
./venv/bin/python link_issues_to_project.py \
  --team-id a168f90b-ba6c-41d9-87ed-4db05ba428a7 \
  --project-id a84c6a45-1304-45d5-8d46-d9c926248ec1 \
  --issues SER-33 SER-34 SER-35

# Link a range of issues
./venv/bin/python link_issues_to_project.py \
  --team-id a168f90b-ba6c-41d9-87ed-4db05ba428a7 \
  --project-id a84c6a45-1304-45d5-8d46-d9c926248ec1 \
  --range "SER-33:SER-50"
```

## Adding New Tools
1. Create your tool script in this directory
2. Add any new dependencies to requirements.txt
3. Use python-dotenv to load the parent .env file
4. Document your tool in this README
