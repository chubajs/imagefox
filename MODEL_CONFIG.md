# ImageFox Model Configuration

## Current Configuration

### Vision Analysis Model
- **Model**: `google/gemini-2.0-flash-lite-001`
- **Purpose**: Primary image analysis
- **Pricing**: 
  - Input: $0.075 per 1M tokens
  - Output: $0.30 per 1M tokens
- **Context**: 1,048,576 tokens
- **Provider**: OpenRouter

### Selection Model
- **Model**: `anthropic/claude-sonnet-4`
- **Purpose**: Intelligent image selection with explanations
- **Pricing**: 
  - Input: $3.00 per 1M tokens
  - Output: $15.00 per 1M tokens
  - Images: $4.80 per 1K images
- **Context**: 1,000,000 tokens (1M)
- **Provider**: OpenRouter

### Token Usage Tracking

OpenRouter returns usage information in responses:
```json
{
  "usage": {
    "prompt_tokens": 194,
    "completion_tokens": 2,
    "total_tokens": 196,
    "cost": 0.0000388  // Actual cost in USD
  }
}
```

### Cost Calculation Example

For a typical image analysis:
- Input tokens: ~1,000 (image + prompt)
- Output tokens: ~500 (analysis response)
- Cost with Gemini 2.0 Flash Lite:
  - Input: 1,000 / 1,000,000 * $0.075 = $0.000075
  - Output: 500 / 1,000,000 * $0.30 = $0.00015
  - **Total: $0.000225 per image**

For selection with Claude Sonnet 4:
- Input tokens: ~5,000 (multiple analyses)
- Output tokens: ~1,000 (selection reasoning)
- Cost calculation:
  - Input: 5,000 / 1,000,000 * $3.00 = $0.015
  - Output: 1,000 / 1,000,000 * $15.00 = $0.015
  - **Total: $0.030**

**Total cost per search with 5 images analyzed and 1 selected: ~$0.031**
- Image analysis: 5 * $0.000225 = $0.001125
- Selection: $0.030
- Total: ~$0.031

## Implementation Details

1. **VisionAnalyzer** (`vision_analyzer.py`):
   - Primary model: `google/gemini-2.0-flash-lite-001`
   - Fallback models: `anthropic/claude-sonnet-4`, `anthropic/claude-3-haiku`

2. **ImageSelector** (`image_selector.py`):
   - Uses `select_with_ai_reasoning()` method
   - Model: `anthropic/claude-sonnet-4`
   - Returns structured JSON with selection explanations

3. **OpenRouterClient** (`openrouter_client.py`):
   - Handles all model API calls
   - Tracks token usage and costs
   - Supports both streaming and non-streaming responses

## API Keys Required
- `OPENROUTER_API_KEY`: Access to all vision and language models
- `APIFY_API_KEY`: Google Images search