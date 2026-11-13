# Technical challenge

Planned items (see CLAUDE.md): structured LLM output with per-user limits, CI/CD, and
live updates with htmx. Each section is filled in when the item ships.

## 1. CI/CD (in progress, Sprint 1)

- **What:** GitHub Actions runs ruff, a migrations check, the test suite on Postgres 16,
  and a double seed on every PR and push to `main`. Render staging auto-deploys from
  `main`; production (`autoDeploy: false`) is promoted by a manual deploy.
- **Files:** `.github/workflows/ci.yml`, `render.yaml`, `build.sh`
- **PRs:** [#1](https://github.com/natashapirani5/MGT656Project-nervous-newt/pull/1)
  (workflow, Render blueprint);
  [passing CI run on PR #1](https://github.com/natashapirani5/MGT656Project-nervous-newt/actions/runs/43359647484)
- **See it working:** the "CI" check on any pull request
  ([Actions tab](https://github.com/natashapirani5/MGT656Project-nervous-newt/actions));
  merging to `main` triggers a staging deploy on Render.
- **TODO:** enable branch protection on `main` so merging requires the CI check to pass
  (not enabled as of Nov 13).

## 2. Structured LLM output + per-user AI limit (planned)

## 3. Live updates with htmx (planned)

## Testing strategy

- Django `TestCase` tests per app: views (incl. permissions), forms, management commands.
- A/B page: every case required by the spec (`abtest/tests/test_abtest.py`).
- External services (OpenRouter) will be mocked; tests run with no network and no keys.
- Not yet tested: browser-level behavior (no Playwright yet).
