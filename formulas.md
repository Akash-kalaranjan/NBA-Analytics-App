### Stage 1 — Volume Score

$$\text{Volume Score} = 0.35 \cdot USG\% + 0.30 \cdot FGA + 0.15 \cdot FTA + 0.15 \cdot MIN + 0.05 \cdot GP$$

**Weight Justification:**

| Feature | Weight | Reason |
|---|---|---|
| USG% | 35% | Best single proxy for offensive role and how central a player is to their team's offense |
| FGA | 30% | Raw shot volume directly reflects scoring opportunity |
| FTA | 15% | Drawing fouls is a repeatable skill that reflects offensive aggression |
| MIN | 15% | Time on floor determines total opportunity |
| GP | 5% | Availability matters but per-game stats already adjust for games missed |

---
### Stage 2 — Efficiency Score

**Step 1 — Expected TS% via OLS Regression:**

$$\hat{TS\%} = \beta_0 + \beta_1 \cdot USG\% + \beta_2 \cdot FG3A\_RATE + \beta_3 \cdot FTA\_RATE$$

$$FG3A\_RATE = \frac{FG3A}{FGA}, \quad FTA\_RATE = \frac{FTA}{FGA}$$

**Regression Output:**

| Coefficient | Feature | Value | Interpretation |
|---|---|---|---|
| β₀ | Intercept | 0.5525 | Baseline expected TS% |
| β₁ | USG% | -0.1094 | Higher usage slightly lowers expected TS% — harder shots |
| β₂ | FG3A Rate | -0.0072 | 3pt rate has minimal effect on expected efficiency |
| β₃ | FTA Rate | +0.1912 | Getting to the line meaningfully boosts expected TS% |

**R² = 0.1988** — shot profile explains ~20% of efficiency variation. The remaining 80% reflects individual scoring skill independent of role.

$$TS\_ABOVE\_EXPECTED = TS\% - \hat{TS\%}$$

**Step 2 — Efficiency Score:**

$$\text{Efficiency Score} = 0.60 \cdot TS\%_{scaled} + 0.40 \cdot TS\_ABOVE\_EXPECTED_{scaled}$$

**Weight Justification:**

| Feature | Weight | Reason |
|---|---|---|
| Raw TS% | 60% | Absolute efficiency still matters — elite shooters should be rewarded |
| TS Above Expected | 40% | Rewards players who beat their role expectations |

---

### Stage 3 — Shot Difficulty & Difficulty Adjusted Efficiency

$$\text{Difficulty} = 0.25 \cdot AVG\_DIST + 0.30 \cdot PCT\_PULLUP + 0.20 \cdot PCT\_MIDRANGE + 0.15 \cdot PCT\_RESTRICTED\_HARD + 0.10 \cdot PCT\_LATE\_CLOCK - 0.10 \cdot PCT\_RESTRICTED\_EASY$$

**Weight Justification:**

| Feature | Weight | Reason |
|---|---|---|
| PCT_PULLUP | 30% | Self-created shots are the hardest shots in basketball — no defensive rotation to exploit |
| AVG_SHOT_DISTANCE | 25% | Farther shots are objectively harder and less efficient on average |
| PCT_MIDRANGE | 20% | Mid-range is the least efficient shot in the modern NBA — taking them willingly signals difficulty |
| PCT_RESTRICTED_HARD | 15% | Driving into traffic is harder than catch-and-shoot rim attempts |
| PCT_LATE_CLOCK | 10% | Rushed shots under 4 seconds reflect forced creation |
| PCT_RESTRICTED_EASY | -10% | Alley-oops, putbacks, and tip-ins are passive — penalized accordingly |

**Difficulty Adjusted Efficiency:**

$$\text{Difficulty Adj. Efficiency} = 0.50 \cdot EFFICIENCY_{scaled} + 0.50 \cdot (TS\% \times \frac{DIFFICULTY}{100})_{scaled}$$

| Feature | Weight | Reason |
|---|---|---|
| Efficiency Score | 50% | Raw efficiency still matters independent of difficulty |
| TS% × Difficulty | 50% | Rewards players who are efficient on hard shots specifically |

---

### Stage 4 — Game Context Score

$$\text{Context Score} = 0.40 \cdot CLUTCH\_VS\_BLOWOUT + 0.25 \cdot LATE\_VS\_EARLY + 0.20 \cdot HOME\_AWAY\_CONSISTENCY + 0.15 \cdot CLOCK\_DISCIPLINE$$

**Weight Justification:**

| Feature | Weight | Reason |
|---|---|---|
| Clutch vs Blowout | 40% | Performing in close games vs checking out in blowouts is the most meaningful situational split |
| Late vs Early Game | 25% | Elevating in the 4th quarter when defenses tighten is a true scorer's trait |
| Home/Away Consistency | 20% | Elite scorers perform regardless of crowd and environment |
| Clock Discipline | 15% | Taking good shots early in the shot clock reflects composure and offensive IQ |

---

### Stage 5 — Team Independence Score

$$\text{Independence Score} = 0.50 \cdot NET\_RATING\_IMPACT + 0.30 \cdot OFF\_RATING\_IMPACT + 0.20 \cdot NET\_RATING_{ON}$$

**Weight Justification:**

| Feature | Weight | Reason |
|---|---|---|
| Net Rating Impact (ON-OFF) | 50% | Best measure of how much the team improves with the player on the floor |
| Offensive Rating Impact | 30% | Isolates the offensive contribution specifically, relevant to scoring impact |
| Net Rating ON | 20% | Absolute team quality on court rewards players on winning teams less than impact does |

---

### Final Model — True Scoring Impact

$$\text{True Scoring Impact} = 0.275 \cdot VOLUME + 0.250 \cdot DIFFICULTY\_ADJ\_EFFICIENCY + 0.250 \cdot EFFICIENCY + 0.150 \cdot CONTEXT + 0.075 \cdot INDEPENDENCE$$

**Weight Justification:**

| Stage | Weight | Reason |
|---|---|---|
| Volume | 27.5% | Opportunity is the foundation — you cannot impact scoring without it |
| Difficulty Adj. Efficiency | 25% | Efficiency on hard shots is the truest measure of scoring skill |
| Efficiency | 25% | Raw efficiency independent of difficulty still captures shooting quality |
| Game Context | 15% | Situational performance separates good scorers from great ones |
| Team Independence | 7.5% | Important but confounded by non-scoring factors — kept intentionally low |

---

### Underrated Score

**Step 1 — Expected Impact via OLS Regression:**

$$EXPECTED\_IMPACT = \beta_0 + \beta_1 \cdot PTS + \beta_2 \cdot USG\% + \beta_3 \cdot MIN$$

**Step 2 — Underrated Score:**

$$UNDERRATED\_SCORE = TRUE\_SCORING\_IMPACT - EXPECTED\_IMPACT$$

**Weight Justification:**

| Feature | Reason |
|---|---|
| PTS | Primary driver of perceived scoring value in public perception |
| USG% | Controls for opportunity — high usage players are expected to have high impact |
| MIN | Controls for playing time — more minutes naturally inflates raw impact |

A positive Underrated Score means the player outperforms what their raw stats would predict. The higher the value, the more the player is undervalued by traditional metrics.

---
