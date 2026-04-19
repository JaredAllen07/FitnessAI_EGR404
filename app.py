import os
from dotenv import load_dotenv
load_dotenv()

import json
from typing import Dict, Any

import streamlit as st
from openai import OpenAI

# -----------------------------
# App setup
# -----------------------------
st.set_page_config(page_title="FitPlan AI", page_icon="💪", layout="wide")

st.title("FitPlan AI")
st.subheader("AI-powered meal and workout planner with scheduling support")

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None


# -----------------------------
# Helper functions
# -----------------------------
def call_openai(system_prompt: str, user_prompt: str) -> str:
    """Generic helper for calling the OpenAI API."""
    if client is None:
        return "OpenAI API key not found. Please set OPENAI_API_KEY in your environment."

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.output_text
    except Exception as e:
        return f"Error calling OpenAI API: {e}"


def format_user_profile(user_data: Dict[str, Any]) -> str:
    """Convert user input into a clean text block for prompts."""
    return f"""
User profile:
- Fitness goal: {user_data['fitness_goal']}
- Age: {user_data['age']}
- Height: {user_data['height']} inches
- Weight: {user_data['weight']} lbs
- Gender: {user_data['gender']}
- Fitness level: {user_data['fitness_level']}
- Workout days per week: {user_data['workout_days']}
- Time per workout: {user_data['workout_time']} minutes
- Availability notes: {user_data['availability']}
- Dietary preferences: {user_data['diet_preferences']}
- Dietary restrictions: {user_data['diet_restrictions']}
- Equipment available: {user_data['equipment']}
- Wants grocery list: {user_data['include_grocery_list']}
""".strip()


# -----------------------------
# Agent functions
# -----------------------------
def workout_agent(user_data: Dict[str, Any]) -> str:
    system_prompt = (
        "You are a workout planning agent. Create realistic, safe, beginner-friendly or intermediate-friendly "
        "weekly workout plans based on the user's goals, schedule, and available equipment. "
        "Keep plans practical for busy students or busy adults. "
        "Do not provide medical advice. "
        "Return a clean response with these sections: Overview, Weekly Workout Plan, and Why This Fits the User."
    )

    user_prompt = f"""
{format_user_profile(user_data)}

Generate a weekly workout plan.
Requirements:
- Keep it realistic and time-efficient.
- Match the user's available equipment.
- Match the user's fitness level.
- Include rest or recovery when appropriate.
- Use a clean, easy-to-read structure.
"""
    return call_openai(system_prompt, user_prompt)


def meal_agent(user_data: Dict[str, Any]) -> str:
    grocery_line = "Include a grocery list section." if user_data["include_grocery_list"] else "Do not include a grocery list section."

    system_prompt = (
        "You are a meal planning agent. Create simple, time-efficient meal plans for busy users. "
        "Respect dietary preferences and restrictions. "
        "Favor realistic meals with repeatable ingredients and minimal preparation. "
        "Do not present this as medical or dietitian advice. "
        "Return a clean response with these sections: Overview, Meal Plan, Why This Fits the User, and optionally Grocery List."
    )

    user_prompt = f"""
{format_user_profile(user_data)}

Generate a simple meal plan.
Requirements:
- Meals should be realistic and easy to prepare.
- Keep the plan time-efficient.
- Respect all dietary preferences and restrictions.
- {grocery_line}
- Use a clean, easy-to-read structure.
"""
    return call_openai(system_prompt, user_prompt)


def scheduling_agent(user_data: Dict[str, Any], workout_output: str, meal_output: str) -> str:
    system_prompt = (
        "You are a scheduling and reminder agent. Turn the generated workout and meal guidance into a realistic "
        "weekly routine for a busy user. "
        "Create a simple schedule and reminder content. "
        "Return a clean response with these sections: Weekly Schedule, Reminder Preview, and Scheduling Notes."
    )

    user_prompt = f"""
{format_user_profile(user_data)}

Workout plan:
{workout_output}

Meal plan:
{meal_output}

Create:
1. A simple weekly schedule for workouts and meal prep.
2. A reminder email preview the user could receive.
3. Short scheduling notes explaining why the timing makes sense.

Keep the schedule practical and simple.
"""
    return call_openai(system_prompt, user_prompt)


def coordinator_agent(user_data: Dict[str, Any]) -> Dict[str, str]:
    """Main coordinator that runs all agents and combines outputs."""
    workout_output = workout_agent(user_data)
    meal_output = meal_agent(user_data)
    scheduling_output = scheduling_agent(user_data, workout_output, meal_output)

    return {
        "workout": workout_output,
        "meal": meal_output,
        "schedule": scheduling_output,
    }


# -----------------------------
# UI
# -----------------------------
with st.form("fitplan_form"):
    st.header("User Information")

    col1, col2 = st.columns(2)

    with col1:
        fitness_goal = st.selectbox(
            "Fitness Goal",
            ["Lose weight", "Build muscle", "Stay active", "Improve general fitness"],
        )
        age = st.number_input("Age", min_value=16, max_value=100, value=21)
        height = st.number_input("Height (inches)", min_value=48, max_value=90, value=68)
        weight = st.number_input("Weight (lbs)", min_value=80, max_value=500, value=160)
        gender = st.selectbox("Gender", ["Male", "Female", "Non-binary", "Prefer not to say"])
        fitness_level = st.selectbox("Fitness Level", ["Beginner", "Intermediate", "Advanced"])

    with col2:
        workout_days = st.slider("Workout Days Per Week", min_value=1, max_value=7, value=4)
        workout_time = st.slider("Time Per Workout (minutes)", min_value=15, max_value=120, value=30)
        availability = st.text_area(
            "Availability / Schedule Notes",
            placeholder="Example: Busy on Tuesdays and Thursdays, free after 5 PM on weekdays.",
        )
        diet_preferences = st.text_input(
            "Dietary Preferences",
            placeholder="Example: High-protein, vegetarian, no preference",
        )
        diet_restrictions = st.text_input(
            "Dietary Restrictions / Allergies",
            placeholder="Example: No nuts, lactose intolerant, no seafood",
        )
        equipment = st.text_input(
            "Available Equipment",
            placeholder="Example: Dumbbells, resistance bands, full gym, no equipment",
        )
        include_grocery_list = st.checkbox("Include Grocery List", value=True)

    submitted = st.form_submit_button("Generate Plan")


if submitted:
    user_data = {
        "fitness_goal": fitness_goal,
        "age": age,
        "height": height,
        "weight": weight,
        "gender": gender,
        "fitness_level": fitness_level,
        "workout_days": workout_days,
        "workout_time": workout_time,
        "availability": availability,
        "diet_preferences": diet_preferences,
        "diet_restrictions": diet_restrictions,
        "equipment": equipment,
        "include_grocery_list": include_grocery_list,
    }

    with st.spinner("Generating your personalized plan..."):
        results = coordinator_agent(user_data)

    st.success("Plan generated successfully.")

    tab1, tab2, tab3 = st.tabs(["Workout Plan", "Meal Plan", "Schedule & Reminders"])

    with tab1:
        st.markdown(results["workout"])

    with tab2:
        st.markdown(results["meal"])

    with tab3:
        st.markdown(results["schedule"])

    with st.expander("Raw User Data"):
        st.json(user_data)


# -----------------------------
# Footer notes
# -----------------------------
st.markdown("---")
st.caption(
    "FitPlan AI is a project prototype for generating general wellness planning suggestions. "
    "It is not medical, nutritional, or professional fitness advice."
)
