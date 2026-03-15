#!/usr/bin/env python3
"""
🎯 vibe-check — Scan your codebase. Extract your coding standards. Automatically.
"""

import argparse
import os
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich import box
from rich.prompt import Prompt, IntPrompt, Confirm

try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env file immediately
except ImportError:
    pass


# ─── Constants ────────────────────────────────────────────────────────────────

IGNORE_DIRS = {
    "venv", "env", ".venv", ".git", "__pycache__",
    "node_modules", ".tox", ".eggs", "build", "dist",
    ".mypy_cache", ".pytest_cache", ".ruff_cache",
}

def get_system_prompt(ext: str) -> str:
    """Generate a language-aware system prompt based on the file extension."""
    lang_name = ext.lstrip(".").upper() if ext else "PROJECT"
    return (
        f"You are a Staff-Level Principal Engineer performing a rigorous codebase analysis of {lang_name} files. "
        "Your objective is to extract, synthesize, and enforce the definitive coding standards "
        f"observed in the provided {ext} source files.\n\n"
        "Produce a highly polished, professional Markdown document containing the following sections. "
        "For EVERY rule you define, you MUST provide a concise code snippet demonstrating the "
        "'Do' and 'Don't' approaches.\n\n"
        "### Required Sections:\n"
        "1. **Core Naming Conventions** — Deep dive into variables, functions, classes, and constants.\n"
        "2. **Documentation & Comments** — Required comment blocks, docstring/documentation formats, and acceptable inline comment usage.\n"
        "3. **Code Organization & Imports** — Structuring files, module ordering, and usage of imports or includes.\n"
        "4. **Error Handling & Resilience** — Standard exception/error patterns, validation, and defensive coding styles.\n"
        "5. **Architectural & Design Patterns** — High-level structural choices observed in the code.\n"
        "6. **Strict Anti-Patterns** — Call out 2-3 specific bad habits to aggressively avoid.\n\n"
        "**Formatting Rules:**\n"
        "- Use bold headings and clean sub-lists.\n"
        "- Ensure code blocks have massive contrast and are perfectly syntactically correct.\n"
        "- Keep the tone authoritative, clear, and pragmatic.\n"
        "- Do NOT add generic introductory or concluding text (e.g., 'Here are the standards'). Start directly with the title."
    )

OUTPUT_FILENAME = "ai-coding-standards.md"

console = Console()

# ─── Banner ───────────────────────────────────────────────────────────────────

BANNER = r"""
 ██╗   ██╗██╗██████╗ ███████╗     ██████╗██╗  ██╗███████╗ ██████╗██╗  ██╗
 ██║   ██║██║██╔══██╗██╔════╝    ██╔════╝██║  ██║██╔════╝██╔════╝██║ ██╔╝
 ██║   ██║██║██████╔╝█████╗      ██║     ███████║█████╗  ██║     █████╔╝
 ╚██╗ ██╔╝██║██╔══██╗██╔══╝      ██║     ██╔══██║██╔══╝  ██║     ██╔═██╗
  ╚████╔╝ ██║██████╔╝███████╗    ╚██████╗██║  ██║███████╗╚██████╗██║  ██╗
   ╚═══╝  ╚═╝╚═════╝ ╚══════╝     ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝
"""


def print_banner():
    """Display the stylized application banner."""
    console.print(Text(BANNER, style="bold cyan"))
    console.print(
        Panel(
            "[bold white]Scan your codebase. Extract your coding standards. Automatically.[/bold white]",
            border_style="cyan",
            box=box.DOUBLE_EDGE,
            padding=(0, 2),
        )
    )
    console.print()


# ─── Step 1: CLI Setup ───────────────────────────────────────────────────────

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="vibe-check",
        description="🎯 Scan a codebase and generate AI-powered coding standards.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Path to the project directory to scan (leave blank for interactive wizard).",
    )
    parser.add_argument(
        "--ext",
        type=str,
        default=".py",
        help="File extension to scan for (default: .py).",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Groq API key. Falls back to GROQ_API_KEY env var.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=3,
        help="Number of largest files to analyze (default: 3).",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default=None,
        help="Directory to save the output file (default: scanned directory).",
    )
    parser.add_argument(
        "--out-file",
        type=str,
        default=None,
        help="Name of the output file (default: <extension>.md).",
    )
    return parser.parse_args(argv)


# ─── Step 2: File Discovery & Filtering ──────────────────────────────────────

def discover_files(scan_path: str, ext: str, top_n: int = 3) -> list[Path]:
    """
    Walk the directory tree and return the top N largest files
    matching the given extension, ignoring common non-project dirs.
    """
    root = Path(scan_path).resolve()
    if not root.is_dir():
        console.print(f"[bold red]✗[/bold red] Path does not exist or is not a directory: {root}")
        sys.exit(1)

    pattern = f"*{ext}" if ext.startswith(".") else f"*.{ext}"
    matches: list[Path] = []

    for filepath in root.rglob(pattern):
        # Skip files inside ignored directories
        if any(part in IGNORE_DIRS for part in filepath.relative_to(root).parts):
            continue
        if filepath.is_file():
            matches.append(filepath)

    # Sort by file size descending, take top N
    matches.sort(key=lambda f: f.stat().st_size, reverse=True)
    return matches[:top_n]


# ─── Step 3: Content Aggregation ─────────────────────────────────────────────

def aggregate_content(files: list[Path], root: Path) -> str:
    """Read selected files and concatenate into a single prompt string."""
    parts = ["Here are the sample files from the codebase:\n"]

    for filepath in files:
        relative = filepath.relative_to(root)
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            content = f"[Could not read file: {exc}]"
        parts.append(f"\n{'='*60}")
        parts.append(f"FILE: {relative}")
        parts.append(f"SIZE: {filepath.stat().st_size:,} bytes")
        parts.append(f"{'='*60}\n")
        parts.append(content)

    return "\n".join(parts)


# ─── Step 4: LLM Call ────────────────────────────────────────────────────────

def call_llm(content: str, ext: str, api_key: str | None = None) -> str:
    """Send aggregated content to Groq (Llama 3.3 70B) and return the analysis."""
    if Groq is None:
        console.print("[bold red]✗[/bold red] groq package not installed. Run: pip install groq")
        sys.exit(1)

    key = api_key or os.environ.get("GROQ_API_KEY")
    if not key:
        console.print(
            "[bold red]✗[/bold red] No API key found. "
            "Pass [cyan]--api-key[/cyan] or set [cyan]GROQ_API_KEY[/cyan] env var."
        )
        sys.exit(1)

    client = Groq(api_key=key)

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": get_system_prompt(ext)},
                {"role": "user", "content": content},
            ],
            temperature=0.3,
            max_tokens=4096,
        )
        return response.choices[0].message.content
    except Exception as exc:
        console.print(f"[bold red]✗[/bold red] LLM API error: {exc}")
        sys.exit(1)


# ─── Step 5: File Output ─────────────────────────────────────────────────────

def write_output(out_dir: str, out_file: str, markdown: str) -> Path:
    """Write the generated standards to the output file."""
    out_path = Path(out_dir).resolve() / out_file
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")
    return out_path



# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    """Entry point — orchestrates the full pipeline with rich CLI output."""
    print_banner()

    args = parse_args()

    # Interactive Wizard if no path provided
    if args.path is None:
        console.print("[dim]✨ No --path provided. Let's set it up![/dim]")
        args.path = Prompt.ask("📂 [bold cyan]Directory to scan[/bold cyan]", default=".")
        args.ext = Prompt.ask("📄 [bold cyan]File extension to look for[/bold cyan]", default=".py")
        if not args.ext.startswith("."):
            args.ext = f".{args.ext}"
        args.top = IntPrompt.ask("🔢 [bold cyan]Max files to analyze[/bold cyan]", default=3)
        args.out_dir = Prompt.ask("📁 [bold cyan]Output directory[/bold cyan]", default=args.path)
        
        ext_clean = args.ext.lstrip(".") if args.ext.startswith(".") else args.ext
        default_out = f"{ext_clean}.md" if ext_clean else "ai-coding-standards.md"
        args.out_file = Prompt.ask("📝 [bold cyan]Output file name[/bold cyan]", default=default_out)
        
        console.print("\n[bold]Configuration Summary:[/bold]")
        console.print(f"  • [cyan]Target Path:[/cyan] {args.path}")
        console.print(f"  • [cyan]Extension:[/cyan]   {args.ext}")
        console.print(f"  • [cyan]Max Files:[/cyan]   {args.top}")
        console.print(f"  • [cyan]Output Dir:[/cyan]  {args.out_dir}")
        console.print(f"  • [cyan]Output File:[/cyan] {args.out_file}")
        console.print()
        
        if not Confirm.ask("🚀 [bold green]Proceed with these settings?[/bold green]", default=True):
            console.print("[dim]Aborted by user.[/dim]")
            sys.exit(0)
            
        console.print()

    # Strip quotes from paths to support drag-and-drop quoted paths on Windows
    args.path = args.path.strip("\"'")
    if args.out_dir is not None:
        args.out_dir = args.out_dir.strip("\"'")
    
    # Ensure extension starts with a dot for consistent logging
    if not args.ext.startswith("."):
        args.ext = f".{args.ext}"

    # Defaults for optional flags
    if args.out_dir is None:
        args.out_dir = args.path

    if args.out_file is None:
        ext_clean = args.ext.lstrip(".")
        args.out_file = f"{ext_clean}.md" if ext_clean else "ai-coding-standards.md"

    root = Path(args.path).resolve()

    # ── Step 1: Discovery ────────────────────────────────────────────────
    console.print(f"[bold cyan]▸ STEP 1[/bold cyan]  Scanning [yellow]{root}[/yellow] for [green]{args.ext}[/green] files…\n")

    with Progress(
        SpinnerColumn(style="cyan"),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        progress.add_task("Discovering files…", total=None)
        files = discover_files(args.path, args.ext, args.top)

    if not files:
        console.print(f"[bold red]✗[/bold red] No [green]{args.ext}[/green] files found in {root}")
        sys.exit(1)

    # Show results table
    table = Table(
        title="📂 Files Selected for Analysis",
        box=box.ROUNDED,
        border_style="cyan",
        title_style="bold white",
        show_lines=True,
    )
    table.add_column("#", style="dim", width=3, justify="right")
    table.add_column("File", style="green")
    table.add_column("Size", style="yellow", justify="right")

    total_bytes = 0
    for i, f in enumerate(files, 1):
        size = f.stat().st_size
        total_bytes += size
        table.add_row(str(i), str(f.relative_to(root)), f"{size:,} B")

    console.print(table)
    console.print(f"  [dim]Total: {total_bytes:,} bytes across {len(files)} file(s)[/dim]\n")

    # ── Step 2: Aggregation ──────────────────────────────────────────────
    console.print("[bold cyan]▸ STEP 2[/bold cyan]  Aggregating file contents…\n")
    content = aggregate_content(files, root)
    console.print(f"  [dim]Assembled {len(content):,} characters for analysis[/dim]\n")

    # ── Step 3: LLM Analysis ─────────────────────────────────────────────
    console.print("[bold cyan]▸ STEP 3[/bold cyan]  Sending to LLM for analysis…\n")

    with Progress(
        SpinnerColumn(style="cyan"),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        progress.add_task("Waiting for AI response…", total=None)
        result = call_llm(content, args.ext, args.api_key)

    console.print("  [bold green]✓[/bold green] Analysis complete\n")

    # ── Step 4: Output ───────────────────────────────────────────────────
    console.print("[bold cyan]▸ STEP 4[/bold cyan]  Writing coding standards…\n")
    out_path = write_output(args.out_dir, args.out_file, result)

    # ── Done ─────────────────────────────────────────────────────────────
    console.print(
        Panel(
            f"[bold green]✓ Success![/bold green]\n\n"
            f"Coding standards written to:\n"
            f"[bold white]{out_path}[/bold white]\n\n"
            f"[dim]{len(result):,} characters · {len(result.splitlines())} lines[/dim]",
            title="🎯 vibe-check complete",
            border_style="green",
            box=box.DOUBLE_EDGE,
            padding=(1, 3),
        )
    )


if __name__ == "__main__":
    main()
