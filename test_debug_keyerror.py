#!/usr/bin/env python3
"""
Test script to reproduce the KeyError: '\n  "intent"' issue
"""
import sys
import json
from agents.automation_script_agent import AutomationScriptAgent

# Create a simple test case
def test_merged_script_json():
    print("="*80)
    print("TEST: Reproducing KeyError issue")
    print("="*80)
    
    # Create a sample merged_script_json like the one from the app
    sample_json = {
        "package": "com.example.tests",
        "imports": [
            "io.restassured.RestAssured",
            "org.testng.annotations.Test"
        ],
        "className": "GeneratedTests",
        "classAnnotations": ["@Test"],
        "fields": [],
        "methods": [
            {
                "scenario_id": "scenario_1",
                "name": "testScenario1",
                "annotations": ["@Test"],
                "body": "// test code here"
            }
        ]
    }
    
    print("\n1. Testing with clean dict:")
    print(f"   Type: {type(sample_json)}")
    print(f"   Keys: {list(sample_json.keys())}")
    
    # Now try to create the agent and call the method
    print("\n2. Creating AutomationScriptAgent...")
    try:
        agent = AutomationScriptAgent(llm=None)  # No LLM needed for this test
        print("   ✓ Agent created successfully")
    except Exception as e:
        print(f"   ✗ Error creating agent: {e}")
        return
    
    # Try calling the method (it will fail on LLM check, but that's OK)
    print("\n3. Attempting to call chat_refine_script_json...")
    try:
        result = agent.chat_refine_script_json(
            current_script_json=sample_json,
            chat_messages=[],
            user_message="test message"
        )
        print(f"   Result: {result}")
    except ValueError as e:
        if "LLM not initialized" in str(e):
            print("   ✓ Got expected LLM error (this is OK)")
        else:
            print(f"   ✗ Unexpected ValueError: {e}")
    except KeyError as e:
        print(f"   ✗ GOT THE KEYERROR: {e}")
        print(f"   Error args: {e.args}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"   ✗ Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)


def test_with_malformed_keys():
    """Test what happens with dict that has weird keys"""
    print("\n" + "="*80)
    print("TEST: Dict with malformed keys")
    print("="*80)
    
    # Create a dict with a weird key like we're seeing in the error
    weird_dict = {
        '\n  "intent"': "some_value",
        "normal_key": "normal_value"
    }
    
    print(f"\n1. Dict with weird key:")
    print(f"   Type: {type(weird_dict)}")
    print(f"   Number of keys: {len(weird_dict)}")
    for i, key in enumerate(weird_dict.keys()):
        print(f"   Key {i}: {repr(key)}")
    
    # Try to access the weird key
    print(f"\n2. Accessing weird key:")
    try:
        value = weird_dict['\n  "intent"']
        print(f"   ✓ Value: {value}")
    except KeyError as e:
        print(f"   ✗ KeyError: {e}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    test_merged_script_json()
    test_with_malformed_keys()
    
    print("\n✅ All tests completed")
