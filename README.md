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

Photographic surreal worlds and clear actions: Explore / Add a project / Join us / Community, with a separate PEOPLE page at /workshop/people/ (RU) and /en/people/ (EN). Public project detail pages are generated from the published catalogue, with sharing and bilingual metadata.

Reviewed updates live in updates.json. Run `python3 scripts/build_feed.py` to rebuild /workshop/feed.json and /workshop/feed.xml. Feeds never read the private submissions table. PEOPLE profiles are added only after a contribution and consent.

See CONTRIBUTING.md for a quick start and starter tasks.

Project cards copy ready-to-share public text and a GPU project-page link. The Community section tells the origin story and offers a short assistant command; it is collapsed until opened.
