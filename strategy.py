"""
Strategy Implementation:
Short Strangle (Sell 1 CE + Sell 1 PE) on a 2-Day Expiry.

Execution Workflow:
1. Determine 2-Day Expiry (DTE = 2, 17:30 IST / 12:00 UTC settlement).
2. Calculate ATM Strike from BTC spot price.
3. Calculate ATM Straddle = ATM CE Bid + ATM PE Bid.
4. Calculate Strike Offset = ATM Straddle * 2.5.
5. Intended CE Strike = ATM Strike + round_to_strike(Offset).
   Intended PE Strike = ATM Strike - round_to_strike(Offset).
6. Validate both legs against Step 1-5 Strike Substitution Engine.
7. Set 200% Stop Loss (3.0x entry premium) and Time Exit (17:29 IST).
"""
from typing import Dict, Tuple, Optional, Any, List
from datetime import datetime, timedelta
import pytz

from models import (
    ContractQuote, 
    DecisionType, 
    SubstitutionExplanation
)
from strike_substitution import StrikeSubstitutionEngine
from delta_client import DeltaClient
from config import config

class TwoDayStraddleStrangleStrategy:
    def __init__(self, delta_client: Optional[DeltaClient] = None, strike_step: float = 400.0):
        self.client = delta_client or DeltaClient()
        self.engine = StrikeSubstitutionEngine(config)
        self.strike_step = strike_step

    def round_to_strike(self, price: float) -> float:
        """Round price to the nearest Delta Exchange strike interval."""
        return round(price / self.strike_step) * self.strike_step

    def get_2day_expiry_date(self, current_time: Optional[datetime] = None) -> str:
        """Calculate the 2-day expiry date in YYYY-MM-DD format."""
        tz = pytz.timezone("Asia/Kolkata")
        now = current_time or datetime.now(tz)
        target_date = now + timedelta(days=2)
        return target_date.strftime("%Y-%m-%d")

    def find_atm_strike(self, spot_price: float, available_strikes: List[float]) -> float:
        """Locate the closest available strike to the current BTC spot price."""
        if not available_strikes:
            return self.round_to_strike(spot_price)
        return min(available_strikes, key=lambda k: abs(k - spot_price))

    def derive_intended_strikes(
        self,
        spot_price: float,
        atm_strike: float,
        atm_straddle_premium: float,
        available_strikes: Optional[List[float]] = None
    ) -> Tuple[float, float, float]:
        """
        Derive target CE and PE strikes using:
        Offset = ATM Straddle Premium * 2.5
        If exact match is available on board, select exact match without clamping.
        """
        offset = atm_straddle_premium * config.STRADDLE_MULTIPLIER
        raw_ce = atm_strike + offset
        raw_pe = atm_strike - offset

        if available_strikes:
            call_strikes = [k for k in available_strikes if k >= spot_price]
            put_strikes = [k for k in available_strikes if k <= spot_price]

            if call_strikes and raw_ce <= max(call_strikes):
                intended_ce = min(call_strikes, key=lambda k: abs(k - raw_ce))
            elif call_strikes:
                intended_ce = max(call_strikes)
            else:
                intended_ce = self.round_to_strike(raw_ce)

            if put_strikes and raw_pe >= min(put_strikes):
                intended_pe = min(put_strikes, key=lambda k: abs(k - raw_pe))
            elif put_strikes:
                intended_pe = min(put_strikes)
            else:
                intended_pe = self.round_to_strike(raw_pe)
        else:
            intended_ce = self.round_to_strike(raw_ce)
            intended_pe = self.round_to_strike(raw_pe)

        return intended_ce, intended_pe, offset

    def evaluate_strangle_trade(
        self,
        spot_price: float,
        target_expiry: str,
        chain_quotes: Dict[float, Tuple[Optional[ContractQuote], Optional[ContractQuote]]],
        quantity: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Evaluate and construct the Short Strangle trade with full Substitution Logic.
        """
        qty = quantity or config.TRADE_QUANTITY
        available_strikes = sorted(chain_quotes.keys())
        if not available_strikes:
            return {"status": "NO_STRIKES_AVAILABLE", "can_trade": False}

        # 1. ATM Strike & ATM Straddle
        atm_k = self.find_atm_strike(spot_price, available_strikes)
        atm_ce, atm_pe = chain_quotes.get(atm_k, (None, None))
        
        atm_ce_bid = atm_ce.bid if atm_ce else 0.0
        atm_pe_bid = atm_pe.bid if atm_pe else 0.0

        if atm_ce_bid <= 0 or atm_pe_bid <= 0:
            # Fallback estimation for 2 DTE ATM straddle (~2% of BTC spot)
            est_straddle = spot_price * 0.02
            atm_straddle = est_straddle
        else:
            atm_straddle = atm_ce_bid + atm_pe_bid

        # 2. Derive intended strikes using Straddle * 2.5
        intended_ce_k, intended_pe_k, offset = self.derive_intended_strikes(
            spot_price=spot_price,
            atm_strike=atm_k,
            atm_straddle_premium=atm_straddle,
            available_strikes=available_strikes
        )

        # Target credit for the OTM strangle is approximately 10-15% of ATM straddle
        # or extracted from intended quotes if available
        intended_ce_pair = chain_quotes.get(intended_ce_k, (None, None))
        intended_pe_pair = chain_quotes.get(intended_pe_k, (None, None))
        
        target_ce_px = (intended_ce_pair[0].bid if intended_ce_pair[0] and intended_ce_pair[0].bid > 0 else (atm_straddle * 0.08))
        target_pe_px = (intended_pe_pair[1].bid if intended_pe_pair[1] and intended_pe_pair[1].bid > 0 else (atm_straddle * 0.08))

        # 3. Evaluate CE Leg substitution
        # Build candidate chains for CE
        ce_candidates_chain = {
            k: (pair[0], pair[1]) for k, pair in chain_quotes.items() if k >= spot_price
        }
        dec_ce, final_ce_k, val_ce, ranked_ce = self.engine.apply_decision(
            intended_strike=intended_ce_k,
            target_expiry=target_expiry,
            target_straddle_credit=target_ce_px * 2.0, # credit tolerance
            chain_quotes=ce_candidates_chain,
            required_qty=qty
        )

        # 4. Evaluate PE Leg substitution
        pe_candidates_chain = {
            k: (pair[0], pair[1]) for k, pair in chain_quotes.items() if k <= spot_price
        }
        dec_pe, final_pe_k, val_pe, ranked_pe = self.engine.apply_decision(
            intended_strike=intended_pe_k,
            target_expiry=target_expiry,
            target_straddle_credit=target_pe_px * 2.0,
            chain_quotes=pe_candidates_chain,
            required_qty=qty
        )

        can_trade = (dec_ce == DecisionType.ELIGIBLE) and (dec_pe == DecisionType.ELIGIBLE)

        # Format Step 5 explanations
        expl_ce = self.engine.explain_substitution(
            intended_strike=intended_ce_k,
            val_result=val_ce,
            selected_strike=final_ce_k,
            decision=dec_ce,
            target_premium=target_ce_px,
            ranked_candidates=ranked_ce
        )

        expl_pe = self.engine.explain_substitution(
            intended_strike=intended_pe_k,
            val_result=val_pe,
            selected_strike=final_pe_k,
            decision=dec_pe,
            target_premium=target_pe_px,
            ranked_candidates=ranked_pe
        )

        orders = []
        if can_trade and final_ce_k and final_pe_k:
            ce_quote = chain_quotes[final_ce_k][0]
            pe_quote = chain_quotes[final_pe_k][1]

            ce_entry = ce_quote.bid if ce_quote else target_ce_px
            pe_entry = pe_quote.bid if pe_quote else target_pe_px

            ce_sl = ce_entry * config.STOP_LOSS_MULTIPLIER
            pe_sl = pe_entry * config.STOP_LOSS_MULTIPLIER

            orders = [
                {
                    "side": "sell",
                    "kind": "CE",
                    "strike": final_ce_k,
                    "symbol": ce_quote.symbol if ce_quote else f"C-BTC-{int(final_ce_k)}",
                    "quantity": qty,
                    "limit_price": round(ce_entry, 2),
                    "stop_loss_trigger": round(ce_sl, 2),
                    "is_substituted": (final_ce_k != intended_ce_k)
                },
                {
                    "side": "sell",
                    "kind": "PE",
                    "strike": final_pe_k,
                    "symbol": pe_quote.symbol if pe_quote else f"P-BTC-{int(final_pe_k)}",
                    "quantity": qty,
                    "limit_price": round(pe_entry, 2),
                    "stop_loss_trigger": round(pe_sl, 2),
                    "is_substituted": (final_pe_k != intended_pe_k)
                }
            ]

        return {
            "spot_price": spot_price,
            "target_expiry": target_expiry,
            "atm_strike": atm_k,
            "atm_straddle_premium": atm_straddle,
            "offset_calculated": offset,
            "intended_ce_strike": intended_ce_k,
            "intended_pe_strike": intended_pe_k,
            "selected_ce_strike": final_ce_k,
            "selected_pe_strike": final_pe_k,
            "can_trade": can_trade,
            "ce_explanation": expl_ce,
            "pe_explanation": expl_pe,
            "orders": orders
        }
