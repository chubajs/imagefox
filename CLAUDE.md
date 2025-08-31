# ImageFox Development Guidelines

## 🎯 PRIORITY RULE
**MANDATORY**: Always work on HIGH PRIORITY (priority 1) Linear issues first. Complete ALL priority 1 issues before moving to priority 2, then complete ALL priority 2 before priority 3, etc. Check issue priorities using MCP Linear tools and focus on the highest priority issues available.

## Project Overview
ImageFox is an intelligent image search and selection agent that is part of the Co.Actor Scale content generation system. It receives search prompts, performs Google image searches via Apify, analyzes images using computer vision LLMs, and selects the best candidates using AI decision-making.

## Tools Directory

### Organization
All utility scripts and tools should be placed in the `tools/` directory with its own virtual environment.

### Setup
```bash
cd tools/
bash setup.sh  # Sets up virtual environment and installs dependencies
```

### Running Tools
```bash
# With activated environment
cd tools/
source venv/bin/activate
python <tool_name>.py

# Without activating environment
tools/venv/bin/python tools/<tool_name>.py
```

### Creating New Tools
1. Create the tool script in `tools/` directory
2. Add dependencies to `tools/requirements.txt`
3. Use python-dotenv to load parent `.env` file automatically
4. Document the tool in `tools/README.md`
5. Include proper error handling and type hints

## Branching Strategy

### Main Branches
- `main` - Production-ready code. All releases are deployed from this branch.
- `develop` - Integration branch for ongoing development.

### Supporting Branches
- `feature/*` - For new features (e.g., `feature/apify-integration`)
- `bugfix/*` - For bug fixes (e.g., `bugfix/image-download-error`)
- `release/*` - For preparing releases (e.g., `release/v1.0.0`)
- `hotfix/*` - For critical production fixes (e.g., `hotfix/api-timeout-fix`)

### Workflow
1. **Features**:
   - Branch from: `develop`
   - Merge back to: `develop`
   - Naming: `feature/[description]`

2. **Bug Fixes**:
   - Branch from: `develop`
   - Merge back to: `develop`
   - Naming: `bugfix/[issue-id]-[description]`

3. **Releases**:
   - Branch from: `develop`
   - Merge back to: `develop` and `main`
   - Naming: `release/v[major].[minor].[patch]`

4. **Hotfixes**:
   - Branch from: `main`
   - Merge back to: `develop` and `main`
   - Naming: `hotfix/v[major].[minor].[patch+1]`

## Code Guidelines

### Module Size
- Keep modules under 500 lines of code
- Split functionality into logical, focused components
- Create utility modules for reusable functionality

### Error Handling
- **REQUIRED**: No graceful degradation or silent failures
- All dependencies must be explicitly required - no fallbacks
- Functions should either work as expected or fail with explicit errors
- Use comprehensive error handling with Sentry reporting
- Include relevant context in error reports
- Log errors before raising exceptions for better debugging
- Never suppress exceptions that should be handled by the caller
- **FORBIDDEN**: Never use mock data or simulated results - always report actual errors
- **REQUIRED**: When APIs fail, report the exact error instead of creating demonstrations
- **REQUIRED**: If unable to retrieve real data, clearly state the failure and its cause

### Configuration
- Store sensitive values in environment variables
- Use .env files for local development
- Document all configuration options
- Required environment variables:
  - `APIFY_API_KEY` - Apify API authentication
  - `OPENROUTER_API_KEY` - OpenRouter API for LLM access
  - `AIRTABLE_API_KEY` - Airtable API for data storage
  - `IMAGEBB_API_KEY` - ImageBB API for image hosting
  - `SENTRY_DSN` - Sentry error monitoring

### Testing
- **REQUIRED**: Test all changes before committing
- Write unit tests for core functionality
- Include integration tests for API interactions
- Test error handling paths
- Test image analysis pipeline with sample images
- Verify API rate limits and retry mechanisms

## Commands to Run

### Linting
```bash
python -m pylint *.py
```

### Type Checking
```bash
mypy --ignore-missing-imports *.py
```

### Testing
```bash
pytest -xvs tests/
```

### Virtual Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Project Management

### Linear Project Configuration
- **Project Name**: Co.Actor Scale (ImageFox)
- **Project ID**: `a84c6a45-1304-45d5-8d46-d9c926248ec1`
- **Team**: Serge & Agents (ID: `a168f90b-ba6c-41d9-87ed-4db05ba428a7`)
- **URL**: https://linear.app/cccrafts/project/coactor-scale-imagefox-3281a3759d4e
- **Always use this project ID when creating Linear issues related to ImageFox**

### Linear User IDs
- **Claude (assignee)**: `64a87888-93a6-4c13-bdac-d3bec9cc7f5d`
- **Serge Bulaev (sbulaev - subscriber)**: `f6869754-5429-4298-a825-ae506cf4e71e`

### Linear Issue Management Rules

#### Required Status Flow
**MANDATORY**: All issues must follow this exact status progression:
**Backlog** → **Todo** → **In Progress** → **In Review** → **Done**

#### Status Update Requirements
**🚨 CRITICAL RULE**: You MUST update Linear issue status at EVERY workflow transition. Status updates are MANDATORY and NON-NEGOTIABLE. Always use MCP Linear tools to update status.

1. **When creating a Linear issue:**
   - Use MCP Linear tools when available
   - Assign the issue to Claude (use assigneeId: `64a87888-93a6-4c13-bdac-d3bec9cc7f5d`)
   - Add sbulaev as a subscriber for notifications
   - Set appropriate priority (1=urgent, 2=high, 3=medium, 4=low)
   - Set initial status to "Backlog"

2. **Before starting work (Backlog → Todo):**
   - **MANDATORY**: Update issue status to "Todo" using `mcp__linear__linear_update_issue`
   - Add comment confirming issue is ready to start
   - Ensure all requirements are clear and dependencies identified

3. **When starting work (Todo → In Progress):**
   - **MANDATORY**: Update the issue status to "In Progress" using `mcp__linear__linear_update_issue`
   - Add a comment describing what work is being started
   - Confirm assignment to Claude if not already assigned
   
4. **During active development:**
   - Keep status as "In Progress"
   - Add progress comments for significant milestones
   - Update the description with findings or technical details
   - Log any blockers or dependencies discovered
   
5. **When starting testing (In Progress → In Review):**
   - **MANDATORY**: Update status to "In Review" using `mcp__linear__linear_update_issue`
   - Begin comprehensive testing (unit tests, integration tests)
   - Add comment indicating testing phase has begun
   - Document test coverage and results
   
6. **When all testing passes (In Review → Done):**
   - **MANDATORY**: Update status to "Done" using `mcp__linear__linear_update_issue`
   - Add final comment summarizing what was accomplished
   - Include relevant code changes, file paths, and test results
   - Reference commit hashes and GitHub URLs
   - Document final test counts and pass rates
   
7. **If blocked at any stage:**
   - Update status to "Blocked" (temporary state)
   - Add comment explaining the specific blocker
   - Create linked issues for dependencies if needed
   - Tag sbulaev in comments for urgent blockers
   - Return to appropriate status once unblocked

#### State IDs for MCP Linear API
- **Backlog**: `8245f16a-f93c-43db-8b02-a4a2e15b0396`
- **Todo**: `77b631ad-be46-423b-82ad-f65c1e9a4383`
- **In Progress**: `dcb6cfe7-2a40-43b4-b9c3-62fdc8a25de3`
- **In Review**: `0cf826dd-f2e3-4c39-9e80-ba8e1cc2794f`
- **Done**: `ec7fb97d-0b09-4913-89eb-73fdf7cf5f3d`

### Linear Integration
- Use MCP Linear tools for issue management when available
- Use scripts in `tools/` directory for project-level operations
- Link commits to Linear issues using the issue ID (e.g., SER-XXX)
- Include Linear issue IDs in PR descriptions

## Project Structure

### Core Components
- `imagefox.py` - Main orchestration module
- `apify_client.py` - Apify Google Images API client
- `vision_analyzer.py` - Computer vision LLM integration
- `image_selector.py` - AI-based image selection logic
- `image_processor.py` - Image download and processing
- `airtable_uploader.py` - Airtable integration for metadata
- `imagebb_uploader.py` - ImageBB image hosting integration
- `openrouter_client.py` - OpenRouter API client for LLMs
- `sentry_integration.py` - Error monitoring

### Supporting Files
- `execute.sh` - Execution script
- `requirements.txt` - Dependencies
- `.env` - Environment variables (not committed)
- `.env.example` - Example environment configuration
- `CLAUDE.md` - Development guidelines
- `TOOLS.md` - Tool usage documentation
- `README.md` - Project documentation
- `tools/` - Utility scripts and tools

## API Integration Guidelines

### Apify Integration
- Use Apify's Google Images crawler for search
- Implement proper rate limiting and error handling
- Cache search results to minimize API calls
- Handle pagination for large result sets

### OpenRouter LLM Integration
- Support multiple vision models for analysis
- Implement fallback chains for model failures
- Use structured output for consistent responses
- Include model capability registry

### Image Processing
- Download images efficiently with concurrent requests
- Validate image formats and dimensions
- Implement retry logic for failed downloads
- Clean up temporary files after processing

### Storage Integration
- Upload selected images to ImageBB
- Store metadata and analysis results in Airtable
- Link images to their source URLs and search queries
- Maintain audit trail of selection decisions

## Dependencies
- Document all new dependencies in requirements.txt
- Keep third-party dependencies to a minimum
- All dependencies must be available in the virtual environment
- Use `pip freeze > requirements.txt` to update dependencies list
- Core dependencies include:
  - `requests` - HTTP client
  - `python-dotenv` - Environment configuration
  - `sentry-sdk` - Error monitoring
  - `pyairtable` - Airtable API client
  - `Pillow` - Image processing
  - `aiohttp` - Async HTTP client
  - `openai` - OpenRouter API compatibility