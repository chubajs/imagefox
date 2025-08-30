#!/usr/bin/env python3
"""
Unit tests for Airtable uploader module.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from airtable_uploader import AirtableUploader, ImageRecord


class TestImageRecord(unittest.TestCase):
    """Test cases for ImageRecord dataclass."""
    
    def test_image_record_creation(self):
        """Test creating ImageRecord with required fields."""
        record = ImageRecord(
            search_query="sunset beach",
            source_url="https://example.com/page",
            image_url="https://example.com/image.jpg"
        )
        
        self.assertEqual(record.search_query, "sunset beach")
        self.assertEqual(record.source_url, "https://example.com/page")
        self.assertEqual(record.image_url, "https://example.com/image.jpg")
        self.assertFalse(record.selected)  # Default value
    
    def test_image_record_to_airtable_fields(self):
        """Test conversion to Airtable fields format."""
        record = ImageRecord(
            search_query="sunset beach",
            source_url="https://example.com/page",
            image_url="https://example.com/image.jpg",
            title="Beautiful Sunset",
            relevance_score=0.95,
            selected=True,
            timestamp="2024-01-01T12:00:00"
        )
        
        fields = record.to_airtable_fields()
        
        # Check field mapping
        self.assertEqual(fields['Search Query'], "sunset beach")
        self.assertEqual(fields['Source URL'], "https://example.com/page")
        self.assertEqual(fields['Image URL'], "https://example.com/image.jpg")
        self.assertEqual(fields['Title'], "Beautiful Sunset")
        self.assertEqual(fields['Relevance Score'], 0.95)
        self.assertTrue(fields['Selected'])
        self.assertIn('Timestamp', fields)
        
        # Check that None values are excluded
        self.assertNotIn('Description', fields)
        self.assertNotIn('Vision Analysis', fields)
    
    def test_timestamp_formatting(self):
        """Test timestamp formatting for Airtable."""
        record = ImageRecord(
            search_query="test",
            source_url="https://example.com",
            image_url="https://example.com/img.jpg",
            timestamp="2024-01-01T12:00:00"
        )
        
        fields = record.to_airtable_fields()
        # Should add Z suffix for UTC
        self.assertTrue(fields['Timestamp'].endswith('Z'))


class TestAirtableUploader(unittest.TestCase):
    """Test cases for AirtableUploader class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Set test environment variables
        os.environ['AIRTABLE_API_KEY'] = 'test_api_key'
        os.environ['AIRTABLE_BASE_ID'] = 'test_base_id'
        os.environ['AIRTABLE_TABLE_NAME'] = 'Images'
        os.environ['AIRTABLE_RATE_LIMIT'] = '5'
        
        # Sample Airtable response
        self.sample_record = {
            "id": "recXXXXXXXXXXXXXX",
            "fields": {
                "Search Query": "sunset beach",
                "Source URL": "https://example.com/page",
                "Image URL": "https://example.com/image.jpg",
                "Title": "Beautiful Sunset",
                "Relevance Score": 0.95,
                "Selected": True
            },
            "createdTime": "2024-01-01T12:00:00.000Z"
        }
        
        self.sample_batch_response = {
            "records": [
                self.sample_record,
                {
                    "id": "recYYYYYYYYYYYYYY",
                    "fields": {
                        "Search Query": "mountain landscape",
                        "Source URL": "https://example.com/mountain",
                        "Image URL": "https://example.com/mountain.jpg"
                    }
                }
            ]
        }
    
    def tearDown(self):
        """Clean up after tests."""
        env_vars = ['AIRTABLE_API_KEY', 'AIRTABLE_BASE_ID', 'AIRTABLE_TABLE_NAME']
        for var in env_vars:
            if var in os.environ:
                del os.environ[var]
    
    def test_initialization_with_params(self):
        """Test uploader initialization with explicit parameters."""
        uploader = AirtableUploader(
            api_key='test_key',
            base_id='test_base',
            table_name='TestTable'
        )
        
        self.assertEqual(uploader.api_key, 'test_key')
        self.assertEqual(uploader.base_id, 'test_base')
        self.assertEqual(uploader.table_name, 'TestTable')
        self.assertEqual(uploader.rate_limit, 5)
    
    def test_initialization_from_environment(self):
        """Test uploader initialization from environment variables."""
        uploader = AirtableUploader()
        
        self.assertEqual(uploader.api_key, 'test_api_key')
        self.assertEqual(uploader.base_id, 'test_base_id')
        self.assertEqual(uploader.table_name, 'Images')
    
    def test_initialization_missing_api_key(self):
        """Test initialization fails without API key."""
        del os.environ['AIRTABLE_API_KEY']
        
        with self.assertRaises(ValueError) as context:
            AirtableUploader()
        self.assertIn('AIRTABLE_API_KEY', str(context.exception))
    
    def test_initialization_missing_base_id(self):
        """Test initialization fails without base ID."""
        del os.environ['AIRTABLE_BASE_ID']
        
        with self.assertRaises(ValueError) as context:
            AirtableUploader()
        self.assertIn('AIRTABLE_BASE_ID', str(context.exception))
    
    def test_validate_record_success(self):
        """Test successful record validation."""
        uploader = AirtableUploader()
        
        record = ImageRecord(
            search_query="test",
            source_url="https://example.com",
            image_url="https://example.com/image.jpg",
            relevance_score=0.8,
            quality_score=0.9,
            selected=True
        )
        
        # Should not raise any exception
        self.assertTrue(uploader.validate_record(record))
    
    def test_validate_record_missing_required_field(self):
        """Test validation fails with missing required field."""
        uploader = AirtableUploader()
        
        # Missing required 'Search Query' field
        fields = {
            "Source URL": "https://example.com",
            "Image URL": "https://example.com/image.jpg"
        }
        
        with self.assertRaises(ValueError) as context:
            uploader.validate_record(fields)
        self.assertIn('Search Query', str(context.exception))
    
    def test_validate_record_invalid_url(self):
        """Test validation fails with invalid URL."""
        uploader = AirtableUploader()
        
        fields = {
            "Search Query": "test",
            "Source URL": "invalid-url",  # Invalid URL
            "Image URL": "https://example.com/image.jpg"
        }
        
        with self.assertRaises(ValueError) as context:
            uploader.validate_record(fields)
        self.assertIn('valid URL', str(context.exception))
    
    def test_validate_record_invalid_number_range(self):
        """Test validation fails with number out of range."""
        uploader = AirtableUploader()
        
        fields = {
            "Search Query": "test",
            "Source URL": "https://example.com",
            "Image URL": "https://example.com/image.jpg",
            "Relevance Score": 1.5  # Out of range (max 1.0)
        }
        
        with self.assertRaises(ValueError) as context:
            uploader.validate_record(fields)
        self.assertIn('must be <=', str(context.exception))
    
    def test_validate_record_invalid_checkbox(self):
        """Test validation fails with invalid checkbox value."""
        uploader = AirtableUploader()
        
        fields = {
            "Search Query": "test",
            "Source URL": "https://example.com",
            "Image URL": "https://example.com/image.jpg",
            "Selected": "yes"  # Should be boolean
        }
        
        with self.assertRaises(ValueError) as context:
            uploader.validate_record(fields)
        self.assertIn('must be a boolean', str(context.exception))
    
    @patch('airtable_uploader.PYAIRTABLE_AVAILABLE', True)
    def test_create_record_success_pyairtable(self):
        """Test successful record creation using pyairtable."""
        with patch('airtable_uploader.AirtableApi') as mock_api:
            mock_table = MagicMock()
            mock_table.create.return_value = self.sample_record
            mock_api.return_value.table.return_value = mock_table
            
            uploader = AirtableUploader()
            
            record = ImageRecord(
                search_query="sunset beach",
                source_url="https://example.com/page",
                image_url="https://example.com/image.jpg"
            )
            
            result = uploader.create_record(record)
            
            # Verify result
            self.assertEqual(result['id'], 'recXXXXXXXXXXXXXX')
            self.assertEqual(result['fields']['Search Query'], 'sunset beach')
            
            # Verify API was called
            mock_table.create.assert_called_once()
            call_args = mock_table.create.call_args[0][0]
            self.assertIn('Search Query', call_args)
    
    @patch('airtable_uploader.PYAIRTABLE_AVAILABLE', False)
    @patch('airtable_uploader.requests.Session')
    def test_create_record_success_requests(self, mock_session_class):
        """Test successful record creation using requests."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_record
        mock_session.post.return_value = mock_response
        
        uploader = AirtableUploader()
        
        record = ImageRecord(
            search_query="sunset beach",
            source_url="https://example.com/page",
            image_url="https://example.com/image.jpg"
        )
        
        result = uploader.create_record(record)
        
        # Verify result
        self.assertEqual(result['id'], 'recXXXXXXXXXXXXXX')
        
        # Verify API was called
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args[1]['json']
        self.assertIn('fields', call_args)
    
    @patch('airtable_uploader.PYAIRTABLE_AVAILABLE', True)
    def test_batch_create_success(self):
        """Test successful batch record creation."""
        with patch('airtable_uploader.AirtableApi') as mock_api:
            mock_table = MagicMock()
            mock_table.batch_create.return_value = self.sample_batch_response['records']
            mock_api.return_value.table.return_value = mock_table
            
            uploader = AirtableUploader()
            
            records = [
                ImageRecord(
                    search_query="sunset beach",
                    source_url="https://example.com/page",
                    image_url="https://example.com/image.jpg"
                ),
                ImageRecord(
                    search_query="mountain landscape",
                    source_url="https://example.com/mountain",
                    image_url="https://example.com/mountain.jpg"
                )
            ]
            
            result = uploader.batch_create(records)
            
            # Verify result
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]['id'], 'recXXXXXXXXXXXXXX')
            
            # Verify API was called
            mock_table.batch_create.assert_called_once()
    
    def test_batch_create_too_many_records(self):
        """Test batch create fails with too many records."""
        uploader = AirtableUploader()
        
        # Create 11 records (exceeds limit of 10)
        records = [
            ImageRecord(
                search_query=f"test {i}",
                source_url="https://example.com",
                image_url=f"https://example.com/image{i}.jpg"
            )
            for i in range(11)
        ]
        
        with self.assertRaises(ValueError) as context:
            uploader.batch_create(records)
        self.assertIn('limited to 10', str(context.exception))
    
    @patch('airtable_uploader.PYAIRTABLE_AVAILABLE', True)
    def test_update_record_success(self):
        """Test successful record update."""
        with patch('airtable_uploader.AirtableApi') as mock_api:
            mock_table = MagicMock()
            mock_table.update.return_value = self.sample_record
            mock_api.return_value.table.return_value = mock_table
            
            uploader = AirtableUploader()
            
            result = uploader.update_record(
                "recXXXXXXXXXXXXXX",
                {"Relevance Score": 0.98, "Selected": True}
            )
            
            # Verify result
            self.assertEqual(result['id'], 'recXXXXXXXXXXXXXX')
            
            # Verify API was called
            mock_table.update.assert_called_once_with(
                "recXXXXXXXXXXXXXX",
                {"Relevance Score": 0.98, "Selected": True}
            )
    
    @patch('airtable_uploader.PYAIRTABLE_AVAILABLE', True)
    def test_get_record_success(self):
        """Test successful record retrieval."""
        with patch('airtable_uploader.AirtableApi') as mock_api:
            mock_table = MagicMock()
            mock_table.get.return_value = self.sample_record
            mock_api.return_value.table.return_value = mock_table
            
            uploader = AirtableUploader()
            
            result = uploader.get_record("recXXXXXXXXXXXXXX")
            
            # Verify result
            self.assertEqual(result['id'], 'recXXXXXXXXXXXXXX')
            
            # Verify API was called
            mock_table.get.assert_called_once_with("recXXXXXXXXXXXXXX")
    
    @patch('airtable_uploader.PYAIRTABLE_AVAILABLE', True)
    def test_query_records_success(self):
        """Test successful record query."""
        with patch('airtable_uploader.AirtableApi') as mock_api:
            mock_table = MagicMock()
            mock_table.all.return_value = [self.sample_record]
            mock_api.return_value.table.return_value = mock_table
            
            uploader = AirtableUploader()
            
            result = uploader.query_records(
                formula="AND({Selected}=TRUE(), {Relevance Score}>0.9)",
                max_records=10,
                sort=[{"field": "Relevance Score", "direction": "desc"}]
            )
            
            # Verify result
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['id'], 'recXXXXXXXXXXXXXX')
            
            # Verify API was called with correct parameters
            mock_table.all.assert_called_once()
            call_kwargs = mock_table.all.call_args[1]
            self.assertIn('formula', call_kwargs)
            self.assertIn('max_records', call_kwargs)
            self.assertIn('sort', call_kwargs)
    
    @patch('airtable_uploader.PYAIRTABLE_AVAILABLE', True)
    def test_delete_record_success(self):
        """Test successful record deletion."""
        with patch('airtable_uploader.AirtableApi') as mock_api:
            mock_table = MagicMock()
            mock_table.delete.return_value = {"deleted": True, "id": "recXXXXXXXXXXXXXX"}
            mock_api.return_value.table.return_value = mock_table
            
            uploader = AirtableUploader()
            
            result = uploader.delete_record("recXXXXXXXXXXXXXX")
            
            # Verify result
            self.assertTrue(result)
            
            # Verify API was called
            mock_table.delete.assert_called_once_with("recXXXXXXXXXXXXXX")
    
    @patch('airtable_uploader.PYAIRTABLE_AVAILABLE', True)
    def test_validate_connection_success(self):
        """Test successful connection validation."""
        with patch('airtable_uploader.AirtableApi') as mock_api:
            mock_table = MagicMock()
            mock_table.all.return_value = [self.sample_record]
            mock_api.return_value.table.return_value = mock_table
            
            uploader = AirtableUploader()
            
            result = uploader.validate_connection()
            
            # Verify result
            self.assertTrue(result)
            
            # Verify API was called
            mock_table.all.assert_called_once()
    
    @patch('airtable_uploader.PYAIRTABLE_AVAILABLE', True)
    def test_validate_connection_failure(self):
        """Test connection validation failure."""
        with patch('airtable_uploader.AirtableApi') as mock_api:
            mock_table = MagicMock()
            mock_table.all.side_effect = Exception("Connection failed")
            mock_api.return_value.table.return_value = mock_table
            
            uploader = AirtableUploader()
            
            result = uploader.validate_connection()
            
            # Verify result
            self.assertFalse(result)
    
    @patch('airtable_uploader.time.sleep')
    def test_rate_limiting(self, mock_sleep):
        """Test rate limiting enforcement."""
        uploader = AirtableUploader()
        uploader.rate_limit = 2  # Set low limit for testing
        
        # Add requests to simulate hitting rate limit
        current_time = 1000.0
        with patch('airtable_uploader.time.time', return_value=current_time):
            uploader.requests_per_second = [current_time - 0.8, current_time - 0.5]
            uploader._enforce_rate_limit()
            
            # Should sleep since we're at the limit
            mock_sleep.assert_called_once()
            sleep_time = mock_sleep.call_args[0][0]
            self.assertGreater(sleep_time, 0)
    
    def test_operation_statistics_tracking(self):
        """Test operation statistics tracking."""
        uploader = AirtableUploader()
        
        # Track various operations
        uploader._track_operation_success('create', 1)
        uploader._track_operation_success('batch_create', 3)
        uploader._track_operation_success('update', 2)
        uploader._track_operation_success('query', 5)
        uploader._track_operation_failure()
        
        stats = uploader.get_operation_stats()
        
        # Check statistics
        self.assertEqual(stats['total_operations'], 5)
        self.assertEqual(stats['successful_operations'], 4)
        self.assertEqual(stats['failed_operations'], 1)
        self.assertEqual(stats['records_created'], 4)  # 1 + 3
        self.assertEqual(stats['records_updated'], 2)
        self.assertEqual(stats['records_queried'], 5)
        self.assertEqual(stats['success_rate'], 0.8)  # 4/5
    
    def test_schema_validation_warning_unknown_field(self):
        """Test schema validation logs warning for unknown fields."""
        uploader = AirtableUploader()
        
        fields = {
            "Search Query": "test",
            "Source URL": "https://example.com",
            "Image URL": "https://example.com/image.jpg",
            "Unknown Field": "should trigger warning"
        }
        
        # Should still validate successfully but log warning
        with patch('airtable_uploader.logger') as mock_logger:
            uploader.validate_record(fields)
            mock_logger.warning.assert_called_once()
            self.assertIn('Unknown field', mock_logger.warning.call_args[0][0])
    
    @patch('airtable_uploader.PYAIRTABLE_AVAILABLE', False)
    @patch('airtable_uploader.requests.Session')
    def test_requests_implementation_error_handling(self, mock_session_class):
        """Test error handling in requests-only implementation."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 422  # Unprocessable Entity
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_session.post.return_value = mock_response
        
        uploader = AirtableUploader()
        
        record = ImageRecord(
            search_query="test",
            source_url="https://example.com",
            image_url="https://example.com/image.jpg"
        )
        
        with self.assertRaises(Exception) as context:
            uploader.create_record(record)
        self.assertIn('Failed to create record', str(context.exception))
    
    def test_table_schema_constants(self):
        """Test table schema constants are properly defined."""
        schema = AirtableUploader.TABLE_SCHEMA
        
        # Check that required fields are marked
        self.assertTrue(schema['Search Query']['required'])
        self.assertTrue(schema['Source URL']['required'])
        self.assertTrue(schema['Image URL']['required'])
        
        # Check optional fields
        self.assertFalse(schema['Title']['required'])
        self.assertFalse(schema['Selected']['required'])
        
        # Check field types
        self.assertEqual(schema['Relevance Score']['type'], 'number')
        self.assertEqual(schema['Source URL']['type'], 'url')
        self.assertEqual(schema['Selected']['type'], 'checkbox')
        
        # Check constraints
        self.assertEqual(schema['Relevance Score']['min'], 0)
        self.assertEqual(schema['Relevance Score']['max'], 1)


if __name__ == '__main__':
    unittest.main()