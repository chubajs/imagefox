# ImageFox Tools Documentation

## Overview
This document provides detailed information about the tools and utilities available in the ImageFox project.

## Core Tools

### 1. Image Search Tool (`tools/search_images.py`)
Searches for images using Apify's Google Images crawler.

**Usage:**
```bash
python tools/search_images.py --query "search term" --limit 50
```

**Parameters:**
- `--query`: Search query string (required)
- `--limit`: Maximum number of results (default: 20)
- `--safe-search`: Enable safe search filter (default: true)
- `--output`: Output format (json/csv, default: json)

**Example:**
```python
from tools.search_images import search_google_images

results = search_google_images(
    query="nature landscape",
    limit=30,
    safe_search=True
)
```

### 2. Vision Analysis Tool (`tools/analyze_image.py`)
Analyzes images using computer vision LLMs via OpenRouter.

**Usage:**
```bash
python tools/analyze_image.py --image-path /path/to/image.jpg --model gpt-4-vision
```

**Parameters:**
- `--image-path`: Path to image file (required)
- `--model`: Vision model to use (default: gpt-4-vision-preview)
- `--prompt`: Custom analysis prompt (optional)
- `--output-format`: Response format (json/text, default: json)

**Supported Models:**
- `openai/gpt-4-vision-preview`
- `anthropic/claude-3-opus`
- `anthropic/claude-3-sonnet`
- `google/gemini-pro-vision`

### 3. Image Selection Tool (`tools/select_best_image.py`)
Selects the best image from candidates using AI decision-making.

**Usage:**
```bash
python tools/select_best_image.py --candidates candidates.json --criteria criteria.json
```

**Parameters:**
- `--candidates`: JSON file with candidate images and analysis
- `--criteria`: Selection criteria configuration
- `--model`: LLM model for selection (default: gpt-4)
- `--top-k`: Number of top images to select (default: 1)

### 4. ImageBB Upload Tool (`tools/upload_to_imagebb.py`)
Uploads images to ImageBB hosting service.

**Usage:**
```bash
python tools/upload_to_imagebb.py --image-path /path/to/image.jpg
```

**Parameters:**
- `--image-path`: Path to image file (required)
- `--name`: Image name (optional)
- `--expiration`: Expiration time in seconds (optional)

**Response:**
```json
{
  "url": "https://i.ibb.co/xxx/image.jpg",
  "delete_url": "https://ibb.co/xxx/delete",
  "id": "xxx"
}
```

### 5. Airtable Integration Tool (`tools/airtable_sync.py`)
Syncs image metadata and analysis results with Airtable.

**Usage:**
```bash
python tools/airtable_sync.py --base-id BASE_ID --table-name Images
```

**Parameters:**
- `--base-id`: Airtable base ID (required)
- `--table-name`: Table name (required)
- `--record-data`: JSON data to sync
- `--update`: Update existing records (default: false)

### 6. Batch Processing Tool (`tools/batch_process.py`)
Processes multiple image search requests in batch.

**Usage:**
```bash
python tools/batch_process.py --input requests.json --output results.json
```

**Parameters:**
- `--input`: Input file with search requests
- `--output`: Output file for results
- `--parallel`: Number of parallel workers (default: 3)
- `--delay`: Delay between requests in seconds (default: 1)

## Utility Scripts

### Setup Script (`tools/setup.sh`)
Initializes the tools environment and installs dependencies.

```bash
cd tools/
bash setup.sh
```

### Test Suite (`tools/test_all.py`)
Runs comprehensive tests for all tools.

```bash
python tools/test_all.py --verbose
```

### Configuration Validator (`tools/validate_config.py`)
Validates environment configuration and API keys.

```bash
python tools/validate_config.py
```

## API Testing Tools

### Apify API Test (`tools/test_apify.py`)
Tests Apify API connectivity and search functionality.

```bash
python tools/test_apify.py --test-query "test search"
```

### OpenRouter API Test (`tools/test_openrouter.py`)
Tests OpenRouter API and vision model availability.

```bash
python tools/test_openrouter.py --list-models
```

### ImageBB API Test (`tools/test_imagebb.py`)
Tests ImageBB upload functionality.

```bash
python tools/test_imagebb.py --test-image sample.jpg
```

## Linear Integration Tools

### Create ImageFox Project (`tools/create_linear_project.py`)
Creates a Linear project for ImageFox development.

```bash
python tools/create_linear_project.py --team-id TEAM_ID
```

### Create Issue (`tools/create_issue.py`)
Creates a new issue in the ImageFox Linear project.

```bash
python tools/create_issue.py --title "Issue Title" --description "Description"
```

### Update Issue (`tools/update_issue.py`)
Updates an existing Linear issue.

```bash
python tools/update_issue.py --issue-id ISSUE_ID --status "In Progress"
```

## Development Tools

### Code Quality Check (`tools/check_quality.py`)
Runs linting and type checking on the codebase.

```bash
python tools/check_quality.py
```

### Performance Profiler (`tools/profile_performance.py`)
Profiles the performance of image processing pipeline.

```bash
python tools/profile_performance.py --sample-size 10
```

### Memory Usage Monitor (`tools/monitor_memory.py`)
Monitors memory usage during image processing.

```bash
python tools/monitor_memory.py --duration 60
```

## Environment Setup

### Required Environment Variables
Create a `.env` file in the project root with:

```bash
# API Keys
APIFY_API_KEY=your_apify_key
OPENROUTER_API_KEY=your_openrouter_key
AIRTABLE_API_KEY=your_airtable_key
IMAGEBB_API_KEY=your_imagebb_key

# Sentry Configuration
SENTRY_DSN=your_sentry_dsn

# Linear Configuration
LINEAR_API_KEY=your_linear_key

# Optional Configuration
MAX_WORKERS=3
REQUEST_TIMEOUT=30
RETRY_ATTEMPTS=3
CACHE_TTL=3600
```

### Virtual Environment Setup
```bash
# Create virtual environment
cd tools/
python -m venv venv

# Activate environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Error Handling

All tools implement comprehensive error handling:
- API errors are caught and reported to Sentry
- Retry logic for transient failures
- Detailed error messages for debugging
- Graceful fallbacks where appropriate

## Rate Limiting

Tools respect API rate limits:
- Apify: 100 requests per minute
- OpenRouter: Varies by model
- ImageBB: 32 MB max file size
- Airtable: 5 requests per second

## Caching

Results are cached to minimize API calls:
- Search results: 1 hour TTL
- Vision analysis: 24 hour TTL
- Image metadata: 7 day TTL

## Logging

All tools use structured logging:
- Info level: Normal operations
- Warning level: Rate limits, retries
- Error level: Failures requiring attention
- Debug level: Detailed troubleshooting

## Testing

Each tool has corresponding tests:
```bash
# Run all tests
pytest tests/

# Run specific tool test
pytest tests/test_search_images.py

# Run with coverage
pytest --cov=tools tests/
```

## Contributing

When adding new tools:
1. Create tool in `tools/` directory
2. Add tests in `tests/`
3. Update this documentation
4. Add dependencies to `tools/requirements.txt`
5. Include error handling and logging
6. Follow project coding standards