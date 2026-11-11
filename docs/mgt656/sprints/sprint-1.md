# Sprint 1: walking skeleton

**Goal:** a deployed Django + Postgres skeleton with auth, the A/B page, seed data, and CI.

## What shipped
- Django project with sign-up/login (`django.contrib.auth`) and editable travel profiles
- Trip, Membership (organizer/participant role + RSVP), ItineraryItem models; trips
  dashboard and trip detail with member-only access
- A/B page `/1ead64a`, click endpoint, `/1ead64a/stats`, `abtest_reset` command
- Idempotent `seed` command with organizer + participant grader accounts and a shared trip
- 34 automated tests, ruff, GitHub Actions CI, Render blueprint (staging + production)
- Issues / PRs: TODO(team): link closed issues and merged PRs

## What works on staging now
TODO(team): staging URL and a quick checklist once deployed.

## Working with agents
TODO(team): one concrete thing that worked or didn't, and what changed. (Human reflection,
not drafted by the agent.)

## Backlog changes for next sprint
TODO(team)
