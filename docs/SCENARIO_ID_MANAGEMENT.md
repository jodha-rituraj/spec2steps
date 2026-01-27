# Scenario ID Management & Surgical Feedback Improvements

## 📋 Current Problem

When using the JSON IR approach for surgical feedback, the system struggles with:

1. **Scenario Numbering Issues**: When scenarios are added, deleted, or reordered, the numbering gets inconsistent
2. **Method-Scenario Linkage**: Methods in scripts have `scenarioId` fields that become stale when scenarios change
3. **No Automatic Renumbering**: The system doesn't intelligently renumber scenario IDs after modifications
4. **Cross-File Consistency**: Feature files and scripts can become out of sync when scenarios are modified

### Example Problem Scenario

**Initial Feature File:**
```json
{
  "scenarios": [
    {"id": "scenario_1", "name": "Valid login", ...},
    {"id": "scenario_2", "name": "Invalid password", ...},
    {"id": "scenario_3", "name": "Missing credentials", ...}
  ]
}
```

**User deletes scenario_2:**
```json
{
  "scenarios": [
    {"id": "scenario_1", "name": "Valid login", ...},
    {"id": "scenario_3", "name": "Missing credentials", ...}  // ❌ Still has ID 3
  ]
}
```

**Problems:**
- ❌ Gap in numbering (scenario_1, scenario_3)
- ❌ Script methods still reference scenario_2
- ❌ New scenarios get scenario_4, making the gap worse
- ❌ No automatic cleanup of orphaned methods in scripts

---

## 🎯 Proposed Solution

### 1. **Stable Scenario IDs with Semantic Meaning**

Instead of sequential numbering, use **stable identifiers** that survive reordering:

```json
{
  "scenarios": [
    {
      "id": "scenario_valid_login",           // ✅ Semantic, stable ID
      "displayOrder": 1,                       // ✅ Explicit ordering
      "name": "Valid login",
      ...
    },
    {
      "id": "scenario_invalid_password",
      "displayOrder": 2,
      "name": "Invalid password",
      ...
    }
  ]
}
```

**Benefits:**
- ✅ IDs don't change when scenarios are reordered
- ✅ Clear semantic meaning
- ✅ Easy to track across feature files and scripts
- ✅ displayOrder can be renumbered without changing IDs

### 2. **Automatic Renumbering on Modifications**

Add utility functions to handle ID management:

```python
def renumber_scenario_ids(feature_json: Dict) -> Dict:
    """
    Renumber scenario IDs to be sequential (scenario_1, scenario_2, ...).
    Useful after deletions or when LLM generates inconsistent IDs.
    
    Also updates:
    - displayOrder fields if present
    - Returns mapping of old_id -> new_id for script updates
    """
    
def update_script_scenario_references(script_json: Dict, id_mapping: Dict) -> Dict:
    """
    Update all method scenarioId references in a script JSON
    based on the provided ID mapping.
    """
    
def validate_scenario_script_consistency(feature_json: Dict, script_json: Dict) -> List[str]:
    """
    Check that all scenarioIds in script methods reference valid scenarios.
    Returns list of warnings/errors.
    """
```

### 3. **Enhanced LLM Prompts for Scenario Management**

#### For Feature File Feedback Agent:

```python
SYSTEM_INSTRUCTION_FEEDBACK_AGENT = """
...

### 🔹 Scenario ID Management (CRITICAL)

When modifying scenarios:
1. **Adding scenarios**: Use the next sequential ID (scenario_N where N = len(scenarios) + 1)
2. **Removing scenarios**: Also remove that scenario from the array
3. **After any add/remove operation**: Renumber ALL scenario IDs sequentially starting from scenario_1
4. **Never leave gaps**: scenario_1, scenario_2, scenario_3 (NOT scenario_1, scenario_3, scenario_5)

Example:
Original: [scenario_1, scenario_2, scenario_3]
User: "Remove scenario 2"
Correct Output: [
  {"id": "scenario_1", ...},  // unchanged
  {"id": "scenario_2", ...}   // was scenario_3, renumbered
]

### 🔹 Renumbering Rules
- After deletion: Renumber remaining scenarios sequentially
- After insertion: Renumber all scenarios from insertion point
- After reordering: Renumber to match new order
- ALWAYS ensure IDs are sequential: scenario_1, scenario_2, scenario_3, ...

"""
```

#### For Script Refinement Agent:

```python
SYSTEM_INSTRUCTION_CHAT_SCRIPT_REFINEMENT_JSON = """
...

### 🔹 Scenario-Method Linkage

Each method in the script has a `scenarioId` field that links it to a scenario in the feature file.

When the user mentions changes to scenarios:
1. Check if scenario IDs have changed in the feature file
2. Update `scenarioId` references in methods accordingly
3. Add actions to remove methods for deleted scenarios
4. Suggest generating new methods for added scenarios

Available actions for scenario management:
- update_method_scenario_id: {"action": "update_method_scenario_id", "method_id": "...", "new_scenario_id": "scenario_2"}
- remove_orphaned_methods: {"action": "remove_orphaned_methods", "valid_scenario_ids": ["scenario_1", "scenario_2"]}

Example:
User: "I deleted scenario 2 from the feature file"
Response:
{
  "intent": "change",
  "explanation": "I'll remove the methods associated with the deleted scenario.",
  "modifications": [
    {"action": "remove_method", "method_id": "method_2"},
    {"action": "remove_method", "method_id": "method_3"}
  ]
}

"""
```

### 4. **Workflow for Cross-File Consistency**

When scenarios change in the feature file:

```python
def sync_script_with_feature(feature_json: Dict, script_json: Dict) -> Tuple[Dict, List[str]]:
    """
    Synchronize script with feature file after scenario changes.
    
    Returns:
        - Updated script_json with corrected scenarioIds
        - List of warnings about orphaned methods or missing implementations
    """
    warnings = []
    
    # Get valid scenario IDs from feature
    valid_scenario_ids = {s["id"] for s in feature_json.get("scenarios", [])}
    
    # Find methods with invalid scenarioIds
    orphaned_methods = []
    for method in script_json.get("methods", []):
        scenario_id = method.get("scenarioId")
        if scenario_id and scenario_id not in valid_scenario_ids:
            orphaned_methods.append(method)
            warnings.append(f"Method {method['name']} references deleted scenario {scenario_id}")
    
    # Find scenarios without implementations
    implemented_scenarios = {m.get("scenarioId") for m in script_json.get("methods", []) if m.get("scenarioId")}
    missing_implementations = valid_scenario_ids - implemented_scenarios
    for scenario_id in missing_implementations:
        warnings.append(f"Scenario {scenario_id} has no corresponding methods in the script")
    
    return script_json, warnings
```

---

## 🔄 Comparison with Market Research Agent Approach

### What We Can Learn

Based on the iterative agent approach from the market-research-agent:

1. **Stable Question IDs**: They likely use stable IDs that don't change during modifications
2. **Explicit Ordering**: Separate ordering from identity
3. **Validation Functions**: Check consistency before and after modifications
4. **Clear Modification Operations**: Well-defined operations for add/remove/reorder

### Adaptation to Our Use Case

```python
# Instead of simple scenario_1, scenario_2...
# Use semantic IDs with explicit ordering

class ScenarioManager:
    """Manages scenario IDs and ordering across feature files."""
    
    @staticmethod
    def generate_stable_id(scenario_name: str, existing_ids: Set[str]) -> str:
        """Generate a unique, stable ID based on scenario name."""
        base_id = re.sub(r'[^a-z0-9_]', '_', scenario_name.lower())
        base_id = f"scenario_{base_id}"
        
        if base_id not in existing_ids:
            return base_id
        
        # Add counter if needed
        counter = 2
        while f"{base_id}_{counter}" in existing_ids:
            counter += 1
        return f"{base_id}_{counter}"
    
    @staticmethod
    def renumber_display_order(scenarios: List[Dict]) -> List[Dict]:
        """Ensure scenarios have sequential displayOrder."""
        for i, scenario in enumerate(scenarios, 1):
            scenario["displayOrder"] = i
        return scenarios
    
    @staticmethod
    def reorder_scenarios(scenarios: List[Dict], new_order: List[int]) -> List[Dict]:
        """Reorder scenarios and update displayOrder."""
        reordered = [scenarios[i] for i in new_order]
        return ScenarioManager.renumber_display_order(reordered)
```

---

## 📝 Implementation Plan

### Phase 1: Add Utility Functions ✅
- [ ] Add `renumber_scenario_ids()` to `gherkin_json_utils.py`
- [ ] Add `update_script_scenario_references()` to `java_json_utils.py`
- [ ] Add `validate_scenario_script_consistency()` to utils
- [ ] Add new modification action: `update_method_scenario_id`

### Phase 2: Update LLM Prompts ✅
- [ ] Enhance `SYSTEM_INSTRUCTION_FEEDBACK_AGENT` with ID management rules
- [ ] Enhance `SYSTEM_INSTRUCTION_CHAT_REFINEMENT_AGENT` with ID management rules
- [ ] Add scenario management section to `SYSTEM_INSTRUCTION_CHAT_SCRIPT_REFINEMENT_JSON`
- [ ] Update examples to show proper ID handling

### Phase 3: Update Agents ✅
- [ ] Modify `RequirementAgent.chat_refine_api_feature_file()` to auto-renumber after changes
- [ ] Modify `AutomationScriptAgent.chat_refine_script_json()` to handle scenario sync
- [ ] Add validation calls before returning results

### Phase 4: Testing ✅
- [ ] Test scenario addition with proper numbering
- [ ] Test scenario deletion with renumbering
- [ ] Test scenario reordering
- [ ] Test cross-file consistency validation
- [ ] Test script method synchronization

---

## 🎓 Key Principles

1. **Single Source of Truth**: Feature file scenario IDs are authoritative
2. **Automatic Consistency**: Scripts automatically sync with feature changes
3. **No Manual ID Management**: System handles all ID operations
4. **Clear Warnings**: Users informed about orphaned methods or missing implementations
5. **Reversible Operations**: Keep ID mapping history for undo operations

---

## 🚀 Quick Wins

**Immediate improvements without major refactoring:**

1. **Add renumbering to feedback agent**: After any modification, auto-renumber scenario IDs
2. **Validate on return**: Check for gaps in scenario IDs before returning
3. **Warn about orphaned methods**: Detect when script methods reference deleted scenarios
4. **Better prompts**: Add explicit ID management instructions to LLM prompts

---

## 📚 References

- JSON Pointer (RFC 6901) for path-based modifications
- JSON Patch (RFC 6902) for structured change operations
- Diffing algorithms for detecting structural changes
