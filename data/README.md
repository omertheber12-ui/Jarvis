# Data Directory

Runtime artifacts live under `data/` so they stay out of the repo root:

- `storage/` – conversation history and other persisted state.
- `credentials/` – OAuth credentials and refresh tokens.
- `logs/` – application log output.

These files are git-ignored by default. Create the directories if they are
missing whenever you deploy the application.

