#!/usr/bin/env python3
"""
Image Selector module for ImageFox.

This module provides intelligent image selection using AI-powered decision making
to choose the best images from analysis results based on multiple criteria.
"""

import os
import json
import logging
import statistics
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import sentry_sdk
from sentry_sdk import capture_exception

from vision_analyzer import ComprehensiveAnalysis, QualityMetrics

logger = logging.getLogger(__name__)


class SelectionStrategy(Enum):
    """Selection strategy options."""
    QUALITY_FIRST = "quality_first"
    RELEVANCE_FIRST = "relevance_first"
    BALANCED = "balanced"
    DIVERSITY_FIRST = "diversity_first"
    COST_OPTIMIZED = "cost_optimized"


@dataclass
class SelectionCriteria:
    """Configuration for image selection criteria."""
    quality_weight: float = 0.4
    relevance_weight: float = 0.3
    diversity_weight: float = 0.2
    cost_weight: float = 0.1
    min_quality_score: float = 0.6
    min_relevance_score: float = 0.5
    max_cost_per_image: float = 0.10
    require_unique_objects: bool = True
    max_similar_compositions: int = 2
    preferred_aspect_ratios: List[str] = None
    exclude_scene_types: List[str] = None


@dataclass
class ImageCandidate:
    """Image candidate with analysis results."""
    image_url: str
    source_url: str
    title: str
    analysis: ComprehensiveAnalysis
    metadata: Dict[str, Any]
    search_query: str


@dataclass
class SelectionResult:
    """Result from image selection process."""
    selected_images: List[ImageCandidate]
    scores: Dict[str, float]
    reasoning: str
    alternatives: List[ImageCandidate]
    diversity_metrics: Dict[str, Any]
    total_candidates: int
    selection_time: float
    strategy_used: SelectionStrategy


@dataclass
class SelectionExplanation:
    """Detailed explanation for a selection decision."""
    candidate: ImageCandidate
    final_score: float
    score_breakdown: Dict[str, float]
    selection_reasons: List[str]
    rejection_reasons: List[str]
    rank: int


class ImageSelector:
    """AI-powered image selection with multi-criteria decision making."""
    
    def __init__(self, criteria: Optional[SelectionCriteria] = None):
        """
        Initialize Image Selector.
        
        Args:
            criteria: Selection criteria configuration
        """
        self.criteria = criteria or SelectionCriteria()
        if self.criteria.preferred_aspect_ratios is None:
            self.criteria.preferred_aspect_ratios = ["16:9", "4:3", "1:1", "3:2"]
        if self.criteria.exclude_scene_types is None:
            self.criteria.exclude_scene_types = []
        
        # Configuration from environment
        self.diversity_threshold = float(os.getenv('DIVERSITY_THRESHOLD', '0.7'))
        self.max_processing_time = float(os.getenv('MAX_SELECTION_TIME', '30.0'))
        
        # Caching
        self.selection_cache = {}
        
        logger.info(f"ImageSelector initialized with strategy weights: "
                   f"quality={self.criteria.quality_weight}, "
                   f"relevance={self.criteria.relevance_weight}, "
                   f"diversity={self.criteria.diversity_weight}")
    
    def select_best(
        self,
        candidates: List[ImageCandidate],
        count: int = 1,
        strategy: SelectionStrategy = SelectionStrategy.BALANCED,
        search_query: Optional[str] = None
    ) -> SelectionResult:
        """
        Select the best images from candidates.
        
        Args:
            candidates: List of image candidates with analysis
            count: Number of images to select
            strategy: Selection strategy to use
            search_query: Original search query for context
        
        Returns:
            Selection result with chosen images and explanations
        
        Raises:
            ValueError: If invalid parameters provided
        """
        start_time = datetime.now()
        
        if not candidates:
            raise ValueError("No candidates provided for selection")
        
        if count <= 0:
            raise ValueError("Selection count must be positive")
        
        if count > len(candidates):
            count = len(candidates)
        
        try:
            # Generate cache key
            cache_key = self._get_cache_key(candidates, count, strategy, search_query)
            if cached := self.selection_cache.get(cache_key):
                logger.info("Using cached selection result")
                return cached
            
            # Apply initial filters
            filtered_candidates = self._apply_filters(candidates, search_query)
            
            if not filtered_candidates:
                logger.warning("No candidates passed filtering criteria")
                return SelectionResult(
                    selected_images=[],
                    scores={},
                    reasoning="No candidates met minimum quality and relevance criteria",
                    alternatives=[],
                    diversity_metrics={},
                    total_candidates=len(candidates),
                    selection_time=0.0,
                    strategy_used=strategy
                )
            
            # Calculate scores for all candidates
            scored_candidates = self._calculate_scores(
                filtered_candidates, strategy, search_query
            )
            
            # Perform selection based on strategy
            if count == 1:
                selected = self._select_single_best(scored_candidates, strategy)
            else:
                selected = self._select_multiple_best(
                    scored_candidates, count, strategy
                )
            
            # Calculate diversity metrics
            diversity_metrics = self._calculate_diversity_metrics(selected)
            
            # Generate explanations
            reasoning = self._generate_reasoning(
                selected, scored_candidates, strategy, search_query
            )
            
            # Get alternatives
            alternatives = [
                candidate for candidate, _ in scored_candidates 
                if candidate not in selected
            ][:min(5, len(scored_candidates) - len(selected))]
            
            # Build result
            selection_time = (datetime.now() - start_time).total_seconds()
            
            result = SelectionResult(
                selected_images=selected,
                scores={c.image_url: score for c, score in scored_candidates},
                reasoning=reasoning,
                alternatives=alternatives,
                diversity_metrics=diversity_metrics,
                total_candidates=len(candidates),
                selection_time=selection_time,
                strategy_used=strategy
            )
            
            # Cache result
            self.selection_cache[cache_key] = result
            
            logger.info(f"Selected {len(selected)} images from {len(candidates)} "
                       f"candidates in {selection_time:.2f}s using {strategy.value}")
            
            return result
            
        except Exception as e:
            logger.error(f"Image selection failed: {str(e)}")
            capture_exception(e)
            raise
    
    def _apply_filters(
        self, 
        candidates: List[ImageCandidate], 
        search_query: Optional[str]
    ) -> List[ImageCandidate]:
        """Apply initial filtering based on minimum criteria."""
        filtered = []
        
        for candidate in candidates:
            analysis = candidate.analysis
            
            # Quality filter
            if analysis.quality_metrics.overall_score < self.criteria.min_quality_score:
                continue
            
            # Relevance filter
            if analysis.relevance_score < self.criteria.min_relevance_score:
                continue
            
            # Cost filter
            if analysis.cost_estimate > self.criteria.max_cost_per_image:
                continue
            
            # Scene type filter
            if analysis.scene_type.lower() in [s.lower() for s in self.criteria.exclude_scene_types]:
                continue
            
            filtered.append(candidate)
        
        logger.debug(f"Filtered {len(candidates)} candidates to {len(filtered)}")
        return filtered
    
    def _calculate_scores(
        self,
        candidates: List[ImageCandidate],
        strategy: SelectionStrategy,
        search_query: Optional[str]
    ) -> List[Tuple[ImageCandidate, float]]:
        """Calculate selection scores for all candidates."""
        scored = []
        
        for candidate in candidates:
            score = self._calculate_candidate_score(candidate, strategy, search_query)
            scored.append((candidate, score))
        
        # Sort by score (highest first)
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return scored
    
    def _calculate_candidate_score(
        self,
        candidate: ImageCandidate,
        strategy: SelectionStrategy,
        search_query: Optional[str]
    ) -> float:
        """Calculate selection score for a single candidate."""
        analysis = candidate.analysis
        
        # Base component scores
        quality_score = self._calculate_quality_score(analysis.quality_metrics)
        relevance_score = analysis.relevance_score
        diversity_score = 1.0  # Will be adjusted during batch selection
        cost_score = 1.0 - min(1.0, analysis.cost_estimate / self.criteria.max_cost_per_image)
        
        # Apply strategy-specific weighting
        weights = self._get_strategy_weights(strategy)
        
        final_score = (
            quality_score * weights['quality'] +
            relevance_score * weights['relevance'] +
            diversity_score * weights['diversity'] +
            cost_score * weights['cost']
        )
        
        # Apply confidence multiplier
        final_score *= analysis.confidence_score
        
        # Bonus for matching search context
        if search_query:
            context_bonus = self._calculate_context_bonus(candidate, search_query)
            final_score *= (1.0 + context_bonus)
        
        return min(1.0, max(0.0, final_score))
    
    def _calculate_quality_score(self, quality_metrics: QualityMetrics) -> float:
        """Calculate composite quality score."""
        return (
            quality_metrics.overall_score * 0.4 +
            quality_metrics.composition_score * 0.25 +
            quality_metrics.technical_quality * 0.2 +
            quality_metrics.clarity_score * 0.15
        )
    
    def _get_strategy_weights(self, strategy: SelectionStrategy) -> Dict[str, float]:
        """Get weighting factors for different strategies."""
        if strategy == SelectionStrategy.QUALITY_FIRST:
            return {'quality': 0.6, 'relevance': 0.2, 'diversity': 0.1, 'cost': 0.1}
        elif strategy == SelectionStrategy.RELEVANCE_FIRST:
            return {'quality': 0.2, 'relevance': 0.6, 'diversity': 0.1, 'cost': 0.1}
        elif strategy == SelectionStrategy.DIVERSITY_FIRST:
            return {'quality': 0.2, 'relevance': 0.2, 'diversity': 0.5, 'cost': 0.1}
        elif strategy == SelectionStrategy.COST_OPTIMIZED:
            return {'quality': 0.2, 'relevance': 0.2, 'diversity': 0.1, 'cost': 0.5}
        else:  # BALANCED
            return {
                'quality': self.criteria.quality_weight,
                'relevance': self.criteria.relevance_weight,
                'diversity': self.criteria.diversity_weight,
                'cost': self.criteria.cost_weight
            }
    
    def _calculate_context_bonus(
        self, 
        candidate: ImageCandidate, 
        search_query: str
    ) -> float:
        """Calculate bonus score based on search context."""
        query_words = search_query.lower().split()
        
        # Check objects for query matches
        object_matches = sum(
            1 for obj in candidate.analysis.objects
            for word in query_words
            if word in obj.lower()
        )
        
        # Check description for query matches
        description_matches = sum(
            1 for word in query_words
            if word in candidate.analysis.description.lower()
        )
        
        # Check title for query matches
        title_matches = sum(
            1 for word in query_words
            if word in candidate.title.lower()
        )
        
        total_matches = object_matches + description_matches + title_matches
        max_possible = len(query_words) * 3  # Each word could match in all three places
        
        return min(0.2, total_matches / max_possible) if max_possible > 0 else 0.0
    
    def _select_single_best(
        self,
        scored_candidates: List[Tuple[ImageCandidate, float]],
        strategy: SelectionStrategy
    ) -> List[ImageCandidate]:
        """Select the single best candidate."""
        if not scored_candidates:
            return []
        
        # Return the highest scoring candidate
        return [scored_candidates[0][0]]
    
    def _select_multiple_best(
        self,
        scored_candidates: List[Tuple[ImageCandidate, float]],
        count: int,
        strategy: SelectionStrategy
    ) -> List[ImageCandidate]:
        """Select multiple candidates with diversity consideration."""
        if count >= len(scored_candidates):
            return [candidate for candidate, _ in scored_candidates]
        
        selected = []
        remaining = list(scored_candidates)
        
        # Always select the top candidate first
        selected.append(remaining[0][0])
        remaining = remaining[1:]
        
        # For remaining selections, consider diversity
        for _ in range(count - 1):
            if not remaining:
                break
            
            best_candidate = None
            best_score = -1
            
            for i, (candidate, base_score) in enumerate(remaining):
                # Calculate diversity penalty
                diversity_penalty = self._calculate_diversity_penalty(candidate, selected)
                
                # Adjust score based on diversity
                adjusted_score = base_score * (1.0 - diversity_penalty * self.criteria.diversity_weight)
                
                if adjusted_score > best_score:
                    best_score = adjusted_score
                    best_candidate = i
            
            if best_candidate is not None:
                selected.append(remaining[best_candidate][0])
                remaining.pop(best_candidate)
        
        return selected
    
    def _calculate_diversity_penalty(
        self,
        candidate: ImageCandidate,
        selected: List[ImageCandidate]
    ) -> float:
        """Calculate diversity penalty for candidate against selected images."""
        if not selected:
            return 0.0
        
        penalties = []
        
        for selected_img in selected:
            penalty = 0.0
            
            # Scene type similarity
            if candidate.analysis.scene_type == selected_img.analysis.scene_type:
                penalty += 0.3
            
            # Object overlap
            candidate_objects = set(obj.lower() for obj in candidate.analysis.objects)
            selected_objects = set(obj.lower() for obj in selected_img.analysis.objects)
            object_overlap = len(candidate_objects.intersection(selected_objects))
            if candidate_objects or selected_objects:
                object_similarity = object_overlap / len(candidate_objects.union(selected_objects))
                penalty += object_similarity * 0.4
            
            # Color similarity
            candidate_colors = set(color.lower() for color in candidate.analysis.colors)
            selected_colors = set(color.lower() for color in selected_img.analysis.colors)
            color_overlap = len(candidate_colors.intersection(selected_colors))
            if candidate_colors or selected_colors:
                color_similarity = color_overlap / len(candidate_colors.union(selected_colors))
                penalty += color_similarity * 0.3
            
            penalties.append(min(1.0, penalty))
        
        # Return maximum penalty (most similar image)
        return max(penalties) if penalties else 0.0
    
    def _calculate_diversity_metrics(self, selected: List[ImageCandidate]) -> Dict[str, Any]:
        """Calculate diversity metrics for selected images."""
        if not selected:
            return {}
        
        # Scene type diversity
        scene_types = [img.analysis.scene_type for img in selected]
        unique_scenes = len(set(scene_types))
        
        # Object diversity
        all_objects = []
        for img in selected:
            all_objects.extend(img.analysis.objects)
        unique_objects = len(set(obj.lower() for obj in all_objects))
        
        # Color diversity
        all_colors = []
        for img in selected:
            all_colors.extend(img.analysis.colors)
        unique_colors = len(set(color.lower() for color in all_colors))
        
        # Quality variance
        quality_scores = [img.analysis.quality_metrics.overall_score for img in selected]
        quality_variance = statistics.variance(quality_scores) if len(quality_scores) > 1 else 0.0
        
        return {
            'scene_type_diversity': unique_scenes / len(selected),
            'unique_objects': unique_objects,
            'unique_colors': unique_colors,
            'quality_variance': quality_variance,
            'selection_count': len(selected)
        }
    
    def _generate_reasoning(
        self,
        selected: List[ImageCandidate],
        scored_candidates: List[Tuple[ImageCandidate, float]],
        strategy: SelectionStrategy,
        search_query: Optional[str]
    ) -> str:
        """Generate human-readable reasoning for selection decisions."""
        if not selected:
            return "No images met the minimum selection criteria."
        
        reasoning_parts = []
        
        # Overall strategy
        reasoning_parts.append(f"Selection made using {strategy.value} strategy.")
        
        # Selection summary
        total_candidates = len(scored_candidates)
        reasoning_parts.append(
            f"Selected {len(selected)} image{'s' if len(selected) != 1 else ''} "
            f"from {total_candidates} candidates."
        )
        
        # Individual image reasoning
        for i, candidate in enumerate(selected, 1):
            analysis = candidate.analysis
            quality = analysis.quality_metrics.overall_score
            relevance = analysis.relevance_score
            confidence = analysis.confidence_score
            
            img_reasoning = (
                f"Image {i}: Quality {quality:.2f}, "
                f"Relevance {relevance:.2f}, "
                f"Confidence {confidence:.2f}. "
                f"Scene: {analysis.scene_type}. "
                f"Key objects: {', '.join(analysis.objects[:3])}."
            )
            reasoning_parts.append(img_reasoning)
        
        # Diversity considerations
        if len(selected) > 1:
            diversity_metrics = self._calculate_diversity_metrics(selected)
            scene_diversity = diversity_metrics.get('scene_type_diversity', 0)
            reasoning_parts.append(
                f"Diversity maintained with {scene_diversity:.1%} scene type variety."
            )
        
        return " ".join(reasoning_parts)
    
    def explain_selection(self, result: SelectionResult) -> List[SelectionExplanation]:
        """Generate detailed explanations for each selection decision."""
        explanations = []
        
        for i, candidate in enumerate(result.selected_images):
            score = result.scores.get(candidate.image_url, 0.0)
            
            # Score breakdown
            analysis = candidate.analysis
            breakdown = {
                'quality': self._calculate_quality_score(analysis.quality_metrics),
                'relevance': analysis.relevance_score,
                'confidence': analysis.confidence_score,
                'cost_efficiency': 1.0 - min(1.0, analysis.cost_estimate / self.criteria.max_cost_per_image)
            }
            
            # Selection reasons
            reasons = []
            if breakdown['quality'] > 0.8:
                reasons.append("High quality score")
            if breakdown['relevance'] > 0.8:
                reasons.append("Strong relevance to search query")
            if breakdown['confidence'] > 0.8:
                reasons.append("High analysis confidence")
            if analysis.quality_metrics.composition_score > 0.8:
                reasons.append("Excellent composition")
            
            explanations.append(SelectionExplanation(
                candidate=candidate,
                final_score=score,
                score_breakdown=breakdown,
                selection_reasons=reasons,
                rejection_reasons=[],
                rank=i + 1
            ))
        
        return explanations
    
    def _get_cache_key(
        self,
        candidates: List[ImageCandidate],
        count: int,
        strategy: SelectionStrategy,
        search_query: Optional[str]
    ) -> str:
        """Generate cache key for selection results."""
        import hashlib
        
        # Create hash of inputs
        candidate_urls = [c.image_url for c in candidates]
        content = f"{sorted(candidate_urls)}{count}{strategy.value}{search_query}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def clear_cache(self):
        """Clear selection cache."""
        self.selection_cache.clear()
        logger.info("Selection cache cleared")
    
    def get_selection_stats(self) -> Dict[str, Any]:
        """Get selection statistics."""
        return {
            'cache_size': len(self.selection_cache),
            'criteria': asdict(self.criteria)
        }