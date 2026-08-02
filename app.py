import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# 1. Page Setup
st.set_page_config(page_title="My Workout Tracker", layout="centered")
st.title("Workout Log")
st.write(f"Today's Date: {date.today()}")

# 2. Setup the Google Sheets Connection
# Replace the URL below with your actual Google Sheet URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1PQnvN6k0wJkti8RDQG_EamBAC6C_qgYU0mrAeoHJ7Qs/edit"

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # This reads the data from your Google Sheet
    return conn.read(spreadsheet=SHEET_URL, usecols=[0,1,2,3,4,5,6], ttl=0)

def save_data(new_entry):
    # This adds the new row to your Google Sheet
    df = load_data()
    # Create a DataFrame for the new entry
    new_df = pd.DataFrame([new_entry])
    # Combine the existing data with the new entry
    df = pd.concat([df, new_df], ignore_index=True)
    conn.update(spreadsheet=SHEET_URL, data=df)

# 3. Creating the Form
with st.form("workout_form"):
    cycle_day = st.selectbox("Cycle Day", ["Push", "Leg", "Pull", "Active Recovery"])
    routines = {
        "Push": ["Chest Press", "Overhead Press", "Tricep Extensions", "Lateral Raises"],
        "Leg": ["Goblet Squats", "RDLs", "Walking Lunges", "Calf Raises"],
        "Pull": ["Dumbbell Rows", "Dumbbell Pullovers", "Bicep Curls"],
        "Active Recovery": ["Yoga"]
    }
    exercise = st.selectbox("Exercise", routines[cycle_day])
    col1, col2, col3 = st.columns(3)
    with col1: sets = st.number_input("Sets", min_value=1, step=1)
    with col2: reps = st.number_input("Reps", min_value=1, step=1)
    with col3: weight = st.number_input("Weight (lbs)", min_value=0, step=5)
    notes = st.text_area("Performance Notes")
    submitted = st.form_submit_button("Log Workout")

if submitted:
    new_workout = {
        "Date": str(date.today()),
        "Cycle Day": cycle_day,
        "Exercise": exercise,
        "Sets": sets,
        "Reps": reps,
        "Weight (lbs)": weight,
        "Notes": notes
    }
    save_data(new_workout)
    st.success("Workout saved to Google Sheets!")

st.divider()
st.subheader("Recent Workouts")
df_logs = load_data()
if not df_logs.empty:
    st.dataframe(df_logs.sort_index(ascending=False), use_container_width=True)
