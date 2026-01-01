# Hybrid Refactoring System

## Overview

This system uses a **hybrid approach** combining LLM intelligence with deterministic pattern matching to provide **clean, accurate code refactoring** with minimal LLM calls.

## Architecture

```
User Feedback → Intent Extraction (LLM) → Pattern Matching (Regex) → Diff Generation (Python) → Result
```

### Components

1. **Intent Extraction** (`SYSTEM_INSTRUCTION_INTENT_EXTRACTION`)
   - Single LLM call to understand user feedback
   - Outputs structured JSON with change type, old/new values
   - Handles: rename_class, rename_method, remove_code, add_import, etc.

2. **Pattern-Based Application** (Deterministic)
   - `apply_rename_class()`: Renames class + all references
   - `apply_rename_method()`: Renames methods
   - `apply_remove_code()`: Removes specific code
   - `apply_add_import()`: Adds imports
   - More patterns easily added

3. **Diff Generation** (Python `difflib`)
   - Accurate unified diff format
   - Shows only actual changes
   - No formatting noise

4. **Fallback** (`SYSTEM_INSTRUCTION_FALLBACK_REFACTORING`)
   - Direct LLM refactoring when patterns fail
   - Safety net for edge cases

## Supported Change Types

### ✅ Simple (Pattern-Based - Recommended)
- Rename class/method/variable
- Add/remove imports
- Remove specific code
- Update strings/references

### ⚠️ Complex (Fallback LLM)
- Add new methods
- Restructure code
- Apply multiple complex changes

## Usage

```python
from utils.utils import refactorAutomationScriptWithFeedback

# Simple feedback
feedback = "Change class name from GeneratedTests to BlockDomainsTest"
diff, refactored_code = refactorAutomationScriptWithFeedback(original_code, feedback)

print(diff)  # Shows only class name change (3-4 lines)
```

## Benefits for 20B Models

1. **Single LLM Call**: Only for intent extraction (simple task)
2. **Deterministic Execution**: Pattern matching is 100% reliable
3. **Clean Diffs**: Only actual changes, no formatting noise
4. **Fast**: Minimal processing time
5. **Extensible**: Easy to add new patterns

## User Guidelines (in UI)

**Best Feedback Examples:**
- ✅ "Change class name from X to Y"
- ✅ "Rename method ABC to XYZ"
- ✅ "Add null check for parameter X"
- ✅ "Remove unused variable/import"

**Avoid:**
- ❌ "Make it better"
- ❌ "Apply all best practices"
- ❌ "Completely restructure"

## Testing

Run `test_hybrid_refactoring.py` to see examples of:
- Class renaming (3-4 line diff)
- Variable removal (1-2 line diff)
- Method renaming (2-3 line diff)

All with clean, accurate output.

## Extending

To add new refactoring patterns:

1. Add to `SUPPORTED_CHANGE_TYPES` in prompt
2. Create `apply_<pattern_name>()` function in utils.py
3. Add case in `apply_refactoring_change()`

Example:
```python
def apply_add_null_check(code: str, parameter_name: str) -> str:
    """Add null check for parameter."""
    # Implementation here
    pass
```
