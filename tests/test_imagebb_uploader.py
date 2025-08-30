#!/usr/bin/env python3
"""
Unit tests for ImageBB uploader module.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import tempfile
import base64

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from imagebb_uploader import ImageBBUploader, UploadResult


class TestImageBBUploader(unittest.TestCase):
    """Test cases for ImageBBUploader class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Set test API key
        os.environ['IMGBB_API_KEY'] = 'test_api_key'
        os.environ['IMAGEBB_RATE_LIMIT'] = '10'
        
        # Sample upload response
        self.mock_upload_response = {
            "data": {
                "id": "2ndCYJK",
                "title": "test_image",
                "url_viewer": "https://ibb.co/2ndCYJK",
                "url": "https://i.ibb.co/w04Prt6/test.jpg",
                "display_url": "https://i.ibb.co/98W13PY/test.jpg",
                "width": "1280",
                "height": "720",
                "size": "122519",
                "time": "1678901234",
                "expiration": "0",
                "image": {
                    "filename": "test.jpg",
                    "name": "test",
                    "mime": "image/jpeg",
                    "extension": "jpg",
                    "url": "https://i.ibb.co/w04Prt6/test.jpg"
                },
                "thumb": {
                    "filename": "test.jpg",
                    "name": "test",
                    "mime": "image/jpeg",
                    "extension": "jpg",
                    "url": "https://i.ibb.co/2ndCYJK/test.jpg"
                },
                "medium": {
                    "filename": "test.jpg",
                    "name": "test",
                    "mime": "image/jpeg",
                    "extension": "jpg",
                    "url": "https://i.ibb.co/98W13PY/test.jpg"
                },
                "delete_url": "https://ibb.co/2ndCYJK/delete-key"
            },
            "success": True,
            "status": 200
        }
        
        # Sample image data (1x1 PNG)
        self.sample_image_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82"
        self.sample_base64 = base64.b64encode(self.sample_image_data).decode('utf-8')
    
    def tearDown(self):
        """Clean up after tests."""
        if 'IMGBB_API_KEY' in os.environ:
            del os.environ['IMGBB_API_KEY']
    
    def test_initialization_with_api_key(self):
        """Test uploader initialization with API key."""
        uploader = ImageBBUploader(api_key='test_key')
        self.assertEqual(uploader.api_key, 'test_key')
        self.assertEqual(uploader.rate_limit, 10)
    
    def test_initialization_from_environment(self):
        """Test uploader initialization from environment variable."""
        uploader = ImageBBUploader()
        self.assertEqual(uploader.api_key, 'test_api_key')
    
    def test_initialization_without_api_key(self):
        """Test uploader initialization fails without API key."""
        del os.environ['IMGBB_API_KEY']
        with self.assertRaises(ValueError) as context:
            ImageBBUploader()
        self.assertIn('IMGBB_API_KEY', str(context.exception))
    
    def test_validate_image_valid_file(self):
        """Test validation of valid image file."""
        uploader = ImageBBUploader()
        
        # Create temporary image file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_file.write(self.sample_image_data)
            temp_path = temp_file.name
        
        try:
            result = uploader.validate_image(temp_path)
            self.assertTrue(result)
        finally:
            os.unlink(temp_path)
    
    def test_validate_image_nonexistent_file(self):
        """Test validation fails for nonexistent file."""
        uploader = ImageBBUploader()
        
        with self.assertRaises(ValueError) as context:
            uploader.validate_image('/nonexistent/file.jpg')
        self.assertIn('does not exist', str(context.exception))
    
    def test_validate_image_unsupported_format(self):
        """Test validation fails for unsupported format."""
        uploader = ImageBBUploader()
        
        # Create temporary file with unsupported extension
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b'not an image')
            temp_path = temp_file.name
        
        try:
            with self.assertRaises(ValueError) as context:
                uploader.validate_image(temp_path)
            self.assertIn('Unsupported format', str(context.exception))
        finally:
            os.unlink(temp_path)
    
    def test_validate_image_too_large(self):
        """Test validation fails for files too large."""
        uploader = ImageBBUploader()
        
        # Create temporary large file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            # Write 33MB of data (exceeds 32MB limit)
            temp_file.write(b'0' * (33 * 1024 * 1024))
            temp_path = temp_file.name
        
        try:
            with self.assertRaises(ValueError) as context:
                uploader.validate_image(temp_path)
            self.assertIn('too large', str(context.exception))
        finally:
            os.unlink(temp_path)
    
    def test_validate_image_empty_file(self):
        """Test validation fails for empty file."""
        uploader = ImageBBUploader()
        
        # Create empty temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            with self.assertRaises(ValueError) as context:
                uploader.validate_image(temp_path)
            self.assertIn('empty', str(context.exception))
        finally:
            os.unlink(temp_path)
    
    def test_validate_base64_image_valid(self):
        """Test validation of valid base64 image."""
        uploader = ImageBBUploader()
        
        result = uploader.validate_base64_image(self.sample_base64)
        self.assertTrue(result)
    
    def test_validate_base64_image_with_data_uri(self):
        """Test validation of base64 image with data URI prefix."""
        uploader = ImageBBUploader()
        
        data_uri = f"data:image/png;base64,{self.sample_base64}"
        result = uploader.validate_base64_image(data_uri)
        self.assertTrue(result)
    
    def test_validate_base64_image_invalid(self):
        """Test validation fails for invalid base64."""
        uploader = ImageBBUploader()
        
        with self.assertRaises(ValueError) as context:
            uploader.validate_base64_image("invalid_base64_data")
        self.assertIn('Invalid base64', str(context.exception))
    
    def test_validate_base64_image_empty(self):
        """Test validation fails for empty base64."""
        uploader = ImageBBUploader()
        
        with self.assertRaises(ValueError) as context:
            uploader.validate_base64_image("")
        self.assertIn('Invalid base64', str(context.exception))
    
    def test_validate_base64_image_too_large(self):
        """Test validation fails for too large base64 image."""
        uploader = ImageBBUploader()
        
        # Create large base64 data
        large_data = base64.b64encode(b'0' * (33 * 1024 * 1024)).decode('utf-8')
        
        with self.assertRaises(ValueError) as context:
            uploader.validate_base64_image(large_data)
        self.assertIn('too large', str(context.exception))
    
    @patch('imagebb_uploader.requests.Session')
    def test_upload_base64_success(self, mock_session_class):
        """Test successful base64 upload."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_upload_response
        mock_session.post.return_value = mock_response
        
        # Test
        uploader = ImageBBUploader()
        result = uploader.upload_base64(self.sample_base64, name="test_image")
        
        # Assertions
        self.assertIsInstance(result, UploadResult)
        self.assertEqual(result.id, "2ndCYJK")
        self.assertEqual(result.title, "test_image")
        self.assertEqual(result.url, "https://i.ibb.co/w04Prt6/test.jpg")
        self.assertEqual(result.width, 1280)
        self.assertEqual(result.height, 720)
        self.assertTrue(result.success)
        
        # Check API call
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        posted_data = call_args[1]['data']
        self.assertIn('key', posted_data)
        self.assertIn('image', posted_data)
        self.assertIn('name', posted_data)
        self.assertEqual(posted_data['name'], 'test_image')
    
    @patch('imagebb_uploader.requests.Session')
    def test_upload_base64_with_expiration(self, mock_session_class):
        """Test base64 upload with expiration."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_upload_response
        mock_session.post.return_value = mock_response
        
        # Test
        uploader = ImageBBUploader()
        result = uploader.upload_base64(self.sample_base64, expiration=3600)
        
        # Check expiration was included in request
        call_args = mock_session.post.call_args
        posted_data = call_args[1]['data']
        self.assertIn('expiration', posted_data)
        self.assertEqual(posted_data['expiration'], '3600')
    
    def test_upload_base64_invalid_expiration(self):
        """Test upload fails with invalid expiration."""
        uploader = ImageBBUploader()
        
        # Test too short expiration
        with self.assertRaises(ValueError) as context:
            uploader.upload_base64(self.sample_base64, expiration=30)
        self.assertIn('between 60 and 15552000', str(context.exception))
        
        # Test too long expiration
        with self.assertRaises(ValueError) as context:
            uploader.upload_base64(self.sample_base64, expiration=20000000)
        self.assertIn('between 60 and 15552000', str(context.exception))
    
    @patch('imagebb_uploader.requests.Session')
    def test_upload_base64_api_error(self, mock_session_class):
        """Test upload handles API errors."""
        # Setup mock for error response
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "status_code": 400,
            "error": {
                "message": "Invalid API key",
                "code": 100
            },
            "status_txt": "Bad Request"
        }
        mock_session.post.return_value = mock_response
        
        # Test
        uploader = ImageBBUploader()
        with self.assertRaises(Exception) as context:
            uploader.upload_base64(self.sample_base64)
        self.assertIn('Invalid API key', str(context.exception))
    
    @patch('imagebb_uploader.requests.Session')
    def test_upload_base64_success_false_in_response(self, mock_session_class):
        """Test upload handles success=false in response."""
        # Setup mock for failed upload response
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": False,
            "error": {
                "message": "File too large"
            }
        }
        mock_session.post.return_value = mock_response
        
        # Test
        uploader = ImageBBUploader()
        with self.assertRaises(Exception) as context:
            uploader.upload_base64(self.sample_base64)
        self.assertIn('File too large', str(context.exception))
    
    @patch('imagebb_uploader.open', mock_open(read_data=b'test_image_data'))
    @patch('imagebb_uploader.os.path.exists', return_value=True)
    @patch('imagebb_uploader.os.path.getsize', return_value=1000)
    @patch('imagebb_uploader.requests.Session')
    def test_upload_file_success(self, mock_session_class, mock_getsize, mock_exists):
        """Test successful file upload."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_upload_response
        mock_session.post.return_value = mock_response
        
        # Test
        uploader = ImageBBUploader()
        result = uploader.upload_file("/fake/path/test.png", name="test_file")
        
        # Assertions
        self.assertIsInstance(result, UploadResult)
        self.assertEqual(result.id, "2ndCYJK")
        mock_session.post.assert_called_once()
    
    @patch('imagebb_uploader.requests.Session')
    def test_upload_url_success(self, mock_session_class):
        """Test successful URL upload."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_upload_response
        mock_session.post.return_value = mock_response
        
        # Test
        uploader = ImageBBUploader()
        result = uploader.upload_url("https://example.com/image.jpg", name="test_url")
        
        # Assertions
        self.assertIsInstance(result, UploadResult)
        self.assertEqual(result.id, "2ndCYJK")
        
        # Check that URL was passed directly
        call_args = mock_session.post.call_args
        posted_data = call_args[1]['data']
        self.assertEqual(posted_data['image'], "https://example.com/image.jpg")
        self.assertEqual(posted_data['name'], "test_url")
    
    @patch('imagebb_uploader.requests.Session')
    def test_delete_image_success(self, mock_session_class):
        """Test successful image deletion."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Image has been deleted successfully"
        mock_session.get.return_value = mock_response
        
        # Test
        uploader = ImageBBUploader()
        result = uploader.delete_image("https://ibb.co/delete/test-key")
        
        # Assertions
        self.assertTrue(result)
        mock_session.get.assert_called_once_with("https://ibb.co/delete/test-key", timeout=30)
    
    @patch('imagebb_uploader.requests.Session')
    def test_delete_image_failure(self, mock_session_class):
        """Test image deletion failure."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_session.get.return_value = mock_response
        
        # Test
        uploader = ImageBBUploader()
        result = uploader.delete_image("https://ibb.co/delete/invalid-key")
        
        # Assertions
        self.assertFalse(result)
    
    @patch('imagebb_uploader.requests.Session')
    def test_get_upload_status_accessible(self, mock_session_class):
        """Test checking upload status for accessible image."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '122519'}
        mock_session.head.return_value = mock_response
        
        # Create sample upload result
        upload_result = UploadResult(
            id="test", title="test", url_viewer="", url="https://test.com/image.jpg",
            display_url="", width=100, height=100, size=122519, time="", expiration="",
            filename="", mime_type="", delete_url="", thumbnail_url="", medium_url="",
            success=True, upload_time=1.0
        )
        
        # Test
        uploader = ImageBBUploader()
        status = uploader.get_upload_status(upload_result)
        
        # Assertions
        self.assertTrue(status['accessible'])
        self.assertEqual(status['status_code'], 200)
        self.assertTrue(status['size_matches'])
        self.assertEqual(status['actual_size'], 122519)
    
    @patch('imagebb_uploader.requests.Session')
    def test_get_upload_status_not_accessible(self, mock_session_class):
        """Test checking upload status for inaccessible image."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.head.side_effect = Exception("Network error")
        
        # Create sample upload result
        upload_result = UploadResult(
            id="test", title="test", url_viewer="", url="https://test.com/image.jpg",
            display_url="", width=100, height=100, size=122519, time="", expiration="",
            filename="", mime_type="", delete_url="", thumbnail_url="", medium_url="",
            success=True, upload_time=1.0
        )
        
        # Test
        uploader = ImageBBUploader()
        status = uploader.get_upload_status(upload_result)
        
        # Assertions
        self.assertFalse(status['accessible'])
        self.assertIn('error', status)
        self.assertIn('checked_at', status)
    
    def test_parse_upload_response(self):
        """Test parsing of upload response."""
        uploader = ImageBBUploader()
        result = uploader._parse_upload_response(self.mock_upload_response, 1.5)
        
        self.assertIsInstance(result, UploadResult)
        self.assertEqual(result.id, "2ndCYJK")
        self.assertEqual(result.title, "test_image")
        self.assertEqual(result.width, 1280)
        self.assertEqual(result.height, 720)
        self.assertEqual(result.size, 122519)
        self.assertEqual(result.upload_time, 1.5)
        self.assertTrue(result.success)
        self.assertEqual(result.mime_type, "image/jpeg")
    
    def test_upload_statistics_tracking(self):
        """Test upload statistics tracking."""
        uploader = ImageBBUploader()
        
        # Create sample result
        upload_result = UploadResult(
            id="test", title="test", url_viewer="", url="", display_url="",
            width=100, height=100, size=1000, time="", expiration="",
            filename="", mime_type="", delete_url="", thumbnail_url="", medium_url="",
            success=True, upload_time=2.0
        )
        
        # Track successful upload
        uploader._track_upload_success(upload_result)
        
        # Track failed upload
        uploader._track_upload_failure()
        
        # Get statistics
        stats = uploader.get_upload_stats()
        
        # Assertions
        self.assertEqual(stats['total_uploads'], 2)
        self.assertEqual(stats['successful_uploads'], 1)
        self.assertEqual(stats['failed_uploads'], 1)
        self.assertEqual(stats['total_size_uploaded'], 1000)
        self.assertEqual(stats['total_upload_time'], 2.0)
        self.assertEqual(stats['success_rate'], 0.5)
        self.assertEqual(stats['average_upload_time'], 2.0)
        self.assertEqual(stats['average_file_size'], 1000)
    
    @patch('imagebb_uploader.time.sleep')
    def test_rate_limiting(self, mock_sleep):
        """Test rate limiting enforcement."""
        uploader = ImageBBUploader()
        uploader.rate_limit = 2  # Set low limit for testing
        
        # Add requests to simulate hitting rate limit
        current_time = 1000.0
        with patch('imagebb_uploader.time.time', return_value=current_time):
            uploader.requests_per_minute = [current_time - 30, current_time - 20]
            uploader._enforce_rate_limit()
            
            # Should sleep since we're at the limit
            mock_sleep.assert_called_once()
            sleep_time = mock_sleep.call_args[0][0]
            self.assertGreater(sleep_time, 0)
    
    def test_supported_formats(self):
        """Test that all expected formats are supported."""
        uploader = ImageBBUploader()
        
        expected_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg'}
        self.assertEqual(uploader.SUPPORTED_FORMATS, expected_formats)
    
    def test_mime_type_mapping(self):
        """Test MIME type mapping."""
        uploader = ImageBBUploader()
        
        self.assertEqual(uploader.MIME_TYPES['.jpg'], 'image/jpeg')
        self.assertEqual(uploader.MIME_TYPES['.png'], 'image/png')
        self.assertEqual(uploader.MIME_TYPES['.gif'], 'image/gif')
        self.assertEqual(uploader.MIME_TYPES['.svg'], 'image/svg+xml')


if __name__ == '__main__':
    unittest.main()