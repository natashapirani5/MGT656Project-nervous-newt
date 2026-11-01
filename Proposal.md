**Option #2 Travel Planer 

**Tagline - Collaborative travel planning site that helps groups to coordinate availability, preferences, and build itineraries together. 

**Major user journeys 

New user: I sign up and create a new account. Then, I fill out my travel profile: including home city, interests, travel preferences, and any wishlist destinations. I can then search for friends to add to my friend list. 

Trip organizer: Log in to the “Trips” pages, where I can see my trip wishlist. I can create a new trip from the wishlist or by entering a destination, tentative dates, a short description, and budget. Next, I can invite friends to join the trip and generate an initial itinerary manually or using AI, which considers the group’s interest and budgets. 

Trip participant: As a friend invited to a trip, I log in to see the invitation and trip overview. I can indicate my availability for the proposed dates and RSVP yes, no, or conditional on certain details. After joining the trip, I can review the itinerary and contribute suggestions. 

**Core features 
User accounts and travel profiles: Editable profiles with name, city, travel interests (e.g., scuba diving, hiking, etc.), wishlist destinations, and trip preferences (e.g., splurges on food, prefers hostels, etc.). 

Friend directory: Ability to search for and add other users

Group trip creation: Create trips with a destination, dates, description, and budget. Ability to invite friends on trips. 

Collaborative itinerary builder:  Day by day itinerary where trip participants can propose to add/edit/remove items. Activities include title, date, time, location, and notes. 

Trips dashboard: Ability to view all upcoming trips on a unified view. 

**Skip for now: 
Travel booking integrations: No direct flight or hotel reservations 

Expense splitting and payment processing: Potential link to Spiltwise/venmo but no expensive settling on the website 

Automated calendar integrations: Dates entered manually for now 

Photo sharing: No social feature for photo sharing 

**AI feature - Primary AI feature will be an itinerary generator. Users can choose to manually work on the itinerary or have AI generate an initial itinerary based on the trip participants’ interests and preferences along with the general trip description (e.g., a relaxing 4 day girl’s trip in Montreal with great food and vintage shopping). Users can then view the recommended itinerary, comment on any changes, or manually edit the entries. 


**Option #3 News Explorer

**Tagline - Personalized news feed that pulls from the sources you trust, for the news that matters to you

**Major user journeys

New user: I sign up and choose my interests from a list of topics (Business, Travel, Entertainment, Tech, etc.), with optional sub-topics (e.g., Fintech, Airlines). I land on my feed straight away, already filled with recent articles.

Reader: I log in and see today’s feed grouped by interest. Each card shows the headline, source, publish time, a 2-line AI summary and a link to the original. I can save an article, dismiss it, mark “more like this/less like this”, and the feed adjusts and becomes more personalized over time.

Friend system: I add a friend by username and can see their news feed (if they allow access). I can also open a comparison page that shows a match score (how similar our feeds are), the interests we share, and where we differ most.

Admin: I manage the list of news sources (add or disable feeds), and view previous articles I've read.

**Core features
Article ingestion: a background job pulls the latest articles every hour from a curated list of 20–30 RSS feeds (Reuters, BBC, FT, etc.) and removes duplicates based on a preset user priority.

Interest profile and feed: alows users to pick topics, then get a ranked, filterable feed with save and dismiss actions.

Saved articles: a reading list users can come back to.

Feed sharing with friends/comparison: allow users to follow friends and see a match score based on topic weights and reading history, plus the topics they share.

AI tagging and summaries: refer to below.

Skip for now:
Free-form web scraping (RSS only; users can’t add arbitrary sites)
Paywalled content or showing full article text (link out to the original)
Comments, likes and social feed
Email digests and push notifications
Mobile app (responsive web app only)
**AI feature
An LLM will be used to process every new article to (a) ensure topic grouping is consistent across sources, (b) de-duplicate articles shared across multiple sources, (c) classify and summarize articles (i.e., provide the 2-line summary, rank articles based on importance) and (d) manage the friend taste-matching functionality.
