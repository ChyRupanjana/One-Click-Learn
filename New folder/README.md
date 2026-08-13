# CodeLearn — Bilingual Coding Learning App

A desktop coding-learning application built with **Python + Tkinter**, storing
all data in a local **JSON** file, and using the free **Piston API** for
real-time, sandboxed code execution. Built for beginners — no web
frontend/backend/database required.

## Features
- Lessons with bilingual content (Bangla / English toggle)
- In-app code editor with a Run button
- Real-time code execution via Piston API (no local compiler needed)
- MCQ quizzes with instant feedback
- XP, streak, and level system
- Progress dashboard with matplotlib charts
- PDF certificate generation (via reportlab) after completing all lessons

## Project Structure
```
CodeLearnApp/
├── main.py                  # Tkinter GUI app (entry point)
├── data_manager.py          # JSON load/save, progress logic
├── code_runner.py           # Piston API calls (real-time code execution)
├── progress_chart.py        # matplotlib chart embedded in Tkinter
├── certificate_generator.py # PDF certificate generation (reportlab)
├── data.json                # Lessons, quizzes, and user progress (JSON storage)
├── requirements.txt
└── README.md
```

## Setup

1. Make sure you have Python 3.8+ installed.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the app:
   ```
   python main.py
   ```

> Note: Code execution requires an internet connection, since it calls the
> free Piston API (`https://emkc.org/api/v2/piston/execute`).

## How It Works
- **Lessons & Quizzes**: stored as a list of dictionaries in `data.json`.
  `data_manager.py` handles all reading/writing — no database engine needed.
- **Real-time execution**: when you click "Run Code," the app sends your code
  to the Piston API in a background thread (so the UI doesn't freeze) and
  displays the output as soon as it comes back — typically within 1-2 seconds.
- **Progress tracking**: XP, streaks, and completed lessons are saved back to
  `data.json` after every action, so progress persists between sessions.
- **Certificates**: once all lessons are marked complete, a PDF certificate is
  generated and saved to the `certificates/` folder.

## Adding More Lessons
Open `data.json` and add a new object to the `"lessons"` list (and, if you
want a quiz for it, a matching object in `"quizzes"` with the same
`lesson_id`). No code changes needed — the app reads lessons dynamically.

## Extending Later (v2 ideas)
- Multi-language compiler switch (C/C++/Java dropdown in the editor)
- Timed coding challenges
- Instructor/admin view for multiple students
