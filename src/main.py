"""
SkillSync — Main Controller
States: IDLE → PARSING → IDLE

Usage:
    python src/main.py <path/to/resume.pdf>
"""

import sys
from enum import Enum, auto
from engine.parser import Resume, ParserError


class State(Enum):
    IDLE    = auto()
    PARSING = auto()


DIVIDER      = "─" * 60
DIVIDER_BOLD = "═" * 60


def _banner():
    print(DIVIDER_BOLD)
    print("  SkillSync · Resume Optimizer  //  v0.1.0-dev")
    print(DIVIDER_BOLD)

def _section(title):
    print(f"\n{DIVIDER}\n  {title}\n{DIVIDER}")

def _err(msg):
    print(f"\n  [ERROR] {msg}", file=sys.stderr)

def _info(msg):
    print(f"  {msg}")


def run(argv):
    _banner()
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

    state = State.PARSING
    _section(f"STATE: PARSING — '{file_path}'")

    try:
        resume = Resume(file_path).extract()
    except ParserError as exc:
        _err(str(exc))
        state = State.IDLE
        _section("STATE: IDLE — parse failed, system reset")
        return

    _section(f"PARSE COMPLETE — {resume.page_count} page(s)")
    _info(f"Source : {resume.file_path}")
    _info(f"Length : {len(resume.raw_text):,} characters")
    _section("RAW TEXT OUTPUT")
    print(resume.raw_text)

    state = State.IDLE
    _section("STATE: IDLE — ready for next operation")


if __name__ == "__main__":
    run(sys.argv)