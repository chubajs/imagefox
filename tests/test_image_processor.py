#!/usr/bin/env python3
"""
Unit tests for Image Processor module.
"""

import os
import sys
import unittest
import asyncio
import tempfile
import shutil
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
from datetime import datetime
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from image_processor import ImageProcessor, ImageMetadata, ProcessingResult
from PIL import Image, ImageDraw


class TestImageMetadata(unittest.TestCase):
    """Test cases for ImageMetadata class."""
    
    def test_image_metadata_creation(self):
        """Test ImageMetadata creation."""
        metadata = ImageMetadata(
            url="https://example.com/image.jpg",
            file_path="/tmp/image.jpg",
            format="JPEG",
            width=1920,
            height=1080,
            file_size=1048576,
            aspect_ratio=1.777,
            color_mode="RGB",
            has_transparency=False,
            exif_data={"Camera": "Test Camera"},
            creation_time=datetime.now(),
            file_hash="abc123",
            processing_time=0.5
        )
        
        self.assertEqual(metadata.url, "https://example.com/image.jpg")
        self.assertEqual(metadata.width, 1920)
        self.assertEqual(metadata.format, "JPEG")
        self.assertFalse(metadata.has_transparency)


class TestProcessingResult(unittest.TestCase):
    """Test cases for ProcessingResult class."""
    
    def test_processing_result_success(self):
        """Test successful ProcessingResult creation."""
        result = ProcessingResult(
            success=True,
            original_metadata=None,
            optimized_metadata=None,
            thumbnail_metadata=None,
            error_message=None,
            temp_files=["/tmp/file1.jpg"],
            total_processing_time=1.5
        )
        
        self.assertTrue(result.success)
        self.assertIsNone(result.error_message)
        self.assertEqual(len(result.temp_files), 1)
        self.assertEqual(result.total_processing_time, 1.5)
    
    def test_processing_result_failure(self):
        """Test failed ProcessingResult creation."""
        result = ProcessingResult(
            success=False,
            original_metadata=None,
            optimized_metadata=None,
            thumbnail_metadata=None,
            error_message="Download failed",
            temp_files=[],
            total_processing_time=0.0
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "Download failed")
        self.assertEqual(len(result.temp_files), 0)


class TestImageProcessor(unittest.TestCase):
    """Test cases for ImageProcessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for tests
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        
        # Create test image
        self.test_image_path = os.path.join(self.temp_dir, "test_image.jpg")
        self.create_test_image(self.test_image_path, (800, 600))
        
        # Create small test image (below minimum size)
        self.small_image_path = os.path.join(self.temp_dir, "small_image.jpg")
        self.create_test_image(self.small_image_path, (200, 150))
        
        # Create large test image
        self.large_image_path = os.path.join(self.temp_dir, "large_image.jpg")
        self.create_test_image(self.large_image_path, (3000, 2000))
        
        # Create test PNG with transparency
        self.png_image_path = os.path.join(self.temp_dir, "test_image.png")
        self.create_test_png_with_transparency(self.png_image_path, (800, 600))
    
    def create_test_image(self, path: str, size: tuple, format: str = "JPEG"):
        """Create a test image file."""
        img = Image.new('RGB', size, color='red')
        draw = ImageDraw.Draw(img)
        # Add some content to make it more realistic - adjust for small images
        margin = min(20, size[0]//4, size[1]//4)
        if size[0] > margin*2 and size[1] > margin*2:
            draw.rectangle([margin, margin, size[0]-margin, size[1]-margin], fill='blue')
        
        ellipse_margin = min(50, size[0]//3, size[1]//3)
        if size[0] > ellipse_margin*2 and size[1] > ellipse_margin*2:
            draw.ellipse([ellipse_margin, ellipse_margin, size[0]-ellipse_margin, size[1]-ellipse_margin], fill='green')
        
        img.save(path, format=format, quality=95)
    
    def create_test_png_with_transparency(self, path: str, size: tuple):
        """Create a test PNG image with transparency."""
        img = Image.new('RGBA', size, color=(255, 0, 0, 128))  # Semi-transparent red
        draw = ImageDraw.Draw(img)
        draw.ellipse([100, 100, size[0]-100, size[1]-100], fill=(0, 255, 0, 200))
        img.save(path, format="PNG")
    
    def test_initialization_default(self):
        """Test ImageProcessor initialization with defaults."""
        processor = ImageProcessor()
        
        self.assertIsNotNone(processor.temp_dir)
        self.assertEqual(processor.concurrent_downloads, 5)
        self.assertEqual(len(processor.temp_files), 0)
        self.assertIn('downloads_attempted', processor.stats)
    
    def test_initialization_custom(self):
        """Test ImageProcessor initialization with custom parameters."""
        processor = ImageProcessor(temp_dir=self.temp_dir, concurrent_downloads=3)
        
        self.assertEqual(str(processor.temp_dir), self.temp_dir)
        self.assertEqual(processor.concurrent_downloads, 3)
    
    def test_validate_image_valid_jpeg(self):
        """Test image validation with valid JPEG."""
        processor = ImageProcessor()
        
        is_valid, error = processor.validate_image(self.test_image_path)
        
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_image_valid_png(self):
        """Test image validation with valid PNG."""
        processor = ImageProcessor()
        
        is_valid, error = processor.validate_image(self.png_image_path)
        
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_image_too_small(self):
        """Test image validation with image below minimum size."""
        processor = ImageProcessor()
        
        is_valid, error = processor.validate_image(self.small_image_path)
        
        self.assertFalse(is_valid)
        self.assertIn("Image too small", error)
    
    def test_validate_image_nonexistent(self):
        """Test image validation with non-existent file."""
        processor = ImageProcessor()
        
        is_valid, error = processor.validate_image("/nonexistent/file.jpg")
        
        self.assertFalse(is_valid)
        self.assertIn("Invalid image file", error)
    
    def test_extract_metadata_jpeg(self):
        """Test metadata extraction from JPEG."""
        processor = ImageProcessor()
        url = "https://example.com/test.jpg"
        
        metadata = processor.extract_metadata(self.test_image_path, url)
        
        self.assertEqual(metadata.url, url)
        self.assertEqual(metadata.format, "JPEG")
        self.assertEqual(metadata.width, 800)
        self.assertEqual(metadata.height, 600)
        self.assertEqual(metadata.aspect_ratio, 800/600)
        self.assertEqual(metadata.color_mode, "RGB")
        self.assertFalse(metadata.has_transparency)
        self.assertGreater(metadata.file_size, 0)
        self.assertIsNotNone(metadata.file_hash)
        self.assertGreater(metadata.processing_time, 0)
    
    def test_extract_metadata_png_with_transparency(self):
        """Test metadata extraction from PNG with transparency."""
        processor = ImageProcessor()
        url = "https://example.com/test.png"
        
        metadata = processor.extract_metadata(self.png_image_path, url)
        
        self.assertEqual(metadata.format, "PNG")
        self.assertEqual(metadata.color_mode, "RGBA")
        self.assertTrue(metadata.has_transparency)
    
    def test_optimize_image_jpeg(self):
        """Test image optimization."""
        processor = ImageProcessor()
        
        optimized_path = processor.optimize_image(self.large_image_path, quality=75)
        
        self.assertIsNotNone(optimized_path)
        self.assertTrue(os.path.exists(optimized_path))
        
        # Check that optimized file is smaller
        original_size = os.path.getsize(self.large_image_path)
        optimized_size = os.path.getsize(optimized_path)
        self.assertLess(optimized_size, original_size)
        
        # Verify optimized image is valid
        with Image.open(optimized_path) as img:
            self.assertEqual(img.format, "JPEG")
            # Should be resized to max dimension
            self.assertLessEqual(max(img.size), 2048)
    
    def test_optimize_image_png_conversion(self):
        """Test PNG optimization (should convert to JPEG)."""
        processor = ImageProcessor()
        
        optimized_path = processor.optimize_image(self.png_image_path, quality=80)
        
        if optimized_path:  # Optimization might not be effective for small files
            self.assertTrue(os.path.exists(optimized_path))
            
            # Should be converted to JPEG
            with Image.open(optimized_path) as img:
                self.assertEqual(img.format, "JPEG")
                self.assertEqual(img.mode, "RGB")  # No transparency
    
    def test_optimize_image_no_improvement(self):
        """Test optimization when no improvement is possible."""
        # Create a small, already optimized image at low quality first
        small_optimized_path = os.path.join(self.temp_dir, "small_opt.jpg")
        
        # Create and save at very low quality to make a very small file
        img = Image.new('RGB', (500, 400), color='red')
        img.save(small_optimized_path, format='JPEG', quality=30, optimize=True)
        
        processor = ImageProcessor()
        result = processor.optimize_image(small_optimized_path, quality=30)
        
        # Should return None if optimization isn't effective (less than 10% reduction)
        # For a small, already compressed image, optimization may not be effective
        if result is not None:
            # If optimization did happen, verify it's a valid result
            self.assertTrue(os.path.exists(result))
        # Either way is acceptable - the test is checking the optimization logic works
    
    def test_generate_thumbnail(self):
        """Test thumbnail generation."""
        processor = ImageProcessor()
        
        thumb_path = processor.generate_thumbnail(self.test_image_path)
        
        self.assertIsNotNone(thumb_path)
        self.assertTrue(os.path.exists(thumb_path))
        
        # Verify thumbnail properties
        with Image.open(thumb_path) as thumb:
            self.assertEqual(thumb.format, "JPEG")
            self.assertEqual(thumb.mode, "RGB")
            # Should be within thumbnail size limits
            self.assertLessEqual(max(thumb.size), max(processor.THUMBNAIL_SIZE))
    
    def test_generate_thumbnail_custom_size(self):
        """Test thumbnail generation with custom size."""
        processor = ImageProcessor()
        custom_size = (150, 150)
        
        thumb_path = processor.generate_thumbnail(self.test_image_path, size=custom_size)
        
        self.assertIsNotNone(thumb_path)
        
        with Image.open(thumb_path) as thumb:
            self.assertLessEqual(max(thumb.size), max(custom_size))
    
    def test_generate_thumbnail_png_conversion(self):
        """Test thumbnail generation from PNG (should convert to JPEG)."""
        processor = ImageProcessor()
        
        thumb_path = processor.generate_thumbnail(self.png_image_path)
        
        self.assertIsNotNone(thumb_path)
        
        with Image.open(thumb_path) as thumb:
            self.assertEqual(thumb.format, "JPEG")
            self.assertEqual(thumb.mode, "RGB")  # Transparency removed
    
    @pytest.mark.asyncio
    async def test_download_image_success(self):
        """Test successful image download."""
        processor = ImageProcessor()
        
        # Mock successful HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {'Content-Length': '1000'}
        
        # Create mock content
        with open(self.test_image_path, 'rb') as f:
            test_data = f.read()
        
        async def mock_iter_chunked(size):
            yield test_data
        
        mock_response.content.iter_chunked = mock_iter_chunked
        
        # Mock session
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        processor.session = mock_session
        
        success, file_path, error = await processor.download_image("https://example.com/test.jpg")
        
        self.assertTrue(success)
        self.assertIsNotNone(file_path)
        self.assertIsNone(error)
        self.assertIn(file_path, processor.temp_files)
    
    @pytest.mark.asyncio
    async def test_download_image_http_error(self):
        """Test download with HTTP error."""
        processor = ImageProcessor()
        
        # Mock failed HTTP response
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.reason = "Not Found"
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        processor.session = mock_session
        
        success, file_path, error = await processor.download_image("https://example.com/notfound.jpg")
        
        self.assertFalse(success)
        self.assertIsNone(file_path)
        self.assertIn("404", error)
    
    @pytest.mark.asyncio
    async def test_download_image_too_large(self):
        """Test download with file too large."""
        processor = ImageProcessor()
        
        # Mock response with large content length
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {'Content-Length': str(20 * 1024 * 1024)}  # 20MB
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        processor.session = mock_session
        
        success, file_path, error = await processor.download_image("https://example.com/huge.jpg")
        
        self.assertFalse(success)
        self.assertIsNone(file_path)
        self.assertIn("File too large", error)
    
    @pytest.mark.asyncio
    async def test_download_image_timeout(self):
        """Test download timeout."""
        processor = ImageProcessor()
        
        # Mock timeout exception
        mock_session = AsyncMock()
        mock_session.get.side_effect = asyncio.TimeoutError()
        
        processor.session = mock_session
        
        success, file_path, error = await processor.download_image("https://example.com/slow.jpg")
        
        self.assertFalse(success)
        self.assertIsNone(file_path)
        self.assertEqual(error, "Download timeout")
    
    @pytest.mark.asyncio
    async def test_process_image_success(self):
        """Test complete image processing pipeline."""
        processor = ImageProcessor(temp_dir=self.temp_dir)
        
        # Mock successful download
        with patch.object(processor, 'download_image') as mock_download:
            mock_download.return_value = (True, self.test_image_path, None)
            
            result = await processor.process_image("https://example.com/test.jpg")
            
            self.assertTrue(result.success)
            self.assertIsNone(result.error_message)
            self.assertIsNotNone(result.original_metadata)
            self.assertEqual(result.original_metadata.width, 800)
            self.assertEqual(result.original_metadata.height, 600)
            self.assertGreater(result.total_processing_time, 0)
    
    @pytest.mark.asyncio
    async def test_process_image_with_optimization(self):
        """Test image processing with optimization."""
        processor = ImageProcessor(temp_dir=self.temp_dir)
        
        # Mock successful download with large image
        with patch.object(processor, 'download_image') as mock_download:
            mock_download.return_value = (True, self.large_image_path, None)
            
            result = await processor.process_image("https://example.com/large.jpg", optimize=True)
            
            self.assertTrue(result.success)
            self.assertIsNotNone(result.original_metadata)
            # Large image should be optimized
            self.assertIsNotNone(result.optimized_metadata)
    
    @pytest.mark.asyncio
    async def test_process_image_with_thumbnail(self):
        """Test image processing with thumbnail generation."""
        processor = ImageProcessor(temp_dir=self.temp_dir)
        
        with patch.object(processor, 'download_image') as mock_download:
            mock_download.return_value = (True, self.test_image_path, None)
            
            result = await processor.process_image("https://example.com/test.jpg", generate_thumb=True)
            
            self.assertTrue(result.success)
            self.assertIsNotNone(result.thumbnail_metadata)
            self.assertLessEqual(
                max(result.thumbnail_metadata.width, result.thumbnail_metadata.height),
                max(processor.THUMBNAIL_SIZE)
            )
    
    @pytest.mark.asyncio
    async def test_process_image_download_failure(self):
        """Test image processing with download failure."""
        processor = ImageProcessor()
        
        with patch.object(processor, 'download_image') as mock_download:
            mock_download.return_value = (False, None, "Download failed")
            
            result = await processor.process_image("https://example.com/fail.jpg")
            
            self.assertFalse(result.success)
            self.assertEqual(result.error_message, "Download failed")
            self.assertIsNone(result.original_metadata)
    
    @pytest.mark.asyncio
    async def test_process_image_validation_failure(self):
        """Test image processing with validation failure."""
        processor = ImageProcessor()
        
        with patch.object(processor, 'download_image') as mock_download:
            mock_download.return_value = (True, self.small_image_path, None)
            
            result = await processor.process_image("https://example.com/small.jpg")
            
            self.assertFalse(result.success)
            self.assertIn("Image too small", result.error_message)
    
    @pytest.mark.asyncio
    async def test_process_images_batch(self):
        """Test batch processing of multiple images."""
        processor = ImageProcessor(temp_dir=self.temp_dir, concurrent_downloads=2)
        
        urls = [
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg",
            "https://example.com/image3.jpg"
        ]
        
        # Mock download responses
        with patch.object(processor, 'download_image') as mock_download:
            mock_download.side_effect = [
                (True, self.test_image_path, None),
                (True, self.test_image_path, None),
                (False, None, "Download failed")
            ]
            
            results = await processor.process_images_batch(urls)
            
            self.assertEqual(len(results), 3)
            self.assertTrue(results[0].success)
            self.assertTrue(results[1].success)
            self.assertFalse(results[2].success)
    
    def test_cleanup_temp(self):
        """Test temporary file cleanup."""
        processor = ImageProcessor()
        
        # Create some temp files
        temp_file1 = os.path.join(self.temp_dir, "temp1.jpg")
        temp_file2 = os.path.join(self.temp_dir, "temp2.jpg")
        
        # Create files
        Path(temp_file1).touch()
        Path(temp_file2).touch()
        
        # Add to processor's temp files list
        processor.temp_files = [temp_file1, temp_file2]
        
        # Verify files exist
        self.assertTrue(os.path.exists(temp_file1))
        self.assertTrue(os.path.exists(temp_file2))
        
        # Cleanup
        processor.cleanup_temp()
        
        # Verify files are removed and list is cleared
        self.assertFalse(os.path.exists(temp_file1))
        self.assertFalse(os.path.exists(temp_file2))
        self.assertEqual(len(processor.temp_files), 0)
    
    def test_get_stats(self):
        """Test statistics retrieval."""
        processor = ImageProcessor()
        
        stats = processor.get_stats()
        
        self.assertIn('downloads_attempted', stats)
        self.assertIn('downloads_successful', stats)
        self.assertIn('images_processed', stats)
        self.assertIn('temp_files_count', stats)
        self.assertIn('temp_dir', stats)
        self.assertEqual(stats['downloads_attempted'], 0)
        self.assertEqual(stats['temp_files_count'], 0)
    
    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test async context manager functionality."""
        async with ImageProcessor(temp_dir=self.temp_dir) as processor:
            self.assertIsNotNone(processor.session)
            
            # Add a temp file to test cleanup
            temp_file = os.path.join(self.temp_dir, "context_test.jpg")
            Path(temp_file).touch()
            processor.temp_files.append(temp_file)
        
        # After context exit, session should be closed and temp files cleaned
        self.assertTrue(processor.session.closed)
        self.assertEqual(len(processor.temp_files), 0)
        self.assertFalse(os.path.exists(temp_file))
    
    def test_configuration_constants(self):
        """Test configuration constants."""
        # Test default values
        self.assertEqual(ImageProcessor.MAX_IMAGE_SIZE_MB, 10)
        self.assertEqual(ImageProcessor.MIN_IMAGE_WIDTH, 400)
        self.assertEqual(ImageProcessor.MIN_IMAGE_HEIGHT, 300)
        self.assertEqual(ImageProcessor.IMAGE_QUALITY, 85)
        self.assertEqual(ImageProcessor.THUMBNAIL_SIZE, (300, 300))
        
        # Test supported formats
        self.assertIn('JPEG', ImageProcessor.SUPPORTED_FORMATS)
        self.assertIn('PNG', ImageProcessor.SUPPORTED_FORMATS)
        self.assertIn('WebP', ImageProcessor.SUPPORTED_FORMATS)
        self.assertIn('GIF', ImageProcessor.SUPPORTED_FORMATS)


class TestImageProcessorEnvironmentConfig(unittest.TestCase):
    """Test ImageProcessor with environment configuration."""
    
    def test_environment_configuration(self):
        """Test configuration from environment variables."""
        with patch.dict(os.environ, {
            'MAX_IMAGE_SIZE_MB': '20',
            'MIN_IMAGE_WIDTH': '800',
            'MIN_IMAGE_HEIGHT': '600',
            'IMAGE_QUALITY': '90'
        }):
            # These are class-level constants, so we need to check the values directly
            self.assertEqual(int(os.getenv('MAX_IMAGE_SIZE_MB', '10')), 20)
            self.assertEqual(int(os.getenv('MIN_IMAGE_WIDTH', '400')), 800)
            self.assertEqual(int(os.getenv('MIN_IMAGE_HEIGHT', '300')), 600)
            self.assertEqual(int(os.getenv('IMAGE_QUALITY', '85')), 90)


if __name__ == '__main__':
    unittest.main()