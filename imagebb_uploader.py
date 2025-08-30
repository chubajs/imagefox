#!/usr/bin/env python3
"""
ImageBB API client for ImageFox.

This module provides a robust client for uploading images to ImageBB
for CDN hosting and image distribution.
"""

import os
import base64
import time
import logging
from typing import Dict, Optional, Union, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import sentry_sdk
from sentry_sdk import capture_exception

logger = logging.getLogger(__name__)


@dataclass
class UploadResult:
    """Result from ImageBB upload operation."""
    id: str
    title: str
    url_viewer: str
    url: str
    display_url: str
    width: int
    height: int
    size: int
    time: str
    expiration: str
    filename: str
    mime_type: str
    delete_url: str
    thumbnail_url: str
    medium_url: str
    success: bool
    upload_time: float


class ImageBBUploader:
    """Client for ImageBB upload API."""
    
    API_BASE_URL = "https://api.imgbb.com/1"
    MAX_FILE_SIZE = 32 * 1024 * 1024  # 32MB free tier limit
    
    SUPPORTED_FORMATS = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg'
    }
    
    MIME_TYPES = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif', 
        '.bmp': 'image/bmp',
        '.webp': 'image/webp',
        '.tiff': 'image/tiff',
        '.svg': 'image/svg+xml'
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize ImageBB uploader.
        
        Args:
            api_key: ImageBB API key. If not provided, reads from environment.
        
        Raises:
            ValueError: If API key is not provided or found in environment.
        """
        self.api_key = api_key or os.getenv('IMGBB_API_KEY')
        if not self.api_key:
            raise ValueError("IMGBB_API_KEY not provided or found in environment")
        
        # Rate limiting configuration
        self.rate_limit = int(os.getenv('IMAGEBB_RATE_LIMIT', '10'))
        self.requests_per_minute = []
        
        # Upload tracking
        self.upload_stats = {
            'total_uploads': 0,
            'successful_uploads': 0,
            'failed_uploads': 0,
            'total_size_uploaded': 0,
            'total_upload_time': 0.0
        }
        
        # Setup session
        self.session = self._create_session()
        
        logger.info("ImageBB uploader initialized")
    
    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry strategy."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=int(os.getenv('RETRY_ATTEMPTS', '3')),
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting to prevent API throttling."""
        current_time = time.time()
        minute_ago = current_time - 60
        
        # Remove requests older than 1 minute
        self.requests_per_minute = [
            req_time for req_time in self.requests_per_minute 
            if req_time > minute_ago
        ]
        
        # Check if we've hit the rate limit
        if len(self.requests_per_minute) >= self.rate_limit:
            # Calculate sleep time
            oldest_request = min(self.requests_per_minute)
            sleep_time = 60 - (current_time - oldest_request) + 0.1
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        # Record this request
        self.requests_per_minute.append(current_time)
    
    def validate_image(self, file_path: str) -> bool:
        """
        Validate image file before upload.
        
        Args:
            file_path: Path to image file
        
        Returns:
            True if valid, False otherwise
        
        Raises:
            ValueError: If validation fails with specific reason
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise ValueError(f"File does not exist: {file_path}")
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.MAX_FILE_SIZE:
                size_mb = file_size / (1024 * 1024)
                raise ValueError(f"File too large: {size_mb:.2f}MB (max: 32MB)")
            
            if file_size == 0:
                raise ValueError("File is empty")
            
            # Check file extension
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in self.SUPPORTED_FORMATS:
                supported = ', '.join(self.SUPPORTED_FORMATS)
                raise ValueError(f"Unsupported format: {file_ext}. Supported: {supported}")
            
            # Try to read file to ensure it's accessible
            with open(file_path, 'rb') as f:
                f.read(1)  # Read one byte to test accessibility
            
            return True
            
        except (OSError, IOError) as e:
            raise ValueError(f"File access error: {e}")
    
    def validate_base64_image(self, base64_data: str, max_size: Optional[int] = None) -> bool:
        """
        Validate base64 encoded image.
        
        Args:
            base64_data: Base64 encoded image string
            max_size: Optional max size override
        
        Returns:
            True if valid, False otherwise
        
        Raises:
            ValueError: If validation fails
        """
        try:
            # Remove data URI prefix if present
            if base64_data.startswith('data:'):
                base64_data = base64_data.split(',')[1]
            
            # Decode to check validity
            decoded_data = base64.b64decode(base64_data)
            data_size = len(decoded_data)
            
            # Check size
            max_allowed = max_size or self.MAX_FILE_SIZE
            if data_size > max_allowed:
                size_mb = data_size / (1024 * 1024)
                max_mb = max_allowed / (1024 * 1024)
                raise ValueError(f"Image too large: {size_mb:.2f}MB (max: {max_mb}MB)")
            
            if data_size == 0:
                raise ValueError("Image data is empty")
            
            return True
            
        except Exception as e:
            raise ValueError(f"Invalid base64 image data: {e}")
    
    def upload_file(
        self,
        file_path: str,
        name: Optional[str] = None,
        expiration: Optional[int] = None
    ) -> UploadResult:
        """
        Upload image file to ImageBB.
        
        Args:
            file_path: Path to image file
            name: Optional custom name for the image
            expiration: Optional expiration time in seconds (60-15552000)
        
        Returns:
            Upload result with URLs and metadata
        
        Raises:
            ValueError: If file validation fails
            Exception: If upload fails
        """
        # Validate image
        self.validate_image(file_path)
        
        # Encode to base64
        with open(file_path, 'rb') as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Use filename as default name
        if not name:
            name = os.path.splitext(os.path.basename(file_path))[0]
        
        return self.upload_base64(image_data, name, expiration)
    
    def upload_base64(
        self,
        base64_data: str,
        name: Optional[str] = None,
        expiration: Optional[int] = None
    ) -> UploadResult:
        """
        Upload base64 encoded image to ImageBB.
        
        Args:
            base64_data: Base64 encoded image string
            name: Optional custom name for the image
            expiration: Optional expiration time in seconds
        
        Returns:
            Upload result with URLs and metadata
        
        Raises:
            ValueError: If validation fails
            Exception: If upload fails
        """
        start_time = time.time()
        
        # Validate image data
        self.validate_base64_image(base64_data)
        
        # Remove data URI prefix if present
        if base64_data.startswith('data:'):
            base64_data = base64_data.split(',')[1]
        
        # Enforce rate limiting
        self._enforce_rate_limit()
        
        # Prepare request data
        data = {
            'key': self.api_key,
            'image': base64_data
        }
        
        if name:
            data['name'] = name
        
        if expiration:
            if not (60 <= expiration <= 15552000):  # 1 min to 180 days
                raise ValueError("Expiration must be between 60 and 15552000 seconds")
            data['expiration'] = str(expiration)
        
        try:
            # Make upload request
            response = self.session.post(
                f"{self.API_BASE_URL}/upload",
                data=data,
                timeout=int(os.getenv('REQUEST_TIMEOUT', '60'))
            )
            
            upload_time = time.time() - start_time
            
            # Parse response
            if response.status_code == 200:
                result_data = response.json()
                
                if result_data.get('success'):
                    result = self._parse_upload_response(result_data, upload_time)
                    self._track_upload_success(result)
                    return result
                else:
                    error_msg = result_data.get('error', {}).get('message', 'Upload failed')
                    raise Exception(f"Upload failed: {error_msg}")
            else:
                # Try to parse error response
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', f"HTTP {response.status_code}")
                except:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                
                raise Exception(f"Upload failed: {error_msg}")
                
        except requests.RequestException as e:
            self._track_upload_failure()
            logger.error(f"Error uploading to ImageBB: {e}")
            capture_exception(e)
            raise Exception(f"Upload request failed: {e}")
    
    def upload_url(
        self,
        image_url: str,
        name: Optional[str] = None,
        expiration: Optional[int] = None
    ) -> UploadResult:
        """
        Upload image from URL to ImageBB.
        
        Args:
            image_url: URL of image to upload
            name: Optional custom name for the image
            expiration: Optional expiration time in seconds
        
        Returns:
            Upload result with URLs and metadata
        
        Raises:
            Exception: If upload fails
        """
        start_time = time.time()
        
        # Enforce rate limiting
        self._enforce_rate_limit()
        
        # Prepare request data
        data = {
            'key': self.api_key,
            'image': image_url
        }
        
        if name:
            data['name'] = name
        
        if expiration:
            if not (60 <= expiration <= 15552000):
                raise ValueError("Expiration must be between 60 and 15552000 seconds")
            data['expiration'] = str(expiration)
        
        try:
            # Make upload request
            response = self.session.post(
                f"{self.API_BASE_URL}/upload",
                data=data,
                timeout=int(os.getenv('REQUEST_TIMEOUT', '60'))
            )
            
            upload_time = time.time() - start_time
            
            # Parse response
            if response.status_code == 200:
                result_data = response.json()
                
                if result_data.get('success'):
                    result = self._parse_upload_response(result_data, upload_time)
                    self._track_upload_success(result)
                    return result
                else:
                    error_msg = result_data.get('error', {}).get('message', 'Upload failed')
                    raise Exception(f"Upload failed: {error_msg}")
            else:
                response.raise_for_status()
                
        except requests.RequestException as e:
            self._track_upload_failure()
            logger.error(f"Error uploading URL to ImageBB: {e}")
            capture_exception(e)
            raise Exception(f"Upload request failed: {e}")
    
    def _parse_upload_response(self, response_data: Dict, upload_time: float) -> UploadResult:
        """
        Parse ImageBB upload response.
        
        Args:
            response_data: Raw API response
            upload_time: Time taken for upload
        
        Returns:
            Structured upload result
        """
        data = response_data['data']
        image_info = data.get('image', {})
        thumb_info = data.get('thumb', {})
        medium_info = data.get('medium', {})
        
        result = UploadResult(
            id=data.get('id', ''),
            title=data.get('title', ''),
            url_viewer=data.get('url_viewer', ''),
            url=data.get('url', ''),
            display_url=data.get('display_url', ''),
            width=int(data.get('width', 0)),
            height=int(data.get('height', 0)),
            size=int(data.get('size', 0)),
            time=data.get('time', ''),
            expiration=data.get('expiration', '0'),
            filename=image_info.get('filename', ''),
            mime_type=image_info.get('mime', ''),
            delete_url=data.get('delete_url', ''),
            thumbnail_url=thumb_info.get('url', ''),
            medium_url=medium_info.get('url', ''),
            success=True,
            upload_time=upload_time
        )
        
        logger.info(f"Image uploaded successfully: {result.id}")
        return result
    
    def delete_image(self, delete_url: str) -> bool:
        """
        Delete uploaded image using delete URL.
        
        Args:
            delete_url: Delete URL from upload response
        
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            response = self.session.get(delete_url, timeout=30)
            
            # ImageBB returns a webpage for deletion, check if it was successful
            if response.status_code == 200:
                # Look for success indicators in the response
                if 'deleted' in response.text.lower() or 'removed' in response.text.lower():
                    logger.info("Image deleted successfully")
                    return True
                else:
                    logger.warning("Delete request completed but success uncertain")
                    return False
            else:
                logger.error(f"Delete request failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting image: {e}")
            capture_exception(e)
            return False
    
    def get_upload_status(self, upload_result: UploadResult) -> Dict:
        """
        Check if uploaded image is still accessible.
        
        Args:
            upload_result: Result from previous upload
        
        Returns:
            Dictionary with status information
        """
        try:
            # Check if the image URL is still accessible
            response = self.session.head(upload_result.url, timeout=10)
            
            status = {
                'accessible': response.status_code == 200,
                'status_code': response.status_code,
                'size_matches': False,
                'checked_at': datetime.now().isoformat()
            }
            
            # Check Content-Length if available
            if 'content-length' in response.headers:
                actual_size = int(response.headers['content-length'])
                status['size_matches'] = actual_size == upload_result.size
                status['actual_size'] = actual_size
                status['expected_size'] = upload_result.size
            
            return status
            
        except Exception as e:
            logger.error(f"Error checking upload status: {e}")
            return {
                'accessible': False,
                'error': str(e),
                'checked_at': datetime.now().isoformat()
            }
    
    def _track_upload_success(self, result: UploadResult):
        """Track successful upload statistics."""
        self.upload_stats['total_uploads'] += 1
        self.upload_stats['successful_uploads'] += 1
        self.upload_stats['total_size_uploaded'] += result.size
        self.upload_stats['total_upload_time'] += result.upload_time
    
    def _track_upload_failure(self):
        """Track failed upload statistics."""
        self.upload_stats['total_uploads'] += 1
        self.upload_stats['failed_uploads'] += 1
    
    def get_upload_stats(self) -> Dict:
        """
        Get upload statistics.
        
        Returns:
            Dictionary with upload statistics
        """
        stats = self.upload_stats.copy()
        
        if stats['total_uploads'] > 0:
            stats['success_rate'] = stats['successful_uploads'] / stats['total_uploads']
            
        if stats['successful_uploads'] > 0:
            stats['average_upload_time'] = stats['total_upload_time'] / stats['successful_uploads']
            stats['average_file_size'] = stats['total_size_uploaded'] / stats['successful_uploads']
        
        return stats


def main():
    """Test the ImageBB uploader."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Initialize uploader
        uploader = ImageBBUploader()
        
        # Test upload with a public image URL
        test_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/320px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
        
        print("Testing ImageBB uploader with URL...")
        result = uploader.upload_url(test_url, name="test_nature_boardwalk")
        
        print(f"\nUpload Results:")
        print(f"ID: {result.id}")
        print(f"Direct URL: {result.url}")
        print(f"Display URL: {result.display_url}")
        print(f"Viewer URL: {result.url_viewer}")
        print(f"Size: {result.width}x{result.height} ({result.size} bytes)")
        print(f"Upload Time: {result.upload_time:.2f}s")
        print(f"Thumbnail: {result.thumbnail_url}")
        
        # Test upload status check
        print("\nChecking upload status...")
        status = uploader.get_upload_status(result)
        print(f"Status: {status}")
        
        # Show upload statistics
        stats = uploader.get_upload_stats()
        print(f"\nUpload Statistics:")
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.4f}")
            else:
                print(f"  {key}: {value}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())