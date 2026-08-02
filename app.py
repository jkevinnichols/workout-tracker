import streamlit as st
import pandas as pd
from datetime import date
import os

# 1. Page Setup
st.set_page_config(page_title="My Workout Tracker", layout="centered")
st.title("Workout Log")
st.write(f"Today's Date: {date.today()}")

# 2. Setup the Data File
DATA_FILE = "workout_log.csv"

# Function to load existing data
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        # Create an empty dataframe with columns if the file doesn't exist
        return pd.DataFrame(columns=["Date", "Cycle Day", "Exercise", "Sets", "Reps", "Weight (lbs)", "Notes"])

# Function to save new data
def save_data(new_entry):
    df = load_data()
    # Add the new row
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    # Save back to CSV
    df.to_csv(DATA_FILE, index=False)

# 3. Creating the Form
with st.form("workout_form"):
    # Dropdowns for your cycle
    cycle_day = st.selectbox("Cycle Day", ["Push", "Leg", "Pull", "Active Recovery"])
    
    # Define your routines based on the cycle day
    routines = {
        "Push": ["Chest Press", "Overhead Press", "Tricep Extensions", "Lateral Raises"],
        "Leg": ["Goblet Squats", "RDLs", "Walking Lunges", "Calf Raises"],
        "Pull": ["Dumbbell Rows", "Dumbbell Pullovers", "Bicep Curls"],
        "Active Recovery": ["Yoga"]
    }
    
    # The exercise dropdown automatically updates based on the selected cycle_day
    exercise = st.selectbox("Exercise", routines[cycle_day])
    
    # Side-by-side columns look good on mobile for short numbers
    col1, col2, col3 = st.columns(3)
    with col1:
        sets = st.number_input("Sets", min_value=1, step=1)
    with col2:
        reps = st.number_input("Reps", min_value=1, step=1)
    with col3:
        weight = st.number_input("Weight (lbs)", min_value=0, step=5)
        
    notes = st.text_area("Performance Notes (e.g., Manageability, cardio output)")
    
    # The submit button
    submitted = st.form_submit_button("Log Workout")

# 4. Handling the Data Submission
if submitted:
    new_workout = {
        "Date": date.today(),
        "Cycle Day": cycle_day,
        "Exercise": exercise,
        "Sets": sets,
        "Reps": reps,
        "Weight (lbs)": weight,
        "Notes": notes
    }
    save_data(new_workout)
    st.success(f"Logged: {sets}x{reps} of {exercise} at {weight}lbs.")

# 5. Display Recent Logs
st.divider()
st.subheader("Recent Workouts")
df_logs = load_data()
if not df_logs.empty:
    # Sort by date, newest first (if Date column is available)
    st.dataframe(df_logs.sort_index(ascending=False), use_container_width=True)
else:
    st.info("No workouts logged yet. Your first entry will appear here!") 
