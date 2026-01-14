"""
Backend Integration Tests.

This module tests the API endpoints using the `requests` library against a running
local backend server. It verifies user profile management, goal updates, and
the food logging lifecycle.
"""

from datetime import date
import requests

BACKEND_URL = "http://localhost:8000"
USER_ID = "4d86859e-f180-47b4-ae36-a2f19d41c93e"

def test_account_setup():
    """
    Test user profile creation and retrieval.

    Verifies:
    1. POST /api/users/profile creates a user with diets, allergies, and goals.
    2. GET /api/users/profile/{id} retrieves the correct data.
    3. Dietary constraints are correctly categorized (allergy vs preference).
    """
    payload = {
        "user_id": USER_ID,
        "email": "bahadurshrey@gmail.com",
        "diets": ["vegetarian"],
        "allergies": ["nuts", "soy"],
        "goal": "Gain Muscle / Weight",
        "dislikes": None,
        "liked_cuisines": []
    }

    post_res = requests.post(f"{BACKEND_URL}/api/users/profile", json=payload)

    assert post_res.status_code == 200, f"POST failed: {post_res.text}"
    assert post_res.json().get("status") == "success"

    get_res = requests.get(f"{BACKEND_URL}/api/users/profile/{payload['user_id']}")

    assert get_res.status_code == 200, f"GET failed: {get_res.text}"

    profile = get_res.json()

    assert profile["user_id"] == payload["user_id"]
    assert profile["email"] == payload["email"]
    assert profile["goal"] == payload["goal"]

    constraints = profile["dietary_constraints"]

    diets = [c["constraint"] for c in constraints if c["constraint_type"] == "preference"]
    allergies = [c["constraint"] for c in constraints if c["constraint_type"] == "allergy"]
    cuisines = [c["constraint"] for c in constraints if c["constraint_type"] == "cuisine"]
    dislikes = next((c["constraint"] for c in constraints if c["constraint_type"] == "dislike"), None)

    assert "vegetarian" in diets
    assert set(allergies) == {"nuts", "soy"}
    assert cuisines == []           
    assert dislikes in ["", None]   

def test_update_user_goals():
    """
    Test updating nutritional goals.

    Verifies:
    1. PATCH /api/users/{id}/goals updates calorie and protein targets.
    2. GET /api/users/{id}/daily-summary reflects the new targets.
    """
    update_payload = {
        "calories": 3000,
        "protein": 250
    }

    patch_res = requests.patch(
        f"{BACKEND_URL}/api/users/{USER_ID}/goals",
        json=update_payload
    )

    assert patch_res.status_code == 200, f"PATCH failed: {patch_res.text}"
    data = patch_res.json()
    assert data["status"] == "success"
    assert data["calories"] == 3000
    assert data["protein"] == 250
    
    summary_res = requests.get(
        f"{BACKEND_URL}/api/users/{USER_ID}/daily-summary",
        params={"date": date.today().isoformat()}
    )

    assert summary_res.status_code == 200, f"GET summary failed: {summary_res.text}"

    summary = summary_res.json()

    assert summary["calories"]["target"] == 3000
    assert summary["protein"]["target"] == 250

def test_food_logging_and_deleting():
    """
    Test the food logging lifecycle.

    Verifies:
    1. POST /log-food adds items to the user's history.
    2. Daily summary totals update correctly after adding items.
    3. DELETE /log-food/{id} removes items.
    4. Totals return to zero after all items are deleted.
    """
    today = date.today().isoformat()

    eggs_payload = {
        "item_name": "Scrambled Eggs",
        "meal_type": "breakfast",
        "calories": 110,
        "protein": 10,
        "date": today
    }

    eggs_res = requests.post(
        f"{BACKEND_URL}/api/users/{USER_ID}/log-food",
        json=eggs_payload
    )
    assert eggs_res.status_code == 200, f"POST eggs failed: {eggs_res.text}"
    eggs_id = eggs_res.json()["id"]

    summary1 = requests.get(
        f"{BACKEND_URL}/api/users/{USER_ID}/daily-summary",
        params={"date": today}
    )
    assert summary1.status_code == 200
    s1 = summary1.json()

    assert s1["calories"]["total"] == 110
    assert s1["protein"]["total"] == 10

    pizza_payload = {
        "item_name": "Cheese Pizza",
        "meal_type": "dinner",
        "calories": 203,
        "protein": 9,
        "date": today
    }

    pizza_res = requests.post(
        f"{BACKEND_URL}/api/users/{USER_ID}/log-food",
        json=pizza_payload
    )
    assert pizza_res.status_code == 200, f"POST pizza failed: {pizza_res.text}"
    pizza_id = pizza_res.json()["id"]

    summary2 = requests.get(
        f"{BACKEND_URL}/api/users/{USER_ID}/daily-summary",
        params={"date": today}
    )
    assert summary2.status_code == 200
    s2 = summary2.json()

    assert s2["calories"]["total"] == 110 + 203
    assert s2["protein"]["total"] == 10 + 9

    del_pizza = requests.delete(
        f"{BACKEND_URL}/api/users/{USER_ID}/log-food/{pizza_id}"
    )
    assert del_pizza.status_code == 200

    summary3 = requests.get(
        f"{BACKEND_URL}/api/users/{USER_ID}/daily-summary",
        params={"date": today}
    )
    assert summary3.status_code == 200
    s3 = summary3.json()

    assert s3["calories"]["total"] == 110
    assert s3["protein"]["total"] == 10

    del_eggs = requests.delete(
        f"{BACKEND_URL}/api/users/{USER_ID}/log-food/{eggs_id}"
    )
    assert del_eggs.status_code == 200

    summary4 = requests.get(
        f"{BACKEND_URL}/api/users/{USER_ID}/daily-summary",
        params={"date": today}
    )
    assert summary4.status_code == 200
    s4 = summary4.json()

    assert s4["calories"]["total"] == 0
    assert s4["protein"]["total"] == 0