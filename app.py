import streamlit as st

import os, groq, langchain_groq
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from llm_prompts.requirement_agent import SYSTEM_INSTRUCTION_REQ_AGENT
from llm_prompts.verification_agent import SYSTEM_INSTRUCTION_VERIFICATION_AGENT
from llm_prompts.java_automation_script_agent import SYSTEM_INSTRUCTION_AUTOMATION_AGENT

os.environ["GROQ_API_KEY"] = "REDACTED"
 #

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.1,
)


def generateFeatureFile(inputRequirement: str) -> str:

    prompt = ChatPromptTemplate.from_template(
        "{SYSTEM_INSTRUCTION}:\n\n{INPUT_REQUIREMENTS}"
    )

    output_parser = StrOutputParser()

    chain = prompt | llm | output_parser

    result = chain.invoke({"SYSTEM_INSTRUCTION": SYSTEM_INSTRUCTION_REQ_AGENT,
    "INPUT_REQUIREMENTS": inputRequirement})

    return result

def generateVerificationOutput(inputRequirement: str, featureFile: str) -> str:
    prompt_verification_agent = ChatPromptTemplate.from_template(
        "{SYSTEM_INSTRUCTION}:\n {INPUT_REQUIREMENTS} GENERATED FEATURE FILE:\n {FEATURE_FILE}"
    )
    output_parser = StrOutputParser()
    verification_chain = prompt_verification_agent | llm | output_parser
    
    verification_result = verification_chain.invoke({"SYSTEM_INSTRUCTION": SYSTEM_INSTRUCTION_VERIFICATION_AGENT,
    "INPUT_REQUIREMENTS": inputRequirement,
    "FEATURE_FILE": featureFile})

    return verification_result

def generateScripts(featureFile: str) -> str:
    prompt_automation_script = ChatPromptTemplate.from_template(
        "{SYSTEM_INSTRUCTION}:\n\n{FEATURE_FILE}"
    )
    output_parser = StrOutputParser()
    chain_automation = prompt_automation_script | llm | output_parser

    automation_script = chain_automation.invoke({"SYSTEM_INSTRUCTION": SYSTEM_INSTRUCTION_AUTOMATION_AGENT,
    "FEATURE_FILE": featureFile})

    return automation_script

# ----------------------------
# Streamlit UI
# ----------------------------

st.set_page_config(page_title = "End to End AI Enabled Test Cases Generation and Automation Dashboard", layout = "wide")

st.title("End to End AI Enabled Test Cases Generation and Automation Dashboard")

inputRequirement = st.text_area(
    "Enter Requirements File/Text",
    height = 300,
    placeholder = "Paste raw requirements here..."
)

generateBtn = st.button("Generate Outputs")

if generateBtn:
    if not inputRequirement.strip():
        st.warning("Please enter some text before generating.")
    else:
        with st.spinner("Generating..."):
            featureFile = generateFeatureFile(inputRequirement)
            verificationOutput = generateVerificationOutput(inputRequirement, featureFile)
            scripts = generateScripts(featureFile)

        tab1, tab2, tab3 = st.tabs(["Feature File", "Verification Output", "Scripts"])

        with tab1:
            st.subheader("Generated Feature File")
            st.code(featureFile, language = "gherkin")

        with tab2:
            st.subheader("Verification Agent Output")
            st.text(verificationOutput)

        with tab3:
            st.subheader("Generated Scripts")
            st.code(scripts, language = "java")
