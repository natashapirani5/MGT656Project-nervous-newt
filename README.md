# Travel Planner (MGT 656, team ancient-water)

Collaborative trip planning: groups coordinate availability and preferences and build
day-by-day itineraries together. Django + Postgres, deployed on Render + Neon.

The project spec for humans and AI agents is [`CLAUDE.md`](CLAUDE.md).

## Run locally

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.example .env   # optional; without DATABASE_URL, local dev uses SQLite
uv run python manage.py migrate
uv run python manage.py seed
DJANGO_DEBUG=1 uv run python manage.py runserver
```

## Test and lint

```bash
uv run python manage.py test
uv run ruff check . && uv run ruff format --check .
```

## Useful commands

- `manage.py seed`: idempotent demo data + grader accounts (see `accounts/management/commands/seed.py`)
- `manage.py abtest_reset --yes`: wipe all A/B rows (run on production before the bot run)

## Key URLs

- `/1ead64a` A/B page, `/1ead64a/stats` JSON stats
- `/healthz` health check
- `/trips/` dashboard, `/profile/` travel profile

After changing dependencies, regenerate Render's requirements file:
`uv export --no-dev --no-hashes --format requirements-txt -o requirements.txt`
