import streamlit as st
import os
import sys
from dotenv import load_dotenv

# ----------------------------
# Early Configuration Setup
# ----------------------------

# Load .env file first
load_dotenv()

# Set environment variable if needed (before importing utils)
if "GROQ_API_KEY" not in os.environ:
    os.environ["GROQ_API_KEY"] = ""  # Set empty to allow lazy loading

# Now import utils after setting environment
from utils.utils import *

# ----------------------------
# Streamlit UI
# ----------------------------

st.set_page_config(page_title="End to End AI-Assisted Test Cases & Script Generator", layout="wide")

st.title("End to End AI-Assisted Test Cases & Script Generator")

# ----------------------------
# Sidebar for API Key Configuration
# ----------------------------
with st.sidebar:
    st.header("⚙️ Configuration")
    
    api_key_input = st.text_input(
        "GROQ API Key (Optional)",
        type="password",
        help="Enter your GROQ API key. If not provided, will use key from .env file.",
        placeholder="gsk_..."
    )
    
    # Privacy and Key Information
    st.info("""
    🔒 **Privacy & Security**
    
    - We **don't store or log** any keys, conversations, or prompts
    - All processing happens in your browser session
    
    📝 **Don't have a GROQ API Key?**
    
    Visit [Groq Console](https://console.groq.com/keys) to create a free key with limited quota
    
    🔐 **Privacy Policy**
    
    For Groq APIs privacy details, refer to [Groq Privacy Policy](https://groq.com/privacy-policy)
    """)
    
    # Handle API key initialization
    if api_key_input:
        api_key_input = api_key_input.strip()
        if api_key_input:
            st.success("✅ Using provided API key")
            # Set the API key in environment for this session
            os.environ["GROQ_API_KEY"] = api_key_input
            # Reinitialize LLM with new API key
            from utils.llm_config import get_llm
            import utils.utils
            try:
                new_llm = get_llm(api_key_input)
                # Update the llm variable in utils module
                utils.utils.llm = new_llm
                st.session_state.api_key_valid = True
            except Exception as e:
                st.error(f"❌ Invalid API key: {str(e)}")
                st.session_state.api_key_valid = False
        else:
            st.warning("⚠️ No API key configured")
            st.session_state.api_key_valid = False
    elif os.getenv("GROQ_API_KEY", "").strip():
        st.info("ℹ️ Using API key from .env file")
        # Initialize LLM with .env API key if not already initialized
        from utils.llm_config import get_llm
        import utils.utils
        try:
            if utils.utils.llm is None:
                env_key = os.getenv("GROQ_API_KEY")
                utils.utils.llm = get_llm(env_key)
            st.session_state.api_key_valid = True
        except Exception as e:
            st.error(f"❌ Error loading API key from .env: {str(e)}")
            st.session_state.api_key_valid = False
    else:
        st.warning("⚠️ No API key configured")
        st.session_state.api_key_valid = False
    
    # Version information at bottom of sidebar
    st.divider()
    st.caption("🔧 **Version 1.0.0** | Jan 2026")

# Initialize session state variables
if 'feature_files' not in st.session_state:
    st.session_state.feature_files = []  # List to store all versions
if 'verification_outputs' not in st.session_state:
    st.session_state.verification_outputs = []  # List to store all versions
if 'input_requirement' not in st.session_state:
    st.session_state.input_requirement = ""
if 'show_feedback_section' not in st.session_state:
    st.session_state.show_feedback_section = False
if 'show_final_edit_section' not in st.session_state:
    st.session_state.show_final_edit_section = False
if 'show_scripts_section' not in st.session_state:
    st.session_state.show_scripts_section = False
if 'java_files' not in st.session_state:
    st.session_state.java_files = []
if 'merged_java_file' not in st.session_state:
    st.session_state.merged_java_file = None
if 'final_feature_file' not in st.session_state:
    st.session_state.final_feature_file = None
if 'user_script_input' not in st.session_state:
    st.session_state.user_script_input = ""
if 'show_script_feedback_section' not in st.session_state:
    st.session_state.show_script_feedback_section = False
if 'script_diff_outputs' not in st.session_state:
    st.session_state.script_diff_outputs = []  # Store diff outputs for each script
if 'feedback_counter' not in st.session_state:
    st.session_state.feedback_counter = 0  # Counter to reset feedback input
if 'refactoring_intents' not in st.session_state:
    st.session_state.refactoring_intents = []  # Store intent for each refactoring iteration
if 'merged_java_history' not in st.session_state:
    st.session_state.merged_java_history = []  # Store history of merged Java files for undo
if 'test_type' not in st.session_state:
    st.session_state.test_type = "API"  # Default to API testing

# Test Type Selection
st.subheader("🎯 Select Test Type")
test_type = st.radio(
    "Choose the type of test automation:",
    options=["API", "UI"],
    index=0 if st.session_state.test_type == "API" else 1,
    horizontal=True,
    help="API: REST API testing with RestAssured | UI: Web UI testing with Selenium WebDriver"
)
st.session_state.test_type = test_type

# Show appropriate info based on selection
if test_type == "API":
    st.info("📡 **API Testing Mode**: Will generate feature files for REST API testing using RestAssured, Cucumber, and TestNG")
else:
    st.info("🌐 **UI Testing Mode**: Will generate feature files for Web UI testing using Selenium WebDriver, Cucumber, and TestNG")

# st.divider()

inputRequirement = st.text_area(
    "Enter Requirements File/Text/User Input",
    value=st.session_state.input_requirement,
    height=150,
    placeholder="Paste raw requirements here..."
)

st.warning("⚠️ **Disclaimer**: AI can make mistakes. Please validate and review all generated outputs before use.")

generateBtn = st.button("Generate Feature File & Verification")

# Stage 1: Generate Feature File and Verification Output
if generateBtn:
    # Check if API key is valid
    if not st.session_state.get('api_key_valid', False):
        st.error("❌ Please configure a valid GROQ API key in the sidebar before generating!")
        st.stop()
    
    if not inputRequirement.strip():
        st.warning("Please enter some text before generating.")
    else:
        # Check if LLM is initialized
        import utils.utils
        if utils.utils.llm is None:
            st.error("❌ LLM not initialized. Please provide a GROQ API key in the sidebar.")
            st.stop()
        
        # Always reset everything for fresh start when Generate button is clicked
        st.session_state.feature_files = []
        st.session_state.verification_outputs = []
        st.session_state.show_feedback_section = False
        st.session_state.show_final_edit_section = False
        st.session_state.show_scripts_section = False
        st.session_state.java_files = []
        st.session_state.merged_java_file = None
        st.session_state.final_feature_file = None
        st.session_state.user_script_input = ""
        st.session_state.show_script_feedback_section = False
        st.session_state.script_diff_outputs = []
        st.session_state.feedback_counter = 0
        st.session_state.refactoring_intents = []
        st.session_state.merged_java_history = []
        
        st.session_state.input_requirement = inputRequirement
        
        # Generate based on test type
        if st.session_state.test_type == "API":
            with st.spinner("Generating API Feature File ..."):
                feature_file = generateFeatureFile(inputRequirement)
                st.session_state.feature_files.append(feature_file)
        else:  # UI
            with st.spinner("Generating UI Feature File ..."):
                feature_file = generateUIFeatureFile(inputRequirement)
                st.session_state.feature_files.append(feature_file)
        
        with st.spinner("Generating Verification Agent Output ..."):
            verification_output = generateVerificationOutput(
                feature_file, 
                inputRequirement
            )
            st.session_state.verification_outputs.append(verification_output)
        
        st.session_state.show_feedback_section = False
        st.session_state.show_final_edit_section = False
        st.session_state.show_scripts_section = False
        st.rerun()

# Always show ALL Feature Files and Verification Outputs if they exist
if st.session_state.feature_files and st.session_state.verification_outputs:
    
    # Display all versions
    for idx, (feature_file, verification_output) in enumerate(zip(st.session_state.feature_files, st.session_state.verification_outputs), 1):
        st.divider()
        
        # Show version number
        if len(st.session_state.feature_files) > 1:
            st.info(f"🔄 Version {idx}")
        
        st.subheader(f"📋 Generated Feature File {f'(Version {idx})' if len(st.session_state.feature_files) > 1 else ''}")
        st.code(feature_file, language="gherkin")
        
        st.divider()
        st.subheader(f"✅ Verification Agent Output {f'(Version {idx})' if len(st.session_state.verification_outputs) > 1 else ''}")
        st.text(verification_output)
    
    # Only show feedback buttons if neither final edit nor scripts section is shown
    if not st.session_state.show_scripts_section and not st.session_state.show_final_edit_section:
        st.divider()
        st.subheader("🔄 Provide Feedback")
        
        col1, col2 = st.columns(2)
        
        with col1:
            reject_btn = st.button("❌ Reject - Regenerate Feature File", use_container_width=True)
        
        with col2:
            accept_btn = st.button("✅ Accept - Proceed to Final Review", use_container_width=True)
        
        # If user rejects (wants to regenerate)
        if reject_btn:
            st.session_state.show_feedback_section = True
            st.rerun()
        
        # If user accepts (proceed to final edit/review)
        if accept_btn:
            st.session_state.show_final_edit_section = True
            st.session_state.show_feedback_section = False
            st.rerun()

# Show Feedback Section if user clicked Reject
if st.session_state.show_feedback_section and not st.session_state.show_scripts_section:
    st.divider()
    st.subheader("📝 Customize Feedback for Regeneration")
    
    current_version = len(st.session_state.feature_files)
    
    st.info("💡 **Tip**: Review the verification output below. You can edit/remove any points you don't want to address, and add your own custom feedback at the end.")
    
    # Combine verification output with space for user feedback
    combined_feedback_template = f"""VERIFICATION OUTPUT:
{st.session_state.verification_outputs[-1]}

────────────────────────────────────────────────────
USER FEEDBACK (Optional - Add your custom feedback below):
────────────────────────────────────────────────────

"""
    
    combined_feedback = st.text_area(
        "Combined Feedback:",
        value=combined_feedback_template,
        height=350,
        key=f"combined_feedback_{current_version}",
        help="Verification output is shown first. Edit it if needed, then add your custom feedback below the separator line."
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        regenerate_btn = st.button("🔄 Regenerate Feature File", use_container_width=True)
    
    with col2:
        skip_feedback_btn = st.button("⏭️ Skip & Proceed to Scripts", use_container_width=True)
    
    if regenerate_btn:
        with st.spinner("Refining Feature File based on feedback..."):
            # Get the latest feature file
            latest_feature_file = st.session_state.feature_files[-1]
            
            # Use the refinement function based on test type
            if st.session_state.test_type == "API":
                refined_feature_file = refineFeatureFileWithFeedback(
                    original_feature_file = latest_feature_file,
                    verification_feedback = combined_feedback,
                    user_feedback = ""
                )
            else:  # UI
                refined_feature_file = refineUIFeatureFileWithFeedback(
                    original_feature_file = latest_feature_file,
                    verification_feedback = combined_feedback,
                    user_feedback = ""
                )
            
            # Append the refined version to history
            st.session_state.feature_files.append(refined_feature_file)
            
            # Generate new verification output for the refined file
            new_verification = generateVerificationOutput(
                refined_feature_file,
                st.session_state.input_requirement
            )
            st.session_state.verification_outputs.append(new_verification)
            
            st.session_state.show_feedback_section = False
        
        st.rerun()
    
    if skip_feedback_btn:
        st.session_state.show_final_edit_section = True
        st.session_state.show_feedback_section = False
        st.rerun()

# Show Final Edit Section before script generation
if st.session_state.show_final_edit_section and not st.session_state.show_scripts_section:
    st.divider()
    st.subheader("📝 Final Review & Edit (Optional)")
    
    st.info("💡 **Last chance to edit!** You can manually modify the feature file below, or proceed directly to script generation.")
    
    # Get the latest feature file
    latest_feature_file = st.session_state.feature_files[-1]
    
    # Editable feature file
    edited_feature_file = st.text_area(
        "Edit Feature File (optional):",
        value=latest_feature_file,
        height=400,
        key="final_edit_feature_file",
        help="Make any final manual edits to the feature file before generating scripts"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        save_and_proceed_btn = st.button("💾 Save Edits & Generate Scripts", use_container_width=True)
    
    with col2:
        proceed_without_edit_btn = st.button("⏭️ Skip Edit & Generate Scripts", use_container_width=True)
    
    if save_and_proceed_btn:
        # Save the edited version as a new version
        if edited_feature_file != latest_feature_file:
            st.session_state.feature_files.append(edited_feature_file)
            st.session_state.verification_outputs.append("(Manually edited by user)")
            st.success("✅ Edits saved!")
        
        st.session_state.show_scripts_section = True
        st.session_state.show_final_edit_section = False
        st.rerun()
    
    if proceed_without_edit_btn:
        st.session_state.show_scripts_section = True
        st.session_state.show_final_edit_section = False
        st.rerun()

# Show Scripts Section if user accepted
if st.session_state.show_scripts_section:
    st.divider()
    st.subheader("🤖 Automation Scripts Generation")
    
    # Use the LATEST feature file for script generation
    latest_feature_file = st.session_state.feature_files[-1]
    
    # Only generate if not already generated
    if not st.session_state.java_files:
        # Add user input section BEFORE generating scripts
        st.info("💡 **Optional**: Provide additional context to help generate better automation scripts")
        
        # Different placeholder text based on test type
        if st.session_state.test_type == "API":
            placeholder_text = ("Provide details like:\n"
                               "- API endpoint patterns or naming conventions\n"
                               "- Custom data models or utility classes to use\n"
                               "- Specific validation rules or assertions needed\n"
                               "- Custom headers, authentication methods, or payload structures\n"
                               "- Performance or timeout requirements\n"
                               "- Mock data patterns or test data details\n"
                               "- Special handling for specific fields or response formats\n"
                               "- Business logic constraints or domain-specific rules")
        else:  # UI
            placeholder_text = ("Provide details like:\n"
                               "- Page URL patterns or routing conventions\n"
                               "- Custom Page Object classes or locator strategies\n"
                               "- Specific element selectors (CSS, XPath, ID patterns)\n"
                               "- Custom wait strategies or timeout requirements\n"
                               "- Browser configuration or driver setup details\n"
                               "- Screenshot capture requirements\n"
                               "- Custom assertion libraries or validation patterns\n"
                               "- JavaScript execution requirements\n"
                               "- Special handling for dynamic elements, iframes, or modals\n"
                               "- Data-driven test data patterns")
        
        user_additional_input = st.text_area(
            "Additional Context for Script Generation (Optional):",
            value=st.session_state.user_script_input,
            height=150,
            placeholder=placeholder_text,
            key="user_script_additional_input"
        )
        
        generate_scripts_btn = st.button("✨ Generate Automation Scripts", use_container_width=True, type="primary")
        
        if generate_scripts_btn:
            st.session_state.user_script_input = user_additional_input
            
            with st.spinner("Parsing Feature File Scenarios..."):
                parser = GherkinScenarioParser()
                featureFileScenarios = parser.parse(latest_feature_file)
                st.success(f"Found {len(featureFileScenarios)} scenario(s)")
            
            # Generate scripts based on test type
            if st.session_state.test_type == "API":
                with st.spinner("Generating API Automation Scripts for each scenario..."):
                    st.session_state.java_files = generateAutomationScriptsPerScenario(
                        featureFileScenarios, 
                        userAdditionalInput=user_additional_input
                    )
                    st.success(f"Generated {len(st.session_state.java_files)} Java file(s)")
            else:  # UI
                with st.spinner("Generating UI Automation Scripts for each scenario..."):
                    st.session_state.java_files = generateUIAutomationScriptsPerScenario(
                        featureFileScenarios, 
                        userAdditionalInput=user_additional_input
                    )
                    st.success(f"Generated {len(st.session_state.java_files)} Java file(s)")
            
            st.rerun()
    
    # Display generated scripts if they exist
    if st.session_state.java_files:
        # Display individual Java files
        st.divider()
        st.subheader("📄 Individual Generated Scripts")
        for i, java_code in enumerate(st.session_state.java_files, 1):
            with st.expander(f"Scenario {i} - Java Code"):
                st.code(java_code, language="java")
        
        # Merge Java files first
        st.divider()
        st.subheader("🔗 Merged Java File")
        st.info("💡 This is the final merged output combining all individual scripts into a single class.")
        
        # Only merge if not already merged
        if not st.session_state.merged_java_file:
            with st.spinner("Merging all Java files into single class..."):
                merger = JavaFileMerger(merged_class_name="GeneratedTests")
                st.session_state.merged_java_file = merger.merge(st.session_state.java_files)
        
        st.code(st.session_state.merged_java_file, language="java")
        
        # Add feedback section for merged script
        if not st.session_state.show_script_feedback_section:
            st.divider()
            st.subheader("💭 Need to modify the merged script?")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📝 Provide Feedback to Refactor Merged Script", use_container_width=True):
                    st.session_state.show_script_feedback_section = True
                    st.rerun()
            with col2:
                if st.button("✅ Accept & Download", use_container_width=True, type="primary"):
                    # Skip feedback and allow download
                    st.session_state.show_script_feedback_section = False
                    st.rerun()
        
        # Show script feedback section for MERGED file
        if st.session_state.show_script_feedback_section:
            st.divider()
            st.subheader("🔧 Refactor Merged Script with Feedback")
            
            # Add helpful guidelines
            st.info("""
            💡 **Feedback Guidelines for Best Results:**
            
            ✅ **Simple & Specific feedback works best:**
            - "Change class name from X to Y"
            - "Rename method ABC to XYZ"  
            - "Add null check for parameter X"
            - "Remove unused variable/import"
            - "Update logger reference"
            - "Add error handling to method X"
            - "Change snake_case to camelCase" ⭐ NEW!
            - "Convert camelCase to snake_case" ⭐ NEW!
            
            ❌ **Avoid complex requests:**
            - "Completely restructure the code"
            - "Apply all best practices"
            - "Make it production-ready"
            
            💡 **Tip**: For complex changes, edit the code directly or download and modify it manually.
            """)
            
            # Show the current merged script in expander
            with st.expander("📄 Current Merged Script (click to expand)", expanded=False):
                st.code(st.session_state.merged_java_file, language="java")
            
            # Feedback input
            script_feedback = st.text_area(
                "Provide your feedback/modification requests for the merged script:",
                height=150,
                placeholder="Example:\n"
                           "- Add null checks for parameters\n"
                           "- Change method names to be more descriptive\n"
                           "- Add error handling for network failures\n"
                           "- Update assertions to include custom messages\n"
                           "- Remove unnecessary code\n"
                           "- Improve code organization...",
                key=f"merged_script_feedback_input_{st.session_state.feedback_counter}"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                refactor_btn = st.button("🔄 Refactor Merged Script", use_container_width=True, type="primary")
            
            with col2:
                done_btn = st.button("✅ Done with Changes", use_container_width=True)
            
            # Add Undo button if there's history
            if st.session_state.merged_java_history:
                st.divider()
                col_undo1, col_undo2 = st.columns([3, 1])
                with col_undo1:
                    st.info(f"💡 **Undo Available**: You can revert to the previous version ({len(st.session_state.merged_java_history)} version(s) in history)")
                with col_undo2:
                    undo_btn = st.button("↩️ Undo Last Change", use_container_width=True, type="secondary")
                
                if undo_btn:
                    # Restore previous version
                    previous_version = st.session_state.merged_java_history.pop()
                    st.session_state.merged_java_file = previous_version
                    
                    # Also remove last diff and intent
                    if st.session_state.script_diff_outputs:
                        st.session_state.script_diff_outputs.pop()
                    if st.session_state.refactoring_intents:
                        st.session_state.refactoring_intents.pop()
                    
                    st.success("↩️ Successfully reverted to previous version!")
                    st.rerun()
            
            if refactor_btn and script_feedback.strip():
                # Step 1: Extract and show intent
                with st.spinner("🤔 Understanding your request..."):
                    from utils.utils import extract_refactoring_intent
                    
                    # Extract intent
                    intent = extract_refactoring_intent(
                        script_feedback,
                        st.session_state.merged_java_file
                    )
                
                # Display the extracted intent
                st.divider()
                st.subheader("🎯 Understanding Your Request")
                
                intent_type = intent.get("type", "unknown")
                
                # Determine if using pattern or fallback
                known_patterns = [
                    "rename_class", "rename_method", "rename_variable",
                    "remove_code", "add_import", "remove_import",
                    "snake_to_camel", "camel_to_snake", "update_string"
                ]
                
                if intent_type in known_patterns:
                    approach = "✅ **Pattern-Based Refactoring** (Fast, Clean Diffs)"
                    reliability = "🎯 High Reliability"
                elif intent_type == "complex":
                    approach = "🔄 **LLM-Based Refactoring** (May have formatting changes)"
                    reliability = "⚠️ Moderate Reliability"
                else:
                    approach = "🔄 **LLM Fallback** (Unknown pattern detected)"
                    reliability = "⚠️ Best Effort"
                
                # Create intent display
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.info(f"""
                    **Detected Intent**: `{intent_type}`
                    
                    **Approach**: {approach}
                    
                    **Details**:
                    - Old Value: `{intent.get("old_value", "N/A")}`
                    - New Value: `{intent.get("new_value", "N/A")}`
                    - Context: {intent.get("context", "N/A")}
                    """)
                
                with col2:
                    st.metric("Reliability", reliability.split()[1])
                
                # Step 2: Perform refactoring
                with st.spinner("🔧 Applying changes..."):
                    # Get the current merged script
                    original_merged_script = st.session_state.merged_java_file
                    
                    # Save current version to history BEFORE refactoring (for undo)
                    if not st.session_state.merged_java_history:
                        st.session_state.merged_java_history = []
                    st.session_state.merged_java_history.append(original_merged_script)
                    
                    # Refactor with feedback
                    diff_output, refactored_script = refactorAutomationScriptWithFeedback(
                        original_merged_script,
                        script_feedback
                    )
                    
                    # Update the merged script
                    st.session_state.merged_java_file = refactored_script
                    
                    # Store diff output - append to list to keep history
                    if not st.session_state.script_diff_outputs:
                        st.session_state.script_diff_outputs = []
                    
                    # Append new diff (keeping all previous diffs)
                    st.session_state.script_diff_outputs.append(diff_output)
                    
                    # Store the intent for this iteration
                    if not st.session_state.refactoring_intents:
                        st.session_state.refactoring_intents = []
                    st.session_state.refactoring_intents.append({
                        "feedback": script_feedback,
                        "intent": intent,
                        "approach": approach
                    })
                    
                    # Increment counter to reset the feedback textarea
                    st.session_state.feedback_counter += 1
                
                st.success("✅ Refactoring complete! You can provide more feedback or click 'Done with Changes'")
                st.rerun()
            
            # Show all diffs if available for the merged script
            if st.session_state.script_diff_outputs:
                st.divider()
                st.success(f"✅ Merged script has been refactored {len(st.session_state.script_diff_outputs)} time(s)!")
                
                # Show each iteration of changes with intent - COLLAPSED by default
                for idx, diff_output in enumerate(st.session_state.script_diff_outputs, 1):
                    # Show intent if available
                    intent_label = ""
                    if st.session_state.refactoring_intents and idx <= len(st.session_state.refactoring_intents):
                        intent_data = st.session_state.refactoring_intents[idx - 1]
                        intent_type = intent_data['intent'].get('type', 'N/A')
                        intent_label = f" [{intent_type}]"
                    
                    # Collapse each iteration - expanded=False for compact UI
                    with st.expander(f"📊 Iteration {idx}{intent_label} - View Changes", expanded=False):
                        # Show intent if available
                        if st.session_state.refactoring_intents and idx <= len(st.session_state.refactoring_intents):
                            intent_data = st.session_state.refactoring_intents[idx - 1]
                            
                            st.markdown("#### 🎯 Your Request & System Understanding")
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"**Your Feedback**: {intent_data['feedback']}")
                                st.markdown(f"**Detected Intent**: `{intent_data['intent'].get('type', 'N/A')}`")
                                st.markdown(f"**Approach Used**: {intent_data['approach']}")
                            with col2:
                                if intent_data['intent'].get('type') in ["rename_class", "rename_method", "rename_variable", "remove_code", "add_import", "remove_import", "snake_to_camel", "camel_to_snake", "update_string"]:
                                    st.success("Pattern ✅")
                                else:
                                    st.warning("LLM 🔄")
                            
                            st.divider()
                        
                        st.markdown("**Changes Made:**")
                        st.info("💡 Lines starting with `-` were removed, lines with `+` were added")
                        st.code(diff_output, language="diff")
                
                st.divider()
                # Show current script in collapsible section for compact UI
                with st.expander("✨ Current Merged Script (After All Changes) - Click to View", expanded=False):
                    st.code(st.session_state.merged_java_file, language="java")
            
            if done_btn:
                st.session_state.show_script_feedback_section = False
                st.rerun()
        
        # Only show download section if NOT in feedback mode
        if not st.session_state.show_script_feedback_section:
            st.divider()
            
            # Download button for merged file
            st.download_button(
                label="📥 Download Merged Java File",
                data=st.session_state.merged_java_file,
                file_name="GeneratedTests.java",
                mime="text/plain"
            )
            
            # Show summary of all changes if any diffs exist
            if st.session_state.script_diff_outputs:
                st.divider()
                st.subheader(f"📋 Summary of All Refactoring Iterations ({len(st.session_state.script_diff_outputs)} total)")
                for i, diff in enumerate(st.session_state.script_diff_outputs, 1):
                    if diff:
                        # Get intent data if available
                        intent_label = ""
                        if st.session_state.refactoring_intents and i <= len(st.session_state.refactoring_intents):
                            intent_data = st.session_state.refactoring_intents[i - 1]
                            intent_type = intent_data['intent'].get('type', 'N/A')
                            intent_label = f" [{intent_type}]"
                        
                        with st.expander(f"🔄 Iteration {i}{intent_label}", expanded=False):
                            # Show feedback and intent
                            if st.session_state.refactoring_intents and i <= len(st.session_state.refactoring_intents):
                                intent_data = st.session_state.refactoring_intents[i - 1]
                                st.markdown(f"**Your Feedback**: {intent_data['feedback']}")
                                st.markdown(f"**Detected Intent**: `{intent_data['intent'].get('type', 'N/A')}`")
                                st.markdown(f"**Approach**: {intent_data['approach']}")
                                st.divider()
                            
                            st.code(diff, language="diff")
        
        # Option to start over (always visible)
        st.divider()
        if st.button("🔄 Start Over"):
            st.session_state.feature_files = []
            st.session_state.verification_outputs = []
            st.session_state.input_requirement = ""
            st.session_state.show_feedback_section = False
            st.session_state.show_final_edit_section = False
            st.session_state.show_scripts_section = False
            st.session_state.java_files = []
            st.session_state.merged_java_file = None
            st.session_state.final_feature_file = None
            st.session_state.user_script_input = ""
            st.session_state.show_script_feedback_section = False
            st.session_state.script_diff_outputs = []
            st.session_state.feedback_counter = 0
            st.session_state.refactoring_intents = []
            st.session_state.merged_java_history = []
            st.rerun()