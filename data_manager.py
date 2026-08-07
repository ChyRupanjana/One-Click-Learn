"""
data_manager.py
Handles all reading/writing to data.json (lessons, quizzes, multi-user progress).
No database used — everything is stored in a single JSON file.
"""

import json
import os
from datetime import date

DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")


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


def get_lesson_by_id(data, lesson_id):
    for lesson in data["lessons"]:
        if lesson["id"] == lesson_id:
            return lesson
    return None


def get_quizzes_by_lesson(data, lesson_id):
    """Returns ALL quiz questions belonging to a lesson, as a list."""
    return [q for q in data["quizzes"] if q["lesson_id"] == lesson_id]


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