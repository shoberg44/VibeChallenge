# 🚀 Vibe-Check — Agent Handoff Prompt

> Copy-paste any section below to another agent so they can help build a specific part.

---

## Project Summary

**vibe-check** is a Python CLI tool that:
1. Scans a local directory for source files (e.g. `.py`)
2. Picks the **3 largest files** (skipping `venv/`, `.git/`, `__pycache__/`, etc.)
3. Sends their contents to an **LLM API** (OpenAI)
4. The LLM analyzes coding style and returns a **Markdown ruleset**
5. Writes the result to `ai-coding-standards.md` in the scanned directory

**Tech stack:** Python 3.10+, `argparse`, `pathlib`, `openai` SDK, `rich` (for terminal UI)

**Repo location:** `c:\Users\steve\Documents\GitHub\VibeChallenge\`

---

## Task A — File Discovery & Filtering (AVAILABLE)

> **Prompt for another agent:**

```
You are working on a Python CLI tool called "vibe-check" in the repo at c:\Users\steve\Documents\GitHub\VibeChallenge\.

Your task: In the file `vibe_check.py`, implement the function `discover_files(path: str, ext: str) -> list[Path]`.

Requirements:
- Use pathlib.Path.rglob() to find all files matching the given extension
- IGNORE directories: venv, env, .venv, .git, __pycache__, node_modules, .tox, .eggs, build, dist
- Sort results by file size DESCENDING
- Return only the TOP 3 largest files
- Return a list of pathlib.Path objects
- Add type hints and a docstring

The function signature should be:
def discover_files(scan_path: str, ext: str) -> list[Path]:
```

---

## Task B — LLM Integration (AVAILABLE)

> **Prompt for another agent:**

```
You are working on a Python CLI tool called "vibe-check" in the repo at c:\Users\steve\Documents\GitHub\VibeChallenge\.

Your task: In the file `vibe_check.py`, implement the function `call_llm(content: str, api_key: str) -> str`.

Requirements:
- Use the `openai` Python SDK (v1.0+)
- Call the `gpt-4o-mini` model via chat completions
- System prompt: "You are a senior software developer performing a code review. Analyze the provided code samples and produce a comprehensive Markdown document defining strict coding standards. Cover: variable/function naming conventions, comment style, docstring format, import ordering, error handling patterns, architectural patterns, and any anti-patterns to avoid."
- The user message should be the concatenated file content
- Return the response content as a string
- Handle API errors gracefully with try/except, print a clear error message
- The API key should come from the argument, or fall back to os.environ.get("OPENAI_API_KEY")

The function signature should be:
def call_llm(content: str, api_key: str | None = None) -> str:
```

---

## Task C — README & Documentation (AVAILABLE)

> **Prompt for another agent:**

```
You are working on a Python CLI tool called "vibe-check" in the repo at c:\Users\steve\Documents\GitHub\VibeChallenge\.

Your task: Write a polished README.md for this tool.

Include:
- Project name with emoji: 🎯 vibe-check
- One-line description
- Features list
- Installation (pip install -r requirements.txt)
- Usage examples with code blocks
- Example output
- How to set the API key (env var OPENAI_API_KEY or --api-key flag)
- License: reference the existing LICENSE file

Keep it concise but professional. This is for a coding competition — make it impressive.
```

---

## Task D — Unit Tests (AVAILABLE)

> **Prompt for another agent:**

```
You are working on a Python CLI tool called "vibe-check" in the repo at c:\Users\steve\Documents\GitHub\VibeChallenge\.

Your task: Create a file called `test_vibe_check.py` with comprehensive unit tests using `pytest`.

The main source file is `vibe_check.py`. Here are the functions you need to test:

### 1. `discover_files(scan_path: str, ext: str, top_n: int = 3) -> list[Path]`
- Uses pathlib.Path.rglob() to find files matching the extension
- Ignores dirs: venv, env, .venv, .git, __pycache__, node_modules, .tox, .eggs, build, dist, .mypy_cache, .pytest_cache, .ruff_cache
- Sorts by file size descending, returns top N
- Exits with sys.exit(1) if path doesn't exist

Test cases needed:
- Returns the 3 largest .py files from a directory with 5+ files
- Correctly ignores files inside venv/, __pycache__/, .git/, etc.
- Returns fewer than 3 if fewer files exist
- Returns empty list if no matching files exist
- Handles extension with and without leading dot (`.py` vs `py`)
- Exits gracefully when given a non-existent path
- Respects the top_n parameter (e.g., top_n=1 returns only 1 file)

### 2. `aggregate_content(files: list[Path], root: Path) -> str`
- Reads files and concatenates with headers

Test cases needed:
- Output contains "FILE:" header for each file
- Output contains "SIZE:" for each file
- Output contains actual file content
- Handles files with UTF-8 content
- Handles unreadable files gracefully (errors="replace")

### 3. `parse_args(argv: list[str] | None = None) -> argparse.Namespace`
- Parses CLI arguments

Test cases needed:
- --path is required; missing it raises SystemExit
- --ext defaults to ".py"
- --top defaults to 3
- --api-key defaults to None
- All flags parse correctly when provided

### 4. `write_output(scan_path: str, markdown: str) -> Path`
- Writes markdown string to ai-coding-standards.md

Test cases needed:
- Creates the output file in the correct location
- File contains the exact markdown content
- Returns the correct Path object

### 5. `call_llm(content: str, api_key: str | None = None) -> str`
- Calls OpenAI API — MOCK THIS, do not make real API calls

Test cases needed:
- Calls OpenAI with correct model ("gpt-4o-mini") and system prompt
- Returns the response content string
- Exits with sys.exit(1) if no API key is found (no arg + no env var)
- Exits with sys.exit(1) on API error
- Exits with sys.exit(1) if openai package is not installed

Requirements:
- Use pytest and tmp_path fixture for filesystem tests
- Use unittest.mock.patch to mock the OpenAI client (never make real API calls)
- Use monkeypatch to test environment variable handling
- Add `pytest` to requirements.txt
- Every test function should have a clear docstring explaining what it verifies
- Aim for at least 90% code coverage of the non-main functions
```

---

## Task E — Swap LLM from OpenAI to Google Gemini (PRIORITY 🔴)

> **Prompt for another agent:**

```
You are working on a Python CLI tool called "vibe-check" in the repo at c:\Users\steve\Documents\GitHub\VibeChallenge\.

Your task: Modify `vibe_check.py` to use **Google Gemini** instead of OpenAI. This is critical — we need a FREE API with no credit card.

### What to change in `vibe_check.py`:

1. **Replace the import**: Remove `from openai import OpenAI`. Replace with `import google.generativeai as genai`.

2. **Replace the `call_llm` function** with this logic:
   - Get the API key from the `api_key` argument, or fall back to `os.environ.get("GEMINI_API_KEY")`
   - If no key found, print error and sys.exit(1)
   - Configure the SDK: `genai.configure(api_key=key)`
   - Create the model: `model = genai.GenerativeModel("gemini-2.0-flash")`
   - Send the prompt: combine the SYSTEM_PROMPT and the user content into a single prompt string
   - Call `model.generate_content(prompt)`
   - Return `response.text`
   - Wrap in try/except, print clear error on failure

3. **Update the CLI help text**: Change `--api-key` help from mentioning OpenAI to: "Google Gemini API key. Falls back to GEMINI_API_KEY env var."

4. **Update error messages**: Any reference to "OPENAI_API_KEY" should become "GEMINI_API_KEY". Any reference to "openai package" should become "google-generativeai package".

5. **Update the import check** at the top: Change the try/except block from importing openai to:
   ```python
   try:
       import google.generativeai as genai
   except ImportError:
       genai = None
   ```

### What to change in `requirements.txt`:
- Replace `openai>=1.0` with `google-generativeai>=0.8.0`
- Keep `rich>=13.0` and `pytest>=7.0` unchanged

### What NOT to change:
- Do NOT touch the banner, CLI args structure, discover_files, aggregate_content, write_output, or main()
- Do NOT change the SYSTEM_PROMPT constant
- Do NOT change the rich UI formatting
- Keep the same function signature: `def call_llm(content: str, api_key: str | None = None) -> str:`

### Verify:
- Run `py -3 vibe_check.py --help` to confirm it still works
- Run `py -3 -c "from vibe_check import call_llm; print('import OK')"` to verify imports
```

---

## Status Dashboard

| Task | Description | Status |
|---|---|---|
| Core CLI + UI | Banner, argparse, rich output | ✅ Done |
| Task A | File Discovery | ✅ Done (built into core) |
| Task B | LLM Integration | 🔄 Being replaced by Task E |
| Task C | README & Documentation | ✅ Done |
| Task D | Unit Tests | 🔄 In progress |
| Task E | Swap to Gemini (free) | 🔴 **HIGH PRIORITY — do this next** |
