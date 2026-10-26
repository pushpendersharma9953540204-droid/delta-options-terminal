"""
Strike Substitution Engine implementing Steps 1 to 5 of the Mandatory Strategy Rule.
"""
from typing import List, Optional, Tuple, Dict
from models import (
    ContractQuote, 
    StrikeValidationResult, 
    ValidationStatus, 
    AlternativeCandidate, 
    DecisionType, 
    SubstitutionExplanation,
    InstrumentKind
)
from config import StrategyConfig, config

class StrikeSubstitutionEngine:
    def __init__(self, cfg: Optional[StrategyConfig] = None):
        self.cfg = cfg or config
        self.substitution_log: List[SubstitutionExplanation] = []

    # -------------------------------------------------------------------------
    # STEP 1: Validate the Intended Strike
    # -------------------------------------------------------------------------
    def validate_strike(
        self,
        strike: float,
        call_quote: Optional[ContractQuote],
        put_quote: Optional[ContractQuote],
        target_expiry: str,
        required_qty: Optional[float] = None
    ) -> StrikeValidationResult:
        """
        Validate whether the target strike is executable and tradable.
        Distinguishes missing contracts, missing quotes, wide spreads,
        insufficient liquidity, and closed market status.
        """
        req_qty = required_qty or self.cfg.TRADE_QUANTITY
        failure_reasons = []

        # 1. Existence check (Contract missing vs quote missing)
        if call_quote is None or put_quote is None:
            missing = []
            if call_quote is None: missing.append("CE contract")
            if put_quote is None: missing.append("PE contract")
            reason = f"Contract does not exist in chain: {', '.join(missing)}"
            return StrikeValidationResult(
                strike=strike,
                is_valid=False,
                status=ValidationStatus.DOES_NOT_EXIST,
                failure_reasons=[reason],
                call_quote=call_quote,
                put_quote=put_quote
            )

        # 2. Expiry check
        if call_quote.expiry != target_expiry or put_quote.expiry != target_expiry:
            failure_reasons.append(f"Expiry mismatch: expected {target_expiry}")

        # 3. Market tradability / closed
        if not call_quote.is_tradable or not put_quote.is_tradable:
            failure_reasons.append("Market is closed or contract trading is disrupted/suspended")
            return StrikeValidationResult(
                strike=strike,
                is_valid=False,
                status=ValidationStatus.MARKET_CLOSED,
                failure_reasons=failure_reasons,
                call_quote=call_quote,
                put_quote=put_quote
            )

        # 4. Valid quotes check (Missing quote != missing contract)
        if call_quote.bid <= 0 or put_quote.bid <= 0:
            missing_quotes = []
            if call_quote.bid <= 0: missing_quotes.append("CE bid <= 0")
            if put_quote.bid <= 0: missing_quotes.append("PE bid <= 0")
            failure_reasons.append(f"No valid executable quotes: {', '.join(missing_quotes)}")
            return StrikeValidationResult(
                strike=strike,
                is_valid=False,
                status=ValidationStatus.NO_VALID_QUOTES,
                failure_reasons=failure_reasons,
                call_quote=call_quote,
                put_quote=put_quote
            )

        # 5. Bid/Ask spread check
        if call_quote.spread_pct > self.cfg.MAX_SPREAD_PCT or put_quote.spread_pct > self.cfg.MAX_SPREAD_PCT:
            excessive = []
            if call_quote.spread_pct > self.cfg.MAX_SPREAD_PCT:
                excessive.append(f"CE spread {call_quote.spread_pct*100:.1f}% > {self.cfg.MAX_SPREAD_PCT*100:.0f}%")
            if put_quote.spread_pct > self.cfg.MAX_SPREAD_PCT:
                excessive.append(f"PE spread {put_quote.spread_pct*100:.1f}% > {self.cfg.MAX_SPREAD_PCT*100:.0f}%")
            failure_reasons.append(f"Excessive bid/ask spread: {', '.join(excessive)}")
            return StrikeValidationResult(
                strike=strike,
                is_valid=False,
                status=ValidationStatus.EXCESSIVE_SPREAD,
                failure_reasons=failure_reasons,
                call_quote=call_quote,
                put_quote=put_quote
            )

        # 6. Orderbook liquidity / depth check
        if call_quote.bid_size < req_qty or put_quote.bid_size < req_qty:
            low_liq = []
            if call_quote.bid_size < req_qty:
                low_liq.append(f"CE bid size {call_quote.bid_size} < required {req_qty}")
            if put_quote.bid_size < req_qty:
                low_liq.append(f"PE bid size {put_quote.bid_size} < required {req_qty}")
            failure_reasons.append(f"Insufficient liquidity: {', '.join(low_liq)}")
            return StrikeValidationResult(
                strike=strike,
                is_valid=False,
                status=ValidationStatus.INSUFFICIENT_LIQUIDITY,
                failure_reasons=failure_reasons,
                call_quote=call_quote,
                put_quote=put_quote
            )

        return StrikeValidationResult(
            strike=strike,
            is_valid=True,
            status=ValidationStatus.VALID,
            failure_reasons=[],
            call_quote=call_quote,
            put_quote=put_quote
        )

    # -------------------------------------------------------------------------
    # STEP 2: Generate Alternative Strikes
    # -------------------------------------------------------------------------
    def generate_candidate_strikes(
        self,
        intended_strike: float,
        target_expiry: str,
        chain_quotes: Dict[float, Tuple[Optional[ContractQuote], Optional[ContractQuote]]]
    ) -> List[AlternativeCandidate]:
        """
        Search strikes around the intended strike for the same expiry.
        For each candidate, calculate executable short straddle premium:
        Combined straddle premium = Call Bid + Put Bid
        Net credit = Gross credit * (1 - slippage) - fees
        """
        candidates = []
        for strike, (c_q, p_q) in chain_quotes.items():
            if c_q is None or p_q is None:
                continue

            raw_credit = c_q.bid + p_q.bid
            slippage = raw_credit * self.cfg.MAX_SLIPPAGE_RATE
            fees = raw_credit * self.cfg.TAKER_FEE_RATE
            net_credit = max(0.0, raw_credit - slippage - fees)
            distance = abs(strike - intended_strike)

            candidate = AlternativeCandidate(
                strike=strike,
                expiry=target_expiry,
                call_quote=c_q,
                put_quote=p_q,
                raw_straddle_credit=raw_credit,
                estimated_slippage=slippage,
                estimated_fees=fees,
                net_straddle_credit=net_credit,
                strike_distance=distance
            )
            candidates.append(candidate)

        return candidates

    # -------------------------------------------------------------------------
    # STEP 3: Rank Alternatives Using Strategy Constraints (Strict Hierarchy)
    # -------------------------------------------------------------------------
    def rank_alternatives(
        self,
        candidates: List[AlternativeCandidate],
        intended_strike: float,
        target_expiry: str,
        target_straddle_credit: float,
        required_qty: Optional[float] = None
    ) -> List[AlternativeCandidate]:
        """
        Evaluate candidates strictly through the 6 hierarchical constraint gates:
        1. Expiry validity
        2. Contract validity (tradable & exist)
        3. Premium-rule compliance (straddle * 2.5 calculation & target premium range)
        4. Risk compliance (stop-loss 3x rule & risk envelope)
        5. Liquidity (bid/ask spread & orderbook depth)
        6. Strike distance (sort eligible survivors by distance; NO arbitrary weighted score!)
        """
        req_qty = required_qty or self.cfg.TRADE_QUANTITY
        evaluated = []

        for cand in candidates:
            reasons = []

            # 1. Expiry validity
            cand.passed_expiry = (
                cand.call_quote.expiry == target_expiry and 
                cand.put_quote.expiry == target_expiry
            )
            if not cand.passed_expiry:
                reasons.append(f"Invalid expiry: {cand.call_quote.expiry} != {target_expiry}")

            # 2. Contract validity (Tradable and not suspended)
            cand.passed_contract_validity = (
                cand.call_quote.is_tradable and 
                cand.put_quote.is_tradable and
                cand.call_quote.status != ValidationStatus.MARKET_CLOSED and
                cand.put_quote.status != ValidationStatus.MARKET_CLOSED
            )
            if not cand.passed_contract_validity:
                reasons.append("Contracts not tradable or market suspended")

            # 3. Premium-rule compliance (straddle * 2.5 verified credit range)
            if target_straddle_credit > 0:
                lower_bound = target_straddle_credit * (1.0 - self.cfg.TARGET_PREMIUM_TOLERANCE_PCT)
                upper_bound = target_straddle_credit * (1.0 + self.cfg.TARGET_PREMIUM_TOLERANCE_PCT)
                cand.passed_premium_rule = (lower_bound <= cand.raw_straddle_credit <= upper_bound)
                if not cand.passed_premium_rule:
                    reasons.append(
                        f"Premium credit {cand.raw_straddle_credit:.2f} out of target range "
                        f"[{lower_bound:.2f}, {upper_bound:.2f}]"
                    )
            else:
                cand.passed_premium_rule = cand.raw_straddle_credit > 0

            # 4. Risk compliance (Stop Loss rule: 3.0x entry price / 200% loss)
            # Ensure premium is positive and stops are mathematically executable
            cand.passed_risk_rule = (
                cand.raw_straddle_credit > 0 and 
                (cand.call_quote.bid > 0) and 
                (cand.put_quote.bid > 0)
            )
            if not cand.passed_risk_rule:
                reasons.append("Risk rule failed: non-viable premium for 200% stop loss")

            # 5. Liquidity (Spread & Depth)
            spread_ok = (
                cand.call_quote.spread_pct <= self.cfg.MAX_SPREAD_PCT and
                cand.put_quote.spread_pct <= self.cfg.MAX_SPREAD_PCT
            )
            depth_ok = (
                cand.call_quote.bid_size >= req_qty and
                cand.put_quote.bid_size >= req_qty
            )
            cand.passed_liquidity = (spread_ok and depth_ok)
            if not cand.passed_liquidity:
                liq_errs = []
                if not spread_ok: liq_errs.append("Spread exceeded limit")
                if not depth_ok: liq_errs.append("Insufficient bid depth")
                reasons.append(f"Liquidity constraint failed: {', '.join(liq_errs)}")

            # Candidate eligibility: Must pass ALL 5 gates
            cand.is_eligible = (
                cand.passed_expiry and
                cand.passed_contract_validity and
                cand.passed_premium_rule and
                cand.passed_risk_rule and
                cand.passed_liquidity
            )
            cand.rejection_reasons = reasons
            evaluated.append(cand)

        # 6. Strike distance ranking: Sort eligible candidates strictly by distance to intended strike
        # Non-eligible candidates are placed after eligible ones
        ranked = sorted(
            evaluated,
            key=lambda c: (
                0 if c.is_eligible else 1,    # Eligible candidates strictly first
                c.strike_distance              # Closest strike distance
            )
        )
        return ranked

    # -------------------------------------------------------------------------
    # STEP 4: Apply Strict Decision
    # -------------------------------------------------------------------------
    def apply_decision(
        self,
        intended_strike: float,
        target_expiry: str,
        target_straddle_credit: float,
        chain_quotes: Dict[float, Tuple[Optional[ContractQuote], Optional[ContractQuote]]],
        required_qty: Optional[float] = None
    ) -> Tuple[DecisionType, Optional[float], StrikeValidationResult, List[AlternativeCandidate]]:
        """
        Apply strict decision:
        - If intended strike passes every check -> Trade intended.
        - If it fails -> select closest eligible alternative that passes every constraint.
        - If no alternative qualifies -> Return NO TRADE.
        - Never change expiry, multiplier, or stop loss automatically.
        """
        # Step 1: Validate intended strike
        call_q, put_q = chain_quotes.get(intended_strike, (None, None))
        val_result = self.validate_strike(
            strike=intended_strike,
            call_quote=call_q,
            put_quote=put_q,
            target_expiry=target_expiry,
            required_qty=required_qty
        )

        if val_result.is_valid:
            return DecisionType.ELIGIBLE, intended_strike, val_result, []

        # Step 2: Generate alternatives
        candidates = self.generate_candidate_strikes(
            intended_strike=intended_strike,
            target_expiry=target_expiry,
            chain_quotes=chain_quotes
        )

        # Step 3: Rank alternatives using hierarchical constraints
        ranked = self.rank_alternatives(
            candidates=candidates,
            intended_strike=intended_strike,
            target_expiry=target_expiry,
            target_straddle_credit=target_straddle_credit,
            required_qty=required_qty
        )

        # Step 4: Pick best eligible candidate
        eligible = [c for c in ranked if c.is_eligible and c.strike != intended_strike]
        if eligible:
            best_alt = eligible[0]
            return DecisionType.ELIGIBLE, best_alt.strike, val_result, ranked

        # No alternative qualifies
        return DecisionType.NO_TRADE, None, val_result, ranked

    # -------------------------------------------------------------------------
    # STEP 5: Explain the Alternative (Pre-trade Table & Audit Logging)
    # -------------------------------------------------------------------------
    def explain_substitution(
        self,
        intended_strike: float,
        val_result: StrikeValidationResult,
        selected_strike: Optional[float],
        decision: DecisionType,
        target_premium: float,
        ranked_candidates: List[AlternativeCandidate]
    ) -> SubstitutionExplanation:
        """
        Format the pre-trade explanation table according to Step 5 specification:
        - Intended strike
        - Failure reason
        - Selected alternative
        - Premium comparison
        - Liquidity
        - Stop-loss
        - Decision
        """
        # Failure reason
        failure_reason = "; ".join(val_result.failure_reasons) if val_result.failure_reasons else "None (Valid)"

        # Premium comparison
        if selected_strike is not None:
            chosen = next((c for c in ranked_candidates if c.strike == selected_strike), None)
            if chosen:
                alt_prem = chosen.raw_straddle_credit
                diff_pct = ((alt_prem - target_premium) / target_premium * 100) if target_premium > 0 else 0.0
                prem_comp = f"Target: {target_premium:.2f} | Alt: {alt_prem:.2f} ({diff_pct:+.1f}%)"
                
                # Liquidity details
                c_q, p_q = chosen.call_quote, chosen.put_quote
                liq = (
                    f"CE: Bid {c_q.bid:.1f}, Ask {c_q.ask:.1f}, Spd {c_q.spread_pct*100:.1f}%, Vol {c_q.bid_size} | "
                    f"PE: Bid {p_q.bid:.1f}, Ask {p_q.ask:.1f}, Spd {p_q.spread_pct*100:.1f}%, Vol {p_q.bid_size}"
                )
                
                # Stop loss calculation (3x entry premium)
                ce_sl = c_q.bid * self.cfg.STOP_LOSS_MULTIPLIER
                pe_sl = p_q.bid * self.cfg.STOP_LOSS_MULTIPLIER
                sl_str = f"CE SL: {ce_sl:.2f} (3x) | PE SL: {pe_sl:.2f} (3x)"
            else:
                # Intended strike was traded directly
                call_q, put_q = val_result.call_quote, val_result.put_quote
                prem_comp = f"Target: {target_premium:.2f} | Intended: {target_premium:.2f}"
                liq = (
                    f"CE: Bid {call_q.bid:.1f}, Ask {call_q.ask:.1f} | "
                    f"PE: Bid {put_q.bid:.1f}, Ask {put_q.ask:.1f}"
                ) if (call_q and put_q) else "N/A"
                sl_str = f"CE SL: {(call_q.bid*3):.2f} | PE SL: {(put_q.bid*3):.2f}" if (call_q and put_q) else "N/A"
        else:
            prem_comp = f"Target: {target_premium:.2f} | Alt: N/A"
            liq = "N/A (No eligible strikes)"
            sl_str = "N/A"

        explanation = SubstitutionExplanation(
            intended_strike=intended_strike,
            failure_reason=failure_reason,
            selected_alternative=selected_strike if selected_strike != intended_strike else None,
            premium_comparison=prem_comp,
            liquidity=liq,
            stop_loss=sl_str,
            decision=decision,
            details={
                "ranked_candidates_count": len(ranked_candidates),
                "rejections": {c.strike: c.rejection_reasons for c in ranked_candidates if not c.is_eligible}
            }
        )
        self.substitution_log.append(explanation)
        return explanation
