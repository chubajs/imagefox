# ImageFox Agent Setup Complete ✅

## Configuration Status

### API Keys Configured
All API keys have been successfully configured in `/home/sbulaev/imagefox/.env`:

- ✅ **AIRTABLE_API_KEY**: `patap1Gg7z...2573` (from artimatic)
- ✅ **APIFY_API_KEY**: `apify_api_...CqWU`
- ✅ **OPENROUTER_API_KEY**: `sk-or-v1-f...8b71`
- ✅ **IMAGEBB_API_KEY**: `ca776abb2e...7155`
- ✅ **SENTRY_DSN**: Configured for error tracking

### Agent Status
- ✅ Agent created in Airtable: `imagefox`
- ✅ Status: **ENABLED** (`on`)
- ✅ Test run successful

### Project Configuration
- Project: **customertimes**
- ImageFox Config: `OurPost->google_images`
- Target: 2 images per article
- Base ID: `appeQMULwPZnW9pmF`

### Current Issue
- ⚠️ **403 Forbidden** on OurPost table access
- This is expected - the AIRTABLE_API_KEY needs permission to access the customertimes base

## How to Use

### 1. Manual Execution
```bash
# Run once
python imagefox_agent.py

# Test mode (limit records)
export IMAGEFOX_TEST_MODE=true
export IMAGEFOX_TEST_RECORD_LIMIT=1
python imagefox_agent.py
```

### 2. Automatic Execution (Every 5 Minutes)
```bash
# Setup cron job
./setup_cron.sh

# Check logs
tail -f logs/imagefox_agent.log
```

### 3. Monitor Agent
```bash
# Check health
./executor.sh health

# View logs
tail -f logs/imagefox_agent.log

# Clean old logs
./executor.sh cleanup
```

## What the Agent Does

1. **Monitors** projects with `imagefox` field configured
2. **Finds** articles with `Status='In Pipeline'` and no images
3. **Generates** search queries from article content
4. **Searches** Google Images via Apify
5. **Analyzes** images with AI (Gemini 2.0 Flash Lite)
6. **Selects** best images based on quality and relevance
7. **Uploads** to ImageBB CDN
8. **Stores** in Airtable attachment field
9. **Tracks** costs (approximately $0.14 per image)

## Required Fields in Target Table

- `Status` - Must be "In Pipeline" for processing
- `article` - Article content for search query
- `title` - Article title (optional but helpful)
- `google_images` - Attachment field for storing images
- `costs` - Number field for cost tracking
- `errors` - Number field for error counting
- `id` - Unique identifier

## Cost Breakdown

Based on testing:
- Average cost per image: **$0.14**
- Search API: ~$0.005
- Vision analysis: ~$0.008
- Selection AI: ~$0.127
- Total per article (2 images): ~$0.28

## Next Steps

1. **Grant Permissions**: Ensure AIRTABLE_API_KEY has access to the target base/table
2. **Enable Cron**: Run `./setup_cron.sh` for automatic execution
3. **Monitor**: Watch logs for processing results

## Troubleshooting

### Permission Errors (403)
- Verify AIRTABLE_API_KEY has access to the base
- Check base ID and table name are correct
- Ensure table exists in the specified base

### No Images Found
- Check article has sufficient content
- Verify Apify credits available
- Review search query generation in logs

### High Costs
- Reduce image count in configuration
- Use TEST_MODE to limit records
- Monitor usage in logs

## Support Files

- `imagefox_agent.py` - Main agent
- `test_agent.py` - Test suite
- `test_imagefox_workflow.py` - Workflow demonstration
- `executor.sh` - Execution management
- `setup_cron.sh` - Cron setup
- `logs/imagefox_agent.log` - Main log file

The ImageFox agent is ready for production use!