"""
Pytest Configuration.

This module defines shared fixtures for Playwright tests, specifically
handling authentication state to speed up tests by reusing login sessions.
"""

import pytest
import os

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """
    Tells Playwright to use the saved login state (auth.json)
    for all tests, so you are already logged in.

    Args:
        browser_context_args (dict): Default context arguments from pytest-playwright.

    Returns:
        dict: Updated context arguments pointing to the storage state file.
    """
    # Ensure the path matches where you saved the file in Step 1
    auth_path = os.path.join(os.path.dirname(__file__), "auth.json")
    
    return {
        **browser_context_args,
        "storage_state": auth_path
    }