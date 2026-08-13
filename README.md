# CodeLearn — Bilingual Coding Learning App

A desktop coding-learning application built with **Python + Tkinter**,
storing all data in local **JSON** files. Supports multiple user accounts,
lessons across several languages, contests with a leaderboard, a live
plagiarism/code-similarity checker, and an admin panel — all running fully
offline, with code executed **locally** (no external API needed).

## Features
- **Multi-user login/signup** — login by username or email, hashed +
  salted passwords, optional "Remember Me" session (30-day expiry)
- Lessons with bilingual content (Bangla / English toggle) across
  Python / C / C++ modules
- **Live search** on the Lessons screen and the Contests screen — filters
  as you type, matches both English and Bangla titles
- In-app code editor with a Run button — executes **locally via
  subprocess** (Python, C, C++, Java supported)
- MCQ quizzes with instant feedback
- XP, streak, and level system
- **Contest system** with problems, submissions, a 7-day submission window,
  and an ICPC-style **leaderboard** (ranked by problems solved, tie-broken
  by penalty time)
- Contests are **named by topic** (e.g. "Python: Strings & Number Theory")
  instead of a generic number, based on what their problems actually cover
- **Admin panel**:
  - Student management — view/edit XP, reset progress, delete accounts
  - **Plagiarism / code-similarity checker** — compares every pair of
    students' accepted solutions per contest problem and flags high-similarity
    pairs for manual review, with a side-by-side code viewer
- Progress dashboard with matplotlib charts
- PDF certificate generation (via reportlab) after completing all lessons

## Project Structure
```
CodeLearnApp/
├── main.py                  # Tkinter GUI app (entry point) — login, home,
│                             #   lessons, quizzes, contests, leaderboard,
│                             #   admin panel + plagiarism checker,
│                             #   progress, certificates
├── auth.py                  # Login/signup, password hashing, sessions
├── data_manager.py          # JSON load/save, lessons/users/progress logic,
│                             #   contest leaderboard, plagiarism detection
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
- **Search**: the Lessons and Contests screens keep the full list in memory
  and re-filter it locally as you type (case-insensitive, checks both
  English and Bangla titles) — no extra file reads per keystroke.
- **Code execution**: when you click "Run Code," `code_runner.py` compiles
  (for C/C++/Java) and runs your code locally in a subprocess with a
  10-second timeout, then returns the output to the UI.
- **Contests, Leaderboard & Topic Names**: contest problems live in
  `contests.json`, each tagged with a topic-based title generated from its
  problems' subject areas (Basic Math, Number Theory, Strings, Arrays,
  Recursion, Bit Manipulation). Submissions and rankings are tracked per
  user and shown on the `LeaderboardScreen`.
- **Plagiarism checker**: every contest submission now also stores the
  submitted code and language. The admin's Plagiarism Checker
  (`PlagiarismCheckScreen`) takes each student's **first accepted** solution
  per problem, strips comments/blank lines/indentation, and compares every
  pair with `difflib.SequenceMatcher`. Pairs at or above a chosen similarity
  threshold (60–90%) are listed with a side-by-side code viewer.
  ⚠️ These are short beginner problems, so similar code can happen by
  chance — flagged pairs are a signal to review manually, not proof of
  copying.
- **Admin panel**: a separate admin login (`AdminLoginScreen`) leads to
  `StudentManagementScreen` for viewing/managing student accounts and
  progress, with a button into the Plagiarism Checker.
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