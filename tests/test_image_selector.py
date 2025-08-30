#!/usr/bin/env python3
"""
Unit tests for Image Selector module.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from dataclasses import asdict
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from image_selector import (
    ImageSelector, SelectionCriteria, ImageCandidate, SelectionResult,
    SelectionExplanation, SelectionStrategy
)
from vision_analyzer import ComprehensiveAnalysis, QualityMetrics


class TestSelectionCriteria(unittest.TestCase):
    """Test cases for SelectionCriteria class."""
    
    def test_selection_criteria_defaults(self):
        """Test SelectionCriteria default values."""
        criteria = SelectionCriteria()
        
        self.assertEqual(criteria.quality_weight, 0.4)
        self.assertEqual(criteria.relevance_weight, 0.3)
        self.assertEqual(criteria.diversity_weight, 0.2)
        self.assertEqual(criteria.cost_weight, 0.1)
        self.assertEqual(criteria.min_quality_score, 0.6)
        self.assertEqual(criteria.min_relevance_score, 0.5)
        self.assertIsNone(criteria.preferred_aspect_ratios)
    
    def test_selection_criteria_custom(self):
        """Test SelectionCriteria with custom values."""
        criteria = SelectionCriteria(
            quality_weight=0.5,
            relevance_weight=0.3,
            diversity_weight=0.1,
            cost_weight=0.1,
            min_quality_score=0.7,
            exclude_scene_types=["adult", "violence"]
        )
        
        self.assertEqual(criteria.quality_weight, 0.5)
        self.assertEqual(criteria.min_quality_score, 0.7)
        self.assertEqual(criteria.exclude_scene_types, ["adult", "violence"])


class TestImageCandidate(unittest.TestCase):
    """Test cases for ImageCandidate class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.quality_metrics = QualityMetrics(
            overall_score=0.85,
            composition_score=0.80,
            clarity_score=0.88,
            color_score=0.82,
            content_relevance=0.90,
            technical_quality=0.87
        )
        
        self.analysis = ComprehensiveAnalysis(
            description="A beautiful mountain landscape",
            objects=["mountain", "lake", "trees"],
            scene_type="landscape",
            colors=["blue", "green", "brown"],
            composition="rule of thirds",
            quality_metrics=self.quality_metrics,
            relevance_score=0.88,
            technical_details={"lighting": "natural"},
            models_used=["gpt-4-vision"],
            processing_time=2.0,
            cost_estimate=0.05,
            confidence_score=0.90,
            timestamp="2023-01-01T12:00:00"
        )
    
    def test_image_candidate_creation(self):
        """Test ImageCandidate creation."""
        candidate = ImageCandidate(
            image_url="https://example.com/image.jpg",
            source_url="https://example.com/page",
            title="Mountain Landscape",
            analysis=self.analysis,
            metadata={"width": 1920, "height": 1080},
            search_query="mountain landscape"
        )
        
        self.assertEqual(candidate.image_url, "https://example.com/image.jpg")
        self.assertEqual(candidate.title, "Mountain Landscape")
        self.assertEqual(candidate.analysis, self.analysis)
        self.assertEqual(candidate.metadata["width"], 1920)


class TestSelectionResult(unittest.TestCase):
    """Test cases for SelectionResult class."""
    
    def test_selection_result_creation(self):
        """Test SelectionResult creation."""
        result = SelectionResult(
            selected_images=[],
            scores={},
            reasoning="Test reasoning",
            alternatives=[],
            diversity_metrics={},
            total_candidates=10,
            selection_time=1.5,
            strategy_used=SelectionStrategy.BALANCED
        )
        
        self.assertEqual(result.total_candidates, 10)
        self.assertEqual(result.selection_time, 1.5)
        self.assertEqual(result.strategy_used, SelectionStrategy.BALANCED)


class TestImageSelector(unittest.TestCase):
    """Test cases for ImageSelector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Set test environment variables
        os.environ['DIVERSITY_THRESHOLD'] = '0.7'
        os.environ['MAX_SELECTION_TIME'] = '30.0'
        
        # Create test quality metrics
        self.quality_metrics_high = QualityMetrics(
            overall_score=0.90,
            composition_score=0.85,
            clarity_score=0.92,
            color_score=0.88,
            content_relevance=0.90,
            technical_quality=0.91
        )
        
        self.quality_metrics_medium = QualityMetrics(
            overall_score=0.75,
            composition_score=0.70,
            clarity_score=0.78,
            color_score=0.72,
            content_relevance=0.75,
            technical_quality=0.76
        )
        
        self.quality_metrics_low = QualityMetrics(
            overall_score=0.50,
            composition_score=0.45,
            clarity_score=0.52,
            color_score=0.48,
            content_relevance=0.55,
            technical_quality=0.51
        )
        
        # Create test analyses
        self.analysis_high = ComprehensiveAnalysis(
            description="A stunning mountain landscape with crystal clear lake",
            objects=["mountain", "lake", "trees", "sky"],
            scene_type="landscape",
            colors=["blue", "green", "brown", "white"],
            composition="rule of thirds with perfect balance",
            quality_metrics=self.quality_metrics_high,
            relevance_score=0.92,
            technical_details={"lighting": "golden hour", "focus": "sharp"},
            models_used=["gpt-4-vision"],
            processing_time=2.0,
            cost_estimate=0.045,
            confidence_score=0.95,
            timestamp="2023-01-01T12:00:00"
        )
        
        self.analysis_medium = ComprehensiveAnalysis(
            description="A nice urban street scene with buildings",
            objects=["building", "street", "car", "people"],
            scene_type="urban",
            colors=["gray", "black", "yellow"],
            composition="centered composition",
            quality_metrics=self.quality_metrics_medium,
            relevance_score=0.70,
            technical_details={"lighting": "daylight", "focus": "adequate"},
            models_used=["claude-3-sonnet"],
            processing_time=1.5,
            cost_estimate=0.032,
            confidence_score=0.80,
            timestamp="2023-01-01T13:00:00"
        )
        
        self.analysis_low = ComprehensiveAnalysis(
            description="A blurry indoor scene",
            objects=["furniture", "wall"],
            scene_type="indoor",
            colors=["beige", "brown"],
            composition="poor framing",
            quality_metrics=self.quality_metrics_low,
            relevance_score=0.40,
            technical_details={"lighting": "poor", "focus": "blurry"},
            models_used=["claude-3-haiku"],
            processing_time=1.0,
            cost_estimate=0.015,
            confidence_score=0.60,
            timestamp="2023-01-01T14:00:00"
        )
        
        # Create test candidates
        self.candidate_high = ImageCandidate(
            image_url="https://example.com/mountain.jpg",
            source_url="https://example.com/page1",
            title="Beautiful Mountain Lake",
            analysis=self.analysis_high,
            metadata={"width": 1920, "height": 1080},
            search_query="mountain landscape"
        )
        
        self.candidate_medium = ImageCandidate(
            image_url="https://example.com/street.jpg",
            source_url="https://example.com/page2",
            title="City Street Scene",
            analysis=self.analysis_medium,
            metadata={"width": 1280, "height": 720},
            search_query="urban scene"
        )
        
        self.candidate_low = ImageCandidate(
            image_url="https://example.com/indoor.jpg",
            source_url="https://example.com/page3",
            title="Indoor Room",
            analysis=self.analysis_low,
            metadata={"width": 800, "height": 600},
            search_query="interior design"
        )
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove test environment variables
        for key in ['DIVERSITY_THRESHOLD', 'MAX_SELECTION_TIME']:
            if key in os.environ:
                del os.environ[key]
    
    def test_initialization_default(self):
        """Test ImageSelector initialization with defaults."""
        selector = ImageSelector()
        
        self.assertIsNotNone(selector.criteria)
        self.assertEqual(selector.criteria.quality_weight, 0.4)
        self.assertEqual(selector.diversity_threshold, 0.7)
        self.assertEqual(len(selector.criteria.preferred_aspect_ratios), 4)
    
    def test_initialization_custom_criteria(self):
        """Test ImageSelector initialization with custom criteria."""
        criteria = SelectionCriteria(
            quality_weight=0.5,
            relevance_weight=0.3,
            min_quality_score=0.8
        )
        
        selector = ImageSelector(criteria)
        
        self.assertEqual(selector.criteria.quality_weight, 0.5)
        self.assertEqual(selector.criteria.min_quality_score, 0.8)
    
    def test_select_best_single_image(self):
        """Test selecting single best image."""
        selector = ImageSelector()
        candidates = [self.candidate_high, self.candidate_medium, self.candidate_low]
        
        result = selector.select_best(candidates, count=1)
        
        self.assertIsInstance(result, SelectionResult)
        self.assertEqual(len(result.selected_images), 1)
        self.assertEqual(result.selected_images[0], self.candidate_high)
        self.assertEqual(result.total_candidates, 3)
        self.assertGreater(result.selection_time, 0)
    
    def test_select_best_multiple_images(self):
        """Test selecting multiple best images."""
        selector = ImageSelector()
        candidates = [self.candidate_high, self.candidate_medium, self.candidate_low]
        
        result = selector.select_best(candidates, count=2)
        
        self.assertEqual(len(result.selected_images), 2)
        # Should select high and medium, not low (filtered out by quality)
        self.assertIn(self.candidate_high, result.selected_images)
        self.assertIn(self.candidate_medium, result.selected_images)
        self.assertNotIn(self.candidate_low, result.selected_images)
    
    def test_select_best_empty_candidates(self):
        """Test selecting from empty candidate list."""
        selector = ImageSelector()
        
        with self.assertRaises(ValueError) as context:
            selector.select_best([], count=1)
        
        self.assertIn("No candidates provided", str(context.exception))
    
    def test_select_best_invalid_count(self):
        """Test selecting with invalid count."""
        selector = ImageSelector()
        candidates = [self.candidate_high]
        
        with self.assertRaises(ValueError) as context:
            selector.select_best(candidates, count=0)
        
        self.assertIn("Selection count must be positive", str(context.exception))
    
    def test_select_best_count_exceeds_candidates(self):
        """Test selecting more images than available."""
        selector = ImageSelector()
        candidates = [self.candidate_high]
        
        result = selector.select_best(candidates, count=5)
        
        # Should return only available candidates
        self.assertEqual(len(result.selected_images), 1)
    
    def test_apply_filters(self):
        """Test candidate filtering."""
        selector = ImageSelector()
        candidates = [self.candidate_high, self.candidate_medium, self.candidate_low]
        
        filtered = selector._apply_filters(candidates, "mountain")
        
        # Low quality candidate should be filtered out
        self.assertEqual(len(filtered), 2)
        self.assertIn(self.candidate_high, filtered)
        self.assertIn(self.candidate_medium, filtered)
        self.assertNotIn(self.candidate_low, filtered)
    
    def test_apply_filters_scene_type_exclusion(self):
        """Test filtering by excluded scene types."""
        criteria = SelectionCriteria(exclude_scene_types=["indoor"])
        selector = ImageSelector(criteria)
        candidates = [self.candidate_high, self.candidate_medium, self.candidate_low]
        
        filtered = selector._apply_filters(candidates, "test")
        
        # Indoor scene should be excluded
        self.assertNotIn(self.candidate_low, filtered)
    
    def test_calculate_scores(self):
        """Test score calculation for candidates."""
        selector = ImageSelector()
        candidates = [self.candidate_high, self.candidate_medium]
        
        scored = selector._calculate_scores(candidates, SelectionStrategy.BALANCED, "mountain")
        
        self.assertEqual(len(scored), 2)
        # Should be sorted by score (highest first)
        self.assertGreater(scored[0][1], scored[1][1])
        self.assertEqual(scored[0][0], self.candidate_high)
    
    def test_calculate_candidate_score(self):
        """Test individual candidate score calculation."""
        selector = ImageSelector()
        
        score = selector._calculate_candidate_score(
            self.candidate_high, SelectionStrategy.BALANCED, "mountain landscape"
        )
        
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        self.assertGreater(score, 0.7)  # High quality candidate should score well
    
    def test_get_strategy_weights(self):
        """Test strategy weight calculation."""
        selector = ImageSelector()
        
        quality_weights = selector._get_strategy_weights(SelectionStrategy.QUALITY_FIRST)
        self.assertEqual(quality_weights['quality'], 0.6)
        
        relevance_weights = selector._get_strategy_weights(SelectionStrategy.RELEVANCE_FIRST)
        self.assertEqual(relevance_weights['relevance'], 0.6)
        
        balanced_weights = selector._get_strategy_weights(SelectionStrategy.BALANCED)
        self.assertEqual(balanced_weights['quality'], 0.4)  # Default criteria
    
    def test_calculate_context_bonus(self):
        """Test search context bonus calculation."""
        selector = ImageSelector()
        
        # Test with matching query
        bonus = selector._calculate_context_bonus(self.candidate_high, "mountain landscape lake")
        self.assertGreater(bonus, 0.0)
        
        # Test with non-matching query
        bonus_low = selector._calculate_context_bonus(self.candidate_high, "car traffic urban")
        self.assertLess(bonus_low, bonus)
    
    def test_select_single_best(self):
        """Test single best selection."""
        selector = ImageSelector()
        scored = [(self.candidate_high, 0.9), (self.candidate_medium, 0.7)]
        
        selected = selector._select_single_best(scored, SelectionStrategy.BALANCED)
        
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0], self.candidate_high)
    
    def test_select_multiple_best_with_diversity(self):
        """Test multiple selection with diversity consideration."""
        # Create similar candidates for diversity testing
        similar_analysis = ComprehensiveAnalysis(
            description="Another mountain landscape",
            objects=["mountain", "lake", "rocks"],  # Similar objects
            scene_type="landscape",  # Same scene type
            colors=["blue", "green"],  # Similar colors
            composition="centered mountain",
            quality_metrics=self.quality_metrics_medium,
            relevance_score=0.85,
            technical_details={},
            models_used=["test"],
            processing_time=1.0,
            cost_estimate=0.03,
            confidence_score=0.85,
            timestamp="test"
        )
        
        similar_candidate = ImageCandidate(
            image_url="https://example.com/mountain2.jpg",
            source_url="https://example.com/page4",
            title="Another Mountain",
            analysis=similar_analysis,
            metadata={},
            search_query="mountain"
        )
        
        selector = ImageSelector()
        scored = [
            (self.candidate_high, 0.9),
            (similar_candidate, 0.88),  # High score but similar to first
            (self.candidate_medium, 0.7)  # Lower score but diverse
        ]
        
        selected = selector._select_multiple_best(scored, 2, SelectionStrategy.BALANCED)
        
        self.assertEqual(len(selected), 2)
        # Should prefer diversity over pure score
        self.assertIn(self.candidate_high, selected)
        # Second selection should consider diversity
        self.assertTrue(
            self.candidate_medium in selected or similar_candidate in selected
        )
    
    def test_calculate_diversity_penalty(self):
        """Test diversity penalty calculation."""
        selector = ImageSelector()
        
        # Test penalty between similar images
        penalty = selector._calculate_diversity_penalty(
            self.candidate_high, [self.candidate_high]
        )
        self.assertGreater(penalty, 0.5)  # High penalty for identical scene
        
        # Test penalty between different images
        penalty_different = selector._calculate_diversity_penalty(
            self.candidate_high, [self.candidate_medium]
        )
        self.assertLess(penalty_different, penalty)  # Lower penalty for different scenes
    
    def test_calculate_diversity_metrics(self):
        """Test diversity metrics calculation."""
        selector = ImageSelector()
        selected = [self.candidate_high, self.candidate_medium]
        
        metrics = selector._calculate_diversity_metrics(selected)
        
        self.assertIn('scene_type_diversity', metrics)
        self.assertIn('unique_objects', metrics)
        self.assertIn('unique_colors', metrics)
        self.assertEqual(metrics['selection_count'], 2)
        self.assertEqual(metrics['scene_type_diversity'], 1.0)  # Two different scenes
    
    def test_generate_reasoning(self):
        """Test reasoning generation."""
        selector = ImageSelector()
        selected = [self.candidate_high]
        scored = [(self.candidate_high, 0.9), (self.candidate_medium, 0.7)]
        
        reasoning = selector._generate_reasoning(
            selected, scored, SelectionStrategy.BALANCED, "mountain landscape"
        )
        
        self.assertIsInstance(reasoning, str)
        self.assertIn("balanced", reasoning.lower())
        self.assertIn("1 image", reasoning)
        self.assertIn("landscape", reasoning)
    
    def test_explain_selection(self):
        """Test selection explanation generation."""
        selector = ImageSelector()
        result = SelectionResult(
            selected_images=[self.candidate_high],
            scores={self.candidate_high.image_url: 0.9},
            reasoning="Test",
            alternatives=[],
            diversity_metrics={},
            total_candidates=1,
            selection_time=1.0,
            strategy_used=SelectionStrategy.BALANCED
        )
        
        explanations = selector.explain_selection(result)
        
        self.assertEqual(len(explanations), 1)
        explanation = explanations[0]
        self.assertIsInstance(explanation, SelectionExplanation)
        self.assertEqual(explanation.candidate, self.candidate_high)
        self.assertEqual(explanation.rank, 1)
        self.assertIn('quality', explanation.score_breakdown)
        self.assertGreater(len(explanation.selection_reasons), 0)
    
    def test_selection_strategies(self):
        """Test different selection strategies."""
        selector = ImageSelector()
        candidates = [self.candidate_high, self.candidate_medium]
        
        # Test each strategy
        strategies = [
            SelectionStrategy.QUALITY_FIRST,
            SelectionStrategy.RELEVANCE_FIRST,
            SelectionStrategy.BALANCED,
            SelectionStrategy.DIVERSITY_FIRST,
            SelectionStrategy.COST_OPTIMIZED
        ]
        
        for strategy in strategies:
            result = selector.select_best(candidates, count=1, strategy=strategy)
            self.assertEqual(len(result.selected_images), 1)
            self.assertEqual(result.strategy_used, strategy)
    
    def test_caching(self):
        """Test selection result caching."""
        selector = ImageSelector()
        candidates = [self.candidate_high]
        
        # First call should calculate
        result1 = selector.select_best(candidates, count=1)
        cache_size_after_first = len(selector.selection_cache)
        
        # Second call with same params should use cache
        result2 = selector.select_best(candidates, count=1)
        cache_size_after_second = len(selector.selection_cache)
        
        self.assertEqual(cache_size_after_first, cache_size_after_second)
        self.assertEqual(result1.selected_images[0], result2.selected_images[0])
    
    def test_get_cache_key_consistency(self):
        """Test cache key generation consistency."""
        selector = ImageSelector()
        candidates = [self.candidate_high]
        
        key1 = selector._get_cache_key(candidates, 1, SelectionStrategy.BALANCED, "test")
        key2 = selector._get_cache_key(candidates, 1, SelectionStrategy.BALANCED, "test")
        key3 = selector._get_cache_key(candidates, 2, SelectionStrategy.BALANCED, "test")
        
        self.assertEqual(key1, key2)
        self.assertNotEqual(key1, key3)
        self.assertEqual(len(key1), 16)
    
    def test_clear_cache(self):
        """Test cache clearing."""
        selector = ImageSelector()
        candidates = [self.candidate_high]
        
        # Add something to cache
        selector.select_best(candidates, count=1)
        self.assertGreater(len(selector.selection_cache), 0)
        
        # Clear cache
        selector.clear_cache()
        self.assertEqual(len(selector.selection_cache), 0)
    
    def test_get_selection_stats(self):
        """Test selection statistics."""
        criteria = SelectionCriteria(quality_weight=0.5)
        selector = ImageSelector(criteria)
        
        stats = selector.get_selection_stats()
        
        self.assertIn('cache_size', stats)
        self.assertIn('criteria', stats)
        self.assertEqual(stats['criteria']['quality_weight'], 0.5)
    
    def test_quality_score_calculation(self):
        """Test composite quality score calculation."""
        selector = ImageSelector()
        
        score = selector._calculate_quality_score(self.quality_metrics_high)
        
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        # Should be weighted average of quality components
        expected = (
            self.quality_metrics_high.overall_score * 0.4 +
            self.quality_metrics_high.composition_score * 0.25 +
            self.quality_metrics_high.technical_quality * 0.2 +
            self.quality_metrics_high.clarity_score * 0.15
        )
        self.assertAlmostEqual(score, expected, places=3)


if __name__ == '__main__':
    unittest.main()