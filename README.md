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
