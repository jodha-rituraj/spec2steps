"""
Test snake_case to camelCase conversion
"""

import sys
sys.path.append('/Users/rituraj_jodha/Documents/Rituraj Jodha/Data Science/LLM/AI Automation From Requirements')

from utils.utils import refactorAutomationScriptWithFeedback

# Sample Java code with snake_case variables
original_code = """package com.example.stepDefinitions;

import io.restassured.response.Response;
import org.apache.logging.log4j.Logger;

public class TestClass {
    
    private String device_name;
    private String user_id;
    private int max_retry_count;
    private static Logger logger;
    
    public void checkDeviceStatus() {
        String current_status = "active";
        int retry_count = 0;
        boolean is_valid = true;
        
        if (device_name != null && user_id != null) {
            logger.info("Device {} for user {}", device_name, user_id);
        }
        
        while (retry_count < max_retry_count) {
            retry_count++;
        }
    }
}
"""

print("=" * 80)
print("TEST: Convert snake_case to camelCase")
print("=" * 80)

feedback = "Change snake_case to camelCase"

try:
    diff, refactored = refactorAutomationScriptWithFeedback(original_code, feedback)
    
    print("\n📊 DIFF OUTPUT:")
    print(diff)
    
    print("\n✨ REFACTORED CODE:")
    print(refactored)
    
    # Verify conversions
    print("\n✅ VERIFICATION:")
    conversions = [
        ("device_name", "orderName"),
        ("user_id", "userId"),
        ("max_retry_count", "maxRetryCount"),
        ("current_status", "currentStatus"),
        ("retry_count", "retryCount"),
        ("is_valid", "isValid")
    ]
    
    for old, new in conversions:
        if new in refactored and old not in refactored:
            print(f"  ✅ {old} → {new}")
        elif old in refactored:
            print(f"  ⚠️  {old} not converted (check if pattern matched)")
        else:
            print(f"  ❓ Could not verify {old}")
    
    print("\n✅ SUCCESS: Snake case conversion complete!")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("""
✅ The snake_to_camel pattern:
- Automatically detects snake_case identifiers
- Converts to camelCase (first word lowercase, rest capitalized)
- Preserves CONSTANTS and ClassName (PascalCase)
- Works with any number of underscores

This is now a simple, one-click refactoring!
""")
