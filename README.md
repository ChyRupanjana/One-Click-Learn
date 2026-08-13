# CodeLearn — Bilingual Coding Learning App

A desktop coding-learning application built with **Python + Tkinter**,
storing all data in local **JSON** files. Supports multiple user accounts,
lessons across several languages, contests with a leaderboard, and an admin
panel — all running fully offline, with code executed **locally** (no
external API needed).

## Features
- **Multi-user login/signup** — login by username or email, hashed +
  salted passwords, optional "Remember Me" session (30-day expiry)
- Lessons with bilingual content (Bangla / English toggle) across
  Python / C / C++ modules
- In-app code editor with a Run button — executes **locally via
  subprocess** (Python, C, C++, Java supported)
- MCQ quizzes with instant feedback
- XP, streak, and level system
- Contest system with problems, submissions, and a **leaderboard**
- **Admin panel** — student management and oversight
- Progress dashboard with matplotlib charts
- PDF certificate generation (via reportlab) after completing all lessons

## Project Structure
```
CodeLearnApp/
├── main.py                  # Tkinter GUI app (entry point) — login, home,
│                             #   lessons, quizzes, contests, leaderboard,
│                             #   admin panel, progress, certificates
├── auth.py                  # Login/signup, password hashing, sessions
├── data_manager.py          # JSON load/save, lessons/users/progress logic
├── code_runner.py           # Local code execution via subprocess
│                             #   (Python, C, C++, Java)
├── progress_chart.py        # matplotlib chart embedded in Tkinter
├── certificate_generator.py # PDF certificate generation (reportlab)
├── data.json                # Lessons, quizzes, and user accounts/progress
├── contests.json            # Contest problems and submissions
├── admin_config.json        # Admin credentials/config
├── session.json             # Saved "Remember Me" session (auto-generated)
├── requirements.txt
└── README.md
```

## Setup

1. Make sure you have Python 3.8+ installed.
2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```
3. For non-Python languages, make sure these are installed and on your PATH:
   - **C**: `gcc`
   - **C++**: `g++`
   - **Java**: JDK (`javac` + `java`)

   (Python code needs no extra install.)
4. Run the app:
   ```
   python main.py
   ```

> Note: Code runs entirely on your machine via `subprocess` — no internet
> connection or external API is required.

## How It Works
- **Accounts**: `auth.py` handles signup/login, hashing passwords with
  `hashlib.pbkdf2_hmac` and a per-user salt. Sessions can be remembered for
  30 days via `session.json`.
- **Lessons & Quizzes**: stored as lists of dictionaries in `data.json`.
  `data_manager.py` handles all reading/writing — no database engine needed.
- **Code execution**: when you click "Run Code," `code_runner.py` compiles
  (for C/C++/Java) and runs your code locally in a subprocess with a
  10-second timeout, then returns the output to the UI.
- **Contests & Leaderboard**: contest problems live in `contests.json`;
  submissions and rankings are tracked per user and shown on the
  `LeaderboardScreen`.
- **Admin panel**: a separate admin login (`AdminLoginScreen`) leads to
  `StudentManagementScreen` for viewing/managing student accounts and
  progress.
- **Progress tracking**: XP, streaks, and completed lessons are saved back
  to `data.json` after every action, so progress persists between sessions.
- **Certificates**: once all lessons are marked complete, a PDF certificate
  is generated via reportlab and saved to the `certificates/` folder.

## Adding More Lessons
Open `data.json` and add a new object to the `"lessons"` list (and, if you
want a quiz for it, a matching object in `"quizzes"` with the same
`lesson_id`). No code changes needed — the app reads lessons dynamically.

## Extending Later
- Timed/ranked contest rounds with live standings
- Richer admin analytics (per-module completion rates, activity logs)
- Password reset flow / rate limiting for auth
- Packaging as a standalone executable (PyInstaller)