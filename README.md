# GPU Workshop

Live: https://gpu.social/ (Russian), https://gpu.social/en/ (English).

Python standard library + SQLite. No build or runtime packages needed.

Run `python3 server.py`, open http://127.0.0.1:9327/workshop/.
Run API tests with `python3 test_api.py`.

Data defaults to `data/workshop.sqlite3`; set GPU_DB in production.
`manage.py` is the SSH-only moderation interface (see `--help`).
Contacts are never part of the public project schema. Source bundles must exclude data/.

Deployment: code in /opt/gpu-workshop/current, dedicated systemd DynamicUser service,
persistent StateDirectory /var/lib/gpu-workshop, Caddy routes /, /en/*, and /workshop/*.
Keep projects.json in every release; the service reads it at startup.
English project descriptions live in EN_PROJECTS in server.py. Add a translation there when publishing a new project.
User-facing operations and launch notes are in outputs/GPU-WORKSHOP.md in the owning workspace.

## GPU UI

A dark night-sky design with one warm accent and two hero actions (Explore projects / Add a project), followed by Projects, Get involved, Community, What’s new and Agreements, with a separate PEOPLE page at /workshop/people/ (RU) and /en/people/ (EN). Public project detail pages are generated from the published catalogue, with sharing and bilingual metadata.

Reviewed updates live in updates.json. Run `python3 scripts/build_feed.py` to rebuild /workshop/feed.json and /workshop/feed.xml. Feeds never read the private submissions table. PEOPLE profiles are added only after a contribution and consent.

See CONTRIBUTING.md for a quick start and starter tasks.

Project cards copy ready-to-share public text and a GPU project-page link. The Community section tells the origin story; the assistant command lives in the Get involved section.

The Dot command authorises scoped daily support through accounts connected by each participant, with an optional review-first instruction. Add public social-post URLs to an update's `social_posts` list (or its summary) so Dot has exact posts to read; entries without social-post URLs are skipped. JSON retains the reviewed update fields. Never add private account data or instructions to the feed. Users control access and approvals in Dot. The owner reported testing the LinkedIn workflow; that is not a guarantee for every account or platform.

GA4 records `dot_prompt_copy_click` for either Dot copy button, with language and placement only. This measures button presses, not successful clipboard writes or Dot activation. Browser-level analytics blocking may exclude some presses.

English project titles and maker names are mapped in EN_TITLES and EN_AUTHORS in server.py. The catalogue API and detail pages use the same localisation so sharing and metadata match the visible title.

## News, search and subscriptions

The public catalogue and news are rendered in HTML by public_pages.py, then enhanced by app.js. Public routes include /workshop/news/ID/, /en/news/ID/, /robots.txt and /sitemap.xml. Pages have canonical and reciprocal hreflang links. Project facts live in public/project-details.json; update facts and their editorial date when reviewing a project. Hidden projects are excluded from discovery.

updates.json remains the reviewed editorial source. The newsletter worker additionally groups newly published catalogue projects after a quiet 15-minute window into runtime_updates in the private SQLite database. The deployment baseline prevents announcing the old catalogue to new subscribers. All public feeds/pages merge these records; they never read pending submissions or subscriber contacts. Fresh approvals therefore become one shared news item, subscription email and ready-to-copy post. Existing update IDs are stable.

Email setup requires GPU_SUBSCRIBE_SECRET (a persistent random key), GPU_SMTP_HOST, GPU_SMTP_PORT and GPU_MAIL_FROM. Production uses the existing loopback Postfix relay and signed agent.gpu.social sender. Keep configuration in /etc/gpu-workshop/notifications.env, outside Git, loaded by the web service and gpu-newsletter.service. External relays may additionally use GPU_SMTP_SSL or GPU_SMTP_STARTTLS and GPU_SMTP_USER/GPU_SMTP_PASSWORD. Never use plaintext external SMTP. The queue runs from gpu-newsletter.timer once a minute and retries transient delivery failures with backoff. No Telegram bot is configured; the community link remains available.

Email subscriptions require an explicit confirmation POST from the emailed link. Until confirmation no news is sent. Old news is not broadcast on joining. Every news email includes an unsubscribe link and one-click unsubscribe headers; GET alone does not confirm or unsubscribe. Private token pages do not load analytics. Tokens are signed and versioned, confirmation expires in 48 hours, and subscriptions and job records stay out of public APIs. A stopped subscription suppresses future delivery. As with SMTP queues generally, a crash after provider acceptance but before recording success can produce a retry; stable Message-ID and unique delivery records reduce duplicates.

Private commands:

- `python3 manage.py notify` — process announcements and the delivery queue (systemd normally runs this).
- `python3 manage.py newsletter-status` — aggregate subscriber/job states without addresses.
- `python3 manage.py posts UPDATE_ID --lang en` — prepare a complete social post from public project data.
- `python3 manage.py social UPDATE_ID --platform LinkedIn --url https://www.linkedin.com/posts/...` — attach an already published public post to the news, website, emails and agent feed. Use a canonical LinkedIn URL or t.me post URL. Dot checks newly added post URLs even when the news item already existed.

GA4 preserves dot_prompt_copy_click and adds newsletter_open, newsletter_signup_request, support_post_click and project_website_click without addresses or subscription tokens. Validate delivery with an explicitly authorised test address. Do not use submission contacts as a mailing list.

## Categories and organic discovery

The six shared groups and bilingual editorial introductions live in public/categories.json.
Known projects have stable group membership; new projects can use a group label or ID,
with legacy categories recognised automatically. Keep B2B as the internal category for
business contact actions. Update the mapping when moderating a project with an unusual category.

The home catalogue combines all projects with six filters and search within the selected group.
Category links also work without JavaScript and lead to permanent RU/EN HTML collections
at /workshop/categories/ID/ and /en/categories/ID/. Each nonempty collection has its own
canonical, reciprocal hreflang, description, ItemList schema and sitemap entry.
Project pages link to their category and other published projects in that group.
category_filter_click in GA4 records group IDs and language, never search text.

SEO/GEO verification: test HTML without JS, matching visible/schema counts, translations,
hidden-project exclusion, canonical and reciprocal language links, sitemap and crawler access.
These checks establish crawlability, not proof of indexing or rankings. Use the owner's
Google Search Console and Bing Webmaster Tools for index coverage and actual search queries.
Add the existing sitemap there once ownership is verified; do not invent a verification token.
For editorial growth, prefer real demos and maker-written use cases over generated keyword pages.

## Project stories

public/stories.json stores bilingual editorial guides: reviewed facts, step-by-step use cases,
public source links and a post draft linking directly to each guide. Stories are published
only while their project is visible in the catalogue. Routes: /workshop/stories/SLUG/
and /en/stories/SLUG/, plus archives. HTML, metadata and Article schema share the same source.
Project pages, relevant news, RSS/JSON and the sitemap link to the guides.
Existing news IDs remain unchanged, so editorial expansion does not resend an old announcement.

Keep interviews separate from editorial guides: do not invent a maker's motivation, quotes,
usage metrics, testimonials or personal experience. Label the source of each guide.
Demo screenshots must come from a real check; do not present an App Store listing as a hands-on review.
Each guide has a ready-to-copy RU/EN post. Publishing social posts still follows the owner's chosen workflow.

The story archive also accepts kind=story submissions using the existing private moderation inbox,
input validation and rate limit. They are never automatically inserted into public stories or feeds.
