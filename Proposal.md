## Option #1 [Name]

#### 1. Tagline

"Letterboxd that fills itself in: connect your streaming and ticketing accounts to get one log of everything you've watched, plus a 'where have I seen them before?' button."

#### 2. Major user journeys

- **Viewer (onboarding and logging):** When I sign up, I connect my accounts: streaming services (Netflix, Max, Disney+, Hulu) and ticketing services (Ticketmaster, TodayTix, Fandango). The app imports my watch history and past tickets onto my timeline, tagged by platform or venue, and keeps syncing new activity. Anything it misses, like a movie at a friend's house or a community theater show, I add manually with "+ Log." I can rate or annotate any imported item afterward.
- **Viewer ("where have I seen them?"):** I'm watching something and an actor looks familiar, but I can't remember where I've seen them. I tap their name in the cast list or search for them. The app shows their filmography with the titles I've already watched or attended highlighted, plus when and where I saw each one: "Oh, she was in that play I saw last spring at Yale Rep!"
- **Viewer (recommendations):** I open "For You" and get picks across streaming, movies, and upcoming live shows. Each comes with a one-line reason drawn from my full history, and streaming picks show which of my connected platforms carries the title. I can save a pick to my watchlist or dismiss it.
- **Friend (matching):** I add a friend by username. Because both of our histories are imported, I see a taste-match score, titles and shows we've both seen (even "you were at the same concert"), where our ratings disagree most, and suggestions to watch together on platforms we both subscribe to.
- **Admin:** I log in to a dashboard where I can watch the health of each connection (failed syncs, broken parsers), fix imported items that matched the wrong title, merge duplicates, and review manually added live performances.

#### 3. Core features (MVP)

*Build:*

1. **Account connections and auto-import:** Netflix viewing-history upload, plus Gmail receipt parsing for ticketing and streaming purchase or rental confirmations. Titles are matched against TMDB for movies and TV, and against parsed event details for live shows.
2. **Unified timeline with manual fallback:** imported and manual entries live side by side, and you can rate, annotate, or correct any entry.
3. **Actor lookup:** a cast and filmography page cross-referenced with your history, showing when and where you saw each title.
4. **Friends and taste match:** follow friends, see a compatibility score, overlapping titles, and shared platforms.
5. **AI recommendations and import cleanup:** see section 4.

*Skip for now:*

- Direct integration with every platform (start with 1–2 sources and add the rest later)
- A browser extension for real-time tracking
- A full live-theater database (rely on ticket data plus manual entries)
- Social feed, comments, and likes
- Mobile app (start with a responsive web app)
- Face recognition for actors

#### 4. AI feature

An LLM works across your imported and manual history to:

- **Clean up imports:** turn messy receipts and history rows ("TodayTix Order #4821 – HADESTOWN 7:30PM") into structured entries with title, venue, date, and type. It also matches each entry to the right title and flags ones it isn't sure about so you can confirm them.
- **Explain its recommendations:** it suggests titles across streaming, movies, and upcoming live shows, each with a reason tied to your history and noting which of your platforms carries it.
- **Write a taste-match summary with a friend:** "You both binge prestige dramas and saw *Hadestown* within a month of each other. Try *Shōgun* together; you both have Hulu."
- **Add a memory jog to actor lookups (optional):** "You've seen this actor 3 times, most recently in *Gladiator II* at AMC in March."

The import cleanup is now the most essential AI feature, because without it the auto-import can't produce a usable log. Recommendations and friend matching remain the user-facing highlight.

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
