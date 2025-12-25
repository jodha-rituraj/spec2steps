from utils.utils import *
import streamlit as st

# ----------------------------
# Streamlit UI
# ----------------------------

st.set_page_config(page_title="End to End AI Enabled Test Cases Generation and Automation Dashboard", layout="wide")

st.title("End to End AI Enabled Test Cases Generation and Automation Dashboard")

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

inputRequirement = st.text_area(
    "Enter Requirements File/Text",
    value=st.session_state.input_requirement,
    height=300,
    placeholder="Paste raw requirements here..."
)

generateBtn = st.button("Generate Feature File & Verification")

# Stage 1: Generate Feature File and Verification Output
if generateBtn:
    if not inputRequirement.strip():
        st.warning("Please enter some text before generating.")
    else:
        st.session_state.input_requirement = inputRequirement
        
        with st.spinner("Generating Feature File ..."):
            feature_file = generateFeatureFile(inputRequirement)
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
    
    st.info("💡 **Tip**: Edit the verification output below to keep only the points you want to address. Remove any lines you want to ignore.")
    
    editable_verification = st.text_area(
        "Edit Verification Feedback (remove unwanted items):",
        value=st.session_state.verification_outputs[-1],
        height=200,
        key=f"edit_verification_{current_version}",
        help="Delete or modify lines you don't want to address"
    )
    
    custom_feedback = st.text_area(
        "Additional custom feedback (optional):",
        height=150,
        placeholder="Add any extra instructions... (optional)",
        key=f"feedback_{current_version}"
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
            
            # Use the refinement function instead of regeneration
            refined_feature_file = refineFeatureFileWithFeedback(
                original_feature_file = latest_feature_file,
                verification_feedback = editable_verification,
                user_feedback = custom_feedback
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
        with st.spinner("Parsing Feature File Scenarios..."):
            parser = GherkinScenarioParser()
            featureFileScenarios = parser.parse(latest_feature_file)
            st.success(f"Found {len(featureFileScenarios)} scenario(s)")
        
        with st.spinner("Generating Automation Scripts for each scenario..."):
            st.session_state.java_files = generateAutomationScriptsV2(featureFileScenarios)
            st.success(f"Generated {len(st.session_state.java_files)} Java file(s)")
    
    # Display individual Java files
    st.subheader("📄 Individual Generated Scripts")
    for i, java_code in enumerate(st.session_state.java_files, 1):
        with st.expander(f"Scenario {i} - Java Code"):
            st.code(java_code, language="java")
    
    # Merge Java files
    st.divider()
    st.subheader("🔗 Merged Java File")
    
    # Only merge if not already merged
    if not st.session_state.merged_java_file:
        with st.spinner("Merging all Java files into single class..."):
            merger = JavaFileMerger(merged_class_name="GeneratedTests")
            st.session_state.merged_java_file = merger.merge(st.session_state.java_files)
    
    st.code(st.session_state.merged_java_file, language="java")
    
    # Download button for merged file
    st.download_button(
        label="📥 Download Merged Java File",
        data=st.session_state.merged_java_file,
        file_name="GeneratedTests.java",
        mime="text/plain"
    )
    
    # Option to start over
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
        st.rerun()