# Quick Reference: Scenario ID Management

## 🎯 The Problem We Solved

When using JSON IR for surgical feedback, scenario additions/deletions would cause:
- ❌ Gaps in numbering: `scenario_1, scenario_3, scenario_5`
- ❌ Orphaned script methods referencing deleted scenarios
- ❌ Confusion and inconsistency between feature files and scripts

## ✅ The Solution

**Automatic Sequential Renumbering** + **Cross-File Validation** + **Smart Prompts**

---

## 🔧 Key Functions

### Feature File Operations

```python
from utils.gherkin_json_utils import renumber_scenario_ids, has_scenario_id_gaps

# Check for gaps
if has_scenario_id_gaps(feature_json):
    print("Gaps detected!")

# Renumber scenarios
updated_feature, id_mapping = renumber_scenario_ids(feature_json)
# id_mapping: {'scenario_3': 'scenario_2', 'scenario_4': 'scenario_3'}
```

### Script Synchronization

```python
from utils.java_json_utils import (
    update_script_scenario_references,
    validate_scenario_script_consistency
)

# Update script references after feature renumbering
updated_script = update_script_scenario_references(script_json, id_mapping)

# Validate consistency
is_valid, warnings = validate_scenario_script_consistency(feature_json, script_json)
```

---

## 💡 Usage in Agents

### RequirementAgent (Feature Files)

```python
# Automatically applied after modifications
if modifications:
    updated_feature = apply_feature_modifications(current_feature_json, modifications)
    
    # Auto-fix gaps
    if has_scenario_id_gaps(updated_feature):
        updated_feature, id_mapping = renumber_scenario_ids(updated_feature)
```

### AutomationScriptAgent (Scripts)

```python
# New helper methods
script_agent = AutomationScriptAgent()

# Validate
is_valid, warnings = script_agent.validate_with_feature(feature_json, script_json)

# Sync after feature changes
updated_script, warnings = script_agent.sync_script_with_feature(
    feature_json, 
    script_json, 
    id_mapping={'scenario_3': 'scenario_2'}
)
```

---

## 📋 Prompt Changes

### Feature File Prompts

**Added to `SYSTEM_INSTRUCTION_FEEDBACK_AGENT`:**
- Scenario ID Management rules
- Automatic renumbering after add/remove
- Examples with proper numbering

**Added to `SYSTEM_INSTRUCTION_CHAT_REFINEMENT_AGENT`:**
- Surgical modification patterns for add/remove with renumbering
- Explanation of why renumbering matters

### Script Prompts

**Added to `SYSTEM_INSTRUCTION_CHAT_SCRIPT_REFINEMENT_JSON`:**
- Scenario-Method Linkage section
- New action: `update_method_scenario_id`
- Examples for handling scenario changes

---

## 🧪 Common Scenarios

### Scenario 1: User Deletes a Scenario

```
User: "Remove scenario 2"

LLM Response:
{
  "intent": "change",
  "modifications": [
    {"op": "remove", "path": "scenarios/1"},
    {"op": "replace", "path": "scenarios/0/id", "value": "scenario_1"},
    {"op": "replace", "path": "scenarios/1/id", "value": "scenario_2"}
  ]
}

Agent: Applies modifications
Agent: Detects gaps (if any)
Agent: Auto-renumbers: {'scenario_3': 'scenario_2'}
```

### Scenario 2: User Adds a Scenario

```
User: "Add scenario for empty fields"

LLM Response:
{
  "intent": "change",
  "modifications": [
    {"op": "add", "path": "scenarios/-", "value": {...}},
    {"op": "replace", "path": "scenarios/2/id", "value": "scenario_3"}
  ]
}

Agent: Applies modifications
Result: Clean sequential IDs
```

### Scenario 3: Syncing Script After Feature Changes

```python
# Feature was modified, scenarios renumbered
feature_json, id_mapping = renumber_scenario_ids(feature_json)

# Update script to match
script_json = update_script_scenario_references(script_json, id_mapping)

# Validate
is_valid, warnings = validate_scenario_script_consistency(feature_json, script_json)
```

---

## ⚠️ Important Rules

1. **Always sequential**: `scenario_1, scenario_2, scenario_3` (no gaps)
2. **Auto-renumber after changes**: Agents handle this automatically
3. **Log ID mappings**: Changes are logged for debugging
4. **Validate consistency**: Check feature-script alignment
5. **Warn about orphans**: Detect methods referencing deleted scenarios

---

## 🎨 Best Practices

### When Modifying Features
```python
# Always check for gaps after modifications
if has_scenario_id_gaps(feature_json):
    feature_json, id_mapping = renumber_scenario_ids(feature_json)
    print(f"Renumbered: {id_mapping}")
```

### When Modifying Scripts
```python
# After feature changes, sync the script
if feature_was_modified and id_mapping:
    script_json = update_script_scenario_references(script_json, id_mapping)
```

### Before Saving
```python
# Validate consistency
is_valid, warnings = validate_scenario_script_consistency(feature_json, script_json)
if not is_valid:
    for warning in warnings:
        print(warning)
```

---

## 📖 Documentation

- **Full Guide**: `docs/SCENARIO_ID_MANAGEMENT.md`
- **Implementation Summary**: `docs/SCENARIO_ID_IMPROVEMENTS_SUMMARY.md`
- **This Quick Ref**: `docs/SCENARIO_ID_QUICK_REFERENCE.md`

---

## 🚀 Quick Test

```python
# Test the improvements
from agents.requirement_agent import RequirementAgent
from agents.automation_script_agent import AutomationScriptAgent

# Create agents
req_agent = RequirementAgent(llm)
script_agent = AutomationScriptAgent(llm)

# Test scenario deletion with auto-renumbering
intent, explanation, updated_feature = req_agent.chat_refine_api_feature_file(
    current_feature_json=feature_json,
    chat_messages=[],
    user_message="Delete scenario 2"
)

# Check if renumbering happened
print("Updated feature scenarios:")
for s in updated_feature.get("scenarios", []):
    print(f"  - {s['id']}: {s['name']}")

# Validate with script
is_valid, warnings = script_agent.validate_with_feature(updated_feature, script_json)
print(f"Valid: {is_valid}")
print(f"Warnings: {warnings}")
```

---

## 🎯 Key Takeaway

**The system now automatically maintains sequential scenario numbering and keeps feature files and scripts in sync, eliminating manual ID management and preventing orphaned references.**
