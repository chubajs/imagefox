#!/usr/bin/env python3
"""
Unit tests for OpenRouter client module.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import tempfile
import requests

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openrouter_client import (
    OpenRouterClient, ModelCapability, ModelInfo, AnalysisResult
)
from dataclasses import asdict


class TestOpenRouterClient(unittest.TestCase):
    """Test cases for OpenRouterClient class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Set test API key
        os.environ['OPENROUTER_API_KEY'] = 'test_api_key'
        os.environ['OPENROUTER_RATE_LIMIT'] = '10'
        
        # Sample API responses
        self.mock_analysis_response = {
            "id": "gen-test123",
            "model": "anthropic/claude-3-sonnet",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": json.dumps({
                            "description": "A beautiful landscape with mountains and lake",
                            "objects": ["mountain", "lake", "trees", "sky"],
                            "scene_type": "landscape",
                            "colors": ["blue", "green", "brown"],
                            "composition": "Rule of thirds with strong foreground",
                            "quality_score": 0.85,
                            "relevance_score": 0.90,
                            "technical_details": {
                                "resolution": "high",
                                "lighting": "natural"
                            }
                        })
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
        }
        
        self.mock_validation_response = {
            "id": "gen-validation",
            "model": "anthropic/claude-3-haiku",
            "choices": [
                {
                    "message": {
                        "content": "Hello"
                    }
                }
            ]
        }
        
        # Sample image data
        self.sample_image_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82"
    
    def tearDown(self):
        """Clean up after tests."""
        if 'OPENROUTER_API_KEY' in os.environ:
            del os.environ['OPENROUTER_API_KEY']
    
    def test_initialization_with_api_key(self):
        """Test client initialization with API key."""
        client = OpenRouterClient(api_key='test_key')
        self.assertEqual(client.api_key, 'test_key')
        self.assertEqual(client.rate_limit, 10)
    
    def test_initialization_from_environment(self):
        """Test client initialization from environment variable."""
        client = OpenRouterClient()
        self.assertEqual(client.api_key, 'test_api_key')
    
    def test_initialization_without_api_key(self):
        """Test client initialization fails without API key."""
        del os.environ['OPENROUTER_API_KEY']
        with self.assertRaises(ValueError) as context:
            OpenRouterClient()
        self.assertIn('OPENROUTER_API_KEY', str(context.exception))
    
    def test_model_registry_content(self):
        """Test that model registry contains expected models."""
        client = OpenRouterClient()
        
        # Check that all expected models are present
        expected_models = [
            "openai/gpt-4-vision-preview",
            "anthropic/claude-3-opus",
            "anthropic/claude-3-sonnet",
            "anthropic/claude-3-haiku",
            "google/gemini-pro-vision"
        ]
        
        for model_id in expected_models:
            self.assertIn(model_id, client.MODEL_REGISTRY)
            model_info = client.MODEL_REGISTRY[model_id]
            self.assertIsInstance(model_info, ModelInfo)
            self.assertIn(ModelCapability.VISION, model_info.capabilities)
    
    def test_select_model_quality_priority(self):
        """Test model selection with quality priority."""
        client = OpenRouterClient()
        model = client.select_model(quality_priority=True, cost_priority=False)
        
        # Should select highest quality model (Claude 3 Opus)
        self.assertEqual(model, "anthropic/claude-3-opus")
    
    def test_select_model_cost_priority(self):
        """Test model selection with cost priority."""
        client = OpenRouterClient()
        model = client.select_model(quality_priority=False, cost_priority=True)
        
        # Should select lowest cost model
        model_info = client.MODEL_REGISTRY[model]
        self.assertIn(ModelCapability.COST_EFFECTIVE, model_info.capabilities)
    
    def test_encode_image_base64(self):
        """Test base64 encoding of image files."""
        client = OpenRouterClient()
        
        # Create temporary image file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_file.write(self.sample_image_data)
            temp_path = temp_file.name
        
        try:
            # Test encoding
            result = client.encode_image_base64(temp_path)
            
            # Should start with data URI
            self.assertTrue(result.startswith('data:image/png;base64,'))
            
            # Should contain base64 data
            self.assertIn(',', result)
            base64_part = result.split(',')[1]
            self.assertGreater(len(base64_part), 0)
            
        finally:
            # Clean up
            os.unlink(temp_path)
    
    def test_encode_image_different_formats(self):
        """Test encoding different image formats."""
        client = OpenRouterClient()
        
        formats = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        expected_mimes = [
            'image/jpeg', 'image/jpeg', 'image/png', 'image/gif', 'image/webp'
        ]
        
        for ext, expected_mime in zip(formats, expected_mimes):
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_file:
                temp_file.write(self.sample_image_data)
                temp_path = temp_file.name
            
            try:
                result = client.encode_image_base64(temp_path)
                self.assertTrue(result.startswith(f'data:{expected_mime};base64,'))
            finally:
                os.unlink(temp_path)
    
    @patch('openrouter_client.requests.Session')
    def test_validate_api_key_success(self, mock_session_class):
        """Test successful API key validation."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_validation_response
        mock_session.post.return_value = mock_response
        
        # Test
        client = OpenRouterClient()
        result = client.validate_api_key()
        
        # Assertions
        self.assertTrue(result)
        mock_session.post.assert_called_once()
    
    @patch('openrouter_client.requests.Session')
    def test_validate_api_key_no_credits(self, mock_session_class):
        """Test API key validation with no credits (but valid key)."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 402  # Payment required but key valid
        mock_session.post.return_value = mock_response
        
        # Test
        client = OpenRouterClient()
        result = client.validate_api_key()
        
        # Should still return True as key is valid
        self.assertTrue(result)
    
    @patch('openrouter_client.requests.Session')
    def test_validate_api_key_failure(self, mock_session_class):
        """Test failed API key validation."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_session.post.return_value = mock_response
        
        # Test
        client = OpenRouterClient()
        result = client.validate_api_key()
        
        # Assertions
        self.assertFalse(result)
    
    @patch('openrouter_client.requests.Session')
    def test_analyze_image_url_success(self, mock_session_class):
        """Test successful image analysis with URL."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_analysis_response
        mock_session.post.return_value = mock_response
        
        # Test
        client = OpenRouterClient()
        result = client.analyze_image("https://example.com/image.jpg", model="anthropic/claude-3-sonnet")
        
        # Assertions
        self.assertIsInstance(result, AnalysisResult)
        self.assertEqual(result.description, "A beautiful landscape with mountains and lake")
        self.assertEqual(result.objects, ["mountain", "lake", "trees", "sky"])
        self.assertEqual(result.scene_type, "landscape")
        self.assertEqual(result.quality_score, 0.85)
        self.assertEqual(result.relevance_score, 0.90)
        self.assertEqual(result.model_used, "anthropic/claude-3-sonnet")
        self.assertGreater(result.processing_time, 0)
        
        # Check API call
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        payload = call_args[1]['json']
        
        # Check payload structure
        self.assertIn('model', payload)
        self.assertIn('messages', payload)
        self.assertEqual(len(payload['messages']), 1)
        
        # Check message content
        message = payload['messages'][0]
        self.assertEqual(message['role'], 'user')
        self.assertEqual(len(message['content']), 2)
        self.assertEqual(message['content'][0]['type'], 'text')
        self.assertEqual(message['content'][1]['type'], 'image_url')
        self.assertEqual(message['content'][1]['image_url']['url'], "https://example.com/image.jpg")
    
    @patch('openrouter_client.requests.Session')
    def test_analyze_image_base64_input(self, mock_session_class):
        """Test image analysis with base64 input."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_analysis_response
        mock_session.post.return_value = mock_response
        
        # Test
        client = OpenRouterClient()
        base64_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        result = client.analyze_image(base64_data)
        
        # Should use the base64 data directly
        call_args = mock_session.post.call_args
        payload = call_args[1]['json']
        message = payload['messages'][0]
        image_url = message['content'][1]['image_url']['url']
        self.assertEqual(image_url, base64_data)
    
    @patch('openrouter_client.requests.Session')
    def test_analyze_image_file_path(self, mock_session_class):
        """Test image analysis with file path."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_analysis_response
        mock_session.post.return_value = mock_response
        
        # Create temporary image file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_file.write(self.sample_image_data)
            temp_path = temp_file.name
        
        try:
            # Test
            client = OpenRouterClient()
            result = client.analyze_image(temp_path)
            
            # Check that base64 encoding was used
            call_args = mock_session.post.call_args
            payload = call_args[1]['json']
            message = payload['messages'][0]
            image_url = message['content'][1]['image_url']['url']
            self.assertTrue(image_url.startswith('data:image/png;base64,'))
            
        finally:
            os.unlink(temp_path)
    
    @patch('openrouter_client.requests.Session')
    def test_analyze_image_custom_prompt(self, mock_session_class):
        """Test image analysis with custom prompt."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_analysis_response
        mock_session.post.return_value = mock_response
        
        # Test
        client = OpenRouterClient()
        custom_prompt = "Describe only the colors in this image"
        result = client.analyze_image("https://example.com/image.jpg", prompt=custom_prompt)
        
        # Check that custom prompt was used
        call_args = mock_session.post.call_args
        payload = call_args[1]['json']
        message = payload['messages'][0]
        text_content = message['content'][0]['text']
        self.assertEqual(text_content, custom_prompt)
    
    @patch('openrouter_client.requests.Session')
    def test_analyze_image_rate_limit_error(self, mock_session_class):
        """Test handling of rate limit errors."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = Exception("Rate limit exceeded")
        mock_session.post.return_value = mock_response
        
        # Test
        client = OpenRouterClient()
        with self.assertRaises(Exception) as context:
            client.analyze_image("https://example.com/image.jpg")
        self.assertIn('Rate limit exceeded', str(context.exception))
    
    @patch('openrouter_client.requests.Session')
    def test_analyze_image_insufficient_credits(self, mock_session_class):
        """Test handling of insufficient credits error."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 402
        mock_session.post.return_value = mock_response
        
        # Test
        client = OpenRouterClient()
        with self.assertRaises(Exception) as context:
            client.analyze_image("https://example.com/image.jpg")
        self.assertIn('Insufficient OpenRouter credits', str(context.exception))
    
    @patch('openrouter_client.requests.Session')
    def test_analyze_image_fallback_on_failure(self, mock_session_class):
        """Test fallback to different model on failure."""
        # Setup mock to fail first, succeed second
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # First call raises exception
        mock_session.post.side_effect = [
            requests.RequestException("Network error"),
            MagicMock(status_code=200, json=lambda: self.mock_analysis_response)
        ]
        
        # Test
        client = OpenRouterClient()
        client.fallback_model = "anthropic/claude-3-haiku"
        result = client.analyze_image("https://example.com/image.jpg", model="openai/gpt-4-vision-preview")
        
        # Should succeed with fallback model
        self.assertIsInstance(result, AnalysisResult)
        self.assertEqual(mock_session.post.call_count, 2)
    
    def test_parse_analysis_response_valid_json(self):
        """Test parsing of valid JSON response."""
        client = OpenRouterClient()
        result = client._parse_analysis_response(
            self.mock_analysis_response, 
            "anthropic/claude-3-sonnet", 
            1.5
        )
        
        self.assertIsInstance(result, AnalysisResult)
        self.assertEqual(result.description, "A beautiful landscape with mountains and lake")
        self.assertEqual(result.processing_time, 1.5)
        self.assertEqual(result.model_used, "anthropic/claude-3-sonnet")
        self.assertGreater(result.cost_estimate, 0)
    
    def test_parse_analysis_response_invalid_json(self):
        """Test parsing of invalid JSON response with fallback."""
        client = OpenRouterClient()
        
        # Create response with non-JSON content
        invalid_response = {
            "choices": [
                {
                    "message": {
                        "content": "This is just plain text, not JSON"
                    }
                }
            ]
        }
        
        result = client._parse_analysis_response(
            invalid_response,
            "test-model",
            1.0
        )
        
        # Should create fallback result
        self.assertIsInstance(result, AnalysisResult)
        self.assertEqual(result.description, "This is just plain text, not JSON")
        self.assertEqual(result.objects, [])
        self.assertEqual(result.quality_score, 0.5)
    
    def test_track_usage(self):
        """Test usage tracking functionality."""
        client = OpenRouterClient()
        
        # Track some usage
        client._track_usage(self.mock_analysis_response, "anthropic/claude-3-sonnet")
        
        stats = client.get_usage_stats()
        
        # Check overall stats
        self.assertEqual(stats['total_requests'], 1)
        self.assertEqual(stats['total_tokens'], 150)
        self.assertGreater(stats['total_cost'], 0)
        
        # Check model-specific stats
        self.assertIn('anthropic/claude-3-sonnet', stats['model_usage'])
        model_stats = stats['model_usage']['anthropic/claude-3-sonnet']
        self.assertEqual(model_stats['requests'], 1)
        self.assertEqual(model_stats['tokens'], 150)
        self.assertGreater(model_stats['cost'], 0)
    
    def test_get_available_models(self):
        """Test getting available models."""
        client = OpenRouterClient()
        models = client.get_available_models()
        
        self.assertIsInstance(models, list)
        self.assertGreater(len(models), 0)
        
        for model in models:
            self.assertIsInstance(model, ModelInfo)
            self.assertIn(ModelCapability.VISION, model.capabilities)
    
    @patch('openrouter_client.time.sleep')
    def test_rate_limiting(self, mock_sleep):
        """Test rate limiting enforcement."""
        client = OpenRouterClient()
        client.rate_limit = 2  # Set low limit for testing
        
        # Add requests to simulate hitting rate limit
        current_time = 1000.0
        with patch('openrouter_client.time.time', return_value=current_time):
            client.requests_per_minute = [current_time - 30, current_time - 20]
            client._enforce_rate_limit()
            
            # Should sleep since we're at the limit
            mock_sleep.assert_called_once()
            sleep_time = mock_sleep.call_args[0][0]
            self.assertGreater(sleep_time, 0)
    
    def test_model_info_dataclass(self):
        """Test ModelInfo dataclass functionality."""
        model = ModelInfo(
            id="test-model",
            name="Test Model",
            capabilities=[ModelCapability.VISION, ModelCapability.FAST],
            cost_per_token=0.001,
            max_tokens=1000,
            context_length=4000,
            quality_score=8.0
        )
        
        self.assertEqual(model.id, "test-model")
        self.assertEqual(model.name, "Test Model")
        self.assertIn(ModelCapability.VISION, model.capabilities)
        self.assertEqual(model.cost_per_token, 0.001)
        
        # Test conversion to dict
        model_dict = asdict(model)
        self.assertIn('id', model_dict)
        self.assertIn('capabilities', model_dict)
    
    def test_analysis_result_dataclass(self):
        """Test AnalysisResult dataclass functionality."""
        result = AnalysisResult(
            description="Test description",
            objects=["object1", "object2"],
            scene_type="test",
            colors=["red", "blue"],
            composition="test composition",
            quality_score=0.8,
            relevance_score=0.9,
            technical_details={"key": "value"},
            model_used="test-model",
            processing_time=1.5,
            cost_estimate=0.001
        )
        
        self.assertEqual(result.description, "Test description")
        self.assertEqual(len(result.objects), 2)
        self.assertEqual(result.quality_score, 0.8)
        
        # Test conversion to dict
        result_dict = asdict(result)
        self.assertIn('description', result_dict)
        self.assertIn('processing_time', result_dict)


if __name__ == '__main__':
    unittest.main()