import streamlit as st

import os, groq, langchain_groq
from dotenv import load_dotenv
from utils.llm_config import llm

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

import re
from typing import List, Set

from llm_prompts.requirement_agent import SYSTEM_INSTRUCTION_REQ_AGENT, SYSTEM_INSTRUCTION_FEEDBACK_AGENT
from llm_prompts.verification_agent import SYSTEM_INSTRUCTION_VERIFICATION_AGENT
from llm_prompts.java_automation_script_agent import SYSTEM_INSTRUCTION_AUTOMATION_AGENT, SYSTEM_INSTRUCTION_AUTOMATION_AGENT_V2

from features.parser import GherkinScenarioParser, extractScenarioOulines
from features.merger import JavaFileMerger

def generateFeatureFile(inputRequirement: str) -> str:

    prompt = ChatPromptTemplate.from_template(
        "{SYSTEM_INSTRUCTION}:\n\n{INPUT_REQUIREMENTS}"
    )

    outputParser = StrOutputParser()

    chain = prompt | llm | outputParser

    result = chain.invoke({"SYSTEM_INSTRUCTION": SYSTEM_INSTRUCTION_REQ_AGENT,
    "INPUT_REQUIREMENTS": inputRequirement})

    return result

def refineFeatureFileWithFeedback(
    original_feature_file: str,
    verification_feedback: str = "",
    user_feedback: str = ""
) -> str:
    """Refine existing feature file based on feedback"""
    
    # Construct feedback context
    feedback_parts = []
    
    if verification_feedback.strip():
        feedback_parts.append(f"VERIFICATION FEEDBACK:\n{verification_feedback}")
    
    if user_feedback.strip():
        feedback_parts.append(f"USER FEEDBACK:\n{user_feedback}")
    
    combined_feedback = "\n\n".join(feedback_parts)
    
    prompt = ChatPromptTemplate.from_template(
        "{SYSTEM_INSTRUCTION}\n\n"
        "ORIGINAL FEATURE FILE:\n{ORIGINAL_FEATURE_FILE}\n\n"
        "{FEEDBACK}"
    )
    
    outputParser = StrOutputParser()
    chain = prompt | llm | outputParser
    
    result = chain.invoke({
        "SYSTEM_INSTRUCTION": SYSTEM_INSTRUCTION_FEEDBACK_AGENT,
        "ORIGINAL_FEATURE_FILE": original_feature_file,
        "FEEDBACK": combined_feedback
    })
    
    return result

def generateVerificationOutput(inputRequirement: str, featureFile: str) -> str:
    promptVerificationAgent = ChatPromptTemplate.from_template(
        "{SYSTEM_INSTRUCTION}:\n {INPUT_REQUIREMENTS} GENERATED FEATURE FILE:\n {FEATURE_FILE}"
    )
    outputParser = StrOutputParser()
    verificationChain = promptVerificationAgent | llm | outputParser
    
    verificationResult = verificationChain.invoke({"SYSTEM_INSTRUCTION": SYSTEM_INSTRUCTION_VERIFICATION_AGENT,
    "INPUT_REQUIREMENTS": inputRequirement,
    "FEATURE_FILE": featureFile})

    return verificationResult

def generateAutomationScripts(featureFile: str) -> str:
    promptAutomationScript = ChatPromptTemplate.from_template(
        "{SYSTEM_INSTRUCTION}:\n\n{FEATURE_FILE}"
    )
    outputParser = StrOutputParser()
    chainAutomation = promptAutomationScript | llm | outputParser

    automationScript = chainAutomation.invoke({"SYSTEM_INSTRUCTION": SYSTEM_INSTRUCTION_AUTOMATION_AGENT,
    "FEATURE_FILE": featureFile})

    return automationScript

def generateAutomationScriptsV2(featureFileScenarios: str) -> List[str]:
    promptAutomationScript = ChatPromptTemplate.from_template(
        "{SYSTEM_INSTRUCTION}:\n\n{FEATURE_FILE}"
    )
    outputParser = StrOutputParser()
    chainAutomation = promptAutomationScript | llm | outputParser

    javaCodeFiles = []

    for i, scenario in enumerate(featureFileScenarios):
        print(f"#-------------------- Generating Java Code for Scenario {i + 1} -------------------#")
        javaCode = chainAutomation.invoke({"SYSTEM_INSTRUCTION": SYSTEM_INSTRUCTION_AUTOMATION_AGENT_V2,
            "FEATURE_FILE": scenario})
        javaCodeFiles.append(javaCode)

    return javaCodeFiles
