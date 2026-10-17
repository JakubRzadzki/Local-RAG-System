## What and why

<!-- What does this change, and why? Link the issue if there is one. -->

## How it was tested

<!-- Commands you ran, or what you checked in the UI. -->

## Checklist

- [ ] The PR title is a [Conventional Commit](https://www.conventionalcommits.org/) (`feat: ...`, `fix(scope): ...`)
- [ ] Commits are small and atomic, with no `Co-Authored-By` trailers
- [ ] `uv run ruff check . && uv run ruff format --check . && uv run mypy src scripts && uv run pytest` passes
- [ ] `cd frontend && npm run typecheck` passes (if the frontend changed)
- [ ] README updated if behaviour, configuration or the API changed
