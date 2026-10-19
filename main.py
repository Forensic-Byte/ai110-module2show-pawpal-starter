"""CLI demonstration of PawPal+'s multi-pet scheduling logic."""
from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


def main() -> None:
    """Build sample pets and print a prioritized daily plan."""
    today = date.today()
    owner = Owner("Jordan", preferences=["morning walks"])
    biscuit = Pet("Biscuit", "dog", "Golden Retriever")
    mochi = Pet("Mochi", "cat", "Tabby")
    owner.add_pet(biscuit)
    owner.add_pet(mochi)
    biscuit.add_task(Task("Morning walk", "08:00", "daily", 30, "high", today, task_id=1))
    mochi.add_task(Task("Breakfast", "07:30", "daily", 10, "high", today, task_id=1))
    biscuit.add_task(Task("Grooming", "11:00", "weekly", 20, "low", today, task_id=2))
    scheduler = Scheduler(owner)
    plan, skipped = scheduler.build_daily_plan(today, available_minutes=90)

    print(f"Today's Schedule for {owner.name} — {today.isoformat()}")
    for item in plan:
        print(
            f"  {item.scheduled_time} — {item.pet_name}: {item.task.description} "
            f"({item.task.duration_minutes} min, {item.task.priority} priority)"
        )
    if skipped:
        print("Not scheduled:")
        for message in skipped:
            print(f"  {message}")
    conflicts = scheduler.detect_conflicts(today)
    if conflicts:
        print("Conflict warnings:")
        for warning in conflicts:
            print(f"  {warning}")
    else:
        print("Conflict warnings: none")


if __name__ == "__main__":
    main()
