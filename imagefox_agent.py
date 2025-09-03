#!/usr/bin/env python3
"""
ImageFox Agent - Automated Google Images Integration

This agent automatically finds and uploads Google images for articles using
the ImageFox pipeline. It processes projects with imagefox field configured
and finds relevant images based on article content.
"""

import os
import sys
import time
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add parent directory to path for ImageFox imports
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from pyairtable import Table
import sentry_sdk
from sentry_sdk import capture_exception

# Import ImageFox components
from imagefox import ImageFox, SearchRequest, ImageResult, WorkflowResult

# Load environment variables
load_dotenv()

# Configuration
AGENT_NAME = "imagefox"
DEBUG = os.getenv('IMAGEFOX_DEBUG', 'false').lower() == 'true'
MAX_ERRORS = 3
DEFAULT_IMAGE_COUNT = 2
TEST_MODE = os.getenv('IMAGEFOX_TEST_MODE', 'false').lower() == 'true'
TEST_RECORD_LIMIT = int(os.getenv('IMAGEFOX_TEST_RECORD_LIMIT', '2'))

# Airtable configuration
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
PROJECTS_BASE = "appAC30YhZkEbjjWK"

if not AIRTABLE_API_KEY:
    raise ValueError("AIRTABLE_API_KEY not found in environment variables")

# Initialize Airtable tables
projects_table = Table(AIRTABLE_API_KEY, PROJECTS_BASE, "Projects")
agents_table = Table(AIRTABLE_API_KEY, PROJECTS_BASE, "Agents")

# Setup logging
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    filename=log_dir / "imagefox_agent.log",
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s: %(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)

# Initialize Sentry if DSN is available
sentry_dsn = os.getenv('SENTRY_DSN')
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        traces_sample_rate=1.0,
        environment='production' if not DEBUG else 'development'
    )

logger.info("Starting ImageFox Agent")
if TEST_MODE:
    logger.info(f"TEST MODE ENABLED: Will process max {TEST_RECORD_LIMIT} records per project")


def check_agent_status() -> bool:
    """Check if the ImageFox agent is enabled."""
    try:
        agents = agents_table.all(formula=f"AND({{Name}}='{AGENT_NAME}')")
        if not agents:
            logger.info(f"No agent found with name {AGENT_NAME}. Skipping.")
            return False
        
        agent = agents[0]
        status = agent["fields"].get("Status", "off")
        
        if status not in ["on", "execute"]:
            logger.info(f"Agent {AGENT_NAME} is {status}. Skipping.")
            return False
        
        logger.info(f"Agent {AGENT_NAME} is {status}. Proceeding.")
        return True
        
    except Exception as e:
        logger.error(f"Error checking agent status: {e}")
        capture_exception(e)
        return False


def parse_imagefox_config(imagefox_field: str) -> Dict[str, Any]:
    """
    Parse the imagefox field configuration.
    
    Expected formats:
    - "TableName->source_field->target_field:count" (e.g., "News->content->google_images:2")
    - "TableName->target_field:count" (e.g., "News->photo:2") - will auto-detect source field
    
    Args:
        imagefox_field: The imagefox field value from projects table
        
    Returns:
        Dictionary with table_name, source_field, target_field, and image_count
    """
    try:
        if '->' not in imagefox_field:
            raise ValueError(f"Invalid imagefox format: {imagefox_field}")
        
        parts = imagefox_field.split('->')
        
        if len(parts) == 3:
            # Format: TableName->source_field->target_field:count
            table_name = parts[0].strip()
            source_field = parts[1].strip()
            target_spec = parts[2].strip()
            
            # Extract target field and count
            if ':' in target_spec:
                target_field, count_str = target_spec.split(':', 1)
                try:
                    image_count = int(count_str.strip())
                except ValueError:
                    logger.warning(f"Invalid image count '{count_str}', using default {DEFAULT_IMAGE_COUNT}")
                    image_count = DEFAULT_IMAGE_COUNT
            else:
                target_field = target_spec
                image_count = DEFAULT_IMAGE_COUNT
                
        elif len(parts) == 2:
            # Format: TableName->target_field:count (auto-detect source)
            table_name = parts[0].strip()
            source_field = None  # Will be auto-detected
            field_spec = parts[1].strip()
            
            # Check if count is specified
            if ':' in field_spec:
                target_field, count_str = field_spec.split(':', 1)
                try:
                    image_count = int(count_str.strip())
                except ValueError:
                    logger.warning(f"Invalid image count '{count_str}', using default {DEFAULT_IMAGE_COUNT}")
                    image_count = DEFAULT_IMAGE_COUNT
            else:
                target_field = field_spec
                image_count = DEFAULT_IMAGE_COUNT
        else:
            raise ValueError(f"Invalid imagefox format: {imagefox_field}")
        
        return {
            'table_name': table_name,
            'source_field': source_field,  # None means auto-detect
            'target_field': target_field,
            'field_name': target_field,  # Keep for backward compatibility
            'image_count': image_count
        }
        
    except Exception as e:
        logger.error(f"Error parsing imagefox config '{imagefox_field}': {e}")
        return None


def generate_search_query(article_content: str, title: str = "") -> str:
    """
    Generate a search query from article content.
    
    Args:
        article_content: The article content
        title: Optional article title
        
    Returns:
        Search query string
    """
    # For now, use a simple approach - extract key words from title and beginning of article
    query_parts = []
    
    if title:
        query_parts.append(title)
    
    # Take first 200 characters of article for context
    if article_content:
        content_preview = article_content[:200].strip()
        # Remove common stop words and punctuation for cleaner search
        import re
        content_preview = re.sub(r'[^\w\s]', ' ', content_preview)
        words = content_preview.split()
        
        # Take first few meaningful words (skip very short ones)
        meaningful_words = [w for w in words[:10] if len(w) > 3]
        if meaningful_words:
            query_parts.extend(meaningful_words[:5])  # Limit to avoid too long queries
    
    query = ' '.join(query_parts)
    
    # Ensure query isn't too long for Google Images
    if len(query) > 100:
        query = query[:100]
    
    logger.debug(f"Generated search query: '{query}'")
    return query


def calculate_processing_cost(workflow_result: WorkflowResult) -> float:
    """Calculate the processing cost from workflow result."""
    return workflow_result.total_cost


def update_record_cost(table: Table, record_id: str, cost: float):
    """Update the cost field in a record."""
    try:
        # Get current cost if it exists
        record = table.all(formula=f"{{id}} = {record_id}")
        if not record:
            logger.warning(f"Record {record_id} not found for cost update")
            return
        
        current_cost = record[0]["fields"].get("costs", 0.0)
        new_cost = current_cost + cost
        
        table.update(record[0]["id"], {"costs": new_cost}, typecast=True)
        logger.info(f"Updated costs for record {record_id}: ${current_cost:.6f} + ${cost:.6f} = ${new_cost:.6f}")
        
    except Exception as e:
        logger.error(f"Failed to update costs for record {record_id}: {e}")


def add_images_to_record(table: Table, record_id: str, field_name: str, image_urls: List[str]) -> bool:
    """
    Add image URLs to an attachment field in a record.
    
    Args:
        table: Airtable table instance
        record_id: The record ID to update
        field_name: The attachment field name
        image_urls: List of image URLs to add
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get the current record
        record = table.all(formula=f"{{id}} = {record_id}")
        if not record:
            logger.error(f"Record {record_id} not found in table")
            return False
        
        record = record[0]
        
        # Prepare image attachments
        new_attachments = [{"url": url} for url in image_urls]
        
        # Check if field already has attachments
        if field_name in record["fields"]:
            existing_attachments = record["fields"][field_name]
            if isinstance(existing_attachments, list):
                # Add to existing attachments
                all_attachments = existing_attachments + new_attachments
            else:
                all_attachments = new_attachments
        else:
            all_attachments = new_attachments
        
        # Update the record
        table.update(record["id"], {field_name: all_attachments}, typecast=True)
        logger.info(f"Added {len(image_urls)} images to record {record_id} field '{field_name}'")
        return True
        
    except Exception as e:
        logger.error(f"Failed to add images to record {record_id}: {e}")
        capture_exception(e)
        return False


def increment_error_count(table: Table, record_id: str):
    """Increment error count for a record if the field exists."""
    try:
        record = table.all(formula=f"{{id}} = {record_id}")
        if not record:
            return
        
        # Check if the errors field exists in the record
        if "errors" in record[0]["fields"] or any("error" in k.lower() for k in record[0]["fields"].keys()):
            current_errors = record[0]["fields"].get("errors", 0)
            new_errors = current_errors + 1
            
            table.update(record[0]["id"], {"errors": new_errors}, typecast=True)
            logger.info(f"Incremented errors for record {record_id}: {current_errors} -> {new_errors}")
        else:
            logger.debug(f"No errors field in table, skipping error count for record {record_id}")
        
    except Exception as e:
        logger.warning(f"Could not increment error count for record {record_id}: {e}")


async def process_project(project: Dict[str, Any], imagefox: ImageFox) -> Dict[str, Any]:
    """
    Process a single project for ImageFox integration.
    
    Args:
        project: Project record from Airtable
        imagefox: ImageFox instance
        
    Returns:
        Dictionary with processing statistics
    """
    project_name = project["fields"]["project"]
    logger.info(f"Processing project: {project_name}")
    
    stats = {
        'project_name': project_name,
        'records_processed': 0,
        'images_added': 0,
        'total_cost': 0.0,
        'errors': 0
    }
    
    try:
        # Parse imagefox configuration(s) - can be comma-delimited
        imagefox_config_str = project["fields"].get("imagefox", "")
        if not imagefox_config_str:
            logger.info(f"No imagefox configuration for project {project_name}")
            return stats
        
        # Split by comma to support multiple configurations
        config_strings = [c.strip() for c in imagefox_config_str.split(',')]
        logger.info(f"Found {len(config_strings)} configuration(s) for {project_name}")
        
        # Process each configuration
        for config_str in config_strings:
            logger.info(f"Processing configuration: {config_str}")
            imagefox_config = parse_imagefox_config(config_str)
            if not imagefox_config:
                logger.error(f"Invalid imagefox configuration for project {project_name}: {config_str}")
                stats['errors'] += 1
                continue
            
            logger.info(f"ImageFox config for {project_name}: {imagefox_config}")
            
            # Process this configuration
            config_stats = await process_configuration(project, imagefox_config, imagefox)
            
            # Aggregate statistics
            stats['records_processed'] += config_stats['records_processed']
            stats['images_added'] += config_stats['images_added']
            stats['total_cost'] += config_stats['total_cost']
            stats['errors'] += config_stats['errors']
            
            logger.info(f"COST_TRACKING: Config '{config_str}' - Cost: ${config_stats['total_cost']:.6f}, Images: {config_stats['images_added']}, Records: {config_stats['records_processed']}")
    
    except Exception as e:
        logger.error(f"Error processing project {project_name}: {e}")
        capture_exception(e)
        stats['errors'] += 1
    
    logger.info(f"COST_TRACKING: Project '{project_name}' - Total cost: ${stats['total_cost']:.6f}, Images: {stats['images_added']}, Records: {stats['records_processed']}, Errors: {stats['errors']}")
    logger.info(f"Project {project_name} processing complete: {stats}")
    return stats


async def process_configuration(project: Dict[str, Any], imagefox_config: Dict[str, Any], imagefox: ImageFox) -> Dict[str, Any]:
    """
    Process a single configuration for a project.
    
    Args:
        project: Project record from Airtable
        imagefox_config: Parsed configuration dictionary
        imagefox: ImageFox instance
        
    Returns:
        Dictionary with processing statistics
    """
    project_name = project["fields"]["project"]
    stats = {
        'records_processed': 0,
        'images_added': 0,
        'total_cost': 0.0,
        'errors': 0
    }
    
    try:
        # Connect to the target table
        base_id = project["fields"]["baseID"]
        table_name = imagefox_config["table_name"]
        field_name = imagefox_config["target_field"]  # Use target_field for images
        source_field = imagefox_config.get("source_field")  # May be None for auto-detect
        image_count = imagefox_config["image_count"]
        
        target_table = Table(AIRTABLE_API_KEY, base_id, table_name)
        
        # Find records that need image processing
        # Status should be "In Pipeline", NOT published, and the image field should be empty
        # Try both Status and status field names for compatibility
        # Skip records that are already published
        formula = f"AND(OR({{Status}}='In Pipeline', {{status}}='In Pipeline'), NOT({{{field_name}}}), NOT({{Published}}))"
        
        try:
            records = target_table.all(formula=formula)
            logger.info(f"Found {len(records)} unpublished records needing images in {project_name} (excluding published posts)")
            
            # Limit records in test mode
            if TEST_MODE and len(records) > TEST_RECORD_LIMIT:
                records = records[:TEST_RECORD_LIMIT]
                logger.info(f"TEST MODE: Limited to {TEST_RECORD_LIMIT} records")
                
        except Exception as e:
            logger.error(f"Failed to fetch records for project {project_name}: {e}")
            stats['errors'] += 1
            return stats
        
        # Process each record
        for record in records:
            record_id = record["fields"].get("id")
            if not record_id:
                logger.warning(f"Record missing ID field in {project_name}")
                continue
            
            try:
                logger.info(f"Processing record {record_id} in project {project_name}")
                
                # Extract article content for search query
                if imagefox_config.get('source_field'):
                    # Use specified source field
                    article_content = record["fields"].get(imagefox_config['source_field'], "")
                else:
                    # Auto-detect: Try common field names for content
                    article_content = (record["fields"].get("content", "") or 
                                     record["fields"].get("article", "") or 
                                     record["fields"].get("Text", "") or
                                     record["fields"].get("description", ""))
                
                # Try to get title
                title = record["fields"].get("title", "") or record["fields"].get("Title", "")
                
                if not article_content:
                    logger.warning(f"Record {record_id} has no article content in any common fields")
                    continue
                
                # Generate search query
                search_query = generate_search_query(article_content, title)
                if not search_query:
                    logger.warning(f"Could not generate search query for record {record_id}")
                    increment_error_count(target_table, record_id)
                    stats['errors'] += 1
                    continue
                
                # Create search request
                search_request = SearchRequest(
                    query=search_query,
                    limit=min(20, image_count * 3),  # Get more candidates than needed
                    max_results=image_count,
                    safe_search=True,
                    enable_processing=True,
                    enable_upload=True,  # Upload to ImageBB for CDN URLs
                    enable_storage=False  # Don't store in Airtable (we'll do it ourselves)
                )
                
                # Execute ImageFox workflow
                logger.info(f"Searching for images with query: '{search_query}'")
                workflow_result = await imagefox.search_and_select(search_request)
                
                # Log cost details
                workflow_cost = workflow_result.total_cost
                logger.info(f"COST_TRACKING: Record {record_id} - Workflow cost: ${workflow_cost:.6f}")
                
                if workflow_result.errors:
                    logger.warning(f"ImageFox workflow had errors: {workflow_result.errors}")
                
                if not workflow_result.selected_images:
                    logger.warning(f"No images found for record {record_id}")
                    increment_error_count(target_table, record_id)
                    stats['errors'] += 1
                    continue
                
                # Extract CDN URLs (prefer ImageBB URLs, fallback to original)
                image_urls = []
                for img in workflow_result.selected_images:
                    url = img.imagebb_url if img.imagebb_url else img.url
                    if url:
                        image_urls.append(url)
                
                if not image_urls:
                    logger.error(f"No valid image URLs for record {record_id}")
                    increment_error_count(target_table, record_id)
                    stats['errors'] += 1
                    continue
                
                # Add images to the record
                success = add_images_to_record(target_table, record_id, field_name, image_urls)
                if success:
                    # Update costs
                    cost = calculate_processing_cost(workflow_result)
                    if cost > 0:
                        update_record_cost(target_table, record_id, cost)
                    
                    stats['records_processed'] += 1
                    stats['images_added'] += len(image_urls)
                    stats['total_cost'] += cost
                    
                    logger.info(f"COST_TRACKING: Record {record_id} - Total cost: ${cost:.6f} for {len(image_urls)} images")
                    logger.info(f"COST_TRACKING: Average per image: ${cost/len(image_urls) if image_urls else 0:.6f}")
                    logger.info(f"Successfully processed record {record_id}: {len(image_urls)} images, ${cost:.6f} cost")
                else:
                    increment_error_count(target_table, record_id)
                    stats['errors'] += 1
                
                # Add small delay between records to avoid overwhelming APIs
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing record {record_id} in project {project_name}: {e}")
                capture_exception(e)
                increment_error_count(target_table, record_id)
                stats['errors'] += 1
                continue
    
    except Exception as e:
        logger.error(f"Error processing configuration {imagefox_config}: {e}")
        capture_exception(e)
        stats['errors'] += 1
    
    return stats


async def main():
    """Main execution function."""
    try:
        logger.info("="*50)
        logger.info("Starting ImageFox Agent execution")
        
        # Check if agent is enabled
        if not check_agent_status():
            return 0
        
        # Initialize ImageFox
        logger.info("Initializing ImageFox...")
        imagefox = ImageFox()
        
        # Validate ImageFox configuration (skip airtable since we don't use the Images table)
        validation_results = imagefox.validate_configuration()
        failed_components = [comp for comp, status in validation_results.items() if not status and comp != 'airtable']
        
        if failed_components:
            logger.error(f"ImageFox validation failed for components: {failed_components}")
            return 1
        
        logger.info("ImageFox validation successful (airtable Images table skipped)")
        
        # Get projects with imagefox field
        try:
            projects = projects_table.all(formula="AND({imagefox}, {turnedOn})")
            logger.info(f"Found {len(projects)} projects with imagefox configuration")
        except Exception as e:
            logger.error(f"Failed to fetch projects: {e}")
            capture_exception(e)
            return 1
        
        if not projects:
            logger.info("No projects with imagefox configuration found")
            return 0
        
        # Process each project
        total_stats = {
            'projects_processed': 0,
            'total_records_processed': 0,
            'total_images_added': 0,
            'total_cost': 0.0,
            'total_errors': 0
        }
        
        for project in projects:
            try:
                project_stats = await process_project(project, imagefox)
                
                total_stats['projects_processed'] += 1
                total_stats['total_records_processed'] += project_stats['records_processed']
                total_stats['total_images_added'] += project_stats['images_added']
                total_stats['total_cost'] += project_stats['total_cost']
                total_stats['total_errors'] += project_stats['errors']
                
                # Add delay between projects
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing project {project.get('fields', {}).get('project', 'unknown')}: {e}")
                capture_exception(e)
                total_stats['total_errors'] += 1
                continue
        
        # Log final statistics with cost breakdown
        logger.info("="*50)
        logger.info("ImageFox Agent execution completed")
        logger.info(f"Final Statistics: {total_stats}")
        logger.info("="*50)
        logger.info("COST_TRACKING: FINAL SUMMARY")
        logger.info(f"COST_TRACKING: Total cost: ${total_stats['total_cost']:.6f}")
        logger.info(f"COST_TRACKING: Total images: {total_stats['total_images_added']}")
        logger.info(f"COST_TRACKING: Total records: {total_stats['total_records_processed']}")
        if total_stats['total_images_added'] > 0:
            avg_per_image = total_stats['total_cost'] / total_stats['total_images_added']
            logger.info(f"COST_TRACKING: Average cost per image: ${avg_per_image:.6f}")
        if total_stats['total_records_processed'] > 0:
            avg_per_record = total_stats['total_cost'] / total_stats['total_records_processed']
            logger.info(f"COST_TRACKING: Average cost per record: ${avg_per_record:.6f}")
        logger.info("="*50)
        
        # Cleanup
        await imagefox.cleanup()
        
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error in ImageFox Agent: {e}")
        capture_exception(e)
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))