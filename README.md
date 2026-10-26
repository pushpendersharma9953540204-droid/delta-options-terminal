# 🎯 Delta Exchange Options Execution Terminal

A real-time deterministic options trading terminal built for **Delta Exchange India** Bitcoin options. Evaluates whether to sell **CE, PE, or BOTH** every day based on the official Delta Execution Guide flowchart rules.

---

## ⚡ Key Features

- **Daily Deterministic Side Selection:** Evaluates BTC Perpetual price (`BTCUSD`) against Delta Exchange's 2-Day Option Chain board range to recommend `SELL BOTH (CE + PE)`, `SELL CE ONLY`, or `SELL PE ONLY`.
- **5-Minute Pre-Entry Live Preparation (9:55 PM – 10:00 PM IST):** Real-time order book quotes, candidate strikes, indicative limit prices, gross credit, and 200% stop loss levels update automatically every **30 seconds**.
- **Permanent 10:00 PM IST Candle Lock:** Captures the exact closed 10:00:00 PM IST candle from Delta Exchange, freezes all values permanently in `entry_snapshot_YYYYMMDD.json`, and terminates auto-refresh (zero live drift).
- **Exact Order Execution Specs:** Full contract specs with Limit Price, Order Book depth, Gross Credit ($ USD and ₹ INR), and 200% Stop Loss ($3.0\times$ entry price).

---

## 🌐 Deploy to Render (Cloud Hosting)

This repository includes `render.yaml` and `Procfile` configured for seamless deployment on **[Render.com](https://render.com)**.

### Option A: 1-Click Blueprint Deploy
1. Sign in to [Render.com](https://render.com).
2. Click **New +** $\to$ **Blueprint**.
3. Connect your GitHub repository (`pushpendersharma9953540204-droid/delta-options-terminal`).
4. Render will automatically detect `render.yaml` and launch the Web Service.

### Option B: Manual Web Service on Render
1. Click **New +** $\to$ **Web Service**.
2. Select your GitHub repository.
3. Configure settings:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`
4. Under **Environment Variables**, add:
   - `DELTA_BASE_URL` = `https://api.india.delta.exchange`
   - `DELTA_API_KEY` = *(your API key if private account data is needed)*
   - `DELTA_API_SECRET` = *(your API secret)*
5. Click **Create Web Service**. Your website URL will be live in ~2 minutes!

---

## ☁️ Deploy to Streamlit Cloud (Alternative Free Host)

1. Go to [share.streamlit.io](https://share.streamlit.io).
2. Connect your GitHub account and select this repository.
3. Set **Main file path:** `app.py`.
4. Click **Deploy!**

---

## 💻 Local Setup

```bash
# Clone the repository
git clone https://github.com/pushpendersharma9953540204-droid/delta-options-terminal.git
cd delta-options-terminal

# Install dependencies
pip install -r requirements.txt

# Run the terminal
streamlit run app.py
```
Or double-click `LAUNCH_DASHBOARD.bat` on Windows.
