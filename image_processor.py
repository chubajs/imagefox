#!/usr/bin/env python3
"""
Image Processor module for ImageFox.

This module handles downloading, validation, optimization, and processing
of images with concurrent operations and comprehensive metadata extraction.
"""

import os
import io
import asyncio
import aiohttp
import tempfile
import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import sentry_sdk
from sentry_sdk import capture_exception

try:
    from PIL import Image, ImageOps, ExifTags
    from PIL.ExifTags import TAGS
except ImportError:
    raise ImportError("PIL (Pillow) is required for image processing. Install with: pip install Pillow")

logger = logging.getLogger(__name__)


@dataclass
class ImageMetadata:
    """Metadata extracted from an image."""
    url: str
    file_path: Optional[str]
    format: str
    width: int
    height: int
    file_size: int
    aspect_ratio: float
    color_mode: str
    has_transparency: bool
    exif_data: Dict[str, Any]
    creation_time: Optional[datetime]
    file_hash: str
    processing_time: float


@dataclass
class ProcessingResult:
    """Result from image processing operation."""
    success: bool
    original_metadata: Optional[ImageMetadata]
    optimized_metadata: Optional[ImageMetadata]
    thumbnail_metadata: Optional[ImageMetadata]
    error_message: Optional[str]
    temp_files: List[str]
    total_processing_time: float


class ImageProcessor:
    """Image processor with downloading, validation, and optimization capabilities."""
    
    # Configuration constants
    MAX_IMAGE_SIZE_MB = int(os.getenv('MAX_IMAGE_SIZE_MB', '10'))
    MIN_IMAGE_WIDTH = int(os.getenv('MIN_IMAGE_WIDTH', '400'))
    MIN_IMAGE_HEIGHT = int(os.getenv('MIN_IMAGE_HEIGHT', '300'))
    IMAGE_QUALITY = int(os.getenv('IMAGE_QUALITY', '85'))
    THUMBNAIL_SIZE = (300, 300)
    
    # Supported formats
    SUPPORTED_FORMATS = {'JPEG', 'JPG', 'PNG', 'WebP', 'GIF', 'BMP', 'TIFF'}
    
    def __init__(self, temp_dir: Optional[str] = None, concurrent_downloads: int = 5):
        """
        Initialize Image Processor.
        
        Args:
            temp_dir: Directory for temporary files (uses system temp if None)
            concurrent_downloads: Maximum concurrent downloads
        """
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir()) / "imagefox"
        self.temp_dir.mkdir(exist_ok=True)
        
        self.concurrent_downloads = concurrent_downloads
        self.session = None
        self.temp_files = []
        
        # Processing statistics
        self.stats = {
            'downloads_attempted': 0,
            'downloads_successful': 0,
            'images_processed': 0,
            'images_optimized': 0,
            'thumbnails_generated': 0,
            'total_bytes_downloaded': 0,
            'total_processing_time': 0.0
        }
        
        logger.info(f"ImageProcessor initialized with temp_dir={self.temp_dir}, "
                   f"concurrent_downloads={concurrent_downloads}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'ImageFox/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
        self.cleanup_temp()
    
    async def download_image(self, url: str, max_size_mb: Optional[int] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Download image from URL.
        
        Args:
            url: Image URL to download
            max_size_mb: Maximum file size in MB (uses default if None)
        
        Returns:
            Tuple of (success, file_path, error_message)
        """
        start_time = datetime.now()
        self.stats['downloads_attempted'] += 1
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=30),
                    headers={'User-Agent': 'ImageFox/1.0'}
                )
            
            max_size_bytes = (max_size_mb or self.MAX_IMAGE_SIZE_MB) * 1024 * 1024
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    return False, None, f"HTTP {response.status}: {response.reason}"
                
                # Check content length
                content_length = response.headers.get('Content-Length')
                if content_length and int(content_length) > max_size_bytes:
                    return False, None, f"File too large: {int(content_length)} bytes"
                
                # Generate temp file path
                file_hash = hashlib.md5(url.encode()).hexdigest()[:12]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_path = self.temp_dir / f"image_{timestamp}_{file_hash}"
                
                # Download with size checking
                downloaded_size = 0
                with open(temp_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        downloaded_size += len(chunk)
                        if downloaded_size > max_size_bytes:
                            temp_path.unlink()
                            return False, None, f"File too large during download: {downloaded_size} bytes"
                        f.write(chunk)
                
                self.temp_files.append(str(temp_path))
                self.stats['downloads_successful'] += 1
                self.stats['total_bytes_downloaded'] += downloaded_size
                
                processing_time = (datetime.now() - start_time).total_seconds()
                logger.debug(f"Downloaded {url} ({downloaded_size} bytes) in {processing_time:.2f}s")
                
                return True, str(temp_path), None
                
        except asyncio.TimeoutError:
            return False, None, "Download timeout"
        except Exception as e:
            logger.error(f"Download failed for {url}: {str(e)}")
            capture_exception(e)
            return False, None, str(e)
    
    def validate_image(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate image format and integrity.
        
        Args:
            file_path: Path to image file
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            with Image.open(file_path) as img:
                # Verify it's a valid image
                img.verify()
                
                # Check format
                if img.format not in self.SUPPORTED_FORMATS:
                    return False, f"Unsupported format: {img.format}"
                
                # Reopen for size checking (verify() closes the image)
                with Image.open(file_path) as img2:
                    width, height = img2.size
                    
                    # Check minimum dimensions
                    if width < self.MIN_IMAGE_WIDTH or height < self.MIN_IMAGE_HEIGHT:
                        return False, f"Image too small: {width}x{height} (min: {self.MIN_IMAGE_WIDTH}x{self.MIN_IMAGE_HEIGHT})"
                    
                    # Check aspect ratio (avoid extremely narrow images)
                    aspect_ratio = max(width, height) / min(width, height)
                    if aspect_ratio > 10:
                        return False, f"Extreme aspect ratio: {aspect_ratio:.1f}"
                
                return True, None
                
        except Exception as e:
            return False, f"Invalid image file: {str(e)}"
    
    def extract_metadata(self, file_path: str, url: str) -> ImageMetadata:
        """
        Extract comprehensive metadata from image.
        
        Args:
            file_path: Path to image file
            url: Original URL of image
        
        Returns:
            ImageMetadata object
        """
        start_time = datetime.now()
        
        try:
            with Image.open(file_path) as img:
                # Basic metadata
                width, height = img.size
                file_size = os.path.getsize(file_path)
                aspect_ratio = width / height
                
                # Color mode and transparency
                color_mode = img.mode
                has_transparency = (
                    'transparency' in img.info or
                    color_mode in ('RGBA', 'LA') or
                    (color_mode == 'P' and 'transparency' in img.info)
                )
                
                # File hash
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
                
                # EXIF data
                exif_data = {}
                creation_time = None
                
                if hasattr(img, '_getexif') and img._getexif():
                    exif_dict = img._getexif()
                    for tag_id, value in exif_dict.items():
                        tag = TAGS.get(tag_id, tag_id)
                        try:
                            # Convert bytes to string if needed
                            if isinstance(value, bytes):
                                value = value.decode('utf-8', errors='ignore')
                            exif_data[tag] = value
                            
                            # Extract creation time
                            if tag in ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized']:
                                try:
                                    creation_time = datetime.strptime(str(value), '%Y:%m:%d %H:%M:%S')
                                except:
                                    pass
                        except:
                            # Skip problematic EXIF data
                            continue
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                return ImageMetadata(
                    url=url,
                    file_path=file_path,
                    format=img.format,
                    width=width,
                    height=height,
                    file_size=file_size,
                    aspect_ratio=aspect_ratio,
                    color_mode=color_mode,
                    has_transparency=has_transparency,
                    exif_data=exif_data,
                    creation_time=creation_time,
                    file_hash=file_hash,
                    processing_time=processing_time
                )
                
        except Exception as e:
            logger.error(f"Failed to extract metadata from {file_path}: {str(e)}")
            capture_exception(e)
            raise
    
    def optimize_image(self, file_path: str, quality: Optional[int] = None) -> Optional[str]:
        """
        Optimize image size and quality.
        
        Args:
            file_path: Path to original image
            quality: JPEG quality (uses default if None)
        
        Returns:
            Path to optimized image or None if optimization failed
        """
        start_time = datetime.now()
        quality = quality or self.IMAGE_QUALITY
        
        try:
            with Image.open(file_path) as img:
                # Convert to RGB if necessary (for JPEG optimization)
                if img.mode in ('RGBA', 'P', 'LA'):
                    # Create white background for transparency
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                
                # Auto-orient based on EXIF
                img = ImageOps.exif_transpose(img)
                
                # Calculate optimization - reduce size if too large
                max_dimension = 2048
                if max(img.size) > max_dimension:
                    img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                
                # Generate optimized file path
                original_path = Path(file_path)
                optimized_path = original_path.parent / f"{original_path.stem}_optimized{original_path.suffix}"
                
                # Save optimized version
                save_kwargs = {
                    'format': 'JPEG',
                    'quality': quality,
                    'optimize': True,
                    'progressive': True
                }
                
                img.save(optimized_path, **save_kwargs)
                
                self.temp_files.append(str(optimized_path))
                self.stats['images_optimized'] += 1
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                # Check if optimization was effective
                original_size = os.path.getsize(file_path)
                optimized_size = os.path.getsize(optimized_path)
                
                if optimized_size < original_size * 0.9:  # At least 10% reduction
                    logger.debug(f"Optimized image: {original_size} -> {optimized_size} bytes "
                               f"({100 * (1 - optimized_size/original_size):.1f}% reduction) "
                               f"in {processing_time:.2f}s")
                    return str(optimized_path)
                else:
                    # Optimization not effective, remove file
                    optimized_path.unlink()
                    self.temp_files.remove(str(optimized_path))
                    return None
                
        except Exception as e:
            logger.error(f"Failed to optimize image {file_path}: {str(e)}")
            capture_exception(e)
            return None
    
    def generate_thumbnail(self, file_path: str, size: Optional[Tuple[int, int]] = None) -> Optional[str]:
        """
        Generate thumbnail of image.
        
        Args:
            file_path: Path to original image
            size: Thumbnail size (uses default if None)
        
        Returns:
            Path to thumbnail or None if generation failed
        """
        start_time = datetime.now()
        size = size or self.THUMBNAIL_SIZE
        
        try:
            with Image.open(file_path) as img:
                # Auto-orient based on EXIF
                img = ImageOps.exif_transpose(img)
                
                # Create thumbnail maintaining aspect ratio
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Convert to RGB for JPEG
                if img.mode in ('RGBA', 'P', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                
                # Generate thumbnail path
                original_path = Path(file_path)
                thumb_path = original_path.parent / f"{original_path.stem}_thumb.jpg"
                
                # Save thumbnail
                img.save(thumb_path, format='JPEG', quality=80, optimize=True)
                
                self.temp_files.append(str(thumb_path))
                self.stats['thumbnails_generated'] += 1
                
                processing_time = (datetime.now() - start_time).total_seconds()
                logger.debug(f"Generated thumbnail {size} in {processing_time:.2f}s")
                
                return str(thumb_path)
                
        except Exception as e:
            logger.error(f"Failed to generate thumbnail for {file_path}: {str(e)}")
            capture_exception(e)
            return None
    
    async def process_image(
        self,
        url: str,
        optimize: bool = True,
        generate_thumb: bool = True
    ) -> ProcessingResult:
        """
        Complete image processing pipeline.
        
        Args:
            url: Image URL to process
            optimize: Whether to optimize the image
            generate_thumb: Whether to generate thumbnail
        
        Returns:
            ProcessingResult with all metadata and file paths
        """
        start_time = datetime.now()
        
        try:
            # Download image
            success, file_path, error = await self.download_image(url)
            if not success:
                return ProcessingResult(
                    success=False,
                    original_metadata=None,
                    optimized_metadata=None,
                    thumbnail_metadata=None,
                    error_message=error,
                    temp_files=[],
                    total_processing_time=0.0
                )
            
            # Validate image
            is_valid, validation_error = self.validate_image(file_path)
            if not is_valid:
                return ProcessingResult(
                    success=False,
                    original_metadata=None,
                    optimized_metadata=None,
                    thumbnail_metadata=None,
                    error_message=validation_error,
                    temp_files=[file_path],
                    total_processing_time=0.0
                )
            
            # Extract metadata
            original_metadata = self.extract_metadata(file_path, url)
            optimized_metadata = None
            thumbnail_metadata = None
            
            # Optimize if requested
            optimized_path = None
            if optimize:
                optimized_path = self.optimize_image(file_path)
                if optimized_path:
                    optimized_metadata = self.extract_metadata(optimized_path, url)
            
            # Generate thumbnail if requested
            thumbnail_path = None
            if generate_thumb:
                thumbnail_path = self.generate_thumbnail(
                    optimized_path if optimized_path else file_path
                )
                if thumbnail_path:
                    thumbnail_metadata = self.extract_metadata(thumbnail_path, url)
            
            self.stats['images_processed'] += 1
            total_processing_time = (datetime.now() - start_time).total_seconds()
            self.stats['total_processing_time'] += total_processing_time
            
            return ProcessingResult(
                success=True,
                original_metadata=original_metadata,
                optimized_metadata=optimized_metadata,
                thumbnail_metadata=thumbnail_metadata,
                error_message=None,
                temp_files=self.temp_files.copy(),
                total_processing_time=total_processing_time
            )
            
        except Exception as e:
            logger.error(f"Failed to process image {url}: {str(e)}")
            capture_exception(e)
            total_processing_time = (datetime.now() - start_time).total_seconds()
            
            return ProcessingResult(
                success=False,
                original_metadata=None,
                optimized_metadata=None,
                thumbnail_metadata=None,
                error_message=str(e),
                temp_files=self.temp_files.copy(),
                total_processing_time=total_processing_time
            )
    
    async def process_images_batch(
        self,
        urls: List[str],
        optimize: bool = True,
        generate_thumb: bool = True
    ) -> List[ProcessingResult]:
        """
        Process multiple images concurrently.
        
        Args:
            urls: List of image URLs to process
            optimize: Whether to optimize images
            generate_thumb: Whether to generate thumbnails
        
        Returns:
            List of ProcessingResults
        """
        semaphore = asyncio.Semaphore(self.concurrent_downloads)
        
        async def process_single(url: str) -> ProcessingResult:
            async with semaphore:
                return await self.process_image(url, optimize, generate_thumb)
        
        tasks = [process_single(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(ProcessingResult(
                    success=False,
                    original_metadata=None,
                    optimized_metadata=None,
                    thumbnail_metadata=None,
                    error_message=str(result),
                    temp_files=[],
                    total_processing_time=0.0
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def cleanup_temp(self):
        """Clean up all temporary files."""
        cleaned = 0
        for temp_file in self.temp_files:
            try:
                Path(temp_file).unlink(missing_ok=True)
                cleaned += 1
            except Exception as e:
                logger.warning(f"Failed to clean up {temp_file}: {str(e)}")
        
        if cleaned > 0:
            logger.debug(f"Cleaned up {cleaned} temporary files")
        
        self.temp_files.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            **self.stats,
            'temp_files_count': len(self.temp_files),
            'temp_dir': str(self.temp_dir)
        }