# 🏠 Price Tracker — Home Essentials Price Monitoring

An automated Amazon price tracker built with Python to monitor the prices of home essentials, store price history, and send Telegram notifications whenever significant price drops are detected.

The project was designed to run continuously on an Oracle Cloud instance, with automated price checks every hour.

## ✨ Features

- 🔎 **Price monitoring:** automated price checks for products listed on Amazon Brazil.
- 📊 **Price history:** stores previously collected prices in an SQLite database.
- 📉 **Price drop detection:** identifies price reductions based on a configurable percentage threshold.
- 📲 **Telegram notifications:** sends alerts when products meet the configured price drop criteria.
- 🤖 **Interactive Telegram bot:** allows users to check products and price history through a Telegram menu.
- ⏰ **Automated execution:** schedules hourly price checks using cron.
- ☁️ **Cloud deployment:** hosted on Oracle Cloud with Ubuntu Server.
- 🔄 **Continuous operation:** uses systemd to keep the Telegram bot running and automatically restart it if it fails.

## 🛠️ Technologies

| Technology | Application |
|---|---|
| Python | Main programming language |
| Playwright | Browser automation and price extraction |
| Microsoft Edge | Browser used for automation |
| SQLite | Price history storage |
| python-telegram-bot | Telegram integration |
| python-dotenv | Environment variable management |
| Linux / Ubuntu | Execution environment |
| cron | Automated task scheduling |
| systemd | Background service management |
| Oracle Cloud | Cloud infrastructure |

## 📁 Project Structure

```text
price_tracker/
│
├── main.py                  # Price monitoring and comparison
├── scraper.py               # Amazon price extraction
├── database.py              # Database operations
├── bot_telegram.py          # Interactive Telegram bot
├── ver_banco.py             # Database inspection
├── products.csv             # List of monitored products
├── prices.db                # SQLite database
├── .env                     # Environment variables (do not commit)
├── README.md                # Project documentation
│
├── tracker.log              # Monitoring logs
├── bot_telegram.log         # Telegram bot logs
└── cron.log                 # Scheduled execution logs
```

## ⚙️ Installation and Configuration

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/price_tracker.git
cd price_tracker
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install playwright python-telegram-bot python-dotenv
```

### 4. Install the browser

The project uses Microsoft Edge with Playwright. Install Edge on your system and verify its availability:

```bash
microsoft-edge --version
```

Browser installation requirements may vary depending on the operating system.

### 5. Configure environment variables

Create a `.env` file in the project root:

```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
TELEGRAM_ALERT_CHAT_ID=your_group_id
```

These variables are used to authenticate the Telegram bot and define where notifications are sent.

**Important:** never commit your `.env` file, tokens, or credentials to GitHub.

## 🛍️ Product Registration

Products are listed in the `products.csv` file, which contains the information required for monitoring, including product names and URLs.

Illustrative example:

```csv
nome,url
STOVE,https://www.amazon.com.br/dp/EXAMPLE
AIRTIGHT CONTAINER,https://www.amazon.com.br/dp/EXAMPLE2
```

Keep the column names and file structure compatible with the current project implementation.

## ▶️ Usage

### Price monitoring

To run a manual price check:

```bash
python main.py
```

The script retrieves the listed products, extracts their current prices, compares them against previous records, and identifies potential price drops.

### Telegram bot

To start the bot manually:

```bash
python bot_telegram.py
```

The bot provides access to the available features through Telegram.

## 📉 Price Drop Threshold

The minimum price drop percentage can be adjusted directly in `main.py`.

Example:

```python
if queda_percentual >= 5:
```

In this example, price reductions of 5% or more meet the alert condition.

The comparison baseline depends on the price comparison logic implemented in the monitoring script.

## ☁️ Oracle Cloud Deployment

The project was deployed on an Oracle Cloud instance running Ubuntu Server, using a Python virtual environment and automated execution.

### Scheduling with cron

Price monitoring is scheduled to run every hour.

Example configuration:

```bash
0 * * * * cd /home/ubuntu/price_tracker && /usr/bin/flock -n /tmp/price_tracker.lock /home/ubuntu/price_tracker/.venv/bin/python main.py >> /home/ubuntu/price_tracker/cron.log 2>&1
```

The `flock` command prevents overlapping executions if a price check takes longer than one hour.

To inspect scheduled tasks:

```bash
crontab -l
```

To monitor execution logs:

```bash
tail -f ~/price_tracker/cron.log
```

### Running the Telegram bot with systemd

The bot runs as a system service, allowing it to remain active after the SSH session is closed.

Service configuration:

```ini
[Unit]
Description=Bot Telegram Price Tracker
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/price_tracker
ExecStart=/home/ubuntu/price_tracker/.venv/bin/python /home/ubuntu/price_tracker/bot_telegram.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Useful commands:

Enable and start the service:

```bash
sudo systemctl enable --now price-tracker-bot
```

Check service status:

```bash
sudo systemctl status price-tracker-bot
```

View service logs:

```bash
sudo journalctl -u price-tracker-bot -f
```

## 🗄️ Database

Price history is stored locally in an SQLite database named `prices.db`.

The database enables price comparisons over time and provides access to previous records without relying on an external database service.

## 🔐 Security

- Do not commit the `.env` file.
- Never expose Telegram bot tokens.
- Use environment variables to store sensitive information.
- Protect cloud instance access and project files.
- Keep backups of the price history database.

## 🚀 Project Goal

This project was developed to simplify price tracking for a residential move by automating the identification of purchasing opportunities and centralizing notifications in a single channel.

Beyond its practical application, the project explores Python automation, web scraping, data persistence, API integration, and cloud application deployment.

---

**Built with Python, automation, and one goal: saving money on a new home. 🏡**
