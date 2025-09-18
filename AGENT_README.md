# ImageFox Agent - Automatic Google Images Integration

The ImageFox Agent automatically finds and uploads Google images for articles using the ImageFox pipeline. It processes projects with imagefox field configured and finds relevant images based on article content.

## Quick Start

### 1. Configure Project

In the Projects table, add `imagefox` field:
```
OurPost->google_images:2
```

Format: `TableName->field_name:count`

### 2. Enable Agent

In Agents table:
- `name`: "imagefox"  
- `Status`: "on"

### 3. Setup Environment

```bash
# Required in .env file
APIFY_API_KEY=your_apify_key
OPENROUTER_API_KEY=your_openrouter_key
AIRTABLE_API_KEY=your_airtable_key
IMAGEBB_API_KEY=your_imagebb_key
```

### 4. Test and Deploy

```bash
# Test
python test_agent.py

# Setup cron (every 5 minutes)
./setup_cron.sh

# Monitor
tail -f logs/imagefox_agent.log
```

## How It Works

1. **Monitors** projects with `imagefox` field configured
2. **Finds** articles with `Status='In Pipeline'` needing images  
3. **Generates** search queries from article content
4. **Searches** for relevant images using Google Images
5. **Analyzes** images with AI for quality and relevance
6. **Selects** best images using AI decision-making
7. **Uploads** to ImageBB CDN for fast delivery
8. **Stores** images in Airtable attachment fields
9. **Tracks** API costs in records

## Required Fields

**Target Table (e.g., OurPost):**
- `Status`: "In Pipeline" 
- `article`: Article content
- `title`: Article title (optional)
- `google_images`: Attachment field  
- `costs`: Number field
- `errors`: Number field
- `id`: Unique ID field

## Management

```bash
# Manual run
python imagefox_agent.py

# Health check  
./executor.sh health

# View logs
tail -f logs/imagefox_agent.log

# Clean logs
./executor.sh cleanup
```

## Cost Tracking

- Updates `costs` field per record
- Typical cost: $0.003-0.013 per image
- Logs total costs for monitoring

## Error Handling

- Max 3 errors per record before skipping
- Comprehensive logging and retry logic
- Sentry integration for real-time alerts
- Rate limiting and API error handling

## Troubleshooting

1. **No images found**: Check article content quality
2. **Permission errors**: Verify Airtable API access
3. **Upload failures**: Check ImageBB API key/limits  
4. **Agent not running**: Verify status in Agents table

Enable debug mode: `export IMAGEFOX_DEBUG=true`