"""
SkillSync — Main Controller
States: IDLE → PARSING → ANALYZING → IDLE

Usage:
    python src/main.py <path/to/resume.pdf>
    python src/main.py <path/to/resume.pdf> <path/to/jd.txt>
"""

import sys
from enum import Enum, auto

from engine.parser   import Resume, ParserError
from engine.analyzer import ScoringEngine, AnalyzerError


class State(Enum):
    IDLE      = auto()
    PARSING   = auto()
    ANALYZING = auto()


DIVIDER      = "─" * 60
DIVIDER_BOLD = "═" * 60


def _banner():
    print(DIVIDER_BOLD)
    print("  SkillSync · Resume Optimizer  //  v0.2.0-dev")
    print(DIVIDER_BOLD)

def _section(title):
    print(f"\n{DIVIDER}\n  {title}\n{DIVIDER}")

def _err(msg):
    print(f"\n  [ERROR] {msg}", file=sys.stderr)

def _info(msg):
    print(f"  {msg}")

def _get_job_description(jd_path: str = None) -> str:
    """Load JD from a .txt file or prompt user to paste interactively."""
    if jd_path:
        if not jd_path.lower().endswith(".txt"):
            raise ValueError(f"'{jd_path}' is not a .txt file.")
        try:
            with open(jd_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            raise ValueError(f"JD file not found: '{jd_path}'")

    # Interactive fallback
    print("\n  Paste the job description below.")
    print("  Press Enter twice when done.\n")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if lines and line == "":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def _print_results(result: dict):
    """Render the scoring breakdown in the terminal."""
    score = result["score"]

    # Score bar
    filled = int(score / 5)
    bar    = "█" * filled + "░" * (20 - filled)

    _section(f"MATCH SCORE: {score}%  [{bar}]")

    if result["strong"]:
        _info(f"STRONG MATCHES   : {', '.join(result['strong'][:10])}")
    else:
        _info("STRONG MATCHES   : none")

    if result["partial"]:
        _info(f"PARTIAL MATCHES  : {', '.join(result['partial'][:10])}")
    else:
        _info("PARTIAL MATCHES  : none")

    if result["missing"]:
        _info(f"MISSING SKILLS   : {', '.join(result['missing'][:10])}")
    else:
        _info("MISSING SKILLS   : none")

    _info(f"\n  RECOMMENDATION   : {result['recommendation']}")


def run(argv):
    _banner()

    # ── IDLE ──────────────────────────────────────────────────────────
    state = State.IDLE
    _section("STATE: IDLE — awaiting input")

    if len(argv) < 2:
        _err("No file path supplied.")
        _info("Usage: python src/main.py <path/to/resume.pdf>")
        return

    file_path = argv[1]

    if not file_path.lower().endswith(".pdf"):
        _err(f"'{file_path}' is not a PDF (expected .pdf extension).")
        _info("Returning to IDLE.")
        return

    # ── PARSING ───────────────────────────────────────────────────────
    state = State.PARSING
    _section(f"STATE: PARSING — '{file_path}'")

    try:
        resume = Resume(file_path).extract()
    except ParserError as exc:
        _err(str(exc))
        state = State.IDLE
        _section("STATE: IDLE — parse failed, system reset")
        return

    _info(f"Extracted {resume.page_count} page(s) — {len(resume.raw_text):,} characters")

    # ── ANALYZING ─────────────────────────────────────────────────────
    state = State.ANALYZING
    jd_path = argv[2] if len(argv) > 2 else None

    if jd_path:
        _section(f"STATE: ANALYZING — loading JD from '{jd_path}'")
    else:
        _section("STATE: ANALYZING — paste your job description")

    try:
        job_text = _get_job_description(jd_path)
    except ValueError as exc:
        _err(str(exc))
        state = State.IDLE
        _section("STATE: IDLE — analysis cancelled, system reset")
        return

    if not job_text:
        _err("No job description provided.")
        state = State.IDLE
        _section("STATE: IDLE — analysis cancelled, system reset")
        return

    _info("Running NLP analysis …")

    try:
        engine = ScoringEngine()
        result = engine.score(resume.raw_text, job_text)
    except AnalyzerError as exc:
        _err(str(exc))
        state = State.IDLE
        _section("STATE: IDLE — analysis failed, system reset")
        return

    # ── RESULTS ───────────────────────────────────────────────────────
    _print_results(result)

    # ── IDLE ──────────────────────────────────────────────────────────
    state = State.IDLE
    _section("STATE: IDLE — ready for next operation")


if __name__ == "__main__":
    run(sys.argv)