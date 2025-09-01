# ImageFox - AI-Powered Image Search & Selection

## 🎯 Project Status: Methodology Validated ✅

ImageFox is an intelligent image search and selection system that proves different analytical approaches to the same content produce different image search results. Part of the Co.Actor Scale content generation system.

## Features
- **Smart Image Search**: Uses Apify's Google Images API for comprehensive image discovery
- **AI Vision Analysis**: Leverages multiple vision LLMs through OpenRouter for image understanding
- **Intelligent Selection**: AI-driven decision making to select the most appropriate images
- **Cloud Storage**: Automatic upload to ImageBB for hosting and Airtable for metadata
- **Batch Processing**: Efficient handling of multiple search requests
- **Error Monitoring**: Integrated Sentry for production monitoring

## Architecture
ImageFox operates as a sub-agent within the Co.Actor Scale ecosystem:
- **Storyteller**: Generates content and sends image requests to ImageFox
- **ImageFox**: Processes image search requests and returns selected images
- **Scheduler**: Publishes content with the selected images

## Installation

### Prerequisites
- Python 3.8 or higher
- Virtual environment (recommended)
- API keys for required services

### Setup
1. Clone the repository:
```bash
git clone [repository-url]
cd imagefox
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Configuration

### Required API Keys
- `APIFY_API_KEY`: For Google Images search
- `OPENROUTER_API_KEY`: For LLM vision analysis
- `AIRTABLE_API_KEY`: For metadata storage
- `IMAGEBB_API_KEY`: For image hosting
- `SENTRY_DSN`: For error monitoring

### Optional Configuration
- `MAX_WORKERS`: Parallel processing workers (default: 3)
- `REQUEST_TIMEOUT`: API timeout in seconds (default: 30)
- `RETRY_ATTEMPTS`: Number of retry attempts (default: 3)

## Usage

### Basic Image Search
```python
from imagefox import ImageFox

fox = ImageFox()
results = fox.search_and_select(
    query="beautiful sunset landscape",
    limit=10,
    selection_criteria={
        "quality": "high",
        "relevance": "strict",
        "style": "photographic"
    }
)
```

### API Endpoint
```python
# POST /search
{
    "query": "search prompt",
    "limit": 20,
    "vision_model": "gpt-4-vision-preview",
    "selection_count": 3,
    "criteria": {
        "min_width": 800,
        "min_height": 600,
        "safe_search": true
    }
}
```

### Command Line Interface
```bash
# Search and select images
python imagefox.py --query "nature landscape" --limit 20 --select 3

# Batch processing
python imagefox.py --batch requests.json --output results.json
```

## Development

### Project Structure
```
imagefox/
├── imagefox.py           # Main orchestration module
├── apify_client.py       # Apify API integration
├── vision_analyzer.py    # Computer vision LLM integration
├── image_selector.py     # AI selection logic
├── image_processor.py    # Image download and processing
├── airtable_uploader.py  # Airtable integration
├── imagebb_uploader.py   # ImageBB integration
├── openrouter_client.py  # OpenRouter API client
├── sentry_integration.py # Error monitoring
├── tools/               # Utility scripts
├── tests/              # Test suite
├── docs/               # Documentation
├── requirements.txt    # Dependencies
└── .env.example       # Environment template
```

### Testing
```bash
# Run all tests
pytest -xvs tests/

# Run specific test
pytest tests/test_vision_analyzer.py

# Run with coverage
pytest --cov=. tests/
```

### Code Quality
```bash
# Linting
python -m pylint *.py

# Type checking
mypy --ignore-missing-imports *.py
```

## API Documentation

### Search Endpoint
- **URL**: `/api/search`
- **Method**: `POST`
- **Body**: Search parameters and criteria
- **Response**: Selected images with metadata

### Analysis Endpoint
- **URL**: `/api/analyze`
- **Method**: `POST`
- **Body**: Image URL or base64 data
- **Response**: Vision analysis results

### Selection Endpoint
- **URL**: `/api/select`
- **Method**: `POST`
- **Body**: Candidate images with analysis
- **Response**: Selected best images

## Integration with Co.Actor Scale

### Storyteller Integration
ImageFox receives image requests from Storyteller through:
- Direct API calls
- Message queue (future)
- Webhook notifications

### Scheduler Integration
Selected images are passed to Scheduler for:
- Content publishing
- Social media posts
- Website updates

## Error Handling
- Comprehensive error catching and reporting
- Automatic retries for transient failures
- Fallback to alternative vision models
- Detailed Sentry error tracking

## Performance
- Concurrent image processing
- Result caching to minimize API calls
- Efficient batch processing
- Rate limit respect for all APIs

## Contributing
Please read CLAUDE.md for development guidelines and TOOLS.md for available utilities.

## License
Part of Co.Actor Scale system - proprietary software.

## Support
For issues and questions, create a Linear issue in the Co.Actor Scale (ImageFox) project.