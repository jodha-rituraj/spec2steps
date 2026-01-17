# JSON-Based Workflow for Gherkin Generation

## 🎯 Overview

This document describes the major architectural refactoring that moves the Gherkin feature file generation from **text-based** to **JSON-based** workflow, enabling **surgical, targeted edits** instead of full regeneration.

## 🔄 What Changed?

### Before (Text-Based)
```
Requirements → LLM → Gherkin Text → Feedback → LLM → New Gherkin Text
```
- LLM generated complete Gherkin files as plain text
- Feedback required regenerating the entire file
- Hard to make targeted changes
- Difficult to track what changed
- Inconsistent formatting

### After (JSON-Based)
```
Requirements → LLM → JSON Structure → Feedback → LLM → Updated JSON → Gherkin Text
```
- LLM generates structured JSON
- Feedback applies **surgical changes** to JSON
- Convert to Gherkin only when needed (for automation scripts)
- Easy to track changes at scenario/step level
- Consistent structure

## 📦 New Components

### 1. `utils/gherkin_json_utils.py`
Contains core utilities:

```python
# Convert JSON to Gherkin
gherkin_text = json_to_gherkin(json_data)

# Convert Gherkin to JSON (for migration/testing)
json_data = gherkin_to_json(gherkin_text)

# Validate JSON structure
is_valid, errors = validate_gherkin_json(json_data)
```

### 2. Updated JSON Schema

```json
{
  "feature": {
    "name": "Feature name",
    "description": "Optional description",
    "tags": ["@tag1", "@tag2"]
  },
  "background": {
    "steps": [
      {"type": "Given", "text": "step text"},
      {"type": "And", "text": "step text"}
    ]
  },
  "scenarios": [
    {
      "id": "scenario_1",
      "type": "Scenario|Scenario Outline",
      "name": "Scenario name",
      "tags": ["@smoke"],
      "steps": [
        {"type": "Given|When|Then|And|But", "text": "step text"}
      ],
      "examples": {
        "headers": ["col1", "col2"],
        "rows": [
          ["val1", "val2"],
          ["val3", "val4"]
        ]
      }
    }
  ]
}
```

## 🔧 Updated Functions

### Generation Functions (now return Dict)
```python
# API Testing
json_data = generateFeatureFile(requirements)

# UI Testing
json_data = generateUIFeatureFile(requirements)
```

### Refinement Functions (now accept/return Dict)
```python
# API Testing
updated_json = refineFeatureFileWithFeedback(
    original_feature_json=json_data,
    verification_feedback="...",
    user_feedback="..."
)

# UI Testing
updated_json = refineUIFeatureFileWithFeedback(
    original_feature_json=json_data,
    verification_feedback="...",
    user_feedback="..."
)
```

### Verification Function (now accepts Dict)
```python
result = generateVerificationOutput(
    inputRequirement=requirements,
    featureJson=json_data
)
```

### Automation Script Generation (auto-converts JSON to Gherkin)
```python
# Automatically converts JSON to Gherkin internally
java_scripts = generateAutomationScriptsPerScenario(
    featureJson=json_data,
    userAdditionalInput="..."
)

# UI automation
ui_scripts = generateUIAutomationScriptsPerScenario(
    featureJson=json_data,
    userAdditionalInput="..."
)
```

## ✅ Benefits

### 1. **Surgical Edits**
Before:
```
Feedback: "Change scenario 3 name"
→ Regenerate entire file (50+ scenarios)
```

After:
```json
Feedback: "Change scenario 3 name"
→ Update only: scenarios[2].name = "New name"
```

### 2. **Better Version Control**
- JSON diffs are clear and precise
- Easy to see exactly what changed
- Can track changes at field level

### 3. **Programmatic Access**
```python
# Easy to query and manipulate
num_scenarios = len(json_data["scenarios"])
scenario_names = [s["name"] for s in json_data["scenarios"]]
add_tag_to_scenario(json_data, "scenario_1", "@critical")
```

### 4. **Validation**
```python
is_valid, errors = validate_gherkin_json(json_data)
if not is_valid:
    print(f"Issues found: {errors}")
```

### 5. **Format Independence**
- Generate Gherkin when needed
- Could also generate: HTML reports, Excel, Markdown, etc.
- Single source of truth

## 🔄 Migration Guide

If you have existing code using the old API:

### Old Code
```python
# Generation
feature_text = generateFeatureFile(requirements)

# Refinement
refined_text = refineFeatureFileWithFeedback(
    original_feature_file=feature_text,
    user_feedback="..."
)

# Verification
result = generateVerificationOutput(requirements, feature_text)

# Automation
scripts = generateAutomationScriptsPerScenario(
    featureFileScenarios=scenarios_list,
    userAdditionalInput="..."
)
```

### New Code
```python
# Generation (returns Dict)
feature_json = generateFeatureFile(requirements)

# Refinement (accepts/returns Dict)
refined_json = refineFeatureFileWithFeedback(
    original_feature_json=feature_json,
    user_feedback="..."
)

# Verification (accepts Dict)
result = generateVerificationOutput(requirements, refined_json)

# Convert to Gherkin when needed
from utils.gherkin_json_utils import json_to_gherkin
feature_text = json_to_gherkin(refined_json)

# Automation (accepts Dict, auto-converts internally)
scripts = generateAutomationScriptsPerScenario(
    featureJson=refined_json,
    userAdditionalInput="..."
)
```

## 📊 Workflow Examples

### Example 1: Generate → Verify → Refine
```python
# 1. Generate from requirements
feature_json = generateFeatureFile(requirements)

# 2. Verify against requirements
verification = generateVerificationOutput(requirements, feature_json)

# 3. If not perfect, refine
if verification != "PERFECT":
    refined_json = refineFeatureFileWithFeedback(
        original_feature_json=feature_json,
        verification_feedback=verification
    )
    feature_json = refined_json

# 4. Convert to Gherkin for automation
feature_text = json_to_gherkin(feature_json)
```

### Example 2: User Feedback Loop
```python
feature_json = generateFeatureFile(requirements)

# User provides feedback
user_feedback = "Remove scenario 5, add validation to scenario 2"

# Apply feedback surgically
updated_json = refineFeatureFileWithFeedback(
    original_feature_json=feature_json,
    user_feedback=user_feedback
)

# Generate automation scripts
scripts = generateAutomationScriptsPerScenario(updated_json)
```

## 🎨 Updated Prompts

All LLM prompts have been updated to:

### 1. `requirement_agent.py`
- Output: JSON structure (not Gherkin text)
- Includes JSON schema in prompt
- Example shows JSON output

### 2. `ui_requirement_agent.py`
- Output: JSON structure for UI testing
- UI-specific JSON structure
- Example shows JSON output

### 3. `feedback agents`
- Input: JSON structure
- Output: Updated JSON structure
- Surgical changes only

### 4. `verification_agent.py`
- Input: JSON structure
- Validates JSON correctness
- Checks scenario coverage

## 🚀 Future Enhancements

With JSON-based workflow, we can easily add:

1. **Scenario Templates Library**
   ```python
   library.add_template("login", scenario_json)
   feature_json["scenarios"].append(library.get_template("login"))
   ```

2. **Scenario Reordering**
   ```python
   scenarios = feature_json["scenarios"]
   scenarios[0], scenarios[1] = scenarios[1], scenarios[0]
   ```

3. **Bulk Operations**
   ```python
   # Add tag to all scenarios
   for scenario in feature_json["scenarios"]:
       scenario.setdefault("tags", []).append("@regression")
   ```

4. **Export to Multiple Formats**
   ```python
   gherkin_text = json_to_gherkin(feature_json)
   html_report = json_to_html(feature_json)
   excel_file = json_to_excel(feature_json)
   markdown_doc = json_to_markdown(feature_json)
   ```

5. **Scenario Analytics**
   ```python
   stats = analyze_feature_json(feature_json)
   print(f"Total scenarios: {stats['total']}")
   print(f"Positive: {stats['positive']}, Negative: {stats['negative']}")
   ```

## 📝 Summary

This refactoring fundamentally improves the maintainability, precision, and flexibility of the Gherkin generation workflow by:

- ✅ Enabling **surgical edits** instead of full regeneration
- ✅ Providing **structured data** for programmatic access
- ✅ Improving **version control** and change tracking
- ✅ Maintaining **backward compatibility** with automation scripts
- ✅ Opening possibilities for **future enhancements**

The JSON-based approach makes the system more robust, testable, and maintainable while preserving all existing functionality.
