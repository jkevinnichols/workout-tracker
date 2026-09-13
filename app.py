import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date
import json
import pandas as pd
import time

st.set_page_config(page_title="My Workout Tracker", layout="wide")
st.title("My Workout Tracker")

# ---------------- 1. Authenticate and connect to Google Sheets ----------------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

try:
    running_in_cloud = "gcp_service_account_json" in st.secrets
except Exception:
    running_in_cloud = False

if running_in_cloud:
    creds_dict = json.loads(st.secrets["gcp_service_account_json"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
else:
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)

client = gspread.authorize(creds)
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1PQnvN6k0wJkti8RDQG_EamBAC6C_qgYU0mrAeoHJ7Qs/edit?gid=0#gid=0").sheet1

# Sheet columns (make sure your header row matches this exactly):
# Date | Cycle Day | Exercise | Set | Reps | Weight | Duration (sec) | Notes
HEADERS = ["Date", "Cycle Day", "Exercise", "Set", "Reps", "Weight", "Duration (sec)", "Notes"]

# ---------------- 2. Exercise lists ----------------
push_exercises = ["Incline Chest Press", "Shoulder Press", "Tricep Extensions", "Lateral Raises"]
leg_exercises = ["Goblet Squats", "Front Squats", "RDLs", "Walking Lunges", "Calf Raises"]
pull_exercises = ["Rows", "Pull Overs", "Bicep Curls", "Suitcase Holds"]
recovery_exercises = ["Yoga with Adriene", "Light Stretching", "Brisk Walk"]

TIME_BASED_EXERCISES = ["Suitcase Holds"]

# ---------------- Helper: cached data pull ----------------
@st.cache_data(ttl=30)
def load_data():
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    return df

def clear_cache():
    load_data.clear()

# ---------------- Session state setup ----------------
if "current_sets" not in st.session_state:
    st.session_state.current_sets = []  # list of dicts for the entry being built
if "last_exercise" not in st.session_state:
    st.session_state.last_exercise = None

tab_log, tab_history, tab_timer = st.tabs(["Log a Session", "History & Progress", "Rest Timer"])

# =========================================================
# TAB 1: LOG A SESSION (with multi-set entry + notes)
# =========================================================
with tab_log:
    st.header("Log a New Session")

    workout_date = st.date_input("Date", date.today())
    workout_type = st.selectbox("Workout Type", ["Push", "Leg", "Pull", "Active Recovery"])

    if workout_type == "Push":
        exercise = st.selectbox("Exercise", push_exercises)
    elif workout_type == "Leg":
        exercise = st.selectbox("Exercise", leg_exercises)
    elif workout_type == "Pull":
        exercise = st.selectbox("Exercise", pull_exercises)
    else:
        exercise = st.selectbox("Exercise", recovery_exercises)

    # Reset the in-progress sets if the exercise changes, to avoid mixing exercises in one entry
    if st.session_state.last_exercise != exercise:
        st.session_state.current_sets = []
        st.session_state.last_exercise = exercise

    is_time_based = exercise in TIME_BASED_EXERCISES

    st.subheader(f"Add sets for: {exercise}")
    col1, col2, col3 = st.columns([1, 1, 1])

    if is_time_based:
        with col1:
            duration = st.number_input("Duration (seconds)", min_value=0, step=5, key="duration_input")
        with col2:
            weight = st.number_input("Weight (lbs)", min_value=0.0, step=2.5, key="weight_input")
        reps = None
    else:
        with col1:
            reps = st.selectbox("Reps", [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20], key="reps_input")
        with col2:
            weight = st.number_input("Weight (lbs)", min_value=0.0, step=2.5, key="weight_input")
        duration = None

    with col3:
        st.write("")
        st.write("")
        if st.button("+ Add Set"):
            set_number = len(st.session_state.current_sets) + 1
            st.session_state.current_sets.append({
                "Set": set_number,
                "Reps": reps,
                "Weight": weight,
                "Duration (sec)": duration,
            })

    # Show sets added so far for this entry
    if st.session_state.current_sets:
        st.write("**Sets logged so far for this entry:**")
        preview_df = pd.DataFrame(st.session_state.current_sets)
        st.dataframe(preview_df, use_container_width=True, hide_index=True)

        if st.button("Remove last set"):
            st.session_state.current_sets.pop()
            st.rerun()

    notes = st.text_area("Notes (optional, applies to this whole entry)")

    st.divider()
    save_col, clear_col = st.columns([1, 1])
    with save_col:
        if st.button("Save Entry to Sheet", type="primary", disabled=len(st.session_state.current_sets) == 0):
            rows_to_insert = []
            for s in st.session_state.current_sets:
                rows_to_insert.append([
                    str(workout_date),
                    workout_type,
                    exercise,
                    s["Set"],
                    s["Reps"],
                    s["Weight"],
                    s["Duration (sec)"],
                    notes,
                ])
            sheet.append_rows(rows_to_insert)
            clear_cache()
            st.success(f"Saved {len(rows_to_insert)} set(s) for {exercise} to your Google Sheet!")
            st.session_state.current_sets = []
            st.rerun()
    with clear_col:
        if st.button("Clear entry without saving"):
            st.session_state.current_sets = []
            st.rerun()

# =========================================================
# TAB 2: HISTORY & PROGRESS (+ edit/delete)
# =========================================================
with tab_history:
    st.header("History & Progress")

    df = load_data()

    if df.empty:
        st.info("No workouts logged yet.")
    else:
        # Make sure expected columns exist even if sheet is missing some
        for col in HEADERS:
            if col not in df.columns:
                df[col] = None

        all_exercises = sorted(df["Exercise"].dropna().unique().tolist())
        selected_exercise = st.selectbox("Filter by exercise", ["All"] + all_exercises)

        filtered_df = df if selected_exercise == "All" else df[df["Exercise"] == selected_exercise]

        st.subheader("Progress Chart")
        if selected_exercise != "All" and not filtered_df.empty:
            chart_df = filtered_df.copy()
            chart_df["Date"] = pd.to_datetime(chart_df["Date"], errors="coerce")
            is_time = selected_exercise in TIME_BASED_EXERCISES
            metric_col = "Duration (sec)" if is_time else "Weight"
            chart_df = chart_df.sort_values("Date")
            if chart_df[metric_col].notna().any():
                st.line_chart(chart_df.set_index("Date")[metric_col])
            else:
                st.write("Not enough data yet for a chart.")
        else:
            st.caption("Pick a specific exercise above to see its progress chart.")

        st.subheader("All Logged Entries")
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

        # ---------------- Edit / Delete ----------------
        st.subheader("Edit or Delete an Entry")
        st.caption("Select a row below using its sheet row number, then edit fields or delete it.")

        # sheet rows are 1-indexed and row 1 is the header, so data row i corresponds to sheet row i+2
        df_display = df.reset_index(drop=True)
        df_display["Sheet Row"] = df_display.index + 2

        row_options = df_display.apply(
            lambda r: f"Row {r['Sheet Row']}: {r['Date']} | {r['Cycle Day']} | {r['Exercise']} | Set {r['Set']}",
            axis=1,
        ).tolist()

        if row_options:
            selected_row_label = st.selectbox("Select entry", row_options)
            selected_sheet_row = int(selected_row_label.split("Row ")[1].split(":")[0])
            record = df_display[df_display["Sheet Row"] == selected_sheet_row].iloc[0]

            with st.form("edit_form"):
                e_date = st.text_input("Date", value=str(record["Date"]))
                e_type = st.text_input("Cycle Day", value=str(record["Cycle Day"]))
                e_exercise = st.text_input("Exercise", value=str(record["Exercise"]))
                e_set = st.text_input("Set", value=str(record["Set"]))
                e_reps = st.text_input("Reps", value=str(record["Reps"]))
                e_weight = st.text_input("Weight", value=str(record["Weight"]))
                e_duration = st.text_input("Duration (sec)", value=str(record["Duration (sec)"]))
                e_notes = st.text_input("Notes", value=str(record["Notes"]))

                update_col, delete_col = st.columns(2)
                update_clicked = update_col.form_submit_button("Update Entry")
                delete_clicked = delete_col.form_submit_button("Delete Entry", type="secondary")

            if update_clicked:
                new_row = [e_date, e_type, e_exercise, e_set, e_reps, e_weight, e_duration, e_notes]
                sheet.update(f"A{selected_sheet_row}:H{selected_sheet_row}", [new_row])
                clear_cache()
                st.success(f"Row {selected_sheet_row} updated.")
                st.rerun()

            if delete_clicked:
                sheet.delete_rows(selected_sheet_row)
                clear_cache()
                st.success(f"Row {selected_sheet_row} deleted.")
                st.rerun()
        else:
            st.write("No entries to edit yet.")

# =========================================================
# TAB 3: REST TIMER
# =========================================================
with tab_timer:
    st.header("Rest Timer")
    default_seconds = st.number_input("Rest duration (seconds)", min_value=5, max_value=600, value=60, step=5)

    if st.button("Start Timer"):
        placeholder = st.empty()
        remaining = default_seconds
        while remaining > 0:
            mins, secs = divmod(remaining, 60)
            placeholder.metric("Time Remaining", f"{mins:02d}:{secs:02d}")
            time.sleep(1)
            remaining -= 1
        placeholder.metric("Time Remaining", "00:00")
        st.success("Rest complete — back to it!")
