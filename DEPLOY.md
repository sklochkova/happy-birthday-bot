# Deployment Guide: Google Cloud e2-micro (Free Tier)

This guide walks you through deploying the Happy Birthday Bot on a Google Cloud Compute Engine **e2-micro** instance, which is part of the **Always Free** tier.

---

## Prerequisites

- A Google Cloud account — sign up at https://cloud.google.com/free
- `gcloud` CLI installed locally — https://cloud.google.com/sdk/docs/install
- A Telegram Bot token from [@BotFather](https://t.me/BotFather)
- Your Telegram user ID (for `BOT_OWNER_ID`) — get it from [@userinfobot](https://t.me/userinfobot)

---

## 1. Create the VM Instance

Authenticate and set your project:

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

Create a free-tier eligible e2-micro instance:

```bash
gcloud compute instances create birthday-bot \
    --machine-type=e2-micro \
    --zone=us-central1-a \
    --image-family=debian-12 \
    --image-project=debian-cloud \
    --boot-disk-size=10GB \
    --boot-disk-type=pd-standard
```

> **Free tier note:** 1x e2-micro instance is free in `us-west1`, `us-central1`, or `us-east1` regions. The 10GB standard persistent disk is within the free 30GB allowance.

---

## 2. SSH into the Instance

```bash
gcloud compute ssh birthday-bot --zone=us-central1-a
```

---

## 3. Install System Dependencies

```bash
sudo apt update && sudo apt install -y python3 python3-venv python3-pip git
```

Verify Python version (should be 3.11+):

```bash
python3 --version
```

---

## 4. Create a Dedicated User

```bash
sudo useradd -r -m -s /bin/bash botuser
```

---

## 5. Clone the Repository

```bash
sudo -u botuser git clone YOUR_REPO_URL /home/botuser/birthday-bot
```

If not using git, you can upload files via SCP:

```bash
# Run this from your LOCAL machine
gcloud compute scp --recurse ./bot ./requirements.txt ./.env.example \
    birthday-bot:/home/botuser/birthday-bot/ --zone=us-central1-a
```

---

## 6. Set Up Python Virtual Environment

```bash
sudo -u botuser bash -c '
    cd /home/botuser/birthday-bot
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
'
```

---

## 7. Configure the Environment

```bash
sudo -u botuser cp /home/botuser/birthday-bot/.env.example /home/botuser/birthday-bot/.env
sudo -u botuser nano /home/botuser/birthday-bot/.env
```

Fill in your values:

```
BOT_TOKEN=your_actual_bot_token_here
BOT_OWNER_ID=your_telegram_user_id
DB_PATH=data/birthdays.db
DEFAULT_TIMEZONE=UTC
DEFAULT_GREETING_TIME=09:00
LOG_LEVEL=INFO
```

---

## 8. Test the Bot Manually

```bash
sudo -u botuser bash -c '
    cd /home/botuser/birthday-bot
    .venv/bin/python -m bot
'
```

Send `/start` to the bot in a Telegram group. If it responds, proceed to the next step. Press `Ctrl+C` to stop.

---

## 9. Create a systemd Service

```bash
sudo tee /etc/systemd/system/birthday-bot.service > /dev/null << 'EOF'
[Unit]
Description=Happy Birthday Telegram Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/home/botuser/birthday-bot
ExecStart=/home/botuser/birthday-bot/.venv/bin/python -m bot
Restart=always
RestartSec=5
EnvironmentFile=/home/botuser/birthday-bot/.env

[Install]
WantedBy=multi-user.target
EOF
```

---

## 10. Enable and Start the Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable birthday-bot
sudo systemctl start birthday-bot
```

Check that it's running:

```bash
sudo systemctl status birthday-bot
```

You should see `Active: active (running)`.

---

## 11. View Logs

Real-time logs:

```bash
sudo journalctl -u birthday-bot -f
```

Logs from the last hour:

```bash
sudo journalctl -u birthday-bot --since "1 hour ago"
```

---

## 12. Updating the Bot

```bash
# Pull latest code
sudo -u botuser bash -c 'cd /home/botuser/birthday-bot && git pull'

# Install any new dependencies
sudo -u botuser bash -c 'cd /home/botuser/birthday-bot && .venv/bin/pip install -r requirements.txt'

# Restart the service
sudo systemctl restart birthday-bot
```

---

## 13. Database Backup

The SQLite database is stored at `data/birthdays.db`. To create a backup:

```bash
sudo -u botuser cp /home/botuser/birthday-bot/data/birthdays.db \
    /home/botuser/birthday-bot/data/birthdays.db.bak
```

For automated daily backups, add a cron job:

```bash
sudo -u botuser crontab -e
```

Add:

```
0 3 * * * cp /home/botuser/birthday-bot/data/birthdays.db /home/botuser/birthday-bot/data/birthdays.db.bak
```

---

## Firewall Notes

- **No inbound ports are needed.** The bot uses long polling (outbound HTTPS requests only).
- The default Google Cloud firewall rules are sufficient. No additional configuration required.

---

## Costs

With the Always Free tier, you pay **$0/month** for:

| Resource | Free Allowance | Bot Usage |
|----------|---------------|-----------|
| e2-micro VM | 1 instance in select US regions | 1 instance |
| Boot disk | 30 GB standard | 10 GB |
| Network egress | 1 GB/month to most regions | Minimal (text messages) |

> **Important:** Stay within the free tier limits to avoid charges. Monitor usage in the [Google Cloud Console](https://console.cloud.google.com/billing).

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Bot doesn't start | Check logs: `journalctl -u birthday-bot -n 50` |
| `BOT_TOKEN` error | Verify `.env` file has the correct token |
| Python version too old | Install Python 3.11+ from deadsnakes PPA |
| Permission denied on DB | Check `data/` dir ownership: `chown -R botuser:botuser data/` |
| Bot stops responding | Check `systemctl status birthday-bot`, restart if needed |
| Out of memory | e2-micro has 1 GB RAM; check with `free -m`, add swap if needed |

### Adding Swap Space (recommended for e2-micro)

```bash
sudo fallocate -l 512M /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```
