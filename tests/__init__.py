"""
Test Suite for AI Automation From Requirements

This package contains all test cases for the hybrid refactoring system:
- test_diff_accuracy.py: Demonstrates accurate diff generation using Python difflib
- test_hybrid_refactoring.py: Tests pattern-based refactoring (rename, remove, etc.)
- test_case_conversion.py: Tests snake_case ↔ camelCase conversion
- test_fallback_mechanism.py: Tests LLM fallback for unknown/complex patterns

Run all tests from project root:
    python -m pytest tests/
    
Run specific test:
    python tests/test_diff_accuracy.py
"""

__version__ = "1.0.0"
