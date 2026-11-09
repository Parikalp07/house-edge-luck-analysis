"""
House edge vs luck: a worked example for an online-games operator.

The question a director asks every Monday:
    "What did we earn last week, why, and how much of it was luck?"

This script answers it with SAMPLE data (simulated: no real players, no real money,
and the game settings below are illustrative, not any company's real numbers).

What it does
  1. Simulates bets for three games over 12 weeks.
  2. For every game-week it runs two checks against what the maths says should happen:
       - MONEY check:    did the house keep what the house edge predicts?
       - WIN-RATE check: did players win as often as the game's odds say they should?
     The money result is noisy (a few big bets swing it). The win rate ignores bet size,
     so it is much sharper at telling a real fault from bad luck.
  3. Writes a weekly table, two charts and a plain-English note a director can repeat.
  4. Tests the method itself: how often does each check raise a false alarm, and how
     often does it catch a real problem?

One game-week has a planted problem (the Wheel in week 9 pays out too much).
The analysis is NOT told where it is.

Run:   python house_edge_luck_analysis.py
Needs: numpy, pandas, matplotlib
"""
from pathlib import Path
from statistics import NormalDist

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).parent / "output"
OUT.mkdir(exist_ok=True)
SEED = 2026

# Illustrative settings. edge = share of stakes the house expects to keep, long run.
GAMES = {
    "Dice":  dict(edge=0.010, p_range=(0.05, 0.95), bets=(40_000, 70_000)),
    "Wheel": dict(edge=0.030, p_range=(0.10, 0.50), bets=(15_000, 30_000)),
    "Slots": dict(edge=0.040, p_range=(0.01, 0.20), bets=(3_000, 9_000)),
}
WEEKS = range(1, 13)
BUG_GAME, BUG_WEEK, BUG_TRUE_EDGE = "Wheel", 9, -0.08   # planted: pays as if the house LOSES 8%
N_TESTS = len(GAMES) * len(WEEKS)
Z_CRIT = NormalDist().inv_cdf(1 - 0.025 / N_TESTS)       # Bonferroni: ~5% false alarms per full run


def simulate(rng, bug=True, keep_sample=False):
    """One run of 12 weeks x 3 games. A bet wins with probability p and pays stake * m,
    where m = (1 - edge) / p, so the expected house result is exactly edge * stake."""
    recs, sample = [], []
    for game, g in GAMES.items():
        for week in WEEKS:
            n = int(rng.integers(*g["bets"]))
            stake = np.round(rng.lognormal(2.0, 1.0, n), 2).clip(0.1, 2000)
            whale = rng.random(n) < 0.01                      # 1% of bets are large
            stake[whale] = np.round(rng.lognormal(5.5, 0.6, whale.sum()), 2)
            p = rng.uniform(*g["p_range"], n)
            m = (1 - g["edge"]) / p                           # advertised payout multiplier
            true_edge = BUG_TRUE_EDGE if (bug and (game, week) == (BUG_GAME, BUG_WEEK)) else g["edge"]
            p_true = np.minimum(p * (1 - true_edge) / (1 - g["edge"]), 0.999)
            win = rng.random(n) < p_true
            house = stake * (1 - m * win)                     # + house keeps, - house pays out
            recs.append(dict(
                game=game, week=week, bets=n, handle=stake.sum(), earned=house.sum(),
                expected=(stake * g["edge"]).sum(),
                var=(stake**2 * m**2 * p * (1 - p)).sum(),    # exact variance of the money result
                wins=int(win.sum()), exp_wins=p.sum(),        # wins seen vs wins the maths expects
                var_wins=(p * (1 - p)).sum()))
            if keep_sample:
                sample.append(pd.DataFrame(dict(game=game, week=week, stake=stake, win_prob=p,
                                                payout_mult=m, house_result=house)).sample(150, random_state=week))
    return pd.DataFrame(recs), (pd.concat(sample) if keep_sample else None)


def add_stats(agg):
    agg = agg.copy()
    agg["se"] = np.sqrt(agg["var"])
    agg["hold_pct"] = 100 * agg["earned"] / agg["handle"]
    agg["expected_hold_pct"] = 100 * agg["expected"] / agg["handle"]
    agg["z_money"] = (agg["earned"] - agg["expected"]) / agg["se"]
    agg["lo95_pct"] = agg["expected_hold_pct"] - 1.96 * 100 * agg["se"] / agg["handle"]
    agg["hi95_pct"] = agg["expected_hold_pct"] + 1.96 * 100 * agg["se"] / agg["handle"]
    agg["z_wins"] = (agg["wins"] - agg["exp_wins"]) / np.sqrt(agg["var_wins"])
    agg["flag_money"] = agg["z_money"].abs() > Z_CRIT      # money gap looks too big
    agg["flag"] = agg["z_wins"].abs() > Z_CRIT             # players win too often or too rarely: investigate
    agg["swing"] = agg["flag_money"] & ~agg["flag"]        # big money swing, normal win rate: luck from a few big bets
    return agg


# ------------------------------------------------------------------ main run
agg, sample = simulate(np.random.default_rng(SEED), bug=True, keep_sample=True)
agg = add_stats(agg)
agg.drop(columns=["var", "var_wins"]).round(3).to_csv(OUT / "weekly_summary.csv", index=False)
sample.round(4).to_csv(OUT / "sample_bets.csv", index=False)

# ------------------------------------------------------------------ chart 1: money vs expected
fig, axes = plt.subplots(1, 3, figsize=(15, 4.2), sharex=True)
for ax, (game, d) in zip(axes, agg.groupby("game", sort=False)):
    ax.fill_between(d["week"], d["lo95_pct"], d["hi95_pct"], color="#9fd8d0", alpha=0.6,
                    label="Range luck explains (95%)")
    ax.plot(d["week"], d["expected_hold_pct"], color="#0a7ea8", lw=2, label="Expected hold")
    ax.plot(d["week"], d["hold_pct"], "o-", color="#222", ms=4, lw=1, label="Actual hold")
    bad = d[d["flag"]]
    ax.scatter(bad["week"], bad["hold_pct"], s=140, facecolors="none", edgecolors="#d7263d", lw=2,
               label="Investigate (win rate off)")
    ax.set_title(game)
    ax.set_xlabel("Week")
    ax.axhline(0, color="#999", lw=0.6)
axes[0].set_ylabel("House hold (% of stakes)")
axes[0].legend(fontsize=8, loc="lower left")
fig.suptitle("Earned vs expected. The shaded band is how far luck alone can plausibly push earnings")
fig.tight_layout()
fig.savefig(OUT / "chart_hold_vs_expected.png", dpi=150)
plt.close(fig)

# ------------------------------------------------------------------ chart 2: the two checks side by side
fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
colors = {"Dice": "#0a7ea8", "Wheel": "#e0912f", "Slots": "#6a5acd"}
w = 0.27
panels = ((axes[0], "z_money", "Money check: did the house earn what the maths expects? (noisy: a few big bets swing it)"),
          (axes[1], "z_wins", "Win-rate check: did players win as often as the maths says? (sharp: ignores bet size)"))
for ax, col, title in panels:
    for i, (game, d) in enumerate(agg.groupby("game", sort=False)):
        ax.bar(d["week"] + (i - 1) * w, d[col], width=w, color=colors[game], label=game)
    for y in (Z_CRIT, -Z_CRIT):
        ax.axhline(y, color="#d7263d", ls="--", lw=1)
    for y in (1.96, -1.96):
        ax.axhline(y, color="#999", ls=":", lw=1)
    ax.set_title(title, fontsize=10)
    ax.set_ylabel("Gap in standard errors (z)")
axes[1].set_xlabel("Week")
axes[0].legend(ncol=3)
fig.suptitle(f"Red dashed line = investigate (|z| > {Z_CRIT:.2f}, set so a clean 12-week run rarely raises a false alarm)")
fig.tight_layout()
fig.savefig(OUT / "chart_z_scores.png", dpi=150)
plt.close(fig)

# ------------------------------------------------------------------ director summary
tot_h, tot_e, tot_x = agg["handle"].sum(), agg["earned"].sum(), agg["expected"].sum()
lines = [f"Across {len(WEEKS)} weeks and {len(GAMES)} games, players staked {tot_h:,.0f} USDT. The house kept "
         f"{tot_e:,.0f} USDT ({100*tot_e/tot_h:.2f}% of stakes). The maths says it should have kept "
         f"{tot_x:,.0f} USDT ({100*tot_x/tot_h:.2f}%)."]
for _, r in agg[agg["flag"]].sort_values("z_wins", key=abs, ascending=False).iterrows():
    direction = "more" if r["z_wins"] > 0 else "less"
    lines.append(
        f"INVESTIGATE: {r['game']}, week {int(r['week'])}. Players won {int(r['wins']):,} bets but the maths "
        f"expects about {r['exp_wins']:,.0f}: {direction} often than designed, {abs(r['z_wins']):.1f} standard errors "
        f"away. Luck does not do this. In money terms the house kept {r['earned']:,.0f} USDT against "
        f"{r['expected']:,.0f} expected ({r['z_money']:+.1f} standard errors), so earnings alone can hide it. "
        f"Next step: check the game's payout logic and the bet logs for that week.")
for _, r in agg[agg["swing"]].sort_values("z_money", key=abs, ascending=False).iterrows():
    lines.append(
        f"LUCK, NOT A FAULT: {r['game']}, week {int(r['week'])}. The house kept {r['earned']:,.0f} USDT against "
        f"{r['expected']:,.0f} expected, a big miss ({r['z_money']:+.1f} standard errors). But players won "
        f"{int(r['wins']):,} bets against {r['exp_wins']:,.0f} expected ({r['z_wins']:+.1f}), which is normal. "
        f"A few large stakes landed the players' way. Keep watching; no action needed.")
lines.append(f"{100*(agg['z_wins'].abs() < 1.96).mean():.0f}% of game-weeks have a normal win rate (|z| < 1.96). "
             f"For honest data about 95% should.")
(OUT / "director_summary.txt").write_text("\n\n".join(lines) + "\n", encoding="utf-8")

# ------------------------------------------------------------------ test the method itself
RUNS = 300
fa_money = fa_wins = caught_money = caught_wins = 0
rng = np.random.default_rng(SEED + 1)
for _ in range(RUNS):
    clean = add_stats(simulate(rng, bug=False)[0])
    fa_money += bool(clean["flag_money"].any())
    fa_wins += bool(clean["flag"].any())
    bugged = add_stats(simulate(rng, bug=True)[0])
    row = bugged[(bugged.game == BUG_GAME) & (bugged.week == BUG_WEEK)].iloc[0]
    caught_money += bool(row["flag_money"])
    caught_wins += bool(row["flag"])
pc = lambda x: f"{100*x/RUNS:.0f}%"
method = (f"Method check over {RUNS} simulated 12-week runs each.\n"
          f"  Money check alone: false alarm in {pc(fa_money)} of clean runs; planted problem caught in {pc(caught_money)}.\n"
          f"  Win-rate check:    false alarm in {pc(fa_wins)} of clean runs; planted problem caught in {pc(caught_wins)}.")
(OUT / "method_check.txt").write_text(method + "\n", encoding="utf-8")

# ------------------------------------------------------------------ print
print("\n\n".join(lines))
print("\n" + method)
print(f"\nAnswer key: planted problem = {BUG_GAME} week {BUG_WEEK}. Flagged = "
      f"{[(r.game, int(r.week)) for r in agg[agg.flag].itertuples()]}; money-swing-only = "
      f"{[(r.game, int(r.week)) for r in agg[agg.swing].itertuples()]}")
print(f"z threshold: {Z_CRIT:.2f} ({N_TESTS} checks)")
print(agg[agg.game == 'Wheel'][['week', 'handle', 'earned', 'expected', 'z_money', 'wins', 'exp_wins', 'z_wins', 'flag', 'swing']]
      .round(2).to_string(index=False))
