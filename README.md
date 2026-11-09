# House edge vs luck: was it the game or just a bad week?

A small, self-contained analysis of the question an online-games operator asks every Monday:
**what did we earn, why, and how much of it was luck?**

All data is **simulated sample data**. There are no real players and no real money, and the game
settings (house edge, win probabilities, volumes) are illustrative. They are not any company's real numbers.

## The answer in four lines

- Over 12 weeks and 3 games, players staked **15.2M USDT**. The house kept **152k USDT (1.00%)**; the maths said about **262k (1.72%)**.
- That 110k shortfall looks scary but is only **1.5 standard errors** from expectation, which is within normal luck.
- **Wheel, week 9 is a real problem.** Players won 8,685 bets where the maths expects about 7,859 (**11.5 standard errors**). Earnings alone hid it (only -1.7 standard errors).
- **Wheel, week 6 is bad luck, not a fault.** The house lost 25k that week, but players won at a normal rate (+1.3 standard errors). A few large bets landed their way.

Charts are in `output/`. The director-ready note is `output/director_summary.txt`, and a one-page memo is in `MEMO.md`.

## The idea, in plain words

Every game has a house edge: a share of all money staked that the house expects to keep in the long run.
In any single week, luck pushes the real result above or below that. The job is to tell
"unlucky week" from "something is wrong".

I run two checks on each game-week:

1. **Money check.** Did the house keep what the edge predicts? The gap is measured in standard errors (a z-score),
   using the exact variance of every bet. This is what the business sees, but it is noisy: a few large stakes
   can swing a week.
2. **Win-rate check.** Did players win as often as the game's odds say they should? This ignores bet size, so it is
   far sharper. A payout bug changes how often players win, and this check sees it even when luck hides it in the money.

Because 36 checks are run, the alarm line is raised to |z| > 3.20 so a clean 12-week run rarely raises a false alarm
(a Bonferroni correction). A plain 1.96 would raise one false alarm about every 20 checks.

## Does the method itself work?

I tested it by simulating 300 clean runs and 300 runs with the planted problem:

| Check | False alarm in a clean 12-week run | Planted problem caught |
|---|---|---|
| Money check alone | 17% | 67% |
| Win-rate check | 7% | 100% |

So the money check alone would both cry wolf and miss real faults. The win-rate check is much better, but its 7% false-alarm rate
is a little above the 5% I designed for. With only 300 runs that gap is within sampling noise, but I would re-test it on real data before relying on it.

## How to run

```
pip install -r requirements.txt
python house_edge_luck_analysis.py
```

It takes about 30 seconds and writes to `output/`:
`weekly_summary.csv`, `sample_bets.csv` (2,000 example bets), `chart_hold_vs_expected.png`, `chart_z_scores.png`,
`director_summary.txt`, `method_check.txt`.

## Limits and what I would do with real data

- The data is simulated, so the result shows the method works, not that any real game has a problem.
- The planted problem is large (the house loses 8% instead of earning 3%). Smaller faults would need more volume to detect.
- The normal approximation is fine for win counts at these volumes, but the money check is skewed by large bets; a bootstrap would be a better reference there.
- With real data I would check: bets by player (bonus abuse, collusion), win rate by payout multiplier, and results by hour of day.
- If an investigation is raised each time, the Bonferroni line should be reviewed against the cost of a missed fault.

## Tools

Python, numpy, pandas, matplotlib. Written with assistance from an AI assistant (Claude); I reviewed the method and can explain every step.
