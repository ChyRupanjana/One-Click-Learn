"""
data_manager.py
Handles all reading/writing to data.json (lessons, quizzes, multi-user progress)
and contests.json (coding contest problems, unlocked every 4 lessons per module).
No database used — everything is stored in plain JSON files.
"""

import json
import os
from datetime import date

DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")
CONTESTS_FILE = os.path.join(os.path.dirname(__file__), "contests.json")


def load_data():
    """Load the entire data.json file into a Python dict."""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    """Write the given dict back to data.json."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_lessons(data):
    return data["lessons"]


def get_lessons_by_module(data, module):
    return [l for l in data["lessons"] if l["module"] == module]


def get_lesson_by_id(data, lesson_id):
    for lesson in data["lessons"]:
        if lesson["id"] == lesson_id:
            return lesson
    return None


def get_quizzes_by_module(data, module):
    """Returns ALL quiz questions belonging to a module (python/c/cpp)."""
    return [q for q in data["quizzes"] if q["module"] == module]


def get_user(data, username):
    """Returns the progress dict for a given logged-in username."""
    return data["users"][username]


def mark_lesson_complete(data, username, lesson_id, xp_reward=20):
    """Mark a lesson complete for this user, award XP, and update streak."""
    user = data["users"][username]
    if lesson_id not in user["completed_lessons"]:
        user["completed_lessons"].append(lesson_id)
        user["xp"] += xp_reward
        _update_streak(user)
        save_data(data)
    return user


def record_quiz_score(data, username, quiz_id, correct, xp_reward=10):
    """Save quiz result for this user and award XP if correct."""
    user = data["users"][username]
    user["quiz_scores"][str(quiz_id)] = "correct" if correct else "incorrect"
    if correct:
        user["xp"] += xp_reward
        _update_streak(user)
    save_data(data)
    return user


def _update_streak(user):
    """Increase streak once per calendar day; reset if a day was missed."""
    today = date.today().isoformat()
    last = user.get("last_activity_date")

    if last == today:
        return  # already counted today

    if last is not None:
        y = date.fromisoformat(last)
        gap = (date.today() - y).days
        if gap == 1:
            user["streak"] += 1
        elif gap > 1:
            user["streak"] = 1
        else:
            user["streak"] = max(user["streak"], 1)
    else:
        user["streak"] = 1

    user["last_activity_date"] = today


def get_level(xp):
    """Simple level formula: every 100 XP is one level."""
    return xp // 100 + 1


def get_progress_percent(data, username):
    total = len(data["lessons"])
    done = len(data["users"][username]["completed_lessons"])
    if total == 0:
        return 0
    return round((done / total) * 100, 1)


# ---------------------------------------------------------------------------
# Contest support. Contest CONTENT (problems, test cases) lives in its own
# file (contests.json) — completely separate from data.json — so adding or
# editing contests never risks corrupting lesson/quiz/user data. Which
# problems a user has SOLVED is still tracked per-user inside data.json.
# ---------------------------------------------------------------------------

def load_contests():
    """Load contests.json and return the list of contest dicts."""
    with open(CONTESTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)["contests"]


def get_contests_by_module(contests, module):
    return [c for c in contests if c["module"] == module]


def get_contest_by_id(contests, contest_id):
    for c in contests:
        if c["id"] == contest_id:
            return c
    return None


def get_problem_by_id(contest, problem_id):
    for p in contest["problems"]:
        if p["id"] == problem_id:
            return p
    return None


def get_completed_lesson_count_in_module(data, username, module):
    """How many lessons THIS user has completed within a single module —
    this count (not specific lesson IDs) is what unlocks contests."""
    completed = set(data["users"][username]["completed_lessons"])
    module_lesson_ids = {l["id"] for l in get_lessons_by_module(data, module)}
    return len(completed & module_lesson_ids)


def is_contest_unlocked(data, username, contest):
    done = get_completed_lesson_count_in_module(data, username, contest["module"])
    return done >= contest["unlock_after_lessons"]


def is_problem_solved(data, username, problem_id):
    user = data["users"][username]
    return problem_id in user.get("completed_contest_problems", [])

def get_solved_count_in_contest(data, username, contest):
    return sum(1 for p in contest["problems"] if is_problem_solved(data, username, p["id"]))


def mark_problem_solved(data, username, problem_id, xp_reward):
    """Marks a contest problem solved (only once — resubmitting an already
    solved problem awards no extra XP) and saves data.json."""
    user = data["users"][username]
    if "completed_contest_problems" not in user:
        user["completed_contest_problems"] = []
    if problem_id not in user["completed_contest_problems"]:
        user["completed_contest_problems"].append(problem_id)
        user["xp"] += xp_reward
        _update_streak(user)
        save_data(data)
    return user