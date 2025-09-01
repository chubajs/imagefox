# ImageFox Experiments

This folder contains the complete ImageFox experiment pipeline and results.

## 📊 Experiment Results

**Methodology Validated**: Different analytical approaches to the same content produce different image search results.

### Top Results (Real Google Images):
1. 🥇 **Aviation Industry Focus** - Score: 87.79/100
   - Image: CAE Pilot Training Program
   - Source: CAE.com

2. 🥈 **Brand Management** - Score: 87.75/100
   - Image: Reputation Management Diagram
   - Source: Determ.com

3. 🥉 **Crisis Management** - Score: 87.06/100
   - Image: Crisis Management Cycle
   - Source: ResearchGate

## 📁 Files

### Pipeline Scripts
- `execute_imagefox_pipeline.py` - Main pipeline runner
- `run_all_experiments.py` - Generate and run all 20 experiments
- `run_key_experiments.py` - Run top 5 experiments only
- `check_results.py` - Analyze and rank results
- `image_analysis_tool.py` - 10-parameter scoring system

### Data Files
- `experiment_queries.json` - All 20 search queries generated
- `experiment_results/` - JSON results for each experiment
  - `EXP-01.json` - Aviation Industry Focus
  - `EXP-03.json` - Media & Communication
  - `EXP-09.json` - Crisis Management
  - `EXP-13.json` - Risk Assessment
  - `EXP-15.json` - Brand Management

### Results
- `imagefox_real_results.html` - Interactive comparison page

## 🚀 Running Experiments

### Single Experiment
```bash
cd experiments
python ../test_single_experiment.py
```

### Top 5 Experiments
```bash
python run_key_experiments.py
```

### All 20 Experiments
```bash
python run_all_experiments.py
```

### Check Results
```bash
python check_results.py
```

## 📈 Scoring Parameters

Each image is scored on 10 parameters:
1. **Relevance to Article** (Weight: 1.5x)
2. **Concept Clarity** (Weight: 1.3x)
3. **Professional Appeal** (Weight: 1.2x)
4. **Visual Quality** (Weight: 1.1x)
5. **Contextual Fit** (Weight: 1.1x)
6. Brand Appropriateness
7. Emotional Impact
8. Informational Value
9. Uniqueness
10. Scalability

## 🔍 Experiment Types

All 20 experiments analyzed the same easyJet pilot incident article:

1. EXP-01: Aviation Industry Focus
2. EXP-02: Corporate Trust & Leadership
3. EXP-03: Media & Communication Strategy
4. EXP-04: Innovation Technology
5. EXP-05: Competitive Market Dynamics
6. EXP-06: Financial Impact
7. EXP-07: HR & Talent Management
8. EXP-08: Customer Experience
9. EXP-09: Crisis Management
10. EXP-10: Regulatory Compliance
11. EXP-11: Cultural Values
12. EXP-12: Strategic Planning
13. EXP-13: Risk Assessment
14. EXP-14: Performance Excellence
15. EXP-15: Brand Management
16. EXP-16: PR Strategy
17. EXP-17: Global Operations
18. EXP-18: Sustainability Focus
19. EXP-19: Industry Trends
20. EXP-20: Wellness Integration

## ✅ Key Finding

The same article analyzed through different lenses produces completely different search queries and finds completely different images from Google, proving the ImageFox methodology.