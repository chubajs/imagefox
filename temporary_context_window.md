# ImageFox Development Context Summary

## Recent Work Completed (SER-41)

### ImageProcessor Module Implementation
- **File**: `image_processor.py` (498 lines) - Complete image processing pipeline
- **Tests**: `tests/test_image_processor.py` (32 test methods)  
- **Status**: ✅ COMPLETED - All 183 tests passing (32 new + 151 existing)

### Key Features Implemented
- **Async Image Downloading**: Concurrent HTTP downloads with aiohttp (configurable concurrent_downloads=5)
- **Image Validation**: Size checks (min 400x300), format validation, max size (10MB) 
- **Metadata Extraction**: Comprehensive analysis with EXIF data, file hashes, processing times
- **Image Optimization**: Smart compression with quality settings, resizing for large images
- **Thumbnail Generation**: Configurable thumbnail creation (default 300x300)
- **Batch Processing**: Concurrent processing of multiple images with semaphore control
- **Error Handling**: Comprehensive error management with Sentry integration
- **Statistics Tracking**: Downloads, processing stats, temp file management
- **Async Context Manager**: Proper resource cleanup with session management

## Architecture Patterns Established

### Core Module Structure (ALL modules follow this pattern)
- **Line Limit**: Under 500 lines per module (strict requirement)
- **Error Handling**: No graceful degradation - explicit failures with Sentry reporting
- **Dataclasses**: Use for structured data (ImageMetadata, ProcessingResult, etc.)
- **Async Support**: aiohttp sessions for HTTP operations, proper async/await patterns
- **Environment Config**: All settings via environment variables with sensible defaults
- **Comprehensive Testing**: 25-32 tests per module with mocking for external dependencies

### Test Patterns
- **pytest + unittest**: Hybrid approach with `@pytest.mark.asyncio` for async tests
- **Mock Strategy**: Mock external APIs, file operations, HTTP requests
- **Coverage**: Test success paths, error conditions, edge cases, configuration
- **Fixtures**: Temporary directories, test images, mock responses

## Linear Workflow (MANDATORY)

### Issue Status Progression
- **Backlog** → **Todo** → **In Progress** → **In Review** → **Done**
- **MUST update Linear status** at each transition using MCP Linear tools
- **Add comments** for major milestones and completion summaries

### Priority Rules (CRITICAL)
- **Priority 1 (Urgent)**: Complete ALL before moving to Priority 2
- **Priority 2 (High)**: Complete ALL before moving to Priority 3
- Work order: Priority 1 → Priority 2 → Priority 3 → Priority 4

### Project Context
- **Project ID**: `a84c6a45-1304-45d5-8d46-d9c926248ec1` (Co.Actor Scale - ImageFox)
- **Team ID**: `a168f90b-ba6c-41d9-87ed-4db05ba428a7` (Serge & Agents)
- **Claude ID**: `64a87888-93a6-4c13-bdac-d3bec9cc7f5d` (assignee for all issues)
- **sbulaev ID**: `f6869754-5429-4298-a825-ae506cf4e71e` (subscriber for notifications)

## API Clients Completed (All Production-Ready)

### 1. ApifyClient (SER-35) ✅ 
- Google Images search via Apify API
- Caching, rate limiting, result parsing
- 17 comprehensive tests

### 2. OpenRouterClient (SER-36) ✅
- Multi-model vision analysis (GPT-4V, Claude 3, Gemini Pro)
- Fallback chains, structured output
- 25 comprehensive tests

### 3. ImageBBUploader (SER-37) ✅ 
- Image hosting and CDN distribution
- Base64/file/URL upload methods
- 29 comprehensive tests

### 4. AirtableUploader (SER-38) ✅
- Metadata storage with schema validation
- Batch operations, rate limiting
- 27 comprehensive tests

### 5. VisionAnalyzer (SER-39) ✅
- Multi-model image analysis coordination
- Consensus building, confidence scoring
- 24 comprehensive tests

### 6. ImageSelector (SER-40) ✅
- AI-powered multi-criteria selection
- Diversity algorithms, scoring strategies
- 29 comprehensive tests

### 7. ImageProcessor (SER-41) ✅ - JUST COMPLETED
- Complete image processing pipeline
- Download, validate, optimize, thumbnail
- 32 comprehensive tests

## Development Environment

### Virtual Environment Setup
```bash
source venv/bin/activate  # ALWAYS use venv
python -m pytest -xvs    # Run all tests
python -m pylint *.py    # Code quality checks
mypy --ignore-missing-imports *.py  # Type checking
```

### Key Dependencies
- `aiohttp` - Async HTTP client
- `requests` - HTTP client fallback  
- `Pillow` - Image processing
- `python-dotenv` - Environment config
- `sentry-sdk` - Error monitoring
- `pyairtable` - Airtable API
- `pytest` + `pytest-asyncio` - Testing

## Environment Variables Required
```bash
APIFY_API_KEY=xxx                    # Apify Google Images API
OPENROUTER_API_KEY=xxx              # OpenRouter LLM API  
IMAGEBB_API_KEY=xxx                 # ImageBB hosting API
AIRTABLE_API_KEY=xxx                # Airtable data storage
SENTRY_DSN=https://xxx@sentry.cccrafts.ai/16  # Error monitoring
```

## Next Priority Issues (Priority 2)

Based on previous Linear issue creation, the next high-priority items to work on are:

### Core Integration Issues
- **SER-42**: Main ImageFox orchestrator that coordinates all modules
- **SER-43**: Integration testing for complete pipeline
- **SER-44**: Performance optimization and caching strategies

### Critical Rules for Next Session

1. **ALWAYS check Linear issues first** - work by priority order
2. **Update Linear status** at every transition (use MCP Linear tools)
3. **Follow 500-line module limit** strictly
4. **Test-driven development** - write tests during implementation
5. **Use virtual environment** - `source venv/bin/activate`
6. **Run full test suite** after each module completion
7. **Add Linear comments** for milestones and completion summaries

## Git Repository
- **Remote**: `origin git@github.com:chubajs/imagefox.git`
- **Branch Strategy**: Feature branches, merge to develop, then main
- **Commits**: Include Linear issue IDs (e.g., "SER-41: Implement ImageProcessor")

## Current Status
- **183 total tests passing** (100% success rate)
- **7 core modules completed** and production-ready
- **All API integrations working** with comprehensive error handling
- **Ready for main orchestrator implementation** (next priority)
- **Architecture patterns established** and consistently applied

## Important Notes
- **No graceful degradation** - all errors must be explicit and reported
- **Sentry integration** is mandatory for all modules
- **Async/await patterns** for all I/O operations
- **Comprehensive logging** with proper error context
- **Environment-based configuration** with sensible defaults