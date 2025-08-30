#!/usr/bin/env python3
"""
Vision Analyzer module for ImageFox.

This module provides intelligent image analysis by coordinating multiple
vision models to extract comprehensive information from images.
"""

import os
import json
import logging
import statistics
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import sentry_sdk
from sentry_sdk import capture_exception

from openrouter_client import OpenRouterClient, AnalysisResult, ModelCapability

logger = logging.getLogger(__name__)


@dataclass
class ImageMetadata:
    """Metadata extracted from image."""
    url: str
    title: str
    source_url: str
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    format: Optional[str] = None


@dataclass
class QualityMetrics:
    """Image quality assessment metrics."""
    overall_score: float
    composition_score: float
    clarity_score: float
    color_score: float
    content_relevance: float
    technical_quality: float


@dataclass
class ComprehensiveAnalysis:
    """Complete analysis result combining multiple models."""
    description: str
    objects: List[str]
    scene_type: str
    colors: List[str]
    composition: str
    quality_metrics: QualityMetrics
    relevance_score: float
    technical_details: Dict[str, Any]
    models_used: List[str]
    processing_time: float
    cost_estimate: float
    confidence_score: float
    timestamp: str


class VisionAnalyzer:
    """Intelligent image analyzer using multiple vision models."""
    
    DEFAULT_ANALYSIS_PROMPT = """
    Analyze this image and provide a detailed assessment in JSON format with these fields:
    {
        "description": "Detailed description of the image content and scene",
        "objects": ["list", "of", "main", "objects", "visible"],
        "scene_type": "type of scene (e.g., landscape, portrait, urban, nature)",
        "colors": ["dominant", "color", "palette"],
        "composition": "description of visual composition and layout",
        "quality_score": 0.95,
        "relevance_score": 0.85,
        "technical_details": {
            "lighting": "description of lighting conditions",
            "perspective": "camera angle and perspective",
            "focus": "focus quality and depth of field",
            "exposure": "exposure quality assessment"
        }
    }
    
    Be precise and objective in your analysis. Focus on visual elements that would be important for content selection.
    """
    
    def __init__(self, openrouter_client: Optional[OpenRouterClient] = None):
        """
        Initialize Vision Analyzer.
        
        Args:
            openrouter_client: Optional pre-configured OpenRouter client
        """
        self.openrouter_client = openrouter_client or OpenRouterClient()
        
        # Configuration
        self.consensus_threshold = float(os.getenv('ANALYSIS_CONSENSUS_THRESHOLD', '0.7'))
        self.quality_weight = float(os.getenv('QUALITY_WEIGHT', '0.4'))
        self.relevance_weight = float(os.getenv('RELEVANCE_WEIGHT', '0.6'))
        self.enable_multi_model = os.getenv('ENABLE_MULTI_MODEL_ANALYSIS', 'true').lower() == 'true'
        
        # Model selection strategy
        self.primary_models = ['openai/gpt-4-vision-preview', 'anthropic/claude-3-opus']
        self.fallback_models = ['anthropic/claude-3-sonnet', 'anthropic/claude-3-haiku']
        
        # Analysis cache
        self.analysis_cache = {}
    
    def analyze_image(
        self,
        image_input: Union[str, bytes, ImageMetadata],
        search_query: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        enable_multi_model: Optional[bool] = None
    ) -> ComprehensiveAnalysis:
        """
        Perform comprehensive image analysis.
        
        Args:
            image_input: Image data (URL, file path, bytes, or metadata)
            search_query: Original search query for relevance scoring
            custom_prompt: Custom analysis prompt
            enable_multi_model: Whether to use multiple models (overrides config)
        
        Returns:
            Comprehensive analysis results
        
        Raises:
            Exception: If analysis fails with all models
        """
        start_time = datetime.now()
        
        try:
            # Extract image URL/data
            if isinstance(image_input, ImageMetadata):
                image_data = image_input.url
                metadata = image_input
            else:
                image_data = image_input
                metadata = None
            
            # Generate cache key
            cache_key = self._get_cache_key(image_data, search_query, custom_prompt)
            if cached := self.analysis_cache.get(cache_key):
                logger.info(f"Using cached analysis for image")
                return cached
            
            # Determine analysis strategy
            use_multi_model = enable_multi_model if enable_multi_model is not None else self.enable_multi_model
            
            if use_multi_model:
                analysis = self._multi_model_analysis(image_data, search_query, custom_prompt)
            else:
                analysis = self._single_model_analysis(image_data, search_query, custom_prompt)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            analysis.processing_time = processing_time
            analysis.timestamp = datetime.now().isoformat()
            
            # Add metadata if available
            if metadata:
                analysis.technical_details.update({
                    'source_metadata': asdict(metadata)
                })
            
            # Cache result
            self.analysis_cache[cache_key] = analysis
            
            logger.info(f"Image analysis completed in {processing_time:.2f}s using {len(analysis.models_used)} models")
            return analysis
            
        except Exception as e:
            logger.error(f"Image analysis failed: {str(e)}")
            capture_exception(e)
            raise
    
    def _single_model_analysis(
        self,
        image_data: Union[str, bytes],
        search_query: Optional[str],
        custom_prompt: Optional[str]
    ) -> ComprehensiveAnalysis:
        """Analyze image using single best model."""
        prompt = custom_prompt or self._build_analysis_prompt(search_query)
        
        # Try primary models first
        for model in self.primary_models:
            try:
                result = self.openrouter_client.analyze_image(
                    image_input=image_data,
                    prompt=prompt,
                    model=model
                )
                
                return self._convert_to_comprehensive_analysis(
                    result, [model], search_query
                )
                
            except Exception as e:
                logger.warning(f"Model {model} failed: {str(e)}")
                continue
        
        # Try fallback models
        for model in self.fallback_models:
            try:
                result = self.openrouter_client.analyze_image(
                    image_input=image_data,
                    prompt=prompt,
                    model=model
                )
                
                return self._convert_to_comprehensive_analysis(
                    result, [model], search_query
                )
                
            except Exception as e:
                logger.warning(f"Fallback model {model} failed: {str(e)}")
                continue
        
        raise Exception("All vision models failed to analyze image")
    
    def _multi_model_analysis(
        self,
        image_data: Union[str, bytes],
        search_query: Optional[str],
        custom_prompt: Optional[str]
    ) -> ComprehensiveAnalysis:
        """Analyze image using multiple models for consensus."""
        prompt = custom_prompt or self._build_analysis_prompt(search_query)
        
        results = []
        models_used = []
        
        # Try to get at least 2 successful analyses
        for model in self.primary_models + self.fallback_models:
            if len(results) >= 2:
                break
                
            try:
                result = self.openrouter_client.analyze_image(
                    image_input=image_data,
                    prompt=prompt,
                    model=model
                )
                results.append(result)
                models_used.append(model)
                
            except Exception as e:
                logger.warning(f"Model {model} failed in multi-model analysis: {str(e)}")
                continue
        
        if not results:
            raise Exception("All models failed in multi-model analysis")
        
        # Merge results if multiple analyses available
        if len(results) > 1:
            return self._merge_analyses(results, models_used, search_query)
        else:
            return self._convert_to_comprehensive_analysis(
                results[0], models_used, search_query
            )
    
    def _merge_analyses(
        self,
        results: List[AnalysisResult],
        models_used: List[str],
        search_query: Optional[str]
    ) -> ComprehensiveAnalysis:
        """Merge multiple analysis results into consensus."""
        # Extract common elements
        all_objects = []
        all_colors = []
        quality_scores = []
        relevance_scores = []
        descriptions = []
        technical_details = {}
        
        for result in results:
            all_objects.extend(result.objects)
            all_colors.extend(result.colors)
            quality_scores.append(result.quality_score)
            relevance_scores.append(result.relevance_score)
            descriptions.append(result.description)
            technical_details.update(result.technical_details)
        
        # Build consensus
        consensus_objects = self._find_consensus_items(all_objects)
        consensus_colors = self._find_consensus_items(all_colors)
        avg_quality = statistics.mean(quality_scores) if quality_scores else 0.0
        avg_relevance = statistics.mean(relevance_scores) if relevance_scores else 0.0
        
        # Select best description (longest and most detailed)
        best_description = max(descriptions, key=len) if descriptions else ""
        
        # Calculate confidence based on agreement
        confidence = self._calculate_consensus_confidence(results)
        
        # Build quality metrics
        quality_metrics = self._build_quality_metrics(results)
        
        return ComprehensiveAnalysis(
            description=best_description,
            objects=consensus_objects,
            scene_type=results[0].scene_type,  # Use first model's scene classification
            colors=consensus_colors,
            composition=results[0].composition,  # Use first model's composition
            quality_metrics=quality_metrics,
            relevance_score=avg_relevance,
            technical_details=technical_details,
            models_used=models_used,
            processing_time=0.0,  # Set later
            cost_estimate=sum(r.cost_estimate for r in results),
            confidence_score=confidence,
            timestamp=""  # Set later
        )
    
    def _find_consensus_items(self, items: List[str], min_frequency: int = 2) -> List[str]:
        """Find items that appear in multiple analyses."""
        from collections import Counter
        
        # Count occurrences (case-insensitive)
        counter = Counter(item.lower() for item in items)
        
        # Return items that appear at least min_frequency times
        consensus_items = []
        for item, count in counter.most_common():
            if count >= min_frequency:
                # Find original case
                original = next(original for original in items if original.lower() == item)
                consensus_items.append(original)
        
        return consensus_items[:10]  # Limit to top 10
    
    def _calculate_consensus_confidence(self, results: List[AnalysisResult]) -> float:
        """Calculate confidence score based on model agreement."""
        if len(results) < 2:
            return 0.8  # Single model baseline
        
        # Compare quality scores
        quality_scores = [r.quality_score for r in results]
        quality_variance = statistics.variance(quality_scores) if len(quality_scores) > 1 else 0
        
        # Compare relevance scores
        relevance_scores = [r.relevance_score for r in results]
        relevance_variance = statistics.variance(relevance_scores) if len(relevance_scores) > 1 else 0
        
        # Lower variance means higher agreement
        max_variance = 0.1  # Maximum expected variance for high confidence
        quality_agreement = max(0, 1 - (quality_variance / max_variance))
        relevance_agreement = max(0, 1 - (relevance_variance / max_variance))
        
        return (quality_agreement + relevance_agreement) / 2
    
    def _build_quality_metrics(self, results: List[AnalysisResult]) -> QualityMetrics:
        """Build comprehensive quality metrics from multiple analyses."""
        quality_scores = [r.quality_score for r in results]
        overall_score = statistics.mean(quality_scores) if quality_scores else 0.0
        
        # Extract technical details for quality sub-scores
        technical_scores = []
        for result in results:
            tech = result.technical_details
            composition_score = self._extract_score_from_text(tech.get('composition', ''), overall_score)
            clarity_score = self._extract_score_from_text(tech.get('focus', ''), overall_score)
            color_score = self._extract_score_from_text(tech.get('lighting', ''), overall_score)
            
            technical_scores.append({
                'composition': composition_score,
                'clarity': clarity_score,
                'color': color_score
            })
        
        # Average technical scores
        if technical_scores:
            avg_composition = statistics.mean(s['composition'] for s in technical_scores)
            avg_clarity = statistics.mean(s['clarity'] for s in technical_scores)
            avg_color = statistics.mean(s['color'] for s in technical_scores)
        else:
            avg_composition = avg_clarity = avg_color = overall_score
        
        return QualityMetrics(
            overall_score=overall_score,
            composition_score=avg_composition,
            clarity_score=avg_clarity,
            color_score=avg_color,
            content_relevance=statistics.mean(r.relevance_score for r in results) if results else 0.0,
            technical_quality=overall_score
        )
    
    def _extract_score_from_text(self, text: str, fallback: float) -> float:
        """Extract quality score from descriptive text."""
        # Simple heuristic based on positive/negative keywords
        positive_words = ['excellent', 'good', 'clear', 'sharp', 'bright', 'vivid', 'balanced']
        negative_words = ['poor', 'blurry', 'dark', 'overexposed', 'underexposed', 'noisy']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return min(1.0, fallback + 0.1)
        elif negative_count > positive_count:
            return max(0.0, fallback - 0.1)
        else:
            return fallback
    
    def _convert_to_comprehensive_analysis(
        self,
        result: AnalysisResult,
        models_used: List[str],
        search_query: Optional[str]
    ) -> ComprehensiveAnalysis:
        """Convert OpenRouter result to comprehensive analysis."""
        quality_metrics = QualityMetrics(
            overall_score=result.quality_score,
            composition_score=result.quality_score,
            clarity_score=result.quality_score,
            color_score=result.quality_score,
            content_relevance=result.relevance_score,
            technical_quality=result.quality_score
        )
        
        return ComprehensiveAnalysis(
            description=result.description,
            objects=result.objects,
            scene_type=result.scene_type,
            colors=result.colors,
            composition=result.composition,
            quality_metrics=quality_metrics,
            relevance_score=result.relevance_score,
            technical_details=result.technical_details,
            models_used=models_used,
            processing_time=result.processing_time,
            cost_estimate=result.cost_estimate,
            confidence_score=0.8,  # Single model baseline
            timestamp=""
        )
    
    def _build_analysis_prompt(self, search_query: Optional[str]) -> str:
        """Build analysis prompt with optional search context."""
        base_prompt = self.DEFAULT_ANALYSIS_PROMPT
        
        if search_query:
            context_prompt = f"""
            
            Additional context: This image was found for the search query "{search_query}".
            Please consider relevance to this query when scoring relevance_score.
            """
            base_prompt += context_prompt
        
        return base_prompt
    
    def _get_cache_key(
        self,
        image_data: Union[str, bytes],
        search_query: Optional[str],
        custom_prompt: Optional[str]
    ) -> str:
        """Generate cache key for analysis results."""
        import hashlib
        
        # Create hash of inputs
        content = f"{image_data}{search_query}{custom_prompt}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def calculate_selection_score(
        self,
        analysis: ComprehensiveAnalysis,
        search_query: Optional[str] = None
    ) -> float:
        """
        Calculate overall selection score for image.
        
        Args:
            analysis: Comprehensive analysis results
            search_query: Original search query for relevance weighting
        
        Returns:
            Selection score (0-1)
        """
        # Base score from quality metrics
        quality_component = (
            analysis.quality_metrics.overall_score * 0.4 +
            analysis.quality_metrics.composition_score * 0.3 +
            analysis.quality_metrics.technical_quality * 0.3
        )
        
        # Relevance component
        relevance_component = analysis.relevance_score
        
        # Confidence component
        confidence_component = analysis.confidence_score
        
        # Weighted final score
        final_score = (
            quality_component * self.quality_weight +
            relevance_component * self.relevance_weight
        ) * confidence_component
        
        return min(1.0, max(0.0, final_score))
    
    def clear_cache(self):
        """Clear analysis cache."""
        self.analysis_cache.clear()
        logger.info("Analysis cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            'cache_size': len(self.analysis_cache),
            'total_analyses': getattr(self, '_total_analyses', 0)
        }