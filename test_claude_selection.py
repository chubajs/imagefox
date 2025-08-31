#!/usr/bin/env python3
"""Test Claude Sonnet 4 selection process"""

import json
from dotenv import load_dotenv
from openrouter_client import OpenRouterClient

load_dotenv()

def test_claude_selection():
    print("Testing Claude Sonnet 4 selection...")
    
    client = OpenRouterClient()
    image_url = 'https://i.ibb.co/ycDQJN5g/healthcare-ai-ma-2025.webp'

    selection_prompt = """You are selecting the best image for this healthcare article:

**Title**: "2025 Healthcare Outlook: M&A and AI Drive Margin Growth"
**Themes**: hospital mergers, AI automation, cost reduction, digital transformation

**This image analysis**:
- Quality Score: 0.90 (high quality infographic)
- Relevance Score: 0.95 (directly about healthcare M&A)  
- Scene: Professional infographic
- Content: "Challenges in healthcare M&A" with 4 key areas

**Your task**: Evaluate if this image is suitable for the article and provide reasoning.

Return JSON:
{
  "suitable": true,
  "confidence": 0.95,
  "reasoning": "detailed explanation",
  "score_breakdown": {
    "relevance_to_topic": 0.95,
    "visual_quality": 0.90,
    "professional_appearance": 0.95
  }
}"""

    try:
        result = client.analyze_image(
            image_input=image_url,
            prompt=selection_prompt,
            model='anthropic/claude-sonnet-4',
            max_tokens=500,
            temperature=0.2
        )
        
        print('✅ Claude Sonnet 4 selection successful!')
        print(f'💰 Cost: ${result.cost_estimate:.6f}')
        
        try:
            selection = json.loads(result.description)
            print(f'\n🎯 SELECTION RESULT:')
            print(f'   Suitable: {selection.get("suitable", "N/A")}')
            print(f'   Confidence: {selection.get("confidence", "N/A")}')  
            print(f'   Reasoning: {selection.get("reasoning", "N/A")[:150]}...')
            
            scores = selection.get('score_breakdown', {})
            print(f'\n📊 DETAILED SCORES:')
            for key, value in scores.items():
                print(f'   {key}: {value}')
                
            return True
                
        except json.JSONDecodeError:
            print('⚠️ Response not in JSON format:')
            print(result.description[:300])
            return False
            
    except Exception as e:
        print(f'❌ Claude selection failed: {e}')
        return False

if __name__ == "__main__":
    success = test_claude_selection()
    print(f"\n{'✅ CLAUDE TEST PASSED' if success else '❌ CLAUDE TEST FAILED'}")
