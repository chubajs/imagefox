# ImageFox API Reference Documentation

## Overview
This document provides comprehensive API specifications for all external services integrated with ImageFox.

## 1. Apify Google Images Scraper API

### Endpoint
```
https://api.apify.com/v2/acts/apify~google-search-scraper/run-sync-get-dataset-items
```

### Authentication
- **Header**: `Authorization: Bearer ${APIFY_API_KEY}`
- **API Key**: Required in environment variable `APIFY_API_KEY`

### Request Configuration

#### POST Request Body
```json
{
  "queries": "search query",
  "maxPagesPerQuery": 1,
  "resultsPerPage": 100,
  "mobileResults": false,
  "languageCode": "en",
  "maxConcurrency": 10,
  "saveHtml": false,
  "saveHtmlToKeyValueStore": false,
  "includeUnfilteredResults": false,
  "customDataFunction": "async ({ input, $, request, response, html }) => { return {} }"
}
```

#### Query Parameters
- `token`: API key (alternative to header auth)
- `timeout`: Request timeout in seconds (60-900)
- `memory`: Memory allocation in MB (128-32768)

### Response Structure
```json
{
  "searchQuery": {
    "term": "search query",
    "page": 1,
    "type": "SEARCH",
    "domain": "google.com",
    "countryCode": "US",
    "locationUule": null,
    "resultsPerPage": "100"
  },
  "url": "https://www.google.com/search?q=...",
  "hasNextPage": false,
  "resultsTotal": 1000000,
  "relatedQueries": [],
  "paidResults": [],
  "paidProducts": [],
  "organicResults": [
    {
      "title": "Image Title",
      "url": "https://source-page-url.com",
      "displayedUrl": "source-page-url.com",
      "description": "Image description",
      "sitelinks": [],
      "productInfo": {},
      "imageUrl": "https://direct-image-url.jpg",
      "thumbnailUrl": "https://thumbnail-url.jpg"
    }
  ]
}
```

### Rate Limits
- Default: 100 requests per minute
- Configurable via `APIFY_RATE_LIMIT` environment variable

### Error Handling
- 401: Invalid API key
- 402: Insufficient credits
- 429: Rate limit exceeded
- 500: Actor execution failed

## 2. OpenRouter Vision API

### Endpoint
```
https://openrouter.ai/api/v1/chat/completions
```

### Authentication
- **Header**: `Authorization: Bearer ${OPENROUTER_API_KEY}`
- **API Key**: Required in environment variable `OPENROUTER_API_KEY`

### Available Vision Models
- `openai/gpt-4-vision-preview` - GPT-4 with vision capabilities
- `anthropic/claude-3-opus` - Claude 3 Opus with vision
- `anthropic/claude-3-sonnet` - Claude 3 Sonnet with vision
- `anthropic/claude-3-haiku` - Claude 3 Haiku with vision
- `google/gemini-pro-vision` - Gemini Pro Vision
- `google/gemini-pro-1.5` - Gemini 1.5 Pro with vision

### Request Format
```json
{
  "model": "openai/gpt-4-vision-preview",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Analyze this image"
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "data:image/jpeg;base64,..." 
          }
        }
      ]
    }
  ],
  "max_tokens": 500,
  "temperature": 0.7,
  "top_p": 1,
  "stream": false
}
```

### Image Input Options
1. **Base64 Encoded**: `data:image/jpeg;base64,{base64_string}`
2. **Direct URL**: `https://image-url.jpg` (must be publicly accessible)

### Response Structure
```json
{
  "id": "gen-xxxxx",
  "model": "openai/gpt-4-vision-preview",
  "object": "chat.completion",
  "created": 1234567890,
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Image analysis response..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 50,
    "total_tokens": 150
  }
}
```

### Rate Limits
- Default: 50 requests per minute
- Configurable via `OPENROUTER_RATE_LIMIT` environment variable
- Token limits vary by model

### Error Codes
- 400: Bad request (invalid model or parameters)
- 401: Invalid API key
- 402: Insufficient credits
- 429: Rate limit exceeded
- 500: Model error

## 3. ImageBB API

### Upload Endpoint
```
https://api.imgbb.com/1/upload
```

### Authentication
- **Parameter**: `key=${IMAGEBB_API_KEY}`
- **API Key**: Required in environment variable `IMAGEBB_API_KEY`

### Upload Methods

#### Method 1: Base64 Upload
```http
POST https://api.imgbb.com/1/upload
Content-Type: application/x-www-form-urlencoded

key=YOUR_API_KEY&image=BASE64_ENCODED_IMAGE_STRING&name=optional_name
```

#### Method 2: Binary Upload
```http
POST https://api.imgbb.com/1/upload
Content-Type: multipart/form-data

key: YOUR_API_KEY
image: [binary image data]
name: optional_name
expiration: 600 (optional, in seconds)
```

#### Method 3: URL Upload
```http
POST https://api.imgbb.com/1/upload
Content-Type: application/x-www-form-urlencoded

key=YOUR_API_KEY&image=https://image-url.jpg
```

### Request Parameters
- `key` (required): API key
- `image` (required): Base64 string, binary file, or image URL
- `name` (optional): Image name (auto-generated if not provided)
- `expiration` (optional): Auto-delete time in seconds (60-15552000)

### Response Structure
```json
{
  "data": {
    "id": "2ndCYJK",
    "title": "image-name",
    "url_viewer": "https://ibb.co/2ndCYJK",
    "url": "https://i.ibb.co/w04Prt6/c1.jpg",
    "display_url": "https://i.ibb.co/98W13PY/c1.jpg",
    "width": "1280",
    "height": "720",
    "size": "122519",
    "time": "1678901234",
    "expiration": "0",
    "image": {
      "filename": "c1.jpg",
      "name": "c1",
      "mime": "image/jpeg",
      "extension": "jpg",
      "url": "https://i.ibb.co/w04Prt6/c1.jpg"
    },
    "thumb": {
      "filename": "c1.jpg",
      "name": "c1",
      "mime": "image/jpeg",
      "extension": "jpg",
      "url": "https://i.ibb.co/2ndCYJK/c1.jpg"
    },
    "medium": {
      "filename": "c1.jpg",
      "name": "c1",
      "mime": "image/jpeg",
      "extension": "jpg",
      "url": "https://i.ibb.co/98W13PY/c1.jpg"
    },
    "delete_url": "https://ibb.co/2ndCYJK/delete-key"
  },
  "success": true,
  "status": 200
}
```

### Limits
- **Free Tier**: 32MB max file size
- **Rate Limit**: 10 uploads per minute (configurable via `IMAGEBB_RATE_LIMIT`)
- **Supported Formats**: JPEG, PNG, GIF, BMP, WEBP, TIFF

### Error Responses
```json
{
  "status_code": 400,
  "error": {
    "message": "Invalid API key",
    "code": 100
  },
  "status_txt": "Bad Request"
}
```

## 4. Airtable API

### Base URL
```
https://api.airtable.com/v0/${AIRTABLE_BASE_ID}
```

### Authentication
- **Header**: `Authorization: Bearer ${AIRTABLE_API_KEY}`
- **API Key**: Required in environment variable `AIRTABLE_API_KEY`

### Python Client (pyairtable)
```python
from pyairtable import Api

api = Api(api_key=AIRTABLE_API_KEY)
table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)
```

### Table Schema (Images)
```python
{
    "search_query": "Text",
    "source_url": "URL",
    "image_url": "URL",
    "thumbnail_url": "URL",
    "hosted_url": "URL",
    "title": "Text",
    "description": "Long text",
    "vision_analysis": "Long text",
    "relevance_score": "Number (0-1)",
    "quality_score": "Number (0-1)",
    "selection_reason": "Long text",
    "selected": "Checkbox",
    "timestamp": "Date and time",
    "model_used": "Single select",
    "processing_time": "Number",
    "tags": "Multiple select",
    "error_log": "Long text"
}
```

### Create Record
```python
# Using pyairtable
record = table.create({
    "search_query": "modern office",
    "source_url": "https://example.com/image.jpg",
    "image_url": "https://i.ibb.co/abc123/image.jpg",
    "vision_analysis": "Office space with modern furniture",
    "relevance_score": 0.95,
    "selected": True,
    "timestamp": "2024-01-01T12:00:00.000Z"
})
```

### Read Records
```python
# Get all records
records = table.all()

# Get with filter
records = table.all(formula="AND({selected}=TRUE(), {relevance_score}>0.8)")

# Get single record
record = table.get(record_id)
```

### Update Record
```python
# Update single field
table.update(record_id, {"selected": True})

# Update multiple fields
table.update(record_id, {
    "relevance_score": 0.98,
    "selection_reason": "High quality and relevance"
})
```

### Batch Operations
```python
# Batch create (max 10 records)
records = table.batch_create([
    {"search_query": "office 1", "image_url": "url1"},
    {"search_query": "office 2", "image_url": "url2"}
])

# Batch update
table.batch_update([
    {"id": "rec1", "fields": {"selected": True}},
    {"id": "rec2", "fields": {"selected": False}}
])
```

### Rate Limits
- **Default**: 5 requests per second
- **Configurable**: via `AIRTABLE_RATE_LIMIT` environment variable
- **Batch limit**: 10 records per request

### Error Handling
```python
from pyairtable.api.types import APIResponse

try:
    record = table.create(data)
except Exception as e:
    # Common errors:
    # 401: Invalid API key
    # 403: Forbidden (check base/table permissions)
    # 404: Base or table not found
    # 422: Invalid request (check field types)
    # 429: Rate limit exceeded
    # 500: Server error
    print(f"Airtable error: {e}")
```

## Error Handling Best Practices

### Retry Strategy
```python
import time
from typing import Optional, Callable, Any

def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0
) -> Any:
    """Retry function with exponential backoff."""
    delay = initial_delay
    
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            # Check if error is retryable
            if hasattr(e, 'response'):
                status_code = e.response.status_code
                if status_code in [429, 500, 502, 503, 504]:
                    time.sleep(delay)
                    delay *= backoff_factor
                else:
                    raise
            else:
                raise
```

### Rate Limiting Implementation
```python
import time
from collections import deque
from threading import Lock

class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, rate: int, per: float = 60.0):
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.time()
        self.lock = Lock()
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        with self.lock:
            current = time.time()
            time_passed = current - self.last_check
            self.last_check = current
            self.allowance += time_passed * (self.rate / self.per)
            
            if self.allowance > self.rate:
                self.allowance = self.rate
            
            if self.allowance < 1.0:
                sleep_time = (1.0 - self.allowance) * (self.per / self.rate)
                time.sleep(sleep_time)
                self.allowance = 0.0
            else:
                self.allowance -= 1.0
```

## Environment Configuration

### Required Environment Variables
```bash
# API Keys
APIFY_API_KEY=your_apify_key
OPENROUTER_API_KEY=your_openrouter_key
AIRTABLE_API_KEY=your_airtable_key
IMAGEBB_API_KEY=your_imagebb_key

# Airtable Configuration
AIRTABLE_BASE_ID=your_base_id
AIRTABLE_TABLE_NAME=Images

# Rate Limits (optional)
APIFY_RATE_LIMIT=100
OPENROUTER_RATE_LIMIT=50
AIRTABLE_RATE_LIMIT=5
IMAGEBB_RATE_LIMIT=10

# Vision Model Configuration (optional)
DEFAULT_VISION_MODEL=openai/gpt-4-vision-preview
FALLBACK_VISION_MODEL=anthropic/claude-3-sonnet
```

## Security Considerations

1. **API Key Storage**: Never commit API keys to version control
2. **Request Validation**: Validate all inputs before sending to APIs
3. **Error Messages**: Don't expose API keys in error messages or logs
4. **HTTPS Only**: Always use HTTPS endpoints
5. **Token Rotation**: Regularly rotate API keys
6. **Rate Limit Headers**: Monitor rate limit headers in responses
7. **Timeout Configuration**: Set appropriate timeouts for all requests

## Testing Recommendations

### Unit Testing
- Mock API responses for consistent testing
- Test error handling for each API
- Verify retry logic with simulated failures
- Test rate limiting behavior

### Integration Testing
- Use test/sandbox environments where available
- Test with real API calls but limited scope
- Verify end-to-end data flow
- Monitor API usage during tests

### Example Test
```python
import pytest
from unittest.mock import patch, MagicMock

def test_apify_search():
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "organicResults": [
                {"imageUrl": "https://test.jpg"}
            ]
        }
        
        # Test your Apify client
        results = apify_client.search("test query")
        assert len(results) == 1
        assert results[0]["imageUrl"] == "https://test.jpg"
```

## Performance Optimization

1. **Concurrent Requests**: Use asyncio for parallel API calls
2. **Caching**: Cache API responses where appropriate
3. **Batch Operations**: Use batch endpoints when available
4. **Connection Pooling**: Reuse HTTP connections
5. **Compression**: Enable gzip compression for large payloads
6. **Selective Fields**: Request only needed fields from APIs

## Monitoring and Logging

### Recommended Metrics
- API response times
- Success/failure rates
- Rate limit utilization
- Error frequencies by type
- Token usage (for LLM APIs)
- Image processing times

### Logging Format
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Log API calls
logger.info(f"Calling {api_name} API", extra={
    "api": api_name,
    "endpoint": endpoint,
    "method": method,
    "params": params_without_keys
})

# Log responses
logger.info(f"{api_name} API response", extra={
    "api": api_name,
    "status_code": response.status_code,
    "duration": response_time,
    "rate_limit_remaining": response.headers.get('X-RateLimit-Remaining')
})
```

## Version History

- **v1.0.0** (2024-01-XX): Initial API documentation
  - Apify Google Images Scraper API v2
  - OpenRouter Vision API v1
  - ImageBB API v1
  - Airtable API v0

## References

- [Apify Documentation](https://docs.apify.com/)
- [OpenRouter API Docs](https://openrouter.ai/docs)
- [ImageBB API Documentation](https://api.imgbb.com/)
- [Airtable API Documentation](https://airtable.com/developers/web/api/introduction)
- [pyairtable Documentation](https://pyairtable.readthedocs.io/)