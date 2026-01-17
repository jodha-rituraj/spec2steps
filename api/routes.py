"""
API Routes for Test Automation Generator
All REST API endpoints for the application
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
import logging
from typing import List

from api.models import (
    GenerateFeatureRequest, GenerateFeatureResponse,
    VerifyFeatureRequest, VerifyFeatureResponse,
    RegenerateFeatureRequest, RegenerateFeatureResponse,
    GenerateScriptsRequest, GenerateScriptsResponse,
    MergeScriptsRequest, MergeScriptsResponse,
    ErrorResponse
)

# Import your existing utility functions
import sys
from pathlib import Path

# Add backend directory to Python path
backend_path = Path(__file__).parent.parent  # Points to backend/
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Now import from utils, features, etc. (which are inside backend/)
from utils.utils import (
    generateFeatureFile,
    generateVerificationOutput,
    generateAutomationScriptsPerScenario
)
from utils.gherkin_json_utils import json_to_gherkin, gherkin_to_json
from features.parser import GherkinScenarioParser
from features.merger import JavaFileMerger

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.post(
    "/generate-feature",
    response_model = GenerateFeatureResponse,
    status_code = status.HTTP_200_OK,
    summary = "Generate Feature File",
    description = "Generates a Gherkin feature file from input requirements"
)
async def generate_feature(request: GenerateFeatureRequest):
    """
    Generate a feature file from requirements
    
    Args:
        request: GenerateFeatureRequest containing requirement text
        
    Returns:
        GenerateFeatureResponse with generated feature file
    """
    try:
        logger.info("Generating feature file from requirements")
        
        if not request.requirement.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Requirement text cannot be empty"
            )
        
        # Generate feature file as JSON using existing function
        feature_json = generateFeatureFile(request.requirement)
        
        # Convert JSON to Gherkin text for API response
        feature_file = json_to_gherkin(feature_json)
        
        logger.info("Feature file generated successfully")
        
        return GenerateFeatureResponse(
            success = True,
            feature_file = feature_file,
            error = None
        )
        
    except Exception as e:
        logger.error(f"Error generating feature file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate feature file: {str(e)}"
        )


@router.post(
    "/verify-feature",
    response_model=VerifyFeatureResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Feature File",
    description="Verifies a feature file against original requirements"
)
async def verify_feature(request: VerifyFeatureRequest):
    """
    Verify feature file against requirements
    
    Args:
        request: VerifyFeatureRequest containing feature file and requirements
        
    Returns:
        VerifyFeatureResponse with verification output
    """
    try:
        logger.info("Verifying feature file")
        
        if not request.feature_file.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Feature file cannot be empty"
            )
        
        if not request.requirement.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Requirement text cannot be empty"
            )
        
        # Convert Gherkin to JSON for verification
        feature_json = gherkin_to_json(request.feature_file)
        
        # Verify feature file using existing function
        verification_output = generateVerificationOutput(
            request.requirement,
            feature_json
        )
        
        logger.info("Feature file verified successfully")
        
        return VerifyFeatureResponse(
            success=True,
            verification_output=verification_output,
            error=None
        )
        
    except Exception as e:
        logger.error(f"Error verifying feature file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify feature file: {str(e)}"
        )


@router.post(
    "/regenerate-feature",
    response_model=RegenerateFeatureResponse,
    status_code=status.HTTP_200_OK,
    summary="Regenerate Feature File",
    description="Regenerates feature file based on verification feedback"
)
async def regenerate_feature(request: RegenerateFeatureRequest):
    """
    Regenerate feature file with feedback
    
    Args:
        request: RegenerateFeatureRequest with feedback and previous version
        
    Returns:
        RegenerateFeatureResponse with new feature file and verification
    """
    try:
        logger.info("Regenerating feature file with feedback")
        
        # Build enhanced requirement with feedback
        if request.custom_feedback and request.custom_feedback.strip():
            enhanced_requirement = (
                f"{request.requirement}\n\n"
                f"PREVIOUS FEATURE FILE:\n{request.previous_feature_file}\n\n"
                f"FEEDBACK FROM VERIFICATION (USER EDITED):\n{request.verification_feedback}\n\n"
                f"ADDITIONAL USER FEEDBACK:\n{request.custom_feedback}"
            )
        else:
            enhanced_requirement = (
                f"{request.requirement}\n\n"
                f"PREVIOUS FEATURE FILE:\n{request.previous_feature_file}\n\n"
                f"FEEDBACK FROM VERIFICATION (USER EDITED):\n{request.verification_feedback}"
            )
        
        # Generate new feature file as JSON
        new_feature_json = generateFeatureFile(enhanced_requirement)
        
        # Convert to Gherkin for response
        new_feature_file = json_to_gherkin(new_feature_json)
        
        # Generate new verification output
        new_verification = generateVerificationOutput(
            enhanced_requirement,
            new_feature_json
        )
        
        logger.info("Feature file regenerated successfully")
        
        return RegenerateFeatureResponse(
            success=True,
            feature_file=new_feature_file,
            verification_output=new_verification,
            error=None
        )
        
    except Exception as e:
        logger.error(f"Error regenerating feature file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate feature file: {str(e)}"
        )


@router.post(
    "/generate-scripts",
    response_model=GenerateScriptsResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Automation Scripts",
    description="Generates Java automation scripts from feature file"
)
async def generate_scripts(request: GenerateScriptsRequest):
    """
    Generate Java automation scripts from feature file
    
    Args:
        request: GenerateScriptsRequest containing feature file
        
    Returns:
        GenerateScriptsResponse with list of Java files
    """
    try:
        logger.info("Generating automation scripts")
        
        if not request.feature_file.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Feature file cannot be empty"
            )
        
        # Convert Gherkin to JSON
        feature_json = gherkin_to_json(request.feature_file)
        
        # Count scenarios from JSON
        scenarios = feature_json.get("scenarios", [])
        
        if not scenarios:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No scenarios found in feature file"
            )
        
        logger.info(f"Found {len(scenarios)} scenario(s)")
        
        # Generate Java files (function handles JSON to Gherkin conversion internally)
        java_files = generateAutomationScriptsPerScenario(feature_json)
        
        logger.info(f"Generated {len(java_files)} Java file(s)")
        
        return GenerateScriptsResponse(
            success=True,
            java_files=java_files,
            scenario_count=len(scenarios),
            error=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating scripts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate scripts: {str(e)}"
        )


@router.post(
    "/merge-scripts",
    response_model=MergeScriptsResponse,
    status_code=status.HTTP_200_OK,
    summary="Merge Java Scripts",
    description="Merges multiple Java files into a single class"
)
async def merge_scripts(request: MergeScriptsRequest):
    """
    Merge multiple Java files into single class
    
    Args:
        request: MergeScriptsRequest containing list of Java files
        
    Returns:
        MergeScriptsResponse with merged Java file
    """
    try:
        logger.info(f"Merging {len(request.java_files)} Java file(s)")
        
        if not request.java_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No Java files provided for merging"
            )
        
        # Merge Java files using existing merger
        merger = JavaFileMerger(merged_class_name=request.class_name)
        merged_file = merger.merge(request.java_files)
        
        logger.info("Java files merged successfully")
        
        return MergeScriptsResponse(
            success=True,
            merged_file=merged_file,
            error=None
        )
        
    except Exception as e:
        logger.error(f"Error merging scripts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to merge scripts: {str(e)}"
        )


# Additional utility endpoints
@router.get("/status")
async def get_status():
    """Get API status"""
    return {
        "status": "operational",
        "message": "Test Automation Generator API is running"
    }