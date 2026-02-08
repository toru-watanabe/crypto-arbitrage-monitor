# 📦 Installation Guide - Crypto Arbitrage Monitor

Complete step-by-step guide to install and run the Crypto Arbitrage Monitor on Windows.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Steps](#installation-steps)
3. [Configuration](#configuration)
4. [Starting the System](#starting-the-system)
5. [Accessing Services](#accessing-services)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

1. **Docker Desktop for Windows**
   - Download from: https://www.docker.com/products/docker-desktop/
   - Version: 4.0.0 or higher
   - Ensure WSL 2 backend is enabled

2. **System Requirements**
   - Windows 10/11 (64-bit)
   - At least 8GB RAM
   - 10GB free disk space
   - Internet connection

### Optional (for Telegram notifications)

- Telegram account
- Telegram bot token (from @BotFather)

---

## Installation Steps

### Step 1: Verify Docker Installation

Open PowerShell and verify Docker is installed:

```powershell
docker --version
docker-compose --version
```

Expected output:
```
Docker version 24.x.x
Docker Compose version v2.x.x
```

### Step 2: Navigate to Project Directory

```powershell
cd D:\crypto-arbitrage-monitor
```

### Step 3: Verify Project Files

Check that all files are present:

```powershell
ls
```

You should see:
- `docker-compose.yml`
- `Dockerfile`
- `requirements.txt`
- `.env`
- `.env.example`
- `src/` directory
- `airflow/` directory
- `scripts/` directory

---

## Configuration

### Step 1: Review Environment Variables

The `.env` file is already configured with your Bybit API credentials:

```bash
BYBIT_API_KEY=kOgFNe6wab1hBKezE7
BYBIT_API_SECRET=123456
```

### Step 2: (Optional) Configure Telegram Notifications

If you want Telegram notifications, follow these steps:

#### Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` command
3. Follow the prompts to create your bot
4. **Save the bot token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

#### Get Your Chat ID

1. Send a message to your new bot (any message)
2. Open this URL in your browser (replace `<YOUR_BOT_TOKEN>`):
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
3. Look for `"chat":{"id":123456789}` in the response
4. **Save the chat ID** (the number after `"id":`)

#### Update .env File

Edit `D:\crypto-arbitrage-monitor\.env` and update:

```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### Step 3: Customize Monitoring Settings (Optional)

Edit `.env` to adjust these settings:

```bash
# Add or remove coins (comma-separated)
COINS=BTC,ETH,BNB,SOL,TRX,DOGE,ADA

# Scraping interval in seconds (default: 60)
SCRAPE_INTERVAL=60

# Minimum profit to trigger notification (default: 0.5%)
MIN_PROFIT_THRESHOLD=0.5

# Exchange fees in percentage
BYBIT_FEE=0.1
BINANCE_FEE=0.1
KUCOIN_FEE=0.1
```

---

## Starting the System

### Step 1: Build and Start Containers

From the project directory, run:

```powershell
docker-compose up -d
```

This command will:
- Download required Docker images (~2-5 minutes first time)
- Build the application container
- Start all services in the background

Expected output:
```
[+] Running 7/7
 ✔ Container crypto-arbitrage-monitor-redis-1              Running
 ✔ Container crypto-arbitrage-monitor-timescaledb-1        Running
 ✔ Container crypto-arbitrage-monitor-airflow-init-1       Started
 ✔ Container crypto-arbitrage-monitor-airflow-webserver-1  Running
 ✔ Container crypto-arbitrage-monitor-airflow-scheduler-1  Running
 ✔ Container crypto-arbitrage-monitor-dashboard-1          Running
```

### Step 2: Wait for Initialization

First startup takes 2-3 minutes for Airflow initialization. Check status:

```powershell
docker-compose ps
```

All services should show "Up" or "running" status.

### Step 3: Initialize Database

Run the database setup script:

```powershell
docker-compose exec dashboard python scripts/setup_databases.py
```

Expected output:
```
============================================================
DATABASE INITIALIZATION
============================================================

1. Initializing TimescaleDB...
✅ TimescaleDB is accessible
✅ TimescaleDB schema created

============================================================
✅ DATABASE INITIALIZATION COMPLETE
============================================================
```

---

## Accessing Services

### 1. **Dashboard** (Main Interface)

- **URL**: http://localhost:8050
- **Description**: Interactive visualization dashboard
- **Auto-refresh**: Every 10 seconds

### 2. **Airflow UI** (Workflow Management)

- **URL**: http://localhost:8080
- **Username**: `admin`
- **Password**: `admin`
- **Description**: Monitor and manage the scraping workflow

#### Enable the DAG

1. Open Airflow UI
2. Find `crypto_arbitrage_monitor` DAG
3. Toggle the switch to **ON** (should turn blue/green)
4. The DAG will start running automatically

### 3. **TimescaleDB** (Database)

- **Host**: localhost
- **Port**: 5432
- **Database**: `arbitrage_monitor`
- **Username**: `postgres`
- **Password**: `postgres123`

Connect using any PostgreSQL client (e.g., pgAdmin, DBeaver)

### 4. **Redis** (Cache)

- **Host**: localhost
- **Port**: 6379
- **Database**: 0

---

## Verification

### Verify All Services are Running

```powershell
docker-compose ps
```

All containers should be "Up".

### Check Logs

```powershell
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# Specific service logs
docker-compose logs dashboard
docker-compose logs airflow-scheduler
```

### Test Individual Components

#### Test Scrapers

```powershell
# Test Bybit scraper
docker-compose exec dashboard python -m src.scrapers.bybit_scraper

# Test Binance scraper
docker-compose exec dashboard python -m src.scrapers.binance_scraper

# Test KuCoin scraper
docker-compose exec dashboard python -m src.scrapers.kucoin_scraper
```

Expected output: Price data for BTC and ETH from each exchange

#### Test Telegram Notifications

```powershell
docker-compose exec dashboard python -m src.notifications.notifier
```

If configured correctly, you should receive a test message on Telegram.

### Verify Dashboard is Working

1. Open http://localhost:8050
2. You should see:
   - Statistics cards at the top
   - Opportunities table (may be empty initially)
   - Price comparison charts
   - Arbitrage heatmap

3. Wait ~60 seconds for the first data to appear

### Verify Airflow DAG is Running

1. Open http://localhost:8080
2. Login with `admin` / `admin`
3. Click on `crypto_arbitrage_monitor` DAG
4. You should see:
   - DAG is enabled (toggle is ON)
   - Recent runs appearing in the graph
   - All tasks turning green (success)

---

## Troubleshooting

### Issue: Containers won't start

**Solution:**

1. Check Docker Desktop is running
2. Verify ports are not in use:
   ```powershell
   netstat -ano | findstr :8050
   netstat -ano | findstr :8080
   netstat -ano | findstr :5432
   netstat -ano | findstr :6379
   ```
3. If ports are in use, stop conflicting services or change ports in `docker-compose.yml`

### Issue: Airflow DAG not appearing

**Solution:**

1. Check scheduler logs:
   ```powershell
   docker-compose logs airflow-scheduler
   ```
2. Ensure DAG file exists:
   ```powershell
   ls airflow\dags\arbitrage_monitor_dag.py
   ```
3. Restart Airflow:
   ```powershell
   docker-compose restart airflow-scheduler airflow-webserver
   ```

### Issue: Dashboard shows no data

**Solution:**

1. Ensure Airflow DAG is enabled and running
2. Check if data is in Redis:
   ```powershell
   docker-compose exec redis redis-cli
   > KEYS *
   > exit
   ```
3. Manually trigger DAG from Airflow UI (click play button)
4. Check dashboard logs:
   ```powershell
   docker-compose logs dashboard
   ```

### Issue: Telegram notifications not working

**Solution:**

1. Verify bot token and chat ID in `.env`
2. Test the bot manually:
   ```powershell
   docker-compose exec dashboard python -m src.notifications.notifier
   ```
3. Check logs for errors:
   ```powershell
   docker-compose logs dashboard | Select-String "Telegram"
   ```
4. Verify bot token at: `https://api.telegram.org/bot<YOUR_TOKEN>/getMe`

### Issue: "No such file or directory" errors

**Solution:**

This usually means Windows line endings vs. Unix line endings.

1. Install dos2unix converter or use Git:
   ```powershell
   git config --global core.autocrlf input
   ```
2. Rebuild containers:
   ```powershell
   docker-compose down
   docker-compose up -d --build
   ```

### Issue: High CPU/Memory usage

**Solution:**

1. Reduce scraping frequency in `.env`:
   ```bash
   SCRAPE_INTERVAL=120  # Increase to 2 minutes
   ```
2. Reduce number of coins in `.env`:
   ```bash
   COINS=BTC,ETH  # Monitor fewer coins
   ```
3. Restart:
   ```powershell
   docker-compose restart
   ```

### Issue: Database connection errors

**Solution:**

1. Check if TimescaleDB is running:
   ```powershell
   docker-compose ps timescaledb
   ```
2. Check database health:
   ```powershell
   docker-compose exec timescaledb pg_isready -U postgres
   ```
3. Re-initialize database:
   ```powershell
   docker-compose exec dashboard python scripts/setup_databases.py
   ```

### Issue: API rate limiting

**Solution:**

Exchanges may rate limit requests. Solutions:

1. Increase `SCRAPE_INTERVAL` in `.env`
2. Reduce number of coins
3. Check exchange API status pages

### Complete Reset

If all else fails, complete reset:

```powershell
# Stop and remove everything (WARNING: Deletes all data)
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Start fresh
docker-compose up -d

# Re-initialize database
docker-compose exec dashboard python scripts/setup_databases.py
```

---

## Maintenance

### Update Configuration

1. Edit `.env` file
2. Restart affected services:
   ```powershell
   docker-compose restart
   ```

### View Real-Time Logs

```powershell
docker-compose logs -f dashboard
```

Press `Ctrl+C` to exit.

### Stop the System

```powershell
docker-compose stop
```

### Start the System Again

```powershell
docker-compose start
```

### Update Code

If you modify source code:

```powershell
docker-compose restart dashboard
```

For Airflow DAG changes:
```powershell
docker-compose restart airflow-scheduler
```

---

## Performance Tuning

### For Low-End Systems

Edit `.env`:
```bash
SCRAPE_INTERVAL=180  # Scrape every 3 minutes
COINS=BTC,ETH        # Monitor only 2 coins
```

### For High-End Systems

Edit `.env`:
```bash
SCRAPE_INTERVAL=30   # Scrape every 30 seconds
COINS=BTC,ETH,BNB,SOL,TRX,DOGE,ADA,XRP,DOT,MATIC,LINK  # More coins
```

---

## Next Steps

1. ✅ System is running
2. ✅ Dashboard accessible at http://localhost:8050
3. ✅ Airflow DAG enabled and running
4. ✅ Notifications configured (optional)

**You're all set!** The system will now:
- Monitor prices every 60 seconds
- Calculate arbitrage opportunities
- Alert you on Telegram when profitable opportunities arise
- Display real-time data on the dashboard

---

## Support

For issues not covered here:

1. Check logs: `docker-compose logs`
2. Verify configuration in `.env`
3. Review Docker Desktop for container status
4. Check exchange API status pages

---

**Happy arbitrage hunting! 💰**
