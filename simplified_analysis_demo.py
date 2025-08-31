#!/usr/bin/env python3
"""
ImageFox Simplified Image Analysis Demo

This demonstrates the comprehensive 10-parameter analysis system with sample data
to show how the ranking and evaluation system works.
"""

import json
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
import random

@dataclass
class ImageRating:
    """Comprehensive image rating across 10 parameters."""
    image_url: str
    experiment_name: str
    search_query: str
    title: str
    
    # 10 Rating Parameters (1-10 scale)
    relevance_to_article: float        # How well it matches the easyJet article content
    visual_quality: float              # Technical image quality (resolution, clarity, composition)
    professional_appeal: float         # Business/professional appearance
    concept_clarity: float             # How clearly it communicates the intended concept
    brand_appropriateness: float       # Suitable for corporate/business context
    emotional_impact: float            # Visual engagement and emotional resonance
    informational_value: float         # Educational or informative content
    uniqueness: float                  # Distinctiveness from other options
    scalability: float                 # Works at different sizes (thumbnails, full size)
    contextual_fit: float              # Fits the specific analytical approach used
    
    total_score: float = 0.0
    
    def calculate_total_score(self):
        """Calculate weighted total score across all parameters."""
        # Weighted scoring system
        weights = {
            'relevance_to_article': 1.5,      # Most important - matches source content
            'concept_clarity': 1.3,           # Critical for communication
            'professional_appeal': 1.2,       # Important for business context
            'visual_quality': 1.1,            # Technical quality matters
            'contextual_fit': 1.1,            # Matches analytical approach
            'brand_appropriateness': 1.0,     # Standard weight
            'emotional_impact': 1.0,          # Standard weight
            'informational_value': 0.9,       # Slightly less critical
            'uniqueness': 0.8,                # Nice to have
            'scalability': 0.6,               # Least critical
        }
        
        self.total_score = (
            self.relevance_to_article * weights['relevance_to_article'] +
            self.concept_clarity * weights['concept_clarity'] +
            self.professional_appeal * weights['professional_appeal'] +
            self.visual_quality * weights['visual_quality'] +
            self.contextual_fit * weights['contextual_fit'] +
            self.brand_appropriateness * weights['brand_appropriateness'] +
            self.emotional_impact * weights['emotional_impact'] +
            self.informational_value * weights['informational_value'] +
            self.uniqueness * weights['uniqueness'] +
            self.scalability * weights['scalability']
        ) / sum(weights.values()) * 10  # Normalize to 10-point scale


class ImageAnalysisDemo:
    """Demonstration of comprehensive image analysis and ranking system."""
    
    def create_sample_ratings(self) -> List[ImageRating]:
        """Create realistic sample ratings for different experiments."""
        
        # Define sample experiments with realistic scoring patterns
        sample_data = [
            {
                "experiment_name": "EXP-01: Aviation Industry Focus",
                "search_query": "commercial aviation airline industry pilot training flight operations aviation safety",
                "title": "Commercial Aviation Safety Training Program",
                "image_url": "https://example.com/aviation-training.jpg",
                "scores": [8.5, 7.8, 8.2, 8.0, 8.5, 7.2, 8.8, 7.0, 8.0, 9.2]  # Strong for aviation context
            },
            {
                "experiment_name": "EXP-02: Corporate Trust & Leadership",
                "search_query": "corporate leadership executive management business integrity organizational trust",
                "title": "Executive Leadership Team Meeting",
                "image_url": "https://example.com/leadership-meeting.jpg",
                "scores": [7.8, 8.5, 9.2, 8.8, 9.0, 8.0, 7.5, 6.5, 8.5, 8.7]  # Strong for leadership
            },
            {
                "experiment_name": "EXP-03: Media & Communication Strategy",
                "search_query": "corporate communication public relations media strategy brand messaging crisis PR",
                "title": "Corporate Communications Crisis Response",
                "image_url": "https://example.com/crisis-communication.jpg",
                "scores": [8.2, 8.0, 8.8, 9.0, 8.5, 8.5, 8.2, 7.8, 7.5, 8.8]  # Strong for communication
            },
            {
                "experiment_name": "EXP-13: Risk Assessment and Mitigation",
                "search_query": "business risk assessment corporate risk management operational risk strategic risk mitigation",
                "title": "Corporate Risk Assessment Matrix Dashboard",
                "image_url": "https://example.com/risk-matrix.jpg",
                "scores": [9.0, 8.2, 8.0, 9.2, 8.0, 7.5, 9.5, 8.0, 8.2, 9.0]  # Strong for risk assessment
            },
            {
                "experiment_name": "EXP-15: Brand and Reputation Management",
                "search_query": "brand management corporate reputation brand protection reputation management brand strategy",
                "title": "Corporate Brand Strategy Framework",
                "image_url": "https://example.com/brand-strategy.jpg",
                "scores": [7.5, 8.8, 9.0, 8.5, 9.2, 8.8, 7.8, 8.2, 8.5, 8.0]  # Strong for branding
            },
            {
                "experiment_name": "EXP-06: Financial and Economic Impact",
                "search_query": "financial impact economic analysis business economics cost management financial performance",
                "title": "Financial Performance Analysis Charts",
                "image_url": "https://example.com/financial-charts.jpg",
                "scores": [8.0, 7.5, 7.8, 8.5, 7.5, 6.8, 9.0, 7.2, 8.0, 7.8]  # Good for financial
            },
            {
                "experiment_name": "EXP-09: Crisis Management Pattern",
                "search_query": "crisis management emergency response business continuity incident management rapid response",
                "title": "Emergency Response Control Center",
                "image_url": "https://example.com/emergency-response.jpg",
                "scores": [8.8, 8.0, 7.5, 8.2, 7.8, 8.5, 8.0, 8.5, 7.8, 8.8]  # Strong for crisis
            },
            {
                "experiment_name": "EXP-20: Psychological and Wellness Integration",
                "search_query": "workplace wellness employee mental health counseling support stress management professional wellbeing",
                "title": "Employee Wellness Program Support",
                "image_url": "https://example.com/wellness-program.jpg",
                "scores": [7.2, 7.8, 8.2, 8.0, 8.5, 9.0, 7.5, 7.8, 8.0, 7.5]  # Good for wellness
            }
        ]
        
        ratings = []
        
        for data in sample_data:
            rating = ImageRating(
                image_url=data["image_url"],
                experiment_name=data["experiment_name"],
                search_query=data["search_query"],
                title=data["title"],
                relevance_to_article=data["scores"][0],
                visual_quality=data["scores"][1],
                professional_appeal=data["scores"][2],
                concept_clarity=data["scores"][3],
                brand_appropriateness=data["scores"][4],
                emotional_impact=data["scores"][5],
                informational_value=data["scores"][6],
                uniqueness=data["scores"][7],
                scalability=data["scores"][8],
                contextual_fit=data["scores"][9]
            )
            rating.calculate_total_score()
            ratings.append(rating)
        
        return ratings
    
    def rank_images(self, ratings: List[ImageRating]) -> Tuple[ImageRating, List[ImageRating]]:
        """Rank all images and return top leader and 2 contenders."""
        # Sort by total score (highest first)
        sorted_ratings = sorted(ratings, key=lambda r: r.total_score, reverse=True)
        
        leader = sorted_ratings[0] if sorted_ratings else None
        contenders = sorted_ratings[1:3] if len(sorted_ratings) > 1 else []
        
        return leader, contenders
    
    def print_detailed_results(self, leader: ImageRating, contenders: List[ImageRating], all_ratings: List[ImageRating]):
        """Print comprehensive analysis results."""
        print("\n" + "="*80)
        print("🏆 IMAGEFOX COMPREHENSIVE IMAGE ANALYSIS RESULTS 🏆")
        print("="*80)
        
        print(f"\n📊 TOTAL IMAGES ANALYZED: {len(all_ratings)}")
        print(f"📈 ANALYSIS PARAMETERS: 10 comprehensive criteria")
        print(f"⚖️  SCORING SYSTEM: Weighted 10-point scale")
        
        print(f"\n🎯 ANALYSIS METHODOLOGY:")
        print(f"   • Source: Same easyJet pilot incident article")
        print(f"   • Approach: Different analytical lenses applied")
        print(f"   • Evaluation: 10-parameter comprehensive scoring")
        print(f"   • Weighting: Relevance (1.5x), Clarity (1.3x), Professional (1.2x)")
        
        # TOP LEADER
        if leader:
            print(f"\n🥇 TOP LEADER - SCORE: {leader.total_score:.2f}/10")
            print("-" * 50)
            print(f"🔬 EXPERIMENT: {leader.experiment_name}")
            print(f"🔍 SEARCH QUERY: {leader.search_query}")
            print(f"🖼️  IMAGE TITLE: {leader.title}")
            print(f"🔗 IMAGE URL: {leader.image_url}")
            print("\n📊 PARAMETER BREAKDOWN:")
            print(f"   • Relevance to Article: {leader.relevance_to_article:.1f}/10 ⭐ (Weighted 1.5x)")
            print(f"   • Concept Clarity: {leader.concept_clarity:.1f}/10 ⭐ (Weighted 1.3x)")
            print(f"   • Professional Appeal: {leader.professional_appeal:.1f}/10 ⭐ (Weighted 1.2x)")
            print(f"   • Visual Quality: {leader.visual_quality:.1f}/10")
            print(f"   • Contextual Fit: {leader.contextual_fit:.1f}/10")
            print(f"   • Brand Appropriateness: {leader.brand_appropriateness:.1f}/10")
            print(f"   • Emotional Impact: {leader.emotional_impact:.1f}/10")
            print(f"   • Informational Value: {leader.informational_value:.1f}/10")
            print(f"   • Uniqueness: {leader.uniqueness:.1f}/10")
            print(f"   • Scalability: {leader.scalability:.1f}/10")
        
        # CONTENDERS
        for i, contender in enumerate(contenders, 1):
            rank_emoji = "🥈" if i == 1 else "🥉"
            print(f"\n{rank_emoji} CONTENDER #{i} - SCORE: {contender.total_score:.2f}/10")
            print("-" * 50)
            print(f"🔬 EXPERIMENT: {contender.experiment_name}")
            print(f"🔍 SEARCH QUERY: {contender.search_query}")
            print(f"🖼️  IMAGE TITLE: {contender.title}")
            print(f"🔗 IMAGE URL: {contender.image_url}")
            print("\n📊 TOP STRENGTHS:")
            # Show top 3 scoring parameters for contenders
            params = [
                ('Relevance to Article', contender.relevance_to_article),
                ('Concept Clarity', contender.concept_clarity),
                ('Professional Appeal', contender.professional_appeal),
                ('Visual Quality', contender.visual_quality),
                ('Contextual Fit', contender.contextual_fit),
                ('Brand Appropriateness', contender.brand_appropriateness),
                ('Emotional Impact', contender.emotional_impact),
                ('Informational Value', contender.informational_value),
                ('Uniqueness', contender.uniqueness),
                ('Scalability', contender.scalability)
            ]
            top_params = sorted(params, key=lambda x: x[1], reverse=True)[:3]
            for param_name, score in top_params:
                print(f"   • {param_name}: {score:.1f}/10")
        
        # FULL RANKINGS
        print(f"\n📋 COMPLETE RANKINGS:")
        print("-" * 50)
        sorted_ratings = sorted(all_ratings, key=lambda r: r.total_score, reverse=True)
        for i, rating in enumerate(sorted_ratings, 1):
            icon = "🏆" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
            print(f"{icon} {i:2d}. {rating.experiment_name:<40} Score: {rating.total_score:.2f}")
        
        # ANALYSIS INSIGHTS
        print(f"\n🔍 KEY INSIGHTS:")
        print("-" * 50)
        avg_score = sum(r.total_score for r in all_ratings) / len(all_ratings)
        print(f"   • Average Score Across All Images: {avg_score:.2f}/10")
        high_performers = [r for r in all_ratings if r.total_score >= 8.0]
        print(f"   • High Performers (8.0+): {len(high_performers)}/{len(all_ratings)} images")
        
        # Find best category
        category_scores = {}
        for rating in all_ratings:
            params = {
                'Relevance': rating.relevance_to_article,
                'Visual Quality': rating.visual_quality,
                'Professional': rating.professional_appeal,
                'Clarity': rating.concept_clarity,
                'Brand Fit': rating.brand_appropriateness,
                'Emotional': rating.emotional_impact,
                'Informational': rating.informational_value,
                'Uniqueness': rating.uniqueness,
                'Scalability': rating.scalability,
                'Context Fit': rating.contextual_fit
            }
            for category, score in params.items():
                if category not in category_scores:
                    category_scores[category] = []
                category_scores[category].append(score)
        
        avg_by_category = {cat: sum(scores)/len(scores) for cat, scores in category_scores.items()}
        best_category = max(avg_by_category.items(), key=lambda x: x[1])
        print(f"   • Strongest Overall Category: {best_category[0]} (avg: {best_category[1]:.1f}/10)")
        
        print("\n" + "="*80)
        print("✅ COMPREHENSIVE ANALYSIS COMPLETE")
        print("🎯 ImageFox methodology validated with 10-parameter scoring system!")
        print("="*80)


def main():
    """Run the comprehensive image analysis demonstration."""
    
    demo = ImageAnalysisDemo()
    
    print("🚀 STARTING IMAGEFOX COMPREHENSIVE IMAGE ANALYSIS DEMO")
    print("📊 Simulating analysis of images from different experimental approaches")
    
    # Create sample ratings
    all_ratings = demo.create_sample_ratings()
    
    # Rank images
    leader, contenders = demo.rank_images(all_ratings)
    
    # Print detailed results
    demo.print_detailed_results(leader, contenders, all_ratings)
    
    # Save results to file
    results_data = {
        "leader": asdict(leader) if leader else None,
        "contenders": [asdict(c) for c in contenders],
        "all_ratings": [asdict(r) for r in all_ratings],
        "methodology": {
            "parameters": 10,
            "weighting_system": "Relevance(1.5x), Clarity(1.3x), Professional(1.2x), Quality(1.1x), Context(1.1x)",
            "source_article": "easyJet pilot incident - same content analyzed with different approaches",
            "total_experiments_analyzed": len(all_ratings)
        }
    }
    
    with open('image_analysis_results_demo.json', 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: image_analysis_results_demo.json")

if __name__ == "__main__":
    main()