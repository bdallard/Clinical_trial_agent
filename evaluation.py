"""
Evaluation script scenario

I want to launch a trial for my new Ulcerative Colitis treatment, what are typical eligibility criteria?
How many trials are currently recruiting for the same condition?
What's the average duration of clinical trials for type 2 diabetes treatments?
How many patients are typically needed for a Phase 3 Asthma trial?
What clinical sites have already been selected in Spain for Phase 2 Major Depressive Disorder trials?

What matters to evaluate??? 

"How many trials are currently recruiting?" → Counting
"What are typical eligibility criteria?" → Synthesis
"What's the average duration?" → Statistics
"What clinical sites in Spain?" → Location filtering

Question: Which of these is HARDEST for your agent to get right? That's where evaluation matters most.
"""

#from src/utils/utils import *

test_cases = [
    # Category 1: Factual queries (easy to verify)
    {
        "question": "How many diabetes trials are recruiting?",
        "expected_function": "count_trials",
        "verify": "Should return a number, check if reasonable (100-500 range)"
    },
    {
        "question": "What phase are most Alzheimer's trials?",
        "expected_function": ["search_trials", "calculate_statistics"],
        "verify": "Should give phase distribution"
    },
    
    # Category 2: Synthesis queries (harder)
    {
        "question": "What are typical inclusion criteria for asthma trials?",
        "expected_function": ["search_trials", "analyze_criteria"],
        "verify": "Should mention age, severity, medication use"
    },
    
    # Category 3: Edge cases
    {
        "question": "How many trials for [very rare disease]?",
        "expected_function": "count_trials",
        "verify": "Should return 0 or very low number, not fail"
    },
    
]

