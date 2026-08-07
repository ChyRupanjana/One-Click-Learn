"""
main.py
Entry point for the Coding Learning App (Bilingual Bangla/English).

Tech stack: Python + Tkinter (GUI) + JSON (storage, multi-user) + local
            subprocess execution for Python/C/C++/Java + matplotlib (progress
            chart) + reportlab (certificate PDF)

Run with:  python main.py
Requires:  pip install matplotlib reportlab
           (also needs gcc/g++ on PATH for C/C++, and a JDK for Java)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading

import data_manager as dm
import code_runner
import auth
import progress_chart
from certificate_generator import generate_certificate

BG_COLOR = "#f5f6fa"
ACCENT_COLOR = "#2c3e50"
BTN_COLOR = "#2980b9"

LANGUAGES = ["python", "c", "cpp", "java"]

DEFAULT_SNIPPETS = {
    "python": 'print("Hello, World!")',
    "c": '#include <stdio.h>\n\nint main() {\n    printf("Hello, World!\\n");\n    return 0;\n}',
    "cpp": '#include <iostream>\nusing namespace std;\n\nint main() {\n    cout << "Hello, World!" << endl;\n    return 0;\n}',
    "java": 'public class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello, World!");\n    }\n}',
}


class CodeLearnApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CodeLearn — Bilingual Coding Learning App")
        self.geometry("1000x680")
        self.configure(bg=BG_COLOR)

        self.data = dm.load_data()
        self.language = "en"          # UI language: "en" or "bn"
        self.current_user = None      # set after login

        container = tk.Frame(self, bg=BG_COLOR)
        container.pack(fill="both", expand=True)
        self.frames = {}

        for F in (LoginScreen, HomeScreen, LessonListScreen, LessonDetailScreen,
                  QuizScreen, ProgressScreen, CertificateScreen, PlaygroundScreen):
            frame = F(container, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.show_frame("LoginScreen")

    def show_frame(self, name):
        frame = self.frames[name]
        if hasattr(frame, "on_show"):
            frame.on_show()
        frame.tkraise()

    def refresh_data(self):
        self.data = dm.load_data()

    def get_current_user_data(self):
        return dm.get_user(self.data, self.current_user)

    def logout(self):
        self.current_user = None
        self.show_frame("LoginScreen")


class LoginScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_COLOR)
        self.app = app

        card = tk.Frame(self, bg="white", padx=40, pady=40)
        card.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(card, text="CodeLearn", font=("Helvetica", 26, "bold"),
                 bg="white", fg=ACCENT_COLOR).pack(pady=(0, 5))
        tk.Label(card, text="Login / সাইন ইন", font=("Helvetica", 12),
                 bg="white", fg="#777").pack(pady=(0, 20))

        tk.Label(card, text="Username:", bg="white", font=("Helvetica", 11)).pack(anchor="w")
        self.username_entry = tk.Entry(card, font=("Helvetica", 12), width=28)
        self.username_entry.pack(pady=(0, 10))

        tk.Label(card, text="Password:", bg="white", font=("Helvetica", 11)).pack(anchor="w")
        self.password_entry = tk.Entry(card, font=("Helvetica", 12), width=28, show="*")
        self.password_entry.pack(pady=(0, 15))

        tk.Button(card, text="Login", bg=BTN_COLOR, fg="white", font=("Helvetica", 12, "bold"),
                  width=24, command=self.login).pack(pady=5)
        tk.Button(card, text="Create New Account", bg="#27ae60", fg="white", font=("Helvetica", 11),
                  width=24, command=self.signup).pack(pady=5)

        self.message_label = tk.Label(card, text="", bg="white", font=("Helvetica", 10), fg="#e74c3c")
        self.message_label.pack(pady=(10, 0))

    def on_show(self):
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self.message_label.config(text="")

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        self.app.refresh_data()

        success, msg = auth.verify_login(self.app.data, username, password)
        if success:
            self.app.current_user = username
            self.app.show_frame("HomeScreen")
        else:
            self.message_label.config(text=msg, fg="#e74c3c")

    def signup(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        self.app.refresh_data()

        success, msg = auth.create_user(self.app.data, username, password)
        if success:
            dm.save_data(self.app.data)
            self.message_label.config(text="Account created! You can log in now.", fg="#27ae60")
        else:
            self.message_label.config(text=msg, fg="#e74c3c")


class HomeScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_COLOR)
        self.app = app

        top = tk.Frame(self, bg=BG_COLOR)
        top.pack(fill="x", padx=20, pady=10)
        tk.Button(top, text="Logout", command=app.logout).pack(side="right")

        tk.Label(self, text="CodeLearn", font=("Helvetica", 30, "bold"),
                 bg=BG_COLOR, fg=ACCENT_COLOR).pack(pady=(20, 5))
        tk.Label(self, text="বাংলা ও ইংরেজিতে কোডিং শেখো — Learn Coding in Bangla & English",
                 font=("Helvetica", 13), bg=BG_COLOR, fg="#555").pack(pady=(0, 30))

        btn_style = {"font": ("Helvetica", 13), "width": 28, "bg": BTN_COLOR,
                     "fg": "white", "bd": 0, "pady": 10, "cursor": "hand2"}

        tk.Button(self, text="📚 Lessons / পাঠসমূহ", command=lambda: app.show_frame("LessonListScreen"),
                   **btn_style).pack(pady=6)
        tk.Button(self, text="💻 Code Playground / কোড লেখো", command=lambda: app.show_frame("PlaygroundScreen"),
                   **{**btn_style, "bg": "#8e44ad"}).pack(pady=6)
        tk.Button(self, text="📊 My Progress / অগ্রগতি", command=lambda: app.show_frame("ProgressScreen"),
                   **btn_style).pack(pady=6)
        tk.Button(self, text="🎓 Get Certificate / সার্টিফিকেট", command=lambda: app.show_frame("CertificateScreen"),
                   **btn_style).pack(pady=6)

        self.status_label = tk.Label(self, text="", font=("Helvetica", 11),
                                      bg=BG_COLOR, fg=ACCENT_COLOR)
        self.status_label.pack(pady=25)

    def on_show(self):
        self.app.refresh_data()
        user = self.app.get_current_user_data()
        level = dm.get_level(user["xp"])
        self.status_label.config(
            text=f"👤 {self.app.current_user}   |   ⭐ XP: {user['xp']}   |   "
                 f"🔥 Streak: {user['streak']} days   |   🏆 Level: {level}"
        )


class LessonListScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_COLOR)
        self.app = app

        top = tk.Frame(self, bg=BG_COLOR)
        top.pack(fill="x", pady=15, padx=20)
        tk.Button(top, text="← Back", command=lambda: app.show_frame("HomeScreen")).pack(side="left")
        tk.Label(top, text="Lessons / পাঠসমূহ", font=("Helvetica", 20, "bold"),
                 bg=BG_COLOR, fg=ACCENT_COLOR).pack(side="left", padx=20)

        self.listbox = tk.Listbox(self, font=("Helvetica", 13), height=15)
        self.listbox.pack(fill="both", expand=True, padx=20, pady=10)
        self.listbox.bind("<<ListboxSelect>>", self.select_lesson)

    def on_show(self):
        self.app.refresh_data()
        self.listbox.delete(0, tk.END)
        self.lesson_ids = []
        completed = self.app.get_current_user_data()["completed_lessons"]
        for lesson in dm.get_lessons(self.app.data):
            mark = "✅ " if lesson["id"] in completed else "⬜ "
            lang_tag = f"[{lesson['language'].upper()}] "
            title = lesson["title_bn"] if self.app.language == "bn" else lesson["title_en"]
            self.listbox.insert(tk.END, f"{mark}{lang_tag}{title}")
            self.lesson_ids.append(lesson["id"])

    def select_lesson(self, event):
        selection = self.listbox.curselection()
        if not selection:
            return
        lesson_id = self.lesson_ids[selection[0]]
        detail_frame = self.app.frames["LessonDetailScreen"]
        detail_frame.load_lesson(lesson_id)
        self.app.show_frame("LessonDetailScreen")


class LessonDetailScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_COLOR)
        self.app = app
        self.current_lesson = None

        top = tk.Frame(self, bg=BG_COLOR)
        top.pack(fill="x", pady=10, padx=20)
        tk.Button(top, text="← Back", command=lambda: app.show_frame("LessonListScreen")).pack(side="left")
        tk.Button(top, text="বাংলা / English", command=self.toggle_language).pack(side="left", padx=10)

        self.title_label = tk.Label(self, font=("Helvetica", 18, "bold"), bg=BG_COLOR, fg=ACCENT_COLOR)
        self.title_label.pack(pady=(5, 5), padx=20, anchor="w")

        self.content_label = tk.Label(self, font=("Helvetica", 12), bg=BG_COLOR, fg="#333",
                                       wraplength=930, justify="left")
        self.content_label.pack(pady=(0, 10), padx=20, anchor="w")

        tk.Label(self, text="Code Editor (type or edit code below):", font=("Helvetica", 11, "bold"),
                 bg=BG_COLOR, fg=ACCENT_COLOR).pack(anchor="w", padx=20)

        self.code_box = tk.Text(self, height=8, font=("Consolas", 12), bg="#2d2d2d", fg="#f8f8f2",
                                 insertbackground="white")
        self.code_box.pack(fill="x", padx=20, pady=(5, 10))

        btn_frame = tk.Frame(self, bg=BG_COLOR)
        btn_frame.pack(fill="x", padx=20)
        self.run_btn = tk.Button(btn_frame, text="▶ Run Code", bg="#27ae60", fg="white",
                                  font=("Helvetica", 11, "bold"), command=self.run_code)
        self.run_btn.pack(side="left")

        tk.Button(btn_frame, text="✔ Mark Lesson Complete", command=self.complete_lesson,
                  bg=BTN_COLOR, fg="white", font=("Helvetica", 11)).pack(side="left", padx=10)

        tk.Button(btn_frame, text="📝 Take Quiz", command=self.go_to_quiz,
                  bg="#8e44ad", fg="white", font=("Helvetica", 11)).pack(side="left")

        tk.Label(self, text="Output:", font=("Helvetica", 11, "bold"), bg=BG_COLOR,
                 fg=ACCENT_COLOR).pack(anchor="w", padx=20, pady=(10, 0))

        self.output_box = tk.Text(self, height=6, font=("Consolas", 11), bg="#1e1e1e", fg="#00ff88")
        self.output_box.pack(fill="both", expand=True, padx=20, pady=(5, 15))
        self.output_box.config(state="disabled")

    def toggle_language(self):
        self.app.language = "bn" if self.app.language == "en" else "en"
        if self.current_lesson:
            self.load_lesson(self.current_lesson["id"])

    def load_lesson(self, lesson_id):
        self.app.refresh_data()
        lesson = dm.get_lesson_by_id(self.app.data, lesson_id)
        self.current_lesson = lesson

        title = lesson["title_bn"] if self.app.language == "bn" else lesson["title_en"]
        content = lesson["content_bn"] if self.app.language == "bn" else lesson["content_en"]

        self.title_label.config(text=title)
        self.content_label.config(text=content)

        self.code_box.delete("1.0", tk.END)
        self.code_box.insert(tk.END, lesson["code_example"])

        self.output_box.config(state="normal")
        self.output_box.delete("1.0", tk.END)
        self.output_box.config(state="disabled")

    def run_code(self):
        code = self.code_box.get("1.0", tk.END)
        language = self.current_lesson["language"]

        self._set_output("Running code...\n")
        self.run_btn.config(state="disabled")
        threading.Thread(target=self._run_code_thread, args=(language, code), daemon=True).start()

    def _run_code_thread(self, language, code):
        result = code_runner.run_code(language, code)
        self.after(0, self._show_run_result, result)

    def _show_run_result(self, result):
        if result["success"]:
            self._set_output(result["output"] or "(no output)")
        else:
            self._set_output("Error:\n" + result["error"])
        self.run_btn.config(state="normal")

    def _set_output(self, text):
        self.output_box.config(state="normal")
        self.output_box.delete("1.0", tk.END)
        self.output_box.insert(tk.END, text)
        self.output_box.config(state="disabled")

    def complete_lesson(self):
        dm.mark_lesson_complete(self.app.data, self.app.current_user, self.current_lesson["id"])
        self.app.refresh_data()
        messagebox.showinfo("Great job!", "Lesson marked complete. +20 XP")

    def go_to_quiz(self):
        quiz_frame = self.app.frames["QuizScreen"]
        quiz_frame.load_quiz(self.current_lesson["id"])
        self.app.show_frame("QuizScreen")


class QuizScreen(tk.Frame):
    """Multi-question quiz for a lesson, with Next/Previous navigation,
    instant correct-answer feedback after submitting, and a Quit option."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_COLOR)
        self.app = app
        self.quiz_list = []       # all questions for the current lesson
        self.current_index = 0
        self.session_answers = {}  # {quiz_id: {"selected": str, "submitted": bool, "correct": bool}}
        self.selected_option = tk.StringVar()

        top = tk.Frame(self, bg=BG_COLOR)
        top.pack(fill="x", pady=15, padx=20)
        tk.Button(top, text="✕ Quit Quiz", command=self.quit_quiz,
                  bg="#e74c3c", fg="white", font=("Helvetica", 10, "bold")).pack(side="left")
        tk.Label(top, text="Quiz / কুইজ", font=("Helvetica", 20, "bold"),
                 bg=BG_COLOR, fg=ACCENT_COLOR).pack(side="left", padx=20)

        self.progress_label = tk.Label(top, font=("Helvetica", 11), bg=BG_COLOR, fg="#777")
        self.progress_label.pack(side="right")

        self.question_label = tk.Label(self, font=("Helvetica", 14), bg=BG_COLOR, fg="#333",
                                        wraplength=900, justify="left")
        self.question_label.pack(pady=20, padx=20, anchor="w")

        self.options_frame = tk.Frame(self, bg=BG_COLOR)
        self.options_frame.pack(padx=20, anchor="w")

        self.submit_btn = tk.Button(self, text="Submit Answer", bg=BTN_COLOR, fg="white",
                                     font=("Helvetica", 12, "bold"), command=self.submit_answer)
        self.submit_btn.pack(pady=15)

        self.result_label = tk.Label(self, font=("Helvetica", 13, "bold"), bg=BG_COLOR,
                                      wraplength=900, justify="left")
        self.result_label.pack()

        nav_frame = tk.Frame(self, bg=BG_COLOR)
        nav_frame.pack(pady=25)
        self.prev_btn = tk.Button(nav_frame, text="← Previous", font=("Helvetica", 11),
                                   width=14, command=self.go_previous)
        self.prev_btn.pack(side="left", padx=8)
        self.next_btn = tk.Button(nav_frame, text="Next →", font=("Helvetica", 11),
                                   width=14, bg="#8e44ad", fg="white", command=self.go_next)
        self.next_btn.pack(side="left", padx=8)

    def load_quiz(self, lesson_id):
        self.app.refresh_data()
        self.quiz_list = dm.get_quizzes_by_lesson(self.app.data, lesson_id)
        self.current_index = 0
        self.session_answers = {}
        self.render_question()

    def quit_quiz(self):
        if messagebox.askyesno("Quit Quiz", "Are you sure you want to quit? "
                                             "Your answered questions will still be saved."):
            self.app.show_frame("LessonListScreen")

    def render_question(self):
        for widget in self.options_frame.winfo_children():
            widget.destroy()
        self.result_label.config(text="")

        if not self.quiz_list:
            self.question_label.config(text="No quiz available for this lesson yet.")
            self.progress_label.config(text="")
            self.submit_btn.config(state="disabled")
            self.prev_btn.config(state="disabled")
            self.next_btn.config(state="disabled")
            return

        quiz = self.quiz_list[self.current_index]
        total = len(self.quiz_list)
        self.progress_label.config(text=f"Question {self.current_index + 1} of {total}")

        question = quiz["question_bn"] if self.app.language == "bn" else quiz["question_en"]
        self.question_label.config(text=question)

        prior = self.session_answers.get(quiz["id"])
        self.selected_option.set(prior["selected"] if prior else "")

        for option in quiz["options"]:
            tk.Radiobutton(self.options_frame, text=option, variable=self.selected_option,
                            value=option, font=("Helvetica", 12), bg=BG_COLOR).pack(anchor="w", pady=3)

        if prior and prior["submitted"]:
            self._show_feedback(quiz, prior["correct"])

        self.prev_btn.config(state="normal" if self.current_index > 0 else "disabled")
        self.next_btn.config(state="normal" if self.current_index < total - 1 else "disabled",
                              text="Finish" if self.current_index == total - 1 else "Next →")

    def submit_answer(self):
        if not self.quiz_list:
            return
        quiz = self.quiz_list[self.current_index]
        chosen = self.selected_option.get()
        if not chosen:
            messagebox.showwarning("No answer selected", "Please choose an option first.")
            return

        already_submitted = quiz["id"] in self.session_answers and self.session_answers[quiz["id"]]["submitted"]
        correct = chosen == quiz["answer"]

        # Only record XP the first time this question is submitted
        if not already_submitted:
            dm.record_quiz_score(self.app.data, self.app.current_user, quiz["id"], correct)
            self.app.refresh_data()

        self.session_answers[quiz["id"]] = {"selected": chosen, "submitted": True, "correct": correct}
        self._show_feedback(quiz, correct)

    def _show_feedback(self, quiz, correct):
        if correct:
            self.result_label.config(text="✅ Correct! +10 XP", fg="#27ae60")
        else:
            self.result_label.config(
                text=f"❌ Incorrect. Correct answer: {quiz['answer']}", fg="#e74c3c"
            )

    def go_previous(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.render_question()

    def go_next(self):
        total = len(self.quiz_list)
        if self.current_index < total - 1:
            self.current_index += 1
            self.render_question()
        else:
            messagebox.showinfo("Quiz Finished", "You've reached the last question of this quiz!")


class ProgressScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_COLOR)
        self.app = app

        top = tk.Frame(self, bg=BG_COLOR)
        top.pack(fill="x", pady=15, padx=20)
        tk.Button(top, text="← Back", command=lambda: app.show_frame("HomeScreen")).pack(side="left")
        tk.Label(top, text="My Progress / অগ্রগতি", font=("Helvetica", 20, "bold"),
                 bg=BG_COLOR, fg=ACCENT_COLOR).pack(side="left", padx=20)

        self.stats_label = tk.Label(self, font=("Helvetica", 13), bg=BG_COLOR, fg="#333")
        self.stats_label.pack(pady=10)

        self.chart_container = tk.Frame(self, bg=BG_COLOR)
        self.chart_container.pack(fill="both", expand=True, padx=20, pady=10)

    def on_show(self):
        self.app.refresh_data()
        data = self.app.data
        user = self.app.get_current_user_data()

        pct = dm.get_progress_percent(data, self.app.current_user)
        level = dm.get_level(user["xp"])
        self.stats_label.config(
            text=f"Lessons completed: {pct}%   |   XP: {user['xp']}   |   "
                 f"Level: {level}   |   Streak: {user['streak']} days"
        )

        for widget in self.chart_container.winfo_children():
            widget.destroy()

        chart_widget = progress_chart.build_progress_chart(self.chart_container, data, user)
        chart_widget.pack(fill="both", expand=True)


class CertificateScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_COLOR)
        self.app = app

        top = tk.Frame(self, bg=BG_COLOR)
        top.pack(fill="x", pady=15, padx=20)
        tk.Button(top, text="← Back", command=lambda: app.show_frame("HomeScreen")).pack(side="left")
        tk.Label(top, text="Certificate / সার্টিফিকেট", font=("Helvetica", 20, "bold"),
                 bg=BG_COLOR, fg=ACCENT_COLOR).pack(side="left", padx=20)

        self.info_label = tk.Label(self, font=("Helvetica", 13), bg=BG_COLOR, fg="#333",
                                    wraplength=900, justify="left")
        self.info_label.pack(pady=30, padx=20)

        self.gen_btn = tk.Button(self, text="🎓 Generate Certificate", bg="#e67e22", fg="white",
                                  font=("Helvetica", 13, "bold"), command=self.generate)
        self.gen_btn.pack(pady=10)

        self.path_label = tk.Label(self, font=("Helvetica", 11), bg=BG_COLOR, fg="#555")
        self.path_label.pack(pady=10)

    def on_show(self):
        self.app.refresh_data()
        data = self.app.data
        user = self.app.get_current_user_data()
        total = len(data["lessons"])
        done = len(user["completed_lessons"])

        if done >= total and total > 0:
            self.info_label.config(text="🎉 Congratulations! You've completed all lessons. "
                                         "Click below to generate your certificate.")
            self.gen_btn.config(state="normal")
        else:
            self.info_label.config(
                text=f"You have completed {done} of {total} lessons. "
                     f"Complete all lessons to unlock your certificate."
            )
            self.gen_btn.config(state="disabled")

    def generate(self):
        username = self.app.current_user
        path = generate_certificate(username, course_title="CodeLearn Fundamentals")
        self.path_label.config(text=f"Saved to: {path}")
        messagebox.showinfo("Certificate Generated", f"Your certificate was saved at:\n{path}")


class PlaygroundScreen(tk.Frame):
    """Free-form code editor: pick ANY supported language and write ANY code,
    not tied to a specific lesson."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_COLOR)
        self.app = app

        top = tk.Frame(self, bg=BG_COLOR)
        top.pack(fill="x", pady=10, padx=20)
        tk.Button(top, text="← Back", command=lambda: app.show_frame("HomeScreen")).pack(side="left")
        tk.Label(top, text="Code Playground / কোড লেখো", font=("Helvetica", 20, "bold"),
                 bg=BG_COLOR, fg=ACCENT_COLOR).pack(side="left", padx=20)

        lang_frame = tk.Frame(self, bg=BG_COLOR)
        lang_frame.pack(fill="x", padx=20, pady=(5, 0))
        tk.Label(lang_frame, text="Language:", font=("Helvetica", 11, "bold"),
                 bg=BG_COLOR, fg=ACCENT_COLOR).pack(side="left")

        self.language_var = tk.StringVar(value="python")
        self.language_dropdown = ttk.Combobox(lang_frame, textvariable=self.language_var,
                                               values=LANGUAGES, state="readonly", width=12,
                                               font=("Helvetica", 11))
        self.language_dropdown.pack(side="left", padx=10)
        self.language_dropdown.bind("<<ComboboxSelected>>", self.on_language_change)

        self.code_box = tk.Text(self, height=14, font=("Consolas", 12), bg="#2d2d2d", fg="#f8f8f2",
                                 insertbackground="white")
        self.code_box.pack(fill="both", expand=True, padx=20, pady=(10, 10))
        self.code_box.insert(tk.END, DEFAULT_SNIPPETS["python"])

        btn_frame = tk.Frame(self, bg=BG_COLOR)
        btn_frame.pack(fill="x", padx=20)
        self.run_btn = tk.Button(btn_frame, text="▶ Run Code", bg="#27ae60", fg="white",
                                  font=("Helvetica", 11, "bold"), command=self.run_code)
        self.run_btn.pack(side="left")

        tk.Button(btn_frame, text="↺ Reset to Sample", command=self.reset_code,
                  font=("Helvetica", 11)).pack(side="left", padx=10)

        tk.Label(self, text="Output:", font=("Helvetica", 11, "bold"), bg=BG_COLOR,
                 fg=ACCENT_COLOR).pack(anchor="w", padx=20, pady=(10, 0))

        self.output_box = tk.Text(self, height=7, font=("Consolas", 11), bg="#1e1e1e", fg="#00ff88")
        self.output_box.pack(fill="both", expand=True, padx=20, pady=(5, 15))
        self.output_box.config(state="disabled")

    def on_language_change(self, event=None):
        self.code_box.delete("1.0", tk.END)
        self.code_box.insert(tk.END, DEFAULT_SNIPPETS[self.language_var.get()])

    def reset_code(self):
        self.code_box.delete("1.0", tk.END)
        self.code_box.insert(tk.END, DEFAULT_SNIPPETS[self.language_var.get()])

    def run_code(self):
        code = self.code_box.get("1.0", tk.END)
        language = self.language_var.get()

        self._set_output(f"Running {language} code...\n")
        self.run_btn.config(state="disabled")
        threading.Thread(target=self._run_code_thread, args=(language, code), daemon=True).start()

    def _run_code_thread(self, language, code):
        result = code_runner.run_code(language, code)
        self.after(0, self._show_run_result, result)

    def _show_run_result(self, result):
        if result["success"]:
            self._set_output(result["output"] or "(no output)")
        else:
            self._set_output("Error:\n" + result["error"])
        self.run_btn.config(state="normal")

    def _set_output(self, text):
        self.output_box.config(state="normal")
        self.output_box.delete("1.0", tk.END)
        self.output_box.insert(tk.END, text)
        self.output_box.config(state="disabled")


if __name__ == "__main__":
    app = CodeLearnApp()
    app.mainloop()