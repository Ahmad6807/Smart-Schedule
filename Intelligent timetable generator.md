# Product Requirements Document (PRD)

## SmartSchedule: Intelligent University Timetable Generator

**Version:** 1.0  
**Date:** 2026-08-31  
**Author:** Product Team  
**Status:** Draft

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)  
2. [Problem Statement](#2-problem-statement)  
3. [Goals and Objectives](#3-goals-and-objectives)  
4. [Target Audience](#4-target-audience)  
5. [Scope](#5-scope)  
   - 5.1 In-Scope  
   - 5.2 Out-of-Scope  
6. [Functional Requirements](#6-functional-requirements)  
   - 6.1 User Management & Course Selection  
   - 6.2 Constraint Definition  
   - 6.3 Timetable Generation  
   - 6.4 Clash Detection & Resolution  
   - 6.5 Schedule Visualization  
   - 6.6 Export & Sharing  
7. [Non-Functional Requirements](#7-non-functional-requirements)  
8. [User Stories / Use Cases](#8-user-stories--use-cases)  
9. [System Architecture](#9-system-architecture)  
10. [Data Model](#10-data-model)  
11. [Algorithm Design](#11-algorithm-design)  
    - 11.1 Core Constraint Satisfaction Problem (CSP)  
    - 11.2 Heuristic Search for Optimization  
    - 11.3 Alternative Slot Recommendation  
    - 11.4 Complexity & Performance  
12. [UI/UX Design](#12-uiux-design)  
13. [Integration Points](#13-integration-points)  
14. [Security & Privacy](#14-security--privacy)  
15. [Performance Metrics](#15-performance-metrics)  
16. [Testing Plan](#16-testing-plan)  
17. [Milestones & Timeline](#17-milestones--timeline)  
18. [Open Questions](#18-open-questions)  
19. [Appendix](#19-appendix)  

---

## 1. Executive Summary

SmartSchedule is a Python-based desktop application that helps university students generate **clash-free weekly timetables** by intelligently scheduling their selected courses. The application takes as input a list of courses (with their available time slots and rooms) and automatically produces an optimal timetable that respects all hard constraints (no overlapping classes) and soft constraints (student preferences such as avoiding early mornings, minimizing gaps, etc.).

Unlike manual checking, SmartSchedule uses **Constraint Satisfaction Problem (CSP)** techniques combined with **heuristic search** to explore possible schedules efficiently. It provides interactive clash resolution suggestions and allows students to refine their preferences to obtain the best possible timetable. The final schedule can be visualized in a clean weekly view and exported to CSV for sharing or printing.

The product aims to reduce the time and stress associated with course registration, prevent enrollment errors, and improve overall student satisfaction with their academic schedule.

---

## 2. Problem Statement

University students often face the following challenges when selecting courses for an upcoming semester:

- **Manual clash checking**: Students must manually compare class times across multiple courses, which is error-prone and time-consuming, especially when considering courses from previous semesters (retakes) or courses with multiple sections.
- **Complex constraints**: Courses may have multiple sections with different time slots, rooms, and instructors. Some sections may be full, while others may have prerequisites or restrictions.
- **Preference conflicts**: Students may have personal preferences (e.g., no 8 AM classes, avoiding long gaps, keeping Fridays free) that are hard to satisfy manually.
- **Limited guidance**: University registration systems often do not provide proactive clash detection or alternative suggestions when a desired schedule is impossible.

As a result, students may end up with suboptimal schedules, miss important classes, or face last-minute changes during add/drop periods. SmartSchedule addresses these issues by providing an automated, intelligent tool that generates optimal, clash-free timetables while considering user preferences.

---

## 3. Goals and Objectives

**Primary Goals:**

1. **Automate clash detection and resolution** for course schedules.
2. **Generate optimal timetables** that satisfy all hard constraints and maximize soft constraint satisfaction.
3. **Provide an intuitive user interface** for inputting courses, constraints, and viewing results.
4. **Offer alternative suggestions** when a perfect schedule cannot be achieved.
5. **Support export to common formats** (CSV) for record-keeping and sharing.

**Measurable Objectives:**

- Reduce time spent on manual clash checking by **90%**.
- Achieve a **95% success rate** in finding a valid timetable when one exists.
- Provide at least **three alternative suggestions** when the initial preferences cannot be met.
- Ensure the application runs on standard student laptops (Windows/macOS/Linux) with minimal resource usage.

---

## 4. Target Audience

- **Primary Users**: University students (undergraduate and graduate) who are selecting courses for an upcoming semester.
- **Secondary Users**: Academic advisors or peer mentors who assist students in course planning.

**User Characteristics:**

- Basic computer literacy.
- Familiarity with course registration processes.
- Varying technical expertise; the application must be simple and intuitive.

---

## 5. Scope

### 5.1 In-Scope

- Desktop application (Python-based, cross-platform).
- Input of courses with multiple sections, each having time slots, days, room, and instructor.
- Definition of hard constraints: no time overlaps between selected sections.
- Definition of soft constraints: time preferences, day preferences, gap minimization, preferred instructors (optional).
- Automatic generation of a clash-free timetable using CSP and optimization algorithms.
- Interactive clash resolution: if a clash is detected, suggest alternative sections or time slots.
- Weekly timetable visualization (grid view).
- Export timetable to CSV.
- Local data storage (JSON/SQLite) for user profiles and saved schedules.

### 5.2 Out-of-Scope

- Web-based or mobile application (future enhancement).
- Integration with university registration systems (API calls) for real-time seat availability.
- Handling of non-time constraints such as prerequisite enforcement (unless provided explicitly by user).
- Multi-user collaboration or sharing via cloud.
- Automatic enrollment or course registration.
- Support for irregular timetables (e.g., bi-weekly classes, rotating schedules).
- Advanced optimization for room allocation across the university (this is a per-student tool, not a university-wide scheduler).

---

## 6. Functional Requirements

### 6.1 User Management & Course Selection

- **FR-1.1**: The application shall allow users to create a profile (optional) to save their course selections and preferences locally.
- **FR-1.2**: Users can manually enter course information: course code, course name, section, days of the week, start time, end time, room, and instructor.
- **FR-1.3**: Users can add multiple sections for the same course (e.g., Lecture, Tutorial, Lab) and mark whether a section is mandatory or optional.
- **FR-1.4**: Users can import a list of courses from a CSV file (with predefined columns: Course Code, Section, Day, Start Time, End Time, Room, Instructor).
- **FR-1.5**: The system shall validate input times (start < end, valid time format, valid day abbreviation) and provide error messages for invalid entries.

### 6.2 Constraint Definition

- **FR-2.1**: The system shall automatically enforce the **hard constraint**: no two selected sections may overlap in time on the same day.
- **FR-2.2**: Users can define **soft constraints** (preferences) with weights:
  - Avoid specific days (e.g., no classes on Friday).
  - Avoid early morning (before 9 AM) or late evening (after 6 PM) classes.
  - Minimize gaps between consecutive classes on the same day.
  - Prefer certain instructors (if sections with different instructors are available).
  - Prefer a balanced schedule (even distribution of classes across days).
- **FR-2.3**: Users can assign a priority (High, Medium, Low) to each soft constraint to influence optimization.

### 6.3 Timetable Generation

- **FR-3.1**: Upon user request (e.g., clicking "Generate Timetable"), the system shall attempt to find a valid assignment of course sections to time slots that satisfies all hard constraints.
- **FR-3.2**: If multiple valid schedules exist, the system shall rank them based on the total weighted satisfaction of soft constraints and present the best one (or top N).
- **FR-3.3**: The generation process shall be **deterministic** (same input yields same output) unless randomness is explicitly requested (e.g., for exploring alternatives).
- **FR-3.4**: The system shall handle up to **50 courses/sections** without significant performance degradation (target < 5 seconds on a standard laptop).
- **FR-3.5**: The system shall support both **exact solving** (guaranteed clash-free if possible) and **approximate solving** (heuristic) when exact solving is computationally expensive.

### 6.4 Clash Detection & Resolution

- **FR-4.1**: Before finalizing, if the user manually selects sections that cause overlaps, the system shall highlight the conflicting sessions.
- **FR-4.2**: The system shall offer alternative sections for the same course (if available) that would resolve the conflict, ranked by minimal change to the current selection and soft constraint satisfaction.
- **FR-4.3**: If no alternative sections exist, the system shall suggest dropping one of the conflicting courses or adjusting other soft constraints (e.g., allowing gaps).
- **FR-4.4**: The user can accept or reject each suggestion; upon acceptance, the schedule is updated automatically.

### 6.5 Schedule Visualization

- **FR-5.1**: The application shall display the generated timetable in a **weekly grid** (rows = time slots, columns = days of the week).
- **FR-5.2**: Each course block shall show course code, section, room, and instructor (if available), with color coding per course.
- **FR-5.3**: The grid shall support zooming (time granularity of 30 minutes by default, adjustable to 15 or 60 minutes).
- **FR-5.4**: Users can hover over a block to see full details (tooltip).
- **FR-5.5**: The view shall clearly indicate any remaining clashes (if any) with red highlighting.

### 6.6 Export & Sharing

- **FR-6.1**: Users can export the timetable to a CSV file with columns: Day, Start Time, End Time, Course Code, Section, Room, Instructor.
- **FR-6.2**: Export shall include all selected sections, even if they have no assigned time (e.g., asynchronous online courses).
- **FR-6.3**: Users can print the timetable directly from the application (using system print dialog).
- **FR-6.4**: Users can save the current schedule (including preferences) to a local project file (JSON) for later editing.

---

## 7. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Performance** | Timetable generation for up to 50 sections completes in < 5 seconds on a mid-range laptop. |
| **Usability** | The UI must be intuitive; first-time users can generate a schedule within 10 minutes. |
| **Reliability** | The system must never produce a schedule that violates hard constraints (when exact solving). |
| **Portability** | Runs on Windows 10+, macOS 10.14+, and major Linux distributions (Python 3.8+). |
| **Maintainability** | Code modular, well-documented, with unit tests covering core algorithm logic. |
| **Security** | All data stored locally; no external network calls unless explicit user action (e.g., import). |
| **Scalability** | Architecture should allow future integration with web services or larger datasets. |
| **Accessibility** | Basic keyboard navigation and screen reader compatibility for visually impaired users. |

---

## 8. User Stories / Use Cases

1. **As a student**, I want to add my selected courses with their available sections so that I can see potential time conflicts.
2. **As a student**, I want to specify that I do not want classes before 10 AM so that my schedule aligns with my preferences.
3. **As a student**, I want the system to automatically find a clash-free combination of sections for all my courses so that I don't have to manually check overlaps.
4. **As a student**, when there is a conflict, I want to see alternative sections that would resolve it so that I can make an informed decision.
5. **As a student**, I want to view my final timetable in a weekly grid so that I can easily understand my weekly routine.
6. **As a student**, I want to export my timetable to CSV so that I can share it with my advisor or import it into my calendar app.
7. **As a student**, I want to save my course list and preferences so that I can come back later and modify them without re-entering everything.

---

## 9. System Architecture

SmartSchedule will be a **desktop application** built with Python. The architecture follows a **Model-View-Controller (MVC)** pattern to separate concerns.

**High-level components:**

- **UI Layer (View)**: Built using a GUI framework (e.g., PyQt5, Tkinter, or PySide6). Responsible for user interaction, input forms, timetable display, and export dialogs.
- **Controller**: Handles user actions, calls the scheduler engine, and updates the view.
- **Model**: Contains data structures for courses, sections, constraints, and schedules. Includes a data access layer for saving/loading JSON files and CSV import/export.
- **Scheduler Engine (Core Logic)**:
  - **Constraint Satisfaction Module**: Implements backtracking, forward checking, and arc consistency to find a valid assignment.
  - **Optimization Module**: Uses heuristic search (e.g., A* with a heuristic that combines soft constraint satisfaction) or local search (simulated annealing) to refine schedules.
  - **Alternative Suggestion Module**: When conflicts occur, uses a local search to find minimal changes (swap sections, drop courses) that restore feasibility.
- **Utilities**: Time parsing, day normalization, logging.

**Technology Stack:**

- Python 3.8+
- GUI: PyQt5 (preferred for rich widgets and cross-platform support)
- Data storage: JSON files (simple) or SQLite (optional for larger data)
- Algorithm libraries: Custom implementation (no external dependencies) to keep the app lightweight.

**Diagram (text):**

```
User --> GUI (View) <--> Controller <--> Scheduler Engine
                                         |
                                         v
                                    Model (Data)
                                         |
                                         v
                                Local Storage (JSON)
```

---

## 10. Data Model

The core entities are:

- **Course**: `course_code` (unique), `name`, `credits` (optional).
- **Section**: `section_id`, `course_code` (FK), `type` (Lecture/Tutorial/Lab), `instructor`, `room`, `days` (list of weekdays), `start_time`, `end_time`. Each section represents a specific offering of a course at a given time.
- **UserPreference**: `user_id`, `preference_type` (e.g., avoid_day, avoid_time, min_gap, prefer_instructor), `value` (e.g., "Friday", "09:00-10:00", "3", "Dr. Smith"), `weight` (1-10).
- **Schedule**: A mapping of selected section IDs to their assigned days/times (essentially the chosen sections). Could be derived from selected sections; no separate storage needed.
- **SelectedCourse**: A user's intention to take a course; they may select one or more sections for that course (e.g., lecture + lab). The system must choose one section per `type` (if mandatory) or none (if optional).

**Relationships:**

- A Course can have multiple Sections.
- A Section belongs to exactly one Course.
- A User can have many UserPreferences.
- A User can have many SelectedCourses (each linking to a Course and specifying which section types are required).

**Example JSON structure for saved project:**

```json
{
  "user": {"name": "John Doe", "id": "local_user"},
  "selected_courses": [
    {
      "course_code": "CS101",
      "required_sections": ["Lecture", "Tutorial"],
      "selected_sections": ["CS101-LEC-01", "CS101-TUT-02"]
    },
    {
      "course_code": "MATH201",
      "required_sections": ["Lecture"],
      "selected_sections": ["MATH201-LEC-01"]
    }
  ],
  "preferences": [
    {"type": "avoid_day", "value": "Friday", "weight": 5},
    {"type": "min_gap", "value": "2", "weight": 3}
  ],
  "schedule": [
    {"section_id": "CS101-LEC-01", "day": "Monday", "start": "09:00", "end": "10:30", "room": "A101"}
  ]
}
```

---

## 11. Algorithm Design

The core scheduling problem is a **Constraint Satisfaction Problem (CSP)** where variables are the required section types for each selected course, and the domain for each variable is the list of available sections (time/room/instructor) that fulfill that type. The hard constraint is that no two assigned sections may overlap in time on the same day.

Optionally, we can extend the CSP to include other constraints (e.g., no more than N hours of class per day) as soft constraints in the optimization phase.

### 11.1 Core Constraint Satisfaction Problem (CSP)

**Variables**: `V = {v1, v2, ..., vk}` where `vi` represents a required section slot for a course (e.g., "CS101 Lecture", "CS101 Tutorial", "MATH201 Lecture"). If a course requires both lecture and lab, they are separate variables but linked (must choose sections from the same course, though they could be different sections; no additional constraint).

**Domains**: Each variable `vi` has a domain `Di` consisting of all possible sections (instances) that belong to that course and type. Each section has an associated time block (day(s), start, end). The domain may be pruned by user preferences (e.g., exclude sections on Friday).

**Hard Constraints**: For any pair of variables `vi` and `vj`, the assigned sections must not overlap in time on any common day. Overlap is defined if both sections are scheduled on the same day and their time intervals intersect (strictly, `start_i < end_j` and `start_j < end_i`). Additionally, a section must be valid (not full, etc.) but seat availability is out of scope.

**Solving Approach**:

- Use **Backtracking Search** with **Forward Checking** and **MRV (Minimum Remaining Values)** heuristic to find a valid assignment.
- **Constraint Propagation**: Apply **Arc Consistency (AC-3)** before and during search to reduce domains.
- If a solution exists, backtracking will find it (given finite domains). The search space is usually small (few dozen variables, domains < 10), so exact solving is feasible.
- For larger instances (many sections with many possible times), we can switch to **DFS with iterative deepening** or **local search** (e.g., min-conflicts) if exact search times out (configurable threshold).

### 11.2 Heuristic Search for Optimization

After finding a valid schedule, we may have multiple solutions. We want to find the one that best satisfies soft constraints (preferences). We can treat this as an optimization problem over the set of valid assignments.

**Approach**: Use **A* search** over the space of partial assignments, where the cost function combines the number of satisfied soft constraints (weighted sum) and the heuristic estimates the remaining potential satisfaction. This is similar to finding the optimal solution in a CSP with preferences. However, A* may be memory-intensive; we can limit open list size or use **Beam Search** (keeping top k states at each depth).

Alternatively, we can generate multiple valid schedules via randomized backtracking (with randomness) and then score them using a **utility function**, selecting the best. This is simpler and often sufficient because the number of valid schedules is not huge.

**Utility Function**:

`Score(Schedule) = Σ (weight_i * satisfaction_i)` where `satisfaction_i` is a binary or continuous value indicating how well a preference is met (e.g., 1 if no class on Friday, else 0; or for gap minimization, a function of total gap hours). We normalize weights to 0-1.

**Local Search Refinement**: If the best schedule found is not optimal, we can apply **Simulated Annealing** or **Hill Climbing with random restarts** to tweak section choices (swap one section for another in the same domain) to improve the score while maintaining hard constraints. This is useful when the search space is large and exact optimization is expensive.

### 11.3 Alternative Slot Recommendation

When the user manually selects sections that cause a clash, or when no complete schedule exists, we need to suggest alternatives.

**For a detected clash between two selected sections A and B:**

- Identify the courses involved and their other available sections.
- For each conflicting course, propose swapping its section with an alternative section that does not conflict with the rest of the schedule (or at least reduces conflicts).
- Rank alternatives by:
  1. Resolving the most conflicts (hard constraint satisfaction).
  2. Minimal change (number of sections changed).
  3. Soft constraint satisfaction score of the new schedule.
- Use a **local search** (e.g., generate all single-section substitutions and evaluate) because the number of alternatives per course is small.
- If no single substitution resolves all conflicts, suggest combinations (two changes) or dropping a course.

The recommendation engine should present the top 3 options to the user with clear explanations (e.g., "Replace MATH201 Lecture Section 01 with Section 02 (Tue 10-11:30) to resolve clash with CS101 Lecture").

### 11.4 Complexity & Performance

- Number of variables (required section types) typically < 15.
- Domain size per variable usually < 10 sections.
- Worst-case search space: `10^15` (too large for brute force) but constraint propagation drastically reduces it.
- Backtracking with forward checking and MRV can solve most student schedules in milliseconds because real-world constraints (specific days/times) prune quickly.
- The optimization step (if using A* or beam search) will still be fast due to small depth.
- We will set a time limit (e.g., 10 seconds) for the solver; if exceeded, the best found solution (or a heuristic solution) is returned with a warning.

---

## 12. UI/UX Design

The application will have a simple, clean interface with the following main screens/tabs:

### Screen 1: Course Input

- **Course List Panel**: Shows added courses and their sections.
- **Add Course Form**: Fields: Course Code, Course Name, Section Type (Lecture/Tutorial/Lab), Instructor, Room, Day(s) multi-select (Mon-Fri), Start Time, End Time.
- **Import CSV** button.
- **Save/Load Project** buttons.

### Screen 2: Preferences

- Checkboxes and sliders for preferences:
  - "Avoid Friday classes" (checkbox)
  - "Earliest start time" (dropdown: 8:00 AM, 9:00 AM, etc.)
  - "Latest end time" (dropdown)
  - "Maximum gap between classes" (spinbox in hours)
  - "Preferred instructors" (list of instructor names with priority)
- Each preference has a weight slider (1-10).

### Screen 3: Timetable Generation

- **"Generate Timetable"** button (prominent).
- After generation, the weekly grid appears.
- Grid columns: Monday-Friday, rows: time slots (30-min increments from 7:00 to 22:00).
- Course blocks color-coded; clicking a block shows details.
- If clashes exist, red outline and warning banner.

### Screen 4: Clash Resolution Dialog (Modal)

- When conflicts are detected (manual selection or generation failure), a dialog lists the conflicts and suggested resolutions in a table:
  - "Conflict: CS101 Lecture (Mon 9-10) overlaps with MATH201 Lecture (Mon 9-10)"
  - Suggested actions: "Replace MATH201 Lecture with Section 02 (Tue 11-12)" with Accept/Reject buttons.
- User can accept all suggestions or choose individually.

### Screen 5: Export / Print

- Buttons: "Export CSV", "Print", "Save Schedule as JSON".
- File save dialog with default filename `timetable_YYYYMMDD.csv`.

**Design Principles:**

- Minimal clicks: most actions accessible from main window.
- Clear visual feedback: color coding, tooltips, progress indicators during generation.
- Error prevention: form validation, confirm dialogs for destructive actions.
- Responsive layout: window resizable, grid scrollable.

---

## 13. Integration Points

- **CSV Import/Export**: The application will support importing course data from CSV files (format: `course_code,section_type,day,start_time,end_time,room,instructor`). Export uses a similar format.
- **Future**: Could integrate with university APIs for real-time course catalog and seat availability (not in current scope).
- **System Calendar**: Optional export to iCalendar (.ics) format could be added later.
- **No external dependencies** for core functionality; all data stored locally.

---

## 14. Security & Privacy

- **Local Storage Only**: All user data (courses, preferences, schedules) are stored locally on the user's machine in JSON files. No data is transmitted over the network.
- **File Permissions**: The application will create files with default user permissions; no sensitive information is stored (only course times and preferences).
- **No Authentication**: Since it's a single-user desktop app, no login is required. However, we may add optional profile names for organization.
- **Data Integrity**: The application will validate all imported data to prevent crashes or malformed schedules.
- **Error Handling**: Robust try-catch blocks and user-friendly error messages.

---

## 15. Performance Metrics

- **Time to generate schedule**: ≤ 5 seconds for up to 50 sections (measured on a reference machine with Intel i5, 8GB RAM).
- **Memory usage**: ≤ 200 MB during normal operation.
- **Startup time**: ≤ 3 seconds.
- **UI responsiveness**: All interactions (except generation) respond within 100 ms.
- **Solver success rate**: ≥ 95% of test cases (with at least one valid schedule) produce a valid schedule within the time limit.

---

## 16. Testing Plan

**Unit Tests:**

- Time overlap detection function.
- Day parsing and normalization.
- Constraint propagation (AC-3) correctness.
- Backtracking solver finds solution for known CSP instances.
- Utility function scoring.
- CSV import/export parsing.

**Integration Tests:**

- End-to-end: Add courses, generate timetable, export CSV, reload project.
- Clash detection and suggestion generation with mock data.
