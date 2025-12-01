import streamlit as st

import os, groq, langchain_groq
from dotenv import load_dotenv
from utils.llm_config import llm

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

import re
from typing import List, Set

from llm_prompts.requirement_agent import SYSTEM_INSTRUCTION_REQ_AGENT
from llm_prompts.verification_agent import SYSTEM_INSTRUCTION_VERIFICATION_AGENT
from llm_prompts.java_automation_script_agent import SYSTEM_INSTRUCTION_AUTOMATION_AGENT, SYSTEM_INSTRUCTION_AUTOMATION_AGENT_V2

def generateFeatureFile(inputRequirement: str) -> str:

    prompt = ChatPromptTemplate.from_template(
        "{SYSTEM_INSTRUCTION}:\n\n{INPUT_REQUIREMENTS}"
    )

    outputParser = StrOutputParser()

    chain = prompt | llm | outputParser

    result = chain.invoke({"SYSTEM_INSTRUCTION": SYSTEM_INSTRUCTION_REQ_AGENT,
    "INPUT_REQUIREMENTS": inputRequirement})

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

def extractScenarioOulines(featureText):
    """
    Parses a Gherkin feature text and extracts individual Scenario Outline blocks.
    Args:
        featureText (str): The raw content of the feature file.
    Returns:
        list: A list of strings, where each string is a complete Scenario Outline block.
    """
    scenarios = []
    currentBlock = []
    
    # Split the text into lines to process them one by one
    lines = featureText.splitlines()

    for line in lines:
        strippedLine = line.strip()

        if strippedLine.startswith("Scenario Outline:"):
            # If we were already building a block, save it to the list
            if currentBlock:
                scenarios.append("\n".join(currentBlock))
                currentBlock = [] # Reset for the new block
            
            currentBlock.append(line)
            
        # If we are currently inside a block (i.e., we have found the first Scenario Outline)
        elif currentBlock:
            currentBlock.append(line)

    # Append the very last block after the loop finishes
    if currentBlock:
        scenarios.append("\n".join(currentBlock))

    return scenarios

def mergeJavaFiles(javaFiles: List[str]) -> str:
    """
    Merges multiple Java file contents into a single file with:
    - All unique package declarations
    - Deduplicated imports
    - All public classes preserved separately
    
    Args:
        javaFiles: List of Java file contents as strings
    
    Returns:
        Merged Java file content as a string
    """
    packages = set()
    imports = set()
    classes = []
    
    for content in javaFiles:
        # Extract package (collect all unique)
        pkg = extractPackagesFromJavaFile(content)
        if pkg:
            packages.add(pkg)

        # Extract imports (collect all unique)
        imports.update(extractImportsFromJavaFile(content))
        
        # Extract complete class definition
        classDefinition = extractClassDefinitionFromJavaFile(content)
        if classDefinition:
            classes.append(classDefinition)    

    # Build merged file
    mergedJavaContent = createMergedJavaFile(
        packages,
        imports,
        classes
    )
    
    return mergedJavaContent


def extractPackagesFromJavaFile(content: str) -> str:
    match = re.search(r'^package\s+[\w.]+;', content, re.MULTILINE)
    return match.group(0) if match else None

def extractImportsFromJavaFile(content: str) -> Set[str]:
    imports = set()
    pattern = r'^import\s+(?:static\s+)?[\w.*]+;'
    matches = re.finditer(pattern, content, re.MULTILINE)
    for match in matches:
        imports.add(match.group(0))
    return imports

def extractClassDefinitionFromJavaFile(content: str) -> str:
    # Find the class declaration
    classMatch = re.search(r'public\s+class\s+\w+\s*{', content)
    if not classMatch:
        return None
    
    # Get content starting from class declaration
    classStart = classMatch.start()
    classContent = content[classStart:]
    
    # Find the matching closing brace for the class
    braceCount = 0
    classEnd = 0
    
    for i, char in enumerate(classContent):
        if char == '{':
            braceCount += 1
        elif char == '}':
            braceCount -= 1
            if braceCount == 0:
                classEnd = i + 1
                break
    
    return classContent[:classEnd].strip()


def createMergedJavaFile(packages: Set[str], imports: Set[str], 
                                   classes: List[str]) -> str:
    lines = []
    
    # Add all packages (sorted for consistency)
    sortedPackages = sorted(packages)
    lines.extend(sortedPackages)
    
    if sortedPackages:
        lines.append('')
    
    # Add imports (sorted for consistency)
    sortedImports = sorted(imports)
    lines.extend(sortedImports)
    
    if sortedImports:
        lines.append('')
    
    # Add all classes
    for i, classDefinition in enumerate(classes):
        lines.append(classDefinition)
        # Add blank line between classes (but not after the last one)
        if i < len(classes) - 1:
            lines.append('')
    
    return '\n'.join(lines)
