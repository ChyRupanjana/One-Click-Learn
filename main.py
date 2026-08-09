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
    "signin_tab":            {"en": "Sign In", "bn": "সাইন ইন"},
    "signup_tab":            {"en": "Sign Up", "bn": "সাইন আপ"},
    "signin_username_label": {"en": "Username or Email:", "bn": "ইউজারনেম বা ইমেইল:"},
    "signup_username_label": {"en": "Username:", "bn": "ইউজারনেম:"},
    "email_hint_label":     {"en": "Email (optional):", "bn": "ইমেইল (ঐচ্ছিক):"},
    "password_label":       {"en": "Password:", "bn": "পাসওয়ার্ড:"},
    "confirm_password_label": {"en": "Confirm Password:", "bn": "পাসওয়ার্ড নিশ্চিত করো:"},
    "remember_me":          {"en": "Remember Me for 30 days", "bn": "৩০ দিন মনে রাখো"},
    "login_btn":            {"en": "Sign In", "bn": "সাইন ইন করো"},
    "signup_btn":           {"en": "Create Account", "bn": "অ্যাকাউন্ট তৈরি করো"},
    "no_account_prompt":    {"en": "Don't have an account?  Sign Up", "bn": "অ্যাকাউন্ট নেই?  সাইন আপ করো"},
    "have_account_prompt":  {"en": "Already have an account?  Sign In", "bn": "আগে থেকেই অ্যাকাউন্ট আছে?  সাইন ইন করো"},
    "passwords_mismatch_msg": {"en": "Passwords do not match.", "bn": "পাসওয়ার্ড দুটো মিলছে না।"},
    "account_created_msg":  {"en": "Account created! Please sign in.", "bn": "অ্যাকাউন্ট তৈরি হয়েছে! এখন সাইন ইন করো।"},

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

    # ContestListScreen / ContestScreen / ProblemScreen
    "contests_btn": {"en": "🏆 Contests", "bn": "🏆 কনটেস্ট"},
    "contest_list_title": {"en": "Contests", "bn": "কনটেস্ট সমূহ"},
    "locked_label": {"en": "🔒 Locked — complete {n} more lesson(s) to unlock",
                      "bn": "🔒 লক করা আছে — আনলক করতে আরও {n}টা lesson শেষ করো"},
    "unlocked_label": {"en": "🔓 Unlocked", "bn": "🔓 আনলক হয়েছে"},
    "problems_solved_label": {"en": "Solved: {solved}/{total}", "bn": "সমাধান হয়েছে: {solved}/{total}"},
    "difficulty_easy": {"en": "Easy", "bn": "সহজ"},
    "difficulty_medium": {"en": "Medium", "bn": "মাঝারি"},
    "difficulty_hard": {"en": "Hard", "bn": "কঠিন"},
    "solved_mark": {"en": "✅ Solved", "bn": "✅ সমাধান হয়েছে"},
    "not_solved_mark": {"en": "⬜ Not solved", "bn": "⬜ সমাধান হয়নি"},
    "submit_btn": {"en": "Submit Solution", "bn": "সমাধান জমা দাও"},
    "test_case_label": {"en": "Test Case {n}", "bn": "টেস্ট কেস {n}"},
    "passed_label": {"en": "PASSED", "bn": "পাস"},
    "failed_label": {"en": "FAILED", "bn": "ফেইল"},
    "all_tests_passed_msg": {"en": "🎉 All test cases passed! Problem solved.",
                              "bn": "🎉 সব টেস্ট কেস পাস হয়েছে! সমস্যাটি সমাধান হয়েছে।"},
    "some_tests_failed_msg": {"en": "Some test cases failed. Try again!",
                               "bn": "কিছু টেস্ট কেস ফেইল করেছে। আবার চেষ্টা করো!"},
    "already_solved_msg": {"en": "Already solved earlier — resubmitting won't award extra XP.",
                            "bn": "আগেই সমাধান হয়েছিল — আবার জমা দিলে অতিরিক্ত এক্সপি পাবে না।"},
    "problem_solved_title": {"en": "Problem Solved!", "bn": "সমস্যা সমাধান হয়েছে!"},
    "problem_solved_msg": {"en": "Great work! +{xp} XP", "bn": "চমৎকার! +{xp} এক্সপি"},
    "input_label": {"en": "Input", "bn": "ইনপুট"},
    "expected_label": {"en": "Expected", "bn": "প্রত্যাশিত"},
    "your_output_label": {"en": "Your Output", "bn": "তোমার আউটপুট"},
    "locked_contest_msg": {"en": "This contest is still locked.", "bn": "এই কনটেস্টটি এখনো লক করা আছে।"},
    "contest_days_remaining": {"en": "⏳ {days} day(s) remaining to submit",
                                "bn": "⏳ সাবমিট করার জন্য আর {days} দিন বাকি"},
    "contest_expired_msg": {"en": "⛔ Submission deadline has passed (7 days). You can still read the problems, but can no longer submit.",
                             "bn": "⛔ সাবমিট করার সময়সীমা (৭ দিন) শেষ হয়ে গেছে। তুমি এখনো প্রবলেম পড়তে পারবে, কিন্তু সাবমিট করতে পারবে না।"},
    "contest_deadline_expired_short": {"en": "⛔ Deadline expired — read-only", "bn": "⛔ সময়সীমা শেষ — শুধু পড়া যাবে"},

    # LeaderboardScreen
    "leaderboard_btn": {"en": "🏆 Leaderboard", "bn": "🏆 লিডারবোর্ড"},
    "leaderboard_title": {"en": "Leaderboard", "bn": "লিডারবোর্ড"},
    "rank_col": {"en": "Rank", "bn": "র‍্যাংক"},
    "team_col": {"en": "Username", "bn": "ইউজারনেম"},
    "score_col": {"en": "Score", "bn": "স্কোর"},
    "penalty_col": {"en": "Penalty", "bn": "পেনাল্টি"},
    "no_submissions_msg": {"en": "No one has submitted to this contest yet.",
                            "bn": "এই কনটেস্টে এখনো কেউ সাবমিট করেনি।"},

    # Admin / Student Management
    "admin_login_link": {"en": "⚙ Admin Login", "bn": "⚙ অ্যাডমিন লগইন"},
    "admin_login_title": {"en": "Admin Login", "bn": "অ্যাডমিন লগইন"},
    "admin_password_label": {"en": "Admin Password:", "bn": "অ্যাডমিন পাসওয়ার্ড:"},
    "admin_login_btn": {"en": "Enter", "bn": "প্রবেশ করো"},
    "admin_wrong_password_msg": {"en": "Incorrect admin password.", "bn": "ভুল অ্যাডমিন পাসওয়ার্ড।"},
    "student_mgmt_title": {"en": "Student Management", "bn": "স্টুডেন্ট ম্যানেজমেন্ট"},
    "admin_logout_btn": {"en": "Exit Admin", "bn": "অ্যাডমিন থেকে বের হও"},
    "col_username": {"en": "Username", "bn": "ইউজারনেম"},
    "col_email": {"en": "Email", "bn": "ইমেইল"},
    "col_xp": {"en": "XP", "bn": "এক্সপি"},
    "col_level": {"en": "Level", "bn": "লেভেল"},
    "col_streak": {"en": "Streak", "bn": "ধারাবাহিকতা"},
    "col_lessons": {"en": "Lessons", "bn": "লেসন"},
    "col_quizzes": {"en": "Quizzes", "bn": "কুইজ"},
    "col_contests": {"en": "Contests", "bn": "কনটেস্ট"},
    "col_certificate": {"en": "Certificate", "bn": "সার্টিফিকেট"},
    "col_actions": {"en": "Actions", "bn": "একশন"},
    "cert_yes": {"en": "✅ Yes", "bn": "✅ হ্যাঁ"},
    "cert_no": {"en": "— No", "bn": "— না"},
    "edit_btn": {"en": "Edit", "bn": "এডিট"},
    "delete_btn": {"en": "Delete", "bn": "ডিলিট"},
    "confirm_delete_title": {"en": "Delete Student", "bn": "স্টুডেন্ট ডিলিট"},
    "confirm_delete_msg": {"en": "Permanently delete '{username}'? This cannot be undone.",
                            "bn": "'{username}' কে স্থায়ীভাবে ডিলিট করবে? এটা আর ফেরানো যাবে না।"},
    "edit_student_title": {"en": "Edit Student: {username}", "bn": "স্টুডেন্ট এডিট করো: {username}"},
    "xp_field_label": {"en": "XP:", "bn": "এক্সপি:"},
    "save_btn": {"en": "Save", "bn": "সেভ করো"},
    "cancel_btn": {"en": "Cancel", "bn": "বাতিল"},
    "reset_progress_btn": {"en": "Reset All Progress", "bn": "সব প্রোগ্রেস রিসেট করো"},
    "confirm_reset_title": {"en": "Reset Progress", "bn": "প্রোগ্রেস রিসেট"},
    "confirm_reset_msg": {"en": "This clears all lessons, quizzes, and contest progress for '{username}' (XP resets to 0). Continue?",
                           "bn": "এতে '{username}' এর সব লেসন, কুইজ, আর কনটেস্ট প্রোগ্রেস মুছে যাবে (এক্সপি ০ হয়ে যাবে)। এগিয়ে যাবে?"},
    "no_students_msg": {"en": "No students have registered yet.", "bn": "এখনো কোনো স্টুডেন্ট রেজিস্টার করেনি।"},
    "invalid_xp_msg": {"en": "Please enter a valid non-negative number for XP.",
                        "bn": "এক্সপির জন্য একটা সঠিক অ-ঋণাত্মক সংখ্যা দাও।"},
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
        self.contests = dm.load_contests()
        self.language = "en"          # UI language: "en" or "bn" — controls EVERYTHING
        self.current_user = None      # set after login
        self.current_module = None    # "python" / "c" / "cpp", set on module select
        self.current_contest = None   # set on contest select
        self.current_problem = None   # set on problem select

        container = tk.Frame(self, bg=BG_COLOR)
        container.pack(fill="both", expand=True)
        self.frames = {}

        for F in (LoginScreen, HomeScreen, ModuleSelectScreen, LessonListScreen, LessonDetailScreen,
                  QuizScreen, ProgressScreen, CertificateScreen, PlaygroundScreen,
                  ContestListScreen, ContestScreen, ProblemScreen, LeaderboardScreen,
                  AdminLoginScreen, StudentManagementScreen):
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
    """Real-app-style auth screen: a 'Sign In' / 'Sign Up' tab pair up top,
    and only the matching form below. New users switch to Sign Up, create
    their account with a username + password, then switch back to Sign In
    to actually log in with those credentials."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_COLOR)
        self.app = app
        self.mode = "signin"   # "signin" or "signup"

        LanguageToggle(self, app, on_change=self.apply_language).place(relx=1.0, y=15, anchor="ne", x=-20)

        card = tk.Frame(self, bg="white", padx=40, pady=30)
        card.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(card, text=tr(app, "app_name"), font=("Helvetica", 26, "bold"),
                 bg="white", fg=ACCENT_COLOR).pack(pady=(0, 15))

        # --- Tab pair: Sign In | Sign Up ---
        tabs = tk.Frame(card, bg="white")
        tabs.pack(pady=(0, 18))
        self.signin_tab_btn = tk.Label(tabs, font=("Helvetica", 12, "bold"), width=12,
                                        pady=8, cursor="hand2")
        self.signin_tab_btn.pack(side="left")
        self.signup_tab_btn = tk.Label(tabs, font=("Helvetica", 12, "bold"), width=12,
                                        pady=8, cursor="hand2")
        self.signup_tab_btn.pack(side="left")
        self.signin_tab_btn.bind("<Button-1>", lambda e: self.switch_mode("signin"))
        self.signup_tab_btn.bind("<Button-1>", lambda e: self.switch_mode("signup"))

        # --- Sign In form ---
        self.signin_frame = tk.Frame(card, bg="white")

        self.signin_username_field_label = tk.Label(self.signin_frame, bg="white", font=("Helvetica", 11))
        self.signin_username_field_label.pack(anchor="w")
        self.signin_username_entry = tk.Entry(self.signin_frame, font=("Helvetica", 12), width=28)
        self.signin_username_entry.pack(pady=(0, 10))

        self.signin_password_field_label = tk.Label(self.signin_frame, bg="white", font=("Helvetica", 11))
        self.signin_password_field_label.pack(anchor="w")
        self.signin_password_entry = tk.Entry(self.signin_frame, font=("Helvetica", 12), width=28, show="*")
        self.signin_password_entry.pack(pady=(0, 10))

        self.remember_var = tk.BooleanVar(value=True)
        self.remember_check = tk.Checkbutton(self.signin_frame, variable=self.remember_var,
                                              bg="white", font=("Helvetica", 10))
        self.remember_check.pack(anchor="w", pady=(0, 12))

        self.login_btn = tk.Button(self.signin_frame, bg=BTN_COLOR, fg="white",
                                    font=("Helvetica", 12, "bold"), width=24, command=self.login)
        self.login_btn.pack(pady=4)

        self.goto_signup_link = tk.Label(self.signin_frame, font=("Helvetica", 10, "underline"),
                                          bg="white", fg=BTN_COLOR, cursor="hand2")
        self.goto_signup_link.pack(pady=(10, 0))
        self.goto_signup_link.bind("<Button-1>", lambda e: self.switch_mode("signup"))

        # --- Sign Up form ---
        self.signup_frame = tk.Frame(card, bg="white")

        self.signup_username_field_label = tk.Label(self.signup_frame, bg="white", font=("Helvetica", 11))
        self.signup_username_field_label.pack(anchor="w")
        self.signup_username_entry = tk.Entry(self.signup_frame, font=("Helvetica", 12), width=28)
        self.signup_username_entry.pack(pady=(0, 10))

        self.signup_email_field_label = tk.Label(self.signup_frame, bg="white", font=("Helvetica", 11))
        self.signup_email_field_label.pack(anchor="w")
        self.signup_email_entry = tk.Entry(self.signup_frame, font=("Helvetica", 12), width=28)
        self.signup_email_entry.pack(pady=(0, 10))

        self.signup_password_field_label = tk.Label(self.signup_frame, bg="white", font=("Helvetica", 11))
        self.signup_password_field_label.pack(anchor="w")
        self.signup_password_entry = tk.Entry(self.signup_frame, font=("Helvetica", 12), width=28, show="*")
        self.signup_password_entry.pack(pady=(0, 10))

        self.signup_confirm_field_label = tk.Label(self.signup_frame, bg="white", font=("Helvetica", 11))
        self.signup_confirm_field_label.pack(anchor="w")
        self.signup_confirm_entry = tk.Entry(self.signup_frame, font=("Helvetica", 12), width=28, show="*")
        self.signup_confirm_entry.pack(pady=(0, 10))

        self.signup_btn_widget = tk.Button(self.signup_frame, bg="#27ae60", fg="white",
                                            font=("Helvetica", 12, "bold"), width=24, command=self.signup)
        self.signup_btn_widget.pack(pady=4)

        self.goto_signin_link = tk.Label(self.signup_frame, font=("Helvetica", 10, "underline"),
                                          bg="white", fg=BTN_COLOR, cursor="hand2")
        self.goto_signin_link.pack(pady=(10, 0))
        self.goto_signin_link.bind("<Button-1>", lambda e: self.switch_mode("signin"))

        self.message_label = tk.Label(card, text="", bg="white", font=("Helvetica", 10), fg="#e74c3c",
                                       wraplength=320, justify="left")
        self.message_label.pack(pady=(10, 0))

        self.admin_link = tk.Button(self, font=("Helvetica", 9, "bold"), bg="#e8e8ec", fg="#666",
                                     bd=0, padx=14, pady=6, cursor="hand2",
                                     command=lambda: app.show_frame("AdminLoginScreen"))
        self.admin_link.place(relx=0.5, rely=1.0, anchor="s", y=-15)

        self.switch_mode("signin")
        self.apply_language()

    def switch_mode(self, mode):
        self.mode = mode
        self.message_label.config(text="")
        if mode == "signin":
            self.signup_frame.pack_forget()
            self.signin_frame.pack()
        else:
            self.signin_frame.pack_forget()
            self.signup_frame.pack()
        self._refresh_tab_styles()

    def _refresh_tab_styles(self):
        active_bg, active_fg = BTN_COLOR, "white"
        inactive_bg, inactive_fg = "#f0f0f0", "#555"
        if self.mode == "signin":
            self.signin_tab_btn.config(bg=active_bg, fg=active_fg)
            self.signup_tab_btn.config(bg=inactive_bg, fg=inactive_fg)
        else:
            self.signin_tab_btn.config(bg=inactive_bg, fg=inactive_fg)
            self.signup_tab_btn.config(bg=active_bg, fg=active_fg)

    def apply_language(self):
        app = self.app
        self.signin_tab_btn.config(text=tr(app, "signin_tab"))
        self.signup_tab_btn.config(text=tr(app, "signup_tab"))

        self.signin_username_field_label.config(text=tr(app, "signin_username_label"))
        self.signin_password_field_label.config(text=tr(app, "password_label"))
        self.remember_check.config(text=tr(app, "remember_me"))
        self.login_btn.config(text=tr(app, "login_btn"))
        self.goto_signup_link.config(text=tr(app, "no_account_prompt"))

        self.signup_username_field_label.config(text=tr(app, "signup_username_label"))
        self.signup_email_field_label.config(text=tr(app, "email_hint_label"))
        self.signup_password_field_label.config(text=tr(app, "password_label"))
        self.signup_confirm_field_label.config(text=tr(app, "confirm_password_label"))
        self.signup_btn_widget.config(text=tr(app, "signup_btn"))
        self.goto_signin_link.config(text=tr(app, "have_account_prompt"))
        self.admin_link.config(text=tr(app, "admin_login_link"))

    def on_show(self):
        self.signin_username_entry.delete(0, tk.END)
        self.signin_password_entry.delete(0, tk.END)
        self.signup_username_entry.delete(0, tk.END)
        self.signup_email_entry.delete(0, tk.END)
        self.signup_password_entry.delete(0, tk.END)
        self.signup_confirm_entry.delete(0, tk.END)
        self.message_label.config(text="")
        self.switch_mode("signin")

    def login(self):
        identifier = self.signin_username_entry.get().strip()
        password = self.signin_password_entry.get()
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
        username = self.signup_username_entry.get().strip()
        email = self.signup_email_entry.get().strip()
        password = self.signup_password_entry.get()
        confirm = self.signup_confirm_entry.get()

        if password != confirm:
            self.message_label.config(text=tr(self.app, "passwords_mismatch_msg"), fg="#e74c3c")
            return

        self.app.refresh_data()
        success, msg = auth.create_user(self.app.data, username, password, email=email)
        if success:
            dm.save_data(self.app.data)
            self.message_label.config(text=tr(self.app, "account_created_msg"), fg="#27ae60")
            self.signup_username_entry.delete(0, tk.END)
            self.signup_email_entry.delete(0, tk.END)
            self.signup_password_entry.delete(0, tk.END)
            self.signup_confirm_entry.delete(0, tk.END)
            self.after(1200, lambda: self.switch_mode("signin"))
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

        self.quiz_btn = tk.Button(top, bg="#ecdff5", fg="#7d3c9e",
                                   font=("Helvetica", 11, "bold"), command=self.start_quiz)
        self.quiz_btn.pack(side="right")
        self.contests_btn = tk.Button(top, bg="#fde3c7", fg="#c76b12",
                                       font=("Helvetica", 11, "bold"), command=self.open_contests)
        self.contests_btn.pack(side="right", padx=8)
        LanguageToggle(top, app, on_change=self.on_show).pack(side="right", padx=10)

        self.listbox = tk.Listbox(self, font=("Helvetica", 13), height=15)
        self.listbox.pack(fill="both", expand=True, padx=20, pady=10)
        self.listbox.bind("<<ListboxSelect>>", self.select_lesson)

        self.apply_language()

    def apply_language(self):
        app = self.app
        self.back_btn.config(text=tr(app, "back_btn"))
        self.quiz_btn.config(text=tr(app, "take_quiz_btn"))
        self.contests_btn.config(text=tr(app, "contests_btn"))

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

    def open_contests(self):
        contest_list_frame = self.app.frames["ContestListScreen"]
        self.app.show_frame("ContestListScreen")


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


class ContestListScreen(tk.Frame):
    """Shows all contests for the current module, with a lock/unlock state
    based on how many lessons of that module the user has completed
    (a new contest unlocks every 4 completed lessons)."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_COLOR)
        self.app = app

        top = tk.Frame(self, bg=BG_COLOR)
        top.pack(fill="x", pady=15, padx=20)
        self.back_btn = tk.Button(top, command=lambda: app.show_frame("LessonListScreen"))
        self.back_btn.pack(side="left")
        self.title_label = tk.Label(top, font=("Helvetica", 20, "bold"), bg=BG_COLOR, fg=ACCENT_COLOR)
        self.title_label.pack(side="left", padx=20)
        LanguageToggle(top, app, on_change=self.on_show).pack(side="right")

        self.list_container = tk.Frame(self, bg=BG_COLOR)
        self.list_container.pack(fill="both", expand=True, padx=20, pady=10)

        self.apply_language()

    def apply_language(self):
        app = self.app
        self.back_btn.config(text=tr(app, "back_btn"))
        self.title_label.config(text=tr(app, "contest_list_title"))

    def on_show(self):
        app = self.app
        app.refresh_data()
        self.apply_language()

        for widget in self.list_container.winfo_children():
            widget.destroy()

        contests = dm.get_contests_by_module(app.contests, app.current_module)
        for contest in contests:
            row = tk.Frame(self.list_container, bg="white", padx=15, pady=12,
                            highlightbackground="#ddd", highlightthickness=1)
            row.pack(fill="x", pady=6)

            unlocked = dm.is_contest_unlocked(app.data, app.current_user, contest)
            title = contest["title_bn"] if app.language == "bn" else contest["title_en"]

            tk.Label(row, text=title, font=("Helvetica", 14, "bold"),
                     bg="white", fg=ACCENT_COLOR).pack(side="left")

            if unlocked:
                solved = dm.get_solved_count_in_contest(app.data, app.current_user, contest)
                total = len(contest["problems"])
                status_text = tr(app, "unlocked_label") + "   |   " + \
                    tr(app, "problems_solved_label", solved=solved, total=total)
                status_color = "#27ae60"
                cmd = lambda c=contest: self.open_contest(c)
            else:
                done = dm.get_completed_lesson_count_in_module(app.data, app.current_user, contest["module"])
                remaining = max(0, contest["unlock_after_lessons"] - done)
                status_text = tr(app, "locked_label", n=remaining)
                status_color = "#999"
                cmd = None

            tk.Label(row, text=status_text, font=("Helvetica", 10), bg="white", fg=status_color).pack(side="left", padx=15)

            btn = tk.Button(row, text="→", font=("Helvetica", 12, "bold"), bg=BTN_COLOR, fg="white",
                             width=4, state="normal" if unlocked else "disabled",
                             command=cmd if cmd else (lambda: None))
            btn.pack(side="right")

    def open_contest(self, contest):
        self.app.current_contest = contest
        contest_frame = self.app.frames["ContestScreen"]
        contest_frame.on_show()
        self.app.show_frame("ContestScreen")


class ContestScreen(tk.Frame):
    """Lists the Easy / Medium / Hard problems inside one unlocked contest."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_COLOR)
        self.app = app

        top = tk.Frame(self, bg=BG_COLOR)
        top.pack(fill="x", pady=15, padx=20)
        self.back_btn = tk.Button(top, command=lambda: app.show_frame("ContestListScreen"))
        self.back_btn.pack(side="left")
        self.title_label = tk.Label(top, font=("Helvetica", 20, "bold"), bg=BG_COLOR, fg=ACCENT_COLOR)
        self.title_label.pack(side="left", padx=20)
        LanguageToggle(top, app, on_change=self.on_show).pack(side="right")
        self.leaderboard_btn = tk.Button(top, bg="#fdf3c7", fg="#a67c00",
                                          font=("Helvetica", 10, "bold"), command=self.open_leaderboard)
        self.leaderboard_btn.pack(side="right", padx=10)

        self.time_status_label = tk.Label(self, font=("Helvetica", 11, "bold"), bg=BG_COLOR)
        self.time_status_label.pack(padx=20, anchor="w")

        self.list_container = tk.Frame(self, bg=BG_COLOR)
        self.list_container.pack(fill="both", expand=True, padx=20, pady=10)

        self.apply_language()

    def apply_language(self):
        self.back_btn.config(text=tr(self.app, "back_btn"))
        self.leaderboard_btn.config(text=tr(self.app, "leaderboard_btn"))

    def open_leaderboard(self):
        contest = self.app.current_contest
        if not contest:
            return
        leaderboard_frame = self.app.frames["LeaderboardScreen"]
        leaderboard_frame.on_show()
        self.app.show_frame("LeaderboardScreen")

    DIFFICULTY_COLORS = {"easy": "#d4f4dd", "medium": "#fde3c7", "hard": "#fadbd8"}
    DIFFICULTY_TEXT_COLORS = {"easy": "#1e7a3d", "medium": "#b3620a", "hard": "#a3281f"}

    def on_show(self):
        app = self.app
        app.refresh_data()
        self.apply_language()
        contest = app.current_contest
        if not contest:
            return

        # Starts this user's 7-day submission timer the first time they open
        # this contest. Does nothing if it was already started earlier.
        dm.start_contest_if_needed(app.data, app.current_user, contest["id"])
        app.refresh_data()

        title = contest["title_bn"] if app.language == "bn" else contest["title_en"]
        self.title_label.config(text=title)

        time_status = dm.get_contest_time_status(app.data, app.current_user, contest["id"])
        if time_status["expired"]:
            self.time_status_label.config(text=tr(app, "contest_expired_msg"), fg="#c0392b")
        else:
            self.time_status_label.config(
                text=tr(app, "contest_days_remaining", days=time_status["days_remaining"]), fg="#e67e22")

        for widget in self.list_container.winfo_children():
            widget.destroy()

        for problem in contest["problems"]:
            row = tk.Frame(self.list_container, bg="white", padx=15, pady=12,
                            highlightbackground="#ddd", highlightthickness=1, cursor="hand2")
            row.pack(fill="x", pady=6)

            p_title = problem["title_bn"] if app.language == "bn" else problem["title_en"]
            diff_key = f"difficulty_{problem['difficulty']}"
            diff_text = tr(app, diff_key)
            diff_bg = self.DIFFICULTY_COLORS.get(problem["difficulty"], "#eeeeee")
            diff_fg = self.DIFFICULTY_TEXT_COLORS.get(problem["difficulty"], "#555")

            solved = dm.is_problem_solved(app.data, app.current_user, problem["id"])
            solved_text = tr(app, "solved_mark") if solved else tr(app, "not_solved_mark")

            left = tk.Frame(row, bg="white")
            left.pack(side="left", fill="x", expand=True)
            tk.Label(left, text=p_title, font=("Helvetica", 13, "bold"), bg="white", fg=ACCENT_COLOR).pack(anchor="w")
            tag_frame = tk.Frame(left, bg="white")
            tag_frame.pack(anchor="w", pady=(3, 0))
            tk.Label(tag_frame, text=diff_text, font=("Helvetica", 9, "bold"), bg=diff_bg, fg=diff_fg,
                     padx=8, pady=2).pack(side="left")
            tk.Label(tag_frame, text="   " + solved_text, font=("Helvetica", 9),
                     bg="white", fg="#27ae60" if solved else "#999").pack(side="left")

            for widget in (row, left):
                widget.bind("<Button-1>", lambda e, p=problem: self.open_problem(p))

            arrow = tk.Label(row, text="→", font=("Helvetica", 14, "bold"), bg="white", fg=BTN_COLOR)
            arrow.pack(side="right")
            arrow.bind("<Button-1>", lambda e, p=problem: self.open_problem(p))

    def open_problem(self, problem):
        self.app.current_problem = problem
        problem_frame = self.app.frames["ProblemScreen"]
        problem_frame.load_problem(problem)
        self.app.show_frame("ProblemScreen")


class ProblemScreen(tk.Frame):
    """Problem statement + a multi-language code editor. Submitting runs the
    code against ALL of the problem's test cases (via code_runner.run_test_cases)
    and marks the problem solved (awarding XP once) only if every case passes."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_COLOR)
        self.app = app
        self.current_problem = None
        self.contest_expired = False

        top = tk.Frame(self, bg=BG_COLOR)
        top.pack(fill="x", pady=10, padx=20)
        self.back_btn = tk.Button(top, command=lambda: app.show_frame("ContestScreen"))
        self.back_btn.pack(side="left")
        LanguageToggle(top, app, on_change=self.apply_language).pack(side="right")

        self.title_label = tk.Label(self, font=("Helvetica", 17, "bold"), bg=BG_COLOR, fg=ACCENT_COLOR)
        self.title_label.pack(pady=(5, 0), padx=20, anchor="w")

        self.time_status_label = tk.Label(self, font=("Helvetica", 10, "bold"), bg=BG_COLOR)
        self.time_status_label.pack(padx=20, pady=(2, 0), anchor="w")

        self.diff_label = tk.Label(self, font=("Helvetica", 10, "bold"), fg="white", padx=8, pady=2)
        self.diff_label.pack(padx=20, pady=(4, 8), anchor="w")

        self.description_label = tk.Label(self, font=("Helvetica", 12), bg=BG_COLOR, fg="#333",
                                           wraplength=930, justify="left")
        self.description_label.pack(pady=(0, 10), padx=20, anchor="w")

        lang_frame = tk.Frame(self, bg=BG_COLOR)
        lang_frame.pack(fill="x", padx=20, pady=(0, 5))
        self.language_field_label = tk.Label(lang_frame, font=("Helvetica", 11, "bold"),
                                              bg=BG_COLOR, fg=ACCENT_COLOR)
        self.language_field_label.pack(side="left")
        self.language_var = tk.StringVar(value="python")
        self.language_dropdown = ttk.Combobox(lang_frame, textvariable=self.language_var,
                                               values=LANGUAGES, state="readonly", width=12,
                                               font=("Helvetica", 11))
        self.language_dropdown.pack(side="left", padx=10)
        self.language_dropdown.bind("<<ComboboxSelected>>", self.on_language_change)

        self.code_box = tk.Text(self, height=10, font=("Consolas", 12), bg="#2d2d2d", fg="#f8f8f2",
                                 insertbackground="white")
        self.code_box.pack(fill="both", expand=True, padx=20, pady=(5, 10))

        self.submit_btn = tk.Button(self, bg="#27ae60", fg="white",
                                     font=("Helvetica", 12, "bold"), command=self.submit)
        self.submit_btn.pack(padx=20, anchor="w")

        self.results_box = tk.Text(self, height=8, font=("Consolas", 10), bg="#1e1e1e", fg="#00ff88")
        self.results_box.pack(fill="both", expand=True, padx=20, pady=(10, 15))
        self.results_box.config(state="disabled")

        self.apply_language()

    def apply_language(self):
        app = self.app
        self.back_btn.config(text=tr(app, "back_btn"))
        self.language_field_label.config(text=tr(app, "language_field_label"))
        self.submit_btn.config(text=tr(app, "submit_btn"))
        if self.current_problem:
            self._render_problem_text()
            self._render_time_status()

    DIFFICULTY_COLORS = {"easy": "#d4f4dd", "medium": "#fde3c7", "hard": "#fadbd8"}
    DIFFICULTY_TEXT_COLORS = {"easy": "#1e7a3d", "medium": "#b3620a", "hard": "#a3281f"}

    def _render_problem_text(self):
        app = self.app
        problem = self.current_problem
        title = problem["title_bn"] if app.language == "bn" else problem["title_en"]
        desc = problem["description_bn"] if app.language == "bn" else problem["description_en"]
        self.title_label.config(text=title)
        self.diff_label.config(text=tr(app, f"difficulty_{problem['difficulty']}"),
                                bg=self.DIFFICULTY_COLORS.get(problem["difficulty"], "#eeeeee"),
                                fg=self.DIFFICULTY_TEXT_COLORS.get(problem["difficulty"], "#555"))
        self.description_label.config(text=desc)

    def _render_time_status(self):
        """Shows days-remaining / expired text and enables or disables the
        Submit button based on this user's 7-day window for the CURRENT contest."""
        app = self.app
        contest = app.current_contest
        if not contest:
            return
        time_status = dm.get_contest_time_status(app.data, app.current_user, contest["id"])
        self.contest_expired = time_status["expired"]
        if time_status["expired"]:
            self.time_status_label.config(text=tr(app, "contest_deadline_expired_short"), fg="#c0392b")
            self.submit_btn.config(state="disabled")
        else:
            days = time_status["days_remaining"] if time_status["days_remaining"] is not None else "?"
            self.time_status_label.config(text=tr(app, "contest_days_remaining", days=days), fg="#e67e22")
            self.submit_btn.config(state="normal")

    def load_problem(self, problem):
        self.current_problem = problem
        self.language_var.set("python")
        self.code_box.delete("1.0", tk.END)
        self.code_box.insert(tk.END, DEFAULT_SNIPPETS["python"])
        self._set_results("")
        self._render_problem_text()
        self._render_time_status()

    def on_language_change(self, event=None):
        self.code_box.delete("1.0", tk.END)
        self.code_box.insert(tk.END, DEFAULT_SNIPPETS[self.language_var.get()])

    def submit(self):
        app = self.app
        contest = app.current_contest
        time_status = dm.get_contest_time_status(app.data, app.current_user, contest["id"])
        if time_status["expired"]:
            self._render_time_status()
            messagebox.showwarning(tr(app, "contest_deadline_expired_short"), tr(app, "contest_expired_msg"))
            return

        code = self.code_box.get("1.0", tk.END)
        language = self.language_var.get()
        self.submit_btn.config(state="disabled")
        self._set_results(tr(self.app, "running_code_msg", language=language))
        threading.Thread(target=self._submit_thread, args=(language, code), daemon=True).start()

    def _submit_thread(self, language, code):
        problem = self.current_problem
        results = code_runner.run_test_cases(language, code, problem["test_cases"])
        self.after(0, self._show_submit_results, results)

    def _show_submit_results(self, results):
        app = self.app
        contest = app.current_contest
        lines = []
        all_passed = all(r["passed"] for r in results)

        # Log this attempt (pass or fail) for the leaderboard's penalty/attempt tracking.
        dm.record_submission(app.data, app.current_user, contest["id"],
                              self.current_problem["id"], all_passed)
        app.refresh_data()

        for i, r in enumerate(results, start=1):
            status = tr(app, "passed_label") if r["passed"] else tr(app, "failed_label")
            lines.append(f"{tr(app, 'test_case_label', n=i)}: {status}")
            if not r["passed"]:
                lines.append(f"  {tr(app, 'input_label')}: {r['input']}")
                lines.append(f"  {tr(app, 'expected_label')}: {r['expected']}")
                lines.append(f"  {tr(app, 'your_output_label')}: {r['actual']}")
                if r["error"]:
                    lines.append(f"  {tr(app, 'error_prefix')}{r['error']}")

        if all_passed:
            already_solved = dm.is_problem_solved(app.data, app.current_user, self.current_problem["id"])
            dm.mark_problem_solved(app.data, app.current_user, self.current_problem["id"],
                                    self.current_problem["xp_reward"])
            app.refresh_data()
            lines.append("")
            lines.append(tr(app, "all_tests_passed_msg"))
            self._set_results("\n".join(lines))
            if already_solved:
                messagebox.showinfo(tr(app, "problem_solved_title"), tr(app, "already_solved_msg"))
            else:
                messagebox.showinfo(tr(app, "problem_solved_title"),
                                     tr(app, "problem_solved_msg", xp=self.current_problem["xp_reward"]))
        else:
            lines.append("")
            lines.append(tr(app, "some_tests_failed_msg"))
            self._set_results("\n".join(lines))

        self._render_time_status()  # re-enables submit_btn only if still within the 7-day window

    def _set_results(self, text):
        self.results_box.config(state="normal")
        self.results_box.delete("1.0", tk.END)
        self.results_box.insert(tk.END, text)
        self.results_box.config(state="disabled")


class LeaderboardScreen(tk.Frame):
    """ICPC-style ranking table for one contest: Rank, Username, Score,
    Penalty, then one color-coded column per problem showing solve time
    (green) or wrong-attempt count (red) — like a Codeforces/vjudge standings
    page. Scrollable vertically since the student list can grow."""

    DIFFICULTY_COLORS = {"easy": "#d4f4dd", "medium": "#fde3c7", "hard": "#fadbd8"}
    DIFFICULTY_TEXT_COLORS = {"easy": "#1e7a3d", "medium": "#b3620a", "hard": "#a3281f"}
    SOLVED_BG = "#e5f8ec"
    SOLVED_FG = "#1e7a3d"
    ATTEMPTED_BG = "#fdecea"
    ATTEMPTED_FG = "#c0392b"
    UNTOUCHED_BG = "#f0f1f4"
    UNTOUCHED_FG = "#aaaaaa"
    ROW_BG = "white"
    ME_ROW_BG = "#eaf3fb"

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_COLOR)
        self.app = app

        top = tk.Frame(self, bg=BG_COLOR)
        top.pack(fill="x", pady=15, padx=20)
        self.back_btn = tk.Button(top, command=lambda: app.show_frame("ContestScreen"))
        self.back_btn.pack(side="left")
        self.title_label = tk.Label(top, font=("Helvetica", 18, "bold"), bg=BG_COLOR, fg=ACCENT_COLOR)
        self.title_label.pack(side="left", padx=20)
        LanguageToggle(top, app, on_change=self.on_show).pack(side="right")

        # Scrollable table area
        table_outer = tk.Frame(self, bg=BG_COLOR)
        table_outer.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        self.canvas = tk.Canvas(table_outer, bg=BG_COLOR, highlightthickness=0)
        scrollbar = tk.Scrollbar(table_outer, orient="vertical", command=self.canvas.yview)
        self.table_frame = tk.Frame(self.canvas, bg=BG_COLOR)
        self.table_frame.bind("<Configure>",
                               lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.table_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.empty_label = tk.Label(self, font=("Helvetica", 12), bg=BG_COLOR, fg="#999")

        self.apply_language()

    def apply_language(self):
        self.back_btn.config(text=tr(self.app, "back_btn"))

    def _fmt_time(self, minutes):
        h, m = divmod(minutes, 60)
        return f"{h}:{m:02d}"

    def on_show(self):
        app = self.app
        app.refresh_data()
        self.apply_language()
        contest = app.current_contest
        if not contest:
            return

        title = contest["title_bn"] if app.language == "bn" else contest["title_en"]
        self.title_label.config(text=f"{tr(app, 'leaderboard_title')}: {title}")

        for widget in self.table_frame.winfo_children():
            widget.destroy()
        self.empty_label.pack_forget()

        rows = dm.get_contest_leaderboard(app.data, contest)
        if not rows:
            self.empty_label.config(text=tr(app, "no_submissions_msg"))
            self.empty_label.pack(pady=30)
            return

        problems = contest["problems"]

        # --- Header row ---
        header_style = {"font": ("Helvetica", 10, "bold"), "bg": BTN_COLOR, "fg": "white",
                         "padx": 8, "pady": 8}
        tk.Label(self.table_frame, text=tr(app, "rank_col"), width=5, **header_style).grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        tk.Label(self.table_frame, text=tr(app, "team_col"), width=16, **header_style).grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
        tk.Label(self.table_frame, text=tr(app, "score_col"), width=6, **header_style).grid(row=0, column=2, sticky="nsew", padx=1, pady=1)
        tk.Label(self.table_frame, text=tr(app, "penalty_col"), width=8, **header_style).grid(row=0, column=3, sticky="nsew", padx=1, pady=1)
        for j, problem in enumerate(problems):
            label_letter = chr(ord('A') + j)
            diff_bg = self.DIFFICULTY_COLORS.get(problem["difficulty"], "#eeeeee")
            diff_fg = self.DIFFICULTY_TEXT_COLORS.get(problem["difficulty"], "#555")
            tk.Label(self.table_frame, text=label_letter, width=10, font=("Helvetica", 10, "bold"),
                     bg=diff_bg, fg=diff_fg, padx=8, pady=8).grid(row=0, column=4 + j, sticky="nsew", padx=1, pady=1)

        # --- Data rows ---
        for i, row in enumerate(rows, start=1):
            is_me = row["username"] == app.current_user
            name_bg = self.ME_ROW_BG if is_me else self.ROW_BG
            base_style = {"font": ("Helvetica", 10, "bold" if is_me else "normal"), "fg": ACCENT_COLOR, "padx": 8, "pady": 6}

            tk.Label(self.table_frame, text=str(i), bg=name_bg, **base_style).grid(row=i, column=0, sticky="nsew", padx=1, pady=1)
            tk.Label(self.table_frame, text=row["username"], bg=name_bg, anchor="w", **base_style).grid(row=i, column=1, sticky="nsew", padx=1, pady=1)
            tk.Label(self.table_frame, text=str(row["score"]), bg=name_bg, **base_style).grid(row=i, column=2, sticky="nsew", padx=1, pady=1)
            tk.Label(self.table_frame, text=str(row["penalty"]), bg=name_bg, **base_style).grid(row=i, column=3, sticky="nsew", padx=1, pady=1)

            for j, problem in enumerate(problems):
                stats = row["problems"][problem["id"]]
                if stats["solved"]:
                    text = self._fmt_time(stats["solve_time_minutes"] or 0)
                    if stats["wrong_attempts"] > 0:
                        text += f"\n(-{stats['wrong_attempts']})"
                    cell_bg, cell_fg = self.SOLVED_BG, self.SOLVED_FG
                elif stats["attempted"]:
                    text = f"(-{stats['total_attempts']})"
                    cell_bg, cell_fg = self.ATTEMPTED_BG, self.ATTEMPTED_FG
                else:
                    text = ""
                    cell_bg, cell_fg = self.UNTOUCHED_BG, self.UNTOUCHED_FG

                tk.Label(self.table_frame, text=text, bg=cell_bg, fg=cell_fg,
                         font=("Helvetica", 9, "bold"), padx=8, pady=6,
                         justify="center").grid(row=i, column=4 + j, sticky="nsew", padx=1, pady=1)


class AdminLoginScreen(tk.Frame):
    """A separate password gate (not tied to any student account) that
    unlocks the Student Management panel. Default password is 'admin123'
    (see auth.py DEFAULT_ADMIN_PASSWORD) — change it via auth.set_admin_password()."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_COLOR)
        self.app = app

        LanguageToggle(self, app, on_change=self.apply_language).place(relx=1.0, y=15, anchor="ne", x=-20)

        card = tk.Frame(self, bg="white", padx=40, pady=30)
        card.place(relx=0.5, rely=0.5, anchor="center")

        self.title_label = tk.Label(card, font=("Helvetica", 20, "bold"), bg="white", fg=ACCENT_COLOR)
        self.title_label.pack(pady=(0, 20))

        self.password_field_label = tk.Label(card, bg="white", font=("Helvetica", 11))
        self.password_field_label.pack(anchor="w")
        self.password_entry = tk.Entry(card, font=("Helvetica", 12), width=28, show="*")
        self.password_entry.pack(pady=(0, 12))
        self.password_entry.bind("<Return>", lambda e: self.try_login())

        self.enter_btn = tk.Button(card, bg=BTN_COLOR, fg="white", font=("Helvetica", 12, "bold"),
                                    width=24, command=self.try_login)
        self.enter_btn.pack(pady=4)

        self.back_link = tk.Label(card, font=("Helvetica", 9, "underline"), bg="white",
                                   fg="#999", cursor="hand2")
        self.back_link.pack(pady=(12, 0))
        self.back_link.bind("<Button-1>", lambda e: app.show_frame("LoginScreen"))

        self.message_label = tk.Label(card, text="", bg="white", font=("Helvetica", 10), fg="#e74c3c")
        self.message_label.pack(pady=(10, 0))

        self.apply_language()

    def apply_language(self):
        app = self.app
        self.title_label.config(text=tr(app, "admin_login_title"))
        self.password_field_label.config(text=tr(app, "admin_password_label"))
        self.enter_btn.config(text=tr(app, "admin_login_btn"))
        self.back_link.config(text=tr(app, "back_btn"))

    def on_show(self):
        self.password_entry.delete(0, tk.END)
        self.message_label.config(text="")

    def try_login(self):
        password = self.password_entry.get()
        if auth.verify_admin_password(password):
            self.app.show_frame("StudentManagementScreen")
        else:
            self.message_label.config(text=tr(self.app, "admin_wrong_password_msg"))


class StudentManagementScreen(tk.Frame):
    """Admin-only panel: a scrollable table of every registered student's
    progress (lessons, quizzes, contests, XP, certificate eligibility) with
    per-row Edit (change XP / reset progress) and Delete actions."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_COLOR)
        self.app = app

        top = tk.Frame(self, bg=BG_COLOR)
        top.pack(fill="x", pady=15, padx=20)
        self.back_btn = tk.Button(top, command=lambda: app.show_frame("LoginScreen"))
        self.back_btn.pack(side="left")
        self.title_label = tk.Label(top, font=("Helvetica", 20, "bold"), bg=BG_COLOR, fg=ACCENT_COLOR)
        self.title_label.pack(side="left", padx=20)
        LanguageToggle(top, app, on_change=self.on_show).pack(side="right")

        table_outer = tk.Frame(self, bg=BG_COLOR)
        table_outer.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        self.canvas = tk.Canvas(table_outer, bg=BG_COLOR, highlightthickness=0)
        scrollbar = tk.Scrollbar(table_outer, orient="vertical", command=self.canvas.yview)
        self.table_frame = tk.Frame(self.canvas, bg=BG_COLOR)
        self.table_frame.bind("<Configure>",
                               lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.table_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.empty_label = tk.Label(self, font=("Helvetica", 12), bg=BG_COLOR, fg="#999")

        self.apply_language()

    def apply_language(self):
        self.back_btn.config(text=tr(self.app, "admin_logout_btn"))
        self.title_label.config(text=tr(self.app, "student_mgmt_title"))

    def on_show(self):
        app = self.app
        app.refresh_data()
        self.apply_language()

        for widget in self.table_frame.winfo_children():
            widget.destroy()
        self.empty_label.pack_forget()

        students = dm.get_all_students_summary(app.data, app.contests)
        if not students:
            self.empty_label.config(text=tr(app, "no_students_msg"))
            self.empty_label.pack(pady=30)
            return

        headers = ["col_username", "col_email", "col_xp", "col_level", "col_streak",
                   "col_lessons", "col_quizzes", "col_contests", "col_certificate", "col_actions"]
        header_style = {"font": ("Helvetica", 10, "bold"), "bg": BTN_COLOR, "fg": "white", "padx": 8, "pady": 8}
        for c, key in enumerate(headers):
            tk.Label(self.table_frame, text=tr(app, key), **header_style).grid(
                row=0, column=c, sticky="nsew", padx=1, pady=1)

        for i, s in enumerate(students, start=1):
            row_bg = "white" if i % 2 else "#f7f8fa"
            cell_style = {"font": ("Helvetica", 10), "bg": row_bg, "fg": ACCENT_COLOR, "padx": 8, "pady": 6}

            tk.Label(self.table_frame, text=s["username"], anchor="w", **cell_style).grid(row=i, column=0, sticky="nsew", padx=1, pady=1)
            tk.Label(self.table_frame, text=s["email"] or "—", anchor="w", **cell_style).grid(row=i, column=1, sticky="nsew", padx=1, pady=1)
            tk.Label(self.table_frame, text=str(s["xp"]), **cell_style).grid(row=i, column=2, sticky="nsew", padx=1, pady=1)
            tk.Label(self.table_frame, text=str(s["level"]), **cell_style).grid(row=i, column=3, sticky="nsew", padx=1, pady=1)
            tk.Label(self.table_frame, text=str(s["streak"]), **cell_style).grid(row=i, column=4, sticky="nsew", padx=1, pady=1)
            tk.Label(self.table_frame, text=f"{s['lessons_done']}/{s['lessons_total']}", **cell_style).grid(row=i, column=5, sticky="nsew", padx=1, pady=1)
            tk.Label(self.table_frame, text=f"{s['quizzes_correct']}/{s['quizzes_total']}", **cell_style).grid(row=i, column=6, sticky="nsew", padx=1, pady=1)
            tk.Label(self.table_frame, text=f"{s['contests_solved']}/{s['contests_total']}", **cell_style).grid(row=i, column=7, sticky="nsew", padx=1, pady=1)

            cert_text = tr(app, "cert_yes") if s["certificate_eligible"] else tr(app, "cert_no")
            cert_fg = "#1e7a3d" if s["certificate_eligible"] else "#999"
            tk.Label(self.table_frame, text=cert_text, bg=row_bg, fg=cert_fg,
                     font=("Helvetica", 10, "bold"), padx=8, pady=6).grid(row=i, column=8, sticky="nsew", padx=1, pady=1)

            action_cell = tk.Frame(self.table_frame, bg=row_bg)
            action_cell.grid(row=i, column=9, sticky="nsew", padx=1, pady=1)
            tk.Button(action_cell, text=tr(app, "edit_btn"), font=("Helvetica", 9), bg="#eaf3fb",
                      fg=BTN_COLOR, command=lambda u=s["username"]: self.open_edit_dialog(u)).pack(side="left", padx=2, pady=4)
            tk.Button(action_cell, text=tr(app, "delete_btn"), font=("Helvetica", 9), bg="#fdecea",
                      fg="#c0392b", command=lambda u=s["username"]: self.delete_student(u)).pack(side="left", padx=2, pady=4)

    def delete_student(self, username):
        app = self.app
        if messagebox.askyesno(tr(app, "confirm_delete_title"), tr(app, "confirm_delete_msg", username=username)):
            dm.delete_student(app.data, username)
            self.on_show()

    def open_edit_dialog(self, username):
        app = self.app
        user = app.data["users"][username]

        dialog = tk.Toplevel(self)
        dialog.title(tr(app, "edit_student_title", username=username))
        dialog.configure(bg="white")
        dialog.geometry("360x260")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        tk.Label(dialog, text=tr(app, "edit_student_title", username=username), font=("Helvetica", 13, "bold"),
                 bg="white", fg=ACCENT_COLOR, wraplength=320, justify="left").pack(pady=(15, 10), padx=15)

        xp_frame = tk.Frame(dialog, bg="white")
        xp_frame.pack(pady=5, padx=15, anchor="w")
        tk.Label(xp_frame, text=tr(app, "xp_field_label"), bg="white", font=("Helvetica", 11)).pack(side="left")
        xp_entry = tk.Entry(xp_frame, font=("Helvetica", 11), width=10)
        xp_entry.insert(0, str(user.get("xp", 0)))
        xp_entry.pack(side="left", padx=8)

        def save_xp():
            try:
                new_xp = int(xp_entry.get())
                if new_xp < 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning(tr(app, "edit_btn"), tr(app, "invalid_xp_msg"))
                return
            dm.set_student_xp(app.data, username, new_xp)
            dialog.destroy()
            self.on_show()

        btn_frame = tk.Frame(dialog, bg="white")
        btn_frame.pack(pady=10, padx=15, anchor="w")
        tk.Button(btn_frame, text=tr(app, "save_btn"), bg=BTN_COLOR, fg="white",
                  font=("Helvetica", 10, "bold"), command=save_xp).pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text=tr(app, "cancel_btn"), font=("Helvetica", 10),
                  command=dialog.destroy).pack(side="left")

        def reset_progress():
            if messagebox.askyesno(tr(app, "confirm_reset_title"), tr(app, "confirm_reset_msg", username=username)):
                dm.reset_student_progress(app.data, username)
                dialog.destroy()
                self.on_show()

        tk.Button(dialog, text=tr(app, "reset_progress_btn"), bg="#fdecea", fg="#c0392b",
                  font=("Helvetica", 10, "bold"), command=reset_progress).pack(pady=(15, 10), padx=15, anchor="w")


if __name__ == "__main__":
    app = CodeLearnApp()
    app.mainloop()