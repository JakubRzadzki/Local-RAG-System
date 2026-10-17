import subprocess
from pathlib import Path

import pytest
from check_commits import check_message, check_subject, commits_in_range, main


@pytest.mark.parametrize(
    "subject",
    [
        "feat: add web search",
        "fix(services): handle CRLF",
        "refactor(api)!: drop the v1 endpoints",
        "docs: update README",
        "ci: run lint, types and tests",
        "feat(frontend,api): add the Web toggle",
        'Revert "feat: add web search"',
        "Merge branch 'main' into feature",
    ],
)
def test_valid_subjects_pass(subject: str) -> None:
    assert check_subject(subject) == []


@pytest.mark.parametrize(
    "subject",
    [
        "added web search",
        "Feat: capitalised type",
        "feat:missing space",
        "feat: ",
        "feature: wrong type",
        "fix(): empty scope",
        "wip",
        "fixup! feat: add web search",
    ],
)
def test_invalid_subjects_fail(subject: str) -> None:
    assert check_subject(subject)


def test_overlong_subject_fails() -> None:
    assert any("characters" in p for p in check_subject("feat: " + "x" * 130))


def test_co_authored_by_trailer_is_rejected() -> None:
    message = "feat: add thing\n\nBody.\n\nCo-Authored-By: Someone <a@b.c>"
    assert any("Co-Authored-By" in p for p in check_message(message))


@pytest.mark.parametrize(
    "text",
    ["Generated with Claude Code", "AI-assisted refactor", "via Copilot", "🤖 bot"],
)
def test_ai_mentions_are_rejected(text: str) -> None:
    assert any("mentions" in p for p in check_message(f"feat: add thing\n\n{text}"))


def test_clean_message_with_body_passes() -> None:
    assert check_message("fix(db): add index\n\nSpeeds up the lookup by hash.") == []


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.name", "Test")
    _git(tmp_path, "config", "user.email", "test@example.com")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _commit(repo: Path, name: str, message: str) -> None:
    (repo / name).write_text(name)
    _git(repo, "add", name)
    _git(repo, "commit", "-q", "-m", message)


def test_range_check_reports_only_bad_commits(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _commit(repo, "a", "chore: initial")
    _commit(repo, "b", "feat: good one")
    _commit(repo, "c", "did stuff")

    assert main(["--range", "HEAD~2..HEAD"]) == 1

    err = capsys.readouterr().err
    assert "did stuff" in err
    assert "good one" not in err


def test_range_check_passes_for_clean_history(repo: Path) -> None:
    _commit(repo, "a", "chore: initial")
    _commit(repo, "b", "fix(api): something")
    assert main(["--range", "HEAD~1..HEAD"]) == 0


def test_unresolvable_range_falls_back_to_head(repo: Path) -> None:
    _commit(repo, "a", "chore: initial")
    commits = commits_in_range("0000000000000000000000000000000000000000..HEAD")
    assert [c.subject for c in commits] == ["chore: initial"]


def test_title_check(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--title", "feat: add web search"]) == 0
    assert main(["--title", "Update stuff"]) == 1
    assert "PR title" in capsys.readouterr().err


@pytest.mark.parametrize(
    "subject",
    ["style(frontend): add dark ChatGPT-style theme", "feat(api): OpenAI-compatible endpoint"],
)
def test_descriptive_product_names_are_allowed(subject: str) -> None:
    assert check_message(subject) == []
