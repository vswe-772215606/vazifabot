# Vazifabot

A simple task list bot for Telegram, in Uzbek. Anyone can use it, and every user gets a list of their own.

- Send any text and it becomes a task. A message with several lines adds one task per line.
- **Vazifalar** shows the list. Tap a task to mark it done, tap again to reopen it.
- **O'chirish** deletes a task. **Bajarilganlarni tozalash** removes the done ones.
- Commands: `/start`, `/vazifalar`, `/yordam`.
- Limits: 30 tasks per user, 100 characters per task, so one list always fits in one Telegram message.

Tasks are stored in a single SQLite file (`data/tasks.db`). The bot uses long polling, so the server needs no domain and no open port.

## Run on your laptop

```sh
cp .env.example .env        # then put the token from @BotFather in it
uv run --env-file .env vazifabot
uv run pytest               # tests
```

A token can serve only one running copy. Stop the laptop copy before starting the server one, or Telegram answers with `409 Conflict`.

## Run on the server (Ubuntu 24.04)

Run as root on the server:

```sh
# 1. uv, installed system-wide
curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh

# 2. a user of its own, and the code in its home
useradd --system --create-home --shell /usr/sbin/nologin vazifabot
git clone <your GitHub repo URL> /home/vazifabot/app
chown -R vazifabot:vazifabot /home/vazifabot/app

# 3. the token: type it on the server, never commit it
cd /home/vazifabot/app
cp .env.example .env && nano .env
chmod 600 .env && chown vazifabot:vazifabot .env

# 4. install, then keep it running and start it with the server
sudo -u vazifabot uv sync --frozen --no-dev
cp deploy/vazifabot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now vazifabot

# check it
systemctl status vazifabot
journalctl -u vazifabot -f
```

To update later: `git pull`, then `sudo -u vazifabot uv sync --frozen --no-dev`, then `systemctl restart vazifabot`.

## The token

The token in `.env` is the bot's password. `.gitignore` keeps it out of git. If it ever leaks (a screenshot, a recording, a commit), send `/revoke` to @BotFather, take the new token, and update `.env`.
