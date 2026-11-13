# CLAUDE.md — MGT 656 Team Project

This file is the spec for this repo. Read it at the start of every session. Rules marked **MUST** are graded; do not break them. When a request conflicts with this file, stop and tell the user instead of guessing.

## Project context

```yaml
team_nickname: ancient-water
ab_hash: 1ead64a             # A/B page is /1ead64a, stats at /1ead64a/stats
framework: django
database: postgres
hosting: Render (web service) + Neon (Postgres; separate DB/branch for staging and production)
staging_url: https://travel-planner-staging-9e6n.onrender.com
production_url: TODO
app_summary: >
  Travel Planner: a collaborative trip-planning site where groups coordinate
  availability and preferences and build day-by-day itineraries together.
ai_feature: >
  "Generate itinerary with AI": the server sends the trip (destination, dates, budget)
  plus every participant's interests, preferences, and budget to OpenRouter and gets
  back a structured day-by-day itinerary that is saved as proposed ItineraryItems.
technical_challenge_items:
  - Structured LLM output: AI returns JSON validated against a schema (Pydantic);
    valid items become ItineraryItem rows; invalid/timeout responses are retried or
    shown as a friendly error. Includes per-user daily AI generation limit.
  - CI/CD: GitHub Actions runs tests + ruff on every PR (merge blocked on failure);
    merge to main auto-deploys staging; production is a manual promote step.
  - Live updates with htmx: itinerary suggestions, edits, and RSVPs update in place
    without full page reloads.
```

## Product scope

Core features (build these):

1. **Accounts and travel profiles:** Django auth sign-up/login. Profile: name, home city, interests (e.g., scuba diving, hiking), wishlist destinations, trip preferences (e.g., splurges on food, prefers hostels).
2. **Friend directory:** search users by name/username, send and accept friend requests.
3. **Group trips:** create a trip (from a wishlist destination or new) with destination, tentative dates, description, budget. Organizer invites friends.
4. **Invitations and RSVP:** invitees see the invite and trip overview, mark availability for proposed dates, and RSVP yes / no / maybe-with-conditions (free-text condition).
5. **Collaborative itinerary:** day-by-day items (title, date, time, location, notes). Participants propose add/edit/remove; organizer approves. Organizer can generate a draft with AI.
6. **Trips dashboard:** all upcoming trips for the user in one view.

Out of scope (do not build): booking integrations, expense splitting/payments (a plain link to Splitwise/Venmo is fine), calendar integrations, photo sharing.

Roles: `organizer` (per trip) and `participant` (per trip). Enforce permissions in views and test them. Seed accounts: one organizer and one participant who share a seeded trip with an itinerary.

## Deadlines (11:59pm America/New_York)

| Date | Milestone |
|---|---|
| Wed Nov 11, 2026 | Sprint 1: walking skeleton |
| Wed Nov 18, 2026 | Sprint 2 (production URL required from here on) |
| Wed Dec 2, 2026 | Sprint 3 |
| Fri Dec 11, 2026 | Sprint 4, then the A/B bot run on production |
| Fri Dec 18, 2026 | Final submission |

Graders read what is on `main` at each deadline.

## Hard requirements (MUST)

1. **Framework:** the one in `framework` above, using its standard conventions (ORM, migrations, auth, templates, test runner).
2. **Database:** PostgreSQL or MySQL. Staging and production each use their own separate database.
3. **Auth:** the framework's standard authentication (e.g., `django.contrib.auth`, Rails `has_secure_password`/Devise, Laravel Breeze). No custom crypto.
4. **AI feature:** call the LLM through OpenRouter (`https://openrouter.ai/api/v1`) **from the server only**. Never expose the API key or call the LLM from browser JavaScript. Key comes from env var `OPENROUTER_API_KEY`.
5. **Tests:** automated tests for all features. Tests MUST NOT call the real LLM, OpenRouter, or any external service. Mock them. Tests must pass with no network access and no real API keys.
6. **Environments:** public staging and production deployments.
7. **12-factor:**
   - All config and secrets in environment variables. Never commit secrets, `.env` files, or keys. Keep a `.env.example` with placeholder values only.
   - Database connection via a URL env var (`DATABASE_URL`).
   - Logs go to stdout/stderr.
   - No user uploads or lasting data on local disk. Use the database or object storage (S3-compatible).
   - App listens on `$PORT`.
   - All schema changes via migrations. Never edit the production schema by hand.
8. **Seed command:** creates demo data plus grader accounts (one per user role). MUST be idempotent: running it twice must not duplicate or fail (use get-or-create / upsert). Use fake data only, passwords used nowhere else, no 2FA, no email verification.
9. **UI:** responsive on phones and desktops. Use a CSS framework (e.g., Bootstrap, Tailwind, Pico).
10. **A/B test page:** exact spec below.

## A/B test page (MUST — follow exactly)

Path: `/<ab_hash>` and `/<ab_hash>/stats`.

Compute the hash correctly:

```bash
printf %s bright-forest | shasum   # → 211c220...  (sanity check: must match)
printf %s <team_nickname> | shasum # use first 7 chars
```

Do NOT use `echo` (it adds a newline and gives the wrong hash).

### `GET /<ab_hash>`

- Public: returns HTTP 200 with no login, no redirect to login, no modal, cookie banner, or pop-up covering the page.
- Lists every team member's nickname.
- Contains **exactly one** `<button id="abtest">`. Its text, trimmed, is exactly `kudos` or `thanks` (lowercase). No other element on the page may use `id="abtest"`.
- Variant assignment:
  - A new visitor (no session/cookie) is assigned `kudos` or `thanks` at random, 50/50.
  - Store the variant in the session or a cookie so the same visitor always sees the same variant.
  - Render the button text **server-side** in the HTML. No JavaScript may set or change it.
- Impressions: record exactly one impression per visitor, the first time they are assigned a variant. Reloads, revisits, and redirects back to the page MUST NOT create another impression.

### Click

- The button sends a request to the server. Preferred: wrap it in a plain `<form method="post">` (include the framework's CSRF token) posting to e.g. `/<ab_hash>/click`.
- Record at most one click per visitor. Repeat clicks are ignored.
- After the POST, redirecting back to `/<ab_hash>` is fine, but it MUST NOT add an impression or change the variant.
- If a POST arrives from a visitor with no assigned variant, do not count it.

### Storage

- Store impressions and clicks in the database with timestamps (e.g., an `ab_visitor` table: `id`, `visitor_id`, `variant`, `impression_at`, `clicked_at` nullable). A unique constraint on `visitor_id` is a good guard against double counting.
- Make sure a reset/cleanup command exists to delete all A/B rows (our own test visits must be wiped before the bot run).

### `GET /<ab_hash>/stats`

- Public. Returns JSON. MUST include key `preferred` with value `"kudos"` or `"thanks"`: the variant with the higher click rate (clicks ÷ impressions), computed live from the database on each request (no caching).
- Handle zero impressions without dividing by zero. Pick a deterministic tie-break.
- Extra keys are allowed:

```json
{"preferred": "kudos", "kudos": {"impressions": 212, "clicks": 63}, "thanks": {"impressions": 207, "clicks": 21}}
```

### Required tests for the A/B page

Write tests that verify: 200 without login; exactly one `#abtest` button with valid text; variant is sticky across requests; one impression per visitor across reloads; at most one click per visitor; click redirect does not add an impression or change variant; `/stats` math, tie, and zero-impression cases; roughly 50/50 assignment over many new visitors.

### Bot run context

After Sprint 4 a Playwright bot visits production; every visit is a new browser context (new visitor). It clicks one variant more often. Free hosting that sleeps is fine. Before the run: confirm production works end to end, then wipe test A/B data.

## Technical challenge (graded on depth)

Do ~3 items well rather than many shallowly. "Done well" means: tested, working on the deployed app, and handles failure (timeouts, bad input, external service down). Options:

- **Delivery:** CI (tests + lint on every PR, merge blocked on failure); CD (merge to `main` auto-deploys staging, deliberate manual promotion to production); Docker Compose dev setup; error tracking + health-check endpoint.
- **Backend:** background job queue with a separate worker process; scheduled jobs; documented JSON API with token auth; importing external data; roles/permissions beyond logged-in; full-text search; file uploads to object storage; email notifications; webhooks; social login.
- **AI:** retrieval over app data with pgvector; structured LLM output (JSON schema) that drives app behavior; an evaluation set run like tests; per-user AI usage limits.
- **Frontend/quality:** live updates without full reloads (Hotwire / LiveView / Livewire / htmx); Playwright end-to-end tests; accessibility checks in CI; measured performance work (indexes, N+1 fixes, caching) with before/after numbers.

For each chosen item, update `docs/mgt656/technical.md` when it ships.

## How we work (process is graded)

- **Backlog:** GitHub issues labeled `user story`. Each has a statement ("As a ..., I want ..., so that ...") and precise acceptance criteria. **Treat acceptance criteria as your spec.** If they are vague or missing, ask before coding. Large stories get sub-issues.
- **Project board:** one GitHub Project with an Iteration field, one iteration per sprint matching the dates above. Unfinished stories move to the next iteration; never delete them. No story points, velocity, or burndown charts.
- **Branches:** never commit directly to `main`. Create a branch per issue (e.g., `42-ab-click-counting`).
- **Pull requests:** every PR description MUST include:
  - `Closes #<issue>`
  - What the AI agent produced
  - What the team changed or rejected (leave a placeholder for the human to fill in if unknown)
  - How to test it
  A teammate reviews before merge. Do not merge PRs yourself unless told to.
- Before declaring a task done: run the full test suite and linter, and confirm migrations are included.

## Required docs: `docs/mgt656/`

```
docs/mgt656/
  team.yaml
  technical.md
  sprints/
    sprint-1.md
    sprint-2.md
    sprint-3.md
    sprint-4.md
    img/              # screenshots only; link to videos, don't commit them
  retrospective.md
```

**`team.yaml`**

```yaml
framework: django        # django | rails | laravel | phoenix | adonisjs
database: postgres       # postgres | mysql
members:
  - nickname: bald-chicken    # course nickname
    github: kljensen          # GitHub username
```

**`sprints/sprint-N.md`** (~half a page): sprint goal; what shipped (links to closed issues and merged PRs); what works on staging now; working with agents (one concrete thing that worked or didn't, and what changed); backlog changes for next sprint.

**`technical.md`:** for each technical-challenge item: what it is, main file paths and PRs, how to see it working. Then testing strategy: what is tested at which level, what is mocked, what is not tested and why.

**`retrospective.md`** (~half a page, final): what went well, what we'd do differently, how our way of working with AI agents changed.

When drafting sprint reports or the retrospective, draft from git history, issues, and PRs, and mark team-reflection sections for humans to complete. Do not invent reflections.

## Never do

- Commit secrets, API keys, passwords (other than the fake seed passwords if they live in seed code), or `.env` files.
- Call OpenRouter or any LLM from the browser or from tests.
- Store uploads or persistent data on local disk.
- Make the A/B page require login, set the button text with JS, or count impressions/clicks more than once per visitor.
- Delete or rewrite unfinished backlog issues.
- Push directly to `main`.

## Submission notes format (for the team, each sprint)

```
Access:
https://<staging-url>/login
admin: admin@example.com / <fake-password>
member: member@example.com / <fake-password>

Notes:
<anything half-done or graders should know>
```

## Grading (for prioritization)

Final: 60 pts = 20 working app + required items, 20 technical challenge, 10 A/B test (working page + correct `preferred` after bot run), 10 process & docs. Sprints graded separately (S1: 10, S2–S4: 15 each). If something is broken at grading, we get 24 hours to fix it, so keep staging and production healthy at all times.

Questions: course GitHub Discussions (github.com/orgs/yale-mgt-656-fall-2026/discussions) or Kyle.
