import streamlit as st

import os, groq, langchain_groq
from dotenv import load_dotenv
from utils.llm_config import llm

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from llm_prompts.requirement_agent import SYSTEM_INSTRUCTION_REQ_AGENT
from llm_prompts.verification_agent import SYSTEM_INSTRUCTION_VERIFICATION_AGENT
from llm_prompts.java_automation_script_agent import SYSTEM_INSTRUCTION_AUTOMATION_AGENT

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

def generateAutomationScripts(featureFile: str) -> str:
    prompt_automation_script = ChatPromptTemplate.from_template(
        "{SYSTEM_INSTRUCTION}:\n\n{FEATURE_FILE}"
    )
    output_parser = StrOutputParser()
    chain_automation = prompt_automation_script | llm | output_parser

    automation_script = chain_automation.invoke({"SYSTEM_INSTRUCTION": SYSTEM_INSTRUCTION_AUTOMATION_AGENT,
    "FEATURE_FILE": featureFile})

    return automation_script
