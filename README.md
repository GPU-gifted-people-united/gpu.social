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
