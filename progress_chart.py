"""
progress_chart.py
Builds a matplotlib chart (embedded in Tkinter) showing lesson progress and XP
for the currently logged-in user.
"""

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def build_progress_chart(parent_frame, data, user):
    """
    Creates a matplotlib figure with two subplots:
    1. Bar chart: completed vs remaining lessons
    2. Bar chart: quiz correct vs incorrect
    Embeds it into the given Tkinter frame and returns the canvas widget.
    """
    lessons = data["lessons"]

    total_lessons = len(lessons)
    completed = len(user["completed_lessons"])
    remaining = total_lessons - completed

    correct = sum(1 for v in user["quiz_scores"].values() if v == "correct")
    incorrect = sum(1 for v in user["quiz_scores"].values() if v == "incorrect")

    fig, axes = plt.subplots(1, 2, figsize=(7, 3.2))
    fig.patch.set_facecolor("#f5f5f5")

    axes[0].bar(["Completed", "Remaining"], [completed, remaining],
                color=["#27ae60", "#bdc3c7"])
    axes[0].set_title("Lesson Progress")
    axes[0].set_ylim(0, max(total_lessons, 1))

    axes[1].bar(["Correct", "Incorrect"], [correct, incorrect],
                color=["#2980b9", "#e74c3c"])
    axes[1].set_title("Quiz Results")
    axes[1].set_ylim(0, max(correct + incorrect, 1))

    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas.draw()
    return canvas.get_tk_widget()
