"""
Neutral Minds — Medical Triage Expert System
Python Interface Layer (CLI + pyswip integration)

This module is the INTERFACE ONLY. All medical reasoning and triage logic
is implemented in the Prolog knowledge base (knowledge_base/expert_system.pl).

Python responsibilities:
  1. Collect user input (symptom selection)
  2. Assert/retract symptom facts into the Prolog engine via pyswip
  3. Query Prolog for triage results
  4. Display results to the user
"""

import os
import sys
from pathlib import Path

try:
    from pyswip import Prolog
except ImportError:
    print("ERROR: pyswip is not installed.")
    print("Install it with:  pip install pyswip")
    print("Also ensure SWI-Prolog is installed and on your system PATH.")
    sys.exit(1)


def safe_input(prompt: str = "") -> str:
    """Read a line from the user, bypassing SWI-Prolog stdin interference.

    On Windows, uses msvcrt to read directly from the console via the
    Win32 Console API, which is completely independent of C stdin.
    On Unix, opens /dev/tty as a fallback.
    """
    sys.stdout.write(prompt)
    sys.stdout.flush()
    if sys.platform == "win32":
        import msvcrt
        chars: list[str] = []
        while True:
            ch = msvcrt.getwche()          # read + echo one char
            if ch in ("\r", "\n"):
                sys.stdout.write("\n")
                break
            elif ch == "\x08":             # Backspace
                if chars:
                    chars.pop()
                    sys.stdout.write(" \x08")
            elif ch == "\x03":             # Ctrl+C
                raise KeyboardInterrupt
            elif ch == "\x1a":             # Ctrl+Z  (EOF on Windows)
                raise EOFError
            else:
                chars.append(ch)
        return "".join(chars)
    else:
        with open("/dev/tty", "r") as tty:
            line = tty.readline()
            if not line:
                raise EOFError
            return line.rstrip("\n").rstrip("\r")


# Path to the Prolog knowledge base (relative to this file's directory)
KB_PATH = Path(__file__).resolve().parent.parent / "knowledge_base" / "expert_system.pl"

DISCLAIMER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⚠  DISCLAIMER                                                            ║
║                                                                            ║
║  Neutral Minds is a DEMONSTRATION rule-based triage system.                ║
║  It is NOT a medical diagnostic tool.                                      ║
║  It does NOT replace professional medical advice, diagnosis, or treatment. ║
║                                                                            ║
║  If you are experiencing a medical emergency, call your local emergency    ║
║  services immediately.                                                     ║
║                                                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ANSI colour codes for terminal output
URGENCY_COLORS = {
    "critical": "\033[91m",
    "urgent":   "\033[93m",
    "moderate": "\033[96m",
    "low":      "\033[92m",
    "none":     "\033[90m",
}
RESET_COLOR = "\033[0m"
BOLD = "\033[1m"


# ---------------------------------------------------------------------------
# Prolog Engine Wrapper
# ---------------------------------------------------------------------------

class TriageEngine:
    """
    Thin wrapper around pyswip that manages Prolog communication.

    All triage reasoning happens inside the Prolog knowledge base.
    This class only:
      - loads the KB
      - asserts / retracts symptom facts
      - queries Prolog for results
    """

    def __init__(self, kb_path: str | Path = KB_PATH):
        self.prolog = Prolog()
        kb_posix = str(Path(kb_path).resolve()).replace("\\", "/")
        if not Path(kb_path).exists():
            raise FileNotFoundError(f"Knowledge base not found: {kb_path}")
        self.prolog.consult(kb_posix)
        # Prevent SWI-Prolog from grabbing terminal control
        list(self.prolog.query("set_prolog_flag(tty_control, false)"))
        # Start with a clean symptom state
        list(self.prolog.query("clear_symptoms"))

    # --- Symptom management (delegates to Prolog predicates) ---

    def add_symptom(self, symptom: str) -> None:
        """Assert a symptom fact in Prolog."""
        list(self.prolog.query(f"add_symptom({symptom})"))

    def remove_symptom(self, symptom: str) -> None:
        """Retract a symptom fact from Prolog."""
        list(self.prolog.query(f"remove_symptom({symptom})"))

    def clear_symptoms(self) -> None:
        """Remove all asserted symptom facts."""
        list(self.prolog.query("clear_symptoms"))

    def get_current_symptoms(self) -> list[str]:
        """Query Prolog for the list of currently asserted symptoms."""
        results = list(self.prolog.query("current_symptoms(S)"))
        if results:
            return [str(s) for s in results[0]["S"]]
        return []

    def get_available_symptoms(self) -> list[tuple[str, str]]:
        """Query Prolog for all recognized symptom IDs and descriptions."""
        results = list(self.prolog.query("available_symptom(Id, Desc)"))
        return [(str(r["Id"]), str(r["Desc"])) for r in results]

    # --- Triage queries (all reasoning happens in Prolog) ---

    def run_triage(self) -> tuple[str, list[str]]:
        """
        Query Prolog's triage/2 predicate.
        Returns (urgency_level, [explanation_strings]).
        """
        results = list(self.prolog.query("triage(Level, Explanations)"))
        if results:
            level = str(results[0]["Level"])
            explanations = [str(e) for e in results[0]["Explanations"]]
            return level, explanations
        return "none", ["Unable to determine triage level."]

    def run_triage_all(self) -> list[tuple[str, list[str]]]:
        """
        Query Prolog for ALL matching urgency levels (not just the highest).
        Useful for showing the full reasoning breakdown to the user.
        """
        all_levels = []
        for level in ["critical", "urgent", "moderate", "low"]:
            results = list(self.prolog.query(
                f"fired_rules({level}, Rules), Rules \\= [], "
                f"extract_explanations(Rules, Explanations)"
            ))
            if results:
                explanations = [str(e) for e in results[0]["Explanations"]]
                all_levels.append((level, explanations))
        return all_levels


# ---------------------------------------------------------------------------
# Display helpers (presentation only — no reasoning logic)
# ---------------------------------------------------------------------------

def print_banner():
    print(f"""
{BOLD}╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║               🏥  NEUTRAL MINDS  —  Medical Triage Expert System             ║
║                        Rule-Based Urgency Classification                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝{RESET_COLOR}
""")


def print_disclaimer():
    print(f"{URGENCY_COLORS['urgent']}{DISCLAIMER}{RESET_COLOR}")


def display_symptom_menu(symptoms: list[tuple[str, str]]):
    """Print the numbered list of available symptoms."""
    print(f"\n{BOLD}Available Symptoms:{RESET_COLOR}")
    print("-" * 50)
    for i, (sid, desc) in enumerate(symptoms, 1):
        print(f"  {i:>2}. {desc} ({sid})")
    print("-" * 50)
    print(f"  {BOLD} 0.  Done — Run triage{RESET_COLOR}")
    print(f"  {BOLD}-1.  Clear all symptoms{RESET_COLOR}")
    print(f"  {BOLD}-2.  Quit{RESET_COLOR}")
    print()


def display_triage_result(level: str, explanations: list[str],
                          all_levels: list[tuple[str, list[str]]] | None = None):
    """Format and display the triage result returned by Prolog."""
    color = URGENCY_COLORS.get(level, "")

    print(f"\n{'=' * 70}")
    print(f"{BOLD}{color}  TRIAGE RESULT:  {level.upper()}{RESET_COLOR}")
    print(f"{'=' * 70}")

    print(f"\n{BOLD}Triggered Rules (highest priority — {level.upper()}):{RESET_COLOR}")
    for i, exp in enumerate(explanations, 1):
        print(f"  {color}▸ Rule {i}:{RESET_COLOR} {exp}")

    if all_levels and len(all_levels) > 1:
        print(f"\n{BOLD}Other matching levels (lower priority):{RESET_COLOR}")
        for lvl, exps in all_levels:
            if lvl == level:
                continue
            lvl_color = URGENCY_COLORS.get(lvl, "")
            print(f"\n  {lvl_color}[{lvl.upper()}]{RESET_COLOR}")
            for exp in exps:
                print(f"    ▸ {exp}")

    print(f"\n{BOLD}Recommended Action:{RESET_COLOR}")
    actions = {
        "critical": "🚨 Seek IMMEDIATE emergency medical attention. Call emergency services NOW.",
        "urgent":   "⚠️  Seek medical attention as soon as possible (within hours).",
        "moderate":  "🩺 Schedule a medical appointment soon (within 24-48 hours).",
        "low":      "💊 Monitor symptoms. Visit a healthcare provider if they persist or worsen.",
        "none":     "ℹ️  No matching rules. Consider consulting a healthcare provider if concerned.",
    }
    print(f"  {color}{actions.get(level, actions['none'])}{RESET_COLOR}")
    print()


# ---------------------------------------------------------------------------
# Interactive CLI loop
# ---------------------------------------------------------------------------

def run_interactive():
    """Main interactive loop: collect symptoms, query Prolog, display results."""
    print_banner()
    print_disclaimer()

    try:
        engine = TriageEngine()
    except FileNotFoundError as e:
        print(f"\n{URGENCY_COLORS['critical']}ERROR: {e}{RESET_COLOR}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{URGENCY_COLORS['critical']}ERROR initializing Prolog engine: {e}{RESET_COLOR}")
        sys.exit(1)

    available = engine.get_available_symptoms()
    if not available:
        print("WARNING: No available symptoms loaded from knowledge base.")
        sys.exit(1)

    selected_symptoms: list[str] = []

    while True:
        if selected_symptoms:
            print(f"\n{BOLD}Currently selected symptoms:{RESET_COLOR}")
            for sym in selected_symptoms:
                desc = next((d for s, d in available if s == sym), sym)
                print(f"  ✓ {desc} ({sym})")

        display_symptom_menu(available)

        try:
            choice = safe_input(f"{BOLD}Enter symptom number(s) (comma-separated) or command: {RESET_COLOR}").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye!")
            break

        if not choice:
            continue

        entries = [c.strip() for c in choice.split(",")]
        should_run_triage = False

        for entry in entries:
            try:
                num = int(entry)
            except ValueError:
                # Allow entering symptom IDs by name
                matching = [s for s, d in available if s == entry.lower().replace(" ", "_")]
                if matching:
                    sym_id = matching[0]
                    if sym_id not in selected_symptoms:
                        engine.add_symptom(sym_id)
                        selected_symptoms.append(sym_id)
                        desc = next((d for s, d in available if s == sym_id), sym_id)
                        print(f"  ✓ Added: {desc}")
                else:
                    print(f"  ✗ Unknown input: '{entry}'")
                continue

            if num == 0:
                should_run_triage = True
                continue
            elif num == -1:
                engine.clear_symptoms()
                selected_symptoms.clear()
                print("  ✓ All symptoms cleared.")
                continue
            elif num == -2:
                print("\nGoodbye! Remember: consult a real medical professional.\n")
                return
            elif 1 <= num <= len(available):
                sym_id, desc = available[num - 1]
                if sym_id in selected_symptoms:
                    print(f"  ⓘ Already selected: {desc}")
                else:
                    engine.add_symptom(sym_id)
                    selected_symptoms.append(sym_id)
                    print(f"  ✓ Added: {desc}")
            else:
                print(f"  ✗ Invalid number: {num}")

        if should_run_triage:
            if not selected_symptoms:
                print("\n  ⚠ No symptoms selected. Please add at least one symptom.")
                continue

            # Query Prolog for the triage result
            level, explanations = engine.run_triage()

            try:
                all_levels = engine.run_triage_all()
            except Exception:
                all_levels = None

            display_triage_result(level, explanations, all_levels)
            print_disclaimer()

            try:
                again = safe_input(f"{BOLD}Run another triage? (y/n): {RESET_COLOR}").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\n\nGoodbye!")
                break

            if again in ("y", "yes"):
                engine.clear_symptoms()
                selected_symptoms.clear()
                print("\n  ✓ Symptoms cleared for new assessment.\n")
            else:
                print("\nGoodbye! Remember: consult a real medical professional.\n")
                break


# ---------------------------------------------------------------------------
# Programmatic API (used by test suite and external callers)
# ---------------------------------------------------------------------------

def run_triage_for_symptoms(symptoms: list[str]) -> dict:
    """
    Programmatic API: run triage for a given list of symptom IDs.

    Returns a dict with keys: level, explanations, all_levels, symptoms.
    All reasoning is performed by Prolog; this function only marshals data.
    """
    engine = TriageEngine()

    for symptom in symptoms:
        engine.add_symptom(symptom)

    level, explanations = engine.run_triage()

    try:
        all_levels = engine.run_triage_all()
        all_levels_dict = {lvl: exps for lvl, exps in all_levels}
    except Exception:
        all_levels_dict = {}

    return {
        "level": level,
        "explanations": explanations,
        "all_levels": all_levels_dict,
        "symptoms": symptoms,
    }


if __name__ == "__main__":
    run_interactive()
