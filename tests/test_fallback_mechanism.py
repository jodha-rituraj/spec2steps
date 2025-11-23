"""
Test to demonstrate LLM fallback for complex/unknown refactoring patterns
"""

import sys
sys.path.append('/Users/rituraj_jodha/Documents/Rituraj Jodha/Data Science/LLM/AI Automation From Requirements')

from utils.utils import refactorAutomationScriptWithFeedback

# Sample Java code
original_code = """package com.example.stepDefinitions;

import io.restassured.response.Response;
import org.apache.logging.log4j.Logger;

public class TestClass {
    
    private String orderName;
    private Response response;
    
    public void checkDevice() {
        if (orderName != null) {
            System.out.println("Checking device: " + orderName);
        }
    }
}
"""

print("=" * 80)
print("TEST 1: Known Pattern (rename_class) - Uses Pattern Matching")
print("=" * 80)

feedback1 = "Change class name from TestClass to OrderValidator"

try:
    diff1, refactored1 = refactorAutomationScriptWithFeedback(original_code, feedback1)
    print("\n✅ SUCCESS: Used pattern matching")
    print("\n📊 DIFF (clean, accurate):")
    print(diff1[:500])  # Show first 500 chars
except Exception as e:
    print(f"\n❌ ERROR: {e}")

print("\n\n" + "=" * 80)
print("TEST 2: Complex Feedback - Should Fallback to LLM")
print("=" * 80)

feedback2 = "Add null checks to all methods and add JavaDoc comments"

try:
    diff2, refactored2 = refactorAutomationScriptWithFeedback(original_code, feedback2)
    print("\n✅ SUCCESS: Used LLM fallback")
    print("\n📊 DIFF (may have formatting changes):")
    print(diff2[:500])  # Show first 500 chars
    print("\n⚠️  Note: Diff may show more changes due to LLM rewrite")
except Exception as e:
    print(f"\n❌ ERROR: {e}")

print("\n\n" + "=" * 80)
print("TEST 3: Unknown Pattern - Should Fallback to LLM")
print("=" * 80)

feedback3 = "Make this code enterprise ready with best practices"

try:
    diff3, refactored3 = refactorAutomationScriptWithFeedback(original_code, feedback3)
    print("\n✅ SUCCESS: Used LLM fallback")
    print("\n📊 DIFF:")
    print(diff3[:500])  # Show first 500 chars
except Exception as e:
    print(f"\n❌ ERROR: {e}")

print("\n\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("""
How the fallback works:

1. LLM extracts intent from feedback
2. If intent type matches known pattern → Use pattern (fast, accurate)
3. If intent type is "complex" or unknown → Raise ValueError
4. ValueError is caught → Falls back to fallback_llm_refactoring()
5. LLM does full code rewrite → Returns result (works, but less clean diff)

This ensures EVERY feedback gets processed, even if less optimal!
""")
