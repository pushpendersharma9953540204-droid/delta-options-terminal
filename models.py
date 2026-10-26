"""
Data models and Enums for the Strike Substitution Engine.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any

class InstrumentKind(str, Enum):
    CE = "CE"
    PE = "PE"

class ValidationStatus(str, Enum):
    VALID = "VALID"
    DOES_NOT_EXIST = "DOES_NOT_EXIST"
    NO_VALID_QUOTES = "NO_VALID_QUOTES"
    EXCESSIVE_SPREAD = "EXCESSIVE_SPREAD"
    INSUFFICIENT_LIQUIDITY = "INSUFFICIENT_LIQUIDITY"
    MARKET_CLOSED = "MARKET_CLOSED"

class DecisionType(str, Enum):
    ELIGIBLE = "Eligible"
    MANUAL_REVIEW = "Manual Review"
    NO_TRADE = "No Trade"

@dataclass
class ContractQuote:
    symbol: str
    instrument_kind: InstrumentKind
    strike: float
    expiry: str
    bid: float
    ask: float
    bid_size: float
    ask_size: float
    is_tradable: bool = True
    status: ValidationStatus = ValidationStatus.VALID

    @property
    def spread(self) -> float:
        return max(0.0, self.ask - self.bid)

    @property
    def mid_price(self) -> float:
        if self.bid > 0 and self.ask > 0:
            return (self.bid + self.ask) / 2.0
        return self.bid if self.bid > 0 else self.ask

    @property
    def spread_pct(self) -> float:
        mid = self.mid_price
        if mid <= 0:
            return 1.0
        return self.spread / mid

@dataclass
class StrikeValidationResult:
    strike: float
    is_valid: bool
    status: ValidationStatus
    failure_reasons: List[str] = field(default_factory=list)
    call_quote: Optional[ContractQuote] = None
    put_quote: Optional[ContractQuote] = None

@dataclass
class AlternativeCandidate:
    strike: float
    expiry: str
    call_quote: ContractQuote
    put_quote: ContractQuote
    
    # Premium calculations (Step 2)
    raw_straddle_credit: float = 0.0      # Call bid + Put bid
    estimated_slippage: float = 0.0       # Slippage allowance
    estimated_fees: float = 0.0           # Exchange commissions
    net_straddle_credit: float = 0.0      # Executable credit
    
    # Distance to original intended strike
    strike_distance: float = 0.0          # abs(strike - intended_strike)
    
    # Step 3 Hierarchical Constraint Gates
    passed_expiry: bool = False
    passed_contract_validity: bool = False
    passed_premium_rule: bool = False
    passed_risk_rule: bool = False
    passed_liquidity: bool = False
    
    # Eligibility & Audit
    is_eligible: bool = False
    rejection_reasons: List[str] = field(default_factory=list)

@dataclass
class SubstitutionExplanation:
    """Step 5: Pre-trade explanation required display table."""
    intended_strike: float
    failure_reason: str
    selected_alternative: Optional[float]
    premium_comparison: str               # Target vs Alternative premium
    liquidity: str                        # Bid, ask, spread, available quantity
    stop_loss: str                        # Calculated using approved rule
    decision: DecisionType
    details: Dict[str, Any] = field(default_factory=dict)

    def to_markdown_table_row(self) -> str:
        alt_str = f"{self.selected_alternative:.0f}" if self.selected_alternative else "None"
        return (
            f"| {self.intended_strike:.0f} "
            f"| {self.failure_reason} "
            f"| {alt_str} "
            f"| {self.premium_comparison} "
            f"| {self.liquidity} "
            f"| {self.stop_loss} "
            f"| **{self.decision.value}** |"
        )
