"""
Pydantic Models for Request/Response Validation
Defines the structure of API requests and responses
"""

from pydantic import BaseModel, Field
from typing import List, Optional


# Request Models
class GenerateFeatureRequest(BaseModel):
    """Request model for generating feature file"""
    requirement: str = Field(..., description="Input requirement text")
    
    class Config:
        json_schema_extra = {
            "example": {
                "requirement": "As a user, I want to login to the system..."
            }
        }


class VerifyFeatureRequest(BaseModel):
    """Request model for verifying feature file"""
    feature_file: str = Field(..., description="Generated feature file content")
    requirement: str = Field(..., description="Original requirement text")
    
    class Config:
        json_schema_extra = {
            "example": {
                "feature_file": "Feature: Login\n  Scenario: User login...",
                "requirement": "As a user, I want to login..."
            }
        }


class RegenerateFeatureRequest(BaseModel):
    """Request model for regenerating feature file with feedback"""
    requirement: str = Field(..., description="Original requirement text")
    previous_feature_file: str = Field(..., description="Previous feature file version")
    verification_feedback: str = Field(..., description="Verification feedback (edited by user)")
    custom_feedback: Optional[str] = Field(None, description="Additional user feedback")
    
    class Config:
        json_schema_extra = {
            "example": {
                "requirement": "As a user, I want to login...",
                "previous_feature_file": "Feature: Login...",
                "verification_feedback": "- Missing scenario: Password reset",
                "custom_feedback": "Add more edge cases"
            }
        }


class GenerateScriptsRequest(BaseModel):
    """Request model for generating automation scripts"""
    feature_file: str = Field(..., description="Final feature file content")
    
    class Config:
        json_schema_extra = {
            "example": {
                "feature_file": "Feature: Login\n  Scenario: User login..."
            }
        }


class MergeScriptsRequest(BaseModel):
    """Request model for merging Java scripts"""
    java_files: List[str] = Field(..., description="List of Java file contents")
    class_name: Optional[str] = Field("GeneratedTests", description="Name for merged class")
    
    class Config:
        json_schema_extra = {
            "example": {
                "java_files": ["public class Test1 {...}", "public class Test2 {...}"],
                "class_name": "MergedTests"
            }
        }


# Response Models
class GenerateFeatureResponse(BaseModel):
    """Response model for feature file generation"""
    success: bool = Field(..., description="Whether generation was successful")
    feature_file: Optional[str] = Field(None, description="Generated feature file content")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "feature_file": "Feature: Login\n  Scenario: User login...",
                "error": None
            }
        }


class VerifyFeatureResponse(BaseModel):
    """Response model for feature verification"""
    success: bool = Field(..., description="Whether verification was successful")
    verification_output: Optional[str] = Field(None, description="Verification analysis output")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "verification_output": "- Coverage Analysis\n  - Missing scenario: Password reset",
                "error": None
            }
        }


class RegenerateFeatureResponse(BaseModel):
    """Response model for feature regeneration"""
    success: bool = Field(..., description="Whether regeneration was successful")
    feature_file: Optional[str] = Field(None, description="Regenerated feature file content")
    verification_output: Optional[str] = Field(None, description="New verification output")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "feature_file": "Feature: Login (updated)...",
                "verification_output": "All scenarios covered",
                "error": None
            }
        }


class GenerateScriptsResponse(BaseModel):
    """Response model for script generation"""
    success: bool = Field(..., description="Whether generation was successful")
    java_files: Optional[List[str]] = Field(None, description="List of generated Java files")
    scenario_count: Optional[int] = Field(None, description="Number of scenarios processed")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "java_files": ["public class LoginTest {...}", "public class SignupTest {...}"],
                "scenario_count": 2,
                "error": None
            }
        }


class MergeScriptsResponse(BaseModel):
    """Response model for script merging"""
    success: bool = Field(..., description="Whether merging was successful")
    merged_file: Optional[str] = Field(None, description="Merged Java file content")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "merged_file": "public class GeneratedTests {...}",
                "error": None
            }
        }


class ErrorResponse(BaseModel):
    """Generic error response model"""
    success: bool = False
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Invalid input",
                "detail": "Feature file cannot be empty"
            }
        }