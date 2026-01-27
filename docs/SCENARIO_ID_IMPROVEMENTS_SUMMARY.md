# Scenario ID Management Improvements - Implementation Summary

## 📋 Changes Made

### ✅ 1. Updated LLM Prompts

#### Feature File Prompts (`llm_prompts/requirement_agent.py`)

**SYSTEM_INSTRUCTION_FEEDBACK_AGENT:**
- Added comprehensive **Scenario ID Management** section
- Enforces sequential numbering: `scenario_1, scenario_2, scenario_3` (no gaps)
- Automatic renumbering after add/remove operations
- Clear examples showing proper ID handling after deletions

**SYSTEM_INSTRUCTION_CHAT_REFINEMENT_AGENT:**
- Added **Scenario ID Management During Modifications** section
- Provides implementation patterns for add/remove operations with renumbering
- Explains why renumbering matters (script linkage, consistency)
- Updated critical rules to enforce renumbering

#### Script Prompts (`llm_prompts/java_json_script_prompts.py`)

**SYSTEM_INSTRUCTION_CHAT_SCRIPT_REFINEMENT_JSON:**
- Added new action: `update_method_scenario_id`
- Added **Scenario-Method Linkage** section explaining scenarioId relationships
- Provides examples for handling:
  - Scenario deletions → Remove associated methods
  - Scenario renumbering → Update scenarioId references
  - Scenario additions → Notify about needed generation
- Updated critical rules to include orphaned method detection

---

### ✅ 2. New Utility Functions

#### Gherkin JSON Utils (`utils/gherkin_json_utils.py`)

```python
def renumber_scenario_ids(feature_json: Dict) -> Tuple[Dict, Dict[str, str]]:
    """
    Renumber scenario IDs sequentially and return ID mapping.
    Returns: (updated_feature_json, {old_id: new_id})
    """

def has_scenario_id_gaps(feature_json: Dict) -> bool:
    """
    Check if scenario IDs have gaps (e.g., scenario_1, scenario_3, scenario_5).
    """
```

#### Java JSON Utils (`utils/java_json_utils.py`)

```python
def update_script_scenario_references(script_json: Dict, id_mapping: Dict) -> Dict:
    """
    Update all method scenarioId references based on ID mapping.
    Used when feature scenarios are renumbered.
    """

def find_orphaned_methods(script_json: Dict, valid_scenario_ids: List[str]) -> List[Dict]:
    """
    Find methods that reference non-existent scenarios.
    """

def validate_scenario_script_consistency(
    feature_json: Dict, 
    script_json: Dict
) -> Tuple[bool, List[str]]:
    """
    Comprehensive validation checking:
    - Orphaned methods (referencing deleted scenarios)
    - Missing implementations (scenarios without methods)
    - Scenario ID numbering gaps
    """
```

New modification action in `apply_json_modification`:
```python
elif action == "update_method_scenario_id":
    # Update scenarioId field in a method
```

---

### ✅ 3. Enhanced Agents

#### Requirement Agent (`agents/requirement_agent.py`)

**Updated imports:**
```python
from utils.gherkin_json_utils import (
    json_to_gherkin, 
    gherkin_to_json, 
    validate_gherkin_json, 
    apply_feature_modifications,
    renumber_scenario_ids,      # NEW
    has_scenario_id_gaps        # NEW
)
```

**Enhanced `chat_refine_api_feature_file()` and `chat_refine_ui_feature_file()`:**
- After applying modifications, automatically checks for ID gaps
- If gaps detected, auto-renumbers scenarios and logs the mapping
- Maintains clean, sequential scenario IDs

```python
if modifications:
    updated_feature = apply_feature_modifications(current_feature_json, modifications)
    
    # Auto-renumber scenario IDs if gaps are detected
    if has_scenario_id_gaps(updated_feature):
        print("🔄 Auto-renumbering scenario IDs to fix gaps...")
        updated_feature, id_mapping = renumber_scenario_ids(updated_feature)
        if id_mapping:
            print(f"   Renumbered scenarios: {id_mapping}")
```

#### Automation Script Agent (`agents/automation_script_agent.py`)

**Updated imports:**
```python
from utils.java_json_utils import (
    json_to_java, 
    java_to_json, 
    merge_script_jsons, 
    apply_json_modification,
    get_json_diff,
    validate_script_json,
    update_script_scenario_references,      # NEW
    find_orphaned_methods,                  # NEW
    validate_scenario_script_consistency    # NEW
)
```

**New methods:**
```python
def validate_with_feature(self, feature_json: Dict, script_json: Dict) -> Tuple[bool, List[str]]:
    """
    Validate script consistency with feature file.
    Returns (is_valid, warnings).
    """

def sync_script_with_feature(
    self, 
    feature_json: Dict, 
    script_json: Dict, 
    id_mapping: Optional[Dict[str, str]] = None
) -> Tuple[Dict, List[str]]:
    """
    Synchronize script with feature after scenario changes.
    Updates scenarioId references and validates consistency.
    """
```

---

## 🎯 How It Works

### Workflow: Adding a Scenario

1. **User adds scenario** via chat refinement
2. **LLM generates modification** with temporary ID
3. **LLM also generates renumbering operations** for all scenarios
4. **Agent applies modifications** 
5. **Agent detects gaps** using `has_scenario_id_gaps()`
6. **Agent auto-renumbers** using `renumber_scenario_ids()` if needed
7. **Returns** clean feature with sequential IDs

### Workflow: Deleting a Scenario

1. **User deletes scenario** (e.g., "Remove scenario 2")
2. **LLM generates remove operation** 
3. **LLM generates renumbering** for remaining scenarios
4. **Agent applies modifications**
5. **Agent auto-renumbers** to close gaps
6. **Returns** clean feature with sequential IDs

### Workflow: Syncing Script with Feature

```python
# After feature file changes
feature_json, id_mapping = renumber_scenario_ids(feature_json)

# Sync the script
script_json, warnings = script_agent.sync_script_with_feature(
    feature_json=feature_json,
    script_json=script_json,
    id_mapping=id_mapping
)

# Validate consistency
is_valid, warnings = script_agent.validate_with_feature(feature_json, script_json)
```

---

## 🚀 Benefits

### Before (Problems)
❌ Scenario deletions left gaps: `scenario_1, scenario_3, scenario_5`  
❌ Scripts had orphaned methods referencing deleted scenarios  
❌ New scenarios got confusing IDs: `scenario_7` when only 4 scenarios exist  
❌ No validation between feature and script consistency  
❌ Manual ID management required

### After (Solutions)
✅ Always sequential IDs: `scenario_1, scenario_2, scenario_3`  
✅ Automatic gap detection and renumbering  
✅ Script methods stay in sync with feature scenarios  
✅ Warnings about orphaned methods and missing implementations  
✅ Fully automated ID management  
✅ Clear audit trail of ID changes (mapping logged)

---

## 📝 Usage Examples

### Example 1: Feature File Refinement with Auto-Renumbering

```python
agent = RequirementAgent(llm)

# User deletes scenario 2
intent, explanation, updated_feature = agent.chat_refine_api_feature_file(
    current_feature_json=current_feature,
    chat_messages=[],
    user_message="Remove scenario 2"
)

# Console output:
# 🔄 Auto-renumbering scenario IDs to fix gaps...
#    Renumbered scenarios: {'scenario_3': 'scenario_2', 'scenario_4': 'scenario_3'}
```

### Example 2: Script Synchronization

```python
script_agent = AutomationScriptAgent(llm)

# After feature scenarios are renumbered
id_mapping = {'scenario_3': 'scenario_2', 'scenario_4': 'scenario_3'}

# Sync the script
updated_script, warnings = script_agent.sync_script_with_feature(
    feature_json=feature_json,
    script_json=script_json,
    id_mapping=id_mapping
)

# Console output:
# 🔄 Updated script scenario references: {'scenario_3': 'scenario_2', 'scenario_4': 'scenario_3'}
```

### Example 3: Validation

```python
is_valid, warnings = script_agent.validate_with_feature(feature_json, script_json)

if not is_valid:
    for warning in warnings:
        print(warning)

# Example warnings:
# ⚠️ Method 'validateDevice' (id: method_2) references deleted scenario 'scenario_2'
# ℹ️ Scenario 'scenario_3' (Check error handling) has no corresponding methods in the script
```

---

## 🧪 Testing Recommendations

### Test Cases to Verify

1. **Scenario Addition**
   - Add scenario to empty feature → should get `scenario_1`
   - Add scenario to end → should get next sequential ID
   - Add scenario in middle → all scenarios should renumber

2. **Scenario Deletion**
   - Delete first scenario → remaining renumber starting from 1
   - Delete middle scenario → gaps closed, sequential numbering restored
   - Delete last scenario → no renumbering needed

3. **Script Synchronization**
   - Renumber scenarios → script methods update scenarioId
   - Delete scenario → orphaned methods detected
   - Add scenario → missing implementation detected

4. **Edge Cases**
   - Delete all scenarios → empty scenarios array, no errors
   - Add multiple scenarios → all get sequential IDs
   - Reorder scenarios → IDs stay with their scenarios

---

## 📚 Documentation

Created comprehensive documentation in:
- **`docs/SCENARIO_ID_MANAGEMENT.md`**: Full architectural overview, rationale, and implementation plan

---

## 🔄 Next Steps (Optional Enhancements)

1. **Automatic script regeneration**: When scenarios are added, offer to generate methods
2. **Orphaned method cleanup**: Automatic removal of methods for deleted scenarios
3. **Scenario reordering**: Handle explicit reordering operations
4. **Stable semantic IDs**: Consider using semantic IDs (e.g., `scenario_valid_login`) instead of numbers
5. **Undo/redo support**: Keep history of ID mappings for reverting changes

---

## ✨ Summary

The JSON IR approach now properly handles scenario numbering through:
1. **Enhanced LLM prompts** that enforce sequential numbering rules
2. **Automatic gap detection** and renumbering in agents
3. **Cross-file consistency** validation and synchronization
4. **Clear warnings** about orphaned or missing implementations
5. **Audit trail** of ID changes via mapping logs

The system is now much more robust and "surgical" in its modifications, maintaining clean state even as scenarios are added, removed, or reordered.
