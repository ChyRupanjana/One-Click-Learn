"""
data_manager.py
Handles all reading/writing to data.json (lessons, quizzes, multi-user progress).
No database used — everything is stored in a single JSON file.
"""

import json
import os
from datetime import date, datetime, timedelta

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
# Contests — unlocked every 2 completed lessons within a module.
# ---------------------------------------------------------------------------

def count_completed_in_module(data, user, module):
    """How many lessons the user has completed within a specific module."""
    module_lesson_ids = {l["id"] for l in data["lessons"] if l["module"] == module}
    return len([lid for lid in user["completed_lessons"] if lid in module_lesson_ids])


def get_contests_by_module(data, module):
    return [c for c in data.get("contests", []) if c["module"] == module]


def is_contest_unlocked(contest, completed_count):
    return completed_count >= contest["unlock_after_lessons"]


def get_problem(data, contest_id, problem_id):
    for contest in data.get("contests", []):
        if contest["id"] == contest_id:
            for problem in contest["problems"]:
                if problem["id"] == problem_id:
                    return contest, problem
    return None, None


def mark_problem_solved(data, username, problem_key, xp_reward=15):
    """
    problem_key should be unique across the whole app, e.g. 'contest3_problem2'.
    Returns True if this was the FIRST time solving it (i.e. XP was awarded).
    """
    user = data["users"][username]
    solved = user.setdefault("solved_problems", {})

    if problem_key in solved:
        return False

    solved[problem_key] = True
    user["xp"] += xp_reward
    _update_streak(user)
    save_data(data)
    return True


# ---------------------------------------------------------------------------
# Contest submission window — a user gets 7 days from the moment they FIRST
# open a given contest to submit solutions for it. After that, submissions
# for that contest are locked (though the problems remain viewable).
# ---------------------------------------------------------------------------

CONTEST_WINDOW_DAYS = 7


def start_contest_if_needed(data, username, contest_id):
    """
    Records the moment this user first opens a contest, starting their
    7-day submission window. Calling this again for an already-started
    contest does nothing (the original start time is kept).
    Returns the (possibly newly-set) start timestamp as an ISO string.
    """
    user = data["users"][username]
    starts = user.setdefault("contest_start_dates", {})

    key = str(contest_id)
    if key not in starts:
        starts[key] = datetime.now().isoformat()
        save_data(data)

    return starts[key]


def get_contest_time_status(data, username, contest_id):
    """
    Returns a dict describing this user's submission window for a contest:
        {
            "started": bool,          # has the user opened this contest yet?
            "expired": bool,          # is the 7-day window over?
            "days_left": int or None, # whole days remaining (0 on the last day)
            "deadline": str or None,  # ISO date the window closes
        }
    """
    user = data["users"][username]
    starts = user.get("contest_start_dates", {})
    key = str(contest_id)

    if key not in starts:
        return {"started": False, "expired": False, "days_left": None, "deadline": None}

    start_time = datetime.fromisoformat(starts[key])
    deadline = start_time + timedelta(days=CONTEST_WINDOW_DAYS)
    now = datetime.now()
    expired = now > deadline
    days_left = max(0, (deadline - now).days) if not expired else 0

    return {
        "started": True,
        "expired": expired,
        "days_left": days_left,
        "deadline": deadline.strftime("%d %b %Y"),
    }