# Test Suite

This folder contains all test cases for the AI Automation From Requirements hybrid refactoring system.

## Test Files

### 1. `test_diff_accuracy.py`
**Purpose**: Demonstrates accurate diff generation using Python's `difflib`

**What it tests**:
- Clean 3-line diffs for simple changes (class rename)
- No formatting noise or extra whitespace changes
- Unified diff format with context lines

**Run**: `python tests/test_diff_accuracy.py`

---

### 2. `test_hybrid_refactoring.py`
**Purpose**: Tests pattern-based refactoring functions

**What it tests**:
- Class renaming (`LoginTest` → `AuthTest`)
- Variable removal (`DEBUG_MODE` variable)
- Method renaming (`validateUser` → `authenticateUser`)

**Expected Output**:
- Clean diffs showing only actual changes
- No formatting changes
- All 3 test cases should pass

**Run**: `python tests/test_hybrid_refactoring.py`

---

### 3. `test_case_conversion.py`
**Purpose**: Tests snake_case ↔ camelCase conversion patterns

**What it tests**:
- Method name conversions (6 different cases)
- Accurate regex-based pattern matching
- Both directions: snake_to_camel and camel_to_snake

**Test Cases**:
1. `validate_user` → `validateUser`
2. `get_user_data` → `getUserData`
3. `process_payment_info` → `processPaymentInfo`
4. `validate_email` → `validateEmail`
5. `send_notification` → `sendNotification`
6. `calculate_total_price` → `calculateTotalPrice`

**Expected Output**: All 6 conversions should be accurate

**Run**: `python tests/test_case_conversion.py`

---

### 4. `test_fallback_mechanism.py`
**Purpose**: Tests the LLM fallback mechanism for unknown/complex patterns

**What it tests**:
- Known patterns use pattern matching (fast, clean)
- Complex feedback triggers LLM fallback
- Unknown patterns trigger LLM fallback
- System never fails, always returns something

**Test Scenarios**:
1. **Known Pattern**: `rename LoginTest to AuthTest`
   - Should use pattern matching
   - Clean 3-line diff

2. **Complex Feedback**: `add error handling to all methods`
   - Should trigger LLM fallback
   - May have formatting changes but works

3. **Unknown Pattern**: `do_some_weird_thing`
   - Should trigger LLM fallback
   - Fallback to full rewrite

**Run**: `python tests/test_fallback_mechanism.py`

---

## Running Tests

### Run All Tests
```bash
# From project root
python -m pytest tests/

# Or run individually
python tests/test_diff_accuracy.py
python tests/test_hybrid_refactoring.py
python tests/test_case_conversion.py
python tests/test_fallback_mechanism.py
```

### Run Specific Test
```bash
python tests/test_hybrid_refactoring.py
```

### Run with Verbose Output
```bash
python -m pytest tests/ -v
```

## Test Results Expected

All tests should:
- ✅ Execute without errors
- ✅ Show accurate diffs (only actual changes)
- ✅ Demonstrate pattern matching works
- ✅ Prove fallback mechanism activates when needed

## Dependencies

Tests require:
- Python 3.13+
- `difflib` (standard library)
- `re` (standard library)
- `json` (standard library)
- Project modules: `utils.utils`, `llm_prompts.java_automation_feedback_agent`

## Test Coverage

Current coverage:
- ✅ Diff accuracy
- ✅ Pattern-based refactoring (9 patterns)
- ✅ Case conversion (snake_case ↔ camelCase)
- ✅ LLM fallback mechanism
- ✅ Intent extraction
- ⏸️ API routes (future)
- ⏸️ Feature file parsing (future)
- ⏸️ Java code generation (future)

## Adding New Tests

To add a new test:

1. Create `test_your_feature.py` in this folder
2. Import required modules from `utils` or `llm_prompts`
3. Write test functions or main block
4. Update this README with test description
5. Run to verify it works

Example structure:
```python
from utils.utils import your_function

def test_your_feature():
    # Arrange
    input_data = "test input"
    
    # Act
    result = your_function(input_data)
    
    # Assert
    assert result == expected_output
    print("✅ Test passed!")

if __name__ == "__main__":
    test_your_feature()
```

## Troubleshooting

**ImportError**: Make sure you're running from project root:
```bash
cd /path/to/AI Automation From Requirements
python tests/test_file.py
```

**ModuleNotFoundError**: Ensure all dependencies are installed and Python path is correct.

**Test Failures**: Check if utils functions have been modified. Update tests accordingly.

---

**Last Updated**: January 2026  
**Status**: All tests passing ✅
