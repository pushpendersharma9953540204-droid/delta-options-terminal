import os
import shutil
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def generate_guide_image(output_path="delta_execution_guide.jpg"):
    # High resolution figure: 14 x 18 inches at 250 DPI = 3500 x 4500 pixels
    fig, ax = plt.subplots(figsize=(14, 18), dpi=250)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    fig.patch.set_facecolor("#f8fafc")

    # Helper function for rounded rectangles
    def draw_card(x, y, w, h, bg_color="#ffffff", border_color="#e2e8f0", border_width=1.5, radius=1.5):
        rect = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle=f"round,pad=0.2,rounding_size={radius}",
            facecolor=bg_color,
            edgecolor=border_color,
            linewidth=border_width,
            zorder=2
        )
        ax.add_patch(rect)

    def draw_circle_badge(x, y, r, color):
        circle = patches.Circle((x, y), r, facecolor=color, edgecolor="none", zorder=4)
        ax.add_patch(circle)

    # ----------------------------------------------------
    # 1. HEADER SECTION
    # ----------------------------------------------------
    draw_card(3, 91, 94, 7.5, bg_color="#ffffff", border_color="#cbd5e1", border_width=2, radius=2)
    ax.text(50, 96.2, "DELTA EXCHANGE - MECHANICAL EXECUTION GUIDE", 
            ha="center", va="center", fontsize=18, fontweight="bold", color="#0f172a", zorder=3)
    ax.text(50, 93.9, "How to Replicate AlgoTest's 86.5% Win Rate Strategy with Zero Human Guesswork", 
            ha="center", va="center", fontsize=10.5, color="#475569", zorder=3)
    ax.text(50, 91.9, "Underlying: BTC Perpetuals  |  Entry: 10:00 PM IST  |  Expiry: 2-Day  |  Offset: ATM Straddle x 2.5  |  Stop Loss: 200% (3.0x)", 
            ha="center", va="center", fontsize=8.5, fontweight="semibold", color="#2563eb", zorder=3)

    # ----------------------------------------------------
    # 2. SECTION: PERFORMANCE BREAKDOWN (THE DISCOVERY)
    # ----------------------------------------------------
    draw_card(3, 75.5, 94, 14.0, bg_color="#ffffff", border_color="#e2e8f0", border_width=1.5, radius=2)
    ax.text(5, 87.5, "1. THE CORE DISCOVERY: HOW ALGOTEST ACHIEVES AN 86.5% WIN RATE", 
            ha="left", va="center", fontsize=12, fontweight="bold", color="#1e293b", zorder=3)
    ax.text(5, 85.6, "AlgoTest evaluates each leg independently. On 197 days, one leg was unlisted on Delta Exchange, so it executed the single available leg.", 
            ha="left", va="center", fontsize=9.0, color="#64748b", zorder=3)

    # Mini Card 1: PE Only
    draw_card(5, 76.5, 28, 7.5, bg_color="#eff6ff", border_color="#bfdbfe", border_width=1.5, radius=1.2)
    draw_circle_badge(8, 82.2, 0.8, "#2563eb")
    ax.text(10, 82.2, "PE ONLY TRADED (CE Unlisted)", ha="left", va="center", fontsize=9.2, fontweight="bold", color="#1d4ed8", zorder=3)
    ax.text(19, 80.4, "103 Days (28.9% of Year) - BTC was Pumping", ha="center", va="center", fontsize=7.8, color="#475569", zorder=3)
    ax.text(19, 78.7, "Win Rate: 95.15% (98 Wins / 5 Losses)", ha="center", va="center", fontsize=8.8, fontweight="bold", color="#16a34a", zorder=3)
    ax.text(19, 77.2, "Net Profit: +$145.45 USD (Rs. 12,363 RS)", ha="center", va="center", fontsize=8.2, fontweight="bold", color="#0f172a", zorder=3)

    # Mini Card 2: CE Only
    draw_card(36, 76.5, 28, 7.5, bg_color="#fffbeb", border_color="#fde68a", border_width=1.5, radius=1.2)
    draw_circle_badge(39, 82.2, 0.8, "#d97706")
    ax.text(41, 82.2, "CE ONLY TRADED (PE Unlisted)", ha="left", va="center", fontsize=9.2, fontweight="bold", color="#b45309", zorder=3)
    ax.text(50, 80.4, "94 Days (26.4% of Year) - BTC was Dumping", ha="center", va="center", fontsize=7.8, color="#475569", zorder=3)
    ax.text(50, 78.7, "Win Rate: 94.68% (89 Wins / 4 Losses)", ha="center", va="center", fontsize=8.8, fontweight="bold", color="#16a34a", zorder=3)
    ax.text(50, 77.2, "Net Profit: +$104.00 USD (Rs. 8,840 RS)", ha="center", va="center", fontsize=8.2, fontweight="bold", color="#0f172a", zorder=3)

    # Mini Card 3: Both Legs
    draw_card(67, 76.5, 28, 7.5, bg_color="#f0fdf4", border_color="#bbf7d0", border_width=1.5, radius=1.2)
    draw_circle_badge(70, 82.2, 0.8, "#16a34a")
    ax.text(72, 82.2, "BOTH LEGS (CE + PE Traded)", ha="left", va="center", fontsize=9.2, fontweight="bold", color="#15803d", zorder=3)
    ax.text(81, 80.4, "159 Days (44.7% of Year) - BTC Flat / Rangebound", ha="center", va="center", fontsize=7.8, color="#475569", zorder=3)
    ax.text(81, 78.7, "Win Rate: 76.10% (121 Wins / 38 Losses)", ha="center", va="center", fontsize=8.8, fontweight="bold", color="#16a34a", zorder=3)
    ax.text(81, 77.2, "Net Profit: +$240.71 USD (Rs. 20,460 RS)", ha="center", va="center", fontsize=8.2, fontweight="bold", color="#0f172a", zorder=3)

    # ----------------------------------------------------
    # 3. SECTION: THE MECHANICAL EXECUTION FLOWCHART
    # ----------------------------------------------------
    draw_card(3, 27, 94, 47.0, bg_color="#ffffff", border_color="#e2e8f0", border_width=1.5, radius=2)
    ax.text(5, 72.3, "2. THE DETERMINISTIC 10:00 PM IST EXECUTION FLOWCHART", 
            ha="left", va="center", fontsize=12, fontweight="bold", color="#1e293b", zorder=3)
    ax.text(5, 70.6, "Follow these steps in strict sequence every night. No discretion, human emotion, or second-guessing required.", 
            ha="left", va="center", fontsize=9.0, color="#64748b", zorder=3)

    # Box 1: 10:00 PM Trigger
    draw_card(20, 64.2, 60, 4.6, bg_color="#f1f5f9", border_color="#94a3b8", border_width=1.5, radius=1)
    ax.text(50, 67.0, "STEP 1: 10:00:00 PM IST (Daily Entry Window)", ha="center", va="center", fontsize=10, fontweight="bold", color="#0f172a", zorder=3)
    ax.text(50, 65.3, "Record BTC Spot Price and calculate ATM Straddle Premium for 2-Day Expiry", ha="center", va="center", fontsize=8.2, color="#475569", zorder=3)

    # Arrow down
    ax.annotate("", xy=(50, 61.2), xytext=(50, 64.2), arrowprops=dict(arrowstyle="->", lw=2, color="#64748b"))

    # Box 2: Target Calculation
    draw_card(15, 56.8, 70, 4.4, bg_color="#eff6ff", border_color="#93c5fd", border_width=1.5, radius=1)
    ax.text(50, 59.6, "STEP 2: Calculate Target Mathematical Strikes", ha="center", va="center", fontsize=9.8, fontweight="bold", color="#1d4ed8", zorder=3)
    ax.text(50, 57.9, "Offset = ATM Straddle x 2.5   |   Target CE = Spot + Offset   |   Target PE = Spot - Offset", ha="center", va="center", fontsize=8.2, fontweight="semibold", color="#1e40af", zorder=3)

    # Arrows split
    ax.annotate("", xy=(30, 53.5), xytext=(45, 56.8), arrowprops=dict(arrowstyle="->", lw=2, color="#64748b"))
    ax.annotate("", xy=(70, 53.5), xytext=(55, 56.8), arrowprops=dict(arrowstyle="->", lw=2, color="#64748b"))

    # Left Column: Call Leg (CE)
    draw_card(5, 42.0, 43, 11.5, bg_color="#f8fafc", border_color="#cbd5e1", border_width=1.5, radius=1.2)
    ax.text(26.5, 51.8, "CALL LEG (CE) EVALUATION", ha="center", va="center", fontsize=9.5, fontweight="bold", color="#0f172a", zorder=3)
    ax.text(26.5, 49.6, "Check Delta Exchange 2-Day Board:", ha="center", va="center", fontsize=8.0, color="#64748b", zorder=3)
    ax.text(26.5, 47.6, "[A] Is Target CE listed?  ->  SELL TARGET CE", ha="center", va="center", fontsize=8.0, fontweight="bold", color="#16a34a", zorder=3)
    ax.text(26.5, 45.4, "[B] Target beyond board?  ->  SNAP TO CLOSEST AVAILABLE CE", ha="center", va="center", fontsize=7.8, fontweight="bold", color="#2563eb", zorder=3)
    ax.text(26.5, 43.6, "    (AlgoTest takes boundary strike regardless of Delta, e.g. Delta 0.12-0.16)", ha="center", va="center", fontsize=6.8, color="#475569", zorder=3)
    ax.text(26.5, 42.4, "[C] Zero board liquidity/quotes?  ->  SKIP CE LEG", ha="center", va="center", fontsize=7.5, fontweight="semibold", color="#dc2626", zorder=3)

    # Right Column: Put Leg (PE)
    draw_card(52, 42.0, 43, 11.5, bg_color="#f8fafc", border_color="#cbd5e1", border_width=1.5, radius=1.2)
    ax.text(73.5, 51.8, "PUT LEG (PE) EVALUATION", ha="center", va="center", fontsize=9.5, fontweight="bold", color="#0f172a", zorder=3)
    ax.text(73.5, 49.6, "Check Delta Exchange 2-Day Board:", ha="center", va="center", fontsize=8.0, color="#64748b", zorder=3)
    ax.text(73.5, 47.6, "[A] Is Target PE listed?  ->  SELL TARGET PE", ha="center", va="center", fontsize=8.0, fontweight="bold", color="#16a34a", zorder=3)
    ax.text(73.5, 45.4, "[B] Target beyond board?  ->  SNAP TO CLOSEST AVAILABLE PE", ha="center", va="center", fontsize=7.8, fontweight="bold", color="#2563eb", zorder=3)
    ax.text(73.5, 43.6, "    (e.g., 24-Oct-2026: Sold $77,200 PE at Delta 0.13 - No Delta Cap!)", ha="center", va="center", fontsize=6.8, color="#475569", zorder=3)
    ax.text(73.5, 42.4, "[C] Zero board liquidity/quotes?  ->  SKIP PE LEG", ha="center", va="center", fontsize=7.5, fontweight="semibold", color="#dc2626", zorder=3)

    # Arrows join to Execution
    ax.annotate("", xy=(45, 38.8), xytext=(26.5, 42.0), arrowprops=dict(arrowstyle="->", lw=2, color="#64748b"))
    ax.annotate("", xy=(55, 38.8), xytext=(73.5, 42.0), arrowprops=dict(arrowstyle="->", lw=2, color="#64748b"))

    # Box 3: Execution
    draw_card(15, 34.2, 70, 4.6, bg_color="#f0fdf4", border_color="#86efac", border_width=2, radius=1)
    ax.text(50, 37.0, "STEP 3: EXECUTE ALL RESOLVED LEG(S) (0.02 BTC Size)", ha="center", va="center", fontsize=10, fontweight="bold", color="#15803d", zorder=3)
    ax.text(50, 35.2, "Both Legs (159 days) OR Single Leg Only (197 days) - Zero Discretion, Pure Algorithmic Execution!", ha="center", va="center", fontsize=8.2, color="#166534", zorder=3)

    # Arrow down to Stop Loss
    ax.annotate("", xy=(50, 31.5), xytext=(50, 34.2), arrowprops=dict(arrowstyle="->", lw=2, color="#64748b"))

    # Box 4: Risk Management
    draw_card(15, 27.8, 70, 3.7, bg_color="#fef2f2", border_color="#fca5a5", border_width=1.5, radius=1)
    ax.text(50, 30.1, "STEP 4: PLACE 200% STOP LOSS (3.0x ENTRY PREMIUM)", ha="center", va="center", fontsize=9.2, fontweight="bold", color="#b91c1c", zorder=3)
    ax.text(50, 28.6, "SL Price = Entry Price x 3.0. Hold winning positions until 17:29 IST settlement on Expiry Day.", ha="center", va="center", fontsize=7.8, color="#7f1d1d", zorder=3)

    # ----------------------------------------------------
    # 4. SECTION: WHY THIS WORKS (THE UNDERLYING DYNAMICS)
    # ----------------------------------------------------
    draw_card(3, 4.5, 94, 21.0, bg_color="#ffffff", border_color="#e2e8f0", border_width=1.5, radius=2)
    ax.text(5, 23.2, "3. WHY THE MECHANICAL FILTER WORKS: THE HIDDEN MOMENTUM EDGE", 
            ha="left", va="center", fontsize=11.5, fontweight="bold", color="#1e293b", zorder=3)

    bullet_y = 21.0
    spacing = 3.9
    bullets = [
        ("The 'Closest Strike' Rule (No Arbitrary Delta Cap):", 
         "AlgoTest does not check Delta thresholds. If target strike is beyond Delta's board, it snaps to the nearest available contract on the chain (e.g., 24-Oct-2026 sold $77,200 PE at Delta 0.13; 06-Nov-2025 sold PE at Delta 0.20). Across the year, 55 trades had Delta > 0.10!"),
        
        ("When BTC Pumps (+1% to +3%):", 
         "Call strikes move out of board range and get skipped. The PE strike remains listed with juicy premium. Selling PE during an upward trend generated 98 Wins vs 5 Losses (95.15% Win Rate, +$145.45 net profit)!"),
        
        ("When BTC Dumps (-1% to -3%):", 
         "Put strikes move out of board range and get skipped. The CE strike remains listed with juicy premium. Selling CE during a downward trend generated 89 Wins vs 4 Losses (94.68% Win Rate, +$104.00 net profit)!"),
        
        ("The Golden Rule of Replicating AlgoTest:", 
         "NEVER reject a trade just because one leg is missing or has a higher Delta. In 55.3% of all days in the backtest, only ONE leg was executed, and those single-leg trades generated 71.8% of the strategy's total profit (Rs. 29,908 RS)!")
    ]

    for title, desc in bullets:
        ax.text(5, bullet_y, title, ha="left", va="center", fontsize=8.8, fontweight="bold", color="#0f172a", zorder=3)
        ax.text(5, bullet_y - 1.4, desc, ha="left", va="center", fontsize=7.8, color="#475569", zorder=3, wrap=True)
        bullet_y -= spacing

    # Footer note
    ax.text(50, 2.2, "Generated for Delta Exchange Short Strangle Strategy  |  Capital: Rs. 5,000 RS  |  1 USD = Rs. 85 RS", 
            ha="center", va="center", fontsize=8, color="#94a3b8", zorder=3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=250, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    
    # Also copy to artifacts directory for web display
    artifact_dir = r"C:\Users\Acer\.gemini\antigravity\brain\cba69691-b4e0-47aa-b266-77c2e75aacf5"
    if os.path.exists(artifact_dir):
        shutil.copy(output_path, os.path.join(artifact_dir, "delta_execution_guide.jpg"))
    print(f"Successfully generated high-quality image at: {output_path}")

if __name__ == "__main__":
    generate_guide_image("delta_execution_guide.jpg")
