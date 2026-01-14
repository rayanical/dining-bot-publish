"""
Core Feature Tests.

This module contains integration tests for the primary features of the application:
custom meal logging, dashboard tracking, chat interaction, and meal planning.
It uses Playwright to drive the browser and mocks backend responses.
"""

import pytest
import re
import json
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:3000"

class TestCoreFeatures:
    """
    Test suite for critical user journeys.
    """

    def test_add_custom_meal(self, page: Page):
        """
        Req: Add Custom Meal or Food
        Verifies the UI flow for logging a custom item.
        Mocks the backend to ensure success.
        
        Steps:
        1. Navigate to log page.
        2. Open custom food form.
        3. Fill out details (Name, Calories).
        4. Submit and verify success toast/message.
        """
        # --- MOCKS ---
        # Mock the POST request to log food
        page.route("**/api/users/*/log-food", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"status": "success", "id": 999})
        ))
        # Mock the refresh of the daily log
        page.route("**/api/users/*/log*", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps([])
        ))

        # 1. Navigate
        page.goto(f"{BASE_URL}/dashboard/log")
        
        # 2. Open Custom Form
        page.get_by_role("button", name=re.compile("Add Custom Food")).click()
        
        # 3. Fill Form
        page.get_by_placeholder("e.g. Homemade Sandwich").fill("Test Sandwich")
        page.get_by_placeholder("0").first.fill("500")
        
        # 4. Submit
        page.get_by_role("button", name="Add to Log").click()
        
        # 5. Verify Success
        # exact=False allows matching "✅ Logged custom item..."
        expect(page.get_by_text("Logged custom item: Test Sandwich", exact=False)).to_be_visible()

    def test_track_daily_intake(self, page: Page):
        """
        Req: Track Daily Intake/Nutrition
        Verifies dashboard renders summary stats correctly based on backend data.
        
        Steps:
        1. Mock daily summary with specific calorie/macro values.
        2. Navigate to dashboard.
        3. Verify headers and specific calorie labels exist.
        4. Verify visual progress bar indicators.
        """
        # --- MOCK ---
        # Mock the summary data so the dashboard always has numbers to show
        page.route("**/api/users/*/daily-summary*", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({
                "status": "success",
                "calories": {"total": 1200, "target": 2000},
                "protein": {"total": 80, "target": 150},
                "carbs": {"total": 100, "target": 250},
                "fat": {"total": 40, "target": 70},
                "history": []
            })
        ))

        page.goto(f"{BASE_URL}/dashboard")
        
        # 1. Verify Header
        expect(page.get_by_role("heading", name="Nutrition Dashboard")).to_be_visible()
        
        # 2. Verify "Calories" Label exists
        expect(page.locator("span", has_text="Calories").first).to_be_visible()
        
        # 3. Verify Progress Bar (Red)
        progress_bar = page.locator(".bg-\\[\\#881C1B\\]")
        expect(progress_bar.first).to_be_visible()

    def test_dining_hall_chat(self, page: Page):
        """
        Req: Dining Hall Chat
        Verifies chat interface interaction.
        
        Steps:
        1. Mock streaming chat endpoint.
        2. Navigate to chat page.
        3. Type and send a message.
        4. Verify user message appears.
        5. Verify mocked bot response appears.
        """
        # --- MOCK ---
        # Mock the AI response stream
        page.route("**/api/ai-chat", lambda route: route.fulfill(
            status=200,
            content_type="text/plain",
            body="This is a mocked AI response about Worcester."
        ))

        page.goto(f"{BASE_URL}/chat")
        
        # 1. Type Message
        user_query = "What is being served at Worcester?"
        page.get_by_placeholder(re.compile("Ask for meal plans")).fill(user_query)
        
        # 2. Send
        page.get_by_role("button", name="Send").click()
        
        # 3. Verify User Message
        expect(page.get_by_text(user_query)).to_be_visible()
        
        # 4. Verify Bot Response
        expect(page.get_by_text("This is a mocked AI response")).to_be_visible()

    def test_generate_meal_plan(self, page: Page):
        """
        Req: Generate Daily Meal Plan
        Verifies Meal Builder UI and Logging.
        
        Steps:
        1. Mock summary (for gap analysis).
        2. Mock meal suggestion endpoint with a specific item.
        3. Navigate to meal builder.
        4. Verify suggested plan appears.
        5. Click 'Log Meal' and verify success message.
        """
        # --- MOCKS ---
        # Mock Summary (Gap Analysis)
        page.route("**/api/users/*/daily-summary*", lambda route: route.fulfill(
            status=200, content_type="application/json", 
            body=json.dumps({"status": "success", "calories": {"total": 500, "target": 2000}, "protein": {"total": 20, "target": 150}})
        ))
        # Mock Meal Suggestions
        page.route("**/api/meal-builder/suggest", lambda route: route.fulfill(
            status=200, content_type="application/json",
            body=json.dumps({
                "status": "success",
                "remaining": {"calories": 1500, "protein": 130},
                "meals": [{
                    "label": "High Protein Power",
                    "totals": {"calories": 600, "protein": 50},
                    "items": [{"id": 101, "item": "Grilled Chicken", "dining_hall": "Worcester", "calories": 300, "protein": 40}]
                }]
            })
        ))
        # Mock Log
        page.route("**/api/users/*/log-food", lambda route: route.fulfill(
            status=200, content_type="application/json", body=json.dumps({"status": "success"})
        ))

        # 1. Navigate
        page.goto(f"{BASE_URL}/meal-builder")

        # 2. Verify Page Loads
        expect(page.get_by_role("heading", name="Meal Builder")).to_be_visible()
        
        # 3. Check for specific plan content
        expect(page.get_by_text("High Protein Power")).to_be_visible()
        expect(page.get_by_text("Grilled Chicken")).to_be_visible()

        # 4. Log Meal
        page.get_by_role("button", name="Log Meal").click()

        # 5. Verify Success
        expect(page.get_by_text("Logged meal: High Protein Power")).to_be_visible()