"""Behavior checks for PawPal+'s domain model and scheduling algorithms."""
from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task


@pytest.fixture
def household():
    owner = Owner("Alex")
    owner.add_pet(Pet("Mochi", "cat"))
    owner.add_pet(Pet("Biscuit", "dog"))
    return owner


def test_mark_complete_changes_status():
    task = Task("Feed", "08:00")
    task.mark_complete()
    assert task.completed is True


def test_adding_task_increases_pet_task_count(household):
    pet = household.pets[0]
    pet.add_task(Task("Feed", "08:00"))
    assert len(pet.tasks) == 1


def test_scheduler_reads_tasks_across_all_pets(household):
    household.pets[0].add_task(Task("Feed", "08:00"))
    household.pets[1].add_task(Task("Walk", "09:00"))
    assert len(Scheduler(household).sort_by_time()) == 2


def test_sorting_is_chronological(household):
    tasks = [Task("Later", "17:30"), Task("Early", "07:05"), Task("Mid", "12:00")]
    assert [task.description for task in Scheduler(household).sort_by_time(tasks)] == [
        "Early", "Mid", "Later"
    ]


def test_filter_by_pet_completion_and_date(household):
    today = date.today()
    task = Task("Feed", "08:00", due_date=today)
    task.mark_complete()
    household.pets[0].add_task(task)
    household.pets[1].add_task(Task("Walk", "09:00", due_date=today))
    result = Scheduler(household).filter_tasks(pet_name="mochi", completed=True, due_on=today)
    assert [(pet.name, item.description) for pet, item in result] == [("Mochi", "Feed")]


def test_daily_completion_creates_next_day_occurrence(household):
    pet = household.pets[0]
    task = Task("Medication", "08:00", "daily", due_date=date.today(), task_id=1)
    pet.add_task(task)
    next_task = Scheduler(household).mark_task_complete(pet.name, task.task_id)
    assert task.completed
    assert next_task is not None
    assert next_task.due_date == date.today() + timedelta(days=1)
    assert not next_task.completed
    assert len(pet.tasks) == 2


def test_weekly_completion_advances_seven_days(household):
    pet = household.pets[0]
    task = Task("Brush", "10:00", "weekly", due_date=date.today(), task_id=1)
    pet.add_task(task)
    next_task = Scheduler(household).mark_task_complete(pet.name, 1)
    assert next_task.due_date == date.today() + timedelta(days=7)


def test_conflicts_detect_duration_overlap(household):
    today = date.today()
    household.pets[0].add_task(Task("Walk", "08:00", due_date=today, duration_minutes=30))
    household.pets[1].add_task(Task("Feed", "08:15", due_date=today, duration_minutes=10))
    conflicts = Scheduler(household).detect_conflicts(today)
    assert len(conflicts) == 1
    assert "overlaps" in conflicts[0]


def test_daily_plan_respects_budget_and_prioritizes(household):
    today = date.today()
    household.pets[0].add_task(Task("Low", "07:00", due_date=today, duration_minutes=20, priority="low"))
    household.pets[1].add_task(Task("Urgent", "09:00", due_date=today, duration_minutes=15, priority="high"))
    plan, skipped = Scheduler(household).build_daily_plan(today, available_minutes=20)
    assert [item.task.description for item in plan] == ["Urgent"]
    assert len(skipped) == 1 and "Low" in skipped[0]


def test_invalid_time_is_rejected():
    with pytest.raises(ValueError, match="HH:MM"):
        Task("Feed", "25:90")
