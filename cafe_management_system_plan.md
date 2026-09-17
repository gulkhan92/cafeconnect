# Cafe Management System - End-to-End Development Plan

## 1. Project Overview

The goal is to build a production-grade cafe management web application that functions as the digital front door of the cafe and as an internal operations tool for the owner and staff.

The system has two user-facing layers:

1. A public marketing website that presents the cafe professionally: ambience gallery, story, menu, location, and a conversational booking assistant. This layer should look and feel like a website built by a large, well-funded hospitality or food-tech company, not a template demo.
2. An authenticated application layer where customers can log in to book tables, check slot availability, place online orders, and track order status, and where cafe staff/owner can log in to a revenue and operations dashboard.

The system is built with entirely free and open-source technology, plus free tiers of two LLM providers used interchangeably (Groq running an open-weight model, and Google Gemini) so the project has zero mandatory recurring cost during development and low-volume production use.

Core capabilities to deliver:

- Public website with ambience gallery, full menu with categories and images, cafe story/about, location and hours, and a persistent login entry point.
- A booking chatbot that understands natural language requests, checks real table and slot availability in the database, and confirms or rejects bookings, using minimal LLM calls per conversation.
- A visual table and slot availability view as a fallback/complement to the chatbot, for users who prefer clicking over chatting.
- Online ordering: browse menu, add to cart, checkout, view order history and live status.
- Role-based access: customer role and staff/admin role, with authentication and authorization enforced on every protected endpoint.
- A real revenue dashboard for the owner: daily/weekly/monthly revenue, best-selling items, table utilization, booking-to-order conversion, and peak-hour analysis, backed by real order and booking data, not mock numbers.

## 2. Problem Statement

Independent cafes typically rely on a mix of disconnected tools: a static Instagram page for ambience and menu, phone calls or WhatsApp for table bookings, a separate POS for orders, and a notebook or spreadsheet for tracking revenue. This creates several concrete problems:

- Customers cannot see live table or slot availability before visiting or calling, leading to walk-ins being turned away or phone lines being tied up during peak hours.
- There is no unified place where a customer can browse the menu, see the actual ambience, book a table, and place an order in one continuous flow.
- Owners have no real-time, data-backed view of revenue, best-selling items, or table utilization, so decisions on staffing, menu changes, and pricing are made on intuition rather than data.
- Any AI-assisted booking experience built naively (sending full conversation history and unrestricted prompts to a paid LLM on every turn) becomes expensive and slow at scale, which is unacceptable for a small business operating on tight margins and free-tier API quotas.
- Small cafe owners cannot justify the cost of enterprise SaaS booking and analytics platforms, so the solution must be self-hosted, built on free/open-source components, and cheap to run.

This project solves these problems by building a single, professionally designed web application that unifies ambience presentation, live menu, conversational and manual table booking, online ordering, and a genuine analytics dashboard, while deliberately engineering the AI booking assistant to minimize token usage and LLM API dependency.

## 3. Tech Stack

All components below are free and open-source, or have a permanently free tier suitable for this project's scale.

Backend:
- Python 3.12
- FastAPI for the REST API layer (async, automatic OpenAPI docs)
- Uvicorn as the ASGI server
- SQLAlchemy 2.x (async) as the ORM
- Alembic for database migrations
- Pydantic v2 for request/response validation

Database and search:
- PostgreSQL 16 (self-hosted, free, e.g. via Docker or a free tier such as Supabase/Neon/Render free Postgres)
- pgvector extension for storing menu item embeddings and enabling semantic search inside the booking/menu chatbot
- Redis (free, self-hosted via Docker) for caching slot availability lookups, rate limiting, and session/short-term chat state

AI and NLP:
- Sentence embeddings generated locally with an open-source Hugging Face model: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions, fast, free, runs on CPU) for menu item semantic search and for FAQ/intent matching before any LLM call is made
- LLM layer with two interchangeable providers, both used on their free tiers:
  - Groq API running `openai/gpt-oss-20b` (fast, low-latency, free tier available with daily/per-minute request caps)
  - Google Gemini API running a Flash-class model (free tier available with per-minute and per-day caps)
  - A provider-abstraction layer in the backend picks whichever provider is currently within its free-tier quota, and fails over to the other automatically on a 429/rate-limit response

Frontend:
- React 18 with Vite as the build tool
- TypeScript
- TailwindCSS for styling, with a custom design system (not default Tailwind look)
- React Router for navigation
- React Query (TanStack Query) for data fetching and caching
- Zustand or Redux Toolkit for lightweight client state (cart, chat session, auth state)
- Framer Motion for subtle, premium-feeling animations
- Recharts or Chart.js for the revenue dashboard charts

Authentication and authorization:
- JWT-based authentication (short-lived access token plus refresh token) issued by the FastAPI backend
- Passwords hashed with bcrypt (via passlib)
- Role-based access control with two roles at minimum: `customer` and `staff_admin`
- OAuth2 password flow for login, with the option to add Google OAuth login later using free Google OAuth client credentials
- All dashboard and booking/order-mutation endpoints protected by dependency-injected auth checks in FastAPI

Data security:
- HTTPS enforced in production (free TLS via Let's Encrypt if self-hosting, or automatic TLS on the chosen free hosting platform)
- Environment variables for all secrets (API keys, DB credentials, JWT signing key), never committed to source control
- Input validation on every endpoint via Pydantic schemas
- Parameterized queries only, via the ORM, to prevent SQL injection
- Rate limiting on public endpoints (chatbot and login) via Redis-backed limiter to prevent abuse and to protect free-tier LLM quotas
- CORS locked down to the deployed frontend origin only
- Audit fields (`created_at`, `updated_at`, `created_by`) on booking and order tables

Deployment (all free-tier options):
- Backend: Render, Railway, or Fly.io free tier, or a free-tier VM
- Frontend: Vercel or Netlify free tier
- Database: Supabase, Neon, or Railway free Postgres with pgvector support
- CI/CD: GitHub Actions (free for public/small private repos)

## 4. Dataset

Two categories of data are needed: menu/item data to seed the cafe's own menu and ambience content, and historical order/transaction data to make the revenue dashboard meaningful during development and demos.

### 4.1 Menu and cafe content data

Use the following free datasets as a seed and reference for realistic menu structure, categories, pricing patterns, and item descriptions. Do not use any dataset that requires payment or a restrictive license.

- "Restaurant Menu Items" (Kaggle, user graphquest): approximately 5,000 real-world restaurant menu items with names, categories, and prices, collected from a food delivery platform. Download from kaggle.com/datasets/graphquest/restaurant-menu-items. Use this to seed realistic item names, category structures (beverages, bakery, breakfast, mains, desserts), and price ranges.
- "Cafe ratings and Prices dataset" (Kaggle, user SevanthiBR): a small, cafe-specific CSV with item and price fields, useful as a direct starting template for a cafe (as opposed to a general restaurant) menu.
- "New York Restaurant Menus and Details" (Kaggle, user anoopjohny): richer menu metadata (descriptions, categories) useful for enriching item descriptions that will later be embedded for semantic search.

Usage instructions:
1. Download the CSV files from Kaggle (requires a free Kaggle account).
2. Write a one-time ETL script (`scripts/seed_menu.py`) that reads the CSVs, filters/maps rows to the project's `menu_items` schema (name, category, description, price, image_url, is_available), and inserts them into PostgreSQL.
3. Manually curate and replace generic items with the actual cafe's real menu before going live. The public dataset is a bootstrapping and testing aid, not the final production menu.
4. For each menu item, generate an embedding of `name + description` using the Hugging Face `all-MiniLM-L6-v2` model and store it in a `pgvector` column, so the chatbot and site search can match natural-language queries like "something cold and chocolatey" to the right items without calling an LLM.
5. Source real ambience photography (interior, seating, coffee preparation, plating) either from the cafe's own photos or from free, license-clear stock photo sites (Unsplash, Pexels) during development, clearly replacing all placeholder images with real cafe photography before production launch.

### 4.2 Bookings and orders data for the dashboard

- "Analyzing International Restaurant Orders Dataset" (Kaggle, Maven Analytics via user agungpambudi): a quarterly set of hypothetical restaurant orders with timestamps, item names, categories, and prices. Download from kaggle.com/datasets/agungpambudi/analyzing-restaurant-orders-international-dataset.
- "Restaurant Cost and Sales Dataset" (Kaggle, user virtualschool/Ahmed Lotfy Twfik): item cost versus price data, useful for margin-aware revenue analysis on the dashboard (revenue vs. estimated cost vs. estimated margin per item).

Usage instructions:
1. Write a script (`scripts/seed_historical_orders.py`) that maps this data into the project's `orders` and `order_items` tables, back-dating timestamps across several months so the dashboard has enough historical spread to render meaningful daily/weekly/monthly trend charts during development.
2. Treat this as synthetic seed data only. Clearly separate it (e.g. a `source = 'seed_demo'` flag) so it can be purged with one command before the cafe goes live with real transactions.
3. All dashboard queries must be written against the live `orders`, `order_items`, and `bookings` tables so that once seed data is purged and real transactions start flowing in, the dashboard automatically reflects genuine revenue with no code changes.

## 5. Phase-Wise Development Plan

### Phase 0: Architecture, Environment, and Repository Setup

Objectives: lock down the technical foundation before any feature work starts.

Tasks:
- Initialize a monorepo with two top-level folders: `backend/` (FastAPI) and `frontend/` (React + Vite).
- Set up Python virtual environment and `requirements.txt` (or `pyproject.toml` with Poetry) pinning: fastapi, uvicorn, sqlalchemy, asyncpg, alembic, pydantic, python-jose or pyjwt, passlib[bcrypt], redis, sentence-transformers, pgvector, groq, google-genai, python-dotenv, slowapi (for rate limiting).
- Set up `docker-compose.yml` with three services: `postgres` (with pgvector extension enabled), `redis`, and the FastAPI `backend`. This gives every developer an identical local environment with one command.
- Define the full database schema in an ER diagram before writing migrations: `users`, `roles`, `menu_items`, `menu_categories`, `tables`, `table_slots`, `bookings`, `orders`, `order_items`, `chat_sessions`, `chat_messages`.
- Create `.env.example` listing every required environment variable (`DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `GROQ_API_KEY`, `GEMINI_API_KEY`, `ENV`) with placeholder values, and add `.env` to `.gitignore`.
- Set up GitHub Actions workflow skeleton for lint (ruff/eslint), test (pytest/vitest), and build, running on every pull request.

Deliverable: a running local stack (`docker compose up`) with an empty FastAPI app returning a health check, and an empty React app rendering a placeholder home page, both connected to the same Git repository with CI passing.

### Phase 1: Database Schema and Migrations

Objectives: implement the full relational schema with correctness and future extensibility in mind.

Tasks:
- Enable the `pgvector` extension in the Postgres database.
- Implement SQLAlchemy models for all tables identified in Phase 0, including:
  - `users`: id, name, email (unique), hashed_password, role, phone, created_at.
  - `menu_categories`: id, name, display_order.
  - `menu_items`: id, category_id, name, description, price, image_url, is_available, embedding (vector(384)).
  - `tables`: id, table_number, capacity, location_tag (e.g. window, patio, indoor).
  - `table_slots`: id, table_id, date, start_time, end_time, is_booked, booking_id (nullable).
  - `bookings`: id, user_id, table_id, slot_id, party_size, status (pending/confirmed/cancelled), created_via (chatbot/manual), created_at.
  - `orders`: id, user_id, booking_id (nullable, for dine-in orders linked to a booking), status (placed/preparing/ready/completed/cancelled), total_amount, source (seed_demo/live), created_at.
  - `order_items`: id, order_id, menu_item_id, quantity, unit_price_at_order_time.
  - `chat_sessions`: id, user_id (nullable for guest), started_at, last_intent.
  - `chat_messages`: id, session_id, role (user/assistant), content, created_at.
- Write Alembic migrations for every model, and check them into version control.
- Add appropriate indexes: unique index on `users.email`, composite index on `table_slots(date, start_time)`, index on `orders.created_at` for dashboard queries, and an HNSW or IVFFlat index on `menu_items.embedding` for fast vector search.
- Write a seed script that creates a default `staff_admin` user, a default set of tables, and generates slots for the next 30 days at fixed intervals (e.g. every 30 minutes within opening hours).

Deliverable: migrations run cleanly on a fresh database, and the seed script produces a fully queryable set of tables, slots, and a default admin account.

### Phase 2: Authentication and Authorization

Objectives: secure every part of the system before any business logic is exposed.

Tasks:
- Implement `/auth/register` and `/auth/login` endpoints. Registration hashes passwords with bcrypt before storage; login verifies the hash and issues a short-lived JWT access token (15 to 30 minutes) and a longer-lived refresh token (7 days), both signed with a secret from environment variables.
- Implement `/auth/refresh` to exchange a valid refresh token for a new access token, and `/auth/logout` to revoke the refresh token (store revoked/active refresh tokens in Redis or a dedicated table).
- Implement a FastAPI dependency `get_current_user` that decodes and validates the JWT on every protected route, and a `require_role("staff_admin")` dependency for admin-only routes.
- Apply role checks explicitly to every mutating endpoint: only `staff_admin` can update menu items, view the revenue dashboard, or change booking/order status beyond what a customer is allowed to do; customers can only view and manage their own bookings and orders.
- Add rate limiting (via slowapi + Redis) on `/auth/login` and on the chatbot endpoint to prevent brute-force attempts and to protect free-tier LLM quotas from abuse.
- On the frontend, implement an auth store (Zustand/Redux) that holds the access token in memory and the refresh token in an httpOnly cookie or secure storage, with automatic silent refresh on 401 responses, and route guards that redirect unauthenticated users away from protected pages.

Deliverable: a working login/registration flow end to end, with role-based route protection verified by automated tests (attempting a staff-only action as a customer must return 403).

### Phase 3: Menu, Tables, and Slot Availability APIs

Objectives: expose the core data the rest of the system depends on.

Tasks:
- Build `GET /menu` (public) returning categories with nested items, and `GET /menu/search?q=` that embeds the query with the Hugging Face model at request time and performs a pgvector cosine-similarity search against `menu_items.embedding`, returning the closest matches. This endpoint is what both the visual site search and the chatbot's menu lookups will call, so no menu question ever needs to reach an LLM.
- Build staff-only `POST/PUT/DELETE /menu/items` for menu management, regenerating the item's embedding whenever its name or description changes.
- Build `GET /tables/availability?date=&party_size=` returning open slots per table for the requested date and party size, reading from `table_slots` and filtering by `is_booked = false` and `tables.capacity >= party_size`.
- Build `POST /bookings` (authenticated) that atomically checks slot availability and creates a booking, using a database transaction with row-level locking (`SELECT ... FOR UPDATE`) on the target slot to prevent double-booking under concurrent requests.
- Build `GET /bookings/me` and staff-only `GET /bookings` (all bookings, filterable by date/status) and `PATCH /bookings/{id}` for status changes (confirm/cancel).
- Write integration tests that specifically simulate two concurrent booking requests for the same slot and assert exactly one succeeds.

Deliverable: fully functional, race-condition-safe booking APIs and a semantic menu search endpoint, independent of any LLM, with test coverage on the concurrency-critical path.

### Phase 4: Booking Chatbot with Minimal LLM Token Usage

Objectives: deliver a natural-language booking and menu assistant that is fast, reliable, and uses the least possible number of LLM tokens per conversation.

Design principles to minimize LLM usage:
- Classify user intent locally first. Use a lightweight rules/regex and keyword layer (and, if needed, the same Hugging Face embedding model to compare the user message against a small fixed set of labeled example intents such as "book_table", "check_availability", "menu_question", "order_item", "small_talk") before ever calling an LLM. Only fall through to the LLM when local classification is ambiguous.
- For menu questions, never send the LLM the full menu. Use the `/menu/search` semantic endpoint from Phase 3 to retrieve only the top 3 to 5 relevant items, and only pass those short snippets to the LLM if a natural-language answer needs to be composed; for a large share of queries, the retrieved items can be returned directly to the user with no LLM call at all.
- For booking, use the LLM only to extract structured fields (date, time, party size, preference) from free text into a fixed JSON schema, in a single short call, then hand off to the deterministic Phase 3 availability and booking APIs. Never let the LLM "decide" whether a table is free; that must always be a database check.
- Keep the system prompt short and static so it benefits from provider-side prompt caching where available, and never resend the full conversation history; keep only a short rolling summary plus the last one or two turns in `chat_sessions`/`chat_messages`, and pass that condensed context to the LLM instead of the entire transcript.
- Cap max output tokens on every LLM call to a small number appropriate to the task (structured extraction needs very few tokens).

Provider abstraction and failover:
- Implement an `llm_client` module with a common interface (`extract_booking_intent(text)`, `answer_with_context(text, context_snippets)`).
- Configure Groq as the primary provider running `openai/gpt-oss-20b` (fast, generous throughput on the free tier), and Gemini (Flash-class free tier model) as the secondary provider.
- On receiving a 429 or quota-exceeded error from the primary provider, automatically retry the same request against the secondary provider within the same user-facing turn, so the user never sees a failure due to quota limits, and log which provider served each request for monitoring.
- Track daily/per-minute call counts per provider in Redis so the system can proactively switch to the secondary provider before hitting a hard limit, rather than reactively after a failure.

Chatbot flow implementation:
- Build `POST /chat/message` accepting `session_id` (create one if absent) and the user message.
- Pipeline: local intent classification, then either (a) direct database/API answer with no LLM call, (b) a single small structured-extraction LLM call followed by a deterministic API call, or (c) a single short LLM call grounded only in retrieved snippets for open-ended questions.
- Persist every turn to `chat_messages` for audit and for future fine-tuning of the local intent classifier.
- Build the chat widget on the frontend: a floating, professionally styled chat panel available on every public page, showing typing indicators, quick-reply buttons for common actions (check availability, view menu, talk to staff), and a clear fallback message directing the user to call the cafe if both LLM providers are temporarily unavailable.

Deliverable: a chatbot that can complete a full booking (date, time, party size, table preference, confirmation) using at most one or two small LLM calls per conversation, with automatic failover between Groq and Gemini, and full conversation logging.

### Phase 5: Online Ordering

Objectives: let logged-in customers browse the menu, build a cart, place an order, and track its status.

Tasks:
- Frontend: menu browsing page with category filters, item detail view, add-to-cart, persistent cart (Zustand/Redux, synced to backend on checkout).
- Backend: `POST /orders` (authenticated) accepting a list of `{menu_item_id, quantity}`, validating item availability and current price server-side (never trust client-submitted prices), computing `total_amount`, and creating the order with status `placed`.
- `GET /orders/me` for customers to see their order history and live status, and staff-only `GET /orders` with filters (status, date range) plus `PATCH /orders/{id}` to progress status (placed to preparing to ready to completed).
- Optional dine-in linkage: allow an order to be attached to an active booking so the dashboard can later report on booking-to-order conversion.
- No real payment gateway integration is required for this phase since the requirement is free-tier tooling; implement a "pay at counter" / "pay on pickup" flow, and clearly document in the README how a free-tier-compatible payment provider (e.g. Stripe test mode) could be added later without changing the order schema.
- Add basic email or in-app notification on order status change (in-app is sufficient; email can use a free transactional email tier such as Resend's free tier if desired).

Deliverable: a working end-to-end ordering flow with server-side price and availability validation, visible order status tracking, and staff-side order management.

### Phase 6: Public-Facing Frontend (Fortune 100-Grade Website)

Objectives: build a public website that reads as a premium, professionally produced brand site, not a developer demo.

Pages and content requirements:
- Home page: full-bleed hero section with high-quality ambience photography or a short looping video, a concise brand statement, a visible primary call to action ("Book a table" and "Order online"), and a persistent, clearly visible "Log in" link/button in the top navigation at all times.
- Ambience/Gallery page: curated, categorized photo gallery (interior, seating areas, coffee bar, outdoor seating if applicable), presented in a refined masonry or lightbox grid, not a plain image dump.
- Menu page: full categorized menu with images, descriptions, dietary tags (vegetarian, vegan, gluten-free where applicable), price, and the semantic search bar from Phase 3 for natural-language browsing ("something warm and spiced").
- About/Story page: brand narrative, sourcing philosophy, founder or team note, values, written in a professional editorial tone.
- Location and Hours page: embedded map, address, opening hours, contact details, and directions.
- Book a Table page: both the chatbot entry point and a manual visual picker (date, party size, table/area preference, available time slots as clickable chips) so users can complete a booking without the chatbot if they prefer.
- Persistent footer with social links, newsletter signup (can be a simple email capture endpoint), and legal/privacy links.

Design execution requirements:
- Establish a formal design system before building pages: a defined color palette (primary, secondary, neutral, semantic colors for success/error/warning), a type scale using two complementary Google Fonts (one serif or display for headings, one clean sans for body), consistent spacing scale, and consistent border-radius/shadow tokens, implemented as Tailwind theme extensions rather than ad hoc utility classes.
- Fully responsive layout tested at mobile, tablet, and desktop breakpoints, with special attention to the navigation bar, gallery grid, and chat widget on small screens.
- Subtle, purposeful motion (fade/slide-in on scroll, smooth hover states) using Framer Motion, applied consistently rather than decoratively.
- Real, on-brand imagery throughout; no generic stock icons or placeholder gray boxes should reach the final build.
- Accessibility basics: sufficient color contrast, alt text on all images, keyboard-navigable menus and forms, semantic HTML landmarks.
- A visible, consistent "Log in" entry point in the header on every public page, leading to the authentication flow from Phase 2, and redirecting authenticated customers to their account area (bookings, orders) and authenticated staff to the dashboard.

Deliverable: a fully responsive, professionally designed public website covering all pages above, connected to the real backend APIs (menu, availability, chatbot), with no mock or placeholder content remaining.

### Phase 7: Revenue and Operations Dashboard

Objectives: give the owner a genuine, data-backed view of business performance.

Tasks:
- Backend analytics endpoints (staff-only), all computed from real `orders`, `order_items`, and `bookings` tables with proper date filtering and aggregation at the database level (not pulled raw and aggregated in Python):
  - `GET /analytics/revenue?range=` returning total revenue, order count, and average order value for day/week/month/custom range, plus a time series for charting.
  - `GET /analytics/top-items?range=` returning best-selling items by quantity and by revenue.
  - `GET /analytics/table-utilization?range=` returning booking counts and occupancy rate per table and per time slot, to reveal peak hours and underused tables.
  - `GET /analytics/conversion?range=` returning the ratio of bookings that resulted in a linked order, and chatbot-originated versus manually-created booking counts.
- Frontend dashboard (staff-only route): summary cards (today's revenue, today's bookings, active orders), a revenue trend chart, a top-selling-items chart, a table utilization heatmap by hour/day, and a filterable, sortable table of recent orders and bookings.
- Add date-range filtering (today, this week, this month, custom) shared consistently across all dashboard widgets.
- Ensure every chart and number is backed by a live query against real data, with the seed/demo data clearly excludable via the `source` flag described in Section 4.2, so the dashboard is trustworthy from day one of real operation.

Deliverable: a staff-only dashboard presenting accurate, real-time business metrics, with clear separation between demo/seed data and live data.

### Phase 8: Security Hardening, Testing, and Deployment

Objectives: make the system production-ready.

Tasks:
- Run a full security pass: confirm all secrets are environment-variable driven, confirm CORS is locked to the production frontend origin, confirm rate limiting is active on auth and chat endpoints, confirm all staff-only endpoints reject non-admin tokens, and confirm SQL is only ever executed through the ORM.
- Write automated backend tests (pytest) covering authentication, booking concurrency, order price validation, and the LLM failover logic (mocked provider responses).
- Write frontend tests (Vitest/React Testing Library) for the booking flow, cart/checkout flow, and auth-guarded routing.
- Set up structured logging (request id, user id where available, latency, LLM provider used per chat turn) to a free-tier-compatible logging destination or simple file/DB logging if no external service is used.
- Deploy backend and database to the chosen free-tier hosting platform, deploy the frontend to the chosen free static hosting platform, and configure environment variables in each platform's dashboard rather than in code.
- Configure automatic HTTPS and confirm the CORS and cookie settings work correctly across the deployed domains.
- Perform a final load-sanity check on the booking concurrency path and on chatbot response latency under the free-tier LLM rate limits, and tune the Redis-based quota tracking accordingly.

Deliverable: a deployed, publicly reachable, secured application, with automated tests passing in CI and a documented deployment process.

### Phase 9: Documentation and Handover

Objectives: leave behind documentation that lets any developer understand, run, and extend the system without external help.

Tasks:
- Write a top-level `README.md` covering: project description, architecture diagram (text or embedded image), full tech stack list, prerequisites, local setup instructions (`docker compose up`, migrations, seed scripts), environment variable reference table, how to run tests, how to switch or add LLM providers, and how to deploy.
- Write a `backend/README.md` covering API structure, folder layout, and how authentication/authorization is implemented.
- Write a `frontend/README.md` covering component structure, design system tokens, and state management approach.
- Generate and publish the FastAPI automatic OpenAPI documentation (`/docs`) as the live API reference.
- Document the dataset provenance and seed/reset process directly in the README, referencing Section 4 of this plan.
- Document the LLM token-minimization strategy explicitly (local intent classification first, semantic retrieval before generation, structured extraction with capped output tokens, provider failover) so future maintainers do not regress into sending full conversation histories to the LLM on every turn.
- Maintain a `CHANGELOG.md` from the first release onward.

Deliverable: complete, clear, professional documentation such that a new developer can clone the repository and have a fully working local environment within a short, well-defined setup sequence.

## 6. Summary of Delivery Order

Phase 0 through Phase 2 establish the secured foundation. Phase 3 and Phase 4 build the core booking and chatbot capability with a strict token-minimization design. Phase 5 adds ordering. Phase 6 delivers the premium public website. Phase 7 delivers the real revenue dashboard. Phase 8 and Phase 9 harden, deploy, and document the system for long-term maintenance. Each phase should be fully tested and demoable before the next phase begins.
