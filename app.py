import streamlit as st
import os
import sys
import difflib
from dotenv import load_dotenv

# ----------------------------
# Early Configuration Setup
# ----------------------------

# Load .env file only for local development (not on Streamlit Cloud)
# Check if running on Streamlit Cloud by checking for STREAMLIT_SHARING environment variable
# or by checking if we're in a Streamlit deployment
IS_STREAMLIT_CLOUD = os.getenv("STREAMLIT_SHARING") is not None or os.getenv("STREAMLIT_SHARING_BASE_URL") is not None

if not IS_STREAMLIT_CLOUD:
    # Only load .env for local development
    load_dotenv()

# Now import utils after setting environment
from utils.gherkin_json_utils import json_to_gherkin, gherkin_to_json

# Import agent classes
from agents import RequirementAgent, VerificationAgent, AutomationScriptAgent

# ----------------------------
# Streamlit UI
# ----------------------------

st.set_page_config(page_title="End to End AI-Assisted Test Cases & Script Generator", layout="wide")

st.title("End to End AI-Assisted Test Cases & Script Generator")

# ----------------------------
# Initialize session state variables FIRST (before sidebar)
# ----------------------------
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
# JSON IR for scripts (new deterministic approach)
if 'script_jsons' not in st.session_state:
    st.session_state.script_jsons = []  # List of script JSON objects
if 'merged_script_json' not in st.session_state:
    st.session_state.merged_script_json = None  # Merged script JSON
if 'use_json_ir' not in st.session_state:
    st.session_state.use_json_ir = True  # Use JSON IR by default
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
if 'workflow_type' not in st.session_state:
    st.session_state.workflow_type = "Feature File"  # Default to feature file generation
if 'direct_feature_file' not in st.session_state:
    st.session_state.direct_feature_file = ""  # For direct script generation workflow

# ----------------------------
# Chat-based refinement session state variables
# ----------------------------
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []  # List of {role: 'user'/'assistant', content: str}
if 'proposed_feature_json' not in st.session_state:
    st.session_state.proposed_feature_json = None  # Proposed changes from LLM
if 'proposed_explanation' not in st.session_state:
    st.session_state.proposed_explanation = ""  # Explanation for proposed changes
if 'current_feature_version_index' not in st.session_state:
    st.session_state.current_feature_version_index = 0  # Index of currently displayed feature file version
if 'include_verification_in_chat' not in st.session_state:
    st.session_state.include_verification_in_chat = False  # Checkbox for including verification output
if 'show_chat_refinement' not in st.session_state:
    st.session_state.show_chat_refinement = False  # Whether to show chat refinement UI
if 'awaiting_confirmation' not in st.session_state:
    st.session_state.awaiting_confirmation = False  # Whether we're waiting for user to apply/reject changes

# ----------------------------
# Script chat-based refinement session state variables
# ----------------------------
if 'script_chat_messages' not in st.session_state:
    st.session_state.script_chat_messages = []  # Chat messages for script refinement
if 'proposed_script' not in st.session_state:
    st.session_state.proposed_script = None  # Proposed script changes from LLM
if 'proposed_script_json' not in st.session_state:
    st.session_state.proposed_script_json = None  # Proposed script JSON IR
if 'script_proposed_explanation' not in st.session_state:
    st.session_state.script_proposed_explanation = ""  # Explanation for proposed script changes
if 'script_reasoning' not in st.session_state:
    st.session_state.script_reasoning = ""  # LLM's thinking/reasoning tokens
if 'script_awaiting_confirmation' not in st.session_state:
    st.session_state.script_awaiting_confirmation = False  # Waiting for user to apply/reject script changes
if 'script_versions' not in st.session_state:
    st.session_state.script_versions = []  # History of script versions for version navigation
if 'current_script_version_index' not in st.session_state:
    st.session_state.current_script_version_index = 0  # Index of currently displayed script version
if 'script_feedback_counter' not in st.session_state:
    st.session_state.script_feedback_counter = 0  # Counter to reset script feedback input

# Initialize agents in session state (BEFORE sidebar uses them)
if 'requirement_agent' not in st.session_state:
    st.session_state.requirement_agent = RequirementAgent()
if 'verification_agent' not in st.session_state:
    st.session_state.verification_agent = VerificationAgent()
if 'automation_agent' not in st.session_state:
    st.session_state.automation_agent = AutomationScriptAgent()

# ----------------------------
# Sidebar for API Key Configuration
# ----------------------------
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # For Streamlit Cloud: API key must be entered manually
    # For local: Can use .env file or enter manually
    if IS_STREAMLIT_CLOUD:
        help_text = "Enter your GROQ API key. Required for Streamlit Cloud deployment."
    else:
        help_text = "Enter your GROQ API key. Optional if set in .env file (local development only)."
    
    api_key_input = st.text_input(
        "GROQ API Key",
        type="password",
        help=help_text,
        placeholder="gsk_...",
        value=""  # Always start empty - don't pre-fill from session
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
    # Priority: 1) User input (sidebar) > 2) Session state (if explicitly set) > 3) .env (local only)
    
    api_key_to_use = None
    key_source = None
    
    if api_key_input and api_key_input.strip():
        # User entered key in sidebar - use it and store in session
        api_key_to_use = api_key_input.strip()
        key_source = "sidebar"
        st.session_state.user_api_key = api_key_to_use  # Store for this session
        st.success("✅ Using provided API key")
    elif st.session_state.get('user_api_key'):
        # Use previously entered API key from this session (user already entered it)
        api_key_to_use = st.session_state.user_api_key
        key_source = "session"
        st.info("ℹ️ Using API key from current session")
    elif not IS_STREAMLIT_CLOUD and os.getenv("GROQ_API_KEY", "").strip():
        # Only check .env file for local development (not on Streamlit Cloud)
        api_key_to_use = os.getenv("GROQ_API_KEY").strip()
        key_source = ".env"
        st.info("ℹ️ Using API key from .env file (local development)")
        # Don't store .env key in session state for security
    else:
        # No API key available
        api_key_to_use = None
        key_source = None
        st.warning("⚠️ No API key configured. Please enter your GROQ API key above.")
    
    # Initialize LLM with the selected API key
    if api_key_to_use:
        from utils.llm_config import get_llm
        try:
            new_llm = get_llm(api_key_to_use)
            # Update all agents with new LLM
            st.session_state.requirement_agent.update_llm(new_llm)
            st.session_state.verification_agent.update_llm(new_llm)
            st.session_state.automation_agent.update_llm(new_llm)
            st.session_state.api_key_valid = True
        except Exception as e:
            st.error(f"❌ Invalid API key: {str(e)}")
            st.session_state.api_key_valid = False
            # Clear invalid key from session
            if key_source == "sidebar" or key_source == "session":
                st.session_state.user_api_key = None
    else:
        st.session_state.api_key_valid = False
    
    # Version information at bottom of sidebar
    st.divider()
    st.caption("🔧 **Version 2.0.0** | Jan 2026")

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

# Workflow Selection
st.subheader("🔀 Select Workflow")
workflow_type = st.radio(
    "What would you like to generate?",
    options=["Feature File", "Scripts Only"],
    index=0 if st.session_state.workflow_type == "Feature File" else 1,
    horizontal=True,
    help="Feature File: Generate feature file from requirements first, then scripts | Scripts Only: Generate scripts from an existing feature file"
)
st.session_state.workflow_type = workflow_type

# st.divider()

# =============================================
# WORKFLOW 1: Feature File Generation (Default)
# =============================================
if workflow_type == "Feature File":
    st.info("📝 **Provide requirements** to generate a feature file. You can paste text or upload a requirements file.")
    
    # Option to upload or paste requirements
    req_input_method = st.radio(
        "How would you like to provide the requirements?",
        options=["Paste Content", "Upload File"],
        horizontal=True,
        key="req_input_method"
    )
    
    if req_input_method == "Paste Content":
        input_requirement = st.text_area(
            "Enter Requirements File/Text/User Input",
            value=st.session_state.input_requirement,
            height=250,
            placeholder="Paste raw requirements here..."
        )
    else:  # Upload File
        req_uploaded_file = st.file_uploader(
            "Upload a requirements file",
            type=["txt", "md", "doc", "docx"],
            help="Upload a text file containing your requirements",
            key="req_file_uploader"
        )
        if req_uploaded_file is not None:
            try:
                # Try to read the file
                file_content = req_uploaded_file.read()
                
                # Try to decode as UTF-8
                try:
                    input_requirement = file_content.decode("utf-8")
                except UnicodeDecodeError:
                    # Try other encodings
                    try:
                        input_requirement = file_content.decode("latin-1")
                    except:
                        st.error("❌ **Error**: Unable to read the file. The file encoding is not supported. Please try a UTF-8 encoded text file.")
                        input_requirement = ""
                
                if input_requirement:
                    st.success(f"✅ Loaded file: {req_uploaded_file.name}")
                    # Show preview
                    with st.expander("📄 Preview uploaded requirements", expanded=False):
                        with st.container(height=300):
                            st.text(input_requirement)
            except Exception as e:
                st.error(f"❌ **Error reading file**: {str(e)}. Please upload a valid text file.")
                input_requirement = ""
        else:
            input_requirement = st.session_state.input_requirement

    st.warning("⚠️ **Disclaimer**: AI can make mistakes. Please validate and review all generated outputs before use.")

    generate_btn = st.button("Generate Feature File & Verification")

# =============================================
# WORKFLOW 2: Direct Script Generation
# =============================================
else:  # Scripts Only
    st.info("📝 **Provide an existing feature file** to directly generate automation scripts. You can paste the content or upload a `.feature` file.")
    
    # Option to upload or paste
    input_method = st.radio(
        "How would you like to provide the feature file?",
        options=["Paste Content", "Upload File"],
        horizontal=True
    )
    
    if input_method == "Paste Content":
        direct_feature_input = st.text_area(
            "Paste your Feature File content:",
            value=st.session_state.direct_feature_file,
            height=300,
            placeholder="Feature: Your feature name\n\n  Scenario: Your scenario\n    Given ...\n    When ...\n    Then ..."
        )
    else:  # Upload File
        uploaded_file = st.file_uploader(
            "Upload a .feature file",
            type=["feature", "txt"],
            help="Upload a Gherkin feature file (.feature or .txt)"
        )
        if uploaded_file is not None:
            try:
                # Try to read the file
                file_content = uploaded_file.read()
                
                # Try to decode as UTF-8
                try:
                    direct_feature_input = file_content.decode("utf-8")
                except UnicodeDecodeError:
                    # Try other encodings
                    try:
                        direct_feature_input = file_content.decode("latin-1")
                    except:
                        st.error("❌ **Error**: Unable to read the file. The file encoding is not supported. Please try a UTF-8 encoded text file.")
                        direct_feature_input = ""
                
                # Validate it looks like a feature file
                if direct_feature_input and not any(keyword in direct_feature_input.lower() for keyword in ["feature:", "scenario:", "given", "when", "then"]):
                    st.warning("⚠️ **Warning**: This file doesn't appear to be a valid Gherkin feature file. It should contain keywords like 'Feature:', 'Scenario:', 'Given', 'When', 'Then'.")
                
                if direct_feature_input:
                    st.success(f"✅ Loaded file: {uploaded_file.name}")
                    # Show preview
                    with st.expander("📄 Preview uploaded feature file", expanded=False):
                        with st.container(height=300):
                            st.code(direct_feature_input, language="gherkin")
            except Exception as e:
                st.error(f"❌ **Error reading file**: {str(e)}. Please upload a valid feature file.")
                direct_feature_input = ""
        else:
            direct_feature_input = st.session_state.direct_feature_file
    
    st.warning("⚠️ **Disclaimer**: AI can make mistakes. Please validate and review all generated outputs before use.")
    
    generate_scripts_btn = st.button("🚀 Generate Scripts from Feature File", type="primary")
    
    # Handle direct script generation
    if generate_scripts_btn:
        # Check if API key is valid
        if not st.session_state.get('api_key_valid', False):
            st.error("❌ Please configure a valid GROQ API key in the sidebar before generating!")
            st.stop()
        
        if not direct_feature_input.strip():
            st.warning("Please provide a feature file before generating scripts.")
        else:
            # Check if LLM is initialized
            import utils.utils
            if utils.utils.llm is None:
                st.error("❌ LLM not initialized. Please provide a GROQ API key in the sidebar.")
                st.stop()
            
            # Reset script-related state
            st.session_state.java_files = []
            st.session_state.merged_java_file = None
            st.session_state.user_script_input = ""
            st.session_state.show_script_feedback_section = False
            st.session_state.script_diff_outputs = []
            st.session_state.feedback_counter = 0
            st.session_state.refactoring_intents = []
            st.session_state.merged_java_history = []
            
            # Store the feature file - convert Gherkin to JSON
            from utils.gherkin_json_utils import gherkin_to_json
            direct_feature_json = gherkin_to_json(direct_feature_input)
            
            st.session_state.direct_feature_file = direct_feature_input
            st.session_state.feature_files = [direct_feature_json]
            st.session_state.verification_outputs = ["(Direct script generation - no verification)"]
            
            # Go directly to script generation
            st.session_state.show_scripts_section = True
            st.session_state.show_feedback_section = False
            st.session_state.show_final_edit_section = False
            
            st.rerun()
    
    # Set these to avoid errors in the rest of the code
    input_requirement = ""
    generate_btn = False

# Stage 1: Generate Feature File and Verification Output (only for Feature File workflow)
if workflow_type == "Feature File" and generate_btn:
    # Check if API key is valid
    if not st.session_state.get('api_key_valid', False):
        st.error("❌ Please configure a valid GROQ API key in the sidebar before generating!")
        st.stop()
    
    if not input_requirement.strip():
        st.warning("Please enter some text before generating.")
    else:
        # Check if LLM is initialized
        if not st.session_state.api_key_valid:
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
        
        st.session_state.input_requirement = input_requirement
        
        # Generate based on test type using agents
        if st.session_state.test_type == "API":
            with st.spinner("Generating API Feature File ..."):
                feature_json = st.session_state.requirement_agent.generate_api_feature_file(input_requirement)
                st.session_state.feature_files.append(feature_json)
        else:  # UI
            with st.spinner("Generating UI Feature File ..."):
                feature_json = st.session_state.requirement_agent.generate_ui_feature_file(input_requirement)
                st.session_state.feature_files.append(feature_json)
        
        with st.spinner("Generating Verification Agent Output ..."):
            verification_output = st.session_state.verification_agent.verify_feature_file(
                input_requirement,
                st.session_state.feature_files[-1]
            )
            st.session_state.verification_outputs.append(verification_output)
        
        st.session_state.show_feedback_section = False
        st.session_state.show_final_edit_section = False
        st.session_state.show_scripts_section = False
        # Reset chat state for new generation
        st.session_state.chat_messages = []
        st.session_state.proposed_feature_json = None
        st.session_state.proposed_explanation = ""
        st.session_state.current_feature_version_index = 0
        st.session_state.show_chat_refinement = True
        st.session_state.awaiting_confirmation = False
        st.rerun()

# =============================================
# Feature File Display with Chat Refinement
# =============================================
if st.session_state.feature_files and st.session_state.verification_outputs and not st.session_state.show_scripts_section:
    
    st.divider()
    
    # Create two-column layout: Main content (feature file) | Chat sidebar
    main_col, chat_col = st.columns([2, 1])
    
    with main_col:
        # Version navigation header
        total_versions = len(st.session_state.feature_files)
        
        # Ensure index is valid
        if st.session_state.current_feature_version_index >= total_versions:
            st.session_state.current_feature_version_index = total_versions - 1
        if st.session_state.current_feature_version_index < 0:
            st.session_state.current_feature_version_index = 0
        
        current_idx = st.session_state.current_feature_version_index
        
        # Version navigation with arrows
        st.subheader("📋 Generated Feature File")
        
        nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
        
        with nav_col1:
            if st.button("◀ Previous", disabled=(current_idx == 0), use_container_width=True, key="prev_version"):
                st.session_state.current_feature_version_index -= 1
                st.rerun()
        
        with nav_col2:
            st.markdown(f"<h4 style='text-align: center;'>Version {current_idx + 1} of {total_versions}</h4>", unsafe_allow_html=True)
        
        with nav_col3:
            if st.button("Next ▶", disabled=(current_idx == total_versions - 1), use_container_width=True, key="next_version"):
                st.session_state.current_feature_version_index += 1
                st.rerun()
        
        # Display current version feature file
        current_feature_json = st.session_state.feature_files[current_idx]
        feature_file_text = json_to_gherkin(current_feature_json)
        
        with st.container(height=600):
            st.code(feature_file_text, language="gherkin")
        
        # Verification Output section with toggle
        st.divider()
        
        verification_col1, verification_col2 = st.columns([3, 1])
        with verification_col1:
            st.subheader("✅ Verification Agent Output")
        with verification_col2:
            include_verification = st.checkbox(
                "Include in chat",
                value=st.session_state.include_verification_in_chat,
                key="include_verification_checkbox",
                help="Check this to include verification feedback in your chat messages"
            )
            st.session_state.include_verification_in_chat = include_verification
        
        current_verification = st.session_state.verification_outputs[current_idx]
        with st.expander("View Verification Output", expanded=False):
            with st.container(height=200):
                st.text(current_verification)
        
        # Action buttons
        st.divider()
        
        action_col1, action_col2 = st.columns(2)
        with action_col1:
            if st.button("✅ Accept & Proceed to Scripts", use_container_width=True, type="primary"):
                st.session_state.show_final_edit_section = True
                st.session_state.show_chat_refinement = False
                st.rerun()
        with action_col2:
            # Download current version
            st.download_button(
                label="📥 Download Feature File",
                data=feature_file_text,
                file_name=f"feature_v{current_idx + 1}.feature",
                mime="text/plain",
                use_container_width=True
            )
    
    # Chat sidebar - fixed height container with scrollable messages
    with chat_col:
        st.subheader("💬 Refine with Chat")
        
        # Fixed-height scrollable chat container
        chat_container = st.container(height=600)
        with chat_container:
            if not st.session_state.chat_messages:
                st.info("👋 Start a conversation! Ask questions or describe changes you'd like to make.")
            
            # Display chat messages using st.chat_message for nice styling
            for msg in st.session_state.chat_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
        
        # Show proposed changes if awaiting confirmation (outside the scrollable area)
        if st.session_state.awaiting_confirmation and st.session_state.proposed_feature_json:
            st.warning("📝 **Proposed Changes Ready - Review and Apply?**")
            
            with st.expander("View Proposed Changes (Diff)", expanded=True):
                proposed_text = json_to_gherkin(st.session_state.proposed_feature_json)
                
                # Get current feature text for diff
                if st.session_state.feature_files:
                    current_feature_json = st.session_state.feature_files[st.session_state.current_feature_version_index]
                    current_text = json_to_gherkin(current_feature_json)
                else:
                    current_text = ""
                
                # Generate unified diff
                current_lines = current_text.splitlines(keepends=True)
                proposed_lines = proposed_text.splitlines(keepends=True)
                
                diff_lines = list(difflib.unified_diff(
                    current_lines,
                    proposed_lines,
                    fromfile='Current Version',
                    tofile='Proposed Version',
                    lineterm=''
                ))
                
                if diff_lines:
                    # Display diff with syntax highlighting
                    diff_text = ''.join(diff_lines)
                    st.code(diff_text, language="diff")
                else:
                    st.info("No differences detected between current and proposed versions.")
                    st.code(proposed_text, language="gherkin")
            
            confirm_col1, confirm_col2 = st.columns(2)
            with confirm_col1:
                if st.button("✅ Apply", use_container_width=True, type="primary", key="apply_changes"):
                    # Apply the proposed changes
                    st.session_state.feature_files.append(st.session_state.proposed_feature_json)
                    
                    # Generate new verification output
                    with st.spinner("Generating verification..."):
                        new_verification = st.session_state.verification_agent.verify_feature_file(
                            st.session_state.input_requirement,
                            st.session_state.proposed_feature_json
                        )
                    st.session_state.verification_outputs.append(new_verification)
                    
                    # Update version index to latest
                    st.session_state.current_feature_version_index = len(st.session_state.feature_files) - 1
                    
                    # Add confirmation to chat
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": "✅ Changes applied! The feature file has been updated to a new version."
                    })
                    
                    # Reset proposal state
                    st.session_state.proposed_feature_json = None
                    st.session_state.proposed_explanation = ""
                    st.session_state.awaiting_confirmation = False
                    
                    st.rerun()
            
            with confirm_col2:
                if st.button("❌ Reject", use_container_width=True, key="reject_changes"):
                    # Add rejection to chat
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": "❌ Changes rejected. Feel free to provide more feedback."
                    })
                    
                    # Reset proposal state
                    st.session_state.proposed_feature_json = None
                    st.session_state.proposed_explanation = ""
                    st.session_state.awaiting_confirmation = False
                    
                    st.rerun()
        
        # Chat input - using form for Enter key submission (fixed at bottom of sidebar)
        with st.form(key=f"chat_form_{st.session_state.feedback_counter}", clear_on_submit=True):
            user_input = st.text_input(
                "Message:",
                placeholder="Ask a question or describe changes...",
                key=f"chat_input_{st.session_state.feedback_counter}",
                label_visibility="collapsed"
            )
            col_send, col_clear = st.columns([3, 1])
            with col_send:
                submitted = st.form_submit_button("📤 Send", use_container_width=True)
            with col_clear:
                # Clear button inside form doesn't work well, we'll handle outside
                pass
        
        # Handle form submission
        if submitted and user_input and user_input.strip():
            # Add user message to chat
            st.session_state.chat_messages.append({
                "role": "user",
                "content": user_input.strip()
            })
            
            # Get current feature file (latest version)
            latest_feature_json = st.session_state.feature_files[-1]
            
            # Prepare verification output if checkbox is checked
            verification_for_chat = ""
            if st.session_state.include_verification_in_chat:
                verification_for_chat = st.session_state.verification_outputs[-1]
            
            # Call the chat refinement method
            with st.spinner("🤔 Thinking..."):
                try:
                    if st.session_state.test_type == "API":
                        intent, explanation, proposed_json = st.session_state.requirement_agent.chat_refine_api_feature_file(
                            current_feature_json=latest_feature_json,
                            chat_messages=st.session_state.chat_messages[:-1],
                            user_message=user_input.strip(),
                            verification_output=verification_for_chat
                        )
                    else:  # UI
                        intent, explanation, proposed_json = st.session_state.requirement_agent.chat_refine_ui_feature_file(
                            current_feature_json=latest_feature_json,
                            chat_messages=st.session_state.chat_messages[:-1],
                            user_message=user_input.strip(),
                            verification_output=verification_for_chat
                        )
                    
                    # Add assistant response to chat
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": explanation
                    })
                    
                    # Only show Apply/Reject if it's a change request with valid proposed feature
                    if intent == "change" and proposed_json is not None:
                        st.session_state.proposed_feature_json = proposed_json
                        st.session_state.proposed_explanation = explanation
                        st.session_state.awaiting_confirmation = True
                    else:
                        # It's a question - no confirmation needed
                        st.session_state.proposed_feature_json = None
                        st.session_state.awaiting_confirmation = False
                    
                    st.session_state.feedback_counter += 1
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": f"Sorry, I encountered an error: {str(e)}"
                    })
            
            st.rerun()
        
        # Clear chat button (outside form)
        if st.session_state.chat_messages:
            if st.button("🗑️ Clear Chat", use_container_width=True, key="clear_chat"):
                st.session_state.chat_messages = []
                st.session_state.proposed_feature_json = None
                st.session_state.proposed_explanation = ""
                st.session_state.awaiting_confirmation = False
                st.session_state.feedback_counter += 1
                st.rerun()

# Show Final Edit Section before script generation
if st.session_state.show_final_edit_section and not st.session_state.show_scripts_section:
    st.divider()
    st.subheader("📝 Final Review & Edit (Optional)")
    
    st.info("💡 **Last chance to edit!** You can manually modify the feature file below, or proceed directly to script generation.")
    
    # Get the latest feature file (JSON)
    latest_feature_json = st.session_state.feature_files[-1]
    
    # Convert to Gherkin for editing
    latest_feature_text = json_to_gherkin(latest_feature_json)
    
    # Editable feature file
    edited_feature_file = st.text_area(
        "Edit Feature File (optional):",
        value=latest_feature_text,
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
        if edited_feature_file != latest_feature_text:
            # Convert edited Gherkin back to JSON
            from utils.gherkin_json_utils import gherkin_to_json
            edited_feature_json = gherkin_to_json(edited_feature_file)
            st.session_state.feature_files.append(edited_feature_json)
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
    
    # === PERSISTENCE: Show Feature File and Chat History ===
    with st.expander("📋 Feature File & Chat History (from refinement)", expanded=False):
        persist_col1, persist_col2 = st.columns([2, 1])
        
        with persist_col1:
            st.markdown("**📄 Final Feature File:**")
            # Show version info
            version_count = len(st.session_state.feature_files)
            st.caption(f"Version {version_count} of {version_count} (Final)")
            
            # Display the feature file
            latest_feature_json = st.session_state.feature_files[-1]
            feature_text = json_to_gherkin(latest_feature_json)
            with st.container(height=600):
                st.code(feature_text, language="gherkin")
        
        with persist_col2:
            st.markdown("**💬 Chat History:**")
            if st.session_state.chat_messages:
                with st.container(height=600):
                    for msg in st.session_state.chat_messages:
                        if msg["role"] == "user":
                            st.markdown(f"**🧑 You:** {msg['content']}")
                        else:
                            st.markdown(f"**🤖 Assistant:** {msg['content']}")
                        st.markdown("---")
            else:
                st.info("No chat refinements were made.")
    
    # Use the LATEST feature file (JSON) for script generation
    latest_feature_json = st.session_state.feature_files[-1]
    
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
            
            # Count scenarios from JSON
            num_scenarios = len(latest_feature_json.get("scenarios", []))
            st.success(f"Found {num_scenarios} scenario(s)")
            
            # Generate scripts using JSON IR (deterministic approach)
            if st.session_state.test_type == "API":
                with st.spinner("Generating API Automation Scripts for each scenario..."):
                    # Generate JSON IR first
                    st.session_state.script_jsons = st.session_state.automation_agent.generate_api_scripts_json_per_scenario(
                        latest_feature_json, 
                        user_additional_input=user_additional_input
                    )
                    # Convert to Java for display
                    st.session_state.java_files = [
                        st.session_state.automation_agent.script_json_to_java(sj) 
                        for sj in st.session_state.script_jsons
                    ]
                    st.success(f"Generated {len(st.session_state.java_files)} Java file(s)")
            else:  # UI
                with st.spinner("Generating UI Automation Scripts for each scenario..."):
                    # Generate JSON IR first
                    st.session_state.script_jsons = st.session_state.automation_agent.generate_ui_scripts_json_per_scenario(
                        latest_feature_json, 
                        user_additional_input=user_additional_input
                    )
                    # Convert to Java for display
                    st.session_state.java_files = [
                        st.session_state.automation_agent.script_json_to_java(sj) 
                        for sj in st.session_state.script_jsons
                    ]
                    st.success(f"Generated {len(st.session_state.java_files)} Java file(s)")
            
            st.rerun()
    
    # Display generated scripts if they exist
    if st.session_state.java_files:
        # Display individual Java files in collapsed expander
        st.divider()
        with st.expander("📄 Individual Generated Scripts (click to expand)", expanded=False):
            for i, java_code in enumerate(st.session_state.java_files, 1):
                st.markdown(f"**Scenario {i}:**")
                with st.container(height=400):
                    st.code(java_code, language="java")
                st.divider()
        
        # Merge Java files first
        st.divider()
        st.subheader("🔗 Merged Java File with Chat Refinement")
        st.info("💡 This is the final merged output. Use the chat to ask questions or request changes. (Using JSON IR for deterministic modifications)")
        
        # Only merge if not already merged
        if not st.session_state.merged_java_file:
            with st.spinner("Merging all scripts into single class..."):
                # Use JSON IR merging if we have script_jsons
                if st.session_state.script_jsons:
                    st.session_state.merged_script_json = st.session_state.automation_agent.merge_script_jsons(
                        st.session_state.script_jsons,
                        merged_class_name="GeneratedTests"
                    )
                    st.session_state.merged_java_file = st.session_state.automation_agent.script_json_to_java(
                        st.session_state.merged_script_json
                    )
                else:
                    # Fallback to legacy string-based merging
                    st.session_state.merged_java_file = st.session_state.automation_agent.merge_java_files(
                        st.session_state.java_files,
                        merged_class_name="GeneratedTests"
                    )
                    # Convert to JSON for future refinements
                    st.session_state.merged_script_json = st.session_state.automation_agent.java_to_script_json(
                        st.session_state.merged_java_file
                    )
                
                # Initialize script versions with the first merged version
                st.session_state.script_versions = [st.session_state.merged_java_file]
                st.session_state.current_script_version_index = 0
        
        # Ensure script_versions is initialized
        if not st.session_state.script_versions:
            st.session_state.script_versions = [st.session_state.merged_java_file]
            st.session_state.current_script_version_index = 0
        
        # === SPLIT VIEW: Script (left) + Chat (right) ===
        script_col, script_chat_col = st.columns([2, 1])
        
        # Script display column
        with script_col:
            # Version navigation
            num_script_versions = len(st.session_state.script_versions)
            current_script_idx = st.session_state.current_script_version_index
            
            if num_script_versions > 1:
                nav_col1, nav_col2, nav_col3 = st.columns([1, 3, 1])
                with nav_col1:
                    if st.button("◀", key="prev_script_version", disabled=(current_script_idx == 0)):
                        st.session_state.current_script_version_index -= 1
                        st.rerun()
                with nav_col2:
                    st.markdown(f"<div style='text-align: center;'>📄 Version {current_script_idx + 1} of {num_script_versions}</div>", unsafe_allow_html=True)
                with nav_col3:
                    if st.button("▶", key="next_script_version", disabled=(current_script_idx == num_script_versions - 1)):
                        st.session_state.current_script_version_index += 1
                        st.rerun()
            else:
                st.caption("📄 Version 1 of 1 (Original)")
            
            # Display current script version
            current_script = st.session_state.script_versions[current_script_idx]
            with st.container(height=800):
                st.code(current_script, language="java")
            
            # Download button for current version
            st.download_button(
                label="📥 Download This Version",
                data=current_script,
                file_name=f"GeneratedTests_v{current_script_idx + 1}.java",
                mime="text/plain",
                use_container_width=True
            )
        
        # Chat column
        with script_chat_col:
            st.subheader("� Refine Script")
            
            # Fixed-height scrollable chat container
            script_chat_container = st.container(height=800)
            with script_chat_container:
                if not st.session_state.script_chat_messages:
                    st.info("👋 Ask questions about the script or describe changes you'd like to make.")
                
                # Display chat messages using st.chat_message for nice styling
                for msg in st.session_state.script_chat_messages:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])
            
            # Show proposed changes if awaiting confirmation
            if st.session_state.script_awaiting_confirmation and st.session_state.proposed_script:
                st.warning("📝 **Proposed Changes Ready - Review and Apply?**")
                
                # Show LLM reasoning if available
                if st.session_state.script_reasoning:
                    with st.expander("🧠 LLM Reasoning (Thinking Process)", expanded=False):
                        with st.container(height=200):
                            st.markdown(st.session_state.script_reasoning)
                
                # Generate diff between current and proposed script
                import difflib
                current_script = st.session_state.script_versions[-1]
                proposed_script = st.session_state.proposed_script
                
                # Create unified diff
                current_lines = current_script.splitlines(keepends=True)
                proposed_lines = proposed_script.splitlines(keepends=True)
                diff_lines = list(difflib.unified_diff(
                    current_lines, 
                    proposed_lines,
                    fromfile='Current Version',
                    tofile='Proposed Version',
                    lineterm=''
                ))
                
                if diff_lines:
                    diff_text = ''.join(diff_lines)
                    with st.expander("📋 View Changes (Diff)", expanded=True):
                        with st.container(height=300):
                            st.code(diff_text, language="diff")
                else:
                    st.info("No visible changes detected.")
                
                # Option to view full proposed script
                with st.expander("📄 View Full Proposed Script", expanded=False):
                    with st.container(height=300):
                        st.code(st.session_state.proposed_script, language="java")
                
                confirm_col1, confirm_col2 = st.columns(2)
                with confirm_col1:
                    if st.button("✅ Apply", use_container_width=True, type="primary", key="apply_script_changes"):
                        # Apply the proposed changes - add to versions
                        st.session_state.script_versions.append(st.session_state.proposed_script)
                        st.session_state.merged_java_file = st.session_state.proposed_script
                        
                        # Update the merged_script_json if we have a proposed JSON
                        if hasattr(st.session_state, 'proposed_script_json') and st.session_state.proposed_script_json:
                            st.session_state.merged_script_json = st.session_state.proposed_script_json
                            st.session_state.proposed_script_json = None
                        
                        # Update version index to latest
                        st.session_state.current_script_version_index = len(st.session_state.script_versions) - 1
                        
                        # Add confirmation to chat
                        st.session_state.script_chat_messages.append({
                            "role": "assistant",
                            "content": "✅ Changes applied! The script has been updated to a new version."
                        })
                        
                        # Reset proposal state
                        st.session_state.proposed_script = None
                        st.session_state.script_proposed_explanation = ""
                        st.session_state.script_awaiting_confirmation = False
                        st.session_state.script_reasoning = ""  # Clear reasoning
                        
                        st.rerun()
                
                with confirm_col2:
                    if st.button("❌ Reject", use_container_width=True, key="reject_script_changes"):
                        # Add rejection to chat
                        st.session_state.script_chat_messages.append({
                            "role": "assistant",
                            "content": "❌ Changes rejected. Feel free to provide more feedback."
                        })
                        
                        # Reset proposal state
                        st.session_state.proposed_script = None
                        st.session_state.script_proposed_explanation = ""
                        st.session_state.script_awaiting_confirmation = False
                        st.session_state.script_reasoning = ""  # Clear reasoning
                        
                        st.rerun()
            
            # Chat input - using form for Enter key submission
            with st.form(key=f"script_chat_form_{st.session_state.script_feedback_counter}", clear_on_submit=True):
                script_user_input = st.text_input(
                    "Message:",
                    placeholder="Ask a question or describe changes...",
                    key=f"script_chat_input_{st.session_state.script_feedback_counter}",
                    label_visibility="collapsed"
                )
                script_submitted = st.form_submit_button("📤 Send", use_container_width=True)
            
            # Handle form submission
            if script_submitted and script_user_input and script_user_input.strip():
                # Add user message to chat
                st.session_state.script_chat_messages.append({
                    "role": "user",
                    "content": script_user_input.strip()
                })
                
                # Get current script (latest version)
                latest_script = st.session_state.script_versions[-1]
                
                # Call the chat refinement method - use JSON IR for deterministic changes
                with st.spinner("🤔 Thinking (deterministic JSON modifications)..."):
                    try:
                        # Use JSON IR-based refinement if we have merged_script_json
                        if st.session_state.merged_script_json:
                            intent, reasoning, explanation, proposed_json = st.session_state.automation_agent.chat_refine_script_json(
                                current_script_json=st.session_state.merged_script_json,
                                chat_messages=st.session_state.script_chat_messages[:-1],
                                user_message=script_user_input.strip()
                            )
                            
                            # Store reasoning for display
                            st.session_state.script_reasoning = reasoning
                            
                            # Convert proposed JSON to Java if we have one
                            proposed_script = None
                            if proposed_json is not None:
                                proposed_script = st.session_state.automation_agent.script_json_to_java(proposed_json)
                                # Store the JSON for next iteration
                                st.session_state.proposed_script_json = proposed_json
                        else:
                            # Fallback to legacy string-based refinement (no reasoning)
                            intent, explanation, proposed_script = st.session_state.automation_agent.chat_refine_script(
                                current_script=latest_script,
                                chat_messages=st.session_state.script_chat_messages[:-1],
                                user_message=script_user_input.strip()
                            )
                            st.session_state.script_reasoning = ""
                        
                        # Add assistant response to chat
                        st.session_state.script_chat_messages.append({
                            "role": "assistant",
                            "content": explanation
                        })
                        
                        # Only show Apply/Reject if it's a change request with valid proposed script
                        if intent == "change" and proposed_script is not None:
                            st.session_state.proposed_script = proposed_script
                            st.session_state.script_proposed_explanation = explanation
                            st.session_state.script_awaiting_confirmation = True
                        else:
                            # It's a question - no confirmation needed
                            st.session_state.proposed_script = None
                            st.session_state.script_awaiting_confirmation = False
                        
                        st.session_state.script_feedback_counter += 1
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        st.session_state.script_chat_messages.append({
                            "role": "assistant",
                            "content": f"Sorry, I encountered an error: {str(e)}"
                        })
                
                st.rerun()
            
            # Clear chat button
            if st.session_state.script_chat_messages:
                if st.button("�️ Clear Chat", use_container_width=True, key="clear_script_chat"):
                    st.session_state.script_chat_messages = []
                    st.session_state.proposed_script = None
                    st.session_state.script_proposed_explanation = ""
                    st.session_state.script_awaiting_confirmation = False
                    st.session_state.script_feedback_counter += 1
                    st.rerun()
        
        # Download final merged file
        st.divider()
        final_col1, final_col2 = st.columns(2)
        with final_col1:
            st.download_button(
                label="📥 Download Final Merged Java File",
                data=st.session_state.script_versions[-1],
                file_name="GeneratedTests.java",
                mime="text/plain",
                use_container_width=True
            )
        with final_col2:
            if len(st.session_state.script_versions) > 1:
                st.success(f"✅ Script refined {len(st.session_state.script_versions) - 1} time(s)")
        
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
            st.session_state.direct_feature_file = ""  # Reset direct feature file
            # Reset JSON IR state
            st.session_state.script_jsons = []
            st.session_state.merged_script_json = None
            # Reset feature file chat-related state
            st.session_state.chat_messages = []
            st.session_state.proposed_feature_json = None
            st.session_state.proposed_explanation = ""
            st.session_state.current_feature_version_index = 0
            st.session_state.include_verification_in_chat = False
            st.session_state.show_chat_refinement = False
            st.session_state.awaiting_confirmation = False
            # Reset script chat-related state
            st.session_state.script_chat_messages = []
            st.session_state.proposed_script = None
            st.session_state.script_proposed_explanation = ""
            st.session_state.script_awaiting_confirmation = False
            st.session_state.script_versions = []
            st.session_state.current_script_version_index = 0
            st.session_state.script_feedback_counter = 0
            st.rerun()