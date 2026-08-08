"""
main.py
Entry point for the Coding Learning App (Bilingual Bangla/English).

Tech stack: Python + Tkinter (GUI) + JSON (storage, multi-user) + local
            subprocess execution for Python/C/C++/Java + matplotlib (progress
            chart) + reportlab (certificate PDF)

Run with:  python main.py
Requires:  pip install matplotlib reportlab
           (also needs gcc/g++ on PATH for C/C++, and a JDK for Java)

UI language: the whole interface (buttons, titles, messages) shows in ONLY
one language at a time — English or Bangla — controlled by the "Eng | বাংলা"
pill in the top-right corner of every screen. Lesson/quiz content (loaded
from data.json) also switches with it.
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

# ---------------------------------------------------------------------------
# Central translation table. Every piece of static UI text lives here so the
# app can show ONLY English or ONLY Bangla at a time, never both together.
# ---------------------------------------------------------------------------
TEXTS = {
    # LoginScreen
    "app_name":            {"en": "CodeLearn", "bn": "CodeLearn"},
    "login_subtitle":       {"en": "Login", "bn": "সাইন ইন"},
    "username_label":       {"en": "Username or Email:", "bn": "ইউজারনেম বা ইমেইল:"},
    "email_hint_label":     {"en": "Email (only needed to sign up):", "bn": "ইমেইল (শুধু সাইন আপের জন্য প্রয়োজন):"},
    "password_label":       {"en": "Password:", "bn": "পাসওয়ার্ড:"},
    "remember_me":          {"en": "Remember Me for 30 days", "bn": "৩০ দিন মনে রাখো"},
    "login_btn":            {"en": "Login", "bn": "লগইন"},
    "signup_btn":           {"en": "Create New Account", "bn": "নতুন অ্যাকাউন্ট তৈরি করো"},
    "account_created_msg":  {"en": "Account created! You can log in now.", "bn": "অ্যাকাউন্ট তৈরি হয়েছে! এখন লগইন করতে পারো।"},

    # HomeScreen
    "app_subtitle":  {"en": "Learn Coding in Bangla & English", "bn": "বাংলা ও ইংরেজিতে কোডিং শেখো"},
    "lessons_btn":   {"en": "📚 Lessons", "bn": "📚 পাঠসমূহ"},
    "playground_btn": {"en": "💻 Code Playground", "bn": "💻 কোড লেখো"},
    "progress_btn":  {"en": "📊 My Progress", "bn": "📊 অগ্রগতি"},
    "certificate_btn": {"en": "🎓 Get Certificate", "bn": "🎓 সার্টিফিকেট"},
    "logout_btn":    {"en": "Logout", "bn": "লগআউট"},
    "xp_label":      {"en": "XP", "bn": "এক্সপি"},
    "streak_label":  {"en": "Streak", "bn": "ধারাবাহিকতা"},
    "days_label":    {"en": "days", "bn": "দিন"},
    "level_label":   {"en": "Level", "bn": "লেভেল"},

    # Shared
    "back_btn": {"en": "← Back", "bn": "← ফিরে যাও"},
    "output_label": {"en": "Output:", "bn": "আউটপুট:"},
    "run_code_btn": {"en": "▶ Run Code", "bn": "▶ কোড চালাও"},

    # ModuleSelectScreen
    "choose_module_title": {"en": "Choose a Module", "bn": "মডিউল বেছে নাও"},
    "python_module":  {"en": "🐍 Python Module", "bn": "🐍 পাইথন মডিউল"},
    "c_module":       {"en": "🔵 C Module", "bn": "🔵 সি মডিউল"},
    "cpp_module":     {"en": "🔷 C++ Module", "bn": "🔷 সি++ মডিউল"},

    # LessonListScreen
    "lessons_title_suffix": {"en": "Lessons", "bn": "পাঠসমূহ"},
    "take_quiz_btn": {"en": "📝 Take Module Quiz", "bn": "📝 কুইজ দাও"},

    # LessonDetailScreen
    "code_editor_label": {"en": "Code Editor (type or edit code below):",
                           "bn": "কোড এডিটর (নিচে কোড লেখো বা এডিট করো):"},
    "complete_lesson_btn": {"en": "✔ Mark Lesson Complete", "bn": "✔ পাঠ সম্পন্ন করো"},
    "great_job_title": {"en": "Great job!", "bn": "চমৎকার!"},
    "lesson_complete_msg": {"en": "Lesson marked complete. +20 XP", "bn": "পাঠ সম্পন্ন হয়েছে। +২০ এক্সপি"},

    # QuizScreen
    "quiz_title": {"en": "Quiz", "bn": "কুইজ"},
    "quit_quiz_btn": {"en": "✕ Quit Quiz", "bn": "✕ কুইজ ছাড়ো"},
    "question_progress": {"en": "Question {i} of {total}", "bn": "প্রশ্ন {i} এর {total}"},
    "no_quiz_msg": {"en": "No quiz available for this lesson yet.",
                     "bn": "এই পাঠের জন্য এখনো কোনো কুইজ নেই।"},
    "submit_answer_btn": {"en": "Submit Answer", "bn": "উত্তর জমা দাও"},
    "previous_btn": {"en": "← Previous", "bn": "← আগের"},
    "next_btn": {"en": "Next →", "bn": "পরের →"},
    "finish_btn": {"en": "Finish", "bn": "শেষ করো"},
    "quit_quiz_confirm_title": {"en": "Quit Quiz", "bn": "কুইজ ছাড়বে?"},
    "quit_quiz_confirm_msg": {"en": "Are you sure you want to quit? Your answered questions will still be saved.",
                               "bn": "তুমি কি নিশ্চিত কুইজ ছাড়তে চাও? তোমার উত্তর দেওয়া প্রশ্নগুলো সংরক্ষিত থাকবে।"},
    "no_answer_title": {"en": "No answer selected", "bn": "কোনো উত্তর বেছে নাওনি"},
    "no_answer_msg": {"en": "Please choose an option first.", "bn": "প্রথমে একটা অপশন বেছে নাও।"},
    "correct_feedback": {"en": "✅ Correct! +10 XP", "bn": "✅ সঠিক! +১০ এক্সপি"},
    "incorrect_feedback_prefix": {"en": "❌ Incorrect. Correct answer: ", "bn": "❌ ভুল উত্তর। সঠিক উত্তর: "},
    "quiz_finished_title": {"en": "Quiz Finished", "bn": "কুইজ শেষ"},
    "quiz_finished_msg": {"en": "You've reached the last question of this quiz!",
                           "bn": "তুমি এই কুইজের শেষ প্রশ্নে পৌঁছে গেছো!"},

    # ProgressScreen
    "progress_title": {"en": "My Progress", "bn": "অগ্রগতি"},
    "lessons_completed_label": {"en": "Lessons completed", "bn": "পাঠ সম্পন্ন হয়েছে"},

    # CertificateScreen
    "certificate_title": {"en": "Certificate", "bn": "সার্টিফিকেট"},
    "cert_congrats_msg": {"en": "🎉 Congratulations! You've completed all lessons. Click below to generate your certificate.",
                           "bn": "🎉 অভিনন্দন! তুমি সব পাঠ সম্পন্ন করেছো। সার্টিফিকেট তৈরি করতে নিচে ক্লিক করো।"},
    "cert_incomplete_msg": {"en": "You have completed {done} of {total} lessons. Complete all lessons to unlock your certificate.",
                             "bn": "তুমি {total} টির মধ্যে {done} টি পাঠ সম্পন্ন করেছো। সার্টিফিকেট আনলক করতে সব পাঠ সম্পন্ন করো।"},
    "generate_cert_btn": {"en": "🎓 Generate Certificate", "bn": "🎓 সার্টিফিকেট তৈরি করো"},
    "saved_to_label": {"en": "Saved to: {path}", "bn": "সংরক্ষিত হয়েছে: {path}"},
    "cert_generated_title": {"en": "Certificate Generated", "bn": "সার্টিফিকেট তৈরি হয়েছে"},
    "cert_generated_msg": {"en": "Your certificate was saved at:\n{path}", "bn": "তোমার সার্টিফিকেট এখানে সংরক্ষিত হয়েছে:\n{path}"},

    # PlaygroundScreen
    "playground_title": {"en": "Code Playground", "bn": "কোড লেখো"},
    "language_field_label": {"en": "Language:", "bn": "ভাষা:"},
    "reset_btn": {"en": "↺ Reset to Sample", "bn": "↺ নমুনায় ফিরে যাও"},
    "running_code_msg": {"en": "Running {language} code...\n", "bn": "{language} কোড চলছে...\n"},
    "running_generic_msg": {"en": "Running code...\n", "bn": "কোড চলছে...\n"},
    "no_output_msg": {"en": "(no output)", "bn": "(কোনো আউটপুট নেই)"},
    "error_prefix": {"en": "Error:\n", "bn": "ত্রুটি:\n"},
}


def tr(app, key, **kwargs):
    """Look up a translated string for the app's current language and
    format it with any given keyword arguments."""
    text = TEXTS[key][app.language]
    return text.format(**kwargs) if kwargs else text


class LanguageToggle(tk.Frame):
    """Reusable 'Eng | বাংলা' pill switcher for the top-right corner of a screen.
    Clicking a side switches app.language and calls on_change() so the current
    screen can re-render ALL of its text in the new language."""

    def __init__(self, parent, app, on_change=None):
        super().__init__(parent, bg="white", highlightbackground="#ddd",
                          highlightcolor="#ddd", highlightthickness=1, bd=0)
        self.app = app
        self.on_change = on_change

        self.eng_btn = tk.Label(self, text=" Eng ", font=("Helvetica", 10, "bold"), cursor="hand2")
        self.eng_btn.pack(side="left", padx=(2, 0), pady=3)
        tk.Label(self, text="|", bg="white", fg="#ccc").pack(side="left")
        self.bn_btn = tk.Label(self, text=" বাংলা ", font=("Helvetica", 10, "bold"), cursor="hand2")
        self.bn_btn.pack(side="left", padx=(0, 2), pady=3)

        self.eng_btn.bind("<Button-1>", lambda e: self.set_language("en"))
        self.bn_btn.bind("<Button-1>", lambda e: self.set_language("bn"))

        self.refresh_style()

    def refresh_style(self):
        active_bg, active_fg = BTN_COLOR, "white"
        inactive_bg, inactive_fg = "white", "#555"
        if self.app.language == "en":
            self.eng_btn.config(bg=active_bg, fg=active_fg)
            self.bn_btn.config(bg=inactive_bg, fg=inactive_fg)
        else:
            self.eng_btn.config(bg=inactive_bg, fg=inactive_fg)
            self.bn_btn.config(bg=active_bg, fg=active_fg)

    def set_language(self, lang):
        if self.app.language == lang:
            return
        self.app.language = lang
        self.refresh_style()
        if self.on_change:
            self.on_change()


class CodeLearnApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CodeLearn — Bilingual Coding Learning App")
        self.geometry("1000x680")
        self.configure(bg=BG_COLOR)

        self.data = dm.load_data()
        self.language = "en"          # UI language: "en" or "bn" — controls EVERYTHING
        self.current_user = None      # set after login
        self.current_module = None    # "python" / "c" / "cpp", set on module select

        container = tk.Frame(self, bg=BG_COLOR)
        container.pack(fill="both", expand=True)
        self.frames = {}

        for F in (LoginScreen, HomeScreen, ModuleSelectScreen, LessonListScreen, LessonDetailScreen,
                  QuizScreen, ProgressScreen, CertificateScreen, PlaygroundScreen):
            frame = F(container, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Auto-login: if a "Remember Me" session was saved last time, skip
        # the login screen and go straight into the app for that user.
        remembered_user = auth.load_session()
        if remembered_user and remembered_user in self.data["users"]:
            self.current_user = remembered_user
            self.show_frame("HomeScreen")
        else:
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
        auth.clear_session()
        self.show_frame("LoginScreen")


class LoginScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_COLOR)
        self.app = app

        LanguageToggle(self, app, on_change=self.apply_language).place(relx=1.0, y=15, anchor="ne", x=-20)

        card = tk.Frame(self, bg="white", padx=40, pady=30)
        card.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(card, text=tr(app, "app_name"), font=("Helvetica", 26, "bold"),
                 bg="white", fg=ACCENT_COLOR).pack(pady=(0, 5))
        self.subtitle_label = tk.Label(card, font=("Helvetica", 12), bg="white", fg="#777")
        self.subtitle_label.pack(pady=(0, 15))

        self.username_field_label = tk.Label(card, bg="white", font=("Helvetica", 11))
        self.username_field_label.pack(anchor="w")
        self.username_entry = tk.Entry(card, font=("Helvetica", 12), width=28)
        self.username_entry.pack(pady=(0, 10))

        self.email_field_label = tk.Label(card, bg="white", font=("Helvetica", 9), fg="#888")
        self.email_field_label.pack(anchor="w")
        self.email_entry = tk.Entry(card, font=("Helvetica", 12), width=28)
        self.email_entry.pack(pady=(0, 10))

        self.password_field_label = tk.Label(card, bg="white", font=("Helvetica", 11))
        self.password_field_label.pack(anchor="w")
        self.password_entry = tk.Entry(card, font=("Helvetica", 12), width=28, show="*")
        self.password_entry.pack(pady=(0, 10))

        self.remember_var = tk.BooleanVar(value=True)
        self.remember_check = tk.Checkbutton(card, variable=self.remember_var,
                                              bg="white", font=("Helvetica", 10))
        self.remember_check.pack(anchor="w", pady=(0, 12))

        self.login_btn = tk.Button(card, bg=BTN_COLOR, fg="white", font=("Helvetica", 12, "bold"),
                                    width=24, command=self.login)
        self.login_btn.pack(pady=4)
        self.signup_btn = tk.Button(card, bg="#27ae60", fg="white", font=("Helvetica", 11),
                                     width=24, command=self.signup)
        self.signup_btn.pack(pady=4)

        self.message_label = tk.Label(card, text="", bg="white", font=("Helvetica", 10), fg="#e74c3c",
                                       wraplength=320, justify="left")
        self.message_label.pack(pady=(10, 0))

        self.apply_language()

    def apply_language(self):
        app = self.app
        self.subtitle_label.config(text=tr(app, "login_subtitle"))
        self.username_field_label.config(text=tr(app, "username_label"))
        self.email_field_label.config(text=tr(app, "email_hint_label"))
        self.password_field_label.config(text=tr(app, "password_label"))
        self.remember_check.config(text=tr(app, "remember_me"))
        self.login_btn.config(text=tr(app, "login_btn"))
        self.signup_btn.config(text=tr(app, "signup_btn"))

    def on_show(self):
        self.username_entry.delete(0, tk.END)
        self.email_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self.message_label.config(text="")

    def login(self):
        identifier = self.username_entry.get().strip()
        password = self.password_entry.get()
        self.app.refresh_data()

        success, msg, username = auth.verify_login(self.app.data, identifier, password)
        if success:
            self.app.current_user = username
            if self.remember_var.get():
                auth.save_session(username)
            else:
                auth.clear_session()
            self.app.show_frame("HomeScreen")
        else:
            self.message_label.config(text=msg, fg="#e74c3c")

    def signup(self):
        username = self.username_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        self.app.refresh_data()

        success, msg = auth.create_user(self.app.data, username, password, email=email)
        if success:
            dm.save_data(self.app.data)
            self.message_label.config(text=tr(self.app, "account_created_msg"), fg="#27ae60")
        else:
            self.message_label.config(text=msg, fg="#e74c3c")


class HomeScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_COLOR)
        self.app = app

        top = tk.Frame(self, bg=BG_COLOR)
        top.pack(fill="x", padx=20, pady=10)
        self.logout_btn = tk.Button(top, command=app.logout)
        self.logout_btn.pack(side="right")
        LanguageToggle(top, app, on_change=self.apply_language).pack(side="right", padx=(0, 10))

        tk.Label(self, text=tr(app, "app_name"), font=("Helvetica", 30, "bold"),
                 bg=BG_COLOR, fg=ACCENT_COLOR).pack(pady=(20, 5))
        self.subtitle_label = tk.Label(self, font=("Helvetica", 13), bg=BG_COLOR, fg="#555")
        self.subtitle_label.pack(pady=(0, 30))

        btn_style = {"font": ("Helvetica", 13), "width": 28, "bg": BTN_COLOR,
                     "fg": "white", "bd": 0, "pady": 10, "cursor": "hand2"}

        self.lessons_btn = tk.Button(self, command=lambda: app.show_frame("ModuleSelectScreen"), **btn_style)
        self.lessons_btn.pack(pady=6)
        self.playground_btn = tk.Button(self, command=lambda: app.show_frame("PlaygroundScreen"),
                                         **{**btn_style, "bg": "#8e44ad"})
        self.playground_btn.pack(pady=6)
        self.progress_btn = tk.Button(self, command=lambda: app.show_frame("ProgressScreen"), **btn_style)
        self.progress_btn.pack(pady=6)
        self.certificate_btn = tk.Button(self, command=lambda: app.show_frame("CertificateScreen"), **btn_style)
        self.certificate_btn.pack(pady=6)

        self.status_label = tk.Label(self, text="", font=("Helvetica", 11),
                                      bg=BG_COLOR, fg=ACCENT_COLOR)
        self.status_label.pack(pady=25)

        self.apply_language()

    def apply_language(self):
        app = self.app
        self.logout_btn.config(text=tr(app, "logout_btn"))
        self.subtitle_label.config(text=tr(app, "app_subtitle"))
        self.lessons_btn.config(text=tr(app, "lessons_btn"))
        self.playground_btn.config(text=tr(app, "playground_btn"))
        self.progress_btn.config(text=tr(app, "progress_btn"))
        self.certificate_btn.config(text=tr(app, "certificate_btn"))
        self.render_status()

    def render_status(self):
        app = self.app
        if not app.current_user:
            return
        user = app.get_current_user_data()
        level = dm.get_level(user["xp"])
        self.status_label.config(
            text=f"👤 {app.current_user}   |   ⭐ {tr(app, 'xp_label')}: {user['xp']}   |   "
                 f"🔥 {tr(app, 'streak_label')}: {user['streak']} {tr(app, 'days_label')}   |   "
                 f"🏆 {tr(app, 'level_label')}: {level}"
        )

    def on_show(self):
        self.app.refresh_data()
        self.render_status()


class ModuleSelectScreen(tk.Frame):
    """Lets the user pick which language module to study: Python, C, or C++."""

    MODULE_KEYS = [
        ("python", "python_module", "#3776ab"),
        ("c", "c_module", "#5c6bc0"),
        ("cpp", "cpp_module", "#00599c"),
    ]

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_COLOR)
        self.app = app

        top = tk.Frame(self, bg=BG_COLOR)
        top.pack(fill="x", pady=15, padx=20)
        self.back_btn = tk.Button(top, command=lambda: app.show_frame("HomeScreen"))
        self.back_btn.pack(side="left")
        self.title_label = tk.Label(top, font=("Helvetica", 20, "bold"), bg=BG_COLOR, fg=ACCENT_COLOR)
        self.title_label.pack(side="left", padx=20)
        LanguageToggle(top, app, on_change=self.apply_language).pack(side="right")

        body = tk.Frame(self, bg=BG_COLOR)
        body.pack(expand=True)

        self.module_buttons = []
        for module_key, text_key, color in self.MODULE_KEYS:
            btn = tk.Button(body, font=("Helvetica", 14, "bold"), width=30, bg=color,
                             fg="white", bd=0, pady=15, cursor="hand2",
                             command=lambda m=module_key: self.open_module(m))
            btn.pack(pady=12)
            self.module_buttons.append((btn, text_key))

        self.apply_language()

    def apply_language(self):
        app = self.app
        self.back_btn.config(text=tr(app, "back_btn"))
        self.title_label.config(text=tr(app, "choose_module_title"))
        for btn, text_key in self.module_buttons:
            btn.config(text=tr(app, text_key))

    def open_module(self, module_key):
        self.app.current_module = module_key
        lesson_list = self.app.frames["LessonListScreen"]
        lesson_list.on_show()
        self.app.show_frame("LessonListScreen")


class LessonListScreen(tk.Frame):
    MODULE_DISPLAY_NAMES = {"python": "Python", "c": "C", "cpp": "C++"}

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_COLOR)
        self.app = app

        top = tk.Frame(self, bg=BG_COLOR)
        top.pack(fill="x", pady=15, padx=20)
        self.back_btn = tk.Button(top, command=lambda: app.show_frame("ModuleSelectScreen"))
        self.back_btn.pack(side="left")
        self.title_label = tk.Label(top, font=("Helvetica", 20, "bold"),
                                     bg=BG_COLOR, fg=ACCENT_COLOR)
        self.title_label.pack(side="left", padx=20)

        self.quiz_btn = tk.Button(top, bg="#8e44ad", fg="white",
                                   font=("Helvetica", 11, "bold"), command=self.start_quiz)
        self.quiz_btn.pack(side="right")
        LanguageToggle(top, app, on_change=self.on_show).pack(side="right", padx=10)

        self.listbox = tk.Listbox(self, font=("Helvetica", 13), height=15)
        self.listbox.pack(fill="both", expand=True, padx=20, pady=10)
        self.listbox.bind("<<ListboxSelect>>", self.select_lesson)

        self.apply_language()

    def apply_language(self):
        app = self.app
        self.back_btn.config(text=tr(app, "back_btn"))
        self.quiz_btn.config(text=tr(app, "take_quiz_btn"))

    def on_show(self):
        self.app.refresh_data()
        self.apply_language()
        module = self.app.current_module
        module_name = self.MODULE_DISPLAY_NAMES.get(module, "")
        self.title_label.config(text=f"{module_name} {tr(self.app, 'lessons_title_suffix')}")

        self.listbox.delete(0, tk.END)
        self.lesson_ids = []
        completed = self.app.get_current_user_data()["completed_lessons"]
        for lesson in dm.get_lessons_by_module(self.app.data, module):
            mark = "✅ " if lesson["id"] in completed else "⬜ "
            title = lesson["title_bn"] if self.app.language == "bn" else lesson["title_en"]
            self.listbox.insert(tk.END, f"{mark}{title}")
            self.lesson_ids.append(lesson["id"])

    def select_lesson(self, event):
        selection = self.listbox.curselection()
        if not selection:
            return
        lesson_id = self.lesson_ids[selection[0]]
        detail_frame = self.app.frames["LessonDetailScreen"]
        detail_frame.load_lesson(lesson_id)
        self.app.show_frame("LessonDetailScreen")

    def start_quiz(self):
        quiz_frame = self.app.frames["QuizScreen"]
        quiz_frame.load_quiz(self.app.current_module)
        self.app.show_frame("QuizScreen")


class LessonDetailScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_COLOR)
        self.app = app
        self.current_lesson = None

        top = tk.Frame(self, bg=BG_COLOR)
        top.pack(fill="x", pady=10, padx=20)
        self.back_btn = tk.Button(top, command=lambda: app.show_frame("LessonListScreen"))
        self.back_btn.pack(side="left")
        LanguageToggle(top, app, on_change=self.apply_language).pack(side="right")

        self.title_label = tk.Label(self, font=("Helvetica", 18, "bold"), bg=BG_COLOR, fg=ACCENT_COLOR)
        self.title_label.pack(pady=(5, 5), padx=20, anchor="w")

        self.content_label = tk.Label(self, font=("Helvetica", 12), bg=BG_COLOR, fg="#333",
                                       wraplength=930, justify="left")
        self.content_label.pack(pady=(0, 10), padx=20, anchor="w")

        self.code_editor_label = tk.Label(self, font=("Helvetica", 11, "bold"),
                                           bg=BG_COLOR, fg=ACCENT_COLOR)
        self.code_editor_label.pack(anchor="w", padx=20)

        self.code_box = tk.Text(self, height=8, font=("Consolas", 12), bg="#2d2d2d", fg="#f8f8f2",
                                 insertbackground="white")
        self.code_box.pack(fill="x", padx=20, pady=(5, 10))

        btn_frame = tk.Frame(self, bg=BG_COLOR)
        btn_frame.pack(fill="x", padx=20)
        self.run_btn = tk.Button(btn_frame, bg="#27ae60", fg="white",
                                  font=("Helvetica", 11, "bold"), command=self.run_code)
        self.run_btn.pack(side="left")

        self.complete_btn = tk.Button(btn_frame, command=self.complete_lesson,
                                       bg=BTN_COLOR, fg="white", font=("Helvetica", 11))
        self.complete_btn.pack(side="left", padx=10)

        self.output_title_label = tk.Label(self, font=("Helvetica", 11, "bold"), bg=BG_COLOR,
                                            fg=ACCENT_COLOR)
        self.output_title_label.pack(anchor="w", padx=20, pady=(10, 0))

        self.output_box = tk.Text(self, height=6, font=("Consolas", 11), bg="#1e1e1e", fg="#00ff88")
        self.output_box.pack(fill="both", expand=True, padx=20, pady=(5, 15))
        self.output_box.config(state="disabled")

        self.apply_language()

    def apply_language(self):
        app = self.app
        self.back_btn.config(text=tr(app, "back_btn"))
        self.code_editor_label.config(text=tr(app, "code_editor_label"))
        self.run_btn.config(text=tr(app, "run_code_btn"))
        self.complete_btn.config(text=tr(app, "complete_lesson_btn"))
        self.output_title_label.config(text=tr(app, "output_label"))
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

        self._set_output(tr(self.app, "running_generic_msg"))
        self.run_btn.config(state="disabled")
        threading.Thread(target=self._run_code_thread, args=(language, code), daemon=True).start()

    def _run_code_thread(self, language, code):
        result = code_runner.run_code(language, code)
        self.after(0, self._show_run_result, result)

    def _show_run_result(self, result):
        if result["success"]:
            self._set_output(result["output"] or tr(self.app, "no_output_msg"))
        else:
            self._set_output(tr(self.app, "error_prefix") + result["error"])
        self.run_btn.config(state="normal")

    def _set_output(self, text):
        self.output_box.config(state="normal")
        self.output_box.delete("1.0", tk.END)
        self.output_box.insert(tk.END, text)
        self.output_box.config(state="disabled")

    def complete_lesson(self):
        dm.mark_lesson_complete(self.app.data, self.app.current_user, self.current_lesson["id"])
        self.app.refresh_data()
        messagebox.showinfo(tr(self.app, "great_job_title"), tr(self.app, "lesson_complete_msg"))


class QuizScreen(tk.Frame):
    """Multi-question quiz for a module, with Next/Previous navigation,
    instant correct-answer feedback after submitting, and a Quit option."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_COLOR)
        self.app = app
        self.quiz_list = []       # all questions for the current module
        self.current_index = 0
        self.session_answers = {}  # {quiz_id: {"selected": str, "submitted": bool, "correct": bool}}
        self.selected_option = tk.StringVar()

        top = tk.Frame(self, bg=BG_COLOR)
        top.pack(fill="x", pady=15, padx=20)
        self.quit_btn = tk.Button(top, command=self.quit_quiz,
                                   bg="#e74c3c", fg="white", font=("Helvetica", 10, "bold"))
        self.quit_btn.pack(side="left")
        self.title_label = tk.Label(top, font=("Helvetica", 20, "bold"),
                                     bg=BG_COLOR, fg=ACCENT_COLOR)
        self.title_label.pack(side="left", padx=20)

        self.progress_label = tk.Label(top, font=("Helvetica", 11), bg=BG_COLOR, fg="#777")
        self.progress_label.pack(side="right")
        LanguageToggle(top, app, on_change=self.apply_language).pack(side="right", padx=10)

        self.question_label = tk.Label(self, font=("Helvetica", 14), bg=BG_COLOR, fg="#333",
                                        wraplength=900, justify="left")
        self.question_label.pack(pady=20, padx=20, anchor="w")

        self.options_frame = tk.Frame(self, bg=BG_COLOR)
        self.options_frame.pack(padx=20, anchor="w")

        self.submit_btn = tk.Button(self, bg=BTN_COLOR, fg="white",
                                     font=("Helvetica", 12, "bold"), command=self.submit_answer)
        self.submit_btn.pack(pady=15)

        self.result_label = tk.Label(self, font=("Helvetica", 13, "bold"), bg=BG_COLOR,
                                      wraplength=900, justify="left")
        self.result_label.pack()

        nav_frame = tk.Frame(self, bg=BG_COLOR)
        nav_frame.pack(pady=25)
        self.prev_btn = tk.Button(nav_frame, font=("Helvetica", 11),
                                   width=14, command=self.go_previous)
        self.prev_btn.pack(side="left", padx=8)
        self.next_btn = tk.Button(nav_frame, font=("Helvetica", 11),
                                   width=14, bg="#8e44ad", fg="white", command=self.go_next)
        self.next_btn.pack(side="left", padx=8)

        self.apply_language()

    def apply_language(self):
        app = self.app
        self.quit_btn.config(text=tr(app, "quit_quiz_btn"))
        self.title_label.config(text=tr(app, "quiz_title"))
        self.submit_btn.config(text=tr(app, "submit_answer_btn"))
        self.prev_btn.config(text=tr(app, "previous_btn"))
        self.render_question()

    def load_quiz(self, module):
        self.app.refresh_data()
        self.quiz_list = dm.get_quizzes_by_module(self.app.data, module)
        self.current_index = 0
        self.session_answers = {}
        self.render_question()

    def quit_quiz(self):
        if messagebox.askyesno(tr(self.app, "quit_quiz_confirm_title"), tr(self.app, "quit_quiz_confirm_msg")):
            self.app.show_frame("LessonListScreen")

    def render_question(self):
        app = self.app
        for widget in self.options_frame.winfo_children():
            widget.destroy()
        self.result_label.config(text="")

        if not self.quiz_list:
            self.question_label.config(text=tr(app, "no_quiz_msg"))
            self.progress_label.config(text="")
            self.submit_btn.config(state="disabled")
            self.prev_btn.config(state="disabled")
            self.next_btn.config(state="disabled", text=tr(app, "next_btn"))
            return

        quiz = self.quiz_list[self.current_index]
        total = len(self.quiz_list)
        self.progress_label.config(text=tr(app, "question_progress", i=self.current_index + 1, total=total))

        question = quiz["question_bn"] if app.language == "bn" else quiz["question_en"]
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
                              text=tr(app, "finish_btn") if self.current_index == total - 1 else tr(app, "next_btn"))

    def submit_answer(self):
        if not self.quiz_list:
            return
        quiz = self.quiz_list[self.current_index]
        chosen = self.selected_option.get()
        if not chosen:
            messagebox.showwarning(tr(self.app, "no_answer_title"), tr(self.app, "no_answer_msg"))
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
        app = self.app
        if correct:
            self.result_label.config(text=tr(app, "correct_feedback"), fg="#27ae60")
        else:
            self.result_label.config(
                text=tr(app, "incorrect_feedback_prefix") + quiz["answer"], fg="#e74c3c"
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
            messagebox.showinfo(tr(self.app, "quiz_finished_title"), tr(self.app, "quiz_finished_msg"))


class ProgressScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_COLOR)
        self.app = app

        top = tk.Frame(self, bg=BG_COLOR)
        top.pack(fill="x", pady=15, padx=20)
        self.back_btn = tk.Button(top, command=lambda: app.show_frame("HomeScreen"))
        self.back_btn.pack(side="left")
        self.title_label = tk.Label(top, font=("Helvetica", 20, "bold"),
                                     bg=BG_COLOR, fg=ACCENT_COLOR)
        self.title_label.pack(side="left", padx=20)
        LanguageToggle(top, app, on_change=self.on_show).pack(side="right")

        self.stats_label = tk.Label(self, font=("Helvetica", 13), bg=BG_COLOR, fg="#333")
        self.stats_label.pack(pady=10)

        self.chart_container = tk.Frame(self, bg=BG_COLOR)
        self.chart_container.pack(fill="both", expand=True, padx=20, pady=10)

        self.apply_language()

    def apply_language(self):
        app = self.app
        self.back_btn.config(text=tr(app, "back_btn"))
        self.title_label.config(text=tr(app, "progress_title"))

    def on_show(self):
        self.app.refresh_data()
        self.apply_language()
        app = self.app
        data = app.data
        user = app.get_current_user_data()

        pct = dm.get_progress_percent(data, app.current_user)
        level = dm.get_level(user["xp"])
        self.stats_label.config(
            text=f"{tr(app, 'lessons_completed_label')}: {pct}%   |   {tr(app, 'xp_label')}: {user['xp']}   |   "
                 f"{tr(app, 'level_label')}: {level}   |   {tr(app, 'streak_label')}: {user['streak']} {tr(app, 'days_label')}"
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
        self.back_btn = tk.Button(top, command=lambda: app.show_frame("HomeScreen"))
        self.back_btn.pack(side="left")
        self.title_label = tk.Label(top, font=("Helvetica", 20, "bold"),
                                     bg=BG_COLOR, fg=ACCENT_COLOR)
        self.title_label.pack(side="left", padx=20)
        LanguageToggle(top, app, on_change=self.on_show).pack(side="right")

        self.info_label = tk.Label(self, font=("Helvetica", 13), bg=BG_COLOR, fg="#333",
                                    wraplength=900, justify="left")
        self.info_label.pack(pady=30, padx=20)

        self.gen_btn = tk.Button(self, bg="#e67e22", fg="white",
                                  font=("Helvetica", 13, "bold"), command=self.generate)
        self.gen_btn.pack(pady=10)

        self.path_label = tk.Label(self, font=("Helvetica", 11), bg=BG_COLOR, fg="#555")
        self.path_label.pack(pady=10)

        self.apply_language()

    def apply_language(self):
        app = self.app
        self.back_btn.config(text=tr(app, "back_btn"))
        self.title_label.config(text=tr(app, "certificate_title"))
        self.gen_btn.config(text=tr(app, "generate_cert_btn"))

    def on_show(self):
        self.app.refresh_data()
        self.apply_language()
        app = self.app
        data = app.data
        user = app.get_current_user_data()
        total = len(data["lessons"])
        done = len(user["completed_lessons"])

        if done >= total and total > 0:
            self.info_label.config(text=tr(app, "cert_congrats_msg"))
            self.gen_btn.config(state="normal")
        else:
            self.info_label.config(text=tr(app, "cert_incomplete_msg", done=done, total=total))
            self.gen_btn.config(state="disabled")

    def generate(self):
        app = self.app
        username = app.current_user
        path = generate_certificate(username, course_title="CodeLearn Fundamentals")
        self.path_label.config(text=tr(app, "saved_to_label", path=path))
        messagebox.showinfo(tr(app, "cert_generated_title"), tr(app, "cert_generated_msg", path=path))


class PlaygroundScreen(tk.Frame):
    """Free-form code editor: pick ANY supported language and write ANY code,
    not tied to a specific lesson."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_COLOR)
        self.app = app

        top = tk.Frame(self, bg=BG_COLOR)
        top.pack(fill="x", pady=10, padx=20)
        self.back_btn = tk.Button(top, command=lambda: app.show_frame("HomeScreen"))
        self.back_btn.pack(side="left")
        self.title_label = tk.Label(top, font=("Helvetica", 20, "bold"),
                                     bg=BG_COLOR, fg=ACCENT_COLOR)
        self.title_label.pack(side="left", padx=20)
        LanguageToggle(top, app, on_change=self.apply_language).pack(side="right")

        lang_frame = tk.Frame(self, bg=BG_COLOR)
        lang_frame.pack(fill="x", padx=20, pady=(5, 0))
        self.language_field_label = tk.Label(lang_frame, font=("Helvetica", 11, "bold"),
                                              bg=BG_COLOR, fg=ACCENT_COLOR)
        self.language_field_label.pack(side="left")

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
        self.run_btn = tk.Button(btn_frame, bg="#27ae60", fg="white",
                                  font=("Helvetica", 11, "bold"), command=self.run_code)
        self.run_btn.pack(side="left")

        self.reset_btn = tk.Button(btn_frame, command=self.reset_code, font=("Helvetica", 11))
        self.reset_btn.pack(side="left", padx=10)

        self.output_title_label = tk.Label(self, font=("Helvetica", 11, "bold"), bg=BG_COLOR,
                                            fg=ACCENT_COLOR)
        self.output_title_label.pack(anchor="w", padx=20, pady=(10, 0))

        self.output_box = tk.Text(self, height=7, font=("Consolas", 11), bg="#1e1e1e", fg="#00ff88")
        self.output_box.pack(fill="both", expand=True, padx=20, pady=(5, 15))
        self.output_box.config(state="disabled")

        self.apply_language()

    def apply_language(self):
        app = self.app
        self.back_btn.config(text=tr(app, "back_btn"))
        self.title_label.config(text=tr(app, "playground_title"))
        self.language_field_label.config(text=tr(app, "language_field_label"))
        self.run_btn.config(text=tr(app, "run_code_btn"))
        self.reset_btn.config(text=tr(app, "reset_btn"))
        self.output_title_label.config(text=tr(app, "output_label"))

    def on_language_change(self, event=None):
        self.code_box.delete("1.0", tk.END)
        self.code_box.insert(tk.END, DEFAULT_SNIPPETS[self.language_var.get()])

    def reset_code(self):
        self.code_box.delete("1.0", tk.END)
        self.code_box.insert(tk.END, DEFAULT_SNIPPETS[self.language_var.get()])

    def run_code(self):
        code = self.code_box.get("1.0", tk.END)
        language = self.language_var.get()

        self._set_output(tr(self.app, "running_code_msg", language=language))
        self.run_btn.config(state="disabled")
        threading.Thread(target=self._run_code_thread, args=(language, code), daemon=True).start()

    def _run_code_thread(self, language, code):
        result = code_runner.run_code(language, code)
        self.after(0, self._show_run_result, result)

    def _show_run_result(self, result):
        if result["success"]:
            self._set_output(result["output"] or tr(self.app, "no_output_msg"))
        else:
            self._set_output(tr(self.app, "error_prefix") + result["error"])
        self.run_btn.config(state="normal")

    def _set_output(self, text):
        self.output_box.config(state="normal")
        self.output_box.delete("1.0", tk.END)
        self.output_box.insert(tk.END, text)
        self.output_box.config(state="disabled")


if __name__ == "__main__":
    app = CodeLearnApp()
    app.mainloop()