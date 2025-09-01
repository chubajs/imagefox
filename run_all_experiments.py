#!/usr/bin/env python3
"""
Run all 20 ImageFox experiments on the easyJet article.
Each experiment will:
1. Extract different themes from the article
2. Generate unique search queries
3. Search Google Images via Apify
4. Analyze images with AI
5. Select the best image
"""

import json
import os
from typing import Dict, List, Tuple

# The actual easyJet article content
EASYJET_ARTICLE = """
easyJet pilot suspended in Cape Verde after public drunkenness incident
Airline confirms immediate suspension following alcohol-related incident at resort

By Sarah Mitchell, Aviation Correspondent
Published: August 30, 2025

An easyJet pilot has been suspended after allegedly being found drunk in public at a Cape Verde resort, just hours before he was scheduled to operate a return flight to London Gatwick. The incident, which occurred at the popular Santa Maria beach resort on the island of Sal, has prompted immediate action from the airline and raised questions about pilot wellness and industry oversight.

Local authorities reported that the pilot, whose identity has not been released, was discovered in an intoxicated state at approximately 3 AM local time on Thursday morning. Hotel security staff alerted police after finding the individual behaving erratically in the resort's pool area. The pilot was scheduled to operate flight EZY1234, departing at 10:30 AM for the seven-hour journey back to the UK.

"We can confirm that a crew member has been suspended pending investigation following an incident in Cape Verde," an easyJet spokesperson stated. "The safety and wellbeing of our passengers and crew is our highest priority. We have a zero-tolerance policy toward alcohol misuse and are taking this matter extremely seriously."

The airline acted swiftly to arrange alternative crew for the affected flight, which departed with a delay of approximately four hours. Passengers were provided with refreshments and compensation in line with EU regulations. Several travelers expressed concern upon learning about the incident, though praised the airline's transparent communication and swift response.

This incident occurs against a backdrop of increased scrutiny on pilot mental health and substance abuse within the aviation industry. Recent studies by the International Air Transport Association (IATA) indicate that while incidents involving pilot intoxication remain extremely rare – occurring in less than 0.01% of flights globally – the consequences can be severe both for safety and airline reputation.

Captain Timothy Richardson, a senior pilot and aviation safety consultant, emphasized the industry's typically robust safeguards: "Modern aviation has multiple layers of protection, including random testing, peer reporting systems, and strict regulatory oversight. When these rare incidents do occur, they're dealt with swiftly and seriously."

The UK Civil Aviation Authority requires pilots to abstain from alcohol for at least eight hours before flying, though many airlines impose stricter policies. Blood alcohol limits for pilots are set at 20mg per 100ml – a quarter of the drink-drive limit in England and Wales. Violations can result in immediate license suspension, criminal prosecution, and career termination.

Industry experts note that the pressures of modern aviation – including irregular schedules, time zone changes, and extended periods away from home – can contribute to stress and potentially problematic behaviors. Dr. Amanda Foster, an aviation psychologist, suggests that "the industry needs to balance strict enforcement with supportive intervention programs that encourage self-reporting and treatment."

The incident has sparked discussion within pilot communities about the effectiveness of current support systems. The British Airline Pilots Association (BALPA) has long advocated for enhanced mental health and wellbeing programs, arguing that creating a culture where pilots feel safe seeking help is crucial for maintaining safety standards.

For easyJet, this incident comes at a challenging time as the airline industry continues to navigate post-pandemic recovery, staff shortages, and industrial relations tensions. The carrier, which operates over 1,000 routes across 35 countries, has generally maintained a strong safety record throughout its 30-year history.

The Cape Verde authorities have confirmed that no criminal charges will be filed, as public intoxication is not a criminal offense on the islands. However, the pilot faces potential regulatory action from the UK CAA and almost certain termination of employment pending the airline's internal investigation.

This incident serves as a stark reminder of the aviation industry's ongoing challenges in maintaining the highest safety standards while supporting the wellbeing of its workforce. As one industry veteran noted, "Every incident, however rare, is an opportunity to strengthen our systems and ensure the traveling public's continued confidence in air travel."

The investigation continues, with findings expected to be reviewed by both easyJet's safety committee and relevant regulatory authorities. The airline has stated it will fully cooperate with all investigations and will implement any recommended changes to prevent similar incidents in the future.
"""

# Define all 20 experimental approaches
EXPERIMENTS = [
    {
        "id": "EXP-01",
        "name": "Aviation Industry Focus",
        "approach": lambda article: extract_aviation_themes(article),
        "query_generator": lambda themes: "commercial aviation airline industry pilot training flight operations aviation safety"
    },
    {
        "id": "EXP-02", 
        "name": "Corporate Trust & Leadership",
        "approach": lambda article: extract_leadership_themes(article),
        "query_generator": lambda themes: "corporate leadership executive management business integrity organizational trust"
    },
    {
        "id": "EXP-03",
        "name": "Media & Communication Strategy",
        "approach": lambda article: extract_communication_themes(article),
        "query_generator": lambda themes: "corporate communication public relations media strategy crisis PR"
    },
    {
        "id": "EXP-04",
        "name": "Innovation Technology",
        "approach": lambda article: extract_innovation_themes(article),
        "query_generator": lambda themes: "business technology innovation digital transformation aviation tech"
    },
    {
        "id": "EXP-05",
        "name": "Competitive Market Dynamics",
        "approach": lambda article: extract_competition_themes(article),
        "query_generator": lambda themes: "competitive market analysis business competition airline industry"
    },
    {
        "id": "EXP-06",
        "name": "Financial Impact",
        "approach": lambda article: extract_financial_themes(article),
        "query_generator": lambda themes: "financial impact economic analysis business economics cost management"
    },
    {
        "id": "EXP-07",
        "name": "HR & Talent Management",
        "approach": lambda article: extract_hr_themes(article),
        "query_generator": lambda themes: "human resources talent management employee development workplace policy"
    },
    {
        "id": "EXP-08",
        "name": "Customer Experience",
        "approach": lambda article: extract_customer_themes(article),
        "query_generator": lambda themes: "customer experience stakeholder management service quality passenger safety"
    },
    {
        "id": "EXP-09",
        "name": "Crisis Management",
        "approach": lambda article: extract_crisis_themes(article),
        "query_generator": lambda themes: "crisis management emergency response business continuity incident management"
    },
    {
        "id": "EXP-10",
        "name": "Regulatory Compliance",
        "approach": lambda article: extract_regulatory_themes(article),
        "query_generator": lambda themes: "regulatory compliance aviation regulations business governance safety standards"
    },
    {
        "id": "EXP-11",
        "name": "Cultural Values",
        "approach": lambda article: extract_cultural_themes(article),
        "query_generator": lambda themes: "corporate culture organizational values workplace ethics safety culture"
    },
    {
        "id": "EXP-12",
        "name": "Strategic Planning",
        "approach": lambda article: extract_strategic_themes(article),
        "query_generator": lambda themes: "strategic business planning corporate strategy airline operations management"
    },
    {
        "id": "EXP-13",
        "name": "Risk Assessment",
        "approach": lambda article: extract_risk_themes(article),
        "query_generator": lambda themes: "business risk assessment corporate risk management operational risk mitigation"
    },
    {
        "id": "EXP-14",
        "name": "Performance Excellence",
        "approach": lambda article: extract_performance_themes(article),
        "query_generator": lambda themes: "business performance excellence operational efficiency quality management"
    },
    {
        "id": "EXP-15",
        "name": "Brand Management",
        "approach": lambda article: extract_brand_themes(article),
        "query_generator": lambda themes: "brand management corporate reputation brand protection reputation crisis"
    },
    {
        "id": "EXP-16",
        "name": "PR Strategy",
        "approach": lambda article: extract_pr_themes(article),
        "query_generator": lambda themes: "public relations crisis communication media management damage control"
    },
    {
        "id": "EXP-17",
        "name": "Global Operations",
        "approach": lambda article: extract_global_themes(article),
        "query_generator": lambda themes: "global business operations international aviation cross-border management"
    },
    {
        "id": "EXP-18",
        "name": "Sustainability Focus",
        "approach": lambda article: extract_sustainability_themes(article),
        "query_generator": lambda themes: "corporate sustainability responsible business aviation environment safety"
    },
    {
        "id": "EXP-19",
        "name": "Industry Trends",
        "approach": lambda article: extract_trends_themes(article),
        "query_generator": lambda themes: "aviation industry trends airline sector analysis market developments"
    },
    {
        "id": "EXP-20",
        "name": "Wellness Integration",
        "approach": lambda article: extract_wellness_themes(article),
        "query_generator": lambda themes: "workplace wellness employee mental health pilot wellbeing support programs"
    }
]

# Theme extraction functions (simplified versions)
def extract_aviation_themes(article: str) -> List[str]:
    """Extract aviation-specific themes."""
    themes = []
    if "pilot" in article.lower():
        themes.append("pilot operations")
    if "flight" in article.lower():
        themes.append("flight safety")
    if "aviation" in article.lower():
        themes.append("aviation industry")
    if "airline" in article.lower():
        themes.append("airline management")
    return themes

def extract_leadership_themes(article: str) -> List[str]:
    """Extract leadership and governance themes."""
    themes = []
    if "management" in article.lower() or "executive" in article.lower():
        themes.append("executive leadership")
    if "decision" in article.lower() or "action" in article.lower():
        themes.append("decision making")
    if "trust" in article.lower() or "confidence" in article.lower():
        themes.append("organizational trust")
    return themes

def extract_communication_themes(article: str) -> List[str]:
    """Extract communication and PR themes."""
    themes = []
    if "spokesperson" in article.lower() or "stated" in article.lower():
        themes.append("corporate communication")
    if "public" in article.lower() or "media" in article.lower():
        themes.append("public relations")
    if "transparent" in article.lower():
        themes.append("transparency")
    return themes

def extract_risk_themes(article: str) -> List[str]:
    """Extract risk management themes."""
    themes = []
    if "risk" in article.lower() or "consequence" in article.lower():
        themes.append("risk assessment")
    if "safety" in article.lower():
        themes.append("safety management")
    if "incident" in article.lower():
        themes.append("incident prevention")
    if "mitigation" in article.lower() or "prevent" in article.lower():
        themes.append("risk mitigation")
    return themes

def extract_brand_themes(article: str) -> List[str]:
    """Extract brand and reputation themes."""
    themes = []
    if "reputation" in article.lower():
        themes.append("reputation management")
    if "brand" in article.lower() or "image" in article.lower():
        themes.append("brand protection")
    if "trust" in article.lower() or "confidence" in article.lower():
        themes.append("brand trust")
    return themes

def extract_crisis_themes(article: str) -> List[str]:
    """Extract crisis management themes."""
    themes = []
    if "incident" in article.lower():
        themes.append("incident response")
    if "emergency" in article.lower() or "immediate" in article.lower():
        themes.append("emergency management")
    if "response" in article.lower() or "action" in article.lower():
        themes.append("crisis response")
    return themes

def extract_financial_themes(article: str) -> List[str]:
    """Extract financial impact themes."""
    themes = []
    if "cost" in article.lower() or "compensation" in article.lower():
        themes.append("financial impact")
    if "delay" in article.lower() or "disruption" in article.lower():
        themes.append("operational costs")
    return themes

def extract_regulatory_themes(article: str) -> List[str]:
    """Extract regulatory compliance themes."""
    themes = []
    if "regulation" in article.lower() or "authority" in article.lower():
        themes.append("regulatory compliance")
    if "policy" in article.lower() or "requirement" in article.lower():
        themes.append("policy adherence")
    return themes

def extract_wellness_themes(article: str) -> List[str]:
    """Extract wellness and mental health themes."""
    themes = []
    if "mental health" in article.lower() or "wellbeing" in article.lower():
        themes.append("employee wellness")
    if "support" in article.lower() or "help" in article.lower():
        themes.append("support programs")
    if "stress" in article.lower() or "pressure" in article.lower():
        themes.append("stress management")
    return themes

# Placeholder functions for other themes
def extract_innovation_themes(article: str) -> List[str]:
    return ["technology adoption", "digital innovation"]

def extract_competition_themes(article: str) -> List[str]:
    return ["market competition", "industry dynamics"]

def extract_hr_themes(article: str) -> List[str]:
    return ["talent management", "employee relations"]

def extract_customer_themes(article: str) -> List[str]:
    return ["customer service", "passenger experience"]

def extract_cultural_themes(article: str) -> List[str]:
    return ["organizational culture", "values alignment"]

def extract_strategic_themes(article: str) -> List[str]:
    return ["strategic planning", "business strategy"]

def extract_performance_themes(article: str) -> List[str]:
    return ["operational excellence", "performance metrics"]

def extract_pr_themes(article: str) -> List[str]:
    return ["public relations", "media management"]

def extract_global_themes(article: str) -> List[str]:
    return ["global operations", "international business"]

def extract_sustainability_themes(article: str) -> List[str]:
    return ["sustainability", "corporate responsibility"]

def extract_trends_themes(article: str) -> List[str]:
    return ["industry trends", "market analysis"]


def run_experiment(exp_config: Dict) -> Dict:
    """Run a single experiment."""
    print(f"\n{'='*60}")
    print(f"Running {exp_config['id']}: {exp_config['name']}")
    print(f"{'='*60}")
    
    # Extract themes using the specific approach
    themes = exp_config['approach'](EASYJET_ARTICLE)
    print(f"Extracted themes: {themes}")
    
    # Generate search query
    search_query = exp_config['query_generator'](themes)
    print(f"Search query: {search_query}")
    
    # TODO: Here we would normally:
    # 1. Call Apify Google Images Scraper with the search query
    # 2. Get image results
    # 3. Analyze images with Vision AI
    # 4. Select the best image
    # 5. Store results
    
    # For now, return experiment metadata
    return {
        "experiment_id": exp_config['id'],
        "experiment_name": exp_config['name'],
        "extracted_themes": themes,
        "search_query": search_query,
        "status": "ready_for_apify_search"
    }


def main():
    """Run all experiments."""
    print("ImageFox Experiment Runner")
    print(f"Article: easyJet pilot incident ({len(EASYJET_ARTICLE)} characters)")
    print(f"Total experiments: {len(EXPERIMENTS)}")
    
    results = []
    for exp in EXPERIMENTS:
        result = run_experiment(exp)
        results.append(result)
    
    # Save results
    output_file = "experiment_queries.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"All experiments complete!")
    print(f"Results saved to: {output_file}")
    print(f"\nNext steps:")
    print("1. Use these queries with Apify Google Images Scraper")
    print("2. Analyze returned images with Vision AI")
    print("3. Select best image for each approach")
    print("4. Compare which approach found the best image")


if __name__ == "__main__":
    main()