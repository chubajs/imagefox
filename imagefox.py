#!/usr/bin/env python3
"""
ImageFox - Intelligent Image Search and Selection Agent

Main orchestration module that coordinates all ImageFox components to provide
comprehensive image search, analysis, and selection capabilities.
"""

import os
import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass, asdict
import tempfile
import shutil
from pathlib import Path

import sentry_sdk
from sentry_sdk import capture_exception
from dotenv import load_dotenv

from apify_client import ApifyClient
from openrouter_client import OpenRouterClient
from vision_analyzer import VisionAnalyzer, ImageMetadata
from image_selector import ImageSelector, ImageCandidate
from image_processor import ImageProcessor
from airtable_uploader import AirtableUploader
from imagebb_uploader import ImageBBUploader

logger = logging.getLogger(__name__)


@dataclass
class SearchRequest:
    """Search request configuration."""
    query: str
    limit: int = 20
    safe_search: bool = True
    min_width: int = 400
    min_height: int = 300
    max_results: int = 5
    enable_processing: bool = True
    enable_upload: bool = True
    enable_storage: bool = True


@dataclass
class ImageResult:
    """Complete image result with all metadata."""
    url: str
    source_url: str
    title: str
    dimensions: str
    analysis: Dict[str, Any]
    selection_score: float
    processed_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    imagebb_url: Optional[str] = None
    airtable_id: Optional[str] = None
    ai_selection_explanation: Optional[str] = None


@dataclass
class WorkflowResult:
    """Complete workflow execution result."""
    search_query: str
    total_found: int
    processed_count: int
    selected_count: int
    selected_images: List[ImageResult]
    processing_time: float
    total_cost: float
    errors: List[str]
    statistics: Dict[str, Any]
    created_at: str


class ImageFox:
    """
    Main ImageFox orchestration class.
    
    Coordinates search, analysis, selection, processing, and storage
    of images through a unified workflow.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize ImageFox orchestrator.
        
        Args:
            config_path: Optional path to .env configuration file
        """
        # Load environment configuration
        if config_path:
            load_dotenv(config_path)
        else:
            load_dotenv()
        
        # Configuration
        self.temp_dir = Path(os.getenv('IMAGEFOX_TEMP_DIR', tempfile.gettempdir())) / 'imagefox'
        self.enable_cleanup = os.getenv('ENABLE_CLEANUP', 'true').lower() == 'true'
        self.max_concurrent = int(os.getenv('MAX_CONCURRENT_OPERATIONS', '5'))
        self.enable_caching = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
        
        # Create temp directory
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self._initialize_components()
        
        # Workflow statistics
        self.stats = {
            'searches_performed': 0,
            'images_processed': 0,
            'images_selected': 0,
            'total_processing_time': 0.0,
            'total_cost': 0.0,
            'errors_count': 0
        }
        
        logger.info("ImageFox orchestrator initialized")
    
    def _initialize_components(self):
        """Initialize all ImageFox components."""
        try:
            # Core API clients
            self.apify_client = ApifyClient()
            self.openrouter_client = OpenRouterClient()
            
            # Analysis and selection
            self.vision_analyzer = VisionAnalyzer(self.openrouter_client)
            self.image_selector = ImageSelector()
            
            # Processing and storage
            self.image_processor = ImageProcessor()
            self.airtable_uploader = AirtableUploader()
            self.imagebb_uploader = ImageBBUploader()
            
            logger.info("All ImageFox components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ImageFox components: {e}")
            capture_exception(e)
            raise
    
    def validate_configuration(self) -> Dict[str, bool]:
        """
        Validate configuration and component connectivity.
        
        Returns:
            Dictionary with validation results for each component
        """
        results = {}
        
        try:
            # Test Apify connection
            results['apify'] = self.apify_client.validate_api_key()
        except Exception as e:
            logger.error(f"Apify validation failed: {e}")
            results['apify'] = False
        
        try:
            # Test OpenRouter connection
            results['openrouter'] = self.openrouter_client.validate_api_key()
        except Exception as e:
            logger.error(f"OpenRouter validation failed: {e}")
            results['openrouter'] = False
        
        try:
            # Test Airtable connection
            results['airtable'] = self.airtable_uploader.validate_connection()
        except Exception as e:
            logger.error(f"Airtable validation failed: {e}")
            results['airtable'] = False
        
        try:
            # Test ImageBB connection (create simple validation)
            results['imagebb'] = True  # ImageBB doesn't have validation endpoint
        except Exception as e:
            logger.error(f"ImageBB validation failed: {e}")
            results['imagebb'] = False
        
        # Check temp directory
        results['temp_directory'] = self.temp_dir.exists() and os.access(self.temp_dir, os.W_OK)
        
        logger.info(f"Configuration validation results: {results}")
        return results
    
    async def search_and_select(self, request: SearchRequest) -> WorkflowResult:
        """
        Main workflow: search, analyze, select, and optionally process/store images.
        
        Args:
            request: Search request configuration
            
        Returns:
            Complete workflow results
        """
        start_time = time.time()
        errors = []
        
        try:
            logger.info(f"Starting search and selection for query: '{request.query}'")
            
            # Step 1: Search for images
            search_results = await self._search_images(request, errors)
            if not search_results:
                return self._create_empty_result(request, start_time, errors)
            
            # Step 2: Analyze images
            analyzed_images = await self._analyze_images(search_results, request, errors)
            if not analyzed_images:
                return self._create_empty_result(request, start_time, errors)
            
            # Step 3: Select best images
            selected_images = await self._select_images(analyzed_images, request, errors)
            if not selected_images:
                return self._create_empty_result(request, start_time, errors)
            
            # Step 4: Process images (optional)
            if request.enable_processing:
                selected_images = await self._process_images(selected_images, errors)
            
            # Step 5: Upload and store (optional)
            if request.enable_upload:
                selected_images = await self._upload_images(selected_images, errors)
            
            if request.enable_storage:
                selected_images = await self._store_metadata(selected_images, request, errors)
            
            # Create result
            processing_time = time.time() - start_time
            result = WorkflowResult(
                search_query=request.query,
                total_found=len(search_results),
                processed_count=len(analyzed_images),
                selected_count=len(selected_images),
                selected_images=selected_images,
                processing_time=processing_time,
                total_cost=self._calculate_total_cost(),
                errors=errors,
                statistics=self._generate_statistics(),
                created_at=datetime.now().isoformat()
            )
            
            # Update internal statistics
            self._update_stats(result)
            
            logger.info(
                f"Workflow completed: {len(selected_images)} images selected from "
                f"{len(search_results)} found in {processing_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            capture_exception(e)
            errors.append(str(e))
            return self._create_empty_result(request, start_time, errors)
        
        finally:
            # Cleanup if enabled
            if self.enable_cleanup:
                await self._cleanup_temp_files()
    
    async def _search_images(self, request: SearchRequest, errors: List[str]) -> List[Dict[str, Any]]:
        """Search for images using Apify."""
        try:
            logger.info(f"Searching for images: '{request.query}' (limit: {request.limit})")
            
            results = self.apify_client.search_images(
                query=request.query,
                limit=request.limit,
                safe_search=request.safe_search,
                min_width=request.min_width,
                min_height=request.min_height
            )
            
            logger.info(f"Found {len(results)} images")
            return results
            
        except Exception as e:
            error_msg = f"Image search failed: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
            return []
    
    async def _analyze_images(self, search_results: List[Dict[str, Any]], request: SearchRequest, errors: List[str]) -> List[ImageCandidate]:
        """Analyze images using vision models."""
        try:
            logger.info(f"Analyzing {len(search_results)} images")
            
            candidates = []
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            async def analyze_single_image(image_data):
                async with semaphore:
                    try:
                        # Create metadata
                        metadata = ImageMetadata(
                            url=image_data.get('url', ''),
                            title=image_data.get('title', ''),
                            source_url=image_data.get('source', ''),
                            width=image_data.get('width'),
                            height=image_data.get('height')
                        )
                        
                        # Analyze image
                        analysis = self.vision_analyzer.analyze_image(
                            metadata,
                            search_query=request.query
                        )
                        
                        # Create candidate
                        candidate = ImageCandidate(
                            url=metadata.url,
                            source_url=metadata.source_url,
                            title=metadata.title,
                            width=metadata.width or 0,
                            height=metadata.height or 0,
                            analysis_data=asdict(analysis)
                        )
                        
                        return candidate
                        
                    except Exception as e:
                        logger.warning(f"Failed to analyze image {image_data.get('url', 'unknown')}: {e}")
                        return None
            
            # Analyze images concurrently
            tasks = [analyze_single_image(image) for image in search_results]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter successful results
            candidates = [r for r in results if isinstance(r, ImageCandidate)]
            
            logger.info(f"Successfully analyzed {len(candidates)}/{len(search_results)} images")
            return candidates
            
        except Exception as e:
            error_msg = f"Image analysis failed: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
            return []
    
    async def _select_images(self, candidates: List[ImageCandidate], request: SearchRequest, errors: List[str]) -> List[ImageResult]:
        """Select best images using selection algorithm."""
        try:
            logger.info(f"Selecting best {request.max_results} images from {len(candidates)} candidates")
            
            # Run AI-powered selection with Claude 3.5 Sonnet
            selection_result = self.image_selector.select_with_ai_reasoning(
                candidates=candidates,
                count=request.max_results,
                search_query=request.query,
                openrouter_client=self.openrouter_client
            )
            
            # Convert to ImageResult objects
            selected_images = []
            for selected in selection_result.selected_images:
                # Get dimensions from metadata
                width = selected.metadata.get('width', 0)
                height = selected.metadata.get('height', 0)
                dimensions = f"{width}x{height}" if width and height else "unknown"
                
                # Create analysis dict with raw responses
                analysis_dict = {
                    'description': selected.analysis.description,
                    'objects': selected.analysis.objects,
                    'scene_type': selected.analysis.scene_type,
                    'colors': selected.analysis.colors,
                    'composition': selected.analysis.composition,
                    'quality_score': selected.analysis.quality_metrics.overall_score,
                    'relevance_score': selected.analysis.relevance_score,
                    'confidence_score': selected.analysis.confidence_score,
                    'models_used': selected.analysis.models_used,
                    'processing_time': selected.analysis.processing_time,
                    'cost_estimate': selected.analysis.cost_estimate,
                    'technical_details': selected.analysis.quality_metrics.__dict__,
                    'raw_model_responses': getattr(selected.analysis, 'raw_model_responses', [])
                }
                
                image_result = ImageResult(
                    url=selected.image_url,
                    source_url=selected.source_url,
                    title=selected.title,
                    dimensions=dimensions,
                    analysis=analysis_dict,
                    selection_score=selection_result.scores.get(selected.image_url, 0.0),
                    ai_selection_explanation=selection_result.ai_selection_explanation
                )
                selected_images.append(image_result)
            
            logger.info(f"Selected {len(selected_images)} images")
            return selected_images
            
        except Exception as e:
            error_msg = f"Image selection failed: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
            return []
    
    async def _process_images(self, images: List[ImageResult], errors: List[str]) -> List[ImageResult]:
        """Process images (download, optimize, generate thumbnails)."""
        try:
            logger.info(f"Processing {len(images)} selected images")
            
            async with self.image_processor as processor:
                for image in images:
                    try:
                        # Process image
                        result = await processor.process_image(
                            image.url,
                            optimize=True,
                            generate_thumbnail=True
                        )
                        
                        if result.success:
                            image.processed_path = result.file_path
                            image.thumbnail_path = result.thumbnail_path
                        else:
                            logger.warning(f"Failed to process image {image.url}: {result.error_message}")
                            
                    except Exception as e:
                        logger.warning(f"Error processing image {image.url}: {e}")
            
            logger.info("Image processing completed")
            return images
            
        except Exception as e:
            error_msg = f"Image processing failed: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
            return images
    
    async def _upload_images(self, images: List[ImageResult], errors: List[str]) -> List[ImageResult]:
        """Upload processed images to ImageBB."""
        try:
            logger.info(f"Uploading {len(images)} images to ImageBB")
            
            for image in images:
                if image.processed_path and Path(image.processed_path).exists():
                    try:
                        upload_result = self.imagebb_uploader.upload_file(image.processed_path)
                        if upload_result:
                            image.imagebb_url = upload_result.get('url')
                            logger.debug(f"Uploaded {image.url} -> {image.imagebb_url}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to upload image {image.url}: {e}")
            
            logger.info("Image upload completed")
            return images
            
        except Exception as e:
            error_msg = f"Image upload failed: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
            return images
    
    async def _store_metadata(self, images: List[ImageResult], request: SearchRequest, errors: List[str]) -> List[ImageResult]:
        """Store image metadata in Airtable."""
        try:
            logger.info(f"Storing metadata for {len(images)} images in Airtable")
            
            records = []
            for image in images:
                record_data = {
                    'Image URL': image.url,
                    'Source URL': image.source_url,
                    'Title': image.title,
                    'Search Query': request.query,
                    'Dimensions': image.dimensions,
                    'Selection Score': image.selection_score,
                    'Analysis Results': str(image.analysis)[:50000],  # Airtable limit
                    'ImageBB URL': image.imagebb_url or '',
                    'Processing Status': 'Completed',
                    'Upload Date': datetime.now().isoformat()
                }
                records.append(record_data)
            
            # Batch create records
            created_records = self.airtable_uploader.batch_create(records)
            
            # Update image objects with Airtable IDs
            for i, record in enumerate(created_records):
                if i < len(images):
                    images[i].airtable_id = record.get('id')
            
            logger.info(f"Stored {len(created_records)} records in Airtable")
            return images
            
        except Exception as e:
            error_msg = f"Metadata storage failed: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
            return images
    
    def _calculate_total_cost(self) -> float:
        """Calculate total cost of workflow execution."""
        total_cost = 0.0
        
        # OpenRouter costs
        if hasattr(self.openrouter_client, 'usage_stats'):
            total_cost += self.openrouter_client.usage_stats.get('total_cost', 0.0)
        
        # Apify costs (estimated)
        if hasattr(self.apify_client, 'usage_stats'):
            total_cost += self.apify_client.usage_stats.get('estimated_cost', 0.0)
        
        return total_cost
    
    def _generate_statistics(self) -> Dict[str, Any]:
        """Generate workflow execution statistics."""
        stats = {}
        
        # Component statistics
        if hasattr(self.apify_client, 'get_usage_stats'):
            stats['apify'] = self.apify_client.get_usage_stats()
        
        if hasattr(self.openrouter_client, 'get_usage_stats'):
            stats['openrouter'] = self.openrouter_client.get_usage_stats()
        
        if hasattr(self.image_processor, 'get_stats'):
            stats['image_processor'] = self.image_processor.get_stats()
        
        if hasattr(self.image_selector, 'get_selection_stats'):
            stats['image_selector'] = self.image_selector.get_selection_stats()
        
        return stats
    
    def _update_stats(self, result: WorkflowResult):
        """Update internal statistics."""
        self.stats['searches_performed'] += 1
        self.stats['images_processed'] += result.processed_count
        self.stats['images_selected'] += result.selected_count
        self.stats['total_processing_time'] += result.processing_time
        self.stats['total_cost'] += result.total_cost
        self.stats['errors_count'] += len(result.errors)
    
    def _create_empty_result(self, request: SearchRequest, start_time: float, errors: List[str]) -> WorkflowResult:
        """Create empty result when workflow fails."""
        return WorkflowResult(
            search_query=request.query,
            total_found=0,
            processed_count=0,
            selected_count=0,
            selected_images=[],
            processing_time=time.time() - start_time,
            total_cost=0.0,
            errors=errors,
            statistics={},
            created_at=datetime.now().isoformat()
        )
    
    async def _cleanup_temp_files(self):
        """Clean up temporary files."""
        try:
            if self.temp_dir.exists():
                # Clean up old temp files
                for file_path in self.temp_dir.iterdir():
                    try:
                        if file_path.is_file():
                            # Remove files older than 1 hour
                            if time.time() - file_path.stat().st_mtime > 3600:
                                file_path.unlink()
                        elif file_path.is_dir():
                            # Remove empty directories
                            try:
                                file_path.rmdir()
                            except OSError:
                                pass  # Directory not empty
                    except Exception as e:
                        logger.warning(f"Failed to clean up {file_path}: {e}")
            
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")
    
    async def process_batch(self, requests: List[SearchRequest]) -> List[WorkflowResult]:
        """
        Process multiple search requests in batch.
        
        Args:
            requests: List of search requests
            
        Returns:
            List of workflow results
        """
        logger.info(f"Processing batch of {len(requests)} search requests")
        
        # Process requests concurrently with semaphore
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def process_single_request(request):
            async with semaphore:
                return await self.search_and_select(request)
        
        # Execute all requests
        tasks = [process_single_request(request) for request in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        successful_results = [r for r in results if isinstance(r, WorkflowResult)]
        
        logger.info(f"Batch processing completed: {len(successful_results)}/{len(requests)} successful")
        return successful_results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        return self.stats.copy()
    
    def clear_cache(self):
        """Clear all component caches."""
        try:
            if hasattr(self.apify_client, 'clear_cache'):
                self.apify_client.clear_cache()
            
            if hasattr(self.vision_analyzer, 'clear_cache'):
                self.vision_analyzer.clear_cache()
            
            if hasattr(self.image_selector, 'clear_cache'):
                self.image_selector.clear_cache()
            
            logger.info("All caches cleared")
            
        except Exception as e:
            logger.error(f"Cache clearing failed: {e}")
    
    async def cleanup(self):
        """Perform final cleanup of resources."""
        try:
            # Clean up temp files
            await self._cleanup_temp_files()
            
            # Close any open connections
            if hasattr(self.image_processor, '__aexit__'):
                try:
                    await self.image_processor.__aexit__(None, None, None)
                except:
                    pass
            
            logger.info("ImageFox cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


async def main():
    """Main CLI interface for ImageFox."""
    import argparse
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='ImageFox - Intelligent Image Search and Selection')
    parser.add_argument('query', help='Search query for images')
    parser.add_argument('--limit', type=int, default=20, help='Maximum images to search')
    parser.add_argument('--max-results', type=int, default=5, help='Maximum images to select')
    parser.add_argument('--no-processing', action='store_true', help='Disable image processing')
    parser.add_argument('--no-upload', action='store_true', help='Disable image upload')
    parser.add_argument('--no-storage', action='store_true', help='Disable metadata storage')
    parser.add_argument('--validate', action='store_true', help='Validate configuration only')
    
    args = parser.parse_args()
    
    try:
        # Initialize ImageFox
        imagefox = ImageFox()
        
        # Validate configuration if requested
        if args.validate:
            print("Validating ImageFox configuration...")
            validation = imagefox.validate_configuration()
            for component, status in validation.items():
                status_str = "✅ OK" if status else "❌ FAILED"
                print(f"  {component}: {status_str}")
            return 0 if all(validation.values()) else 1
        
        # Create search request
        request = SearchRequest(
            query=args.query,
            limit=args.limit,
            max_results=args.max_results,
            enable_processing=not args.no_processing,
            enable_upload=not args.no_upload,
            enable_storage=not args.no_storage
        )
        
        # Execute workflow
        print(f"🔍 Searching for: '{request.query}'")
        result = await imagefox.search_and_select(request)
        
        # Display results
        print(f"\n📊 Results:")
        print(f"  Found: {result.total_found} images")
        print(f"  Processed: {result.processed_count} images")
        print(f"  Selected: {result.selected_count} images")
        print(f"  Processing time: {result.processing_time:.2f}s")
        print(f"  Total cost: ${result.total_cost:.6f}")
        
        if result.errors:
            print(f"  Errors: {len(result.errors)}")
            for error in result.errors:
                print(f"    - {error}")
        
        print(f"\n🖼️  Selected Images:")
        for i, image in enumerate(result.selected_images, 1):
            print(f"  {i}. {image.title}")
            print(f"     URL: {image.url}")
            print(f"     Score: {image.selection_score:.3f}")
            print(f"     Dimensions: {image.dimensions}")
            if image.imagebb_url:
                print(f"     CDN URL: {image.imagebb_url}")
            print()
        
        # Cleanup
        await imagefox.cleanup()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))