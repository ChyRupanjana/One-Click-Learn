"""
data_manager.py
Handles all reading/writing to data.json (lessons, quizzes, multi-user progress)
and contests.json (coding contest problems, unlocked every 4 lessons per module).
No database used — everything is stored in plain JSON files.
"""

import json
import os
from datetime import date, datetime, timedelta

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


# ---------------------------------------------------------------------------
# Contest submission deadline — each user gets 7 days to submit solutions
# for a contest, counted from the moment THEY first open it (not from when
# it unlocked). Problems remain readable after the deadline; only new
# submissions are blocked.
# ---------------------------------------------------------------------------

CONTEST_DEADLINE_DAYS = 7


def start_contest_if_needed(data, username, contest_id):
    """Records the first time this user opens this contest. Calling it again
    for the same contest does nothing (the start time never resets)."""
    user = data["users"][username]
    if "contest_start_dates" not in user:
        user["contest_start_dates"] = {}
    if contest_id not in user["contest_start_dates"]:
        user["contest_start_dates"][contest_id] = datetime.now().isoformat()
        save_data(data)
    return user["contest_start_dates"][contest_id]


def get_contest_time_status(data, username, contest_id):
    """
    Returns a dict describing this user's submission window for a contest:
        {"started": bool, "days_remaining": int or None, "expired": bool}
    - started=False means the user hasn't opened this contest yet (no timer running).
    - days_remaining is a rounded-up whole-day count (e.g. 6.2 days left -> 7).
    - expired=True once the 7-day window from first open has passed.
    """
    user = data["users"][username]
    start_str = user.get("contest_start_dates", {}).get(contest_id)
    if not start_str:
        return {"started": False, "days_remaining": None, "expired": False}

    start_dt = datetime.fromisoformat(start_str)
    remaining = timedelta(days=CONTEST_DEADLINE_DAYS) - (datetime.now() - start_dt)

    if remaining.total_seconds() <= 0:
        return {"started": True, "days_remaining": 0, "expired": True}

    whole_days = remaining.days + (1 if remaining.seconds > 0 else 0)
    return {"started": True, "days_remaining": max(whole_days, 1), "expired": False}


# ---------------------------------------------------------------------------
# Contest leaderboard (ICPC-style: rank by problems solved, tie-break by
# lowest penalty). This requires tracking EVERY submission attempt (not just
# the final solved state) so we know, per problem, how many wrong attempts
# happened before an accepted one, and how long it took from contest start.
# ---------------------------------------------------------------------------

PENALTY_MINUTES_PER_WRONG_ATTEMPT = 20


def record_submission(data, username, contest_id, problem_id, passed):
    """Logs one submission attempt (pass or fail) with a timestamp. Called on
    every Submit click, regardless of outcome — this is what powers the
    leaderboard's per-problem attempt count and solve time."""
    user = data["users"][username]
    if "contest_submissions" not in user:
        user["contest_submissions"] = {}
    if contest_id not in user["contest_submissions"]:
        user["contest_submissions"][contest_id] = {}
    if problem_id not in user["contest_submissions"][contest_id]:
        user["contest_submissions"][contest_id][problem_id] = []
    user["contest_submissions"][contest_id][problem_id].append({
        "timestamp": datetime.now().isoformat(),
        "passed": bool(passed),
    })
    save_data(data)


def get_problem_stats(data, username, contest_id, problem_id):
    """
    Per-problem submission stats for one user in one contest:
        {"attempted": bool, "solved": bool, "wrong_attempts": int,
         "solve_time_minutes": int or None, "total_attempts": int}
    wrong_attempts = attempts before the accepted one (if solved), or the
    total failed attempts so far (if never solved).
    """
    user = data["users"][username]
    attempts = user.get("contest_submissions", {}).get(contest_id, {}).get(problem_id, [])
    if not attempts:
        return {"attempted": False, "solved": False, "wrong_attempts": 0,
                "solve_time_minutes": None, "total_attempts": 0}

    start_str = user.get("contest_start_dates", {}).get(contest_id)
    start_dt = datetime.fromisoformat(start_str) if start_str else None

    wrong_before_solve = 0
    solve_time_minutes = None
    solved = False
    for a in attempts:
        if a["passed"]:
            solved = True
            if start_dt:
                t = datetime.fromisoformat(a["timestamp"])
                solve_time_minutes = max(0, int((t - start_dt).total_seconds() // 60))
            break
        wrong_before_solve += 1

    return {
        "attempted": True,
        "solved": solved,
        "wrong_attempts": wrong_before_solve if solved else len(attempts),
        "solve_time_minutes": solve_time_minutes,
        "total_attempts": len(attempts),
    }


def get_contest_leaderboard(data, contest):
    """
    Returns leaderboard rows for everyone who has started this contest,
    sorted ICPC-style: highest score (problems solved) first, then lowest
    penalty. Each row:
        {"username": str, "score": int, "penalty": int,
         "problems": {problem_id: <get_problem_stats() dict>}}
    """
    rows = []
    for username, user in data["users"].items():
        if contest["id"] not in user.get("contest_start_dates", {}):
            continue

        problems_stats = {}
        score = 0
        penalty = 0
        for problem in contest["problems"]:
            stats = get_problem_stats(data, username, contest["id"], problem["id"])
            problems_stats[problem["id"]] = stats
            if stats["solved"]:
                score += 1
                penalty += (stats["solve_time_minutes"] or 0) + \
                    PENALTY_MINUTES_PER_WRONG_ATTEMPT * stats["wrong_attempts"]

        rows.append({"username": username, "score": score, "penalty": penalty, "problems": problems_stats})

    rows.sort(key=lambda r: (-r["score"], r["penalty"]))
    return rows