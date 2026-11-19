# Sprint 2: friends, trips, and production

**Goal:** let travelers find friends, create a trip and invite those friends, and put the app on a public production site that only updates when we deliberately promote a change from staging.

## What shipped

- **Friend directory:** search for travelers by name or email (results show name and home city, never email addresses), send, accept, and decline friend requests, and see or remove friends on `/friends/`
- **Trips:** a "New trip" form at `/trips/new/` that suggests wishlist destinations and rejects an end date before the start date; the creator becomes the organizer; organizers can edit trip details
- **Invites:** organizers can invite one or more friends from the trip page; invitees join with RSVP "Pending"; only friends can be invited, there are no duplicates, and participants who try get an error page
- **Seed data:** the two grader accounts are friends, each has a pending friend request to try, and the organizer has a friend (Jordan Lee) who isn't on the Montreal trip yet, so invites can be tried right away
- **Production and safe deploys:** `travel-planner-production` on Render with its own Neon database, the `/healthz` health check, and Auto-Deploy off; merging to `main` updates staging only (staging auto-deploy restored in #40); "CI" is a required check on `main`; release steps and screenshots of both Events tabs are in `docs/mgt656/technical.md`

**Merged PRs**

- [#37 Friend directory: search, friend requests, friends list (#14)](https://github.com/natashapirani5/MGT656Project-nervous-newt/pull/37)
- [#38 Create a trip and invite friends (#15)](https://github.com/natashapirani5/MGT656Project-nervous-newt/pull/38)
- [#39 Production site and release steps (#13)](https://github.com/natashapirani5/MGT656Project-nervous-newt/pull/39)

**Closed Sprint 2 issues** ([project board](https://github.com/users/natashapirani5/projects/2), Sprint 2 iteration)

- [#13 Production site and safe deploys](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/13)
- [#14 Friend directory](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/14), with sub-issues [#23 search](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/23), [#24 friend requests](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/24), [#25 friends list](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/25)
- [#15 Create a trip and invite friends](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/15)
- [#40 Fix staging auto-deploy](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/40)

## What works on staging and production now

- Staging: https://travel-planner-staging-9e6n.onrender.com
- Production: https://travel-planner-production-1ad2.onrender.com

Checked on Nov 18, 2026:

- [x] `/healthz` returns OK on both sites
- [x] Both grader accounts (`admin@example.com`, `member@example.com`) log in on staging and production
- [x] `/friends/`: search, accept or decline the seeded pending request, see and remove friends
- [x] `/trips/new/`: create a trip; the organizer can edit it and invite Jordan Lee
- [x] `/1ead64a` and `/1ead64a/stats` work on production
- [x] Migrations and seed ran on the production deploy ("Seed data is in place.")
- [x] Production only changes when someone clicks Manual Deploy
- [x] Staging auto-deploys on merge to `main`; this was broken after Nov 12 and fixed in [#40](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/40), with screenshots of both Events tabs saved in `docs/mgt656/sprints/img/` and linked from `docs/mgt656/technical.md`

## Working with agents

The agents worked well when given the full project context. They kept the overall goal in view rather than handling tasks in isolation, and they gave clear, step-by-step guidance. They were also helpful for troubleshooting, since they could quickly diagnose errors and suggest fixes.

## Backlog changes for Sprint 3

- All Sprint 2 stories (#13, #14, #15) were closed.
- **Bug fixed during Sprint 2:** [#40 Fix staging auto-deploy](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/40) was found late in the sprint, when merges after Nov 12 (including #37, #38 and #39) didn't deploy to staging until we deployed by hand on Nov 18. It is now closed: staging auto-deploys on merge again, the Events-tab screenshots that prove "merging updates staging only" for #13 are in `technical.md`, and #40 is no longer on the Sprint 3 backlog.
- **Sprint 3:**
  - [#16 Respond to an invite: availability and RSVP](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/16) (builds on the invites from #15)
  - [#17 Collaborative itinerary](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/17) → [#26](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/26), [#27](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/27), [#28](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/28)
  - [#20 Generate an itinerary with AI](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/20) → [#29](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/29), [#30](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/30), [#31](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/31)
- Team task: [#33 Sprint 3 report and submission](https://github.com/natashapirani5/MGT656Project-nervous-newt/issues/33)
- From now on, every release to production is a deliberate Manual Deploy after the change is checked on staging.
