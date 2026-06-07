## EDA Interpretation

### Top 15 Scorers

* High PPG does not equal high efficiency. SGA and Jokić score fewer points than Luka on average but shoot far more efficiently
* Jaylen Brown is the least efficient of the top scorers despite high volume
* Even amongst the most reputable scorers who face tough defensive coverages and take harder shots than the average player, volume and efficiency alone are insufficient to determine true scoring value
* This emphasizes the importance of this model — by incorporating shot difficulty and situational context, we can build a more complete picture of how good a scorer each player truly is

### Efficiency vs Usage Rate

* As usage rate increases, players tend to score more points, reflected by the brighter colors on the right side of the chart
* Variance is highest among low usage players as smaller shot samples make efficiency numbers less reliable
* As usage increases, efficiency regresses toward the league mean. Higher quality players remain efficient at high volume, but not astronomically above average due to increased shot difficulty and greater defensive attention
* Severe outliers in true shooting percentage are concentrated among low usage players. High efficiency outliers likely benefit from offensive gravity created by teammates. Low efficiency outliers are likely poor scorers who rarely shoot for good reason
* Neither extreme is reliable for evaluating true scoring ability, further supporting the need to adjust for usage when building a scoring impact model

### Scoring Distribution

* The distribution of points per game is right skewed, with most NBA players hovering around 5 to 15 PPG
* This makes 20+ PPG scorers and especially 25 to 33 PPG scorers statistical outliers, making high volume scoring that much more impressive and valuable
* Modern NBA offenses emphasize depth and ball movement while defensive schemes have become increasingly versatile and complex. Despite this, a select few elite scorers consistently average high PPG
* A scoring model must account for this skew. The jump from 20 to 25 PPG represents a much rarer and more meaningful level of offensive ability than going from 8 to 13 PPG

### Correlation Heatmap

* Scoring volume and efficiency have a weak but positive correlation. Only 6.25% of the variation in efficiency is explained by scoring volume
* The weak positive correlation is consistent with confounding by player talent. More talented scorers tend to have higher usage and better efficiency, explaining the slight positive relationship
* The relationship being weak confirms that volume alone does not explain efficiency. Shot type, difficulty, and defensive context account for the remaining variation, which is exactly what this model aims to capture
* **FGA vs PTS (r = 0.98)** — scoring is primarily a volume stat. More shot attempts directly translates to more points, highlighting the need to adjust for opportunity when evaluating scoring quality
* **TOV vs USG% (r = 0.80)** — high usage players handle the ball more and turn it over more. This is a byproduct of opportunity, not a criticism
* **OFF_RATING** has relatively weak correlations with most individual stats, suggesting it captures team level context that box score stats do not fully explain. This makes it a useful independent feature in the model
* **TS% vs USG% (r = 0.0)** — efficiency and usage have no linear relationship at the league level. Elite players who maintain high efficiency at high usage are genuinely beating the expected tradeoff

---

### Stage 1 - The Volume Model

### Goal
Capture how much scoring opportunity a player receives. Before evaluating *how well* a player scores, we need to understand *how much* they are asked to score. Volume is the foundation of the model.

### What We Measure
Five features that collectively reflect scoring opportunity:
- **Usage Rate (USG%)** — proportion of team plays used by the player while on the floor
- **Field Goal Attempts (FGA)** — raw shot volume per game
- **Free Throw Attempts (FTA)** — ability to draw fouls and score at the line
- **Minutes (MIN)** — time on the floor
- **Games Played (GP)** — availability and durability across the season

### Formula
Each feature is scaled to a 0–1 range using MinMax scaling, then combined as a weighted average:

$$\text{Volume Score} = 0.35 \cdot USG\% + 0.30 \cdot FGA + 0.15 \cdot FTA + 0.15 \cdot MIN + 0.05 \cdot GP$$

The final score is scaled to 0–100.

### Results
Luka Dončić leads with a 97.3 volume score, consistent with his league-high usage and FGA. Giannis (80.7) and Jokić (75.4) rank lower than their PPG would suggest due to fewer shot attempts, reflecting their efficiency-first offensive roles. Tyrese Maxey's high minutes (38.0) boost his score despite lower usage than peers.

### Limitations
- Volume alone says nothing about efficiency. A player could shoot 25 times and make 8
- FGA and USG% overlap significantly, introducing some redundancy
- GP weighting is low (5%) but a player missing 30 games still receives a similar score to a healthy player with the same per-game numbers
- Does not distinguish between shot types, as a high FGA player taking mostly mid-range shots is treated the same as one taking corner threes

### Future Improvements
- Weight FGA by shot quality
- Introduce an availability adjustment that more heavily penalizes missed games
- Separate FGA into zones to better reflect shot selection

---

### Stage 2 — Efficiency Model


### Goal
Measure how efficiently a player scores relative to their expected efficiency given their usage rate and shot profile.


### What We Measure 


**Feature Engineering:** 
- FG3A_RATE = FG3A / FGA (proportion of shots that are 3-pointers)
- FTA_RATE = FTA / FGA (free throw attempts per shot attempt)


**Expected TS% (Linear Regression):** 
- EXPECTED_TS = (β1 × USG_PCT) + (β2 × FG3A_RATE) + (β3 × FTA_RATE) + intercept
- β1, β2, β3 are coefficients learned from all 384 players


**Efficiency Above Expectation:**
- TS_ABOVE_EXPECTED = Actual TS% - EXPECTED_TS


### Formula


**Efficiency Score:**
- EFFICIENCY_SCORE = (TS_PCT_SCALED × 0.60 + TS_ABOVE_EXPECTED_SCALED × 0.40) × 100


### Results
- top of the efficiency leaderboard dominated by big men and catch-and-shoot specialists, revealing an important limitation of efficiency metrics in isolation. 
- **Jakob Poeltl (80.3)** and **Deandre Ayton (75.6)** lead the list despite averaging only 10.7 and 12.5 PPG, respectively. Both benefit from high TS% on low usage (rarely take difficult shots and score primarily on assisted rim finishes inflating efficiency without reflecting true scoring creation). 
- **Nikola Jokić (71.2)** is the standout exception, maintaining elite efficiency (TS% = 0.670) at a usage rate of 28.9% and 27.7 PPG. Beating expected TS% by 7.0% at that volume is genuinely elite. 
- **Shai Gilgeous-Alexander (69.2)** ranks 10th despite leading the league in PPG (31.1) and carrying a 32.3% usage rate. His TS% of 0.665 is 6.1% (above expected) — exceptional given  volume & high shot difficulty level. Only high scoring volume gaurd that is amongst the top 15.
- **Key takeaway**: Raw efficiency rewards role players who operate in favorable conditions. Hence, Stage 3 (Shot Difficulty) is necessary to adjust for the context in which efficiency is generated. 
- I.E: Player A = big man finishing assisted lobs and a ball handler creating off the dribble at 30% usage. Player B = a scoring gaurd who operates as the offensive engine and the primary shot creator. Clearly player 


R² = 0.20 — our model explains 20% of the variation in TS%. The remaining 80% is driven by factors not yet captured and shot difficulty, defender distance, and shot location are examples of such, which will be addressed in Stage 3.


### Limitation
Big men dominate efficiency rankings due to naturally high percentage shots near the rim. Shot difficulty adjustment in Stage 3 will correct this bias.


### Future Improvement
Expected TS% should incorporate defender distance, assisted vs unassisted FGA, shot distance, and shot  zone for a more accurate baseline. This is addressed in Stage 3.

---

### Stage 3 - Shot Difficulty


Goal: 
Raw efficiency stats like TS% treat all shots equally (Devin Booker pull-up fadeaway and a Mark Williams catch-and-finish dunk count the same). 
 Stage 3 measures how hard a player's shot diet actually is 
Contextualizes efficiency relative to the difficulty of shots taken and role in the offense 


### What We Measure


- **PCT_PULLUP (0.30)** — Pull-ups, step backs, fadeaways, turnarounds. Fully self-created with no offensive setup — the hardest shot category in the NBA
- **AVG_SHOT_DISTANCE (0.25)** — Farther shots are objectively harder and less efficient on average
- **PCT_MIDRANGE (0.20)** — Analytically the worst shot in basketball — low percentage with no three-point bonus. Players who voluntarily live in mid-range face a genuinely hard diet
- **PCT_RESTRICTED_HARD (+0.15)** — Rim attempts created through driving or cutting. The player earned the opportunity through contact or movement, making these difficult despite the short distance
- **PCT_LATE_CLOCK (0.10)** — Shots taken with 4 or fewer seconds on the clock. Rushed and off-balance, but low frequency keeps the weight modest
- **PCT_RESTRICTED_EASY (-0.10)** — Alley oops, putbacks, tip-ins. The easiest shots in basketball — the player is simply finishing what the offense created. Penalized accordingly


How the score is built
Each feature is scaled 0-1 using MinMaxScaler
Multiplied by its weight, summed, then rescaled to 0-100. 
Higher = harder shot diet on average.


Key findings
DeRozan tops the hardest-shot diet at 100.0 due to his extremely high mid-range rate (47%), high pull-up rate, and almost no easy rim shots. His entire game is self-created jump shots from difficult areas.


Booker (94.3) and SGA (90.7) follow, as both are elite pull-up scorers who rarely benefit from easy finishes.


Jalen Brunson lands at 80.1, with his difficulty stemming from a 47% pull-up rate and high mid-range usage, not rim attacks. The model correctly identifies his difficulty as self-creation based, not athleticism based.


Centers like Jalen Duren and DeAndre Ayton score low since their shot diet consists mainly of high volume of assisted rim shots. Their efficiency in Stage 2 is real, but it comes from easy looks.


### Overall interpretation


The difficulty-adjusted efficiency score answers a specific question: who is actually hard to stop? Not just who scores a lot, or who shoots a high percentage, but who scores efficiently on shots that are genuinely difficult to create and convert.


SGA at 84.6 means he is the hardest player in the league to defend on a per-shot basis. He creates his own shot at an elite rate, takes it from difficult distances, and still converts at 66.5% TS. That combination is historically rare. KD and Kawhi behind him makes intuitive sense as both are elite self-creators with high efficiency, just lower volume than SGA.


Booker is the most actionable finding. He ranks 2nd in shot difficulty but 12th in difficulty-adjusted efficiency. That gap tells you he is taking on more shot difficulty than he can consistently convert, which has real implications for Phoenix's offensive design. His value may be overstated by traditional scoring metrics. DeRozan at 100.0 difficulty but only 72.7 adjusted efficiency tells a similar story as he has the hardest shot diet in the league but not converting at a rate that justifies the difficulty. At 18.4 PPG he is likely leaving points on the table by over-indexing on mid-range.


### Statistical Significance


- Weights (0.30, 0.25, 0.20 etc.) are manually chosen based on basketball intuition, not derived from data. A different weighting scheme produces different rankings and there is no internal validation confirming these weights are optimal
- The R² of 0.1985 in Stage 2 is low by design, but a weak expected TS% baseline makes TS_ABOVE_EXPECTED noisy, which flows into difficulty-adjusted efficiency downstream
- With 384 players, rankings at the extremes are meaningful. Players ranked 8th vs 12th are likely within noise — tight middle-of-the-list rankings should not be over-interpreted


### Limitations & Potential Bias


- **One season sample** — scores reflect 2025–26 specifically. Players coming off injury, in a contract year, or in a new system will look different than their career baseline
- **System effects** — players on bad teams face more isolation and late clock situations by necessity, inflating difficulty scores. Cam Thomas at 86.2 partly reflects Brooklyn's broken offense, not purely individual skill
- **Pull-up classification** — the model flags any shot with "Pull-Up", "Fadeaway", or "Step Back" in ACTION_TYPE as self-created. Some of these come off clean pick and roll actions where the defense is already compromised, which are not as hard as true isolation pull-ups
- **Easy rim shots undercounted** — plain "Layup Shot" and "Running Layup" are classified as neutral. Many are catch-and-finish plays that belong in the easy bucket, slightly underpenalizing high-volume dunkers and lob threats
- **Sample size** — players with fewer games have noisier shot distributions. The model does not weight by sample size
- **Measures shots taken, not shots available** — a player on a great offensive team may pass up difficult shots because better ones exist. Jokić's low difficulty score reflects his playmaking role and system, not an inability to create hard shots

---

### Stage 4 - Game Context / Situation

### What We Measure

- **FG_PCT_CLUTCH** — field goal percentage in the 4Q of games that ended within 5 points. Closest proxy to true pressure shooting available in the data
- **FG_PCT_BLOWOUT** — field goal percentage in games decided by 15+ points. Baseline performance with no pressure
- **FG_PCT_LATE_GAME** — field goal percentage in the final 5 minutes of the 4Q regardless of margin
- **FG_PCT_EARLY_GAME** — field goal percentage in the 1st and 2nd quarters. Baseline performance early
- **FG_PCT_HOME / FG_PCT_AWAY** — shooting splits by arena. Measures consistency regardless of crowd and environment
- **IS_END_OF_QUARTER** — shots taken in the last 4 seconds of a quarter. Desperation/heave attempts, not true shot clock pressure

### How the Context Score is Built

Four derived metrics are created, scaled 0–1, then blended:

$$CLUTCH\_VS\_BLOWOUT = FG\%_{clutch} - FG\%_{blowout} \times 0.40$$

$$LATE\_VS\_EARLY = FG\%_{late} - FG\%_{early} \times 0.25$$

$$HOME\_AWAY\_CONSISTENCY = 1 - |FG\%_{home} - FG\%_{away}| \times 0.20$$

$$CLOCK\_DISCIPLINE = FG\%_{early clock} - FG\%_{late clock} \times 0.15$$

Higher score = player elevates in pressure situations, performs consistently late, and maintains efficiency regardless of venue.

### Key Findings

- **Cooper Flagg** leads with the highest context score, 4.1 points ahead of 2nd place. He shoots 4.8 percentage points better in clutch situations than blowouts and elevates late in games, genuinely impressive for a rookie. His clutch FG% of 45.6% is modest in isolation however, as part of his high context score is explained by underperforming in blowouts (40.8%) rather than dramatically overperforming in clutch moments. The question remains how his numbers would look on a competitive roster where close games carry higher stakes

- **Giannis Antetokounmpo** is the most statistically meaningful result in the clutch rankings. At 56 attempts (the largest sample in the list), his 58.9% clutch FG% is the highest rate in the entire dataset at that sample size. However, it is worth noting that Giannis also played only 36 games this season, and being on and off the court consistently may have not prepared opposing defensive schemes as to how much of a threat Giannis would be.

- **Devin Booker (65.1)** is interesting in the context of Stage 3. He takes the hardest shots, performs consistently in clutch situations (52.3% clutch FG%), and shows the biggest early-to-late game improvement (42.8% → 51.9%). His Stage 3 efficiency gap may be partially explained by shot timing, as he takes harder shots later in games when defenses are most locked in

- **Kevin Durant (62.5)** actually understates his clutch value. His blowout FG% (55.6%) is higher than his clutch FG% (54.3%), which penalizes him in this model. But shooting 54.3% in clutch situations on 35 attempts while also shooting 55.6% in blowouts means he is simply consistent everywhere, not that he shrinks. The model penalizes consistency, which is a known limitation

- **SGA** at 55.6% clutch FG% on 36 attempts reinforces his Stage 3 result — efficient on hard shots and in pressure situations, the rarest combination in the dataset

### Limitations

- No mechanism to distinguish the quality of clutch situations. For instance, a close game between two lottery teams carries the same weight as a playoff race. Players who are not primary scoring options in clutch situations benefit from reduced defensive attention, somewhat inflating their context scores relative to stars who face focused coverage in identical situations
- **Final margin proxy problem**: IS_CLOSE_GAME uses the final score margin, not the live margin at the time of the shot. A game that ends by 2 points but was a 20-point blowout at halftime gets classified as clutch for every shot, including first half garbage time. This inflates clutch attempt counts and adds noise to clutch FG%

### Statistical Significance

- **Small clutch samples**: even the largest sample in the top 15 (Giannis, 56 attempts) represents roughly 1–2 shots per close 4th quarter game. A few made or missed shots meaningfully swing the percentage. Players at the minimum threshold of 35 attempts should be interpreted with caution
- **Manual weights**: context score weights (0.40, 0.25, 0.20, 0.15) reflect basketball intuition, not statistical optimization. A different weighting scheme would produce different rankings
- **Narrow spread is a finding, not a flaw**: Cooper Flagg (73.1) vs Kevin Durant (62.5) is a 10.6 point gap across the top 15, compared to Stage 3's 100.0 to 62.5 spread. This suggests situational performance is genuinely more uniform across good players than shot difficulty. Elite scorers tend to show up in big moments at similar rates, making shot creation the bigger differentiator.

---

## Stage 5 — Team Independence Score

The previous four stages measure what a player does individually. We measured how much they score, how efficiently, on how hard shots, and in what situations. None of them answer how much of that scoring is dependent on their team's system and surrounding talent. Stage 5 addresses this by measuring how much better or worse a team performs offensively and overall when a player is on versus off the court.

### What We Measure

- **NET_RATING_IMPACT** measures the difference in team net rating with the player on vs off the court. The single most important signal of individual impact independent of teammates
- **OFF_RATING_IMPACT** applies the same calculation but for offensive rating specifically. Isolates scoring contribution from defensive impact
- **NET_RATING_ON** captures absolute team quality when the player is on court. Distinguishes players who elevate bad teams from players who merely contribute to already good ones

### How the Independence Score is Built

Three features scaled 0–1 and blended:

$$\text{Independence Score} = 0.50 \cdot NET\_RATING\_IMPACT + 0.30 \cdot OFF\_RATING\_IMPACT + 0.20 \cdot NET\_RATING_{ON}$$

A higher independence score means the team is meaningfully better with the player on court, particularly offensively, and that the team is genuinely good when they play. It correlates to scoring directly translating to team success and gives stronger implications that this player is the offense. A lower score may imply minimal impact and that the scoring is more so a reflection of the system, essentially that the scoring may be replaceable.

### Key Findings

- **Wembanyama leads at 100.0.** The Spurs post a NET_RATING of +17.0 with him on court vs +0.6 without him, a swing of 16.4 points per 100 possessions. Extraordinary for a player in his second season. His offensive impact (6.2) is lower than his overall impact, suggesting his defensive presence drives a significant part of the swing, but his scoring independence is still elite given SAS' offensive rating jumps dramatically with him on court
- **Jokić at 99.3** with an OFF_RATING_IMPACT of 13.4 is the most analytically interesting finding in Stage 5. Denver's offense is 13.4 points per 100 possessions better with him on court. This directly addresses the Stage 3 limitation where his low shot difficulty score seemed to undervalue him. Jokić doesn't need to take hard shots because he makes everyone around him more efficient. The on/off data confirms he is the engine of Denver's offense, not merely a weapon within it
- **SGA at 99.0** with NET_RATING_ON of +16.3 is the strongest absolute team quality finding. OKC is a genuinely elite team when he plays, not just marginally better. Combined with his Stage 1 through 4 results, SGA's cross-stage consistency is unmatched in the entire dataset
- **Kawhi at 96.0** produces a net rating swing of 13.8 points with him on vs off. The Clippers are a below average team without him (NET_RATING_OFF of -6.3), confirming he is single-handedly keeping them competitive. His scoring independence is real as he is not benefiting from a system or teammate quality
- **Giannis at 94.6** with a NET_RATING_OFF of -9.7 is the most dramatic dependency finding. Milwaukee collapses without him to nearly -10 net rating, one of the largest off-court drops in the dataset. Combined with his Stage 4 clutch finding, Giannis is both the most clutch and the most irreplaceable player on his team
- **JJJ at 94.3** averaged across two team stints reflects genuine impact. Memphis is dramatically worse without him regardless of team context, confirming he is a true franchise cornerstone despite playing for a rebuilding team

### Limitations and Potential Bias

- Net rating on/off splits do not account for lineup quality. Julian Champagnie ranking 7th exposes this key limitation. When Champagnie is off the court, other starters including Wembanyama may also be resting, artificially tanking the off-court net rating and inflating his apparent impact. This is a known confounding problem with on/off metrics. A player's independence score reflects who else is on or off the court at the same time, not purely their individual contribution
- Stars on contending teams may have their net rating impact understated because capable teammates compensate when they sit, minimizing the on/off gap. Conversely, stars on rebuilding teams show larger swings because their absence exposes a much weaker supporting cast. The independence score may inadvertently penalize players on deep rosters and reward players on talent-thin teams, outside of the individual player's control. This makes findings like Wembanyama's and SGA's 13+ point impacts even more impressive given the quality of their surrounding rosters

### Statistical Significance

- On/off splits are among the most reliable advanced metrics available because they measure actual outcomes rather than modeled predictions. A 13+ point NET_RATING_IMPACT like Jokić or Kawhi represents thousands of possessions of evidence, making these findings genuinely statistically meaningful
- Lineup combinations introduce confounding. A player's on/off numbers are influenced by which teammates they share the court with and which lineups they face. A star who plays exclusively with other stars will have inflated off-court numbers because their absence coincides with weaker lineups taking the floor
- Small market and rebuilding teams systematically produce larger on/off swings because their supporting cast is weaker. This inflates independence scores for players on bad teams and slightly deflates them for players on deep rosters like Boston or Denver

---

## Final Model — True Scoring Impact

### Goal

The TRUE_SCORING_IMPACT score answers a single question: "If you needed someone to score for your team in the most complete and valuable way possible, who would you pick?"

This composite metric blends all 5 stages into a single score, rewarding players who demonstrate sustained scoring value across multiple dimensions rather than excelling in just one.

### What We Measure

- **VOLUME_SCORE (27.5%)** — How much scoring burden the player carries. Rewards players who handle high usage, attempt more shots, and play heavy minutes
- **DIFFICULTY_ADJ_EFFICIENCY (25%)** — How efficiently the player scores adjusted for how hard their shots actually are. Rewards players who convert on self-created, high difficulty attempts
- **EFFICIENCY_SCORE (25%)** — How efficiently the player scores relative to what is expected given their role. Rewards players who beat their expected TS% at high usage
- **CONTEXT_SCORE (15%)** — How well the player performs in high pressure situations. Rewards players who elevate in clutch moments, late game situations, and away from home
- **INDEPENDENCE_SCORE (7.5%)** — How much the team depends on the player's scoring. Rewards players whose presence meaningfully improves the team's offensive and overall performance

A player who scores high across all five dimensions is not just a scorer, but a complete and irreplaceable offensive weapon. The composite rewards breadth of scoring value over dominance in any single dimension.

### How the Score is Built

Each stage score is independently rescaled to 0–1 using MinMaxScaler before combining. This ensures no single stage dominates the composite due to a wider score distribution.

Every stage contributes based on relative position within that stage rather than raw magnitude.

$$TRUE\_SCORING\_IMPACT = 0.275 \cdot VOLUME + 0.250 \cdot DIFFICULTY\_ADJ\_EFF + 0.250 \cdot EFFICIENCY + 0.150 \cdot CONTEXT + 0.075 \cdot INDEPENDENCE$$

The final score is normalized to 0–100. A higher score implies a more complete scorer across all weighted dimensions. A lower score does not mean the player is a poor scorer, but rather that their scoring value is concentrated in fewer dimensions.

### Key Findings

- **SGA at 100.0** is the most complete scorer in the NBA this season. No other player combines elite scores across all 5 dimensions simultaneously. He ranks top 5 in volume, efficiency, difficulty-adjusted efficiency, and team independence
- **Luka at 92.1** carries the highest volume score (97.3) but relatively weak efficiency (55.7). The most important finding for evaluating Luka is that he is the highest volume scorer in the dataset by a significant margin, but his efficiency and difficulty-adjusted efficiency rank lower than peers like SGA, KD, and Kawhi
- **Jaylen Brown at 80.3** has the 2nd highest volume score (89.5) but the lowest efficiency in the top 15 (44.6), the starkest efficiency-volume gap in the dataset. Combined with a low independence score (68.6), the model suggests his scoring value comes from the Celtics offensive design as well as tough shot-making ability combined with volume and scoring reputability
- **Cam Spencer at 75.4** averages only 11.1 PPG but ranks 23rd overall. Elite efficiency and shot difficulty carry him, but low volume correctly penalizes him from the top 10
- **The bottom 10** consists mostly of young or developing players and inefficient big men. Players who operate on low efficiency, low difficulty, and low independence — consistent with the scoring impact formula

### Limitations and Potential Bias

- **Weight subjectivity** — the five stage weights are manually assigned based on basketball intuition, not statistically derived. Giving volume a slightly lower weight would elevate Kawhi and KD over Luka. Giving independence a higher weight would elevate Jokić and Wembanyama. The model reflects one defensible weighting philosophy, not the objectively correct one
- **One season sample** — the entire model reflects 2025-26 only. Players coming off injury, in contract years, or in new systems will look different than their career baseline. Embiid's context score (36.6) partly reflects missed time and rust. Cade Cunningham's 73.9 score was impacted by a rib injury that tanked his late season volume and efficiency
- **Scoring only** — a player like Jrue Holiday, Draymond Green, or Mikal Bridges may contribute enormous value to winning basketball without ranking highly here. This model deliberately narrows its scope to scoring impact and should not be interpreted as an overall player value metric

### Statistical Significance

- Stage 1 and Stage 2 are built on 384 players with full season samples and are the most statistically reliable inputs. Stage 3 uses 102,400 individual shot attempts, making shot-level aggregations highly reliable for players with 200+ attempts. Stage 4 clutch splits remain the weakest input. Stage 5 on/off data is reliable for star players with heavy minutes but noisy for players with inconsistent roles
- The top and bottom of the rankings are the most defensible findings. The 7.5 point gap between SGA (100.0) and Luka (92.1) is meaningful and consistent across multiple independent data sources. The 1.0 point gap between Jokić (88.1) and Ant (87.9) is not, thus those two players are statistically indistinguishable at this level of model precision
- **Correlation between stages is an unresolved issue** — shot difficulty and volume are not fully independent, and difficulty and efficiency overlap by design in Stage 3. The composite is not a sum of truly independent signals. A future improvement would be to orthogonalize the stage scores using PCA before combining them, removing overlap between correlated inputs and producing a more statistically independent composite.

