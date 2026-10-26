"""
Delta Exchange Options Trading Terminal & Execution Guide.
Evaluates which side to sell tonight at 10:00:00 PM IST (CE, PE, or BOTH).
All data powered directly by Delta Exchange India API (BTCUSD Perpetual Future, 7 Days a Week).
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import pytz
import os

from config import config
from todays_strikes import get_complete_trade_ticket
from delta_client import DeltaClient

# Set page configuration
st.set_page_config(
    page_title="Delta Execution Guide | Which Side to Sell Tonight",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for clean white / light trading terminal theme
st.markdown("""
<style>
    /* Completely remove sidebar & collapse control */
    [data-testid="stSidebar"],
    [data-testid="collapsedControl"],
    section[data-testid="stSidebar"] {
        display: none !important;
        visibility: hidden !important;
        width: 0px !important;
    }

    /* Clean White Theme Base */
    .main { background-color: #f8fafc; color: #0f172a; }
    body, [data-testid="stAppViewContainer"] {
        background-color: #f8fafc;
        color: #0f172a;
    }
    
    /* Live Pulse Indicator */
    @keyframes livePulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
        70% { transform: scale(1.1); box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }
    .live-pulse-dot {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background-color: #ef4444;
        animation: livePulse 1.5s infinite;
        vertical-align: middle;
        margin-right: 6px;
    }
    
    /* 30-Second Progress Bar */
    @keyframes countdownProgress {
        from { width: 100%; }
        to { width: 0%; }
    }
    .progress-bar-30s {
        height: 4px;
        background: linear-gradient(90deg, #10b981, #0284c7);
        animation: countdownProgress 30s linear infinite;
    }
    
    /* Responsive Mobile Padding for Streamlit Container */
    @media (max-width: 768px) {
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
            padding-left: 0.6rem !important;
            padding-right: 0.6rem !important;
        }
    }

    /* Metric Cards - Modern Clean White Cards */
    .metric-card {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 14px 16px;
        border: 1px solid #e2e8f0;
        margin-bottom: 0px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-title {
        font-size: 0.78rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 1.65rem;
        font-weight: 700;
        line-height: 1.25;
        margin-bottom: 4px;
        word-break: break-word;
        color: #0f172a;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #64748b;
    }
    
    /* High-Contrast Color Utility Classes for White Theme */
    .green-text { color: #059669 !important; }
    .red-text { color: #dc2626 !important; }
    .gold-text { color: #d97706 !important; }
    .blue-text { color: #0284c7 !important; }

    /* Responsive Grid Containers */
    .card-grid-4 {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 16px;
    }
    .card-grid-2 {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 14px;
        margin-bottom: 16px;
    }
    .timing-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 12px;
        font-size: 0.9rem;
    }
    .order-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px 16px;
        font-size: 0.92rem;
    }
    .order-card-call {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        border: 2px solid #ef4444;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        margin-bottom: 16px;
    }
    .order-card-put {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        border: 2px solid #10b981;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        margin-bottom: 16px;
    }
    .order-card-skipped {
        background-color: #f8fafc;
        border-radius: 10px;
        padding: 20px;
        border: 2px dashed #94a3b8;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
        display: flex;
        flex-direction: column;
        justify-content: center;
        margin-bottom: 16px;
        color: #475569;
    }

    /* Hero Decision Card */
    .hero-decision-card {
        background: #ffffff;
        border-radius: 10px;
        padding: 20px 24px;
        margin-bottom: 18px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
    }
    .decision-badge-large {
        font-size: 1.45rem;
        font-weight: 800;
        padding: 8px 18px;
        border-radius: 8px;
        display: inline-block;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }

    /* Mobile Responsive Breakpoints */
    @media (max-width: 960px) {
        .card-grid-4 {
            grid-template-columns: repeat(2, 1fr) !important;
            gap: 10px !important;
        }
        .card-grid-2 {
            grid-template-columns: 1fr !important;
            gap: 12px !important;
        }
    }
    @media (max-width: 600px) {
        .card-grid-4 {
            grid-template-columns: 1fr !important;
            gap: 8px !important;
        }
        .metric-value {
            font-size: 1.4rem !important;
        }
        .metric-card {
            padding: 12px 14px !important;
        }
        .timing-grid {
            grid-template-columns: 1fr 1fr !important;
            gap: 8px !important;
            font-size: 0.82rem !important;
        }
        .order-grid {
            grid-template-columns: 1fr !important;
            gap: 8px !important;
            font-size: 0.88rem !important;
        }
    }

    /* Refined Status Strip - Light Mode */
    .status-strip {
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-left: 4px solid #0284c7;
        padding: 10px 16px;
        border-radius: 6px;
        margin-bottom: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
    }
    .status-title {
        font-size: 0.92rem;
        font-weight: 600;
        color: #0f172a;
    }
    .status-badge {
        background: #e0f2fe;
        color: #0369a1;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 4px;
        border: 1px solid #bae6fd;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Hide Deploy button completely from top right */
    .stDeployButton,
    [data-testid="stDeployButton"],
    header [data-testid="stHeader"] .stDeployButton,
    header [data-testid="stToolbar"] .stDeployButton,
    button[title*="Deploy"],
    button[aria-label*="Deploy"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# MAIN DASHBOARD RENDERING FUNCTION
# -----------------------------------------------------------------------------
def render_main_dashboard(signal, is_live_mode: bool, usd_to_inr: float):
    # -------------------------------------------------------------------------
    # STATUS STRIP
    # -------------------------------------------------------------------------
    if signal.get('is_pre_entry_window'):
        st.markdown(f"""
        <div class="status-strip" style="background:#fffbeb; border:1px solid #fef3c7; border-left:4px solid #f59e0b; padding:12px 18px; margin-bottom:16px;">
            <div style="display:flex; justify-content:space-between; align-items:center; width:100%; flex-wrap:wrap; gap:10px;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span class="live-pulse-dot"></span>
                    <div>
                        <span style="font-size:0.95rem; font-weight:800; color:#b45309;">⚡ 5-MINUTE PRE-ENTRY LIVE MODE (9:55 PM – 10:00 PM IST)</span>
                        <div style="font-size:0.8rem; color:#64748b;">Manual Trade Preparation Active &bull; Live Delta Quotes Updating Every <b>30 Seconds</b></div>
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:0.92rem; font-weight:800; color:#dc2626;">{signal['countdown_display']}</div>
                    <div style="font-size:0.75rem; color:#64748b;">Last Updated: <b>{signal['last_updated_time']}</b> &bull; Auto-refreshing in 30s</div>
                </div>
            </div>
            <div style="width:100%; height:4px; background:#f1f5f9; border-radius:2px; margin-top:10px; overflow:hidden;">
                <div class="progress-bar-30s"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="status-strip" style="background:#f0fdf4; border:1px solid #dcfce7; border-left:4px solid #059669; padding:10px 16px; margin-bottom:16px;">
            <div style="display:flex; justify-content:space-between; align-items:center; width:100%; flex-wrap:wrap; gap:8px;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#059669; box-shadow:0 0 6px rgba(5,150,105,0.4);"></span>
                    <span class="status-title" style="color:#065f46;">🔒 10:00:00 PM IST Candle Closed & Data Locked</span>
                    <span style="font-size:0.8rem; color:#64748b; margin-left:4px;">(Official Delta Exchange Execution Fixed &bull; Auto-Refresh Stopped &bull; No Live Drift)</span>
                </div>
                <div class="status-badge" style="background:#d1fae5; color:#047857; border-color:#a7f3d0; font-size:0.78rem;">
                    🔒 22:00 IST CANDLE LOCKED
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # HERO DECISION BANNER (WHICH SIDE TO SELL TONIGHT)
    # -------------------------------------------------------------------------
    dec_badge_bg = "#ecfdf5" if "BOTH" in signal['decision'] else ("#eff6ff" if "PE" in signal['decision'] else "#fff1f2")
    dec_badge_border = "#a7f3d0" if "BOTH" in signal['decision'] else ("#bfdbfe" if "PE" in signal['decision'] else "#fecdd3")
    dec_badge_color = signal.get("decision_color", "#059669")

    st.markdown(f"""
    <div class="hero-decision-card" style="border-left: 6px solid {dec_badge_color};">
        <div>
            <div style="font-size:0.85rem; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:6px;">
                🎯 10:00 PM IST STRATEGY RECOMMENDATION (DELTA EXECUTION GUIDE)
            </div>
            <div class="decision-badge-large" style="background:{dec_badge_bg}; border:2px solid {dec_badge_border}; color:{dec_badge_color};">
                {signal['decision_badge']}
            </div>
            <div style="font-size:1.05rem; font-weight:600; color:#0f172a; margin-top:6px;">
                Market Regime: <span style="color:{dec_badge_color};">{signal['market_regime']}</span>
            </div>
            <div style="font-size:0.9rem; color:#475569; margin-top:6px; line-height:1.5;">
                {signal['decision_explanation']}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Timing & Schedule Banner
    st.markdown(f"""
    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 4px solid #059669; padding: 14px 18px; border-radius: 8px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); color: #0f172a;">
        <div class="timing-grid">
            <div>📅 <b>Entry:</b> <span class="green-text">{signal['entry_date']}</span></div>
            <div>🕙 <b>Time:</b> <span class="gold-text">{signal['entry_time']}</span></div>
            <div>📅 <b>Expiry:</b> <span class="green-text">{signal['expiry_date']}</span></div>
            <div>🏁 <b>Settlement:</b> <span class="blue-text">{signal['expiry_settlement_time']}</span></div>
            <div>⏱️ <b>Exit:</b> <span class="gold-text">{signal['exit_time']}</span></div>
            <div>⏳ <b>Holding:</b> <span class="blue-text">{signal['holding_duration']}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4-Step Flowchart Audit
    st.markdown("#### ⚡ 4-Step Mechanical Flowchart Audit")
    step_ce_color = "#059669" if signal['ce_status'] == "QUEUE_SELL" else "#dc2626"
    step_pe_color = "#059669" if signal['pe_status'] == "QUEUE_SELL" else "#dc2626"

    st.markdown(f"""
    <div class="card-grid-4">
        <div class="metric-card" style="border-top: 3px solid #0284c7;">
            <div class="metric-title">Step 1: Spot & Straddle</div>
            <div style="font-size:1.1rem; font-weight:700; color:#0f172a; margin-bottom:2px;">${signal['btc_price']:,.2f} Spot</div>
            <div class="metric-sub">ATM Straddle: <b>${signal['atm_straddle']:,.2f}</b></div>
            <div style="font-size:0.75rem; color:#059669; font-weight:600; margin-top:4px;">✅ Spot & Premium Captured</div>
        </div>
        <div class="metric-card" style="border-top: 3px solid #d97706;">
            <div class="metric-title">Step 2: Math Strikes</div>
            <div style="font-size:1.05rem; font-weight:700; color:#0f172a; margin-bottom:2px;">Offset: ${signal['offset']:,.0f}</div>
            <div class="metric-sub">CE: ${signal['intended_ce']:,.0f} | PE: ${signal['intended_pe']:,.0f}</div>
            <div style="font-size:0.75rem; color:#059669; font-weight:600; margin-top:4px;">✅ Formula: Spot ± 2.5×Straddle</div>
        </div>
        <div class="metric-card" style="border-top: 3px solid {step_ce_color};">
            <div class="metric-title">Step 3A: Call Board Audit</div>
            <div style="font-size:1.05rem; font-weight:700; color:{step_ce_color}; margin-bottom:2px;">{signal['ce_status']}</div>
            <div class="metric-sub">{signal['ce_rule_code']} (Δ {signal['ce_greek_delta']:.2f})</div>
            <div style="font-size:0.75rem; color:#475569; margin-top:4px;">${signal['selected_ce']:,.0f} CE Selected</div>
        </div>
        <div class="metric-card" style="border-top: 3px solid {step_pe_color};">
            <div class="metric-title">Step 3B: Put Board Audit</div>
            <div style="font-size:1.05rem; font-weight:700; color:{step_pe_color}; margin-bottom:2px;">{signal['pe_status']}</div>
            <div class="metric-sub">{signal['pe_rule_code']} (Δ {signal['pe_greek_delta']:.2f})</div>
            <div style="font-size:0.75rem; color:#475569; margin-top:4px;">${signal['selected_pe']:,.0f} PE Selected</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # DYNAMIC ORDER EXECUTION CARDS
    # -------------------------------------------------------------------------
    order_heading = "⚡ Exact Orders to Place (Pre-Entry Live Preparation — Updates Every 30s)" if signal.get('is_pre_entry_window') else "⚡ Exact Orders to Place (10:00 PM IST Locked Execution)"
    st.subheader(order_heading)

    curr_choice = st.radio(
        "Display Currency Format:",
        ["💵 USD ($) Primary (Strategy Standard)", "🌐 USD ($) Only", "🇮🇳 INR (₹) Primary"],
        index=0,
        horizontal=True
    )

    if signal.get('is_pre_entry_window'):
        entry_badge = "<span style='background:#fef3c7; color:#b45309; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:700; margin-left:6px; border:1px solid #fde68a;'>⚡ LIVE BID</span>"
        book_label = "Live Order Book:"
    else:
        entry_badge = "<span style='background:#d1fae5; color:#047857; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:700; margin-left:6px; border:1px solid #a7f3d0;'>🔒 10:00 PM LOCKED</span>"
        book_label = "10:00 PM Order Book:"

    ce_badge_html = f"<span style='background:#fef3c7; color:#b45309; font-size:0.7rem; font-weight:700; padding:2px 7px; border-radius:4px; border:1px solid #fde68a;'>{signal['ce_dist']:,.0f} PTS AWAY</span>" if signal['is_ce_sub'] else "<span style='background:#d1fae5; color:#047857; font-size:0.7rem; font-weight:700; padding:2px 7px; border-radius:4px; border:1px solid #a7f3d0;'>EXACT MATCH</span>"
    pe_badge_html = f"<span style='background:#fef3c7; color:#b45309; font-size:0.7rem; font-weight:700; padding:2px 7px; border-radius:4px; border:1px solid #fde68a;'>{signal['pe_dist']:,.0f} PTS AWAY</span>" if signal['is_pe_sub'] else "<span style='background:#d1fae5; color:#047857; font-size:0.7rem; font-weight:700; padding:2px 7px; border-radius:4px; border:1px solid #a7f3d0;'>EXACT MATCH</span>"

    ce_entry_inr = signal['ce_entry_price'] * usd_to_inr
    ce_bid_inr = signal['ce_live_bid'] * usd_to_inr
    ce_ask_inr = signal['ce_live_ask'] * usd_to_inr
    ce_credit_inr = signal['ce_credit'] * usd_to_inr
    ce_sl_inr = signal['ce_sl'] * usd_to_inr
    ce_loss_inr = signal['ce_max_loss'] * usd_to_inr

    pe_entry_inr = signal['pe_entry_price'] * usd_to_inr
    pe_bid_inr = signal['pe_live_bid'] * usd_to_inr
    pe_ask_inr = signal['pe_live_ask'] * usd_to_inr
    pe_credit_inr = signal['pe_credit'] * usd_to_inr
    pe_sl_inr = signal['pe_sl'] * usd_to_inr
    pe_loss_inr = signal['pe_max_loss'] * usd_to_inr

    # Helper formatters based on currency choice
    def fmt_price(usd_val, inr_val):
        if "USD ($) Only" in curr_choice:
            return f"&#36;{usd_val:,.2f} USD"
        elif "INR (₹) Primary" in curr_choice:
            return f"₹{inr_val:,.2f} RS <span style='color:#64748b; font-size:0.82rem;'>(&#36;{usd_val:,.2f} USD)</span>"
        else:
            return f"&#36;{usd_val:,.2f} USD <span style='color:#64748b; font-size:0.82rem;'>(₹{inr_val:,.2f} RS)</span>"

    def fmt_book(usd_b, usd_a, inr_b, inr_a):
        if "USD ($) Only" in curr_choice:
            return f"&#36;{usd_b:,.1f} / &#36;{usd_a:,.1f} USD"
        elif "INR (₹) Primary" in curr_choice:
            return f"₹{inr_b:,.0f} / ₹{inr_a:,.0f} RS <span style='color:#64748b; font-size:0.8rem;'>(&#36;{usd_b:,.1f} / &#36;{usd_a:,.1f})</span>"
        else:
            return f"&#36;{usd_b:,.1f} / &#36;{usd_a:,.1f} USD <span style='color:#64748b; font-size:0.8rem;'>(₹{inr_b:,.0f} / ₹{inr_a:,.0f} RS)</span>"

    def fmt_credit(usd_c, inr_c):
        if "USD ($) Only" in curr_choice:
            return f"&#36;{usd_c:,.2f} USDT"
        elif "INR (₹) Primary" in curr_choice:
            return f"₹{inr_c:,.2f} RS <span style='color:#64748b; font-size:0.82rem;'>(&#36;{usd_c:,.2f} USDT)</span>"
        else:
            return f"&#36;{usd_c:,.2f} USDT <span style='color:#64748b; font-size:0.82rem;'>(₹{inr_c:,.2f} RS)</span>"

    def fmt_sl(usd_s, inr_s):
        if "USD ($) Only" in curr_choice:
            return f"&#36;{usd_s:,.2f} USD (3.0×)"
        elif "INR (₹) Primary" in curr_choice:
            return f"₹{inr_s:,.2f} RS <span style='color:#64748b; font-size:0.82rem;'>(&#36;{usd_s:,.2f} USD) (3.0×)</span>"
        else:
            return f"&#36;{usd_s:,.2f} USD <span style='color:#64748b; font-size:0.82rem;'>(₹{inr_s:,.2f} RS) (3.0×)</span>"

    def fmt_loss(usd_l, inr_l):
        if "USD ($) Only" in curr_choice:
            return f"-&#36;{usd_l:,.2f} USDT"
        elif "INR (₹) Primary" in curr_choice:
            return f"-₹{inr_l:,.2f} RS <span style='color:#64748b; font-size:0.82rem;'>(-&#36;{usd_l:,.2f} USDT)</span>"
        else:
            return f"-&#36;{usd_l:,.2f} USDT <span style='color:#64748b; font-size:0.82rem;'>(-₹{inr_l:,.2f} RS)</span>"

    ord1, ord2 = st.columns(2)

    # CALL LEG COLUMN
    with ord1:
        if signal['ce_status'] == "QUEUE_SELL":
            st.markdown(f"""<div class="order-card-call">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; flex-wrap:wrap; gap:6px;">
    <span style="font-size:1.15rem; font-weight:bold; color:#dc2626;">🔴 SELL CALL (CE) LEG</span>
    {ce_badge_html}
</div>
<div style="font-size:2.2rem; font-weight:bold; color:#0f172a; margin-bottom:6px; line-height:1.2;">
    &#36;{signal['selected_ce']:,.0f} CE
</div>
<div style="font-size:0.88rem; color:#64748b; margin-bottom:14px;">
    Symbol: <b style="color:#0f172a;">{signal['ce_symbol']}</b> &nbsp;|&nbsp; Greeks Delta: <b style="color:#dc2626;">{signal['ce_greek_delta']:.4f}</b>
</div>
<hr style="border:none; border-top:1px solid #e2e8f0; margin:12px 0;">
<div class="order-grid">
    <div>Quantity: <b style="color:#0f172a;">{signal['quantity']} BTC</b></div>
    <div>Limit Price: <b style="color:#059669; font-size:1.02rem;">{fmt_price(signal['ce_entry_price'], ce_entry_inr)}</b> {entry_badge}</div>
    <div>{book_label} <b style="color:#0f172a;">{fmt_book(signal['ce_live_bid'], signal['ce_live_ask'], ce_bid_inr, ce_ask_inr)}</b></div>
    <div>Gross Credit: <b style="color:#059669; font-size:1.05rem;">{fmt_credit(signal['ce_credit'], ce_credit_inr)}</b></div>
    <div><b>200% STOP LOSS:</b> <b style="color:#dc2626; font-size:1.05rem;">{fmt_sl(signal['ce_sl'], ce_sl_inr)}</b></div>
    <div>Max Loss at SL: <b style="color:#dc2626;">{fmt_loss(signal['ce_max_loss'], ce_loss_inr)}</b></div>
</div>
</div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="order-card-skipped">
                <div style="font-size:1.15rem; font-weight:bold; color:#dc2626; margin-bottom:8px;">
                    🚫 CALL LEG (CE): SKIPPED TONIGHT
                </div>
                <div style="font-size:0.92rem; color:#0f172a; margin-bottom:10px;">
                    <b>Reason:</b> Outside Delta Exchange Board Range (Bullish Surge Filter Triggered)
                </div>
                <div style="font-size:0.84rem; color:#64748b; line-height:1.45;">
                    Delta Exchange creates contracts ±4% to ±5% around spot. During strong BTC upward momentum, Call strikes move out of range. 
                    <b>Strategy Rule:</b> Do not cancel the trade! Execute the available Put leg cleanly. PE-only trades achieved a <b>95.15% Win Rate</b> in the backtest!
                </div>
            </div>
            """, unsafe_allow_html=True)

    # PUT LEG COLUMN
    with ord2:
        if signal['pe_status'] == "QUEUE_SELL":
            st.markdown(f"""<div class="order-card-put">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; flex-wrap:wrap; gap:6px;">
    <span style="font-size:1.15rem; font-weight:bold; color:#059669;">🟢 SELL PUT (PE) LEG</span>
    {pe_badge_html}
</div>
<div style="font-size:2.2rem; font-weight:bold; color:#0f172a; margin-bottom:6px; line-height:1.2;">
    &#36;{signal['selected_pe']:,.0f} PE
</div>
<div style="font-size:0.88rem; color:#64748b; margin-bottom:14px;">
    Symbol: <b style="color:#0f172a;">{signal['pe_symbol']}</b> &nbsp;|&nbsp; Greeks Delta: <b style="color:#059669;">{signal['pe_greek_delta']:.4f}</b>
</div>
<hr style="border:none; border-top:1px solid #e2e8f0; margin:12px 0;">
<div class="order-grid">
    <div>Quantity: <b style="color:#0f172a;">{signal['quantity']} BTC</b></div>
    <div>Limit Price: <b style="color:#059669; font-size:1.02rem;">{fmt_price(signal['pe_entry_price'], pe_entry_inr)}</b> {entry_badge}</div>
    <div>{book_label} <b style="color:#0f172a;">{fmt_book(signal['pe_live_bid'], signal['pe_live_ask'], pe_bid_inr, pe_ask_inr)}</b></div>
    <div>Gross Credit: <b style="color:#059669; font-size:1.05rem;">{fmt_credit(signal['pe_credit'], pe_credit_inr)}</b></div>
    <div><b>200% STOP LOSS:</b> <b style="color:#dc2626; font-size:1.05rem;">{fmt_sl(signal['pe_sl'], pe_sl_inr)}</b></div>
    <div>Max Loss at SL: <b style="color:#dc2626;">{fmt_loss(signal['pe_max_loss'], pe_loss_inr)}</b></div>
</div>
</div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="order-card-skipped">
                <div style="font-size:1.15rem; font-weight:bold; color:#dc2626; margin-bottom:8px;">
                    🚫 PUT LEG (PE): SKIPPED TONIGHT
                </div>
                <div style="font-size:0.92rem; color:#0f172a; margin-bottom:10px;">
                    <b>Reason:</b> Outside Delta Exchange Board Range (Bearish Dump Filter Triggered)
                </div>
                <div style="font-size:0.84rem; color:#64748b; line-height:1.45;">
                    Delta Exchange creates contracts ±4% to ±5% around spot. During strong BTC downward momentum, Put strikes move out of range. 
                    <b>Strategy Rule:</b> Do not cancel the trade! Execute the available Call leg cleanly. CE-only trades achieved a <b>94.68% Win Rate</b> in the backtest!
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Net Initial Credit Notice
    active_credit = (signal['ce_credit'] if signal['ce_status'] == "QUEUE_SELL" else 0.0) + (signal['pe_credit'] if signal['pe_status'] == "QUEUE_SELL" else 0.0)
    active_credit_rs = active_credit * usd_to_inr
    
    if "USD ($) Only" in curr_choice:
        credit_txt = f"**${active_credit:,.2f} USDT**"
    elif "INR (₹) Primary" in curr_choice:
        credit_txt = f"**₹{active_credit_rs:,.2f} RS** (${active_credit:,.2f} USDT)"
    else:
        credit_txt = f"**${active_credit:,.2f} USDT** (₹{active_credit_rs:,.2f} RS)"

    if signal.get('is_pre_entry_window'):
        st.info(f"💡 **Estimated Premium Credit To Collect:** {credit_txt}. Pre-entry live mode updates every 30 seconds. At 10:00:00 PM IST, this candle closes and values lock permanently.")
    else:
        st.info(f"💡 **Total Initial Premium Credit Collected:** {credit_txt}. Fixed 10:00 PM IST execution values do not fluctuate on page refresh. Exit at 2-Day Expiry ({signal['expiry_date']} at {signal['exit_time']}) or when 200% Stop Loss is hit.")

    # -------------------------------------------------------------------------
    # DELTA EXCHANGE ACTIVE BOARD SCANNER TABLE
    # -------------------------------------------------------------------------
    with st.expander("🔍 Delta Exchange 2-Day Expiry Board Range Scanner (All Listed Contracts)", expanded=False):
        if signal.get("all_chain_prods"):
            chain_df = pd.DataFrame(signal["all_chain_prods"])
            
            # Format columns
            chain_df["Strike"] = chain_df["strike"].apply(lambda x: f"${x:,.0f}")
            chain_df["CE Delta"] = chain_df["ce_delta"].apply(lambda x: f"{x:.4f}" if x is not None else "-")
            chain_df["CE Bid/Ask"] = chain_df.apply(lambda r: f"${r['ce_bid']:,.1f} / ${r['ce_ask']:,.1f}", axis=1)
            chain_df["PE Delta"] = chain_df["pe_delta"].apply(lambda x: f"{x:.4f}" if x is not None else "-")
            chain_df["PE Bid/Ask"] = chain_df.apply(lambda r: f"${r['pe_bid']:,.1f} / ${r['pe_ask']:,.1f}", axis=1)

            def get_tag(r):
                tags = []
                if r["is_atm"]: tags.append("🎯 ATM Base")
                if r["is_selected_ce"]: tags.append("🔴 SOLD CE")
                if r["is_selected_pe"]: tags.append("🟢 SOLD PE")
                if r["is_intended_ce"] and not r["is_selected_ce"]: tags.append("⚠️ Target CE (Unlisted)")
                if r["is_intended_pe"] and not r["is_selected_pe"]: tags.append("⚠️ Target PE (Unlisted)")
                return " | ".join(tags) if tags else "Listed"

            chain_df["Board Status"] = chain_df.apply(get_tag, axis=1)

            cols_to_show = ["Strike", "CE Delta", "CE Bid/Ask", "PE Delta", "PE Bid/Ask", "Board Status"]
            st.dataframe(chain_df[cols_to_show], use_container_width=True, hide_index=True)
        else:
            st.caption("Live option chain board details loaded.")

# -----------------------------------------------------------------------------
# MAIN APP ENTRY POINT (TIMING LOGIC & DUAL-FRAGMENT DISPATCH)
# -----------------------------------------------------------------------------
ist_tz = pytz.timezone("Asia/Kolkata")
now_ist = datetime.now(ist_tz)
is_natural_pre_entry = (now_ist.hour == 21 and now_ist.minute >= 55)

col_title, col_ctrl = st.columns([3, 2])
with col_title:
    st.title("🎯 Delta Execution Guide: Which Side to Sell Tonight?")
    st.caption("Deterministic evaluation: BTC Perp & Delta Exchange 2-Day Board Range. Auto-updates every 30s during 9:55–10:00 PM IST.")

with col_ctrl:
    col_tgl, col_btn = st.columns([2, 1])
    with col_tgl:
        st.write("")
        test_preview = st.toggle("⚡ Preview 9:55-10 PM Live", value=False, help="Turn on anytime to test live 30-second preparation feed & countdown.")
    with col_btn:
        st.write("")
        if st.button("🔄 Refresh", type="primary"):
            st.rerun()

if test_preview:
    trade_mode = "live_pre_entry"
    is_live_mode = True
elif is_natural_pre_entry:
    trade_mode = "live_pre_entry"
    is_live_mode = True
elif now_ist.hour >= 22:
    trade_mode = "locked_10pm"
    is_live_mode = False
else:
    trade_mode = "auto"
    is_live_mode = False

if is_live_mode:
    @st.fragment(run_every=30)
    def live_terminal():
        with st.spinner("Connecting to Delta Exchange API (30s poll)..."):
            sig = get_complete_trade_ticket(mode=trade_mode)

        if not sig:
            st.error("Unable to connect to Delta Exchange API. Please check your network connection.")
            return

        # If in auto mode and candle just locked (at 10:00:00 PM), trigger full rerun to freeze
        if not test_preview and sig.get("is_entry_locked"):
            st.rerun()

        render_main_dashboard(sig, is_live_mode=True, usd_to_inr=getattr(config, "USD_TO_INR", 85.0))
        
        # JavaScript auto-reload fallback (fires at 32 seconds if websocket pauses)
        import streamlit.components.v1 as components
        components.html(
            """
            <script>
            if (!window.__prep_timer) {
                window.__prep_timer = setTimeout(function() {
                    window.__prep_timer = null;
                    window.location.reload();
                }, 32000);
            }
            </script>
            """,
            height=0
        )
    live_terminal()
else:
    @st.fragment
    def locked_terminal():
        with st.spinner("Loading closed 10:00 PM candle execution..."):
            sig = get_complete_trade_ticket(mode=trade_mode)

        if not sig:
            st.error("Unable to connect to Delta Exchange API. Please check your network connection.")
            return

        render_main_dashboard(sig, is_live_mode=False, usd_to_inr=getattr(config, "USD_TO_INR", 85.0))
    locked_terminal()
