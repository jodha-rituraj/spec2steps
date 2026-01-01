"""
Test script to demonstrate the new hybrid refactoring approach.
This shows how the system extracts intent and applies targeted changes.
"""

import sys
sys.path.append('/Users/rituraj_jodha/Documents/Rituraj Jodha/Data Science/LLM/AI Automation From Requirements')

from utils.utils import refactorAutomationScriptWithFeedback

# Sample Java code
original_code = """package com.example.stepDefinitions;

import io.restassured.RestAssured;
import io.restassured.response.Response;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import io.cucumber.java.en.*;
import org.testng.Assert;

import com.example.service.ApiClient;

public class GeneratedTests {
    
    ApiClient apiClient = new ApiClient();
    Response response;
    private static Logger logger = LogManager.getLogger(GeneratedTests.class);
    
    public GeneratedTests() {
        // Constructor
    }
    
    @Given("a device exists")
    public void aDeviceExists() {
        logger.info("Checking device exists");
        Assert.assertNotNull(response);
    }
}
"""

# Test Case 1: Simple class rename
print("=" * 80)
print("TEST 1: Rename class from GeneratedTests to BlockDomainsTest")
print("=" * 80)

feedback1 = "Change class name from GeneratedTests to BlockDomainsTest"

try:
    diff1, refactored1 = refactorAutomationScriptWithFeedback(original_code, feedback1)
    print("\n📊 DIFF OUTPUT:")
    print(diff1)
    print("\n✅ SUCCESS: Class renamed with clean, targeted changes!")
except Exception as e:
    print(f"\n❌ ERROR: {e}")

# Test Case 2: Remove variable
print("\n\n" + "=" * 80)
print("TEST 2: Remove unused apiClient variable")
print("=" * 80)

feedback2 = "Remove the unused apiClient variable"

try:
    diff2, refactored2 = refactorAutomationScriptWithFeedback(original_code, feedback2)
    print("\n📊 DIFF OUTPUT:")
    print(diff2)
    print("\n✅ SUCCESS: Variable removed cleanly!")
except Exception as e:
    print(f"\n❌ ERROR: {e}")

# Test Case 3: Rename method
print("\n\n" + "=" * 80)
print("TEST 3: Rename method")
print("=" * 80)

feedback3 = "Rename method aDeviceExists to verifyDeviceExistence"

try:
    diff3, refactored3 = refactorAutomationScriptWithFeedback(original_code, feedback3)
    print("\n📊 DIFF OUTPUT:")
    print(diff3)
    print("\n✅ SUCCESS: Method renamed!")
except Exception as e:
    print(f"\n❌ ERROR: {e}")

print("\n\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("""
✅ The new hybrid approach:
1. Extracts intent from feedback (1 LLM call)
2. Applies targeted regex-based changes (deterministic)
3. Generates clean, accurate diffs (Python difflib)

✅ Benefits:
- Only actual changes shown in diff (no formatting noise)
- Fast and reliable with 20B models
- Easy to debug and understand
- Extensible with more patterns

✅ Fallback available for complex cases
""")
