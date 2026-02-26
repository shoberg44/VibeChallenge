#!/usr/bin/env python3
"""
Comprehensive unit-test suite for vibe_check.py.

Run with:
    pytest test_vibe_check.py -v --tb=short
"""

import argparse
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── Import the module under test ──────────────────────────────────────────────
import vibe_check


# ═══════════════════════════════════════════════════════════════════════════════
# 1. discover_files
# ═══════════════════════════════════════════════════════════════════════════════


class TestDiscoverFiles:
    """Tests for discover_files(scan_path, ext, top_n)."""

    # -- helpers ----------------------------------------------------------
    @staticmethod
    def _populate(base: Path, rel_paths: dict[str, int]) -> None:
        """Create files under *base* with the given relative paths and sizes.

        ``rel_paths`` maps ``"subdir/file.py"`` → desired file-size in bytes.
        """
        for rel, size in rel_paths.items():
            p = base / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"x" * size)

    # -- tests ------------------------------------------------------------
    def test_returns_three_largest_files(self, tmp_path: Path):
        """Should return the 3 largest .py files when more than 3 exist."""
        self._populate(tmp_path, {
            "a.py": 100,
            "b.py": 200,
            "c.py": 300,
            "d.py": 400,
            "e.py": 500,
        })
        result = vibe_check.discover_files(str(tmp_path), ".py", top_n=3)
        sizes = [f.stat().st_size for f in result]
        assert len(result) == 3
        assert sizes == [500, 400, 300], "Files should be ordered largest-first"

    def test_ignores_venv_directory(self, tmp_path: Path):
        """Files inside a venv/ directory must be excluded."""
        self._populate(tmp_path, {
            "venv/big.py": 9999,
            "real.py": 10,
        })
        result = vibe_check.discover_files(str(tmp_path), ".py")
        names = [f.name for f in result]
        assert "big.py" not in names
        assert "real.py" in names

    def test_ignores_pycache_directory(self, tmp_path: Path):
        """Files inside __pycache__/ must be excluded."""
        self._populate(tmp_path, {
            "__pycache__/cached.py": 5000,
            "main.py": 10,
        })
        result = vibe_check.discover_files(str(tmp_path), ".py")
        names = [f.name for f in result]
        assert "cached.py" not in names
        assert "main.py" in names

    def test_ignores_git_directory(self, tmp_path: Path):
        """Files inside .git/ must be excluded."""
        self._populate(tmp_path, {
            ".git/hooks/pre-commit.py": 8000,
            "app.py": 20,
        })
        result = vibe_check.discover_files(str(tmp_path), ".py")
        names = [f.name for f in result]
        assert "pre-commit.py" not in names
        assert "app.py" in names

    def test_ignores_node_modules(self, tmp_path: Path):
        """Files inside node_modules/ must be excluded."""
        self._populate(tmp_path, {
            "node_modules/dep.py": 6000,
            "src/index.py": 15,
        })
        result = vibe_check.discover_files(str(tmp_path), ".py")
        names = [f.name for f in result]
        assert "dep.py" not in names

    def test_ignores_multiple_excluded_dirs(self, tmp_path: Path):
        """All directories in IGNORE_DIRS should be skipped simultaneously."""
        self._populate(tmp_path, {
            "env/a.py": 100,
            ".venv/b.py": 200,
            ".tox/c.py": 300,
            ".eggs/d.py": 400,
            "build/e.py": 500,
            "dist/f.py": 600,
            ".mypy_cache/g.py": 700,
            ".pytest_cache/h.py": 800,
            ".ruff_cache/i.py": 900,
            "legit.py": 10,
        })
        result = vibe_check.discover_files(str(tmp_path), ".py")
        assert len(result) == 1
        assert result[0].name == "legit.py"

    def test_returns_fewer_than_top_n_when_not_enough_files(self, tmp_path: Path):
        """If fewer matching files exist than top_n, return whatever is found."""
        self._populate(tmp_path, {"only.py": 50})
        result = vibe_check.discover_files(str(tmp_path), ".py", top_n=3)
        assert len(result) == 1

    def test_returns_empty_list_when_no_matching_files(self, tmp_path: Path):
        """An empty list is returned when no files match the extension."""
        self._populate(tmp_path, {"readme.md": 100})
        result = vibe_check.discover_files(str(tmp_path), ".py")
        assert result == []

    def test_extension_without_leading_dot(self, tmp_path: Path):
        """Passing 'py' (no dot) should work the same as '.py'."""
        self._populate(tmp_path, {"script.py": 42})
        result = vibe_check.discover_files(str(tmp_path), "py")
        assert len(result) == 1
        assert result[0].name == "script.py"

    def test_extension_with_leading_dot(self, tmp_path: Path):
        """Passing '.py' (with dot) should find .py files."""
        self._populate(tmp_path, {"script.py": 42})
        result = vibe_check.discover_files(str(tmp_path), ".py")
        assert len(result) == 1
        assert result[0].name == "script.py"

    def test_exits_on_nonexistent_path(self, tmp_path: Path):
        """Should call sys.exit(1) when the path does not exist."""
        fake_path = str(tmp_path / "does_not_exist")
        with pytest.raises(SystemExit) as exc_info:
            vibe_check.discover_files(fake_path, ".py")
        assert exc_info.value.code == 1

    def test_top_n_parameter_limits_results(self, tmp_path: Path):
        """top_n=1 should return only the single largest file."""
        self._populate(tmp_path, {
            "small.py": 10,
            "medium.py": 50,
            "large.py": 100,
        })
        result = vibe_check.discover_files(str(tmp_path), ".py", top_n=1)
        assert len(result) == 1
        assert result[0].name == "large.py"

    def test_top_n_five(self, tmp_path: Path):
        """top_n=5 should return all 5 files when exactly 5 exist."""
        self._populate(tmp_path, {
            "a.py": 10,
            "b.py": 20,
            "c.py": 30,
            "d.py": 40,
            "e.py": 50,
        })
        result = vibe_check.discover_files(str(tmp_path), ".py", top_n=5)
        assert len(result) == 5


# ═══════════════════════════════════════════════════════════════════════════════
# 2. aggregate_content
# ═══════════════════════════════════════════════════════════════════════════════


class TestAggregateContent:
    """Tests for aggregate_content(files, root)."""

    def test_contains_file_header(self, tmp_path: Path):
        """Output must include a 'FILE:' header for each file."""
        f = tmp_path / "example.py"
        f.write_text("pass", encoding="utf-8")
        result = vibe_check.aggregate_content([f], tmp_path)
        assert "FILE: example.py" in result

    def test_contains_size_header(self, tmp_path: Path):
        """Output must include a 'SIZE:' line for each file."""
        f = tmp_path / "example.py"
        f.write_text("hello", encoding="utf-8")
        result = vibe_check.aggregate_content([f], tmp_path)
        assert "SIZE:" in result
        assert "bytes" in result

    def test_contains_file_content(self, tmp_path: Path):
        """Actual file content should appear in the aggregated string."""
        f = tmp_path / "example.py"
        f.write_text("print('hello world')", encoding="utf-8")
        result = vibe_check.aggregate_content([f], tmp_path)
        assert "print('hello world')" in result

    def test_multiple_files(self, tmp_path: Path):
        """All files should be represented in the aggregated output."""
        f1 = tmp_path / "one.py"
        f2 = tmp_path / "two.py"
        f1.write_text("# file one", encoding="utf-8")
        f2.write_text("# file two", encoding="utf-8")
        result = vibe_check.aggregate_content([f1, f2], tmp_path)
        assert "FILE: one.py" in result
        assert "FILE: two.py" in result
        assert "# file one" in result
        assert "# file two" in result

    def test_handles_utf8_content(self, tmp_path: Path):
        """UTF-8 encoded content (including non-ASCII) must be preserved."""
        f = tmp_path / "unicode.py"
        f.write_text("msg = '日本語テスト 🎯'", encoding="utf-8")
        result = vibe_check.aggregate_content([f], tmp_path)
        assert "日本語テスト 🎯" in result

    def test_handles_unreadable_file_gracefully(self, tmp_path: Path):
        """If a file cannot be read, a placeholder error message should appear
        instead of crashing."""
        f = tmp_path / "binary.py"
        # Write raw bytes that include invalid UTF-8 sequences
        f.write_bytes(b"\x80\x81\x82\x83")
        # aggregate_content uses errors="replace", so it should NOT raise
        result = vibe_check.aggregate_content([f], tmp_path)
        assert "FILE: binary.py" in result  # header is still present

    def test_separator_lines(self, tmp_path: Path):
        """Each file block should be separated by a line of '=' characters."""
        f = tmp_path / "sep.py"
        f.write_text("pass", encoding="utf-8")
        result = vibe_check.aggregate_content([f], tmp_path)
        assert "=" * 60 in result


# ═══════════════════════════════════════════════════════════════════════════════
# 3. parse_args
# ═══════════════════════════════════════════════════════════════════════════════


class TestParseArgs:
    """Tests for parse_args(argv)."""

    def test_path_defaults_to_none(self):
        """Omitting --path should result in args.path being None (triggering the wizard)."""
        ns = vibe_check.parse_args([])
        assert ns.path is None

    def test_ext_defaults_to_py(self):
        """--ext should default to '.py' when not provided."""
        ns = vibe_check.parse_args(["--path", "/some/dir"])
        assert ns.ext == ".py"

    def test_top_defaults_to_three(self):
        """--top should default to 3 when not provided."""
        ns = vibe_check.parse_args(["--path", "/some/dir"])
        assert ns.top == 3

    def test_api_key_defaults_to_none(self):
        """--api-key should default to None when not provided."""
        ns = vibe_check.parse_args(["--path", "/some/dir"])
        assert ns.api_key is None

    def test_all_flags_parsed(self):
        """All flags should parse correctly when explicitly provided."""
        ns = vibe_check.parse_args([
            "--path", "/my/project",
            "--ext", ".js",
            "--api-key", "sk-test-key",
            "--top", "5",
        ])
        assert ns.path == "/my/project"
        assert ns.ext == ".js"
        assert ns.api_key == "sk-test-key"
        assert ns.top == 5

    def test_returns_namespace_object(self):
        """parse_args should return an argparse.Namespace instance."""
        ns = vibe_check.parse_args(["--path", "."])
        assert isinstance(ns, argparse.Namespace)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. write_output
# ═══════════════════════════════════════════════════════════════════════════════


class TestWriteOutput:
    """Tests for write_output(scan_path, markdown)."""

    def test_creates_output_file(self, tmp_path: Path):
        """The output file should be created in the target directory."""
        vibe_check.write_output(str(tmp_path), "# Standards")
        expected = tmp_path / "ai-coding-standards.md"
        assert expected.exists()

    def test_file_contains_exact_content(self, tmp_path: Path):
        """The written file should contain exactly the markdown passed in."""
        md = "# My Coding Standards\n\n- Rule 1\n- Rule 2\n"
        vibe_check.write_output(str(tmp_path), md)
        content = (tmp_path / "ai-coding-standards.md").read_text(encoding="utf-8")
        assert content == md

    def test_returns_correct_path(self, tmp_path: Path):
        """write_output must return the Path object pointing to the new file."""
        result = vibe_check.write_output(str(tmp_path), "content")
        expected = (tmp_path / "ai-coding-standards.md").resolve()
        assert result == expected

    def test_overwrites_existing_file(self, tmp_path: Path):
        """If the file already exists, it should be overwritten cleanly."""
        vibe_check.write_output(str(tmp_path), "old content")
        vibe_check.write_output(str(tmp_path), "new content")
        content = (tmp_path / "ai-coding-standards.md").read_text(encoding="utf-8")
        assert content == "new content"


# ═══════════════════════════════════════════════════════════════════════════════
# 5. call_llm  (always mocked — no real API calls)
# ═══════════════════════════════════════════════════════════════════════════════


class TestCallLLM:
    """Tests for call_llm(content, api_key).

    The Groq client is **always** mocked so no real API calls are made.
    """

    def _build_mock_response(self, text: str = "mock analysis") -> MagicMock:
        """Return a mock that mimics the Groq chat completion response."""
        mock_message = MagicMock()
        mock_message.content = text

        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        return mock_response

    @patch("vibe_check.Groq")
    def test_calls_groq_with_correct_model(self, mock_groq_cls):
        """The LLM call must use the 'llama-3.3-70b-versatile' model."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = self._build_mock_response()
        mock_groq_cls.return_value = mock_client

        vibe_check.call_llm("sample code", api_key="sk-test")

        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs.kwargs["model"] == "llama-3.3-70b-versatile"

    @patch("vibe_check.Groq")
    def test_sends_system_prompt(self, mock_groq_cls):
        """The system prompt constant should be included in the messages."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = self._build_mock_response()
        mock_groq_cls.return_value = mock_client

        vibe_check.call_llm("sample code", api_key="sk-test")

        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs["messages"]
        system_msgs = [m for m in messages if m["role"] == "system"]
        assert len(system_msgs) == 1
        assert system_msgs[0]["content"] == vibe_check.SYSTEM_PROMPT

    @patch("vibe_check.Groq")
    def test_returns_response_content(self, mock_groq_cls):
        """call_llm should return the text content from the API response."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = self._build_mock_response(
            "# Generated Standards"
        )
        mock_groq_cls.return_value = mock_client

        result = vibe_check.call_llm("code here", api_key="sk-test")
        assert result == "# Generated Standards"

    def test_exits_when_no_api_key(self, monkeypatch):
        """Should sys.exit(1) when no API key is provided and env var is unset."""
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        with pytest.raises(SystemExit) as exc_info:
            vibe_check.call_llm("code", api_key=None)
        assert exc_info.value.code == 1

    @patch("vibe_check.Groq")
    def test_exits_on_api_error(self, mock_groq_cls):
        """Should sys.exit(1) when the API raises an exception."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RuntimeError("API boom")
        mock_groq_cls.return_value = mock_client

        with pytest.raises(SystemExit) as exc_info:
            vibe_check.call_llm("code", api_key="sk-test")
        assert exc_info.value.code == 1

    def test_exits_when_groq_not_installed(self, monkeypatch):
        """Should sys.exit(1) when the groq package is not available."""
        monkeypatch.setattr(vibe_check, "Groq", None)
        with pytest.raises(SystemExit) as exc_info:
            vibe_check.call_llm("code", api_key="sk-test")
        assert exc_info.value.code == 1

    @patch("vibe_check.Groq")
    def test_uses_env_var_when_no_arg(self, mock_groq_cls, monkeypatch):
        """Falls back to GROQ_API_KEY env var when api_key arg is None."""
        monkeypatch.setenv("GROQ_API_KEY", "sk-env-key")
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = self._build_mock_response()
        mock_groq_cls.return_value = mock_client

        vibe_check.call_llm("code", api_key=None)

        mock_groq_cls.assert_called_once_with(api_key="sk-env-key")

    @patch("vibe_check.Groq")
    def test_prefers_explicit_key_over_env(self, mock_groq_cls, monkeypatch):
        """An explicitly passed api_key should take precedence over the env var."""
        monkeypatch.setenv("GROQ_API_KEY", "sk-env-key")
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = self._build_mock_response()
        mock_groq_cls.return_value = mock_client

        vibe_check.call_llm("code", api_key="sk-explicit")

        mock_groq_cls.assert_called_once_with(api_key="sk-explicit")
