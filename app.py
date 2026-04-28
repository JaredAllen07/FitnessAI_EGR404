import os
import json
import re
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage
from pathlib import Path
from typing import Dict, Any, List

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

st.set_page_config(
    page_title="FitPlan AI",
    page_icon="💪",
    layout="wide"
)

# -----------------------------
# Custom Styling
# -----------------------------
st.markdown(
    """
    <style>
    .main-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 0px;
    }

    .subtitle {
        font-size: 18px;
        color: #B0B0B0;
        margin-bottom: 25px;
    }

    .section-card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #333333;
        margin-bottom: 20px;
    }

    .small-note {
        color: #A0A0A0;
        font-size: 14px;
    }

    .stButton>button {
        border-radius: 10px;
        padding: 0.6rem 1rem;
        font-weight: 600;
    }

    .stDownloadButton>button {
        border-radius: 10px;
        padding: 0.6rem 1rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-title">FitPlan AI</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">A multi-agent AI planner for workouts, meals, scheduling, progress tracking, and email-based calendar export.</div>',
    unsafe_allow_html=True,
)

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_APP_PASSWORD = os.getenv("SENDER_APP_PASSWORD")

PROGRESS_FILE = Path("progress.json")


# -----------------------------
# Email + Calendar Helpers
# -----------------------------
def create_ics_file(schedule_items: List[Dict[str, Any]]) -> str:
    ics = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//FitPlan AI//Workout Schedule//EN",
    ]

    for item in schedule_items:
        start_dt = datetime.strptime(
            f"{item['date']} {item['start_time']}",
            "%Y-%m-%d %I:%M %p",
        )

        end_dt = start_dt + timedelta(
            minutes=int(item.get("duration_minutes", 60))
        )

        start_str = start_dt.strftime("%Y%m%dT%H%M%S")
        end_str = end_dt.strftime("%Y%m%dT%H%M%S")

        title = f"Gym Day: {item['title']}"
        description = item.get("details", "").replace("\n", "\\n")

        ics.extend([
            "BEGIN:VEVENT",
            f"SUMMARY:{title}",
            f"DTSTART:{start_str}",
            f"DTEND:{end_str}",
            f"DESCRIPTION:{description}",
            "BEGIN:VALARM",
            "TRIGGER:-P1D",
            "ACTION:DISPLAY",
            "DESCRIPTION:Workout reminder - 1 day before",
            "END:VALARM",
            "BEGIN:VALARM",
            "TRIGGER:-PT2H",
            "ACTION:DISPLAY",
            "DESCRIPTION:Workout reminder - 2 hours before",
            "END:VALARM",
            "END:VEVENT",
        ])

    ics.append("END:VCALENDAR")

    return "\n".join(ics)


def send_schedule_email(
    to_email: str,
    schedule_items: List[Dict[str, Any]],
    ics_content: str,
):
    if not SENDER_EMAIL or not SENDER_APP_PASSWORD:
        raise ValueError(
            "Missing SENDER_EMAIL or SENDER_APP_PASSWORD in .env file."
        )

    msg = EmailMessage()

    msg["Subject"] = "Your FitPlan AI Workout Schedule"
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email

    schedule_text = ""

    for item in schedule_items:
        schedule_text += (
            f"- Gym Day: {item['title']} on "
            f"{item['date']} at {item['start_time']} "
            f"for {item.get('duration_minutes', 60)} minutes\n"
        )

    body = f"""
Hi,

Here is your FitPlan AI workout schedule:

{schedule_text}

A calendar file is attached to this email. You can import it into:
- Google Calendar
- Apple Calendar
- Outlook Calendar

Included reminders:
- 1 day before workout
- 2 hours before workout

Best,
FitPlan AI
"""

    msg.set_content(body)

    msg.add_attachment(
        ics_content,
        subtype="calendar",
        filename="fitplan_workout_schedule.ics",
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
        smtp.send_message(msg)


# -----------------------------
# OpenAI Helper
# -----------------------------
def call_openai(system_prompt: str, user_prompt: str) -> str:
    if client is None:
        return "OpenAI API key not found."

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
    return f"""
User profile:
- Fitness goal: {user_data['fitness_goal']}
- Age: {user_data['age']}
- Height: {user_data['height']} inches
- Weight: {user_data['weight']} lbs
- Gender: {user_data['gender']}
- Fitness level: {user_data['fitness_level']}
- Preferred workout split: {user_data['workout_split']}
- Preferred workout style: {user_data['workout_style']}
- Workout days per week: {user_data['workout_days']}
- Time per workout: {user_data['workout_time']} minutes
- Availability notes: {user_data['availability']}
- Dietary preferences: {user_data['diet_preferences']}
- Dietary restrictions: {user_data['diet_restrictions']}
- Equipment available: {user_data['equipment']}
- Wants grocery list: {user_data['include_grocery_list']}
- Preferred workout time: {user_data['preferred_workout_time']}
- Schedule start date: {user_data['schedule_start_date']}
""".strip()


# -----------------------------
# AI Agents
# -----------------------------
def workout_agent(user_data: Dict[str, Any]) -> str:
    system_prompt = (
        "You are a workout planning agent. "
        "Create realistic and time-efficient workout plans."
    )

    user_prompt = f"""
{format_user_profile(user_data)}

Generate:
- Overview
- Weekly workout plan
- Exercise instructions
- Why the plan fits the user
"""

    return call_openai(system_prompt, user_prompt)


def meal_agent(user_data: Dict[str, Any]) -> str:
    grocery_line = (
        "Include a grocery list."
        if user_data["include_grocery_list"]
        else "Do not include a grocery list."
    )

    system_prompt = (
        "You are a meal planning agent. "
        "Create simple meal plans for busy users."
    )

    user_prompt = f"""
{format_user_profile(user_data)}

Generate:
- Overview
- Meal plan
- Why the plan fits the user
- Grocery list if requested

{grocery_line}
"""

    return call_openai(system_prompt, user_prompt)


def scheduling_agent(
    user_data: Dict[str, Any],
    workout_output: str,
    meal_output: str,
) -> str:
    system_prompt = (
        "You are a scheduling agent. "
        "Create realistic schedules using AM/PM time."
    )

    user_prompt = f"""
{format_user_profile(user_data)}

Workout plan:
{workout_output}

Meal plan:
{meal_output}

Generate:
- Weekly schedule
- Reminder preview
- Scheduling notes
"""

    return call_openai(system_prompt, user_prompt)


def schedule_json_agent(
    user_data: Dict[str, Any],
    workout_output: str,
) -> str:
    system_prompt = (
        "Convert workout schedules into clean JSON arrays."
    )

    user_prompt = f"""
{format_user_profile(user_data)}

Workout plan:
{workout_output}

Return ONLY valid JSON in this format:

[
  {{
    "title": "Push",
    "date": "YYYY-MM-DD",
    "start_time": "06:00 PM",
    "duration_minutes": 60,
    "details": "Workout details"
  }}
]
"""

    return call_openai(system_prompt, user_prompt)


def coordinator_agent(user_data: Dict[str, Any]) -> Dict[str, str]:
    workout_output = workout_agent(user_data)

    meal_output = meal_agent(user_data)

    scheduling_output = scheduling_agent(
        user_data,
        workout_output,
        meal_output,
    )

    calendar_json_output = schedule_json_agent(
        user_data,
        workout_output,
    )

    return {
        "workout": workout_output,
        "meal": meal_output,
        "schedule": scheduling_output,
        "calendar_json": calendar_json_output,
    }


# -----------------------------
# Save / Export Helpers
# -----------------------------
def extract_json_array(text: str) -> List[Dict[str, Any]]:
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()

    start = text.find("[")
    end = text.rfind("]")

    if start == -1 or end == -1:
        raise ValueError("No JSON array found.")

    json_text = text[start:end + 1]

    return json.loads(json_text)


def build_full_plan_text(
    user_data: Dict[str, Any],
    results: Dict[str, str],
) -> str:
    return f"""
FITPLAN AI GENERATED PLAN

USER SUMMARY
Fitness Goal: {user_data['fitness_goal']}
Fitness Level: {user_data['fitness_level']}
Workout Split: {user_data['workout_split']}
Workout Style: {user_data['workout_style']}

WORKOUT PLAN
{results['workout']}

MEAL PLAN
{results['meal']}

SCHEDULE
{results['schedule']}
""".strip()


def load_progress() -> Dict[str, Any]:
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)

    return {}


def save_progress(progress_data: Dict[str, Any]) -> None:
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress_data, f, indent=4)


def update_schedule_from_editor(edited_rows):
    updated_schedule = []

    for row in edited_rows:
        updated_schedule.append(
            {
                "title": str(row["title"]),
                "date": str(row["date"]),
                "start_time": str(row["start_time"]),
                "duration_minutes": int(row["duration_minutes"]),
                "details": str(row["details"]),
            }
        )

    return updated_schedule


# -----------------------------
# Main Form
# -----------------------------
with st.form("fitplan_form"):
    st.header("User Information")

    st.caption(
        "Enter your information below. "
        "The app will generate a personalized plan, editable schedule, "
        "export files, and progress tracker."
    )

    input_tab1, input_tab2, input_tab3, input_tab4 = st.tabs(
        [
            "1. Physical Info",
            "2. Workout Preferences",
            "3. Nutrition",
            "4. Scheduling & Email",
        ]
    )

    with input_tab1:
        col1, col2 = st.columns(2)

        with col1:
            age = st.number_input(
                "Age",
                min_value=16,
                max_value=100,
                value=21,
            )

            height = st.number_input(
                "Height (inches)",
                min_value=48,
                max_value=90,
                value=68,
            )

        with col2:
            weight = st.number_input(
                "Weight (lbs)",
                min_value=80,
                max_value=500,
                value=160,
            )

            gender = st.selectbox(
                "Gender",
                [
                    "Male",
                    "Female",
                    "Non-binary",
                    "Prefer not to say",
                ],
            )

    with input_tab2:
        col1, col2 = st.columns(2)

        with col1:
            fitness_goal = st.selectbox(
                "Fitness Goal",
                [
                    "Lose weight",
                    "Build muscle",
                    "Stay active",
                    "Improve general fitness",
                ],
            )

            fitness_level = st.selectbox(
                "Fitness Level",
                [
                    "Beginner",
                    "Intermediate",
                    "Advanced",
                ],
            )

            workout_days = st.slider(
                "Workout Days Per Week",
                min_value=1,
                max_value=7,
                value=4,
            )

            workout_time = st.slider(
                "Time Per Workout (minutes)",
                min_value=15,
                max_value=120,
                value=60,
            )

        with col2:
            workout_split = st.selectbox(
                "Preferred Workout Split",
                [
                    "No preference",
                    "Full body",
                    "Upper / Lower",
                    "Push / Pull / Legs",
                    "Body part split",
                    "Custom",
                ],
            )

            custom_workout_split = ""

            if workout_split == "Custom":
                custom_workout_split = st.text_input(
                    "Enter your custom workout split",
                    placeholder="Example: Chest/Triceps, Back/Biceps, Legs",
                )

            workout_style = st.selectbox(
                "Preferred Workout Style",
                [
                    "No preference",
                    "Strength training",
                    "Hypertrophy / muscle building",
                    "Endurance",
                    "Plyometrics / explosive training",
                    "Functional fitness",
                    "Mobility / flexibility",
                    "Calisthenics",
                    "Mixed",
                ],
            )

            equipment = st.text_input(
                "Available Equipment",
                placeholder="Example: Dumbbells, full gym, bodyweight only",
            )

    with input_tab3:
        diet_preferences = st.text_input(
            "Dietary Preferences",
            placeholder="Example: High-protein, vegetarian",
        )

        diet_restrictions = st.text_input(
            "Dietary Restrictions / Allergies",
            placeholder="Example: No nuts, lactose intolerant",
        )

        include_grocery_list = st.checkbox(
            "Include Grocery List",
            value=True,
        )

    with input_tab4:
        availability = st.text_area(
            "Availability / Schedule Notes",
            placeholder="Example: Busy Tuesdays and Thursdays",
        )

        schedule_start_date = st.date_input(
            "Schedule Start Date"
        )

        time_options = [
            "05:00 AM", "05:30 AM",
            "06:00 AM", "06:30 AM",
            "07:00 AM", "07:30 AM",
            "08:00 AM", "08:30 AM",
            "09:00 AM", "09:30 AM",
            "10:00 AM", "10:30 AM",
            "11:00 AM", "11:30 AM",
            "12:00 PM", "12:30 PM",
            "01:00 PM", "01:30 PM",
            "02:00 PM", "02:30 PM",
            "03:00 PM", "03:30 PM",
            "04:00 PM", "04:30 PM",
            "05:00 PM", "05:30 PM",
            "06:00 PM", "06:30 PM",
            "07:00 PM", "07:30 PM",
            "08:00 PM", "08:30 PM",
            "09:00 PM", "09:30 PM",
            "10:00 PM",
        ]

        preferred_workout_time = st.selectbox(
            "Preferred Workout Start Time",
            time_options,
            index=26,
        )

        recipient_email = st.text_input(
            "Email to Send Schedule To",
            placeholder="Example: user@example.com",
        )

    submitted = st.form_submit_button("Generate Personalized Plan")


# -----------------------------
# Generate Plan
# -----------------------------
if submitted:
    final_workout_split = (
        custom_workout_split.strip()
        if workout_split == "Custom"
        else workout_split
    )

    if workout_split == "Custom" and not final_workout_split:
        st.error("Please enter your custom workout split.")
        st.stop()

    if not recipient_email.strip():
        st.error("Please enter an email address.")
        st.stop()

    user_data = {
        "fitness_goal": fitness_goal,
        "age": age,
        "height": height,
        "weight": weight,
        "gender": gender,
        "fitness_level": fitness_level,
        "workout_split": final_workout_split,
        "workout_style": workout_style,
        "workout_days": workout_days,
        "workout_time": workout_time,
        "availability": availability,
        "diet_preferences": diet_preferences,
        "diet_restrictions": diet_restrictions,
        "equipment": equipment,
        "include_grocery_list": include_grocery_list,
        "preferred_workout_time": preferred_workout_time,
        "schedule_start_date": schedule_start_date.strftime("%Y-%m-%d"),
        "recipient_email": recipient_email.strip(),
    }

    with st.spinner("Generating your personalized plan..."):
        results = coordinator_agent(user_data)

    st.session_state["results"] = results
    st.session_state["user_data"] = user_data

    st.success("Plan generated successfully.")


# -----------------------------
# Results Section
# -----------------------------
if "results" in st.session_state:
    results = st.session_state["results"]
    user_data = st.session_state["user_data"]

    output_tab1, output_tab2, output_tab3, output_tab4 = st.tabs(
        [
            "Workout Plan",
            "Meal Plan",
            "Schedule",
            "Calendar File Data",
        ]
    )

    with output_tab1:
        st.markdown(results["workout"])

    with output_tab2:
        st.markdown(results["meal"])

    with output_tab3:
        st.markdown(results["schedule"])

    with output_tab4:
        st.code(results["calendar_json"], language="json")

    st.markdown("---")

    st.header("Edit, Export, Email, and Track Progress")

    try:
        schedule_items = extract_json_array(
            results["calendar_json"]
        )

        st.subheader("Editable Workout Schedule")

        edited_schedule = st.data_editor(
            schedule_items,
            num_rows="dynamic",
            width="stretch",
            key="editable_schedule",
        )

        edited_schedule_items = update_schedule_from_editor(
            edited_schedule
        )

        full_plan_text = build_full_plan_text(
            user_data,
            results,
        )

        ics_content = create_ics_file(
            edited_schedule_items
        )

        st.subheader("Export Options")

        st.download_button(
            label="Download Full Plan (.txt)",
            data=full_plan_text,
            file_name="fitplan_full_plan.txt",
            mime="text/plain",
        )

        st.download_button(
            label="Download Calendar File (.ics)",
            data=ics_content,
            file_name="fitplan_workout_schedule.ics",
            mime="text/calendar",
        )

        st.download_button(
            label="Download Schedule JSON",
            data=json.dumps(
                edited_schedule_items,
                indent=4,
            ),
            file_name="fitplan_schedule.json",
            mime="application/json",
        )

        st.subheader("Email Schedule")

        st.info(
            f"Schedule will be sent to: "
            f"{user_data['recipient_email']}"
        )

        if st.button("Send Edited Workout Schedule Email"):
            try:
                send_schedule_email(
                    to_email=user_data["recipient_email"],
                    schedule_items=edited_schedule_items,
                    ics_content=ics_content,
                )

                st.success(
                    "Workout schedule email sent successfully."
                )

            except Exception as e:
                st.error(f"Could not send email: {e}")

        st.subheader("Progress Tracking")

        progress_data = load_progress()

        for item in edited_schedule_items:
            progress_key = (
                f"{item['date']}_{item['title']}"
            )

            if progress_key not in progress_data:
                progress_data[progress_key] = {
                    "completed": False,
                    "notes": "",
                }

            st.markdown(
                f"**Gym Day: {item['title']} — "
                f"{item['date']} at "
                f"{item['start_time']}**"
            )

            progress_data[progress_key]["completed"] = st.checkbox(
                "Completed",
                value=progress_data[progress_key]["completed"],
                key=f"completed_{progress_key}",
            )

            progress_data[progress_key]["notes"] = st.text_area(
                "Notes",
                value=progress_data[progress_key]["notes"],
                key=f"notes_{progress_key}",
                placeholder="Example: Increase weight next week.",
            )

        if st.button("Save Progress"):
            save_progress(progress_data)

            st.success(
                "Progress saved successfully."
            )

    except Exception as e:
        st.error(
            f"Could not load editable schedule tools: {e}"
        )

    with st.expander("Raw User Data"):
        st.json(user_data)

st.markdown("---")

st.caption(
    "FitPlan AI is a project prototype for generating "
    "general wellness planning suggestions. "
    "It is not medical or professional advice."
)
