# PawPal+ Project Reflection

> This draft describes implementation decisions and verification that are visible in the project files and this Codex work session. Before submitting, add or adjust any account of your own experience with the course's VS Code assistant or your personal satisfaction/improvement points so the reflection remains accurate to you.

## 1. System Design

**a. Initial design**

The initial design separates the household, pets, care tasks, and scheduling work. `Owner` manages multiple `Pet` objects and exposes all their tasks through `get_all_tasks()`. Each `Pet` stores its own `Task` objects. `Scheduler` takes an `Owner` and performs household-wide operations. `ScheduledItem` is the display-ready result of planning, including the pet, task, assigned time, and explanation.

**b. Design changes**

The implementation added `ScheduledItem` after separating stored task data from a generated plan. A task's preferred time and its generated start time serve different purposes: preferred time helps order tasks of equal priority, while the planner packs selected tasks sequentially to enforce the available-time budget. The implementation also made the recurrence transition a Scheduler operation so completing a task can update both its completion state and its pet's task list.

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The planner considers due date, completion state, an optional pet filter, task priority, preferred time, duration, and the owner's available minutes. High-priority tasks are considered first. Within the same priority, preferred time orders the tasks. Tasks too long for the remaining budget are skipped with an explanation. The conflict checker compares actual time intervals, including duration, and flags overlaps across pets.

**b. Tradeoffs**

The daily planner uses a greedy priority-first rule rather than trying every possible task combination to maximize the number of tasks completed. This is straightforward to explain and predictable for a care plan, but a long high-priority task can use time that could otherwise fit several shorter tasks. Conflict checking is separate and reports overlaps based on each task's preferred time; the generated plan itself packs tasks from the chosen start time. A future version could make these schedule semantics more explicit in the UI and let owners select a planning strategy.

## 3. AI Collaboration

**a. How you used AI**

In this work session, Codex inspected the course requirements and the provided starter repository, then drafted the domain model, Streamlit integration, CLI demo, tests, diagrams, and documentation. The most useful context was the assignment's explicit requirements and the starter app, because they made the required classes, multi-pet behavior, UI fields, and test cases concrete.

**b. Judgment and verification**

The implementation keeps recurrence in `Scheduler.mark_task_complete()` rather than making a `Task` mutate a pet's task list. A `Task` can create a description of its next occurrence, while the scheduler assigns a new ID and adds it to the correct pet. This avoids giving a task responsibility for its containing pet. Verification is based on the test suite and the CLI demo; review the implementation and run both locally before submission.

Separate AI chats by design, implementation, and testing can keep the context focused and make it easier to trace suggestions back to a phase. This implementation happened in one Codex work session, so I did not personally use separate VS Code chat sessions here.

## 4. Testing and Verification

**a. What you tested**

The test suite checks completion and task addition, household-wide retrieval, chronological sorting, combined filtering, daily and weekly recurrence, duration-based conflict detection, budget behavior with priority ordering, and validation of malformed times. These tests cover core behavior and several boundaries that would otherwise create confusing schedules or silent errors.

**b. Confidence**

The local test run passed all 10 tests. That gives me good confidence in the backend rules covered by the suite, but it does not establish every Streamlit interaction or all date/time edge cases. Additional checks could cover daylight-saving transitions, simultaneous recurring tasks, empty households, and planner behavior when tasks have identical priorities and times.

## 5. Reflection

**a. What went well**

The code keeps the domain model independent from Streamlit, so the CLI demo and tests can exercise scheduling without launching a browser. The owner-level task method also makes multi-pet scheduling explicit rather than accidentally planning for only one pet.

**b. What you would improve**

A next iteration could let owners choose whether the plan follows preferred times exactly or packs tasks into a continuous block, and could add task editing/deletion with stable IDs. I would also test the interface manually with multiple pets and verify session-state behavior after reruns.

**c. Key takeaway**

The design shows why a human lead architect still needs to decide what the schedule means, set boundaries between classes, and verify generated code against requirements. AI can speed up drafting, but behavior such as recurrence and household-wide retrieval needs clear requirements and tests.
