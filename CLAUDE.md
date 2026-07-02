# Claude Code instructions

Repo-specific guidance for AI assistants (Claude Code, Cursor, etc.). Humans, skim this too.

## Project shape

- Python package `playerdatapy` — typed client for the PlayerData GraphQL API.
- Generated from `schema.graphql` by `ariadne-codegen` (config in `pyproject.toml` under `[tool.ariadne-codegen]`). `schema.graphql` is refreshed from the public SDL at `https://app.playerdata.co.uk/api/schema.graphql`.
- Custom codegen plugin at `codegen_plugins/docstrings.py` injects schema descriptions into generated enums.
- Docs site at `docs/`, built with MkDocs Material + mkdocstrings, deployed to GitHub Pages via `.github/workflows/docs.yml`.
- Examples in `examples/direct/` (raw GraphQL) and `examples/pydantic/` (typed `PlayerDataAPI` — preferred).

## Generated files — DO NOT hand-edit

These are output of `uv run ariadne-codegen` and excluded from ruff:

- `playerdatapy/custom_queries.py`
- `playerdatapy/custom_mutations.py`
- `playerdatapy/custom_fields.py`
- `playerdatapy/custom_typing_fields.py`
- `playerdatapy/input_types.py`
- `playerdatapy/enums.py`
- `playerdatapy/gqlclient.py`
- `playerdatapy/base_model.py`
- `playerdatapy/base_operation.py`
- `playerdatapy/async_base_client.py`

Any edits will be wiped on next codegen run. To change them, edit `schema.graphql` (or update upstream schema in the `PlayerData/api` repo) or the codegen plugin.

## Updating docs

Three paths, all converge on `docs.yml` workflow rebuild on merge to `main`.

### 1. Narrative pages (`docs/*.md`)
Edit Markdown, open PR. Pages: `index`, `quickstart`, `auth`, `concepts`, `metrics`, `limits`, `errors`, `examples`, `faq`, `api`.

### 2. API reference (`docs/api.md`)
**Auto-rendered.** Uses mkdocstrings `:::` directives → griffe introspects Python source. To improve coverage:

- Add/edit docstrings in `playerdatapy/*` hand-written modules (`gqlauth.py`, `playerdata_api.py`, `auth/*.py`).
- Generated modules carry docstrings via ariadne-codegen + the enum plugin — don't edit by hand.

### 3. SDK regeneration
`schema.graphql` is committed. Nightly CI (`.github/workflows/codegen.yml`, 06:00 UTC) refreshes it from the public SDL at `https://app.playerdata.co.uk/api/schema.graphql` and reruns codegen — PR opens only if anything drifts.

Local:
```bash
curl -fsSL https://app.playerdata.co.uk/api/schema.graphql -o schema.graphql
uv sync --group codegen
uv run ariadne-codegen
git add schema.graphql playerdatapy/
```
Also triggered by `workflow_dispatch` or pushing `schema.graphql` to `main`.

## Local commands

```bash
uv sync                       # base install
uv sync --group docs          # + mkdocs stack
uv sync --group codegen       # + ariadne-codegen
uv sync --group test          # + pytest + ruff

uv run mkdocs serve           # preview docs at http://127.0.0.1:8000
uv run mkdocs build --strict  # build site/ (fail on any warning)

uv run ruff check             # lint
uv run pytest                 # tests
```

## Conventions

- Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `ci:`, `refactor:`).
- Never include AI attribution in commit messages.
- Don't ignore lint errors — fix or extract.
- Public API only in docs/examples — no `_private` access. `mkdocstrings` filters `^_` out anyway (`mkdocs.yml`).
- Support email: `support@playerdata.com` (not `.co.uk`).
- OAuth endpoints: no `/api` prefix on `/oauth/authorize` and `/oauth/token` (only `/api/graphql` carries `/api`).
- Authentication flows live in `playerdatapy.gqlauth.AuthenticationType`.

## When making changes

1. **Touching `schema.graphql`** → run `uv run ariadne-codegen`; commit schema + regenerated files together. Nightly CI does this automatically via `codegen.yml`.
2. **Touching public Python API** → check `docs/api.md` still renders sensibly via `mkdocs build --strict`.
3. **Touching docs theme** (`docs/stylesheets/extra.css`, `mkdocs.yml`) → preview with `mkdocs serve` before pushing.
4. **Touching workflows** → verify with `act` locally or watch the run after push.

## Hosting

GitHub Pages, source = `gh-pages` branch, deployed via `mkdocs gh-deploy` in `.github/workflows/docs.yml`. URL: <https://playerdata.github.io/playerdatapy/>.
