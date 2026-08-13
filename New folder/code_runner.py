"""
code_runner.py
Runs user-written code LOCALLY using subprocess — supports Python, C, C++,
and Java. No external API needed.

Requirements on the local machine for each language:
  - Python: no extra install needed
  - C:      gcc must be installed and on PATH
  - C++:    g++ must be installed and on PATH
  - Java:   JDK (javac + java) must be installed and on PATH
"""

import subprocess
import sys
import tempfile
import os
import re

TIMEOUT_SECONDS = 10

SUPPORTED_LANGUAGES = ["python", "c", "cpp", "java"]


def run_code(language, code, stdin_input=""):
    language = language.lower().strip()
    try:
        if language == "python":
            return _run_python(code, stdin_input)
        elif language == "c":
            return _run_c_cpp("c", code, stdin_input)
        elif language in ("cpp", "c++"):
            return _run_c_cpp("cpp", code, stdin_input)
        elif language == "java":
            return _run_java(code, stdin_input)
        else:
            return {"success": False, "output": "", "error": f"Unsupported language: {language}"}
    except Exception as e:
        return {"success": False, "output": "", "error": f"Execution error: {e}"}


def _run_python(code, stdin_input):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        temp_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, temp_path],
            input=stdin_input,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
        if result.returncode != 0:
            return {"success": False, "output": result.stdout, "error": result.stderr}
        return {"success": True, "output": result.stdout, "error": ""}
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "", "error": "Code took too long to run (possible infinite loop)."}
    finally:
        os.remove(temp_path)


def _run_c_cpp(language, code, stdin_input):
    ext = ".c" if language == "c" else ".cpp"
    compiler = "gcc" if language == "c" else "g++"

    with tempfile.NamedTemporaryFile(mode="w", suffix=ext, delete=False, encoding="utf-8") as f:
        f.write(code)
        src_path = f.name

    exe_path = src_path + (".exe" if os.name == "nt" else ".out")

    try:
        compile_result = subprocess.run(
            [compiler, src_path, "-o", exe_path],
            capture_output=True, text=True, timeout=TIMEOUT_SECONDS,
        )
        if compile_result.returncode != 0:
            return {"success": False, "output": "", "error": compile_result.stderr}

        run_result = subprocess.run(
            [exe_path], input=stdin_input, capture_output=True, text=True, timeout=TIMEOUT_SECONDS,
        )
        if run_result.returncode != 0:
            return {"success": False, "output": run_result.stdout, "error": run_result.stderr}
        return {"success": True, "output": run_result.stdout, "error": ""}

    except FileNotFoundError:
        return {"success": False, "output": "",
                "error": f"'{compiler}' not found. Install MinGW (Windows) or gcc/g++ to run {language.upper()} code."}
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "", "error": "Code took too long to run (possible infinite loop)."}
    finally:
        os.remove(src_path)
        if os.path.exists(exe_path):
            os.remove(exe_path)


def _run_java(code, stdin_input):
    match = re.search(r"public\s+class\s+(\w+)", code)
    class_name = match.group(1) if match else "Main"

    temp_dir = tempfile.mkdtemp()
    src_path = os.path.join(temp_dir, f"{class_name}.java")

    with open(src_path, "w", encoding="utf-8") as f:
        f.write(code)

    try:
        compile_result = subprocess.run(
            ["javac", src_path],
            capture_output=True, text=True, timeout=TIMEOUT_SECONDS, cwd=temp_dir,
        )
        if compile_result.returncode != 0:
            return {"success": False, "output": "", "error": compile_result.stderr}

        run_result = subprocess.run(
            ["java", "-cp", temp_dir, class_name],
            input=stdin_input, capture_output=True, text=True, timeout=TIMEOUT_SECONDS,
        )
        if run_result.returncode != 0:
            return {"success": False, "output": run_result.stdout, "error": run_result.stderr}
        return {"success": True, "output": run_result.stdout, "error": ""}

    except FileNotFoundError:
        return {"success": False, "output": "",
                "error": "'javac'/'java' not found. Install a JDK to run Java code."}
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "", "error": "Code took too long to run (possible infinite loop)."}
    finally:
        for fname in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, fname))
        os.rmdir(temp_dir)


def run_test_cases(language, code, test_cases):
    results = []
    for case in test_cases:
        result = run_code(language, code, stdin_input=case.get("input", ""))
        actual = result["output"].strip()
        expected = case.get("expected_output", "").strip()
        passed = result["success"] and actual == expected
        results.append({
            "input": case.get("input", ""),
            "expected": expected,
            "actual": actual,
            "passed": passed,
            "error": result["error"],
        })
    return results