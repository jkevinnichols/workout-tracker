import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date
import json

st.title("My Workout Tracker")

# 1. Authenticate and connect to Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# --- CLOUD VS LOCAL AUTHENTICATION ---
if "gcp_service_account_json" in st.secrets:
    # We are running in the cloud! Use the Streamlit Secret vault.
    creds_dict = json.loads(st.secrets["gcp_service_account_json"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
else:
    # We are running locally! Use the credentials file on the computer.
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)

client = gspread.authorize(creds)

# Make sure this matches exactly what worked for you earlier
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1PQnvN6k0wJkti8RDQG_EamBAC6C_qgYU0mrAeoHJ7Qs/edit?gid=0#gid=0").sheet1

# 2. Setup exercise lists
push_exercises = ["Bench Press", "Incline Dumbbell Press", "Tricep Extensions"]
leg_exercises = ["Squats", "Leg Press", "Calf Raises"]
pull_exercises = ["Deadlifts", "Pull-ups", "Bicep Curls"]
recovery_exercises = ["Yoga with Adriene", "Light Stretching", "Brisk Walk"]

# 3. Create the app interface
st.header("Log a New Session")

workout_date = st.date_input("Date", date.today())
workout_type = st.selectbox("Workout Type", ["Push", "Leg", "Pull", "Active Recovery"])

if workout_type == "Push":
    exercise = st.selectbox("Exercise", push_exercises)
elif workout_type == "Leg":
    exercise = st.selectbox("Exercise", leg_exercises)
elif workout_type == "Pull":
    exercise = st.selectbox("Exercise", pull_exercises)
elif workout_type == "Active Recovery":
    exercise = st.selectbox("Exercise", recovery_exercises)

notes = st.text_area("Notes (Weight, Reps, etc.)")

# 4. Save the data when the button is clicked
if st.button("Save to Sheet"):
    row_to_insert = [str(workout_date), workout_type, exercise, notes] 
    sheet.append_row(row_to_insert)
    st.success("Workout saved to your Google Sheet!")