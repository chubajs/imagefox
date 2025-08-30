#!/usr/bin/env python3
"""
Airtable API client for ImageFox.

This module provides a robust client for storing image metadata,
analysis results, and selection audit trails in Airtable.
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass, asdict
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import sentry_sdk
from sentry_sdk import capture_exception

logger = logging.getLogger(__name__)

# Try to import pyairtable, fallback to requests-only implementation
try:
    from pyairtable import Api as AirtableApi
    from pyairtable.exceptions import AirtableApiError
    PYAIRTABLE_AVAILABLE = True
except ImportError:
    AirtableApi = None
    AirtableApiError = Exception
    PYAIRTABLE_AVAILABLE = False
    logger.warning("pyairtable not available, using requests-only implementation")


@dataclass
class ImageRecord:
    """Structured representation of an Images table record."""
    search_query: str
    source_url: str
    image_url: str
    thumbnail_url: Optional[str] = None
    hosted_url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    vision_analysis: Optional[str] = None
    relevance_score: Optional[float] = None
    quality_score: Optional[float] = None
    selection_reason: Optional[str] = None
    selected: bool = False
    timestamp: Optional[str] = None
    model_used: Optional[str] = None
    processing_time: Optional[float] = None
    tags: Optional[List[str]] = None
    error_log: Optional[str] = None
    
    def to_airtable_fields(self) -> Dict[str, Any]:
        """Convert to Airtable fields format."""
        fields = {}
        
        # Map dataclass fields to Airtable field names
        field_mapping = {
            'search_query': 'Search Query',
            'source_url': 'Source URL',
            'image_url': 'Image URL',
            'thumbnail_url': 'Thumbnail URL',
            'hosted_url': 'ImageBB URL',
            'title': 'Title',
            'description': 'Description',
            'vision_analysis': 'Vision Analysis',
            'relevance_score': 'Relevance Score',
            'quality_score': 'Quality Score',
            'selection_reason': 'Selection Reason',
            'selected': 'Selected',
            'timestamp': 'Timestamp',
            'model_used': 'Model Used',
            'processing_time': 'Processing Time',
            'tags': 'Tags',
            'error_log': 'Error Log'
        }
        
        for field_name, airtable_name in field_mapping.items():
            value = getattr(self, field_name)
            if value is not None:
                if field_name == 'timestamp' and isinstance(value, str):
                    # Ensure timestamp is in ISO format
                    if not value.endswith('Z') and '+' not in value:
                        value = datetime.fromisoformat(value).isoformat() + 'Z'
                fields[airtable_name] = value
        
        return fields


class AirtableUploader:
    """Client for Airtable API to manage Images table."""
    
    API_BASE_URL = "https://api.airtable.com/v0"
    
    # Standard Images table schema
    TABLE_SCHEMA = {
        'Search Query': {'type': 'singleLineText', 'required': True},
        'Source URL': {'type': 'url', 'required': True},
        'Image URL': {'type': 'url', 'required': True},
        'Thumbnail URL': {'type': 'url', 'required': False},
        'ImageBB URL': {'type': 'url', 'required': False},
        'Title': {'type': 'singleLineText', 'required': False},
        'Description': {'type': 'multilineText', 'required': False},
        'Vision Analysis': {'type': 'multilineText', 'required': False},
        'Relevance Score': {'type': 'number', 'required': False, 'min': 0, 'max': 1},
        'Quality Score': {'type': 'number', 'required': False, 'min': 0, 'max': 1},
        'Selection Reason': {'type': 'multilineText', 'required': False},
        'Selected': {'type': 'checkbox', 'required': False, 'default': False},
        'Timestamp': {'type': 'dateTime', 'required': False},
        'Model Used': {'type': 'singleSelect', 'required': False},
        'Processing Time': {'type': 'number', 'required': False},
        'Tags': {'type': 'multipleSelects', 'required': False},
        'Error Log': {'type': 'multilineText', 'required': False}
    }
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        base_id: Optional[str] = None,
        table_name: Optional[str] = None
    ):
        """
        Initialize Airtable uploader.
        
        Args:
            api_key: Airtable API key. If not provided, reads from environment.
            base_id: Airtable base ID. If not provided, reads from environment.
            table_name: Table name. If not provided, reads from environment.
        
        Raises:
            ValueError: If required parameters are not provided or found in environment.
        """
        self.api_key = api_key or os.getenv('AIRTABLE_API_KEY')
        self.base_id = base_id or os.getenv('AIRTABLE_BASE_ID')
        self.table_name = table_name or os.getenv('AIRTABLE_TABLE_NAME', 'Images')
        
        if not self.api_key:
            raise ValueError("AIRTABLE_API_KEY not provided or found in environment")
        if not self.base_id:
            raise ValueError("AIRTABLE_BASE_ID not provided or found in environment")
        
        # Rate limiting configuration (5 requests per second)
        self.rate_limit = int(os.getenv('AIRTABLE_RATE_LIMIT', '5'))
        self.requests_per_second = []
        
        # Operation tracking
        self.operation_stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'records_created': 0,
            'records_updated': 0,
            'records_queried': 0
        }
        
        # Initialize API client
        if PYAIRTABLE_AVAILABLE:
            self.api = AirtableApi(self.api_key)
            self.table = self.api.table(self.base_id, self.table_name)
            logger.info("Using pyairtable for Airtable operations")
        else:
            self.session = self._create_session()
            logger.info("Using requests-only implementation for Airtable")
        
        logger.info(f"Airtable uploader initialized for base {self.base_id}, table {self.table_name}")
    
    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry strategy (requests-only mode)."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=int(os.getenv('RETRY_ATTEMPTS', '3')),
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PATCH", "DELETE"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
        
        return session
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting to prevent API throttling."""
        current_time = time.time()
        one_second_ago = current_time - 1
        
        # Remove requests older than 1 second
        self.requests_per_second = [
            req_time for req_time in self.requests_per_second 
            if req_time > one_second_ago
        ]
        
        # Check if we've hit the rate limit
        if len(self.requests_per_second) >= self.rate_limit:
            # Calculate sleep time
            oldest_request = min(self.requests_per_second)
            sleep_time = 1 - (current_time - oldest_request) + 0.1
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        # Record this request
        self.requests_per_second.append(current_time)
    
    def validate_record(self, record: Union[ImageRecord, Dict]) -> bool:
        """
        Validate record against table schema.
        
        Args:
            record: ImageRecord instance or dictionary to validate
        
        Returns:
            True if valid, False otherwise
        
        Raises:
            ValueError: If validation fails with specific reason
        """
        if isinstance(record, ImageRecord):
            fields = record.to_airtable_fields()
        else:
            fields = record
        
        # Check required fields
        for field_name, schema in self.TABLE_SCHEMA.items():
            if schema.get('required', False) and field_name not in fields:
                raise ValueError(f"Required field missing: {field_name}")
        
        # Validate field types and constraints
        for field_name, value in fields.items():
            if field_name not in self.TABLE_SCHEMA:
                logger.warning(f"Unknown field in record: {field_name}")
                continue
                
            schema = self.TABLE_SCHEMA[field_name]
            
            # Type validation
            if schema['type'] == 'number':
                if not isinstance(value, (int, float)):
                    raise ValueError(f"Field {field_name} must be a number, got {type(value)}")
                
                # Range validation
                if 'min' in schema and value < schema['min']:
                    raise ValueError(f"Field {field_name} must be >= {schema['min']}")
                if 'max' in schema and value > schema['max']:
                    raise ValueError(f"Field {field_name} must be <= {schema['max']}")
            
            elif schema['type'] == 'url':
                if not isinstance(value, str) or not value.startswith(('http://', 'https://')):
                    raise ValueError(f"Field {field_name} must be a valid URL")
            
            elif schema['type'] == 'checkbox':
                if not isinstance(value, bool):
                    raise ValueError(f"Field {field_name} must be a boolean")
        
        return True
    
    def create_record(self, record: Union[ImageRecord, Dict]) -> Dict:
        """
        Create a single record in the Images table.
        
        Args:
            record: ImageRecord instance or dictionary with field data
        
        Returns:
            Created record with Airtable ID and metadata
        
        Raises:
            Exception: If creation fails
        """
        # Validate record
        self.validate_record(record)
        
        # Convert to fields format
        if isinstance(record, ImageRecord):
            fields = record.to_airtable_fields()
        else:
            fields = record
        
        # Enforce rate limiting
        self._enforce_rate_limit()
        
        try:
            if PYAIRTABLE_AVAILABLE:
                # Use pyairtable
                result = self.table.create(fields)
            else:
                # Use requests implementation
                url = f"{self.API_BASE_URL}/{self.base_id}/{self.table_name}"
                payload = {"fields": fields}
                
                response = self.session.post(
                    url,
                    json=payload,
                    timeout=int(os.getenv('REQUEST_TIMEOUT', '30'))
                )
                
                if response.status_code == 200:
                    result = response.json()
                else:
                    response.raise_for_status()
            
            # Track success
            self._track_operation_success('create')
            logger.info(f"Record created successfully: {result.get('id')}")
            return result
            
        except Exception as e:
            self._track_operation_failure()
            logger.error(f"Error creating record: {e}")
            capture_exception(e)
            raise Exception(f"Failed to create record: {e}")
    
    def batch_create(self, records: List[Union[ImageRecord, Dict]]) -> List[Dict]:
        """
        Create multiple records in batch (max 10 per request).
        
        Args:
            records: List of ImageRecord instances or dictionaries
        
        Returns:
            List of created records with Airtable IDs
        
        Raises:
            Exception: If batch creation fails
        """
        if len(records) > 10:
            raise ValueError("Batch operations limited to 10 records per request")
        
        # Validate all records
        validated_records = []
        for record in records:
            self.validate_record(record)
            if isinstance(record, ImageRecord):
                validated_records.append(record.to_airtable_fields())
            else:
                validated_records.append(record)
        
        # Enforce rate limiting
        self._enforce_rate_limit()
        
        try:
            if PYAIRTABLE_AVAILABLE:
                # Use pyairtable
                result = self.table.batch_create(
                    [{"fields": fields} for fields in validated_records]
                )
            else:
                # Use requests implementation
                url = f"{self.API_BASE_URL}/{self.base_id}/{self.table_name}"
                payload = {
                    "records": [{"fields": fields} for fields in validated_records]
                }
                
                response = self.session.post(
                    url,
                    json=payload,
                    timeout=int(os.getenv('REQUEST_TIMEOUT', '60'))
                )
                
                if response.status_code == 200:
                    result = response.json().get('records', [])
                else:
                    response.raise_for_status()
            
            # Track success
            self._track_operation_success('batch_create', len(result))
            logger.info(f"Batch created {len(result)} records successfully")
            return result
            
        except Exception as e:
            self._track_operation_failure()
            logger.error(f"Error creating batch records: {e}")
            capture_exception(e)
            raise Exception(f"Failed to create batch records: {e}")
    
    def update_record(self, record_id: str, fields: Dict) -> Dict:
        """
        Update an existing record.
        
        Args:
            record_id: Airtable record ID
            fields: Dictionary of fields to update
        
        Returns:
            Updated record
        
        Raises:
            Exception: If update fails
        """
        # Validate fields (partial validation for updates)
        for field_name, value in fields.items():
            if field_name in self.TABLE_SCHEMA:
                schema = self.TABLE_SCHEMA[field_name]
                
                # Basic type validation
                if schema['type'] == 'number' and not isinstance(value, (int, float)):
                    raise ValueError(f"Field {field_name} must be a number")
                elif schema['type'] == 'url' and not value.startswith(('http://', 'https://')):
                    raise ValueError(f"Field {field_name} must be a valid URL")
                elif schema['type'] == 'checkbox' and not isinstance(value, bool):
                    raise ValueError(f"Field {field_name} must be a boolean")
        
        # Enforce rate limiting
        self._enforce_rate_limit()
        
        try:
            if PYAIRTABLE_AVAILABLE:
                # Use pyairtable
                result = self.table.update(record_id, fields)
            else:
                # Use requests implementation
                url = f"{self.API_BASE_URL}/{self.base_id}/{self.table_name}/{record_id}"
                payload = {"fields": fields}
                
                response = self.session.patch(
                    url,
                    json=payload,
                    timeout=int(os.getenv('REQUEST_TIMEOUT', '30'))
                )
                
                if response.status_code == 200:
                    result = response.json()
                else:
                    response.raise_for_status()
            
            # Track success
            self._track_operation_success('update')
            logger.info(f"Record updated successfully: {record_id}")
            return result
            
        except Exception as e:
            self._track_operation_failure()
            logger.error(f"Error updating record {record_id}: {e}")
            capture_exception(e)
            raise Exception(f"Failed to update record: {e}")
    
    def get_record(self, record_id: str) -> Dict:
        """
        Get a single record by ID.
        
        Args:
            record_id: Airtable record ID
        
        Returns:
            Record data
        
        Raises:
            Exception: If retrieval fails
        """
        # Enforce rate limiting
        self._enforce_rate_limit()
        
        try:
            if PYAIRTABLE_AVAILABLE:
                # Use pyairtable
                result = self.table.get(record_id)
            else:
                # Use requests implementation
                url = f"{self.API_BASE_URL}/{self.base_id}/{self.table_name}/{record_id}"
                
                response = self.session.get(
                    url,
                    timeout=int(os.getenv('REQUEST_TIMEOUT', '30'))
                )
                
                if response.status_code == 200:
                    result = response.json()
                else:
                    response.raise_for_status()
            
            # Track success
            self._track_operation_success('query')
            return result
            
        except Exception as e:
            self._track_operation_failure()
            logger.error(f"Error getting record {record_id}: {e}")
            capture_exception(e)
            raise Exception(f"Failed to get record: {e}")
    
    def query_records(
        self,
        formula: Optional[str] = None,
        sort: Optional[List[Dict]] = None,
        max_records: Optional[int] = None,
        fields: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Query records with filters and sorting.
        
        Args:
            formula: Airtable formula for filtering
            sort: List of sort specifications
            max_records: Maximum number of records to return
            fields: Specific fields to retrieve
        
        Returns:
            List of matching records
        
        Raises:
            Exception: If query fails
        """
        # Enforce rate limiting
        self._enforce_rate_limit()
        
        try:
            if PYAIRTABLE_AVAILABLE:
                # Use pyairtable
                kwargs = {}
                if formula:
                    kwargs['formula'] = formula
                if sort:
                    kwargs['sort'] = sort
                if max_records:
                    kwargs['max_records'] = max_records
                if fields:
                    kwargs['fields'] = fields
                
                result = self.table.all(**kwargs)
            else:
                # Use requests implementation
                url = f"{self.API_BASE_URL}/{self.base_id}/{self.table_name}"
                params = {}
                
                if formula:
                    params['filterByFormula'] = formula
                if max_records:
                    params['maxRecords'] = max_records
                if fields:
                    params['fields'] = fields
                if sort:
                    for i, sort_spec in enumerate(sort):
                        params[f'sort[{i}][field]'] = sort_spec['field']
                        params[f'sort[{i}][direction]'] = sort_spec.get('direction', 'asc')
                
                response = self.session.get(
                    url,
                    params=params,
                    timeout=int(os.getenv('REQUEST_TIMEOUT', '60'))
                )
                
                if response.status_code == 200:
                    result = response.json().get('records', [])
                else:
                    response.raise_for_status()
            
            # Track success
            self._track_operation_success('query', len(result))
            logger.info(f"Query returned {len(result)} records")
            return result
            
        except Exception as e:
            self._track_operation_failure()
            logger.error(f"Error querying records: {e}")
            capture_exception(e)
            raise Exception(f"Failed to query records: {e}")
    
    def delete_record(self, record_id: str) -> bool:
        """
        Delete a record by ID.
        
        Args:
            record_id: Airtable record ID
        
        Returns:
            True if deletion successful
        
        Raises:
            Exception: If deletion fails
        """
        # Enforce rate limiting
        self._enforce_rate_limit()
        
        try:
            if PYAIRTABLE_AVAILABLE:
                # Use pyairtable
                result = self.table.delete(record_id)
                success = result.get('deleted', False)
            else:
                # Use requests implementation
                url = f"{self.API_BASE_URL}/{self.base_id}/{self.table_name}/{record_id}"
                
                response = self.session.delete(
                    url,
                    timeout=int(os.getenv('REQUEST_TIMEOUT', '30'))
                )
                
                success = response.status_code == 200
                if not success:
                    response.raise_for_status()
            
            if success:
                self._track_operation_success('delete')
                logger.info(f"Record deleted successfully: {record_id}")
            return success
            
        except Exception as e:
            self._track_operation_failure()
            logger.error(f"Error deleting record {record_id}: {e}")
            capture_exception(e)
            raise Exception(f"Failed to delete record: {e}")
    
    def _track_operation_success(self, operation_type: str, count: int = 1):
        """Track successful operations."""
        self.operation_stats['total_operations'] += 1
        self.operation_stats['successful_operations'] += 1
        
        if operation_type == 'create':
            self.operation_stats['records_created'] += count
        elif operation_type == 'batch_create':
            self.operation_stats['records_created'] += count
        elif operation_type == 'update':
            self.operation_stats['records_updated'] += count
        elif operation_type == 'query':
            self.operation_stats['records_queried'] += count
    
    def _track_operation_failure(self):
        """Track failed operations."""
        self.operation_stats['total_operations'] += 1
        self.operation_stats['failed_operations'] += 1
    
    def get_operation_stats(self) -> Dict:
        """
        Get operation statistics.
        
        Returns:
            Dictionary with operation statistics
        """
        stats = self.operation_stats.copy()
        
        if stats['total_operations'] > 0:
            stats['success_rate'] = stats['successful_operations'] / stats['total_operations']
        
        return stats
    
    def validate_connection(self) -> bool:
        """
        Test connection to Airtable base and table.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to get base information or a limited query
            records = self.query_records(max_records=1)
            logger.info("Airtable connection validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Airtable connection validation failed: {e}")
            capture_exception(e)
            return False


def main():
    """Test the Airtable uploader."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Initialize uploader
        uploader = AirtableUploader()
        
        # Test connection
        if not uploader.validate_connection():
            print("Connection validation failed")
            return 1
        
        # Create a test record
        test_record = ImageRecord(
            search_query="test sunset",
            source_url="https://example.com/source",
            image_url="https://example.com/image.jpg",
            title="Test Sunset Image",
            description="Beautiful sunset for testing",
            relevance_score=0.95,
            quality_score=0.88,
            selected=True,
            timestamp=datetime.now().isoformat() + 'Z'
        )
        
        print("Creating test record...")
        result = uploader.create_record(test_record)
        print(f"Created record with ID: {result['id']}")
        
        # Update the record
        print("Updating record...")
        updated = uploader.update_record(
            result['id'],
            {"Quality Score": 0.92, "Tags": ["test", "sunset"]}
        )
        print(f"Updated record: {updated['id']}")
        
        # Query records
        print("Querying records...")
        records = uploader.query_records(
            formula="AND({Selected}=TRUE(), {Relevance Score}>0.9)",
            max_records=5
        )
        print(f"Found {len(records)} matching records")
        
        # Show statistics
        stats = uploader.get_operation_stats()
        print(f"\nOperation Statistics:")
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.4f}")
            else:
                print(f"  {key}: {value}")
        
        # Clean up test record
        print(f"Deleting test record...")
        uploader.delete_record(result['id'])
        print("Test record deleted")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())