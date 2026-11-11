import copy
import difflib
import os

import streamlit as st
from dotenv import load_dotenv

from agents import AutomationScriptAgent, RequirementAgent, VerificationAgent
from core.gherkin_json import gherkin_to_json, json_to_gherkin
from core.llm import get_llm

# On Streamlit Cloud, keys must come from the sidebar, never from a server-side .env.
IS_STREAMLIT_CLOUD = bool(os.getenv("STREAMLIT_SHARING") or os.getenv("STREAMLIT_SHARING_BASE_URL"))
if not IS_STREAMLIT_CLOUD:
    load_dotenv()

DISCLAIMER = "**Disclaimer**: AI can make mistakes. Review all generated output before use."

FEATURE_STATE = {
    "input_requirement": "",
    "direct_feature_file": "",
    "feature_files": [],
    "verification_outputs": [],
    "current_feature_version_index": 0,
    "include_verification_in_chat": False,
    "chat_messages": [],
    "proposed_feature_json": None,
    "awaiting_confirmation": False,
    "feedback_counter": 0,
    "show_final_edit_section": False,
    "show_scripts_section": False,
}
SCRIPT_STATE = {
    "user_script_input": "",
    "script_jsons": [],
    "java_files": [],
    "merged_script_json": None,
    "merged_java_file": None,
    "script_versions": [],
    "current_script_version_index": 0,
    "script_chat_messages": [],
    "proposed_script": None,
    "proposed_script_json": None,
    "script_reasoning": "",
    "script_awaiting_confirmation": False,
    "script_feedback_counter": 0,
}
SETTINGS_STATE = {
    "test_type": "API",
    "workflow_type": "Feature File",
    "llm_provider": "Groq",
    "user_api_key": "",
    "azure_endpoint": "",
    "azure_deployment": "",
    "azure_api_version": "2024-02-01",
    "api_key_valid": False,
}

API_CONTEXT_HINT = """Provide details like:
- API endpoint patterns or naming conventions
- Custom data models or utility classes to use
- Specific validation rules or assertions needed
- Custom headers, authentication methods, or payload structures
- Mock data patterns or test data details
- Business logic constraints or domain-specific rules"""

UI_CONTEXT_HINT = """Provide details like:
- Page URL patterns or routing conventions
- Custom Page Object classes or locator strategies
- Specific element selectors (CSS, XPath, ID patterns)
- Custom wait strategies or timeout requirements
- Browser configuration or driver setup details
- Special handling for dynamic elements, iframes, or modals"""


def reset_state(*groups):
    for group in groups:
        for key, value in group.items():
            st.session_state[key] = copy.deepcopy(value)


def init_state():
    for group in (FEATURE_STATE, SCRIPT_STATE, SETTINGS_STATE):
        for key, value in group.items():
            if key not in st.session_state:
                st.session_state[key] = copy.deepcopy(value)
    if "requirement_agent" not in st.session_state:
        st.session_state.requirement_agent = RequirementAgent()
        st.session_state.verification_agent = VerificationAgent()
        st.session_state.automation_agent = AutomationScriptAgent()


def read_upload(uploaded_file) -> str:
    data = uploaded_file.read()
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1")


def unified_diff(current: str, proposed: str) -> str:
    return "\n".join(
        difflib.unified_diff(
            current.splitlines(), proposed.splitlines(), fromfile="current", tofile="proposed", lineterm=""
        )
    )


def text_or_upload(label, upload_label, file_types, default, height, placeholder, key, language):
    """Paste-or-upload input. Returns the text (possibly empty)."""
    method = st.radio(label, ["Paste Content", "Upload File"], horizontal=True, key=f"{key}_method")
    if method == "Paste Content":
        return st.text_area(upload_label, value=default, height=height, placeholder=placeholder, key=f"{key}_text")

    uploaded = st.file_uploader(upload_label, type=file_types, key=f"{key}_file")
    if uploaded is None:
        return default
    try:
        text = read_upload(uploaded)
    except Exception as e:
        st.error(f"Could not read file: {e}")
        return ""
    st.success(f"Loaded file: {uploaded.name}")
    with st.expander("Preview", expanded=False), st.container(height=300):
        st.code(text, language=language)
    return text


def version_nav(index_key: str, total: int, prefix: str):
    idx = st.session_state[index_key]
    left, mid, right = st.columns([1, 2, 1])
    with left:
        if st.button("◀ Previous", disabled=idx == 0, use_container_width=True, key=f"{prefix}_prev"):
            st.session_state[index_key] -= 1
            st.rerun()
    with mid:
        st.markdown(f"<div style='text-align:center'><b>Version {idx + 1} of {total}</b></div>", unsafe_allow_html=True)
    with right:
        if st.button("Next ▶", disabled=idx == total - 1, use_container_width=True, key=f"{prefix}_next"):
            st.session_state[index_key] += 1
            st.rerun()


def call_llm(fn, *args, **kwargs):
    """Run a model call; on failure show the error and stop this run, leaving state untouched."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        st.error(f"Model call failed: {e}")
        st.stop()


def require_llm():
    if not st.session_state.api_key_valid:
        st.error("Configure an LLM provider in the sidebar first.")
        st.stop()


def render_sidebar():
    with st.sidebar:
        st.header("Configuration")
        provider = st.selectbox(
            "LLM Provider",
            ["Groq", "Azure OpenAI"],
            index=0 if st.session_state.llm_provider == "Groq" else 1,
        )
        st.session_state.llm_provider = provider
        llm_kwargs = configure_groq() if provider == "Groq" else configure_azure()

        st.info("**Privacy**: keys, prompts and conversations are not stored or logged.")

        if llm_kwargs:
            try:
                llm = get_llm(**llm_kwargs)
                for agent in ("requirement_agent", "verification_agent", "automation_agent"):
                    st.session_state[agent].update_llm(llm)
                st.session_state.api_key_valid = True
            except Exception as e:
                st.error(f"Initialization error: {e}")
                st.session_state.api_key_valid = False
        else:
            st.session_state.api_key_valid = False

        st.divider()
        st.subheader("Test Type")
        st.session_state.test_type = st.radio(
            "Type of test automation",
            ["API", "UI"],
            index=0 if st.session_state.test_type == "API" else 1,
            horizontal=True,
        )
        if st.session_state.test_type == "API":
            st.caption("REST Assured, Cucumber, TestNG")
        else:
            st.caption("Selenium WebDriver, Cucumber, TestNG")

        st.divider()
        st.subheader("Workflow")
        st.session_state.workflow_type = st.radio(
            "What to generate",
            ["Feature File", "Scripts Only"],
            index=0 if st.session_state.workflow_type == "Feature File" else 1,
            horizontal=True,
            help="Feature File: requirements → feature file → scripts. Scripts Only: start from an existing feature file.",
        )


def configure_groq():
    env_key = "" if IS_STREAMLIT_CLOUD else os.getenv("GROQ_API_KEY", "").strip()
    key = st.text_input(
        "Groq API Key",
        type="password",
        placeholder="gsk_...",
        value=st.session_state.user_api_key,
        help="Get a free key at console.groq.com/keys" + ("" if IS_STREAMLIT_CLOUD else ". Optional if GROQ_API_KEY is set in .env."),
    ).strip()
    if key:
        st.session_state.user_api_key = key
        st.success("Using provided Groq key")
        return {"provider": "groq", "api_key": key}
    if env_key:
        st.info("Using Groq key from .env")
        return {"provider": "groq", "api_key": env_key}
    st.warning("No Groq API key configured.")
    return None


def configure_azure():
    s = st.session_state
    s.user_api_key = st.text_input("Azure OpenAI API Key", type="password", value=s.user_api_key)
    s.azure_endpoint = st.text_input("Endpoint", placeholder="https://your-resource.openai.azure.com/", value=s.azure_endpoint)
    s.azure_deployment = st.text_input("Deployment Name", placeholder="e.g. gpt-4o", value=s.azure_deployment)
    s.azure_api_version = st.text_input("API Version", value=s.azure_api_version)

    if s.user_api_key and s.azure_endpoint and s.azure_deployment:
        st.success("Azure configuration provided")
        return {
            "provider": "azure",
            "api_key": s.user_api_key,
            "endpoint": s.azure_endpoint,
            "deployment_name": s.azure_deployment,
            "api_version": s.azure_api_version,
        }
    env = {k: os.getenv(k) for k in ("AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT_NAME")}
    if not IS_STREAMLIT_CLOUD and all(env.values()):
        st.info("Using Azure config from .env")
        return {"provider": "azure"}
    st.warning("Azure OpenAI configuration incomplete.")
    return None


def render_requirements_input():
    st.info("**Provide requirements** to generate a feature file.")
    requirement = text_or_upload(
        "How would you like to provide the requirements?",
        "Requirements",
        ["txt", "md"],
        st.session_state.input_requirement,
        250,
        "Paste raw requirements here...",
        "req",
        "text",
    )
    st.warning(DISCLAIMER)
    if not st.button("Generate Feature File & Verification", type="primary"):
        return

    require_llm()
    if not requirement.strip():
        st.warning("Enter some requirements first.")
        return

    reset_state(FEATURE_STATE, SCRIPT_STATE)
    st.session_state.input_requirement = requirement
    agent = st.session_state.requirement_agent
    with st.spinner(f"Generating {st.session_state.test_type} feature file..."):
        generate = agent.generate_api_feature_file if st.session_state.test_type == "API" else agent.generate_ui_feature_file
        feature_json = call_llm(generate, requirement)
    with st.spinner("Verifying against requirements..."):
        verification = call_llm(st.session_state.verification_agent.verify_feature_file, requirement, feature_json)

    st.session_state.feature_files = [feature_json]
    st.session_state.verification_outputs = [verification]
    st.rerun()


def render_feature_file_input():
    st.info("**Provide an existing feature file** to generate automation scripts directly.")
    feature_text = text_or_upload(
        "How would you like to provide the feature file?",
        "Feature file",
        ["feature", "txt"],
        st.session_state.direct_feature_file,
        300,
        "Feature: Your feature name\n\n  Scenario: Your scenario\n    Given ...\n    When ...\n    Then ...",
        "feature",
        "gherkin",
    )
    if feature_text and not any(k in feature_text.lower() for k in ("feature:", "scenario:", "given", "when", "then")):
        st.warning("This doesn't look like a Gherkin feature file (no Feature/Scenario/Given/When/Then).")
    st.warning(DISCLAIMER)
    if not st.button("Generate Scripts from Feature File", type="primary"):
        return

    require_llm()
    if not feature_text.strip():
        st.warning("Provide a feature file first.")
        return

    reset_state(FEATURE_STATE, SCRIPT_STATE)
    st.session_state.direct_feature_file = feature_text
    st.session_state.feature_files = [gherkin_to_json(feature_text)]
    st.session_state.verification_outputs = ["(Direct script generation - no verification)"]
    st.session_state.show_scripts_section = True
    st.rerun()


def render_feature_review():
    s = st.session_state
    st.divider()
    main_col, chat_col = st.columns([2, 1])

    with main_col:
        total = len(s.feature_files)
        s.current_feature_version_index = max(0, min(s.current_feature_version_index, total - 1))
        idx = s.current_feature_version_index

        st.subheader("Generated Feature File")
        version_nav("current_feature_version_index", total, "feature")
        feature_text = json_to_gherkin(s.feature_files[idx])
        with st.container(height=600):
            st.code(feature_text, language="gherkin")

        st.divider()
        title_col, check_col = st.columns([3, 1])
        title_col.subheader("Verification Agent Output")
        s.include_verification_in_chat = check_col.checkbox(
            "Include in chat",
            value=s.include_verification_in_chat,
            help="Send the verification feedback along with your next chat message",
        )
        with st.expander("View Verification Output", expanded=False), st.container(height=200):
            st.text(s.verification_outputs[idx])

        st.divider()
        accept_col, download_col = st.columns(2)
        if accept_col.button("Accept & Proceed to Scripts", use_container_width=True, type="primary"):
            s.show_final_edit_section = True
            st.rerun()
        download_col.download_button(
            "Download Feature File",
            data=feature_text,
            file_name=f"feature_v{idx + 1}.feature",
            mime="text/plain",
            use_container_width=True,
        )

    with chat_col:
        render_feature_chat()


def render_feature_chat():
    s = st.session_state
    st.subheader("Refine with Chat")
    with st.container(height=600):
        if not s.chat_messages:
            st.info("Ask questions or describe changes you'd like to make.")
        for msg in s.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    if s.awaiting_confirmation and s.proposed_feature_json:
        st.warning("**Proposed changes ready. Review and apply?**")
        proposed_text = json_to_gherkin(s.proposed_feature_json)
        current_text = json_to_gherkin(s.feature_files[s.current_feature_version_index])
        with st.expander("View Proposed Changes (Diff)", expanded=True):
            diff = unified_diff(current_text, proposed_text)
            if diff:
                st.code(diff, language="diff", wrap_lines=True)
            else:
                st.info("No differences from the current version.")

        apply_col, reject_col = st.columns(2)
        if apply_col.button("Apply", use_container_width=True, type="primary", key="apply_feature"):
            with st.spinner("Verifying..."):
                verification = call_llm(s.verification_agent.verify_feature_file, s.input_requirement, s.proposed_feature_json)
            s.feature_files.append(s.proposed_feature_json)
            s.verification_outputs.append(verification)
            s.current_feature_version_index = len(s.feature_files) - 1
            s.chat_messages.append({"role": "assistant", "content": "Changes applied as a new version."})
            s.proposed_feature_json, s.awaiting_confirmation = None, False
            st.rerun()
        if reject_col.button("Reject", use_container_width=True, key="reject_feature"):
            s.chat_messages.append({"role": "assistant", "content": "Changes rejected."})
            s.proposed_feature_json, s.awaiting_confirmation = None, False
            st.rerun()

    with st.form(key=f"chat_form_{s.feedback_counter}", clear_on_submit=True):
        message = st.text_input("Message", placeholder="Ask a question or describe changes...", label_visibility="collapsed")
        submitted = st.form_submit_button("Send", use_container_width=True)

    if submitted and message.strip():
        s.chat_messages.append({"role": "user", "content": message.strip()})
        verification = s.verification_outputs[-1] if s.include_verification_in_chat else ""
        refine = (
            s.requirement_agent.chat_refine_api_feature_file
            if s.test_type == "API"
            else s.requirement_agent.chat_refine_ui_feature_file
        )
        with st.spinner("Thinking..."):
            try:
                intent, explanation, proposed = refine(
                    current_feature_json=s.feature_files[-1],
                    chat_messages=s.chat_messages[:-1],
                    user_message=message.strip(),
                    verification_output=verification,
                )
                s.chat_messages.append({"role": "assistant", "content": explanation})
                has_change = intent in ("change", "regenerate") and proposed is not None
                s.proposed_feature_json = proposed if has_change else None
                s.awaiting_confirmation = has_change
                s.feedback_counter += 1
            except Exception as e:
                st.error(f"Error: {e}")
                s.chat_messages.append({"role": "assistant", "content": f"Sorry, I encountered an error: {e}"})
        st.rerun()

    if s.chat_messages and st.button("Clear Chat", use_container_width=True, key="clear_chat"):
        s.chat_messages, s.proposed_feature_json, s.awaiting_confirmation = [], None, False
        s.feedback_counter += 1
        st.rerun()


def render_final_edit():
    s = st.session_state
    st.divider()
    st.subheader("Final Review & Edit (Optional)")
    st.info("Edit the feature file manually, or proceed directly to script generation.")

    latest_text = json_to_gherkin(s.feature_files[-1])
    edited = st.text_area("Edit Feature File", value=latest_text, height=400, key="final_edit_feature_file")

    save_col, skip_col = st.columns(2)
    if save_col.button("Save Edits & Generate Scripts", use_container_width=True):
        if edited != latest_text:
            s.feature_files.append(gherkin_to_json(edited))
            s.verification_outputs.append("(Manually edited by user)")
        s.show_scripts_section, s.show_final_edit_section = True, False
        st.rerun()
    if skip_col.button("Skip Edit & Generate Scripts", use_container_width=True):
        s.show_scripts_section, s.show_final_edit_section = True, False
        st.rerun()


def render_scripts():
    s = st.session_state
    st.divider()
    st.subheader("Automation Scripts")

    with st.expander("Feature File & Chat History", expanded=False):
        feature_col, history_col = st.columns([2, 1])
        with feature_col, st.container(height=600):
            st.code(json_to_gherkin(s.feature_files[-1]), language="gherkin")
        with history_col:
            if not s.chat_messages:
                st.info("No chat refinements were made.")
            for msg in s.chat_messages:
                who = "You" if msg["role"] == "user" else "Assistant"
                st.markdown(f"**{who}:** {msg['content']}")

    if not s.java_files:
        render_script_generation()
        return

    st.divider()
    with st.expander("Per-scenario scripts", expanded=False):
        for i, java_code in enumerate(s.java_files, 1):
            st.markdown(f"**Scenario {i}**")
            with st.container(height=400):
                st.code(java_code, language="java")

    if not s.merged_java_file:
        agent = s.automation_agent
        if s.script_jsons:
            s.merged_script_json = agent.merge_script_jsons(s.script_jsons)
            s.merged_java_file = agent.script_json_to_java(s.merged_script_json)
        else:
            s.merged_java_file = agent.merge_java_files(s.java_files)
            s.merged_script_json = agent.java_to_script_json(s.merged_java_file)
        s.script_versions = [s.merged_java_file]
        s.current_script_version_index = 0

    st.divider()
    st.subheader("Merged Java File")
    script_col, chat_col = st.columns([2, 1])
    with script_col:
        idx = s.current_script_version_index
        version_nav("current_script_version_index", len(s.script_versions), "script")
        with st.container(height=800):
            st.code(s.script_versions[idx], language="java")
        st.download_button(
            "Download This Version",
            data=s.script_versions[idx],
            file_name=f"GeneratedTests_v{idx + 1}.java",
            mime="text/plain",
            use_container_width=True,
        )
    with chat_col:
        render_script_chat()

    st.divider()
    st.download_button(
        "Download Final Java File",
        data=s.script_versions[-1],
        file_name="GeneratedTests.java",
        mime="text/plain",
        type="primary",
    )
    if st.button("Start Over"):
        reset_state(FEATURE_STATE, SCRIPT_STATE)
        st.rerun()


def render_script_generation():
    s = st.session_state
    st.info("**Optional**: extra context helps the generated scripts match your framework.")
    context = st.text_area(
        "Additional context for script generation",
        value=s.user_script_input,
        height=150,
        placeholder=API_CONTEXT_HINT if s.test_type == "API" else UI_CONTEXT_HINT,
    )
    if not st.button("Generate Automation Scripts", use_container_width=True, type="primary"):
        return

    require_llm()
    s.user_script_input = context
    feature_json = s.feature_files[-1]
    agent = s.automation_agent
    count = len(feature_json.get("scenarios", []))
    with st.spinner(f"Generating {s.test_type} scripts for {count} scenario(s)..."):
        generate = (
            agent.generate_api_scripts_json_per_scenario if s.test_type == "API" else agent.generate_ui_scripts_json_per_scenario
        )
        s.script_jsons = call_llm(generate, feature_json, context)
        s.java_files = [agent.script_json_to_java(sj) for sj in s.script_jsons]
    st.rerun()


def render_script_chat():
    s = st.session_state
    st.subheader("Refine Script")
    with st.container(height=800):
        if not s.script_chat_messages:
            st.info("Ask questions about the script or describe changes you'd like to make.")
        for msg in s.script_chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    if s.script_awaiting_confirmation and s.proposed_script:
        st.warning("**Proposed changes ready. Review and apply?**")
        if s.script_reasoning:
            with st.expander("Model reasoning", expanded=False), st.container(height=200):
                st.markdown(s.script_reasoning)
        diff = unified_diff(s.script_versions[-1], s.proposed_script)
        if diff:
            with st.expander("View Changes (Diff)", expanded=True), st.container(height=300):
                st.code(diff, language="diff", wrap_lines=True)
        else:
            st.info("No visible changes.")
        with st.expander("View Full Proposed Script", expanded=False), st.container(height=300):
            st.code(s.proposed_script, language="java")

        apply_col, reject_col = st.columns(2)
        if apply_col.button("Apply", use_container_width=True, type="primary", key="apply_script"):
            s.script_versions.append(s.proposed_script)
            s.merged_java_file = s.proposed_script
            if s.proposed_script_json:
                s.merged_script_json = s.proposed_script_json
            s.current_script_version_index = len(s.script_versions) - 1
            s.script_chat_messages.append({"role": "assistant", "content": "Changes applied as a new version."})
            clear_script_proposal()
            st.rerun()
        if reject_col.button("Reject", use_container_width=True, key="reject_script"):
            s.script_chat_messages.append({"role": "assistant", "content": "Changes rejected."})
            clear_script_proposal()
            st.rerun()

    with st.form(key=f"script_chat_form_{s.script_feedback_counter}", clear_on_submit=True):
        message = st.text_input("Message", placeholder="Ask a question or describe changes...", label_visibility="collapsed")
        submitted = st.form_submit_button("Send", use_container_width=True)

    if submitted and message.strip():
        s.script_chat_messages.append({"role": "user", "content": message.strip()})
        history = s.script_chat_messages[:-1]
        agent = s.automation_agent
        with st.spinner("Thinking..."):
            try:
                proposed_script, s.proposed_script_json, s.script_reasoning = None, None, ""
                if s.merged_script_json:
                    intent, s.script_reasoning, explanation, proposed_json = agent.chat_refine_script_json(
                        s.merged_script_json, history, message.strip()
                    )
                    if proposed_json is not None:
                        proposed_script = agent.script_json_to_java(proposed_json)
                        s.proposed_script_json = proposed_json
                else:
                    intent, explanation, proposed_script = agent.chat_refine_script(
                        s.script_versions[-1], history, message.strip()
                    )
                s.script_chat_messages.append({"role": "assistant", "content": explanation})
                has_change = intent in ("change", "regenerate") and proposed_script is not None
                s.proposed_script = proposed_script if has_change else None
                s.script_awaiting_confirmation = has_change
                s.script_feedback_counter += 1
            except Exception as e:
                st.error(f"Error: {e}")
                s.script_chat_messages.append({"role": "assistant", "content": f"Sorry, I encountered an error: {e}"})
        st.rerun()

    if s.script_chat_messages and st.button("Clear Chat", use_container_width=True, key="clear_script_chat"):
        s.script_chat_messages = []
        clear_script_proposal()
        s.script_feedback_counter += 1
        st.rerun()


def clear_script_proposal():
    s = st.session_state
    s.proposed_script, s.proposed_script_json, s.script_reasoning = None, None, ""
    s.script_awaiting_confirmation = False


st.set_page_config(page_title="Requirements to Test Automation", layout="wide")
st.title("Requirements to Test Automation")
init_state()
render_sidebar()

if st.session_state.workflow_type == "Feature File":
    render_requirements_input()
else:
    render_feature_file_input()

if st.session_state.feature_files and not st.session_state.show_scripts_section:
    render_feature_review()
if st.session_state.show_final_edit_section and not st.session_state.show_scripts_section:
    render_final_edit()
if st.session_state.show_scripts_section:
    render_scripts()
