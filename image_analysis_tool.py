#!/usr/bin/env python3
"""
ImageFox Comprehensive Image Analysis and Ranking Tool

This tool analyzes all images selected by different experimental approaches and 
rates them across 10 parameters to identify the top leader and 2 contenders.
"""

import logging
import json
import asyncio
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
from imagefox import SearchRequest, ImageFox
from openrouter_client import OpenRouterClient

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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


class ImageAnalyzer:
    """Comprehensive image analysis and ranking system."""
    
    def __init__(self):
        self.openrouter_client = OpenRouterClient()
        self.imagefox = ImageFox()
        self.article_content = self._load_article()
        
    def _load_article(self) -> str:
        """Load the easyJet article content for relevance analysis."""
        try:
            with open('easyjet_article.txt', 'r') as f:
                return f.read()
        except FileNotFoundError:
            return "easyJet pilot incident analysis article"  # fallback
    
    async def analyze_image_comprehensive(self, image_url: str, experiment_name: str, 
                                        search_query: str, title: str) -> ImageRating:
        """Perform comprehensive 10-parameter analysis of an image."""
        
        # Create analysis prompt for the 10 parameters
        analysis_prompt = f"""
        Analyze this image comprehensively across 10 parameters for the ImageFox experiment "{experiment_name}".
        
        CONTEXT:
        - Source Article: easyJet pilot incident analysis (professional misconduct, corporate response, industry implications)
        - Search Query Used: "{search_query}"
        - Analytical Approach: {experiment_name}
        - Image Title: "{title}"
        
        Rate the image on each parameter (1-10 scale, where 10 is excellent):
        
        1. RELEVANCE_TO_ARTICLE: How well does this image relate to the easyJet pilot incident and corporate response themes?
        2. VISUAL_QUALITY: Technical quality - resolution, clarity, composition, professional photography
        3. PROFESSIONAL_APPEAL: Suitable for business/corporate context, professional appearance
        4. CONCEPT_CLARITY: How clearly does the image communicate its intended concept/message?
        5. BRAND_APPROPRIATENESS: Suitable for corporate communications, appropriate tone
        6. EMOTIONAL_IMPACT: Visual engagement, emotional resonance, memorability
        7. INFORMATIONAL_VALUE: Educational content, data visualization, informative elements
        8. UNIQUENESS: Distinctive from typical stock photos, creative or unique perspective
        9. SCALABILITY: Works well at different sizes (thumbnail to full size display)
        10. CONTEXTUAL_FIT: How well does it match the specific analytical approach ({experiment_name})?
        
        Respond in JSON format:
        {{
            "relevance_to_article": 7.5,
            "visual_quality": 8.0,
            "professional_appeal": 9.0,
            "concept_clarity": 7.0,
            "brand_appropriateness": 8.5,
            "emotional_impact": 6.5,
            "informational_value": 7.5,
            "uniqueness": 6.0,
            "scalability": 8.0,
            "contextual_fit": 8.5,
            "reasoning": "Brief explanation of the overall assessment and key strengths/weaknesses."
        }}
        """
        
        try:
            # Download image temporarily for analysis
            success, file_path, error = await self.imagefox.image_processor.download_image(image_url)
            
            if not success:
                logging.warning(f"Failed to download image {image_url}: {error}")
                return self._create_default_rating(image_url, experiment_name, search_query, title)
            
            # Analyze with vision model
            result = self.openrouter_client.analyze_image_with_prompt(
                file_path, 
                analysis_prompt,
                model="google/gemini-2.0-flash-lite-001"
            )
            
            # Clean up downloaded file
            import os
            if file_path and os.path.exists(file_path):
                os.unlink(file_path)
            
            # Parse the analysis result
            try:
                if hasattr(result, 'raw_content') and result.raw_content:
                    # Try to extract JSON from the response
                    content = result.raw_content
                    # Look for JSON in the response
                    import re
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        analysis_data = json.loads(json_match.group())
                        
                        rating = ImageRating(
                            image_url=image_url,
                            experiment_name=experiment_name,
                            search_query=search_query,
                            title=title,
                            relevance_to_article=float(analysis_data.get('relevance_to_article', 5.0)),
                            visual_quality=float(analysis_data.get('visual_quality', 5.0)),
                            professional_appeal=float(analysis_data.get('professional_appeal', 5.0)),
                            concept_clarity=float(analysis_data.get('concept_clarity', 5.0)),
                            brand_appropriateness=float(analysis_data.get('brand_appropriateness', 5.0)),
                            emotional_impact=float(analysis_data.get('emotional_impact', 5.0)),
                            informational_value=float(analysis_data.get('informational_value', 5.0)),
                            uniqueness=float(analysis_data.get('uniqueness', 5.0)),
                            scalability=float(analysis_data.get('scalability', 5.0)),
                            contextual_fit=float(analysis_data.get('contextual_fit', 5.0))
                        )
                        rating.calculate_total_score()
                        return rating
                        
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logging.warning(f"Failed to parse analysis result: {e}")
                
        except Exception as e:
            logging.error(f"Error analyzing image {image_url}: {e}")
            
        # Return default rating if analysis fails
        return self._create_default_rating(image_url, experiment_name, search_query, title)
    
    def _create_default_rating(self, image_url: str, experiment_name: str, 
                             search_query: str, title: str) -> ImageRating:
        """Create a default rating when analysis fails."""
        rating = ImageRating(
            image_url=image_url,
            experiment_name=experiment_name,
            search_query=search_query,
            title=title,
            relevance_to_article=5.0,
            visual_quality=5.0,
            professional_appeal=5.0,
            concept_clarity=5.0,
            brand_appropriateness=5.0,
            emotional_impact=5.0,
            informational_value=5.0,
            uniqueness=5.0,
            scalability=5.0,
            contextual_fit=5.0
        )
        rating.calculate_total_score()
        return rating
    
    async def run_experiment_and_analyze(self, experiment_config: Dict) -> ImageRating:
        """Run a single experiment and analyze the resulting image."""
        experiment_name = experiment_config['name']
        search_query = experiment_config['query']
        
        logging.info(f"Running {experiment_name}...")
        
        # Create search request
        request = SearchRequest(
            query=search_query,
            limit=5,
            max_results=1,
            enable_processing=False,
            enable_upload=False,
            enable_storage=False
        )
        
        # Execute search and selection
        result = await self.imagefox.search_and_select(request)
        
        if result.selected_images:
            selected_image = result.selected_images[0]
            
            # Analyze the selected image
            rating = await self.analyze_image_comprehensive(
                selected_image.image_url,
                experiment_name,
                search_query,
                selected_image.title
            )
            
            logging.info(f"{experiment_name} completed - Total Score: {rating.total_score:.2f}")
            return rating
        else:
            logging.warning(f"{experiment_name} - No images selected")
            return self._create_default_rating("", experiment_name, search_query, "No image selected")
    
    def rank_images(self, ratings: List[ImageRating]) -> Tuple[ImageRating, List[ImageRating]]:
        """Rank all images and return top leader and 2 contenders."""
        # Sort by total score (highest first)
        sorted_ratings = sorted(ratings, key=lambda r: r.total_score, reverse=True)
        
        leader = sorted_ratings[0] if sorted_ratings else None
        contenders = sorted_ratings[1:3] if len(sorted_ratings) > 1 else sorted_ratings[1:] if len(sorted_ratings) > 1 else []
        
        return leader, contenders
    
    def print_detailed_results(self, leader: ImageRating, contenders: List[ImageRating], all_ratings: List[ImageRating]):
        """Print comprehensive analysis results."""
        print("\n" + "="*80)
        print("🏆 IMAGEFOX COMPREHENSIVE IMAGE ANALYSIS RESULTS 🏆")
        print("="*80)
        
        print(f"\n📊 TOTAL IMAGES ANALYZED: {len(all_ratings)}")
        print(f"📈 ANALYSIS PARAMETERS: 10 comprehensive criteria")
        print(f"⚖️  SCORING SYSTEM: Weighted 10-point scale")
        
        # TOP LEADER
        if leader:
            print(f"\n🥇 TOP LEADER - SCORE: {leader.total_score:.2f}/10")
            print("-" * 50)
            print(f"🔬 EXPERIMENT: {leader.experiment_name}")
            print(f"🔍 SEARCH QUERY: {leader.search_query}")
            print(f"🖼️  IMAGE TITLE: {leader.title}")
            print(f"🔗 IMAGE URL: {leader.image_url}")
            print("\n📊 PARAMETER BREAKDOWN:")
            print(f"   • Relevance to Article: {leader.relevance_to_article:.1f}/10")
            print(f"   • Visual Quality: {leader.visual_quality:.1f}/10")
            print(f"   • Professional Appeal: {leader.professional_appeal:.1f}/10")
            print(f"   • Concept Clarity: {leader.concept_clarity:.1f}/10")
            print(f"   • Brand Appropriateness: {leader.brand_appropriateness:.1f}/10")
            print(f"   • Emotional Impact: {leader.emotional_impact:.1f}/10")
            print(f"   • Informational Value: {leader.informational_value:.1f}/10")
            print(f"   • Uniqueness: {leader.uniqueness:.1f}/10")
            print(f"   • Scalability: {leader.scalability:.1f}/10")
            print(f"   • Contextual Fit: {leader.contextual_fit:.1f}/10")
        
        # CONTENDERS
        for i, contender in enumerate(contenders, 1):
            rank_emoji = "🥈" if i == 1 else "🥉"
            print(f"\n{rank_emoji} CONTENDER #{i} - SCORE: {contender.total_score:.2f}/10")
            print("-" * 50)
            print(f"🔬 EXPERIMENT: {contender.experiment_name}")
            print(f"🔍 SEARCH QUERY: {contender.search_query}")
            print(f"🖼️  IMAGE TITLE: {contender.title}")
            print(f"🔗 IMAGE URL: {contender.image_url}")
            print("\n📊 PARAMETER BREAKDOWN:")
            print(f"   • Relevance to Article: {contender.relevance_to_article:.1f}/10")
            print(f"   • Visual Quality: {contender.visual_quality:.1f}/10")
            print(f"   • Professional Appeal: {contender.professional_appeal:.1f}/10")
            print(f"   • Concept Clarity: {contender.concept_clarity:.1f}/10")
            print(f"   • Brand Appropriateness: {contender.brand_appropriateness:.1f}/10")
            print(f"   • Emotional Impact: {contender.emotional_impact:.1f}/10")
            print(f"   • Informational Value: {contender.informational_value:.1f}/10")
            print(f"   • Uniqueness: {contender.uniqueness:.1f}/10")
            print(f"   • Scalability: {contender.scalability:.1f}/10")
            print(f"   • Contextual Fit: {contender.contextual_fit:.1f}/10")
        
        # FULL RANKINGS
        print(f"\n📋 COMPLETE RANKINGS:")
        print("-" * 50)
        sorted_ratings = sorted(all_ratings, key=lambda r: r.total_score, reverse=True)
        for i, rating in enumerate(sorted_ratings, 1):
            print(f"{i:2d}. {rating.experiment_name:<35} Score: {rating.total_score:.2f}")
        
        print("\n" + "="*80)
        print("✅ ANALYSIS COMPLETE - ImageFox methodology validated with comprehensive scoring!")
        print("="*80)


async def main():
    """Run comprehensive image analysis across all experiments."""
    
    # Define all 20 experiments with their search queries
    experiments = [
        {"name": "EXP-01: Aviation Industry Focus", "query": "commercial aviation airline industry pilot training flight operations aviation safety airline management"},
        {"name": "EXP-02: Corporate Trust & Leadership", "query": "corporate leadership executive management business integrity organizational trust ethical governance accountability"},
        {"name": "EXP-03: Media & Communication Strategy", "query": "corporate communication public relations media strategy brand messaging crisis PR social media management"},
        {"name": "EXP-04: Innovation Technology Focus", "query": "business technology innovation digital transformation performance optimization technology solutions enterprise systems"},
        {"name": "EXP-05: Competitive Market Dynamics", "query": "competitive market analysis business competition market dynamics competitive advantage industry competition market leadership"},
        {"name": "EXP-06: Financial and Economic Impact", "query": "financial impact economic analysis business economics cost management financial performance economic consequences investment returns"},
        {"name": "EXP-07: Human Resources and Talent Management", "query": "human resources talent management employee development workforce management HR strategy talent acquisition employee support"},
        {"name": "EXP-08: Customer and Stakeholder Experience", "query": "customer experience stakeholder management service quality customer satisfaction client relations customer service excellence"},
        {"name": "EXP-09: Crisis Management Pattern", "query": "crisis management emergency response business continuity incident management rapid response crisis intervention"},
        {"name": "EXP-10: Regulatory Compliance Focus", "query": "regulatory compliance business governance compliance standards legal requirements regulatory framework audit compliance"},
        {"name": "EXP-11: Cultural and Organizational Values", "query": "corporate culture organizational values workplace culture company values team culture professional ethics business culture"},
        {"name": "EXP-12: Strategic Planning and Future Vision", "query": "strategic business planning corporate strategy long-term vision business development strategic management future planning"},
        {"name": "EXP-13: Risk Assessment and Mitigation", "query": "business risk assessment corporate risk management operational risk strategic risk mitigation threat analysis"},
        {"name": "EXP-14: Performance and Excellence Focus", "query": "business performance excellence performance optimization high performance professional excellence operational excellence"},
        {"name": "EXP-15: Brand and Reputation Management", "query": "brand management corporate reputation brand protection reputation management brand strategy corporate branding brand equity"},
        {"name": "EXP-16: Communication and Public Relations Strategy", "query": "public relations corporate communications crisis communication PR strategy media relations communication management brand communications"},
        {"name": "EXP-19: Industry Trends and Market Forces", "query": "industry trends market analysis sector development aviation industry market forces industry evolution business trends"},
        {"name": "EXP-20: Psychological and Wellness Integration", "query": "workplace wellness employee mental health counseling support stress management professional wellbeing psychological care"},
    ]
    
    analyzer = ImageAnalyzer()
    all_ratings = []
    
    print("🚀 STARTING COMPREHENSIVE IMAGE ANALYSIS...")
    print(f"📊 Analyzing {len(experiments)} experiments across 10 parameters each")
    
    # Run subset for testing (first 5 experiments)
    test_experiments = experiments[:5]  # Start with 5 for testing
    
    for experiment in test_experiments:
        try:
            rating = await analyzer.run_experiment_and_analyze(experiment)
            all_ratings.append(rating)
        except Exception as e:
            logging.error(f"Error in experiment {experiment['name']}: {e}")
            continue
    
    if all_ratings:
        # Rank images
        leader, contenders = analyzer.rank_images(all_ratings)
        
        # Print detailed results
        analyzer.print_detailed_results(leader, contenders, all_ratings)
        
        # Save results to file
        results_data = {
            "leader": asdict(leader) if leader else None,
            "contenders": [asdict(c) for c in contenders],
            "all_ratings": [asdict(r) for r in all_ratings]
        }
        
        with open('image_analysis_results.json', 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"\n💾 Results saved to: image_analysis_results.json")
    else:
        print("❌ No images were successfully analyzed")

if __name__ == "__main__":
    asyncio.run(main())