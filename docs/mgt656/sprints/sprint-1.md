# Sprint 1: walking skeleton

**Goal:** a deployed Django + Postgres skeleton with auth, the A/B page, seed data, and CI.

## What shipped

- Django project with sign-up/login (`django.contrib.auth`) and editable travel profiles
- Trip, Membership (organizer/participant role + RSVP), ItineraryItem models; trips
  dashboard and trip detail with member-only access
- A/B page `/1ead64a`, click endpoint, `/1ead64a/stats`, `abtest_reset` command
- Idempotent `seed` command with organizer + participant grader accounts and a shared trip
- 34 automated tests, ruff, GitHub Actions CI, Render blueprint (staging + production)

**Merged PRs**

- [#1 Sprint 1 walking skeleton: auth, trips, A/B page, seed, CI](https://github.com/natashapirani5/MGT656Project-nervous-newt/pull/1)
- [#12 Sprint 1 docs](https://github.com/natashapirani5/MGT656Project-nervous-newt/pull/12)

**Sprint 1 issues** ([project board](https://github.com/users/natashapirani5/projects/2), Sprint 1 iteration)

- [#3 Setup Sprint 1 stories](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/3)
- [#4 Staging deployment](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/4)
- [#6 Sign up, log in, and set up a travel profile](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/6)
- [#7 Seed demo data and grader accounts](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/7)
- [#8 A/B test page and stats](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/8)
- [#9 Automated tests and lint on every pull request](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/9)
- [#10 Public staging site](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/10)

## What works on staging now

Staging: https://travel-planner-staging-9e6n.onrender.com

Checked on staging on Nov 13, 2026:

- [x] `/healthz` returns `{"status": "ok"}`
- [x] Log in with the organizer account (`admin@example.com`) and see the seeded Montreal trip on `/trips/`
- [x] Log in with the participant account (`member@example.com`) and see the same trip
- [x] `/1ead64a` loads with no login, lists all four nicknames, and has one `kudos`/`thanks` button
- [x] The variant stays the same on reload
- [x] Clicking the button updates `/1ead64a/stats`
- [x] Migrations and seed ran on deploy (grader accounts and seeded trip exist)

## Working with agents

It was really interesting to work with agents in a team setting. Right from the start, our team had the urge to vibe code the skeleton but quickly realized how disorganized it could get with a larger project where everyone is contributing. We then spent time making sure Claude Code is connected to our Github repository, and that we are pointing the agents to the same context via an agent-readme file. Once we created a project with issues, assigned members to each issue, we were able to individually work with our agents in a much more effective and organized manner to create new branches, edit files, look over pull requests, and in general progress toward the end goal.

## Backlog changes for next sprint

Feature stories for the core features were written in [#2 Setup product backlog for future sprints](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/2) and placed in Sprints 2–4 on the project board:

- **Sprint 2:**
  - [#13 Production site and safe deploys](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/13)
  - [#14 Friend directory](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/14)
  - [#15 Create a trip and invite friends](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/15)
- **Sprint 3:**
  - [#16 Respond to an invite: availability and RSVP](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/16)
  - [#17 Collaborative itinerary](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/17)
  - [#20 Generate an itinerary with AI](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/20)
- **Sprint 4:**
  - [#18 Dashboard: see what needs my attention](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/18)
  - [#19 View a friend's travel profile](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/19)
  - [#21 Live updates without page reloads](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/21)
  - [#22 A/B test bot run readiness](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/22)

Larger stories are split into sub-issues:

- [#14 Friend directory](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/14) → [#23](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/23), [#24](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/24), [#25](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/25)
- [#17 Collaborative itinerary](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/17) → [#26](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/26), [#27](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/27), [#28](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/28)
- [#20 Generate an itinerary with AI](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/20) → [#29](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/29), [#30](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/30), [#31](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/31)

Team tasks for each sprint's report and submission: [#32 Sprint 2](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/32), [#33 Sprint 3](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/33), [#34 Sprint 4](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/34), [#35 Retrospective and final submission](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/35).

Sprint 2 also adds a public production URL (required from Nov 18).
