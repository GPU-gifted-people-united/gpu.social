# Build GPU together

GPU is our shared home. Pick a useful change, open a pull request, and explain what it improves. No assigned roles.

## Run locally

- Python 3.10+; no runtime packages needed.
- `python3 server.py`, then http://127.0.0.1:9327/workshop/.
- `python3 test_api.py` checks persistence, privacy and public routes.
- `node --check public/app.js` checks JavaScript syntax.
- Check Russian, English and a phone viewport before submitting UI changes.

## Where things live

- `public/index.html` and `public/index-en.html`: home pages.
- `public/people.html` and `public/people-en.html`: PEOPLE.
- `public/people.json`: consenting contributors and their public links. Add profiles after an accepted contribution, with the person's approval. Do not infer membership from project authorship.
- `public/style.css`, `public/expedition.svg`: visual design.
- `public/app.js`: catalogue, forms, feed, prompt and sharing.
- `updates.json`: reviewed public updates. IDs must remain stable. Run `python3 scripts/build_feed.py` after editing; commit both generated feeds.
- `server.py`: public project pages, API and private submissions.
- `projects.json`: initial projects; published projects live in the server database. English translations are in `EN_PROJECTS`.

## Small starter tasks

- Record a short demo of a project with its maker.
- Improve one RU/EN explanation.
- Propose an accessibility or mobile layout improvement.
- Make sharing a specific project easier.
- Write a useful public update for the expedition log.

Projects remain their authors' property. The site's code licence is not yet selected; do not assume permission to reuse it beyond contributions. Major changes are discussed together. Never commit databases, contact details, private submissions, credentials or deployment keys.

Main requires maintainer/code-owner review and CI. After checks on an accepted main commit pass, the Deploy workflow sends an archive using a key restricted to the server release receiver. The receiver validates paths, backs up SQLite, switches releases and checks health; it restores the previous release on health failure. Deployment keys and private data stay outside the repository.
