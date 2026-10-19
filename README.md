# PawPal+

PawPal+ is a pet care planner built with Python, dataclasses, and Streamlit. It keeps care tasks for multiple pets, prioritizes the work that fits an owner's available time, and explains what the plan includes.

## Features

- Add pets with a name, species, and optional breed.
- Schedule care tasks with a due date, preferred time, duration, priority, and one-time/daily/weekly frequency.
- Generate a daily plan across pets within a chosen time budget. High-priority tasks are considered first; selected items are shown with the reason they fit.
- See warnings for tasks whose time intervals overlap, including overlaps between pets.
- Complete daily and weekly tasks to automatically add their next occurrence.
- Filter tasks in the backend by pet, completion status, and due date.
- View and complete household tasks in the Streamlit UI.

## Run PawPal+

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

The app starts with a sample household. Add pets in the sidebar, add their tasks, choose a date and time budget, and select **Generate schedule**. The task list lets you mark recurring care complete; the next occurrence is then added to that pet.

## Implementation summary

`Task` stores the activity, its due date/time, duration, priority, recurrence, and completion state. `Pet` owns its task list. `Owner` manages multiple pets and supplies all pet-task pairs through `get_all_tasks()`. `Scheduler` reads tasks through that owner method, then sorts and filters them, constructs a time-budgeted plan, checks overlaps, and advances recurrence when a task is completed. `ScheduledItem` packages each selected task with its planned time and a short reason. `app.py` stores the owner in Streamlit session state so UI actions preserve household data during the session.

## Smarter Scheduling

| Feature | Method | Behavior |
|---|---|---|
| Sorting | `Scheduler.sort_by_time()` | Orders task objects by validated 24-hour `HH:MM` time. |
| Filtering | `Scheduler.filter_tasks()` | Filters household tasks by pet name, completion state, and due date. |
| Time budget and priority | `Scheduler.build_daily_plan()` | Considers high priority first, fits tasks into the available minute budget, and reports tasks that do not fit. |
| Conflict detection | `Scheduler.detect_conflicts()` | Warns when task intervals overlap on the same date, including between different pets. |
| Recurring tasks | `Task.next_occurrence()` and `Scheduler.mark_task_complete()` | Completing a daily/weekly task adds the next date's task; one-time tasks do not repeat. |

The planner treats duration as continuous scheduled time from the selected start. The task's preferred time is used for tie-breaking within a priority, while the generated plan packs selected tasks sequentially so it can enforce a single time budget.

## Demo Walkthrough

1. Enter an owner name and add each pet from the sidebar.
2. Schedule care tasks, choosing each pet, a date, preferred time, duration, priority, and recurrence.
3. Choose a plan date, available minutes, and start time, then generate the plan. Tasks are listed across pets with a reason for inclusion.
4. If two tasks occupy overlapping intervals, read the warning under the plan. Tasks that exceed the remaining budget are listed as skipped.
5. In **All tasks**, mark a daily or weekly task complete. The app records the completed instance and adds the next occurrence.

## CLI sample

Run `python main.py` to see the backend operate across two pets:

```text
Today's Schedule for Jordan — 2026-10-19
  08:00 — Mochi: Breakfast (10 min, high priority)
  08:10 — Biscuit: Morning walk (30 min, high priority)
  08:40 — Biscuit: Grooming (20 min, low priority)
Conflict warnings: none
```

The displayed date follows the computer's current date; the times and task details are fixed sample data.

## Testing PawPal+

Run the automated suite with:

```bash
python -m pytest
```

Tests cover task completion and addition, multi-pet retrieval, chronological sorting, filtering, daily and weekly recurrence, duration overlap detection, time-budget/priority behavior, and invalid time input. Local verification output:

```text
..........                                                               [100%]
10 passed in 0.02s
```

## Architecture

The final class diagram is in [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd). A compact initial draft is retained as [`diagrams/uml_draft.mmd`](diagrams/uml_draft.mmd).

## Project files

- `pawpal_system.py` — domain classes and scheduling algorithms
- `app.py` — Streamlit interface
- `main.py` — CLI demonstration
- `tests/test_pawpal.py` — automated tests
- `reflection.md` — design and AI collaboration reflection draft
