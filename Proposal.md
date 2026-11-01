## Option #1 [Name]

#### 1. Tagline

"Letterboxd for everything you watch: one log for your streaming, movies, and live shows, plus a 'where have I seen them before?' button."

#### 2. Major user journeys

- **Viewer (logging):** I log in and land on my timeline. I tap "+ Log," search for a title (a show, a movie, or a Broadway or theater performance), pick where I watched it (Netflix, Max, a theater, a live venue), and add a date, a rating, and an optional note. It shows up on my timeline and updates my stats.
- **Viewer ("where have I seen them?"):** I'm halfway through a show and don't recognize an actor. I search their name or pick them from the cast list. The app shows their filmography with the titles I've already logged highlighted, so I can see "Oh, she was in that play I saw last spring!"
- **Viewer (recommendations):** I open "For You" and get a short list of picks with a one-line reason for each ("because you rated *Past Lives* 5★ and love slow-burn romance"). I can save one to my watchlist or dismiss it.
- **Friend (matching):** I add a friend by username. I open their profile and see a taste-match score, the titles we've both seen, where our ratings disagree most, and suggestions for something to watch together.
- **Admin:** I log in to a dashboard where I can merge duplicate titles, review user-submitted live performances that aren't in the movie database, and handle reported content.

#### 3. Core features (MVP)

*Build:*

1. **Unified viewing log:** manual logging of movies, TV shows, and live performances, with platform or venue tags, using the TMDB API for movie and TV data plus a simple form for live shows.
2. **Actor lookup:** a cast and filmography page that cross-references your log.
3. **Personal profile and stats:** timeline, ratings, and breakdowns by platform and genre.
4. **Friends and taste match:** follow friends, see a compatibility score and overlapping titles.
5. **AI recommendations:** see section 4.

*Skip for now:*

- Automatic import from streaming platforms (most have no public API; at most, offer CSV upload for Netflix history later)
- A full live-theater database (let users add performances manually)
- Social feed, comments, and likes
- Mobile app (start with a responsive web app)
- Face recognition for actors

#### 4. AI feature

An LLM reads your viewing log, ratings, and notes, then:

- **Explains its recommendations:** it suggests 5 titles across movies, TV, and live shows, each with a short reason tied to your history, instead of opaque "you might like" lists.
- **Writes a taste-match summary with a friend:** "You both love A24 horror and Phoebe Waller-Bridge, but Sam rates musicals way higher. Try *The Bear* together this weekend."
- **Adds context to actor lookups (optional):** "You've seen Paul Mescal in 3 things, most recently *Gladiator II*. He's known for intense dramatic roles."

The recommendation and friend-match feature is the strongest core AI feature, since it uses data only your app has: cross-platform history plus live shows.

---

## Option #2 Travel Planer

**Tagline** - Collaborative travel planning site that helps groups to coordinate availability, preferences, and build itineraries together.

### Major user journeys

- **New user:** I sign up and create a new account. Then, I fill out my travel profile: including home city, interests, travel preferences, and any wishlist destinations. I can then search for friends to add to my friend list.
- **Trip organizer:** Log in to the "Trips" pages, where I can see my trip wishlist. I can create a new trip from the wishlist or by entering a destination, tentative dates, a short description, and budget. Next, I can invite friends to join the trip and generate an initial itinerary manually or using AI, which considers the group's interest and budgets.
- **Trip participant:** As a friend invited to a trip, I log in to see the invitation and trip overview. I can indicate my availability for the proposed dates and RSVP yes, no, or conditional on certain details. After joining the trip, I can review the itinerary and contribute suggestions.

### Core features

1. **User accounts and travel profiles:** Editable profiles with name, city, travel interests (e.g., scuba diving, hiking, etc.), wishlist destinations, and trip preferences (e.g., splurges on food, prefers hostels, etc.).
2. **Friend directory:** Ability to search for and add other users
3. **Group trip creation:** Create trips with a destination, dates, description, and budget. Ability to invite friends on trips.
4. **Collaborative itinerary builder:** Day by day itinerary where trip participants can propose to add/edit/remove items. Activities include title, date, time, location, and notes.
5. **Trips dashboard:** Ability to view all upcoming trips on a unified view.

*Skip for now:*

- **Travel booking integrations:** No direct flight or hotel reservations
- **Expense splitting and payment processing:** Potential link to Spiltwise/venmo but no expensive settling on the website
- **Automated calendar integrations:** Dates entered manually for now
- **Photo sharing:** No social feature for photo sharing

### AI feature

Primary AI feature will be an itinerary generator. Users can choose to manually work on the itinerary or have AI generate an initial itinerary based on the trip participants' interests and preferences along with the general trip description (*e.g., a relaxing 4 day girl's trip in Montreal with great food and vintage shopping*). Users can then view the recommended itinerary, comment on any changes, or manually edit the entries.

---

## Option #3 News Explorer

**Tagline** - Personalized news feed that pulls from the sources you trust, for the news that matters to you

### Major user journeys

- **New user:** I sign up and choose my interests from a list of topics (Business, Travel, Entertainment, Tech, etc.), with optional sub-topics (e.g., Fintech, Airlines). I land on my feed straight away, already filled with recent articles.
- **Reader:** I log in and see today's feed grouped by interest. Each card shows the headline, source, publish time, a 2-line AI summary and a link to the original. I can save an article, dismiss it, mark "more like this/less like this", and the feed adjusts and becomes more personalized over time.
- **Friend system:** I add a friend by username and can see their news feed (if they allow access). I can also open a comparison page that shows a match score (how similar our feeds are), the interests we share, and where we differ most.
- **Admin:** I manage the list of news sources (add or disable feeds), and view previous articles I've read.

### Core features

1. **Article ingestion:** a background job pulls the latest articles every hour from a curated list of 20–30 RSS feeds (Reuters, BBC, FT, etc.) and removes duplicates based on a preset user priority.
2. **Interest profile and feed:** alows users to pick topics, then get a ranked, filterable feed with save and dismiss actions.
3. **Saved articles:** a reading list users can come back to.
4. **Feed sharing with friends/comparison:** allow users to follow friends and see a match score based on topic weights and reading history, plus the topics they share.
5. **AI tagging and summaries:** refer to below.

*Skip for now:*

- Free-form web scraping (RSS only; users can't add arbitrary sites)
- Paywalled content or showing full article text (link out to the original)
- Comments, likes and social feed
- Email digests and push notifications
- Mobile app (responsive web app only)

### AI feature

An LLM will be used to process every new article to (a) ensure topic grouping is consistent across sources, (b) de-duplicate articles shared across multiple sources, (c) classify and summarize articles (i.e., provide the 2-line summary, rank articles based on importance) and (d) manage the friend taste-matching functionality.
