# Technical challenge

Planned items (see CLAUDE.md): structured LLM output with per-user limits, CI/CD, and
live updates with htmx. Each section is filled in when the item ships.

## 1. CI/CD (Sprint 1, production added in Sprint 2)

- **What:** GitHub Actions runs ruff, a migrations check, the test suite on Postgres 16,
  and a double seed on every PR and push to `main`. Render staging auto-deploys from
  `main`; production (`autoDeploy: false`) is promoted by a manual deploy.
- **Environments:**

  | | URL | Database (Neon) | Deploys |
  |---|---|---|---|
  | Staging | https://travel-planner-staging-9e6n.onrender.com | `Staging` branch | Automatically on every merge to `main` |
  | Production | https://travel-planner-production-1ad2.onrender.com | `production` branch | Only when a team member clicks **Manual Deploy** on Render |

  Each service has its own `DATABASE_URL` and `SECRET_KEY`, set only in Render's
  Environment tab (never committed). Both use the health check `/healthz`.
- **Files:** `.github/workflows/ci.yml`, `render.yaml`, `build.sh`
- **PRs:** [#1](https://github.com/natashapirani5/MGT656Project-nervous-newt/pull/1)
  (workflow, Render blueprint);
  [passing CI run on PR #1](https://github.com/natashapirani5/MGT656Project-nervous-newt/actions/runs/43359647484)
- **Release steps:**
  1. Open a PR. The `test` check (CI) must pass before it can merge.
  2. Merge to `main`. Render deploys staging automatically.
  3. Check the change on staging.
  4. On Render, open `travel-planner-production` and click
     **Manual Deploy → Deploy latest commit**.
  5. Check production: `/healthz` returns `{"status": "ok"}`, both grader accounts can log
     in, and `/1ead64a` and `/1ead64a/stats` load.
- **Migrations and seed:** the start command runs `migrate` and `seed` before gunicorn on
  every deploy (Render's free plan has no pre-deploy step), so both environments are always
  migrated and seeded.
- **See it working:** the "CI" check on any pull request
  ([Actions tab](https://github.com/natashapirani5/MGT656Project-nervous-newt/actions));
  after a merge to `main`, Render's Events tab shows a new staging deploy and no new
  production deploy.
- **Branch protection:** `main` is protected (enabled Nov 13), so changes go through pull
  requests, and the `test` check is a required status check (enabled Nov 18), so a PR with
  failing tests or lint can't merge.

## 2. Structured LLM output + per-user AI limit (planned)

## 3. Live updates with htmx (planned)

## Testing strategy

- Django `TestCase` tests per app: views (incl. permissions), forms, management commands.
- A/B page: every case required by the spec (`abtest/tests/test_abtest.py`).
- External services (OpenRouter) will be mocked; tests run with no network and no keys.
- Not yet tested: browser-level behavior (no Playwright yet).
