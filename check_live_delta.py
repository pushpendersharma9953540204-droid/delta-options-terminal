"""
Live Delta Exchange Market Scanner & Strike Substitution Evaluator.
Fetches real-time BTC price, 2-day expiry chain, ATM straddle, and applies
the Strike Substitution Logic directly against live Delta Exchange order books.
"""
import sys
import os
import requests
from datetime import datetime, timezone
from typing import Dict, Tuple, Optional, List

from config import config
from models import ContractQuote, InstrumentKind, ValidationStatus, DecisionType
from strategy import TwoDayStraddleStrangleStrategy

class DualLogger:
    def __init__(self, filename="live_trade_plan.txt"):
        self.terminal = sys.stdout
        self.log_file = open(filename, "w", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        if not self.log_file.closed:
            self.log_file.write(message)

    def flush(self):
        self.terminal.flush()
        if not self.log_file.closed:
            self.log_file.flush()

    def close(self):
        if not self.log_file.closed:
            self.log_file.close()

def load_env_file():
    """Load .env file if available."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()

def get_live_btc_price(base_url: str) -> float:
    """Fetch live BTC mark price from Delta Exchange ticker."""
    url = f"{base_url}/v2/tickers/BTCUSD"
    try:
        r = requests.get(url, timeout=5)
        res = r.json().get("result", {})
        px = float(res.get("mark_price") or res.get("close") or res.get("spot_price") or 0.0)
        return px
    except Exception as e:
        print(f"[!] Error fetching BTC price: {e}")
        return 0.0

def get_live_option_chain(base_url: str, underlying="BTC"):
    """Fetch all active options and tickers for the underlying asset."""
    # 1. Products
    p_url = f"{base_url}/v2/products"
    r_prod = requests.get(p_url, params={"contract_types": "call_options,put_options"}, timeout=8)
    all_prods = r_prod.json().get("result", [])
    btc_prods = [p for p in all_prods if p.get("underlying_asset", {}).get("symbol") == underlying]

    # 2. Tickers
    t_url = f"{base_url}/v2/tickers"
    r_tick = requests.get(t_url, timeout=8)
    tickers_dict = {t["symbol"]: t for t in r_tick.json().get("result", [])}

    return btc_prods, tickers_dict

def main():
    load_env_file()
    base_url = os.getenv("DELTA_BASE_URL", config.DELTA_BASE_URL)
    api_key = os.getenv("DELTA_API_KEY", "")

    logger = DualLogger("live_trade_plan.txt")
    sys.stdout = logger

    print("=" * 80)
    print(" LIVE DELTA EXCHANGE MARKET EVALUATOR")
    print(f" Connected Endpoint: {base_url}")
    if api_key:
        print(f" Read-Only API Key: [AUTHENTICATED] ({api_key[:6]}...{api_key[-4:]})")
        from delta_client import DeltaClient
        client = DeltaClient(base_url=base_url, api_key=api_key, api_secret=os.getenv("DELTA_API_SECRET", ""))
        bal = client.get_balances()
        if bal.get("success"):
            meta = bal.get("meta", {})
            print(f" Account Net Equity: ${float(meta.get('net_equity', 0.0)):,.2f} USD")
        else:
            print(f" [!] Balance check: {bal.get('error', 'Auth Failed')}")
    else:
        print(" API Key: [None provided] - Running on Live Public Market Data")
    print("=" * 80)

    print("\n[+] Fetching live BTC index and mark price...")
    btc_price = get_live_btc_price(base_url)
    if btc_price <= 0:
        print("[!] Unable to fetch BTC price. Please check your internet connection.")
        return

    print(f"    Current BTC Price: ${btc_price:,.2f}")

    print("\n[+] Fetching live option contracts and quotes from Delta Exchange...")
    prods, tickers = get_live_option_chain(base_url)
    print(f"    Total active BTC option contracts retrieved: {len(prods)}")

    # Group options by expiry date
    expiries = sorted(list(set(p.get("settlement_time") for p in prods if p.get("settlement_time"))))
    
    # Target 2-day expiry (approx 48 hours away)
    now_utc = datetime.now(timezone.utc)
    target_exp = None
    for exp_str in expiries:
        try:
            exp_dt = datetime.strptime(exp_str.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S%z")
            hours_diff = (exp_dt - now_utc).total_seconds() / 3600.0
            if 30 <= hours_diff <= 65:
                target_exp = exp_str
                break
        except Exception:
            continue

    if not target_exp and expiries:
        target_exp = expiries[1] if len(expiries) > 1 else expiries[0]

    print(f"\n[+] Selected 2-Day Expiry Contract: {target_exp}")

    # Build chain dictionary for target expiry
    chain_quotes: Dict[float, Tuple[Optional[ContractQuote], Optional[ContractQuote]]] = {}
    exp_prods = [p for p in prods if p.get("settlement_time") == target_exp]

    for p in exp_prods:
        strike = float(p.get("strike_price", 0.0))
        sym = p.get("symbol", "")
        ctype = p.get("contract_type", "")
        kind = InstrumentKind.CE if "call" in ctype else InstrumentKind.PE
        tick = tickers.get(sym, {})
        quotes = tick.get("quotes", {})
        
        bid = float(quotes.get("best_bid") or 0.0)
        ask = float(quotes.get("best_ask") or 0.0)
        bid_size = float(quotes.get("best_bid_size") or 0.0)
        ask_size = float(quotes.get("best_ask_size") or 0.0)

        cq = ContractQuote(
            symbol=sym,
            instrument_kind=kind,
            strike=strike,
            expiry=target_exp,
            bid=bid,
            ask=ask,
            bid_size=bid_size,
            ask_size=ask_size,
            is_tradable=(p.get("trading_status") == "live")
        )

        current_pair = chain_quotes.get(strike, (None, None))
        if kind == InstrumentKind.CE:
            chain_quotes[strike] = (cq, current_pair[1])
        else:
            chain_quotes[strike] = (current_pair[0], cq)

    # Run the Strategy Evaluator with Mandatory Substitution Logic
    strat = TwoDayStraddleStrangleStrategy(strike_step=400.0)
    result = strat.evaluate_strangle_trade(
        spot_price=btc_price,
        target_expiry=target_exp,
        chain_quotes=chain_quotes,
        quantity=config.TRADE_QUANTITY
    )

    print("\n" + "=" * 80)
    print(" LIVE STRATEGY EVALUATION & STRIKE SUBSTITUTION")
    print("=" * 80)
    print(f" Current BTC Spot:               ${btc_price:,.2f}")
    print(f" 2-Day Expiry Date:              {target_exp}")
    print(f" ATM Strike Identified:          ${result['atm_strike']:,.0f}")
    print(f" Live ATM Straddle Premium:      ${result['atm_straddle_premium']:,.2f}")
    print(f" Strike Offset (Straddle * 2.5): ${result['offset_calculated']:,.2f}")
    print(f" Intended Call Strike:           ${result['intended_ce_strike']:,.0f} CE")
    print(f" Intended Put Strike:            ${result['intended_pe_strike']:,.0f} PE")
    print("-" * 80)
    
    ce_sel_str = f"${result['selected_ce_strike']:,.0f} CE" if result['selected_ce_strike'] else "None (No Qualified Strike)"
    pe_sel_str = f"${result['selected_pe_strike']:,.0f} PE" if result['selected_pe_strike'] else "None (No Qualified Strike)"
    print(f" Selected Call Strike:           {ce_sel_str}")
    print(f" Selected Put Strike:            {pe_sel_str}")
    print(f" Execution Status:               {'ELIGIBLE TO TRADE' if result['can_trade'] else 'NO TRADE (Constraints Enforced)'}")
    print("=" * 80)

    # Print Step 5 Table for both legs
    print("\n[+] STEP 5 PRE-TRADE EXPLANATION LOG (LIVE ORDER BOOK AUDIT):")
    print("| Intended Strike | Failure Reason | Selected Alt | Premium Comparison | Liquidity | Stop-Loss | Decision |")
    print("|---|---|---|---|---|---|---|")
    print(result["ce_explanation"].to_markdown_table_row())
    print(result["pe_explanation"].to_markdown_table_row())

    # Print Live Orders
    if result["can_trade"]:
        print("\n[+] EXECUTABLE SHORT STRANGLE ORDERS (200% STOP-LOSS TRIGGER):")
        for idx, o in enumerate(result["orders"], 1):
            sub_label = " [SUBSTITUTE]" if o["is_substituted"] else " [INTENDED]"
            print(f"  Order {idx}: SELL {o['quantity']} {o['symbol']}{sub_label}")
            print(f"           Limit Entry Price:  ${o['limit_price']:,.2f}")
            print(f"           200% Stop-Loss:     ${o['stop_loss_trigger']:,.2f} (3.0x entry premium)")
    else:
        print("\n[!] Trade Aborted (NO TRADE):")
        print("    Delta Exchange has not yet listed strikes as far OTM as the Straddle * 2.5 target,")
        print("    or quotes did not meet the strict spread/liquidity safety constraints.")
        print("    The strategy strict rules protected you from forcing a distorted trade!")

    print("\n" + "=" * 80)
    print(" Report saved to: live_trade_plan.txt")
    print("=" * 80)

    sys.stdout = logger.terminal
    logger.close()

if __name__ == "__main__":
    main()
