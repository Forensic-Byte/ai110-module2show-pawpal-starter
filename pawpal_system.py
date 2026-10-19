"""Core domain model and scheduling logic for PawPal+."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime, time, timedelta
from typing import Iterable

PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


def _parse_time(value: str) -> time:
    """Parse a 24-hour HH:MM clock value and reject invalid input."""
    try:
        return datetime.strptime(value, "%H:%M").time()
    except (TypeError, ValueError) as exc:
        raise ValueError("Time must use 24-hour HH:MM format.") from exc


@dataclass
class Task:
    """A care activity with a due date, time, duration, and recurrence."""

    description: str
    time: str
    frequency: str = "once"
    duration_minutes: int = 15
    priority: str = "medium"
    due_date: date = field(default_factory=date.today)
    completed: bool = False
    task_id: int = 0

    def __post_init__(self) -> None:
        _parse_time(self.time)
        self.frequency = self.frequency.lower()
        self.priority = self.priority.lower()
        if self.frequency not in {"once", "daily", "weekly"}:
            raise ValueError("Frequency must be once, daily, or weekly.")
        if self.priority not in PRIORITY_RANK:
            raise ValueError("Priority must be low, medium, or high.")
        if not self.description.strip():
            raise ValueError("Task description cannot be empty.")
        if self.duration_minutes < 1:
            raise ValueError("Duration must be at least one minute.")

    def mark_complete(self) -> None:
        """Mark this task instance complete."""
        self.completed = True

    def next_occurrence(self) -> Task | None:
        """Return the next recurring instance, or None for one-time tasks."""
        if self.frequency == "once":
            return None
        delta = timedelta(days=1 if self.frequency == "daily" else 7)
        return replace(self, due_date=self.due_date + delta, completed=False, task_id=0)


@dataclass
class Pet:
    """A pet and the care tasks associated with it."""

    name: str
    species: str = "other"
    breed: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet."""
        self.tasks.append(task)


@dataclass
class Owner:
    """An owner who manages one or more pets and their shared preferences."""

    name: str
    pets: list[Pet] = field(default_factory=list)
    preferences: list[str] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's household."""
        if any(existing.name.casefold() == pet.name.casefold() for existing in self.pets):
            raise ValueError(f"A pet named {pet.name} already exists.")
        self.pets.append(pet)

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every pet-task pair managed by this owner."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]


@dataclass(frozen=True)
class ScheduledItem:
    """A task selected for a plan with its display time and explanation."""

    pet_name: str
    task: Task
    scheduled_time: str
    reason: str


@dataclass
class Scheduler:
    """Sort, filter, plan, and validate tasks across an owner's pets."""

    owner: Owner

    def sort_by_time(self, tasks: Iterable[Task] | None = None) -> list[Task]:
        """Return tasks ordered chronologically by their 24-hour time."""
        source = list(tasks) if tasks is not None else [task for _, task in self.owner.get_all_tasks()]
        return sorted(source, key=lambda task: (_parse_time(task.time), task.description.casefold()))

    def filter_tasks(
        self,
        *,
        pet_name: str | None = None,
        completed: bool | None = None,
        due_on: date | None = None,
    ) -> list[tuple[Pet, Task]]:
        """Filter household tasks by pet, completion, and optional date."""
        return [
            (pet, task)
            for pet, task in self.owner.get_all_tasks()
            if (pet_name is None or pet.name.casefold() == pet_name.casefold())
            and (completed is None or task.completed is completed)
            and (due_on is None or task.due_date == due_on)
        ]

    def detect_conflicts(self, due_on: date | None = None) -> list[str]:
        """Return warnings for overlapping tasks on the same date."""
        items = [
            (pet, task)
            for pet, task in self.owner.get_all_tasks()
            if not task.completed and (due_on is None or task.due_date == due_on)
        ]
        warnings: list[str] = []
        for index, (pet_a, task_a) in enumerate(items):
            start_a = datetime.combine(task_a.due_date, _parse_time(task_a.time))
            end_a = start_a + timedelta(minutes=task_a.duration_minutes)
            for pet_b, task_b in items[index + 1 :]:
                if task_a.due_date != task_b.due_date:
                    continue
                start_b = datetime.combine(task_b.due_date, _parse_time(task_b.time))
                end_b = start_b + timedelta(minutes=task_b.duration_minutes)
                if start_a < end_b and start_b < end_a:
                    warnings.append(
                        f"{pet_a.name}: {task_a.description} ({task_a.time}) overlaps "
                        f"{pet_b.name}: {task_b.description} ({task_b.time})."
                    )
        return warnings

    def mark_task_complete(self, pet_name: str, task_id: int) -> Task | None:
        """Complete a task and append its next daily or weekly occurrence."""
        pet = next((p for p in self.owner.pets if p.name == pet_name), None)
        if pet is None:
            raise ValueError(f"Pet {pet_name!r} was not found.")
        task = next((t for t in pet.tasks if t.task_id == task_id), None)
        if task is None:
            raise ValueError(f"Task {task_id} was not found for {pet_name}.")
        if task.completed:
            return None
        task.mark_complete()
        new_task = task.next_occurrence()
        if new_task is not None:
            new_task.task_id = max((t.task_id for t in pet.tasks), default=0) + 1
            pet.add_task(new_task)
        return new_task

    def build_daily_plan(
        self,
        due_on: date,
        available_minutes: int = 480,
        start_time: str = "08:00",
        pet_name: str | None = None,
    ) -> tuple[list[ScheduledItem], list[str]]:
        """Prioritize due tasks into a time budget and return schedule plus skips."""
        if available_minutes < 0:
            raise ValueError("Available minutes cannot be negative.")
        cursor = datetime.combine(due_on, _parse_time(start_time))
        remaining = available_minutes
        candidates = [
            (pet, task)
            for pet, task in self.owner.get_all_tasks()
            if not task.completed
            and task.due_date == due_on
            and (pet_name is None or pet.name.casefold() == pet_name.casefold())
        ]
        candidates.sort(
            key=lambda pair: (
                PRIORITY_RANK[pair[1].priority],
                _parse_time(pair[1].time),
                pair[0].name.casefold(),
                pair[1].description.casefold(),
            )
        )
        plan: list[ScheduledItem] = []
        skipped: list[str] = []
        for pet, task in candidates:
            if task.duration_minutes > remaining:
                skipped.append(
                    f"{pet.name}: {task.description} skipped ({task.duration_minutes} min; "
                    f"{remaining} min remain)."
                )
                continue
            display_time = cursor.strftime("%H:%M")
            reason = f"{task.priority.title()} priority; fits the remaining time budget."
            plan.append(ScheduledItem(pet.name, task, display_time, reason))
            cursor += timedelta(minutes=task.duration_minutes)
            remaining -= task.duration_minutes
        return plan, skipped
