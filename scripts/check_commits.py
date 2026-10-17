"""Validate commit messages and pull request titles.

Rules:
- Conventional Commits: ``type(scope)!: description``.
- Subject line at most 120 characters.
- No ``Co-Authored-By`` trailers and no mentions of AI assistants or generated content.
- No ``fixup!`` / ``squash!`` commits (clean them up before merging).

Usage:
    python scripts/check_commits.py --range BASE..HEAD
    python scripts/check_commits.py --title "feat: add something"

The script uses only the standard library, so CI can run it without installing anything.
"""

import argparse
import re
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass

TYPES = "feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert"
CONVENTIONAL = re.compile(rf"^({TYPES})(\([a-z0-9][\w\-./, ]*\))?!?: \S.*$")
AUTO_GENERATED = re.compile(r'^(Merge |Revert ")')
SUBJECT_MAX_LENGTH = 120

CO_AUTHOR = re.compile(r"^\s*co-authored-by:", re.IGNORECASE | re.MULTILINE)
# Attribution to an AI assistant. Product names used descriptively ("ChatGPT-style UI",
# "OpenAI-compatible API") are fine, so only assistant names and attribution phrases match.
AI_MENTION = re.compile(
    r"(\b(claude|anthropic|copilot|generated (?:with|by)|ai[- ]assisted)\b|🤖)",
    re.IGNORECASE,
)
FIXUP = re.compile(r"^(fixup|squash)!")

RECORD_SEPARATOR = "\x1e"
FIELD_SEPARATOR = "\x1f"


@dataclass(frozen=True)
class Commit:
    sha: str
    message: str

    @property
    def subject(self) -> str:
        return self.message.splitlines()[0] if self.message.strip() else ""


def check_subject(subject: str) -> list[str]:
    """Problems with a commit subject or pull request title."""
    if AUTO_GENERATED.match(subject):
        return []
    problems: list[str] = []
    if FIXUP.match(subject):
        problems.append("fixup!/squash! commits must be cleaned up before merging")
    elif not CONVENTIONAL.match(subject):
        problems.append(
            f"subject is not a Conventional Commit (expected '<{TYPES}>(scope)?: description')"
        )
    if len(subject) > SUBJECT_MAX_LENGTH:
        problems.append(f"subject is {len(subject)} characters (max {SUBJECT_MAX_LENGTH})")
    return problems


def check_message(message: str) -> list[str]:
    """Problems with a full commit message (subject, body and trailers)."""
    problems = check_subject(message.splitlines()[0] if message.strip() else "")
    if CO_AUTHOR.search(message):
        problems.append("Co-Authored-By trailers are not allowed")
    match = AI_MENTION.search(message)
    if match:
        problems.append(f"mentions '{match.group(0)}' (no AI attribution in commit messages)")
    return problems


def commits_in_range(revision_range: str) -> list[Commit]:
    """Commits in ``revision_range``; falls back to HEAD if the range cannot be resolved."""
    log_format = f"%H{FIELD_SEPARATOR}%B{RECORD_SEPARATOR}"

    def run(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "log", f"--format={log_format}", *args],
            capture_output=True,
            text=True,
            check=False,
        )

    result = run(revision_range)
    if result.returncode != 0:
        # e.g. a force-push whose previous tip no longer exists: check the new tip only.
        print(f"warning: cannot resolve '{revision_range}', checking HEAD only", file=sys.stderr)
        result = run("-1", "HEAD")
        if result.returncode != 0:
            raise SystemExit(result.stderr.strip() or "git log failed")
    commits = []
    for record in result.stdout.split(RECORD_SEPARATOR):
        if record.strip():
            sha, _, message = record.strip().partition(FIELD_SEPARATOR)
            commits.append(Commit(sha=sha, message=message.strip()))
    return commits


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--range", dest="revision_range", help="git revision range, BASE..HEAD")
    parser.add_argument("--title", help="pull request title to validate")
    args = parser.parse_args(argv)
    if not args.revision_range and args.title is None:
        parser.error("give --range and/or --title")

    failures: list[str] = []
    if args.title is not None:
        failures += [f"PR title {args.title!r}: {p}" for p in check_subject(args.title)]
    if args.revision_range:
        for commit in commits_in_range(args.revision_range):
            failures += [
                f"{commit.sha[:8]} {commit.subject!r}: {p}" for p in check_message(commit.message)
            ]

    if failures:
        print("Commit checks failed:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    print("Commit checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
