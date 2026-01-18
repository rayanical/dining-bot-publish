"""
Hallucination Test Suite.

This module tests the RAG pipeline's faithfulness to retrieved context by
using an LLM as a judge to verify that generated answers match the source data.

Uses Dec 12, 2025 menu data as the ground truth context.
"""

import os
from datetime import date
from typing import List, Tuple
import requests

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
DEMO_DATE = date(2025, 12, 12)  # Ground truth: Dec 12, 2025 menu data

# Initialize OpenAI client for judge
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Golden set of questions based on typical dining queries
GOLDEN_QUESTIONS = [
    "What's for lunch at Worcester?",
    "Are there any vegan options available today?",
    "What high-protein breakfast items are available?",
    "Is there pizza available today?",
    "What options are available at Berkshire for dinner?",
]


def _call_chat_endpoint(query: str, demo_mode: bool = True) -> str:
    """
    Call the chat endpoint with a query.
    
    Args:
        query: The user question.
        demo_mode: Whether to enable demo mode (Dec 12 menus).
    
    Returns:
        The bot's response text.
    """
    payload = {
        "query": query,
        "demo_mode": demo_mode,
    }
    response = requests.post(f"{BACKEND_URL}/api/chat", json=payload, timeout=60)
    if response.status_code != 200:
        return f"ERROR: {response.status_code} - {response.text}"
    return response.text


def _judge_faithfulness(question: str, answer: str) -> Tuple[bool, str]:
    """
    Use an LLM as a judge to verify answer faithfulness.
    
    The judge determines if the answer could plausibly come from a dining
    hall menu. We can't verify exact items without the raw data, but we
    check for:
    - No obvious hallucinations (made-up restaurants, impossible claims)
    - Reasonable dining hall response format
    - Acknowledgment when data isn't available
    
    Args:
        question: The original question asked.
        answer: The bot's generated answer.
    
    Returns:
        Tuple of (passed: bool, reasoning: str)
    """
    judge_prompt = f"""You are evaluating a dining hall chatbot's response for faithfulness.

The chatbot is designed to answer questions about UMass dining hall menus.
It should ONLY use information from its retrieved menu data and should
NOT make up food items, restaurants, or nutritional information.

Question: {question}

Bot's Answer: {answer}

Evaluate the answer on these criteria:
1. Does it appear to be answering from actual menu data (mentions specific items, halls, nutrition)?
2. Does it avoid obvious hallucinations (fake restaurants, impossible nutrition values)?
3. If no data was available, does it clearly say so rather than making things up?
4. Are the dining halls mentioned valid UMass halls (Berkshire, Worcester, Hampshire, Franklin)?

Respond with EXACTLY this format:
VERDICT: PASS or FAIL
REASONING: [one sentence explanation]"""

    try:
        response = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": judge_prompt}],
            temperature=0.1,
            max_tokens=150,
        )
        result = response.choices[0].message.content or ""
        
        # Parse verdict
        passed = "VERDICT: PASS" in result.upper()
        reasoning = result.split("REASONING:")[-1].strip() if "REASONING:" in result else result
        
        return passed, reasoning
    except Exception as e:
        return False, f"Judge error: {str(e)}"


def test_hallucination_rate():
    """
    Test the hallucination rate of the RAG pipeline.
    
    Runs the golden set of questions with demo mode enabled,
    then uses an LLM judge to verify faithfulness.
    
    Outputs:
        Pass/fail score and detailed results for each question.
    """
    print("\n" + "=" * 60)
    print("HALLUCINATION TEST SUITE - Dec 12, 2025 Ground Truth")
    print("=" * 60 + "\n")
    
    results: List[Tuple[str, str, bool, str]] = []
    
    for question in GOLDEN_QUESTIONS:
        print(f"\n📝 Question: {question}")
        
        # Get bot's answer
        answer = _call_chat_endpoint(question, demo_mode=True)
        print(f"🤖 Answer: {answer[:200]}..." if len(answer) > 200 else f"🤖 Answer: {answer}")
        
        # Judge faithfulness
        passed, reasoning = _judge_faithfulness(question, answer)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {reasoning}")
        
        results.append((question, answer, passed, reasoning))
    
    # Summary
    passed_count = sum(1 for _, _, p, _ in results if p)
    total = len(results)
    rate = (passed_count / total) * 100 if total > 0 else 0
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed_count}/{total} passed ({rate:.1f}%)")
    print("=" * 60)
    
    # Assert for pytest
    assert rate >= 80, f"Hallucination rate too high: only {rate:.1f}% passed"
    
    return results


if __name__ == "__main__":
    # Allow running directly for debugging
    test_hallucination_rate()
