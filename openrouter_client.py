#!/usr/bin/env python3
"""
OpenRouter Vision LLM API client for ImageFox.

This module provides a robust client for interacting with OpenRouter's
vision-capable language models for image analysis.
"""

import os
import json
import base64
import time
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import sentry_sdk
from sentry_sdk import capture_exception

logger = logging.getLogger(__name__)


class ModelCapability(Enum):
    """Model capability flags."""
    VISION = "vision"
    FAST = "fast"
    HIGH_QUALITY = "high_quality"
    COST_EFFECTIVE = "cost_effective"


@dataclass
class ModelInfo:
    """Information about a vision model."""
    id: str
    name: str
    capabilities: List[ModelCapability]
    cost_per_token: float  # Average cost for backward compatibility
    max_tokens: int
    context_length: int
    quality_score: float  # 1-10 scale
    input_cost_per_million: Optional[float] = None  # Cost per 1M input tokens
    output_cost_per_million: Optional[float] = None  # Cost per 1M output tokens


@dataclass
class AnalysisResult:
    """Structured result from image analysis."""
    description: str
    objects: List[str]
    scene_type: str
    colors: List[str]
    composition: str
    quality_score: float
    relevance_score: float
    technical_details: Dict[str, Any]
    model_used: str
    processing_time: float
    cost_estimate: float


class OpenRouterClient:
    """Client for OpenRouter Vision API."""
    
    API_BASE_URL = "https://openrouter.ai/api/v1"
    
    # Model registry with capabilities and costs
    MODEL_REGISTRY = {
        "openai/gpt-4-vision-preview": ModelInfo(
            id="openai/gpt-4-vision-preview",
            name="GPT-4 Vision Preview",
            capabilities=[ModelCapability.VISION, ModelCapability.HIGH_QUALITY],
            cost_per_token=0.01,
            max_tokens=4096,
            context_length=128000,
            quality_score=9.0
        ),
        "anthropic/claude-3-opus": ModelInfo(
            id="anthropic/claude-3-opus",
            name="Claude 3 Opus",
            capabilities=[ModelCapability.VISION, ModelCapability.HIGH_QUALITY],
            cost_per_token=0.015,
            max_tokens=4096,
            context_length=200000,
            quality_score=9.5
        ),
        "anthropic/claude-3-sonnet": ModelInfo(
            id="anthropic/claude-3-sonnet",
            name="Claude 3 Sonnet",
            capabilities=[ModelCapability.VISION, ModelCapability.COST_EFFECTIVE],
            cost_per_token=0.003,
            max_tokens=4096,
            context_length=200000,
            quality_score=8.5
        ),
        "anthropic/claude-3.5-sonnet": ModelInfo(
            id="anthropic/claude-3.5-sonnet",
            name="Claude 3.5 Sonnet",
            capabilities=[ModelCapability.VISION, ModelCapability.HIGH_QUALITY],
            cost_per_token=0.003,
            max_tokens=8192,
            context_length=200000,
            quality_score=9.2
        ),
        "anthropic/claude-sonnet-4": ModelInfo(
            id="anthropic/claude-sonnet-4",
            name="Claude Sonnet 4",
            capabilities=[ModelCapability.VISION, ModelCapability.HIGH_QUALITY],
            cost_per_token=0.000009,  # Average of $3/M input + $15/M output = ~$9/M average
            max_tokens=8192,
            context_length=1000000,  # 1M context window
            quality_score=9.5,
            input_cost_per_million=3.0,  # $3/M input tokens
            output_cost_per_million=15.0  # $15/M output tokens
        ),
        "anthropic/claude-3-haiku": ModelInfo(
            id="anthropic/claude-3-haiku",
            name="Claude 3 Haiku",
            capabilities=[ModelCapability.VISION, ModelCapability.FAST, ModelCapability.COST_EFFECTIVE],
            cost_per_token=0.00025,
            max_tokens=4096,
            context_length=200000,
            quality_score=7.5
        ),
        "google/gemini-pro-vision": ModelInfo(
            id="google/gemini-pro-vision",
            name="Gemini Pro Vision",
            capabilities=[ModelCapability.VISION, ModelCapability.FAST],
            cost_per_token=0.00025,
            max_tokens=2048,
            context_length=32000,
            quality_score=8.0
        ),
        "google/gemini-2.0-flash-exp:free": ModelInfo(
            id="google/gemini-2.0-flash-exp:free",
            name="Gemini 2.0 Flash Experimental",
            capabilities=[ModelCapability.VISION, ModelCapability.FAST, ModelCapability.COST_EFFECTIVE],
            cost_per_token=0.0,  # Free tier
            max_tokens=8192,
            context_length=1000000,  # 1M context window
            quality_score=8.8
        ),
        "google/gemini-2.0-flash-lite-001": ModelInfo(
            id="google/gemini-2.0-flash-lite-001",
            name="Gemini 2.0 Flash Lite",
            capabilities=[ModelCapability.VISION, ModelCapability.FAST, ModelCapability.COST_EFFECTIVE],
            cost_per_token=0.0000001875,  # Average of input/output for backward compatibility
            max_tokens=8192,
            context_length=1048576,  # 1M+ context window
            quality_score=8.5,
            input_cost_per_million=0.075,  # $0.075/M input tokens
            output_cost_per_million=0.30  # $0.30/M output tokens
        ),
        "anthropic/claude-sonnet-4": ModelInfo(
            id="anthropic/claude-sonnet-4",
            name="Claude Sonnet 4",
            capabilities=[ModelCapability.VISION, ModelCapability.HIGH_QUALITY],
            cost_per_token=0.000009,  # Average for backward compatibility
            max_tokens=8192,
            context_length=1000000,
            quality_score=9.5,
            input_cost_per_million=3.0,   # $3/M input tokens
            output_cost_per_million=15.0  # $15/M output tokens
        )
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenRouter client.
        
        Args:
            api_key: OpenRouter API key. If not provided, reads from environment.
        
        Raises:
            ValueError: If API key is not provided or found in environment.
        """
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not provided or found in environment")
        
        # Configuration
        self.rate_limit = int(os.getenv('OPENROUTER_RATE_LIMIT', '50'))
        self.default_model = os.getenv('DEFAULT_VISION_MODEL', 'openai/gpt-4-vision-preview')
        self.fallback_model = os.getenv('FALLBACK_VISION_MODEL', 'anthropic/claude-3-sonnet')
        
        # Rate limiting
        self.requests_per_minute = []
        
        # Usage tracking
        self.usage_stats = {
            'total_requests': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'model_usage': {}
        }
        
        # Setup session
        self.session = self._create_session()
        
        logger.info("OpenRouter client initialized")
    
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
        
        # Set default headers
        session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://imagefox.cccrafts.ai',
            'X-Title': 'ImageFox'
        })
        
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
    
    def select_model(self, quality_priority: bool = True, cost_priority: bool = False) -> str:
        """
        Select the best available model based on criteria.
        
        Args:
            quality_priority: Prioritize high quality models
            cost_priority: Prioritize cost-effective models
        
        Returns:
            Selected model ID
        """
        if cost_priority:
            # Sort by cost (ascending)
            sorted_models = sorted(
                self.MODEL_REGISTRY.values(),
                key=lambda m: m.cost_per_token
            )
        elif quality_priority:
            # Sort by quality (descending)
            sorted_models = sorted(
                self.MODEL_REGISTRY.values(),
                key=lambda m: m.quality_score,
                reverse=True
            )
        else:
            # Default order
            sorted_models = list(self.MODEL_REGISTRY.values())
        
        # Return the first available model
        for model in sorted_models:
            if ModelCapability.VISION in model.capabilities:
                return model.id
        
        # Fallback to default
        return self.default_model
    
    def encode_image_base64(self, image_path: str) -> str:
        """
        Encode image file to base64.
        
        Args:
            image_path: Path to image file
        
        Returns:
            Base64 encoded image with data URI prefix
        """
        try:
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
                base64_data = base64.b64encode(image_data).decode('utf-8')
                
                # Determine MIME type
                extension = os.path.splitext(image_path)[1].lower()
                mime_types = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg', 
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp'
                }
                mime_type = mime_types.get(extension, 'image/jpeg')
                
                return f"data:{mime_type};base64,{base64_data}"
                
        except Exception as e:
            logger.error(f"Error encoding image: {e}")
            capture_exception(e)
            raise
    
    def analyze_image(
        self,
        image_input: Union[str, bytes],
        prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> AnalysisResult:
        """
        Analyze an image using vision LLM.
        
        Args:
            image_input: Image file path, URL, or base64 data
            prompt: Optional custom analysis prompt
            model: Model to use (if not specified, auto-selects)
            max_tokens: Maximum response tokens
            temperature: Response randomness (0-1)
        
        Returns:
            Structured analysis results
        
        Raises:
            Exception: If analysis fails
        """
        start_time = time.time()
        
        # Select model if not specified
        if not model:
            model = self.select_model()
        
        # Prepare image data
        if image_input.startswith('http'):
            # URL - pass directly
            image_url = image_input
        elif image_input.startswith('data:'):
            # Already base64 encoded
            image_url = image_input
        else:
            # File path - encode to base64
            image_url = self.encode_image_base64(image_input)
        
        # Default analysis prompt
        if not prompt:
            prompt = """Analyze this image in detail. Provide a comprehensive description including:

1. Overall scene and subject matter
2. Objects and elements visible
3. Colors, lighting, and composition
4. Image quality and technical aspects
5. Relevance to search queries (if any)

Format your response as JSON with these fields:
- description: detailed text description
- objects: list of objects/subjects identified
- scene_type: category of scene (portrait, landscape, product, etc.)
- colors: dominant colors present
- composition: composition style and quality
- quality_score: technical quality rating 0-1
- relevance_score: relevance to typical search needs 0-1
- technical_details: any technical observations"""
        
        # Enforce rate limiting
        self._enforce_rate_limit()
        
        # Prepare request
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "response_format": {"type": "json_object"}
        }
        
        try:
            # Make API request
            response = self.session.post(
                f"{self.API_BASE_URL}/chat/completions",
                json=payload,
                timeout=int(os.getenv('REQUEST_TIMEOUT', '60'))
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse response
                result = self._parse_analysis_response(
                    data, model, processing_time
                )
                
                # Track usage
                self._track_usage(data, model)
                
                return result
                
            elif response.status_code == 402:
                raise Exception("Insufficient OpenRouter credits")
            elif response.status_code == 429:
                raise Exception("Rate limit exceeded")
            else:
                response.raise_for_status()
                
        except (requests.RequestException, Exception) as e:
            logger.error(f"Error analyzing image: {e}")
            capture_exception(e)
            
            # Try fallback model if primary failed
            if model != self.fallback_model:
                logger.info(f"Retrying with fallback model: {self.fallback_model}")
                return self.analyze_image(
                    image_input, prompt, self.fallback_model, max_tokens, temperature
                )
            else:
                raise
    
    def _parse_analysis_response(
        self, 
        response_data: Dict, 
        model: str, 
        processing_time: float
    ) -> AnalysisResult:
        """
        Parse API response into structured result.
        
        Args:
            response_data: Raw API response
            model: Model used for analysis
            processing_time: Time taken for processing
        
        Returns:
            Structured analysis result
        """
        try:
            choice = response_data['choices'][0]
            content = choice['message']['content']
            
            # Debug logging
            logger.debug(f"Raw API response content: {content[:200]}...")
            
            if not content or content.strip() == '':
                raise ValueError("Empty response content from API")
            
            # Parse JSON response
            analysis_data = json.loads(content)
            
            # Calculate cost estimate
            usage = response_data.get('usage', {})
            total_tokens = usage.get('total_tokens', 0)
            model_info = self.MODEL_REGISTRY.get(model)
            cost_estimate = total_tokens * model_info.cost_per_token if model_info else 0.0
            
            # Create structured result
            result = AnalysisResult(
                description=analysis_data.get('description', ''),
                objects=analysis_data.get('objects', []),
                scene_type=analysis_data.get('scene_type', 'unknown'),
                colors=analysis_data.get('colors', []),
                composition=analysis_data.get('composition', ''),
                quality_score=float(analysis_data.get('quality_score', 0.5)),
                relevance_score=float(analysis_data.get('relevance_score', 0.5)),
                technical_details=analysis_data.get('technical_details', {}),
                model_used=model,
                processing_time=processing_time,
                cost_estimate=cost_estimate
            )
            
            logger.info(f"Image analyzed successfully using {model}")
            return result
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error parsing analysis response: {e}")
            
            # Create fallback result from raw content
            content = response_data.get('choices', [{}])[0].get('message', {}).get('content', '')
            return AnalysisResult(
                description=content[:500],  # Truncate if too long
                objects=[],
                scene_type='unknown',
                colors=[],
                composition='',
                quality_score=0.5,
                relevance_score=0.5,
                technical_details={},
                model_used=model,
                processing_time=processing_time,
                cost_estimate=0.0
            )
    
    def _track_usage(self, response_data: Dict, model: str):
        """Track API usage statistics."""
        usage = response_data.get('usage', {})
        total_tokens = usage.get('total_tokens', 0)
        
        model_info = self.MODEL_REGISTRY.get(model)
        cost = total_tokens * model_info.cost_per_token if model_info else 0.0
        
        self.usage_stats['total_requests'] += 1
        self.usage_stats['total_tokens'] += total_tokens
        self.usage_stats['total_cost'] += cost
        
        if model not in self.usage_stats['model_usage']:
            self.usage_stats['model_usage'][model] = {
                'requests': 0,
                'tokens': 0,
                'cost': 0.0
            }
        
        self.usage_stats['model_usage'][model]['requests'] += 1
        self.usage_stats['model_usage'][model]['tokens'] += total_tokens
        self.usage_stats['model_usage'][model]['cost'] += cost
    
    def get_available_models(self) -> List[ModelInfo]:
        """
        Get list of available vision models.
        
        Returns:
            List of model information
        """
        return list(self.MODEL_REGISTRY.values())
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get API usage statistics.
        
        Returns:
            Dictionary with usage statistics
        """
        return self.usage_stats.copy()
    
    def validate_api_key(self) -> bool:
        """
        Test API connectivity and validate API key.
        
        Returns:
            True if API key is valid, False otherwise.
        """
        try:
            # Make a simple test request
            payload = {
                "model": "anthropic/claude-3-haiku",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 5
            }
            
            response = self.session.post(
                f"{self.API_BASE_URL}/chat/completions",
                json=payload,
                timeout=10
            )
            
            if response.status_code in [200, 402]:  # 402 = no credits but key valid
                logger.info("OpenRouter API key validated successfully")
                return True
            else:
                logger.error(f"API key validation failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            capture_exception(e)
            return False


def main():
    """Test the OpenRouter client."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Initialize client
        client = OpenRouterClient()
        
        # Validate API key
        if not client.validate_api_key():
            print("API key validation failed")
            return 1
        
        # Show available models
        models = client.get_available_models()
        print(f"\nAvailable models ({len(models)}):")
        for model in models:
            print(f"  - {model.name} (${model.cost_per_token:.5f}/token)")
        
        # Test analysis with a public image URL
        test_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
        
        print(f"\nAnalyzing test image...")
        result = client.analyze_image(test_url, model="anthropic/claude-3-haiku")
        
        print(f"\nAnalysis Results:")
        print(f"Description: {result.description[:200]}...")
        print(f"Scene Type: {result.scene_type}")
        print(f"Objects: {', '.join(result.objects[:5])}")
        print(f"Quality Score: {result.quality_score:.2f}")
        print(f"Model Used: {result.model_used}")
        print(f"Processing Time: {result.processing_time:.2f}s")
        print(f"Cost Estimate: ${result.cost_estimate:.6f}")
        
        # Show usage stats
        stats = client.get_usage_stats()
        print(f"\nUsage Statistics: {json.dumps(stats, indent=2)}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())