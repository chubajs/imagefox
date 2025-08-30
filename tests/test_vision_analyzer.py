#!/usr/bin/env python3
"""
Unit tests for Vision Analyzer module.
"""

import os
import sys
import unittest
import json
from unittest.mock import patch, MagicMock, call
from dataclasses import asdict
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vision_analyzer import (
    VisionAnalyzer, ImageMetadata, QualityMetrics, 
    ComprehensiveAnalysis
)
from openrouter_client import AnalysisResult, ModelInfo, ModelCapability


class TestImageMetadata(unittest.TestCase):
    """Test cases for ImageMetadata class."""
    
    def test_image_metadata_creation(self):
        """Test ImageMetadata creation."""
        metadata = ImageMetadata(
            url="https://example.com/image.jpg",
            title="Test Image",
            source_url="https://example.com/page",
            width=1920,
            height=1080,
            file_size=1048576,
            format="JPEG"
        )
        
        self.assertEqual(metadata.url, "https://example.com/image.jpg")
        self.assertEqual(metadata.width, 1920)
        self.assertEqual(metadata.height, 1080)
        self.assertEqual(metadata.format, "JPEG")
    
    def test_image_metadata_optional_fields(self):
        """Test ImageMetadata with only required fields."""
        metadata = ImageMetadata(
            url="https://example.com/image.jpg",
            title="Test Image",
            source_url="https://example.com/page"
        )
        
        self.assertIsNone(metadata.width)
        self.assertIsNone(metadata.height)
        self.assertIsNone(metadata.file_size)
        self.assertIsNone(metadata.format)


class TestQualityMetrics(unittest.TestCase):
    """Test cases for QualityMetrics class."""
    
    def test_quality_metrics_creation(self):
        """Test QualityMetrics creation."""
        metrics = QualityMetrics(
            overall_score=0.95,
            composition_score=0.90,
            clarity_score=0.92,
            color_score=0.88,
            content_relevance=0.85,
            technical_quality=0.94
        )
        
        self.assertEqual(metrics.overall_score, 0.95)
        self.assertEqual(metrics.composition_score, 0.90)
        self.assertEqual(metrics.content_relevance, 0.85)


class TestComprehensiveAnalysis(unittest.TestCase):
    """Test cases for ComprehensiveAnalysis class."""
    
    def test_comprehensive_analysis_creation(self):
        """Test ComprehensiveAnalysis creation."""
        quality_metrics = QualityMetrics(
            overall_score=0.95,
            composition_score=0.90,
            clarity_score=0.92,
            color_score=0.88,
            content_relevance=0.85,
            technical_quality=0.94
        )
        
        analysis = ComprehensiveAnalysis(
            description="A beautiful landscape scene",
            objects=["mountain", "lake", "trees"],
            scene_type="landscape",
            colors=["blue", "green", "brown"],
            composition="rule of thirds with mountain in background",
            quality_metrics=quality_metrics,
            relevance_score=0.90,
            technical_details={"lighting": "natural daylight"},
            models_used=["openai/gpt-4-vision-preview"],
            processing_time=2.5,
            cost_estimate=0.05,
            confidence_score=0.85,
            timestamp="2023-01-01T12:00:00"
        )
        
        self.assertEqual(analysis.scene_type, "landscape")
        self.assertEqual(len(analysis.objects), 3)
        self.assertEqual(analysis.quality_metrics.overall_score, 0.95)


class TestVisionAnalyzer(unittest.TestCase):
    """Test cases for VisionAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Set test environment variables
        os.environ['ANALYSIS_CONSENSUS_THRESHOLD'] = '0.7'
        os.environ['QUALITY_WEIGHT'] = '0.4'
        os.environ['RELEVANCE_WEIGHT'] = '0.6'
        os.environ['ENABLE_MULTI_MODEL_ANALYSIS'] = 'true'
        
        # Mock OpenRouter client
        self.mock_client = MagicMock()
        
        # Sample analysis result
        self.mock_analysis_result = AnalysisResult(
            description="A beautiful mountain landscape with a lake",
            objects=["mountain", "lake", "trees", "sky"],
            scene_type="landscape",
            colors=["blue", "green", "brown", "white"],
            composition="Centered composition with mountain as focal point",
            quality_score=0.92,
            relevance_score=0.88,
            technical_details={
                "lighting": "Natural daylight with good exposure",
                "perspective": "Wide angle landscape view",
                "focus": "Sharp focus throughout the scene",
                "exposure": "Well balanced exposure"
            },
            model_used="openai/gpt-4-vision-preview",
            processing_time=2.3,
            cost_estimate=0.045
        )
        
        # Second analysis result for multi-model testing
        self.mock_analysis_result_2 = AnalysisResult(
            description="Scenic mountain view with pristine lake reflection",
            objects=["mountain", "water", "vegetation", "clouds"],
            scene_type="nature",
            colors=["azure", "emerald", "earth tones"],
            composition="Rule of thirds with mountain positioned off-center",
            quality_score=0.89,
            relevance_score=0.91,
            technical_details={
                "lighting": "Golden hour lighting with warm tones",
                "perspective": "Elevated viewpoint",
                "focus": "Excellent depth of field",
                "exposure": "Slightly overexposed highlights"
            },
            model_used="anthropic/claude-3-opus",
            processing_time=1.8,
            cost_estimate=0.038
        )
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove test environment variables
        for key in ['ANALYSIS_CONSENSUS_THRESHOLD', 'QUALITY_WEIGHT', 
                   'RELEVANCE_WEIGHT', 'ENABLE_MULTI_MODEL_ANALYSIS']:
            if key in os.environ:
                del os.environ[key]
    
    def test_initialization(self):
        """Test VisionAnalyzer initialization."""
        analyzer = VisionAnalyzer(openrouter_client=self.mock_client)
        
        self.assertEqual(analyzer.openrouter_client, self.mock_client)
        self.assertEqual(analyzer.consensus_threshold, 0.7)
        self.assertEqual(analyzer.quality_weight, 0.4)
        self.assertEqual(analyzer.relevance_weight, 0.6)
        self.assertTrue(analyzer.enable_multi_model)
    
    def test_initialization_with_defaults(self):
        """Test VisionAnalyzer initialization with default client."""
        with patch('vision_analyzer.OpenRouterClient') as mock_client_class:
            mock_instance = MagicMock()
            mock_client_class.return_value = mock_instance
            
            analyzer = VisionAnalyzer()
            
            self.assertEqual(analyzer.openrouter_client, mock_instance)
            mock_client_class.assert_called_once()
    
    def test_single_model_analysis_success(self):
        """Test successful single model analysis."""
        self.mock_client.analyze_image.return_value = self.mock_analysis_result
        
        analyzer = VisionAnalyzer(openrouter_client=self.mock_client)
        result = analyzer._single_model_analysis(
            "https://example.com/image.jpg",
            "mountain landscape",
            None
        )
        
        self.assertIsInstance(result, ComprehensiveAnalysis)
        self.assertEqual(result.description, self.mock_analysis_result.description)
        self.assertEqual(len(result.objects), 4)
        self.assertEqual(result.scene_type, "landscape")
        self.assertEqual(len(result.models_used), 1)
        self.mock_client.analyze_image.assert_called_once()
    
    def test_single_model_analysis_with_fallback(self):
        """Test single model analysis with fallback to secondary model."""
        # First model fails, second succeeds
        self.mock_client.analyze_image.side_effect = [
            Exception("Primary model failed"),
            self.mock_analysis_result
        ]
        
        analyzer = VisionAnalyzer(openrouter_client=self.mock_client)
        result = analyzer._single_model_analysis(
            "https://example.com/image.jpg",
            "mountain landscape",
            None
        )
        
        self.assertIsInstance(result, ComprehensiveAnalysis)
        self.assertEqual(result.description, self.mock_analysis_result.description)
        self.assertEqual(self.mock_client.analyze_image.call_count, 2)
    
    def test_single_model_analysis_all_models_fail(self):
        """Test single model analysis when all models fail."""
        self.mock_client.analyze_image.side_effect = Exception("All models failed")
        
        analyzer = VisionAnalyzer(openrouter_client=self.mock_client)
        
        with self.assertRaises(Exception) as context:
            analyzer._single_model_analysis(
                "https://example.com/image.jpg",
                "mountain landscape",
                None
            )
        
        self.assertIn("All vision models failed", str(context.exception))
    
    def test_multi_model_analysis_success(self):
        """Test successful multi-model analysis."""
        self.mock_client.analyze_image.side_effect = [
            self.mock_analysis_result,
            self.mock_analysis_result_2
        ]
        
        analyzer = VisionAnalyzer(openrouter_client=self.mock_client)
        result = analyzer._multi_model_analysis(
            "https://example.com/image.jpg",
            "mountain landscape",
            None
        )
        
        self.assertIsInstance(result, ComprehensiveAnalysis)
        self.assertEqual(len(result.models_used), 2)
        self.assertGreater(result.confidence_score, 0.5)
        # Should have consensus objects (mountain appears in both)
        self.assertIn("mountain", result.objects)
        self.assertEqual(self.mock_client.analyze_image.call_count, 2)
    
    def test_multi_model_analysis_single_success(self):
        """Test multi-model analysis with only one model succeeding."""
        self.mock_client.analyze_image.side_effect = [
            self.mock_analysis_result,
            Exception("Second model failed")
        ]
        
        analyzer = VisionAnalyzer(openrouter_client=self.mock_client)
        result = analyzer._multi_model_analysis(
            "https://example.com/image.jpg",
            "mountain landscape",
            None
        )
        
        self.assertIsInstance(result, ComprehensiveAnalysis)
        self.assertEqual(len(result.models_used), 1)
        self.assertEqual(result.description, self.mock_analysis_result.description)
    
    def test_analyze_image_with_url(self):
        """Test analyze_image with URL input."""
        self.mock_client.analyze_image.return_value = self.mock_analysis_result
        
        analyzer = VisionAnalyzer(openrouter_client=self.mock_client)
        result = analyzer.analyze_image(
            "https://example.com/image.jpg",
            search_query="mountain landscape"
        )
        
        self.assertIsInstance(result, ComprehensiveAnalysis)
        self.assertGreater(result.processing_time, 0)
        self.assertTrue(result.timestamp)
    
    def test_analyze_image_with_metadata(self):
        """Test analyze_image with ImageMetadata input."""
        self.mock_client.analyze_image.return_value = self.mock_analysis_result
        
        metadata = ImageMetadata(
            url="https://example.com/image.jpg",
            title="Test Image",
            source_url="https://example.com/page",
            width=1920,
            height=1080
        )
        
        analyzer = VisionAnalyzer(openrouter_client=self.mock_client)
        result = analyzer.analyze_image(
            metadata,
            search_query="mountain landscape"
        )
        
        self.assertIsInstance(result, ComprehensiveAnalysis)
        self.assertIn('source_metadata', result.technical_details)
        self.assertEqual(
            result.technical_details['source_metadata']['width'], 
            1920
        )
    
    def test_analyze_image_with_cache(self):
        """Test analyze_image caching functionality."""
        self.mock_client.analyze_image.return_value = self.mock_analysis_result
        
        analyzer = VisionAnalyzer(openrouter_client=self.mock_client)
        
        # First call should hit the API (disable multi-model for predictable count)
        result1 = analyzer.analyze_image(
            "https://example.com/image.jpg", 
            enable_multi_model=False
        )
        self.assertEqual(self.mock_client.analyze_image.call_count, 1)
        
        # Second call with same input should use cache
        result2 = analyzer.analyze_image(
            "https://example.com/image.jpg",
            enable_multi_model=False
        )
        self.assertEqual(self.mock_client.analyze_image.call_count, 1)  # Still 1
        
        # Results should be identical
        self.assertEqual(result1.description, result2.description)
    
    def test_find_consensus_items(self):
        """Test consensus finding for object lists."""
        analyzer = VisionAnalyzer(openrouter_client=self.mock_client)
        
        items = ["mountain", "Mountain", "lake", "trees", "sky", "mountain", "Lake"]
        consensus = analyzer._find_consensus_items(items, min_frequency=2)
        
        # Should find mountain and lake (case insensitive)
        self.assertIn("mountain", [item.lower() for item in consensus])
        self.assertIn("lake", [item.lower() for item in consensus])
        self.assertEqual(len(consensus), 2)
    
    def test_calculate_consensus_confidence(self):
        """Test consensus confidence calculation."""
        analyzer = VisionAnalyzer(openrouter_client=self.mock_client)
        
        # High agreement results
        results_high_agreement = [
            self.mock_analysis_result,
            AnalysisResult(
                description="Similar description",
                objects=["mountain", "lake"],
                scene_type="landscape",
                colors=["blue", "green"],
                composition="good composition",
                quality_score=0.91,  # Very close to 0.92
                relevance_score=0.89,  # Very close to 0.88
                technical_details={},
                model_used="test",
                processing_time=1.0,
                cost_estimate=0.01
            )
        ]
        
        confidence_high = analyzer._calculate_consensus_confidence(results_high_agreement)
        self.assertGreater(confidence_high, 0.7)
        
        # Low agreement results
        results_low_agreement = [
            self.mock_analysis_result,
            AnalysisResult(
                description="Different description",
                objects=["car", "building"],
                scene_type="urban",
                colors=["red", "black"],
                composition="different composition",
                quality_score=0.3,  # Very different from 0.92
                relevance_score=0.2,  # Very different from 0.88
                technical_details={},
                model_used="test",
                processing_time=1.0,
                cost_estimate=0.01
            )
        ]
        
        confidence_low = analyzer._calculate_consensus_confidence(results_low_agreement)
        self.assertLess(confidence_low, confidence_high)
    
    def test_build_quality_metrics(self):
        """Test quality metrics building."""
        analyzer = VisionAnalyzer(openrouter_client=self.mock_client)
        
        results = [self.mock_analysis_result, self.mock_analysis_result_2]
        metrics = analyzer._build_quality_metrics(results)
        
        self.assertIsInstance(metrics, QualityMetrics)
        # Should average the quality scores: (0.92 + 0.89) / 2 = 0.905
        self.assertAlmostEqual(metrics.overall_score, 0.905, places=2)
        self.assertAlmostEqual(metrics.content_relevance, (0.88 + 0.91) / 2, places=2)
    
    def test_calculate_selection_score(self):
        """Test selection score calculation."""
        analyzer = VisionAnalyzer(openrouter_client=self.mock_client)
        
        quality_metrics = QualityMetrics(
            overall_score=0.9,
            composition_score=0.85,
            clarity_score=0.88,
            color_score=0.87,
            content_relevance=0.82,
            technical_quality=0.91
        )
        
        analysis = ComprehensiveAnalysis(
            description="Test",
            objects=["test"],
            scene_type="test",
            colors=["test"],
            composition="test",
            quality_metrics=quality_metrics,
            relevance_score=0.85,
            technical_details={},
            models_used=["test"],
            processing_time=1.0,
            cost_estimate=0.01,
            confidence_score=0.9,
            timestamp="test"
        )
        
        score = analyzer.calculate_selection_score(analysis, "test query")
        
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        # With good scores and high confidence, should be relatively high
        self.assertGreater(score, 0.7)
    
    def test_build_analysis_prompt_with_query(self):
        """Test analysis prompt building with search query."""
        analyzer = VisionAnalyzer(openrouter_client=self.mock_client)
        
        prompt = analyzer._build_analysis_prompt("mountain landscape")
        
        self.assertIn("mountain landscape", prompt)
        self.assertIn("relevance", prompt.lower())
    
    def test_build_analysis_prompt_without_query(self):
        """Test analysis prompt building without search query."""
        analyzer = VisionAnalyzer(openrouter_client=self.mock_client)
        
        prompt = analyzer._build_analysis_prompt(None)
        
        self.assertIn("JSON format", prompt)
        self.assertNotIn("search query", prompt)
    
    def test_get_cache_key_consistency(self):
        """Test cache key generation consistency."""
        analyzer = VisionAnalyzer(openrouter_client=self.mock_client)
        
        key1 = analyzer._get_cache_key("image.jpg", "query", "prompt")
        key2 = analyzer._get_cache_key("image.jpg", "query", "prompt")
        key3 = analyzer._get_cache_key("image.jpg", "different", "prompt")
        
        self.assertEqual(key1, key2)
        self.assertNotEqual(key1, key3)
        self.assertEqual(len(key1), 16)  # Should be 16 character hash
    
    def test_extract_score_from_text(self):
        """Test score extraction from descriptive text."""
        analyzer = VisionAnalyzer(openrouter_client=self.mock_client)
        
        # Text with positive keywords
        positive_text = "excellent clarity and sharp focus with vivid colors"
        positive_score = analyzer._extract_score_from_text(positive_text, 0.8)
        self.assertGreater(positive_score, 0.8)
        
        # Text with negative keywords
        negative_text = "poor quality with blurry details and dark exposure"
        negative_score = analyzer._extract_score_from_text(negative_text, 0.8)
        self.assertLess(negative_score, 0.8)
        
        # Neutral text
        neutral_text = "standard composition with typical framing"
        neutral_score = analyzer._extract_score_from_text(neutral_text, 0.8)
        self.assertEqual(neutral_score, 0.8)
    
    def test_clear_cache(self):
        """Test cache clearing functionality."""
        analyzer = VisionAnalyzer(openrouter_client=self.mock_client)
        
        # Add some items to cache
        analyzer.analysis_cache["key1"] = "value1"
        analyzer.analysis_cache["key2"] = "value2"
        self.assertEqual(len(analyzer.analysis_cache), 2)
        
        # Clear cache
        analyzer.clear_cache()
        self.assertEqual(len(analyzer.analysis_cache), 0)
    
    def test_get_cache_stats(self):
        """Test cache statistics retrieval."""
        analyzer = VisionAnalyzer(openrouter_client=self.mock_client)
        
        # Add some items to cache
        analyzer.analysis_cache["key1"] = "value1"
        analyzer.analysis_cache["key2"] = "value2"
        
        stats = analyzer.get_cache_stats()
        
        self.assertIn('cache_size', stats)
        self.assertEqual(stats['cache_size'], 2)
        self.assertIn('total_analyses', stats)


if __name__ == '__main__':
    unittest.main()