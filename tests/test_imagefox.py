#!/usr/bin/env python3
"""
Unit tests for ImageFox main orchestration module.
"""

import os
import sys
import unittest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock, call
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from imagefox import (
    ImageFox, SearchRequest, ImageResult, WorkflowResult
)
from vision_analyzer import ImageMetadata, ComprehensiveAnalysis
from image_selector import ImageCandidate, SelectionResult


class TestSearchRequest(unittest.TestCase):
    """Test cases for SearchRequest dataclass."""
    
    def test_search_request_defaults(self):
        """Test SearchRequest with default values."""
        request = SearchRequest(query="test query")
        
        self.assertEqual(request.query, "test query")
        self.assertEqual(request.limit, 20)
        self.assertEqual(request.max_results, 5)
        self.assertTrue(request.safe_search)
        self.assertTrue(request.enable_processing)
        self.assertTrue(request.enable_upload)
        self.assertTrue(request.enable_storage)
    
    def test_search_request_custom_values(self):
        """Test SearchRequest with custom values."""
        request = SearchRequest(
            query="custom query",
            limit=50,
            max_results=10,
            safe_search=False,
            min_width=800,
            min_height=600,
            enable_processing=False,
            enable_upload=False,
            enable_storage=False
        )
        
        self.assertEqual(request.query, "custom query")
        self.assertEqual(request.limit, 50)
        self.assertEqual(request.max_results, 10)
        self.assertFalse(request.safe_search)
        self.assertEqual(request.min_width, 800)
        self.assertEqual(request.min_height, 600)
        self.assertFalse(request.enable_processing)
        self.assertFalse(request.enable_upload)
        self.assertFalse(request.enable_storage)


class TestImageResult(unittest.TestCase):
    """Test cases for ImageResult dataclass."""
    
    def test_image_result_creation(self):
        """Test ImageResult creation."""
        result = ImageResult(
            url="https://example.com/image.jpg",
            source_url="https://example.com/page",
            title="Test Image",
            dimensions="1920x1080",
            analysis={"quality_score": 0.9},
            selection_score=0.85,
            processed_path="/tmp/processed.jpg",
            imagebb_url="https://i.ibb.co/test.jpg",
            airtable_id="recABC123"
        )
        
        self.assertEqual(result.url, "https://example.com/image.jpg")
        self.assertEqual(result.selection_score, 0.85)
        self.assertEqual(result.processed_path, "/tmp/processed.jpg")
        self.assertEqual(result.imagebb_url, "https://i.ibb.co/test.jpg")
        self.assertEqual(result.airtable_id, "recABC123")


class TestWorkflowResult(unittest.TestCase):
    """Test cases for WorkflowResult dataclass."""
    
    def test_workflow_result_creation(self):
        """Test WorkflowResult creation."""
        image_result = ImageResult(
            url="https://example.com/image.jpg",
            source_url="https://example.com/page",
            title="Test Image",
            dimensions="1920x1080",
            analysis={"quality_score": 0.9},
            selection_score=0.85
        )
        
        result = WorkflowResult(
            search_query="test query",
            total_found=20,
            processed_count=15,
            selected_count=1,
            selected_images=[image_result],
            processing_time=5.2,
            total_cost=0.05,
            errors=[],
            statistics={"processed": 15},
            created_at="2023-01-01T12:00:00"
        )
        
        self.assertEqual(result.search_query, "test query")
        self.assertEqual(result.total_found, 20)
        self.assertEqual(result.selected_count, 1)
        self.assertEqual(len(result.selected_images), 1)
        self.assertEqual(result.processing_time, 5.2)
        self.assertEqual(result.total_cost, 0.05)


class TestImageFox(unittest.TestCase):
    """Test cases for ImageFox orchestration class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Set test environment variables
        self.original_env = os.environ.copy()
        os.environ.update({
            'IMAGEFOX_TEMP_DIR': tempfile.gettempdir(),
            'ENABLE_CLEANUP': 'false',  # Disable cleanup in tests
            'MAX_CONCURRENT_OPERATIONS': '2',
            'ENABLE_CACHING': 'true'
        })
        
        # Mock all component initialization
        self.patch_apify = patch('imagefox.ApifyClient')
        self.patch_openrouter = patch('imagefox.OpenRouterClient')
        self.patch_vision = patch('imagefox.VisionAnalyzer')
        self.patch_selector = patch('imagefox.ImageSelector')
        self.patch_processor = patch('imagefox.ImageProcessor')
        self.patch_airtable = patch('imagefox.AirtableUploader')
        self.patch_imagebb = patch('imagefox.ImageBBUploader')
        
        self.mock_apify = self.patch_apify.start()
        self.mock_openrouter = self.patch_openrouter.start()
        self.mock_vision = self.patch_vision.start()
        self.mock_selector = self.patch_selector.start()
        self.mock_processor = self.patch_processor.start()
        self.mock_airtable = self.patch_airtable.start()
        self.mock_imagebb = self.patch_imagebb.start()
        
        # Setup mock instances
        self.apify_instance = MagicMock()
        self.openrouter_instance = MagicMock()
        self.vision_instance = MagicMock()
        self.selector_instance = MagicMock()
        self.processor_instance = MagicMock()
        self.airtable_instance = MagicMock()
        self.imagebb_instance = MagicMock()
        
        self.mock_apify.return_value = self.apify_instance
        self.mock_openrouter.return_value = self.openrouter_instance
        self.mock_vision.return_value = self.vision_instance
        self.mock_selector.return_value = self.selector_instance
        self.mock_processor.return_value = self.processor_instance
        self.mock_airtable.return_value = self.airtable_instance
        self.mock_imagebb.return_value = self.imagebb_instance
        
        # Sample data
        self.sample_search_results = [
            {
                'url': 'https://example.com/image1.jpg',
                'title': 'Test Image 1',
                'source': 'https://example.com/page1',
                'width': 1920,
                'height': 1080
            },
            {
                'url': 'https://example.com/image2.jpg',
                'title': 'Test Image 2',
                'source': 'https://example.com/page2',
                'width': 1600,
                'height': 900
            }
        ]
        
        self.sample_analysis = ComprehensiveAnalysis(
            description="A beautiful test image",
            objects=["test", "object"],
            scene_type="test",
            colors=["blue", "green"],
            composition="centered",
            quality_metrics=MagicMock(),
            relevance_score=0.9,
            technical_details={"lighting": "good"},
            models_used=["test-model"],
            processing_time=1.0,
            cost_estimate=0.01,
            confidence_score=0.85,
            timestamp="2023-01-01T12:00:00"
        )
    
    def tearDown(self):
        """Clean up after tests."""
        # Restore environment
        os.environ.clear()
        os.environ.update(self.original_env)
        
        # Stop all patches
        self.patch_apify.stop()
        self.patch_openrouter.stop()
        self.patch_vision.stop()
        self.patch_selector.stop()
        self.patch_processor.stop()
        self.patch_airtable.stop()
        self.patch_imagebb.stop()
    
    def test_initialization(self):
        """Test ImageFox initialization."""
        imagefox = ImageFox()
        
        self.assertIsNotNone(imagefox.apify_client)
        self.assertIsNotNone(imagefox.vision_analyzer)
        self.assertIsNotNone(imagefox.image_selector)
        self.assertIsNotNone(imagefox.image_processor)
        self.assertIsNotNone(imagefox.airtable_uploader)
        self.assertIsNotNone(imagefox.imagebb_uploader)
        
        # Check component initialization
        self.mock_apify.assert_called_once()
        self.mock_openrouter.assert_called_once()
        self.mock_vision.assert_called_once_with(self.openrouter_instance)
        self.mock_selector.assert_called_once()
        self.mock_processor.assert_called_once()
        self.mock_airtable.assert_called_once()
        self.mock_imagebb.assert_called_once()
    
    def test_validate_configuration(self):
        """Test configuration validation."""
        # Setup mock validation methods
        self.apify_instance.validate_api_key.return_value = True
        self.openrouter_instance.validate_api_key.return_value = True
        self.airtable_instance.validate_connection.return_value = True
        
        imagefox = ImageFox()
        results = imagefox.validate_configuration()
        
        self.assertIn('apify', results)
        self.assertIn('openrouter', results)
        self.assertIn('airtable', results)
        self.assertIn('imagebb', results)
        self.assertIn('temp_directory', results)
        
        self.assertTrue(results['apify'])
        self.assertTrue(results['openrouter'])
        self.assertTrue(results['airtable'])
        self.assertTrue(results['imagebb'])
        self.assertTrue(results['temp_directory'])
    
    def test_validate_configuration_failures(self):
        """Test configuration validation with failures."""
        # Setup mock validation methods to fail
        self.apify_instance.validate_api_key.side_effect = Exception("API key invalid")
        self.openrouter_instance.validate_api_key.return_value = False
        self.airtable_instance.validate_connection.return_value = False
        
        imagefox = ImageFox()
        results = imagefox.validate_configuration()
        
        self.assertFalse(results['apify'])
        self.assertFalse(results['openrouter'])
        self.assertFalse(results['airtable'])
        self.assertTrue(results['imagebb'])  # ImageBB always returns True
    
    @patch('imagefox.asyncio.gather')
    async def test_search_images_success(self, mock_gather):
        """Test successful image search."""
        self.apify_instance.search_images.return_value = self.sample_search_results
        
        imagefox = ImageFox()
        request = SearchRequest(query="test query")
        errors = []
        
        results = await imagefox._search_images(request, errors)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['url'], 'https://example.com/image1.jpg')
        self.assertEqual(len(errors), 0)
        
        self.apify_instance.search_images.assert_called_once_with(
            query="test query",
            limit=20,
            safe_search=True,
            min_width=400,
            min_height=300
        )
    
    async def test_search_images_failure(self):
        """Test image search failure."""
        self.apify_instance.search_images.side_effect = Exception("Search failed")
        
        imagefox = ImageFox()
        request = SearchRequest(query="test query")
        errors = []
        
        results = await imagefox._search_images(request, errors)
        
        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        self.assertIn("Image search failed", errors[0])
    
    async def test_analyze_images_success(self):
        """Test successful image analysis."""
        # Mock vision analyzer
        self.vision_instance.analyze_image.return_value = self.sample_analysis
        
        imagefox = ImageFox()
        request = SearchRequest(query="test query")
        errors = []
        
        results = await imagefox._analyze_images(self.sample_search_results, request, errors)
        
        self.assertEqual(len(results), 2)
        self.assertIsInstance(results[0], ImageCandidate)
        self.assertEqual(results[0].url, 'https://example.com/image1.jpg')
        self.assertEqual(len(errors), 0)
    
    async def test_analyze_images_partial_failure(self):
        """Test image analysis with partial failures."""
        # First call succeeds, second fails
        self.vision_instance.analyze_image.side_effect = [
            self.sample_analysis,
            Exception("Analysis failed")
        ]
        
        imagefox = ImageFox()
        request = SearchRequest(query="test query")
        errors = []
        
        results = await imagefox._analyze_images(self.sample_search_results, request, errors)
        
        # Should return 1 successful result out of 2
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].url, 'https://example.com/image1.jpg')
    
    async def test_select_images_success(self):
        """Test successful image selection."""
        # Create mock candidates
        candidates = [
            ImageCandidate(
                url='https://example.com/image1.jpg',
                source_url='https://example.com/page1',
                title='Test Image 1',
                width=1920,
                height=1080,
                analysis_data=asdict(self.sample_analysis)
            ),
            ImageCandidate(
                url='https://example.com/image2.jpg',
                source_url='https://example.com/page2',
                title='Test Image 2',
                width=1600,
                height=900,
                analysis_data=asdict(self.sample_analysis)
            )
        ]
        
        # Mock selection result
        mock_selection = SelectionResult(
            selected_images=[
                {
                    'url': 'https://example.com/image1.jpg',
                    'source_url': 'https://example.com/page1',
                    'title': 'Test Image 1',
                    'width': 1920,
                    'height': 1080,
                    'analysis_data': asdict(self.sample_analysis),
                    'final_score': 0.95
                }
            ],
            scores={'https://example.com/image1.jpg': 0.95},
            reasoning="Selected based on quality",
            alternatives=[],
            selection_time=1.0,
            total_candidates=2
        )
        
        self.selector_instance.select_best.return_value = mock_selection
        
        imagefox = ImageFox()
        request = SearchRequest(query="test query", max_results=1)
        errors = []
        
        results = await imagefox._select_images(candidates, request, errors)
        
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], ImageResult)
        self.assertEqual(results[0].url, 'https://example.com/image1.jpg')
        self.assertEqual(results[0].selection_score, 0.95)
        self.assertEqual(len(errors), 0)
        
        self.selector_instance.select_best.assert_called_once_with(
            candidates=candidates,
            count=1,
            search_query="test query"
        )
    
    async def test_process_images_success(self):
        """Test successful image processing."""
        # Mock processor context manager
        processor_context = AsyncMock()
        self.processor_instance.__aenter__.return_value = processor_context
        self.processor_instance.__aexit__.return_value = None
        
        # Mock processing result
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.file_path = "/tmp/processed.jpg"
        mock_result.thumbnail_path = "/tmp/thumb.jpg"
        
        processor_context.process_image.return_value = mock_result
        
        images = [ImageResult(
            url='https://example.com/image1.jpg',
            source_url='https://example.com/page1',
            title='Test Image 1',
            dimensions='1920x1080',
            analysis={'quality': 0.9},
            selection_score=0.85
        )]
        
        imagefox = ImageFox()
        errors = []
        
        results = await imagefox._process_images(images, errors)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].processed_path, "/tmp/processed.jpg")
        self.assertEqual(results[0].thumbnail_path, "/tmp/thumb.jpg")
        self.assertEqual(len(errors), 0)
    
    async def test_upload_images_success(self):
        """Test successful image upload."""
        # Mock successful upload
        self.imagebb_instance.upload_file.return_value = {
            'url': 'https://i.ibb.co/test.jpg'
        }
        
        # Create test file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(b"test image data")
        
        try:
            images = [ImageResult(
                url='https://example.com/image1.jpg',
                source_url='https://example.com/page1',
                title='Test Image 1',
                dimensions='1920x1080',
                analysis={'quality': 0.9},
                selection_score=0.85,
                processed_path=temp_path
            )]
            
            imagefox = ImageFox()
            errors = []
            
            results = await imagefox._upload_images(images, errors)
            
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].imagebb_url, 'https://i.ibb.co/test.jpg')
            self.assertEqual(len(errors), 0)
            
        finally:
            # Clean up test file
            os.unlink(temp_path)
    
    async def test_store_metadata_success(self):
        """Test successful metadata storage."""
        # Mock successful storage
        self.airtable_instance.batch_create.return_value = [
            {'id': 'recABC123'}
        ]
        
        images = [ImageResult(
            url='https://example.com/image1.jpg',
            source_url='https://example.com/page1',
            title='Test Image 1',
            dimensions='1920x1080',
            analysis={'quality': 0.9},
            selection_score=0.85,
            imagebb_url='https://i.ibb.co/test.jpg'
        )]
        
        imagefox = ImageFox()
        request = SearchRequest(query="test query")
        errors = []
        
        results = await imagefox._store_metadata(images, request, errors)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].airtable_id, 'recABC123')
        self.assertEqual(len(errors), 0)
        
        # Verify batch_create was called with correct data
        self.airtable_instance.batch_create.assert_called_once()
        call_args = self.airtable_instance.batch_create.call_args[0][0]
        self.assertEqual(len(call_args), 1)
        self.assertEqual(call_args[0]['Image URL'], 'https://example.com/image1.jpg')
        self.assertEqual(call_args[0]['Search Query'], 'test query')
    
    def test_calculate_total_cost(self):
        """Test total cost calculation."""
        # Mock usage stats
        self.openrouter_instance.usage_stats = {'total_cost': 0.05}
        self.apify_instance.usage_stats = {'estimated_cost': 0.02}
        
        imagefox = ImageFox()
        total_cost = imagefox._calculate_total_cost()
        
        self.assertEqual(total_cost, 0.07)
    
    def test_generate_statistics(self):
        """Test statistics generation."""
        # Mock component stats
        self.apify_instance.get_usage_stats.return_value = {'requests': 1}
        self.openrouter_instance.get_usage_stats.return_value = {'tokens': 100}
        self.processor_instance.get_stats.return_value = {'processed': 2}
        self.selector_instance.get_selection_stats.return_value = {'selections': 1}
        
        imagefox = ImageFox()
        stats = imagefox._generate_statistics()
        
        self.assertIn('apify', stats)
        self.assertIn('openrouter', stats)
        self.assertIn('image_processor', stats)
        self.assertIn('image_selector', stats)
        
        self.assertEqual(stats['apify']['requests'], 1)
        self.assertEqual(stats['openrouter']['tokens'], 100)
        self.assertEqual(stats['image_processor']['processed'], 2)
        self.assertEqual(stats['image_selector']['selections'], 1)
    
    def test_update_stats(self):
        """Test internal statistics updates."""
        imagefox = ImageFox()
        
        result = WorkflowResult(
            search_query="test",
            total_found=10,
            processed_count=8,
            selected_count=3,
            selected_images=[],
            processing_time=5.0,
            total_cost=0.1,
            errors=["error1", "error2"],
            statistics={},
            created_at="2023-01-01T12:00:00"
        )
        
        imagefox._update_stats(result)
        
        self.assertEqual(imagefox.stats['searches_performed'], 1)
        self.assertEqual(imagefox.stats['images_processed'], 8)
        self.assertEqual(imagefox.stats['images_selected'], 3)
        self.assertEqual(imagefox.stats['total_processing_time'], 5.0)
        self.assertEqual(imagefox.stats['total_cost'], 0.1)
        self.assertEqual(imagefox.stats['errors_count'], 2)
    
    def test_get_stats(self):
        """Test statistics retrieval."""
        imagefox = ImageFox()
        imagefox.stats['test_key'] = 'test_value'
        
        stats = imagefox.get_stats()
        
        self.assertEqual(stats['test_key'], 'test_value')
        # Ensure it's a copy, not reference
        stats['new_key'] = 'new_value'
        self.assertNotIn('new_key', imagefox.stats)
    
    def test_clear_cache(self):
        """Test cache clearing."""
        self.apify_instance.clear_cache = MagicMock()
        self.vision_instance.clear_cache = MagicMock()
        self.selector_instance.clear_cache = MagicMock()
        
        imagefox = ImageFox()
        imagefox.clear_cache()
        
        self.apify_instance.clear_cache.assert_called_once()
        self.vision_instance.clear_cache.assert_called_once()
        self.selector_instance.clear_cache.assert_called_once()
    
    async def test_cleanup(self):
        """Test resource cleanup."""
        # Mock processor exit
        self.processor_instance.__aexit__ = AsyncMock()
        
        imagefox = ImageFox()
        await imagefox.cleanup()
        
        # Should attempt to exit processor
        self.processor_instance.__aexit__.assert_called_once_with(None, None, None)


if __name__ == '__main__':
    # Run async tests with asyncio
    def async_test(f):
        def wrapper(*args, **kwargs):
            return asyncio.run(f(*args, **kwargs))
        return wrapper
    
    # Apply async wrapper to async test methods
    for name in dir(TestImageFox):
        if name.startswith('test_') and 'async' in name:
            method = getattr(TestImageFox, name)
            setattr(TestImageFox, name, async_test(method))
    
    unittest.main()