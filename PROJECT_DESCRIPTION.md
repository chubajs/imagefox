# ImageFox Project Description

## Executive Summary
ImageFox is an intelligent image search and selection agent designed as a critical component of the Co.Actor Scale content generation ecosystem. It bridges the gap between text-based content generation (Storyteller) and visual content needs, providing smart, context-aware image selection for automated content publishing.

## Problem Statement
Content generation systems often struggle with:
- Finding relevant, high-quality images that match content context
- Analyzing and selecting the most appropriate images from search results
- Ensuring image rights and quality standards
- Integrating visual content seamlessly with text content
- Managing image storage and distribution

## Solution Architecture

### Core Capabilities
1. **Intelligent Search**
   - Receives natural language image prompts
   - Translates prompts into optimized search queries
   - Leverages Apify's Google Images API for comprehensive results
   - Implements smart filtering and safe search

2. **AI-Powered Analysis**
   - Uses multiple computer vision LLMs via OpenRouter
   - Analyzes image composition, quality, and relevance
   - Extracts metadata: dimensions, colors, objects, scenes
   - Generates detailed image descriptions

3. **Smart Selection**
   - AI-driven decision making for best image selection
   - Considers multiple criteria: relevance, quality, composition
   - Ranks candidates based on weighted scoring
   - Supports batch selection for multiple options

4. **Storage & Distribution**
   - Automatic upload to ImageBB for CDN hosting
   - Metadata storage in Airtable for tracking
   - Integration with content management systems
   - URL generation for direct embedding

## Technical Implementation

### Technology Stack
- **Language**: Python 3.8+
- **Search API**: Apify (Google Images crawler)
- **Vision AI**: OpenRouter (GPT-4 Vision, Claude 3, Gemini Pro)
- **Image Hosting**: ImageBB API
- **Data Storage**: Airtable
- **Error Monitoring**: Sentry
- **Testing**: Pytest
- **Async Processing**: aiohttp

### Key Components
1. **Search Module** (`apify_client.py`)
   - Manages Apify API interactions
   - Implements rate limiting and retries
   - Handles pagination and result parsing

2. **Vision Analyzer** (`vision_analyzer.py`)
   - Interfaces with OpenRouter API
   - Supports multiple vision models
   - Implements fallback chains
   - Structures analysis outputs

3. **Selection Engine** (`image_selector.py`)
   - AI-powered selection algorithm
   - Multi-criteria decision making
   - Customizable selection parameters
   - Ranking and scoring system

4. **Storage Manager** (`storage_manager.py`)
   - ImageBB upload handling
   - Airtable metadata sync
   - URL management
   - Cleanup utilities

## Integration Points

### Input Sources
- **Storyteller Agent**: Direct API calls with content context
- **Manual Requests**: CLI and web interface
- **Batch Processing**: JSON file inputs
- **Webhook Triggers**: External system integrations

### Output Destinations
- **Scheduler Agent**: For content publishing
- **Airtable Database**: Metadata and analytics
- **ImageBB CDN**: Public image hosting
- **API Responses**: Direct integration

## Use Cases

### Primary Use Cases
1. **Blog Post Illustration**
   - Find relevant images for articles
   - Select hero images and supporting visuals
   - Ensure thematic consistency

2. **Social Media Content**
   - Select engaging images for posts
   - Optimize for platform requirements
   - Maintain brand consistency

3. **Product Descriptions**
   - Find product-related images
   - Select high-quality visuals
   - Support multiple angles/views

4. **News Content**
   - Find relevant news images
   - Verify image appropriateness
   - Ensure editorial standards

### Advanced Features
- **Style Matching**: Select images matching specific visual styles
- **Color Harmony**: Choose images with compatible color palettes
- **Composition Analysis**: Evaluate rule of thirds, focal points
- **Text Overlay Suitability**: Assess areas for text placement

## Performance Metrics

### Key Performance Indicators
- **Search Accuracy**: Relevance of returned images (target: >80%)
- **Selection Quality**: Human agreement with AI selection (target: >75%)
- **Processing Speed**: Average time per request (target: <5 seconds)
- **API Efficiency**: Minimize API calls through caching
- **Error Rate**: System reliability (target: <1% error rate)

### Scalability
- Concurrent request handling (3-10 workers)
- Request queuing for high loads
- Result caching (1-24 hour TTL)
- Rate limit management across APIs

## Development Roadmap

### Phase 1: Core Functionality (Current)
- Basic search integration ✓
- Vision model integration ✓
- Simple selection algorithm ✓
- Storage implementation ✓

### Phase 2: Enhanced Intelligence
- Advanced selection criteria
- Multi-model ensemble analysis
- Context-aware search optimization
- Quality scoring algorithms

### Phase 3: Advanced Features
- Video frame extraction
- GIF search and analysis
- SVG and vector image support
- Custom training for selection

### Phase 4: Enterprise Features
- Rights management integration
- Brand safety checks
- Custom model fine-tuning
- Analytics dashboard

## Security & Compliance

### Data Security
- API key encryption
- Secure image transmission
- Access control for storage
- Audit logging

### Content Safety
- Safe search enforcement
- NSFW content detection
- Copyright awareness
- Brand safety filters

## Monitoring & Maintenance

### Error Tracking
- Sentry integration for real-time alerts
- Detailed error context capture
- Performance monitoring
- API health checks

### Logging
- Structured logging for debugging
- Request/response tracking
- Performance metrics
- Usage analytics

## Team & Resources

### Development Team
- Part of Co.Actor Scale ecosystem
- Managed in Linear (Team: Serge & Agents)
- Integrated with Storyteller and Scheduler teams

### Documentation
- CLAUDE.md: Development guidelines
- TOOLS.md: Utility documentation
- README.md: User documentation
- API docs: Inline and external

## Success Criteria
1. Seamless integration with Co.Actor Scale
2. High-quality image selection accuracy
3. Robust error handling and recovery
4. Scalable architecture for growth
5. Comprehensive monitoring and analytics

## Conclusion
ImageFox represents a critical evolution in the Co.Actor Scale ecosystem, bringing intelligent visual content selection to automated content generation. By combining advanced AI vision capabilities with smart selection algorithms, ImageFox ensures that generated content is not only textually relevant but also visually compelling.