"""
Configuration parameters for Delta Exchange Options Trading & Strike Substitution Engine.
"""
from dataclasses import dataclass
import os

# Load .env file if present
_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ[_k.strip()] = _v.strip()

@dataclass
class StrategyConfig:
    # Delta Exchange API endpoints
    DELTA_BASE_URL: str = os.getenv("DELTA_BASE_URL", "https://api.india.delta.exchange")
    DELTA_API_KEY: str = os.getenv("DELTA_API_KEY", "")
    DELTA_API_SECRET: str = os.getenv("DELTA_API_SECRET", "")

    # Underlying & trade sizing
    UNDERLYING_SYMBOL: str = "BTCUSD (BTC Perpetual Future)"
    PERPETUAL_SYMBOL: str = "BTCUSD"
    TRADE_QUANTITY: float = 0.02          # BTC contracts per leg
    ENTRY_TIME_IST: str = "22:00:00"      # Daily entry IST (10:00 PM)
    EXIT_TIME_IST: str = "17:29:00"       # Expiry exit IST
    EXCLUDED_WEEKDAYS: tuple = ()         # Every day trade (No excluded days)

    # Strategy Multipliers & Targets
    STRADDLE_MULTIPLIER: float = 2.5       # Intended strike distance = ATM Straddle * 2.5
    STOP_LOSS_MULTIPLIER: float = 3.0     # 200% loss = 3.0x entry premium
    TARGET_PREMIUM_TOLERANCE_PCT: float = 0.25 # +/- 25% tolerance on premium compliance

    # Liquidity & Execution Constraints (Step 1 & Step 3)
    MAX_SPREAD_PCT: float = 0.08          # Max allowable (Ask - Bid) / Mid (8%)
    MIN_ORDERBOOK_DEPTH: float = 0.02     # Minimum quantity at best bid (BTC)
    MAX_SLIPPAGE_RATE: float = 0.005      # 0.5% estimated execution slippage
    TAKER_FEE_RATE: float = 0.0003        # 0.03% taker commission on Delta
    MAX_CANDIDATE_SEARCH_STRIKES: int = 10 # Number of strikes above and below to search

    # Currency & Capital Configuration
    USD_TO_INR: float = 85.0              # Delta Exchange India conversion rate: $1 USD = 85 INR
    CAPITAL_INR: float = 5000.0           # Capital used for the strategy in INR: ₹5,000

config = StrategyConfig()
