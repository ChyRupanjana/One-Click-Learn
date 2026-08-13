"""
main.py
Entry point for One Click Learn — a bilingual (Bangla/English) coding
learning app.

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
    "app_name":            {"en": "One Click Learn", "bn": "One Click Learn"},
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
    "search_placeholder": {"en": "🔍 Search lessons...", "bn": "🔍 পাঠ খুঁজুন..."},
    "no_results_msg": {"en": "No lessons match your search.", "bn": "কোনো পাঠ পাওয়া যায়নি।"},
    "search_contests_placeholder": {"en": "🔍 Search contests by name or topic...", "bn": "🔍 নাম বা টপিক দিয়ে কনটেস্ট খুঁজুন..."},

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

    # Content Management (Admin: Add Lesson / Add Contest)
    "content_mgmt_btn": {"en": "📤 Upload Content", "bn": "📤 কনটেন্ট আপলোড"},
    "content_mgmt_title": {"en": "Upload Content", "bn": "কনটেন্ট আপলোড"},
    "content_mgmt_subtitle": {"en": "Add a brand-new lesson or a brand-new contest to the app.",
                               "bn": "অ্যাপে একদম নতুন একটা লেসন বা নতুন একটা কনটেস্ট যোগ করো।"},
    "add_lesson_card_title": {"en": "📘 Add New Lesson", "bn": "📘 নতুন লেসন যোগ করো"},
    "add_lesson_card_desc": {"en": "Create a lesson with a title, content, and a code example.",
                              "bn": "টাইটেল, কনটেন্ট আর একটা কোড উদাহরণ দিয়ে নতুন লেসন তৈরি করো।"},
    "add_contest_card_title": {"en": "🏆 Add New Contest", "bn": "🏆 নতুন কনটেস্ট যোগ করো"},
    "add_contest_card_desc": {"en": "Create a contest with one or more problems and test cases.",
                               "bn": "এক বা একাধিক প্রবলেম আর টেস্ট কেস দিয়ে নতুন কনটেস্ট তৈরি করো।"},
    "open_btn": {"en": "Open →", "bn": "ওপেন করো →"},

    # Add Lesson dialog
    "add_lesson_title": {"en": "Add New Lesson", "bn": "নতুন লেসন যোগ করো"},
    "module_field_label": {"en": "Module:", "bn": "মডিউল:"},
    "lesson_title_en_label": {"en": "Title (English):", "bn": "টাইটেল (ইংরেজি):"},
    "lesson_title_bn_label": {"en": "Title (Bangla):", "bn": "টাইটেল (বাংলা):"},
    "lesson_content_en_label": {"en": "Content (English):", "bn": "কনটেন্ট (ইংরেজি):"},
    "lesson_content_bn_label": {"en": "Content (Bangla):", "bn": "কনটেন্ট (বাংলা):"},
    "code_example_label": {"en": "Code Example:", "bn": "কোড উদাহরণ:"},
    "save_lesson_btn": {"en": "Save Lesson", "bn": "লেসন সেভ করো"},
    "lesson_saved_title": {"en": "Lesson Added", "bn": "লেসন যোগ হয়েছে"},
    "lesson_saved_msg": {"en": "'{title}' has been added to the {module} module.",
                          "bn": "'{title}' {module} মডিউলে যোগ হয়ে গেছে।"},
    "lesson_missing_fields_msg": {"en": "Please fill in the module, both titles, and both content fields.",
                                   "bn": "মডিউল, দুইটা টাইটেল, আর দুইটা কনটেন্ট ফিল্ড পূরণ করো।"},

    # Add Contest dialog
    "add_contest_title": {"en": "Add New Contest", "bn": "নতুন কনটেস্ট যোগ করো"},
    "contest_id_label": {"en": "Contest ID:", "bn": "কনটেস্ট আইডি:"},
    "unlock_after_label": {"en": "Unlock after N lessons:", "bn": "কয়টা লেসনের পর আনলক হবে:"},
    "contest_title_en_label": {"en": "Contest Title (English):", "bn": "কনটেস্ট টাইটেল (ইংরেজি):"},
    "contest_title_bn_label": {"en": "Contest Title (Bangla):", "bn": "কনটেস্ট টাইটেল (বাংলা):"},
    "problems_label": {"en": "Problems", "bn": "প্রবলেম সমূহ"},
    "add_problem_btn": {"en": "+ Add Problem", "bn": "+ প্রবলেম যোগ করো"},
    "remove_btn": {"en": "Remove", "bn": "সরাও"},
    "save_contest_btn": {"en": "Save Contest", "bn": "কনটেস্ট সেভ করো"},
    "no_problems_msg": {"en": "No problems added yet. Add at least one problem below.",
                         "bn": "এখনো কোনো প্রবলেম যোগ হয়নি। নিচ থেকে অন্তত একটা প্রবলেম যোগ করো।"},
    "contest_missing_fields_msg": {"en": "Please fill in the contest ID and both titles.",
                                    "bn": "কনটেস্ট আইডি আর দুইটা টাইটেল পূরণ করো।"},
    "contest_duplicate_id_msg": {"en": "A contest with this ID already exists. Choose a different ID.",
                                  "bn": "এই আইডি দিয়ে আগে থেকেই একটা কনটেস্ট আছে। অন্য আইডি দাও।"},
    "contest_no_problems_msg": {"en": "Add at least one problem before saving the contest.",
                                 "bn": "কনটেস্ট সেভ করার আগে অন্তত একটা প্রবলেম যোগ করো।"},
    "contest_saved_title": {"en": "Contest Added", "bn": "কনটেস্ট যোগ হয়েছে"},
    "contest_saved_msg": {"en": "'{title}' has been added with {n} problem(s).",
                           "bn": "'{title}' {n}টা প্রবলেম সহ যোগ হয়ে গেছে।"},

    # Add Problem dialog (nested inside Add Contest)
    "add_problem_title": {"en": "Add Problem", "bn": "প্রবলেম যোগ করো"},
    "problem_id_label": {"en": "Problem ID:", "bn": "প্রবলেম আইডি:"},
    "difficulty_label": {"en": "Difficulty:", "bn": "কঠিনতা:"},
    "problem_title_en_label": {"en": "Problem Title (English):", "bn": "প্রবলেম টাইটেল (ইংরেজি):"},
    "problem_title_bn_label": {"en": "Problem Title (Bangla):", "bn": "প্রবলেম টাইটেল (বাংলা):"},
    "problem_desc_en_label": {"en": "Description (English):", "bn": "বর্ণনা (ইংরেজি):"},
    "problem_desc_bn_label": {"en": "Description (Bangla):", "bn": "বর্ণনা (বাংলা):"},
    "xp_reward_label": {"en": "XP Reward:", "bn": "এক্সপি পুরস্কার:"},
    "test_cases_label": {"en": "Test Cases", "bn": "টেস্ট কেস"},
    "add_test_case_btn": {"en": "+ Add Test Case", "bn": "+ টেস্ট কেস যোগ করো"},
    "test_input_label": {"en": "Input:", "bn": "ইনপুট:"},
    "test_expected_label": {"en": "Expected Output:", "bn": "প্রত্যাশিত আউটপুট:"},
    "save_problem_btn": {"en": "Save Problem", "bn": "প্রবলেম সেভ করো"},
    "problem_missing_fields_msg": {"en": "Please fill in the problem ID, both titles, both descriptions, and XP reward.",
                                    "bn": "প্রবলেম আইডি, দুইটা টাইটেল, দুইটা বর্ণনা, আর এক্সপি রিওয়ার্ড পূরণ করো।"},
    "problem_no_testcases_msg": {"en": "Add at least one test case.", "bn": "অন্তত একটা টেস্ট কেস যোগ করো।"},
    "problem_duplicate_id_msg": {"en": "A problem with this ID already exists in this contest.",
                                  "bn": "এই আইডি দিয়ে এই কনটেস্টে আগে থেকেই একটা প্রবলেম আছে।"},
    "invalid_xp_reward_msg": {"en": "Please enter a valid positive number for XP reward.",
                               "bn": "এক্সপি রিওয়ার্ডের জন্য একটা সঠিক পজিটিভ সংখ্যা দাও।"},

    # PlagiarismCheckScreen
    "plagiarism_check_btn": {"en": "🕵 Plagiarism Checker", "bn": "🕵 প্লেজিয়ারিজম চেকার"},
    "plagiarism_title": {"en": "Code Similarity Checker", "bn": "কোড সিমিলারিটি চেকার"},
    "plagiarism_disclaimer": {
        "en": "These are short beginner problems, so similar code can happen by "
              "chance. Treat matches below as a signal to review manually — "
              "not proof of copying.",
        "bn": "এগুলো ছোট বিগিনার প্রবলেম, তাই কাকতালীয়ভাবেও কোড মিলে যেতে পারে। "
              "নিচের মিলগুলোকে নিজে চেক করার ইঙ্গিত হিসেবে নাও — কপি করার প্রমাণ হিসেবে না।"},
    "threshold_label": {"en": "Minimum similarity:", "bn": "সর্বনিম্ন সিমিলারিটি:"},
    "scan_btn": {"en": "🔍 Scan All Contests", "bn": "🔍 সব কনটেস্ট স্ক্যান করো"},
    "scanning_msg": {"en": "Scanning submissions...", "bn": "সাবমিশন স্ক্যান করা হচ্ছে..."},
    "no_matches_msg": {"en": "No matches found at or above this threshold.",
                        "bn": "এই থ্রেশহোল্ডে বা তার উপরে কোনো মিল পাওয়া যায়নি।"},
    "col_problem": {"en": "Problem", "bn": "প্রবলেম"},
    "col_student_a": {"en": "Student A", "bn": "স্টুডেন্ট A"},
    "col_student_b": {"en": "Student B", "bn": "স্টুডেন্ট B"},
    "col_similarity": {"en": "Similarity", "bn": "সিমিলারিটি"},
    "view_code_btn": {"en": "View Code", "bn": "কোড দেখো"},
    "code_compare_title": {"en": "Compare: {a} vs {b}", "bn": "তুলনা: {a} বনাম {b}"},
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
        self.title("One Click Learn — Bilingual Coding Learning App")
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
                  AdminLoginScreen, StudentManagementScreen, ContentManagementScreen, PlagiarismCheckScreen):
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

        search_frame = tk.Frame(self, bg=BG_COLOR)
        search_frame.pack(fill="x", padx=20, pady=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filter_lessons())
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                      font=("Helvetica", 12), relief="solid", bd=1)
        self.search_entry.pack(fill="x", ipady=6)
        self.clear_search_btn = tk.Button(search_frame, text="✕", font=("Helvetica", 10),
                                           bg=BG_COLOR, bd=0, cursor="hand2",
                                           command=lambda: self.search_var.set(""))
        self.clear_search_btn.place(in_=self.search_entry, relx=1.0, rely=0.5,
                                     anchor="e", x=-6)

        self.listbox = tk.Listbox(self, font=("Helvetica", 13), height=15)
        self.listbox.pack(fill="both", expand=True, padx=20, pady=10)
        self.listbox.bind("<<ListboxSelect>>", self.select_lesson)

        self.apply_language()

    def apply_language(self):
        app = self.app
        self.back_btn.config(text=tr(app, "back_btn"))
        self.quiz_btn.config(text=tr(app, "take_quiz_btn"))
        self.contests_btn.config(text=tr(app, "contests_btn"))
        self._set_placeholder()

    def _set_placeholder(self):
        placeholder = tr(self.app, "search_placeholder")
        current = self.search_var.get()
        # Only overwrite if the box is empty or still showing the old placeholder
        if not current or current == getattr(self, "_placeholder_text", None):
            self._suppress_filter = True
            self.search_var.set(placeholder)
            self._suppress_filter = False
        self._placeholder_text = placeholder
        self.search_entry.config(fg="#999999")
        self.search_entry.bind("<FocusIn>", self._clear_placeholder)
        self.search_entry.bind("<FocusOut>", self._restore_placeholder)

    def _clear_placeholder(self, event=None):
        if self.search_var.get() == self._placeholder_text:
            self.search_var.set("")
            self.search_entry.config(fg="black")

    def _restore_placeholder(self, event=None):
        if not self.search_var.get():
            self._set_placeholder()

    def on_show(self):
        self.app.refresh_data()
        self.apply_language()
        module = self.app.current_module
        module_name = self.MODULE_DISPLAY_NAMES.get(module, "")
        self.title_label.config(text=f"{module_name} {tr(self.app, 'lessons_title_suffix')}")

        completed = self.app.get_current_user_data()["completed_lessons"]
        self.all_lessons = []
        for lesson in dm.get_lessons_by_module(self.app.data, module):
            self.all_lessons.append({
                "id": lesson["id"],
                "title_en": lesson["title_en"],
                "title_bn": lesson["title_bn"],
                "completed": lesson["id"] in completed,
            })
        self.filter_lessons()

    def filter_lessons(self):
        if getattr(self, "_suppress_filter", False):
            return
        query = self.search_var.get().strip().lower()
        if query == getattr(self, "_placeholder_text", None):
            query = ""

        self.listbox.delete(0, tk.END)
        self.lesson_ids = []
        for lesson in getattr(self, "all_lessons", []):
            title = lesson["title_bn"] if self.app.language == "bn" else lesson["title_en"]
            if query and query not in title.lower() \
                    and query not in lesson["title_en"].lower() \
                    and query not in lesson["title_bn"].lower():
                continue
            mark = "✅ " if lesson["completed"] else "⬜ "
            self.listbox.insert(tk.END, f"{mark}{title}")
            self.lesson_ids.append(lesson["id"])

        if query and not self.lesson_ids:
            self.listbox.insert(tk.END, tr(self.app, "no_results_msg"))

    def select_lesson(self, event):
        selection = self.listbox.curselection()
        if not selection or selection[0] >= len(self.lesson_ids):
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

        # Re-enable the submit button in case a previous module had no quiz
        # and left it disabled (bug fix: it was never turned back on).
        self.submit_btn.config(state="normal")

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
            try:
                dm.record_quiz_score(self.app.data, self.app.current_user, quiz["id"], correct)
                self.app.refresh_data()
            except Exception as e:
                # Surface any backend error instead of failing silently,
                # so a broken save never looks like "nothing happened".
                import traceback
                traceback.print_exc()
                messagebox.showerror("Error", f"Could not save your answer:\n{e}")
                return

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
        path = generate_certificate(username, course_title="One Click Learn Fundamentals")
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

        search_frame = tk.Frame(self, bg=BG_COLOR)
        search_frame.pack(fill="x", padx=20, pady=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.render_contests())
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                      font=("Helvetica", 12), relief="solid", bd=1)
        self.search_entry.pack(fill="x", ipady=6)
        self.clear_search_btn = tk.Button(search_frame, text="✕", font=("Helvetica", 10),
                                           bg=BG_COLOR, bd=0, cursor="hand2",
                                           command=lambda: self.search_var.set(""))
        self.clear_search_btn.place(in_=self.search_entry, relx=1.0, rely=0.5,
                                     anchor="e", x=-6)

        self.list_container = tk.Frame(self, bg=BG_COLOR)
        self.list_container.pack(fill="both", expand=True, padx=20, pady=10)

        self.apply_language()

    def apply_language(self):
        app = self.app
        self.back_btn.config(text=tr(app, "back_btn"))
        self.title_label.config(text=tr(app, "contest_list_title"))
        self._set_placeholder()

    def _set_placeholder(self):
        placeholder = tr(self.app, "search_contests_placeholder")
        current = self.search_var.get()
        if not current or current == getattr(self, "_placeholder_text", None):
            self._suppress_filter = True
            self.search_var.set(placeholder)
            self._suppress_filter = False
        self._placeholder_text = placeholder
        self.search_entry.config(fg="#999999")
        self.search_entry.bind("<FocusIn>", self._clear_placeholder)
        self.search_entry.bind("<FocusOut>", self._restore_placeholder)

    def _clear_placeholder(self, event=None):
        if self.search_var.get() == self._placeholder_text:
            self.search_var.set("")
            self.search_entry.config(fg="black")

    def _restore_placeholder(self, event=None):
        if not self.search_var.get():
            self._set_placeholder()

    def on_show(self):
        app = self.app
        app.refresh_data()
        self.apply_language()
        self.all_contests = dm.get_contests_by_module(app.contests, app.current_module)
        self.render_contests()

    def render_contests(self):
        if getattr(self, "_suppress_filter", False):
            return
        app = self.app
        query = self.search_var.get().strip().lower()
        if query == getattr(self, "_placeholder_text", None):
            query = ""

        for widget in self.list_container.winfo_children():
            widget.destroy()

        contests = getattr(self, "all_contests", [])
        shown = 0
        for contest in contests:
            title = contest["title_bn"] if app.language == "bn" else contest["title_en"]
            if query and query not in title.lower() \
                    and query not in contest["title_en"].lower() \
                    and query not in contest["title_bn"].lower():
                continue
            shown += 1
            row = tk.Frame(self.list_container, bg="white", padx=15, pady=12,
                            highlightbackground="#ddd", highlightthickness=1)
            row.pack(fill="x", pady=6)

            unlocked = dm.is_contest_unlocked(app.data, app.current_user, contest)

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

        if query and shown == 0:
            tk.Label(self.list_container, text=tr(app, "no_results_msg"),
                     font=("Helvetica", 12), bg=BG_COLOR, fg="#999").pack(pady=20)

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

        # Log this attempt (pass or fail) for the leaderboard's penalty/attempt
        # tracking, and store the code itself so the admin's plagiarism
        # checker can compare solutions across students.
        dm.record_submission(app.data, app.current_user, contest["id"],
                              self.current_problem["id"], all_passed,
                              code=self.code_box.get("1.0", tk.END),
                              language=self.language_var.get())
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
        self.plagiarism_btn = tk.Button(top, bg="#f5e6f7", fg="#7d3c9e",
                                         font=("Helvetica", 11, "bold"),
                                         command=lambda: app.show_frame("PlagiarismCheckScreen"))
        self.plagiarism_btn.pack(side="right", padx=8)
        self.content_mgmt_btn = tk.Button(top, bg="#e6f7ec", fg="#1e7a3d",
                                           font=("Helvetica", 11, "bold"),
                                           command=lambda: app.show_frame("ContentManagementScreen"))
        self.content_mgmt_btn.pack(side="right", padx=8)

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
        self.plagiarism_btn.config(text=tr(self.app, "plagiarism_check_btn"))
        self.content_mgmt_btn.config(text=tr(self.app, "content_mgmt_btn"))

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


class ContentManagementScreen(tk.Frame):
    """Admin-only panel: two big cards that let the admin add a brand-new
    lesson or a brand-new contest (with problems + test cases) directly
    from the app, without hand-editing data.json / contests.json."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_COLOR)
        self.app = app

        top = tk.Frame(self, bg=BG_COLOR)
        top.pack(fill="x", pady=15, padx=20)
        self.back_btn = tk.Button(top, command=lambda: app.show_frame("StudentManagementScreen"))
        self.back_btn.pack(side="left")
        self.title_label = tk.Label(top, font=("Helvetica", 20, "bold"), bg=BG_COLOR, fg=ACCENT_COLOR)
        self.title_label.pack(side="left", padx=20)
        LanguageToggle(top, app, on_change=self.apply_language).pack(side="right")

        self.subtitle_label = tk.Label(self, font=("Helvetica", 11), bg=BG_COLOR, fg="#666")
        self.subtitle_label.pack(padx=25, anchor="w")

        body = tk.Frame(self, bg=BG_COLOR)
        body.pack(expand=True, pady=30)

        # -- Add Lesson card --
        lesson_card = tk.Frame(body, bg="white", padx=30, pady=25, highlightbackground="#ddd", highlightthickness=1)
        lesson_card.grid(row=0, column=0, padx=15, pady=10)
        self.lesson_card_title = tk.Label(lesson_card, font=("Helvetica", 15, "bold"), bg="white", fg=ACCENT_COLOR)
        self.lesson_card_title.pack(anchor="w")
        self.lesson_card_desc = tk.Label(lesson_card, font=("Helvetica", 10), bg="white", fg="#666",
                                          wraplength=260, justify="left")
        self.lesson_card_desc.pack(anchor="w", pady=(6, 16))
        self.add_lesson_btn = tk.Button(lesson_card, bg=BTN_COLOR, fg="white", font=("Helvetica", 11, "bold"),
                                         width=20, pady=6, command=self.open_add_lesson_dialog)
        self.add_lesson_btn.pack(anchor="w")

        # -- Add Contest card --
        contest_card = tk.Frame(body, bg="white", padx=30, pady=25, highlightbackground="#ddd", highlightthickness=1)
        contest_card.grid(row=0, column=1, padx=15, pady=10)
        self.contest_card_title = tk.Label(contest_card, font=("Helvetica", 15, "bold"), bg="white", fg=ACCENT_COLOR)
        self.contest_card_title.pack(anchor="w")
        self.contest_card_desc = tk.Label(contest_card, font=("Helvetica", 10), bg="white", fg="#666",
                                           wraplength=260, justify="left")
        self.contest_card_desc.pack(anchor="w", pady=(6, 16))
        self.add_contest_btn = tk.Button(contest_card, bg=BTN_COLOR, fg="white", font=("Helvetica", 11, "bold"),
                                          width=20, pady=6, command=self.open_add_contest_dialog)
        self.add_contest_btn.pack(anchor="w")

        self.apply_language()

    def apply_language(self):
        app = self.app
        self.back_btn.config(text=tr(app, "admin_logout_btn"))
        self.title_label.config(text=tr(app, "content_mgmt_title"))
        self.subtitle_label.config(text=tr(app, "content_mgmt_subtitle"))
        self.lesson_card_title.config(text=tr(app, "add_lesson_card_title"))
        self.lesson_card_desc.config(text=tr(app, "add_lesson_card_desc"))
        self.add_lesson_btn.config(text=tr(app, "open_btn"))
        self.contest_card_title.config(text=tr(app, "add_contest_card_title"))
        self.contest_card_desc.config(text=tr(app, "add_contest_card_desc"))
        self.add_contest_btn.config(text=tr(app, "open_btn"))

    def on_show(self):
        self.app.refresh_data()
        self.app.contests = dm.load_contests()
        self.apply_language()

    # ------------------------------------------------------------------
    # Add Lesson dialog
    # ------------------------------------------------------------------
    def open_add_lesson_dialog(self):
        app = self.app

        dialog = tk.Toplevel(self)
        dialog.title(tr(app, "add_lesson_title"))
        dialog.configure(bg="white")
        dialog.geometry("560x640")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        outer = tk.Frame(dialog, bg="white", padx=20, pady=15)
        outer.pack(fill="both", expand=True)

        tk.Label(outer, text=tr(app, "add_lesson_title"), font=("Helvetica", 14, "bold"),
                 bg="white", fg=ACCENT_COLOR).pack(anchor="w", pady=(0, 12))

        tk.Label(outer, text=tr(app, "module_field_label"), bg="white", font=("Helvetica", 10, "bold")).pack(anchor="w")
        module_var = tk.StringVar(value="python")
        tk.OptionMenu(outer, module_var, "python", "c", "cpp").pack(anchor="w", pady=(0, 10))

        tk.Label(outer, text=tr(app, "lesson_title_en_label"), bg="white", font=("Helvetica", 10, "bold")).pack(anchor="w")
        title_en_entry = tk.Entry(outer, font=("Helvetica", 10), width=60)
        title_en_entry.pack(anchor="w", pady=(0, 10))

        tk.Label(outer, text=tr(app, "lesson_title_bn_label"), bg="white", font=("Helvetica", 10, "bold")).pack(anchor="w")
        title_bn_entry = tk.Entry(outer, font=("Helvetica", 10), width=60)
        title_bn_entry.pack(anchor="w", pady=(0, 10))

        tk.Label(outer, text=tr(app, "lesson_content_en_label"), bg="white", font=("Helvetica", 10, "bold")).pack(anchor="w")
        content_en_text = tk.Text(outer, font=("Helvetica", 10), width=60, height=4, wrap="word")
        content_en_text.pack(anchor="w", pady=(0, 10))

        tk.Label(outer, text=tr(app, "lesson_content_bn_label"), bg="white", font=("Helvetica", 10, "bold")).pack(anchor="w")
        content_bn_text = tk.Text(outer, font=("Helvetica", 10), width=60, height=4, wrap="word")
        content_bn_text.pack(anchor="w", pady=(0, 10))

        tk.Label(outer, text=tr(app, "code_example_label"), bg="white", font=("Helvetica", 10, "bold")).pack(anchor="w")
        code_text = tk.Text(outer, font=("Courier New", 10), width=60, height=6, wrap="none")
        code_text.pack(anchor="w", pady=(0, 12))

        message_label = tk.Label(outer, text="", bg="white", font=("Helvetica", 10), fg="#e74c3c")
        message_label.pack(anchor="w")

        def save_lesson():
            module = module_var.get()
            title_en = title_en_entry.get().strip()
            title_bn = title_bn_entry.get().strip()
            content_en = content_en_text.get("1.0", "end").strip()
            content_bn = content_bn_text.get("1.0", "end").strip()
            code_example = code_text.get("1.0", "end").strip()

            if not (module and title_en and title_bn and content_en and content_bn):
                message_label.config(text=tr(app, "lesson_missing_fields_msg"))
                return

            dm.add_lesson(app.data, module, title_en, title_bn, content_en, content_bn, code_example)
            app.refresh_data()
            dialog.destroy()
            messagebox.showinfo(tr(app, "lesson_saved_title"),
                                 tr(app, "lesson_saved_msg", title=title_en, module=module))

        btn_row = tk.Frame(outer, bg="white")
        btn_row.pack(anchor="w", pady=(4, 0))
        tk.Button(btn_row, text=tr(app, "save_lesson_btn"), bg=BTN_COLOR, fg="white",
                  font=("Helvetica", 10, "bold"), command=save_lesson).pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text=tr(app, "cancel_btn"), font=("Helvetica", 10),
                  command=dialog.destroy).pack(side="left")

    # ------------------------------------------------------------------
    # Add Contest dialog (contest info + a running list of problems)
    # ------------------------------------------------------------------
    def open_add_contest_dialog(self):
        app = self.app

        dialog = tk.Toplevel(self)
        dialog.title(tr(app, "add_contest_title"))
        dialog.configure(bg="white")
        dialog.geometry("620x680")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        problems = []  # accumulates fully-built problem dicts before final save

        outer = tk.Frame(dialog, bg="white", padx=20, pady=15)
        outer.pack(fill="both", expand=True)

        tk.Label(outer, text=tr(app, "add_contest_title"), font=("Helvetica", 14, "bold"),
                 bg="white", fg=ACCENT_COLOR).pack(anchor="w", pady=(0, 12))

        module_row = tk.Frame(outer, bg="white")
        module_row.pack(anchor="w", fill="x", pady=(0, 10))
        tk.Label(module_row, text=tr(app, "module_field_label"), bg="white", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky="w")
        module_var = tk.StringVar(value="python")
        contest_id_entry_ref = {}

        def suggest_id(*_):
            if "entry" in contest_id_entry_ref:
                entry = contest_id_entry_ref["entry"]
                entry.delete(0, tk.END)
                entry.insert(0, dm.next_contest_id(app.contests, module_var.get()))

        tk.OptionMenu(module_row, module_var, "python", "c", "cpp", command=suggest_id).grid(row=0, column=1, sticky="w", padx=10)

        tk.Label(module_row, text=tr(app, "unlock_after_label"), bg="white", font=("Helvetica", 10, "bold")).grid(row=0, column=2, sticky="w", padx=(20, 0))
        unlock_entry = tk.Entry(module_row, font=("Helvetica", 10), width=6)
        unlock_entry.insert(0, "2")
        unlock_entry.grid(row=0, column=3, sticky="w", padx=8)

        tk.Label(outer, text=tr(app, "contest_id_label"), bg="white", font=("Helvetica", 10, "bold")).pack(anchor="w")
        contest_id_entry = tk.Entry(outer, font=("Helvetica", 10), width=40)
        contest_id_entry.insert(0, dm.next_contest_id(app.contests, module_var.get()))
        contest_id_entry.pack(anchor="w", pady=(0, 10))
        contest_id_entry_ref["entry"] = contest_id_entry

        tk.Label(outer, text=tr(app, "contest_title_en_label"), bg="white", font=("Helvetica", 10, "bold")).pack(anchor="w")
        contest_title_en_entry = tk.Entry(outer, font=("Helvetica", 10), width=60)
        contest_title_en_entry.pack(anchor="w", pady=(0, 10))

        tk.Label(outer, text=tr(app, "contest_title_bn_label"), bg="white", font=("Helvetica", 10, "bold")).pack(anchor="w")
        contest_title_bn_entry = tk.Entry(outer, font=("Helvetica", 10), width=60)
        contest_title_bn_entry.pack(anchor="w", pady=(0, 10))

        tk.Label(outer, text=tr(app, "problems_label"), font=("Helvetica", 11, "bold"),
                 bg="white", fg=ACCENT_COLOR).pack(anchor="w", pady=(10, 4))

        problems_list_frame = tk.Frame(outer, bg="white")
        problems_list_frame.pack(anchor="w", fill="x")

        def refresh_problems_list():
            for w in problems_list_frame.winfo_children():
                w.destroy()
            if not problems:
                tk.Label(problems_list_frame, text=tr(app, "no_problems_msg"), bg="white",
                         fg="#999", font=("Helvetica", 9)).pack(anchor="w")
                return
            for idx, p in enumerate(problems):
                row = tk.Frame(problems_list_frame, bg="#f7f8fa")
                row.pack(fill="x", pady=2)
                tk.Label(row, text=f"[{p['difficulty']}] {p['title_en']}  ({p['id']})",
                         bg="#f7f8fa", font=("Helvetica", 9), anchor="w").pack(side="left", padx=6, pady=4)
                tk.Button(row, text=tr(app, "remove_btn"), font=("Helvetica", 8), bg="#fdecea",
                          fg="#c0392b", command=lambda i=idx: remove_problem(i)).pack(side="right", padx=6)

        def remove_problem(idx):
            problems.pop(idx)
            refresh_problems_list()

        def on_problem_added(problem):
            problems.append(problem)
            refresh_problems_list()

        add_problem_btn = tk.Button(outer, text=tr(app, "add_problem_btn"), bg="#eaf3fb", fg=BTN_COLOR,
                                     font=("Helvetica", 10, "bold"),
                                     command=lambda: self.open_add_problem_dialog(dialog, on_problem_added, problems))
        add_problem_btn.pack(anchor="w", pady=(8, 12))

        message_label = tk.Label(outer, text="", bg="white", font=("Helvetica", 10), fg="#e74c3c")
        message_label.pack(anchor="w")

        def save_contest():
            module = module_var.get()
            contest_id = contest_id_entry.get().strip()
            title_en = contest_title_en_entry.get().strip()
            title_bn = contest_title_bn_entry.get().strip()

            try:
                unlock_after = int(unlock_entry.get())
                if unlock_after < 0:
                    raise ValueError
            except ValueError:
                message_label.config(text=tr(app, "invalid_xp_reward_msg"))
                return

            if not (contest_id and title_en and title_bn):
                message_label.config(text=tr(app, "contest_missing_fields_msg"))
                return
            if dm.contest_id_exists(app.contests, contest_id):
                message_label.config(text=tr(app, "contest_duplicate_id_msg"))
                return
            if not problems:
                message_label.config(text=tr(app, "contest_no_problems_msg"))
                return

            contest = {
                "id": contest_id,
                "module": module,
                "unlock_after_lessons": unlock_after,
                "title_en": title_en,
                "title_bn": title_bn,
                "problems": problems,
            }
            dm.add_contest(app.contests, contest)
            dialog.destroy()
            messagebox.showinfo(tr(app, "contest_saved_title"),
                                 tr(app, "contest_saved_msg", title=title_en, n=len(problems)))

        btn_row = tk.Frame(outer, bg="white")
        btn_row.pack(anchor="w", pady=(4, 0))
        tk.Button(btn_row, text=tr(app, "save_contest_btn"), bg=BTN_COLOR, fg="white",
                  font=("Helvetica", 10, "bold"), command=save_contest).pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text=tr(app, "cancel_btn"), font=("Helvetica", 10),
                  command=dialog.destroy).pack(side="left")

        refresh_problems_list()

    # ------------------------------------------------------------------
    # Add Problem dialog (nested — invoked from the Add Contest dialog)
    # ------------------------------------------------------------------
    def open_add_problem_dialog(self, parent_dialog, on_saved, existing_problems):
        app = self.app

        dialog = tk.Toplevel(parent_dialog)
        dialog.title(tr(app, "add_problem_title"))
        dialog.configure(bg="white")
        dialog.geometry("560x680")
        dialog.transient(parent_dialog)
        dialog.grab_set()

        test_cases = []  # list of (input_entry_value, expected_entry_value) captured at save time

        outer = tk.Frame(dialog, bg="white", padx=20, pady=15)
        outer.pack(fill="both", expand=True)

        tk.Label(outer, text=tr(app, "add_problem_title"), font=("Helvetica", 13, "bold"),
                 bg="white", fg=ACCENT_COLOR).pack(anchor="w", pady=(0, 10))

        row1 = tk.Frame(outer, bg="white")
        row1.pack(anchor="w", fill="x", pady=(0, 10))
        tk.Label(row1, text=tr(app, "problem_id_label"), bg="white", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky="w")
        problem_id_entry = tk.Entry(row1, font=("Helvetica", 10), width=20)
        problem_id_entry.grid(row=0, column=1, sticky="w", padx=8)
        tk.Label(row1, text=tr(app, "difficulty_label"), bg="white", font=("Helvetica", 10, "bold")).grid(row=0, column=2, sticky="w", padx=(20, 0))
        difficulty_var = tk.StringVar(value="easy")
        tk.OptionMenu(row1, difficulty_var, "easy", "medium", "hard").grid(row=0, column=3, sticky="w", padx=8)

        tk.Label(outer, text=tr(app, "problem_title_en_label"), bg="white", font=("Helvetica", 10, "bold")).pack(anchor="w")
        p_title_en_entry = tk.Entry(outer, font=("Helvetica", 10), width=55)
        p_title_en_entry.pack(anchor="w", pady=(0, 8))

        tk.Label(outer, text=tr(app, "problem_title_bn_label"), bg="white", font=("Helvetica", 10, "bold")).pack(anchor="w")
        p_title_bn_entry = tk.Entry(outer, font=("Helvetica", 10), width=55)
        p_title_bn_entry.pack(anchor="w", pady=(0, 8))

        tk.Label(outer, text=tr(app, "problem_desc_en_label"), bg="white", font=("Helvetica", 10, "bold")).pack(anchor="w")
        p_desc_en_text = tk.Text(outer, font=("Helvetica", 10), width=55, height=3, wrap="word")
        p_desc_en_text.pack(anchor="w", pady=(0, 8))

        tk.Label(outer, text=tr(app, "problem_desc_bn_label"), bg="white", font=("Helvetica", 10, "bold")).pack(anchor="w")
        p_desc_bn_text = tk.Text(outer, font=("Helvetica", 10), width=55, height=3, wrap="word")
        p_desc_bn_text.pack(anchor="w", pady=(0, 8))

        xp_row = tk.Frame(outer, bg="white")
        xp_row.pack(anchor="w", pady=(0, 10))
        tk.Label(xp_row, text=tr(app, "xp_reward_label"), bg="white", font=("Helvetica", 10, "bold")).pack(side="left")
        xp_entry = tk.Entry(xp_row, font=("Helvetica", 10), width=8)
        xp_entry.insert(0, "30")
        xp_entry.pack(side="left", padx=8)

        tk.Label(outer, text=tr(app, "test_cases_label"), font=("Helvetica", 11, "bold"),
                 bg="white", fg=ACCENT_COLOR).pack(anchor="w", pady=(6, 4))

        tc_container = tk.Frame(outer, bg="white")
        tc_container.pack(anchor="w", fill="x")
        tc_rows = []  # list of (row_frame, input_entry, expected_entry)

        def add_test_case_row():
            row = tk.Frame(tc_container, bg="#f7f8fa")
            row.pack(fill="x", pady=3)
            tk.Label(row, text=tr(app, "test_input_label"), bg="#f7f8fa", font=("Helvetica", 9)).grid(row=0, column=0, padx=(4, 2), pady=4)
            in_entry = tk.Entry(row, font=("Helvetica", 9), width=20)
            in_entry.grid(row=0, column=1, padx=2)
            tk.Label(row, text=tr(app, "test_expected_label"), bg="#f7f8fa", font=("Helvetica", 9)).grid(row=0, column=2, padx=(10, 2))
            exp_entry = tk.Entry(row, font=("Helvetica", 9), width=20)
            exp_entry.grid(row=0, column=3, padx=2)

            def remove_row():
                tc_container_row = (row, in_entry, exp_entry)
                if tc_container_row in tc_rows:
                    tc_rows.remove(tc_container_row)
                row.destroy()

            tk.Button(row, text="✕", font=("Helvetica", 8), bg="#fdecea", fg="#c0392b",
                      command=remove_row).grid(row=0, column=4, padx=6)
            tc_rows.append((row, in_entry, exp_entry))

        tk.Button(outer, text=tr(app, "add_test_case_btn"), bg="#eaf3fb", fg=BTN_COLOR,
                  font=("Helvetica", 9, "bold"), command=add_test_case_row).pack(anchor="w", pady=(4, 10))

        message_label = tk.Label(outer, text="", bg="white", font=("Helvetica", 10), fg="#e74c3c")
        message_label.pack(anchor="w")

        def save_problem():
            problem_id = problem_id_entry.get().strip()
            title_en = p_title_en_entry.get().strip()
            title_bn = p_title_bn_entry.get().strip()
            desc_en = p_desc_en_text.get("1.0", "end").strip()
            desc_bn = p_desc_bn_text.get("1.0", "end").strip()
            xp_text = xp_entry.get().strip()

            if not (problem_id and title_en and title_bn and desc_en and desc_bn and xp_text):
                message_label.config(text=tr(app, "problem_missing_fields_msg"))
                return
            try:
                xp_reward = int(xp_text)
                if xp_reward <= 0:
                    raise ValueError
            except ValueError:
                message_label.config(text=tr(app, "invalid_xp_reward_msg"))
                return
            if any(p["id"] == problem_id for p in existing_problems):
                message_label.config(text=tr(app, "problem_duplicate_id_msg"))
                return

            collected_cases = []
            for _, in_entry, exp_entry in tc_rows:
                in_val = in_entry.get()
                exp_val = exp_entry.get().strip()
                if exp_val == "":
                    continue
                collected_cases.append({"input": in_val, "expected_output": exp_val})

            if not collected_cases:
                message_label.config(text=tr(app, "problem_no_testcases_msg"))
                return

            problem = {
                "id": problem_id,
                "difficulty": difficulty_var.get(),
                "title_en": title_en,
                "title_bn": title_bn,
                "description_en": desc_en,
                "description_bn": desc_bn,
                "xp_reward": xp_reward,
                "test_cases": collected_cases,
            }
            on_saved(problem)
            dialog.destroy()

        btn_row = tk.Frame(outer, bg="white")
        btn_row.pack(anchor="w", pady=(8, 0))
        tk.Button(btn_row, text=tr(app, "save_problem_btn"), bg=BTN_COLOR, fg="white",
                  font=("Helvetica", 10, "bold"), command=save_problem).pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text=tr(app, "cancel_btn"), font=("Helvetica", 10),
                  command=dialog.destroy).pack(side="left")

        add_test_case_row()  # start with one empty row for convenience


class PlagiarismCheckScreen(tk.Frame):
    """Admin-only tool: scans every contest problem, compares each pair of
    students' FIRST accepted solution using difflib text similarity, and
    lists pairs at or above a chosen similarity threshold for manual review.
    See the disclaimer shown on-screen — this flags candidates for a human
    to look at, it does not prove copying on its own."""

    THRESHOLD_OPTIONS = [90, 85, 80, 75, 70, 60]

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_COLOR)
        self.app = app
        self.last_report = []

        top = tk.Frame(self, bg=BG_COLOR)
        top.pack(fill="x", pady=15, padx=20)
        self.back_btn = tk.Button(top, command=lambda: app.show_frame("StudentManagementScreen"))
        self.back_btn.pack(side="left")
        self.title_label = tk.Label(top, font=("Helvetica", 20, "bold"), bg=BG_COLOR, fg=ACCENT_COLOR)
        self.title_label.pack(side="left", padx=20)
        LanguageToggle(top, app, on_change=self.apply_language).pack(side="right")

        self.disclaimer_label = tk.Label(self, font=("Helvetica", 10, "italic"), bg="#fff8e1",
                                          fg="#8a6d3b", wraplength=940, justify="left",
                                          padx=12, pady=8)
        self.disclaimer_label.pack(fill="x", padx=20, pady=(0, 10))

        controls = tk.Frame(self, bg=BG_COLOR)
        controls.pack(fill="x", padx=20, pady=(0, 10))
        self.threshold_field_label = tk.Label(controls, font=("Helvetica", 11, "bold"),
                                               bg=BG_COLOR, fg=ACCENT_COLOR)
        self.threshold_field_label.pack(side="left")
        self.threshold_var = tk.IntVar(value=dm.DEFAULT_PLAGIARISM_THRESHOLD)
        self.threshold_dropdown = ttk.Combobox(controls, textvariable=self.threshold_var,
                                                values=self.THRESHOLD_OPTIONS, state="readonly",
                                                width=6, font=("Helvetica", 11))
        self.threshold_dropdown.pack(side="left", padx=10)
        self.scan_btn = tk.Button(controls, bg=BTN_COLOR, fg="white",
                                   font=("Helvetica", 11, "bold"), command=self.run_scan)
        self.scan_btn.pack(side="left", padx=10)

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
        app = self.app
        self.back_btn.config(text=tr(app, "back_btn"))
        self.title_label.config(text=tr(app, "plagiarism_title"))
        self.disclaimer_label.config(text=tr(app, "plagiarism_disclaimer"))
        self.threshold_field_label.config(text=tr(app, "threshold_label"))
        self.scan_btn.config(text=tr(app, "scan_btn"))
        if self.last_report or hasattr(self, "_scanned_once"):
            self._render_report()

    def on_show(self):
        self.app.refresh_data()
        self.apply_language()

    def run_scan(self):
        app = self.app
        self._scanned_once = True
        self.scan_btn.config(state="disabled", text=tr(app, "scanning_msg"))
        self.update_idletasks()
        threshold = self.threshold_var.get()
        self.last_report = dm.get_plagiarism_report(app.data, app.contests, threshold)
        self.scan_btn.config(state="normal", text=tr(app, "scan_btn"))
        self._render_report()

    def _render_report(self):
        app = self.app
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        self.empty_label.pack_forget()

        if not self.last_report:
            self.empty_label.config(text=tr(app, "no_matches_msg"))
            self.empty_label.pack(pady=30)
            return

        headers = ["col_problem", "col_student_a", "col_student_b", "col_similarity", "col_actions"]
        header_style = {"font": ("Helvetica", 10, "bold"), "bg": BTN_COLOR, "fg": "white", "padx": 8, "pady": 8}
        for c, key in enumerate(headers):
            tk.Label(self.table_frame, text=tr(app, key), **header_style).grid(
                row=0, column=c, sticky="nsew", padx=1, pady=1)

        row_i = 1
        for group in self.last_report:
            problem_title = group["problem_title_bn"] if app.language == "bn" else group["problem_title_en"]
            contest_title = group["contest_title_bn"] if app.language == "bn" else group["contest_title_en"]
            for pair in group["pairs"]:
                row_bg = "white" if row_i % 2 else "#f7f8fa"
                cell_style = {"font": ("Helvetica", 10), "bg": row_bg, "fg": ACCENT_COLOR, "padx": 8, "pady": 6}

                tk.Label(self.table_frame, text=f"{contest_title} — {problem_title}", anchor="w",
                         wraplength=260, justify="left", **cell_style).grid(row=row_i, column=0, sticky="nsew", padx=1, pady=1)
                tk.Label(self.table_frame, text=pair["user_a"], anchor="w", **cell_style).grid(row=row_i, column=1, sticky="nsew", padx=1, pady=1)
                tk.Label(self.table_frame, text=pair["user_b"], anchor="w", **cell_style).grid(row=row_i, column=2, sticky="nsew", padx=1, pady=1)

                sim = pair["similarity"]
                sim_color = "#c0392b" if sim >= 90 else ("#e67e22" if sim >= 80 else "#b3620a")
                tk.Label(self.table_frame, text=f"{sim}%", font=("Helvetica", 10, "bold"),
                         bg=row_bg, fg=sim_color, padx=8, pady=6).grid(row=row_i, column=3, sticky="nsew", padx=1, pady=1)

                action_cell = tk.Frame(self.table_frame, bg=row_bg)
                action_cell.grid(row=row_i, column=4, sticky="nsew", padx=1, pady=1)
                tk.Button(action_cell, text=tr(app, "view_code_btn"), font=("Helvetica", 9), bg="#eaf3fb",
                          fg=BTN_COLOR,
                          command=lambda g=group, p=pair: self.open_code_compare(g, p)).pack(padx=2, pady=4)

                row_i += 1

    def open_code_compare(self, group, pair):
        app = self.app
        code_a, _ = dm.get_first_passing_code(app.data, pair["user_a"], group["contest_id"], group["problem_id"])
        code_b, _ = dm.get_first_passing_code(app.data, pair["user_b"], group["contest_id"], group["problem_id"])

        dialog = tk.Toplevel(self)
        dialog.title(tr(app, "code_compare_title", a=pair["user_a"], b=pair["user_b"]))
        dialog.configure(bg="white")
        dialog.geometry("900x520")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        cols = tk.Frame(dialog, bg="white")
        cols.pack(fill="both", expand=True, padx=10, pady=10)

        left = tk.Frame(cols, bg="white")
        left.pack(side="left", fill="both", expand=True, padx=(0, 5))
        tk.Label(left, text=pair["user_a"], font=("Helvetica", 12, "bold"), bg="white", fg=ACCENT_COLOR).pack(anchor="w")
        left_box = tk.Text(left, font=("Consolas", 10), bg="#2d2d2d", fg="#f8f8f2", wrap="none")
        left_box.pack(fill="both", expand=True, pady=5)
        left_box.insert("1.0", code_a or "")
        left_box.config(state="disabled")

        right = tk.Frame(cols, bg="white")
        right.pack(side="left", fill="both", expand=True, padx=(5, 0))
        tk.Label(right, text=pair["user_b"], font=("Helvetica", 12, "bold"), bg="white", fg=ACCENT_COLOR).pack(anchor="w")
        right_box = tk.Text(right, font=("Consolas", 10), bg="#2d2d2d", fg="#f8f8f2", wrap="none")
        right_box.pack(fill="both", expand=True, pady=5)
        right_box.insert("1.0", code_b or "")
        right_box.config(state="disabled")


if __name__ == "__main__":
    app = CodeLearnApp()
    app.mainloop()