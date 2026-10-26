"""
Unit tests for the 6-Step Strike Substitution Logic.
Verifies all constraints, failure modes, ranking order, and decisions.
"""
import unittest
from models import (
    ContractQuote, 
    InstrumentKind, 
    ValidationStatus, 
    DecisionType
)
from strike_substitution import StrikeSubstitutionEngine
from config import StrategyConfig

class TestStrikeSubstitution(unittest.TestCase):
    def setUp(self):
        self.cfg = StrategyConfig(
            MAX_SPREAD_PCT=0.08,
            MIN_ORDERBOOK_DEPTH=0.02,
            STRADDLE_MULTIPLIER=2.5,
            STOP_LOSS_MULTIPLIER=3.0,
            TARGET_PREMIUM_TOLERANCE_PCT=0.25
        )
        self.engine = StrikeSubstitutionEngine(self.cfg)
        self.target_expiry = "2026-10-29"

    def test_intended_strike_valid_passes(self):
        """If intended strike is valid and tradable, trade it without substitution."""
        c_q = ContractQuote("C-BTC-80000", InstrumentKind.CE, 80000, self.target_expiry, 50.0, 52.0, 0.1, 0.1)
        p_q = ContractQuote("P-BTC-80000", InstrumentKind.PE, 80000, self.target_expiry, 60.0, 62.0, 0.1, 0.1)
        chain = {80000.0: (c_q, p_q)}

        decision, strike, val_res, ranked = self.engine.apply_decision(
            intended_strike=80000.0,
            target_expiry=self.target_expiry,
            target_straddle_credit=110.0,
            chain_quotes=chain
        )
        self.assertEqual(decision, DecisionType.ELIGIBLE)
        self.assertEqual(strike, 80000.0)
        self.assertTrue(val_res.is_valid)

    def test_missing_quote_not_treated_as_missing_contract(self):
        """Missing quote must be identified as NO_VALID_QUOTES, not DOES_NOT_EXIST."""
        c_q = ContractQuote("C-BTC-80000", InstrumentKind.CE, 80000, self.target_expiry, 0.0, 0.0, 0.0, 0.0)
        p_q = ContractQuote("P-BTC-80000", InstrumentKind.PE, 80000, self.target_expiry, 60.0, 62.0, 0.1, 0.1)
        
        val_res = self.engine.validate_strike(80000.0, c_q, p_q, self.target_expiry)
        self.assertFalse(val_res.is_valid)
        self.assertEqual(val_res.status, ValidationStatus.NO_VALID_QUOTES)

    def test_missing_contract_treated_as_does_not_exist(self):
        """When contract is None in chain, status is DOES_NOT_EXIST."""
        p_q = ContractQuote("P-BTC-80000", InstrumentKind.PE, 80000, self.target_expiry, 60.0, 62.0, 0.1, 0.1)
        val_res = self.engine.validate_strike(80000.0, None, p_q, self.target_expiry)
        self.assertFalse(val_res.is_valid)
        self.assertEqual(val_res.status, ValidationStatus.DOES_NOT_EXIST)

    def test_excessive_spread_triggers_fallback(self):
        """When spread > 8%, strike fails validation and selects valid alternative."""
        # Intended strike with 20% spread
        c_q_bad = ContractQuote("C-BTC-80000", InstrumentKind.CE, 80000, self.target_expiry, 50.0, 62.0, 0.1, 0.1) # 21% spread
        p_q_bad = ContractQuote("P-BTC-80000", InstrumentKind.PE, 80000, self.target_expiry, 50.0, 51.0, 0.1, 0.1)
        
        # Valid alternative at 80400
        c_q_alt = ContractQuote("C-BTC-80400", InstrumentKind.CE, 80400, self.target_expiry, 48.0, 49.0, 0.1, 0.1)
        p_q_alt = ContractQuote("P-BTC-80400", InstrumentKind.PE, 80400, self.target_expiry, 50.0, 51.0, 0.1, 0.1)

        chain = {
            80000.0: (c_q_bad, p_q_bad),
            80400.0: (c_q_alt, p_q_alt)
        }

        decision, strike, val_res, ranked = self.engine.apply_decision(
            intended_strike=80000.0,
            target_expiry=self.target_expiry,
            target_straddle_credit=100.0,
            chain_quotes=chain
        )

        self.assertEqual(decision, DecisionType.ELIGIBLE)
        self.assertEqual(strike, 80400.0)
        self.assertEqual(val_res.status, ValidationStatus.EXCESSIVE_SPREAD)

    def test_ranking_constraints_reject_invalid_premium(self):
        """Alternative with premium outside target tolerance is rejected."""
        # Target credit is 100.0 (+/- 25% = 75 to 125)
        # Cand 80200 has credit 40.0 (fails premium rule)
        # Cand 80400 has credit 90.0 (passes premium rule)
        c_q_int = None
        p_q_int = None
        
        c_80200 = ContractQuote("C-80200", InstrumentKind.CE, 80200, self.target_expiry, 20.0, 20.5, 0.1, 0.1)
        p_80200 = ContractQuote("P-80200", InstrumentKind.PE, 80200, self.target_expiry, 20.0, 20.5, 0.1, 0.1) # total = 40

        c_80400 = ContractQuote("C-80400", InstrumentKind.CE, 80400, self.target_expiry, 45.0, 46.0, 0.1, 0.1)
        p_80400 = ContractQuote("P-80400", InstrumentKind.PE, 80400, self.target_expiry, 45.0, 46.0, 0.1, 0.1) # total = 90

        chain = {
            80000.0: (c_q_int, p_q_int),
            80200.0: (c_80200, p_80200),
            80400.0: (c_80400, p_80400),
        }

        decision, strike, val_res, ranked = self.engine.apply_decision(
            intended_strike=80000.0,
            target_expiry=self.target_expiry,
            target_straddle_credit=100.0,
            chain_quotes=chain
        )

        # Even though 80200 is closer (dist 200 vs 400), it fails premium compliance!
        # Thus 80400 must be chosen.
        self.assertEqual(decision, DecisionType.ELIGIBLE)
        self.assertEqual(strike, 80400.0)

    def test_no_trade_when_all_alternatives_fail(self):
        """If no alternative satisfies constraints, return NO_TRADE."""
        c_q_int = None
        p_q_int = None
        # Illiquid alternative
        c_alt = ContractQuote("C-80400", InstrumentKind.CE, 80400, self.target_expiry, 50.0, 51.0, 0.001, 0.001) # depth too small
        p_alt = ContractQuote("P-80400", InstrumentKind.PE, 80400, self.target_expiry, 50.0, 51.0, 0.001, 0.001)

        chain = {
            80000.0: (c_q_int, p_q_int),
            80400.0: (c_alt, p_alt)
        }

        decision, strike, val_res, ranked = self.engine.apply_decision(
            intended_strike=80000.0,
            target_expiry=self.target_expiry,
            target_straddle_credit=100.0,
            chain_quotes=chain
        )
        self.assertEqual(decision, DecisionType.NO_TRADE)
        self.assertIsNone(strike)

if __name__ == "__main__":
    unittest.main()
