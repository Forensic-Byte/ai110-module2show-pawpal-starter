"""Streamlit interface for the PawPal+ care planner."""
from datetime import date

import pandas as pd
import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan")
    st.session_state.owner.add_pet(Pet("Mochi", "cat"))
    st.session_state.next_task_id = 1

owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)

st.title("🐾 PawPal+")
st.caption("A thoughtful daily care plan for every pet in your household.")

with st.sidebar:
    st.header("Household")
    owner.name = st.text_input("Owner name", value=owner.name)
    st.write("Pets: " + (", ".join(p.name for p in owner.pets) if owner.pets else "none yet"))
    with st.form("add_pet_form", clear_on_submit=True):
        st.subheader("Add a pet")
        pet_name = st.text_input("Pet name")
        species = st.selectbox("Species", ["dog", "cat", "other"])
        breed = st.text_input("Breed (optional)")
        add_pet = st.form_submit_button("Add pet")
    if add_pet:
        try:
            owner.add_pet(Pet(pet_name.strip(), species, breed.strip()))
            st.success(f"Added {pet_name}.")
        except ValueError as exc:
            st.error(str(exc))

st.subheader("Schedule a care task")
if not owner.pets:
    st.info("Add a pet in the sidebar before scheduling care.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            task_pet = st.selectbox("Pet", [pet.name for pet in owner.pets])
            task_description = st.text_input("What needs to happen?", placeholder="Evening walk")
            due_on = st.date_input("Due date", value=date.today())
        with col2:
            task_time = st.time_input("Preferred time")
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        with col3:
            priority = st.selectbox("Priority", ["high", "medium", "low"])
            frequency = st.selectbox("Repeat", ["once", "daily", "weekly"])
        submitted = st.form_submit_button("Add task", type="primary")
    if submitted:
        try:
            pet = next(p for p in owner.pets if p.name == task_pet)
            pet.add_task(Task(
                task_description.strip(), task_time.strftime("%H:%M"), frequency,
                int(duration), priority, due_on, task_id=st.session_state.next_task_id,
            ))
            st.session_state.next_task_id += 1
            st.success(f"Scheduled {task_description} for {task_pet}.")
        except (ValueError, StopIteration) as exc:
            st.error(str(exc) or "Choose a pet and enter a task description.")

st.divider()
st.subheader("Today's care plan")
plan_date = st.date_input("Plan date", value=date.today(), key="plan_date")
left, right = st.columns([1, 2])
with left:
    available_minutes = st.number_input("Time available (minutes)", min_value=0, max_value=1440, value=240)
    start_at = st.time_input("Start planning at", value=__import__("datetime").time(8, 0))
    selected_pet = st.selectbox("Show tasks for", ["All pets"] + [p.name for p in owner.pets])
    make_plan = st.button("Generate schedule", type="primary")
with right:
    if make_plan:
        plan, skipped = scheduler.build_daily_plan(
            plan_date, int(available_minutes), start_at.strftime("%H:%M"),
            None if selected_pet == "All pets" else selected_pet,
        )
        if plan:
            st.success(f"{len(plan)} task(s) fit into the {available_minutes}-minute plan.")
            st.dataframe(pd.DataFrame([
                {"Time": item.scheduled_time, "Pet": item.pet_name,
                 "Care task": item.task.description, "Duration": f"{item.task.duration_minutes} min",
                 "Priority": item.task.priority.title(), "Why included": item.reason}
                for item in plan
            ]), use_container_width=True, hide_index=True)
        else:
            st.info("No outstanding tasks are due on this date.")
        for message in skipped:
            st.warning(message)
        conflicts = scheduler.detect_conflicts(plan_date)
        for warning in conflicts:
            st.warning(warning)
        if not conflicts:
            st.caption("No overlapping task times detected.")

st.divider()
st.subheader("All tasks")
if owner.get_all_tasks():
    for pet in owner.pets:
        if not pet.tasks:
            continue
        st.markdown(f"**{pet.name}** · {pet.species}")
        for task in sorted(pet.tasks, key=lambda t: (t.due_date, t.time)):
            cols = st.columns([3, 1.2, 1.2, 1.3, 1.5])
            cols[0].write(("✅ " if task.completed else "▫️ ") + task.description)
            cols[1].write(task.due_date.isoformat())
            cols[2].write(task.time)
            cols[3].write(f"{task.priority.title()} · {task.frequency}")
            if not task.completed and cols[4].button("Mark complete", key=f"complete-{pet.name}-{task.task_id}"):
                next_task = scheduler.mark_task_complete(pet.name, task.task_id)
                if next_task:
                    st.toast(f"Completed. Next occurrence: {next_task.due_date.isoformat()}.")
                else:
                    st.toast("Task completed.")
                st.rerun()
else:
    st.info("No care tasks yet. Add one above to get started.")
