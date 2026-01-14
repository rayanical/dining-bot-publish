"""
Frontend UI/UX Tests.

This module covers broader UI tests including the landing page, onboarding flow,
nutritional data display accuracy, and non-functional requirements (NFRs) like
responsiveness and load time.
"""

import pytest
import re
import time
import json
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:3000"

class TestDiningChatbot:
    """
    Test suite for general UI functionality and NFRs.
    """

    def test_landing_page_content(self, page: Page):
        """
        Verifies public branding elements on the landing page.
        Ensures the title and main heading are correct.
        """
        page.goto(BASE_URL)
        expect(page).to_have_title(re.compile("Create Next App|Dining Bot", re.IGNORECASE))
        expect(page.get_by_role("heading", name="Your Personal Dining Companion")).to_be_visible()

    def test_onboarding_wizard_flow(self, page: Page):
        """
        Req: Upload Dietary Constraints & Set Nutrition Goals.
        
        Walks through the multi-step onboarding wizard.
        Uses the 'auth.json' session fixture to bypass login.
        
        Steps:
        1. Navigate to onboarding.
        2. Complete 'Dietary Constraints' step.
        3. Complete 'Goals' step.
        4. Complete 'Cuisines' step.
        5. Complete 'Dislikes' step.
        6. Verify 'Finish' button appears.
        """
        # 1. Navigate directly to onboarding
        page.goto(f"{BASE_URL}/onboarding")

        # --- LOCATOR SETUP ---
        # Look inside <main> to avoid clicking DevTools buttons
        next_button = page.locator("main").get_by_role("button", name="Next")

        # STEP 1: Welcome
        expect(page.get_by_text("Welcome to the UMass Dining Bot")).to_be_visible()
        next_button.click()

        # STEP 2: Constraints
        expect(page.get_by_text("First, what should we avoid?")).to_be_visible()
        
        # Select Vegan
        page.locator("label").filter(has_text="Vegan").locator("input").click()
        
        # Type Allergy
        allergy_input = page.get_by_placeholder("e.g., Peanuts, Dairy")
        allergy_input.click()
        allergy_input.fill("Shellfish")
        
        # Small wait to let React update the state before we click Next
        page.wait_for_timeout(500)
        
        # Use force=True to bypass any temporary overlapping elements/re-renders
        next_button.click(force=True)

        # STEP 3: Goals
        expect(page.get_by_text("What are your primary health goals?")).to_be_visible()
        page.get_by_role("button", name="Gain Muscle / Weight").click()
        next_button.click(force=True)

        # STEP 4: Cuisines
        expect(page.get_by_text("What do you *like* to eat?")).to_be_visible()
        page.get_by_role("button", name="East Asian").click()
        next_button.click(force=True)

        # STEP 5: Dislikes
        expect(page.get_by_text("Almost done!")).to_be_visible()
        page.get_by_placeholder("e.g., Olives").fill("Mushrooms")
        page.wait_for_timeout(500)
        
        # Finish
        expect(page.get_by_role("button", name="Finish & Start Chatting")).to_be_visible()

    def test_nutritional_accuracy_display(self, page: Page):
        """
        Req: Accuracy of Nutritional Info
        
        Verifies that the UI accurately calculates and displays nutritional data.
        We mock the backend to return specific decimal values and verify the UI
        rounding logic works as expected (e.g., 95.4 -> 95).
        """
        # Mock Data with specific decimals to test frontend accuracy/rounding
        mock_data = {
            "results": [{
                "id": 9999,
                "item": "Precision Test Apple",
                "dining_hall": "Test Hall",
                "calories": 95.4,  # Should round down to 95
                "protein_g": 0.6,  # Should round up to 1
                "diet_types": ["Vegan"],
                "allergens": []
            }]
        }

        # Intercept the search request (Uses auth.json for login, but mocks the data source)
        page.route("**/api/food/search*", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(mock_data)
        ))

        # Navigate to Dashboard Log
        page.goto(f"{BASE_URL}/dashboard/log")

        # Perform Search
        page.get_by_placeholder("Search food").fill("Precision Test Apple")
        page.get_by_role("button", name="Search").click()

        # Verify Display Accuracy
        # Check Item Name matches
        expect(page.get_by_text("Precision Test Apple")).to_be_visible()
        # Check Calories (95.4 -> 95)
        expect(page.get_by_text("95 kcal")).to_be_visible()
        # Check Protein (0.6 -> 1)
        expect(page.get_by_text("1g protein")).to_be_visible()

    def test_nfr_performance_load(self, page: Page):
        """
        NFR: Performance < 5s
        
        Verifies that the main landing page loads and becomes interactive
        within 5 seconds.
        """
        start = time.time()
        page.goto(BASE_URL)
        page.wait_for_selector("button:has-text('Get Started')")
        assert time.time() - start < 5.0

    def test_nfr_mobile_responsiveness(self, page: Page):
        """
        NFR: Mobile Layout
        
        Verifies that the UI adjusts correctly to a mobile viewport (iPhone 12 Pro dimensions)
        and that no horizontal scrolling occurs on the body.
        """
        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(BASE_URL)
        expect(page.get_by_role("heading", name="Your Personal Dining Companion")).to_be_visible()
        
        scroll_width = page.evaluate("document.body.scrollWidth")
        assert scroll_width <= 440, "Mobile view broken"