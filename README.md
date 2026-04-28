# FitPlan AI

FitPlan AI is a multi-agent AI-powered fitness and meal planning application designed for busy students and individuals who struggle to fit health routines into their day-to-day schedule.

The app generates personalized workout plans, meal plans, editable schedules, calendar files, email-based schedule delivery, and simple progress tracking.

## Project Partner

Jared Allen

## Project Title

FitPlan AI: A Multi-Agent Fitness and Meal Planner with Scheduling and Email Support

## Project Description

FitPlan AI helps users create realistic workout and meal plans based on their goals, availability, dietary preferences, physical stats, and available equipment. The application focuses on creating plans that are practical and time-efficient rather than overly complicated.

Users enter information such as fitness goals, workout availability, workout split preference, workout style, dietary restrictions, age, height, weight, gender, and equipment. The system uses multiple AI agents to generate a workout plan, meal plan, schedule, calendar-ready file, and reminder email.

The application also allows users to edit the generated schedule, export the plan, send the schedule by email, and track workout progress.

## Features

- Personalized AI-generated workout plans
- Personalized AI-generated meal plans
- Custom workout split option
- Workout style options such as strength training, hypertrophy, plyometrics, functional fitness, mobility, and calisthenics
- Exercise instructions included in the workout plan
- Editable workout schedule
- Calendar file export using `.ics`
- Email delivery of workout schedule and calendar attachment
- Downloadable full plan as `.txt`
- Downloadable schedule as `.json`
- Local progress tracking with workout completion and notes
- Multi-tab Streamlit interface

## AI Agent Structure

The project uses a simple multi-agent workflow:

1. **Workout Agent**  
   Generates a personalized workout plan based on the user’s goals, equipment, schedule, workout split, and workout style.

2. **Meal Agent**  
   Generates a simple meal plan and optional grocery list based on dietary preferences, restrictions, and fitness goals.

3. **Scheduling Agent**  
   Creates a weekly schedule and reminder preview based on the generated workout and meal plans.

4. **Schedule JSON Agent**  
   Converts the workout schedule into structured JSON so it can be edited, exported, emailed, and converted into a calendar file.

5. **Coordinator Agent**  
   Runs each agent and combines the outputs into one complete user-facing result.

## Resources Used

- Python
- Streamlit
- OpenAI API
- python-dotenv
- smtplib for email sending
- Gmail App Password for authenticated email delivery
- Local JSON file for progress tracking

## Deliverables

The final project includes:

- A working Streamlit application
- AI-generated workout and meal plans
- Editable schedule feature
- Calendar `.ics` export
- Email-based schedule delivery
- Progress tracking
- GitHub repository with code and documentation
- Final report
- Recorded demo presentation


