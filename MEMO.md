# Memo: Monday games review (sample data)

**To:** Head of Games  **From:** Data Analyst  **Re:** What we earned, why, and what luck had to do with it

## Headline
We kept 1.00% of stakes against 1.72% expected. That gap is **normal luck**, not a trend. **One game, the Wheel in week 9, has a real fault and needs checking today.**

## The numbers
- Players staked 15.2M USDT across Dice, Wheel and Slots over 12 weeks.
- The house kept 152k USDT. The maths says about 262k. The 110k shortfall is 1.5 standard errors away, which luck produces regularly.

## What needs action
**Wheel, week 9.** Players won 8,685 bets where the maths expects about 7,859. Luck does not do this (11.5 standard errors). Earnings that week looked only mildly low, so a profit-only report would have missed it. At that week's volume, a fault like this costs roughly 43,000 USDT a week. **Ask:** have engineering check the Wheel's payout logic and that week's bet logs.

## What does not need action
**Wheel, week 6.** The house lost 25k USDT that week, a bad-looking number. But players won at a normal rate. A few large stakes landed their way. This is luck, so I would keep watching and not change anything.

## How sure am I
I tested the method on 300 simulated runs: it caught a planted problem every time and raised a false alarm in about 7% of clean runs. So one flag in a quarter is worth a quick look before it is treated as a fault.

*All figures come from simulated sample data. Charts and code are in the repository.*
