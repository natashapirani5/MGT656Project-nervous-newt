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
- [#<DOCS_PR> Sprint 1 docs](https://github.com/natashapirani5/MGT656Project-nervous-newt/pull/<DOCS_PR>) <!-- this PR; fill in the number once opened -->

**Closed issues**

- [#2 Setup product backlog for future sprints](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/2)
- [#3 Setup Sprint 1 stories](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/3)
- [#4 Staging deployment](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/4)
- [#5 Complete docs and submit](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/5)

<!-- CHECK BEFORE MERGE: remove any issue above that is not actually closed. -->

## What works on staging now

Staging: <STAGING_URL>  <!-- from #4 -->

<!-- Tick only what was checked by hand on staging; leave the rest unticked and mention it in the grader notes. -->
- [ ] Log in with the organizer account (`admin@example.com`)
- [ ] Log in with the participant account (`member@example.com`)
- [ ] `/1ead64a` loads, and the variant stays the same on reload
- [ ] Clicking the button updates `/1ead64a/stats`
- [ ] Migrations and seed ran on deploy

## Working with agents

TODO(team): one concrete thing that worked or didn't, and what we changed.
**Written by the team, not drafted by AI.**

## Backlog changes for next sprint

TODO(team): confirm against the project board once #2 lands. Known so far:

- User stories #6–#10 (accounts, seed, A/B page, CI, staging site) were not in this
  sprint's scope and move to Sprint 2. <CONFIRM with team>
- Feature stories from [#2](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/2)
  (profiles, friend directory, group trips and invites, availability and RSVP, collaborative
  itinerary, trips dashboard, AI itinerary generation) go into Sprints 2–4.
- Sprint 2 also needs a public production URL (required from Nov 18).
- <any Sprint 1 item not finished, e.g. branch protection on `main`, moves to Sprint 2>
