## EDA Interpretation

### Top 15 scorers
High PPG does not equal high efficiency. SGA and Jokić score fewer points than Luka on average but shoot far more efficiently. Jaylen Brown is the least efficient of the top scorers despite high volume. Even amongst the most reputable scorers who face tough defensive coverages and take harder shots than the average player, volume and efficiency alone are insufficient to determine true scoring value. This  emphasizes the importance of this model, as by incorporating shot difficulty and situational context, we can build a more complete picture of how good a scorer each player truly is.

### Efficiency vs Usage Rate
As usage rate increases, players tend to score more points, reflected by the brighter colors on the right side of the chart. This is consistent with higher opportunity leading to more shot attempts and higher PPG. Variance is highest among low usage players on the left side of the chart. This makes sense as low volume players have smaller shot samples, making their efficiency numbers less reliable. As usage increases, efficiency regresses toward the league mean and higher quality players remain efficient at high volume, but not astronomically above average due to the increased difficulty of shots and greater defensive attention they face. 

Severe outliers in true shooting percentage, both above and below the mean, are concentrated among low usage players. High efficiency outliers at low usage likely benefit from offensive gravity created by teammates, and low efficiency outliers at low usage are likely poor scorers who rarely shoot for good reason. Neither extreme is reliable for evaluating true scoring ability, which further supports the need to adjust for usage when building a scoring impact model.

### Scoring Distribution
The distribution of points per game is right skewed, with a heavy tail on the right side. Most NBA players hover around 5-15 PPG, making 20+ PPG scorers and especially 25-33 PPG scorers statistical outliers. This makes high volume scoring that much more impressive and valuable.

Modern NBA offenses emphasize depth and ball movement, while defensive schemes have become increasingly versatile and complex. Despite this, a select few elite scorers consistently average high PPG, which speaks to the difficulty and rarity of what they do. A scoring model must account for this skew as the difference between a player going from 8 to 13 PPG is common, while the jump from 20 to 25 PPG represents a much rarer and more meaningful level of offensive ability.

### Correlation Heatmap
Scoring volume and efficiency have a weak, but positive correlation, as only 6.25% of the variation in efficiency is explained by the scoring volume. Overall, the weak positive correlation is relatively consistent with confounding by player talent, as more talented scorers tend to have higher usage and better efficiency, explaining the slight positive relationship. However, the relationship being weak confirms that volume alone does not explain efficiency. Shot type, difficulty, and defensive context account for the remaining variation, hence is exactly what this model aims to capture.

FGA and PTS have an extremely strong correlation (r = 0.98), confirming that scoring is primarily a volume stat, more shot attempts directly translates to more points. This highlights the need to adjust for opportunity when evaluating scoring quality.

TOV and USG_PCT have a strong correlation (r = 0.80), which is expected as high usage players handle the ball more and therefore turn it over more. This is not necessarily a criticism on those NBA players, it is a byproduct of opportunity.

OFF_RATING has relatively weak correlations with most individual stats, suggesting that offensive rating captures team level context that individual box score stats do not fully explain. This makes it a useful independent feature in the model.

TS_PCT and USG_PCT have virtually zero correlation (r = 0.0), confirming that efficiency and usage have no linear relationship at the league level. Elite players who maintain high efficiency at high usage are genuinely beating the expected tradeoff.

### Limitations — Stage 1
Volume score weights are manually assigned based on domain knowledge. A more rigorous approach would derive weights statistically using PCA or regression analysis. This is a planned improvement for future iterations.

## Stage 1 — Volume Score
Luka Dončić ranks #1 in volume score (97.3), consistent with his league leading usage rate and shot attempts. Notably Jokić ranks lower (75.4) despite scoring 27.7 PPG, suggesting he generates 
points efficiently without requiring dominant possession usage. This sets up Stage 2 where efficiency is rewarded.

## Stage 2 — Efficiency Model

### Goal
Measure how efficiently a player scores relative to their expected efficiency given their usage rate and shot profile.

### Formula

**Feature Engineering:**
- FG3A_RATE = FG3A / FGA (proportion of shots that are 3 pointers)
- FTA_RATE = FTA / FGA (free throw attempts per shot attempt)

**Expected TS% (Linear Regression):**
- EXPECTED_TS = (β1 × USG_PCT) + (β2 × FG3A_RATE) + (β3 × FTA_RATE) + intercept
- β1, β2, β3 are coefficients learned from all 384 players

**Efficiency Above Expectation:**
- TS_ABOVE_EXPECTED = Actual TS% - EXPECTED_TS

**Efficiency Score:**
- EFFICIENCY_SCORE = (TS_PCT_SCALED × 0.60 + TS_ABOVE_EXPECTED_SCALED × 0.40) × 100

### Results
R² = 0.20 — our model explains 20% of the variation in TS%. The remaining 80% is driven by factors not yet captured and shot difficulty, defender distance, and shot location are examples of such, which will be addressed in Stage 3.

### Limitation
Big men dominate efficiency rankings due to naturally high percentage shots near the rim. Shot difficulty adjustment in Stage 3 will correct this bias.

### Future Improvement
Expected TS% should incorporate defender distance, assisted vs unassisted FGA, shot distance, and shot  zone for a more accurate baseline. This is addressed in Stage 3.

### Future Improvement — Stage 3
Defender distance data available via PlayerDashPtShots endpoint. Adding this feature will improve shot difficulty accuracy. Planned for next iteration.

### Stage 3 - Shot Difficulty
Problem: Raw efficiency stats like TS% treat all shots equally. A Devin Booker pull-up fadeaway from 16 feet and a Mark Williams catch-and-finish dunk both count the same. Stage 3 fixes that by measuring how hard a player's shot diet actually is, so it contextualizes the efficiency a player is scoring on relative to their role in the offense.

What we measure

Five features capture shot difficulty at the player level:

AVG_SHOT_DISTANCE (weight: 0.25) — The average distance of all shot attempts. Farther shots are objectively harder regardless of shot type.

PCT_PULLUP (weight: 0.30) — Percentage of shots that were pull-ups, step backs, fadeaways, or turnarounds. These are fully self-created with no offensive setup as it is the hardest category of shot in the NBA.

PCT_MIDRANGE (weight: 0.20) — Percentage of shots from mid-range. It is analytically the worst shot in basketball due to it being a low percentage, no three point bonus type of shot. Players who voluntarily live there face a hard diet.

PCT_RESTRICTED_HARD (weight: +0.15) — Percentage of rim attempts that were driving or cutting plays. The player created the opportunity through contact or movement, making these genuinely difficult despite the short distance.

PCT_RESTRICTED_EASY (weight: -0.10) — Percentage of rim attempts that were alley oops, putbacks, or tip-ins. These are the easiest shots in basketball since the player is simply finishing what the offense created for them.

PCT_LATE_CLOCK (weight: 0.10) — Percentage of shots taken with 4 or fewer seconds on the shot clock. Rushed, off-balance, defender-closing shots. However, the lack of volume/frequency of this occurring makes it weighted less than other shot situations.

How the score is built
Each feature is scaled 0-1 using MinMaxScaler, multiplied by its weight, summed, then rescaled to 0-100. Higher = harder shot diet on average.

Key findings
DeRozan tops the hardest shot diets at 100.0 due to his extremely high mid-range rate (47%), high pull-up rate, almost no easy rim shots. His entire game is self-created jump shots from difficult areas.

Booker (94.3) and SGA (90.7) follow, as both are elite pull-up scorers who rarely benefit from easy finishes.

Jalen Brunson lands at 80.1 as his difficulty comes from a 47% pull-up rate and high mid-range usage, not rim attacks. The model correctly identifies his difficulty as self-creation based, not athleticism based.

Centers like Jalen Duren and Deandre Ayton score low since their shot diet consists of mainly high easy rim shot rates drag their difficulty scores down, which is accurate. Their efficiency in Stage 2 is real but it comes from easy looks.

Difficulty Adjusted Efficiency

This Combines Stage 2 efficiency with shot difficulty with a 50/50 split. A player needs both a high efficiency and a higher shot difficulty for an overall high ranking, essentially proving that they are efficient in spite of a relatively harder shot diet.

When running the output, we see that SGA leads at 84.6. He is the only player in the top 15 who combines elite efficiency, elite pull-up rate, and high shot difficulty. KD (80.9) and Kawhi (75.4) follow as the other true elite difficulty-adjusted scorers.

Then, Booker (68.5) is the most interesting case, as he has the hardest shot diet in the top tier but drops significantly on difficulty-adjusted efficiency because his conversion rate doesn't match the difficulty he takes on.

Overall interpretation
The difficulty-adjusted efficiency score answers a specific question: who is actually hard to stop? Not just who scores a lot, or who shoots a high percentage, but who scores efficiently on shots that are genuinely difficult to create and convert.

SGA at 84.6 means he is the hardest player in the league to defend on a per-shot basis. He creates his own shot at an elite rate, takes it from difficult distances, and still converts at 66.5% TS. That combination is historically rare. KD and Kawhi behind him makes intuitive sense as both are elite self-creators with high efficiency, just lower volume than SGA.

Booker is the most actionable finding. He ranks 2nd in shot difficulty but 12th in difficulty-adjusted efficiency. That gap tells you he is taking on more shot difficulty than he can consistently convert, which has real implications for Phoenix's offensive design. His value may be overstated by traditional scoring metrics. DeRozan at 100.0 difficulty but only 72.7 adjusted efficiency tells a similar story as he has the hardest shot diet in the league but not converting at a rate that justifies the difficulty. At 18.4 PPG he is likely leaving points on the table by over-indexing on mid-range.

Statistical Significance
The weights (0.30, 0.25, 0.20 etc.) are manually chosen, not derived from data. A different weighting scheme would produce different rankings. The model has no internal validation telling you those weights are optimal as they reflect basketball intuition, not statistical optimization.

The R² of 0.1985 in Stage 2 is low by design, but it also means the expected TS% baseline is noisy. A weak baseline makes TS_ABOVE_EXPECTED less reliable, which flows into difficulty-adjusted efficiency downstream.

With 384 players, the sample is large enough to be meaningful at the extremes since SGA and DeRozan are genuinely different from average. But players ranked 8th vs 12th are likely within noise. We do not read too much into tight rankings in the middle of the list.

Limitations and Potential Bias
These scores reflect 2025-26 specifically (one season sample). A player coming off injury, in a contract year, or in a new system will look different than their career baseline. DeRozan on the Clippers in a rebuilding year may not represent his true value tier.

Team and system effects are not fully removed. A player on a bad team faces more isolation situations and late clock shots by necessity, which inflates their difficulty score. Cam Thomas at 86.2 partly reflects Brooklyn's broken offense, not just his individual skill.

The pull-up classification is imperfect. The model flags any shot with "Pull-Up", "Fadeaway", "Step Back" etc. in ACTION_TYPE as self-created. But some pull-ups come off clean pick and roll actions where the defense is compromised, which aren't as hard as a true isolation pull-up. The data doesn't let us distinguish.

Easy rim shots may be undercounted. Plain "Layup Shot" and "Running Layup" are classified as neutral  (neither hard nor easy). Many of those are catch-and-finish plays that probably belong in the easy bucket. This slightly underpenalizes high-volume dunkers and lob threats.

Injury and games played. Players with fewer games have noisier shot distributions. A player who played 45 games has half the shot sample of someone who played 82. The model doesn't weight by sample size.

This model measures shot quality taken, not shot quality available. A player on a great offensive team may pass up difficult shots because better ones are available. Their difficulty score looks low not because they can't create, but because they don't need to. Nikola Jokić is a good example of this issue as his low difficulty score reflects his system and playmaking role, not an inability to create hard shots.

### Stage 4 - Game Context / Situation

Issue: Scoring averages treat all shots equally regardless of when they happen. A mid-range jumper in the first quarter of a 20-point blowout and a pull-up three with 30 seconds left in a one-possession game both count the same in box scores. The reality is, both of these shots have different values in a basketball game, which is why Stage 4 was created to measure whether players perform differently (better or worse) in more valuable moments of a game.

What we measure
FG_PCT_CLUTCH — field goal percentage in the 4th quarter of games that ended within 5 points. This was the closest proxy to true pressure shooting available in the data.
FG_PCT_BLOWOUT — field goal percentage in games decided by 15+ points. Baseline performance with no pressure.
FG_PCT_LATE_GAME — field goal percentage in the final 5 minutes of the 4th quarter regardless of margin.
FG_PCT_EARLY_GAME — field goal percentage in the 1st and 2nd quarters. Baseline performance early.
FG_PCT_HOME / FG_PCT_AWAY — shooting splits by venue. Measures consistency regardless of crowd and environment.
IS_END_OF_QUARTER — shots taken in the last 4 seconds of a quarter. Desperation/heave attempts, not true shot clock pressure

How the Context Score is built
Four derived metrics are created, scaled 0-1, then blended:
CLUTCH_VS_BLOWOUT      = FG_PCT_CLUTCH - FG_PCT_BLOWOUT        × 0.40
LATE_VS_EARLY          = FG_PCT_LATE_GAME - FG_PCT_EARLY_GAME  × 0.25
HOME_AWAY_CONSISTENCY  = 1 - |FG_PCT_HOME - FG_PCT_AWAY|       × 0.20
CLOCK_DISCIPLINE       = FG_PCT_EARLY_CLOCK - FG_PCT_LATE_CLOCK × 0.15
A higher score means the player elevates in pressure situations, performs consistently late, and maintains efficiency regardless of venue.

Key Findings:
Cooper Flagg has the highest context score with a gap of 4.1 points ahead of the 2nd highest score (Collin Gillespie). In particular, he shoots 4.8 percentage points better in clutch situations than blowouts and elevates late in games, which is genuinely impressive for a rookie. This also raises the question of how his clutch numbers would look on a competitive roster where close games carry higher stakes, as he rarely pads his stats when there is a lack of incentive to score, whereas when games get competitive, he rises to the occasion. However, it is worth noting that his clutch FG% of 45.6% is modest in isolation, as part of his high context score is explained by him underperforming in blowouts (40.8%) rather than dramatically overperforming in clutch moments.

At 56 clutch attempts, Giannis Antetokounmpo is the most statistically meaningful result of the Clutch rankings list, as 56 clutch attempts is the largest sample in the clutch kings list among star players, and a 58.9% clutch FG% is the highest rate in the entire dataset at that sample size. It also directly contradicts a narrative around Giannis that he is a poor clutch performer. It is quite interesting that he was able to get up as many clutch shot attempts despite playing less than half of the season.

Devin Booker with a 65.1 context score is interesting in context of Stage 3. This is due to him taking the hardest shots, performs consistently in clutch situations (0.523 clutch FG%), and shows the biggest early-to-late game improvement (0.428 → 0.519). His Stage 3 efficiency gap may be partially explained by shot timing, as he's taking harder shots later in games when defenses are locked in.

Kevin Durant at 62.5 actually understates his clutch value. His blowout FG% (0.556) is higher than his clutch FG% (0.543) which penalizes him in this model, but KD shooting 54.3% in clutch situations on 35 attempts while also shooting 55.6% in blowouts means he is simply consistent everywhere, not that he shrinks. The model penalizes consistency which is a known limitation.

SGA at 0.556 clutch FG% on 36 attempts reinforces his Stage 3 result as he is efficient on hard shots AND in pressure situations, which is the rarest combination in the dataset.

It is interesting that players like Collin Gillespie and Kyle Kuzma appear in the top 15 context scores alongside established stars. This is worth unpacking rather than dismissing entirely. Kuzma's 57.1% clutch FG% on 35 attempts is a legitimately strong number, he has historically been trusted in late game situations and the data reflects that he converts when given the opportunity. Gillespie similarly shows a consistent pattern of elevating in close games versus blowouts, and his late game numbers suggest he is a player who competes harder when the game matters, which is a genuine trait regardless of his overall role. 

However, both players benefit from a key limitation of the model: it has no mechanism to distinguish the quality of clutch situations. A close game between two lottery teams does not carry the same stakes as a close game in a playoff race, yet both count equally here. Additionally, neither player is the primary option in those moments, meaning they are often benefiting from defensive attention drawn by teammates rather than creating under true pressure. So while their situational shooting numbers are real and worth acknowledging, their context scores are somewhat inflated relative to stars who face more focused defensive coverage in identical situations.

Another limitation is that there is a final margin proxy problem. IS_CLOSE_GAME uses the final score margin, not the live margin at the time of the shot. A game that ends 104-102 but was a 15-point blowout at halftime gets classified as clutch for every shot including first half garbage time. This inflates clutch attempt counts and adds noise to clutch FG%.

Statistical Significance
Clutch samples are inherently small. Even Giannis' 56 clutch attempts being the largest in this list represents roughly 1-2 shots per close 4th quarter game. At that sample size, a few made or missed shots meaningfully swing the percentage. Players at the minimum threshold of 35 attempts should be interpreted with significant caution.
The context score weights (0.40, 0.25, 0.20, 0.15) are manually assigned, not statistically derived. A different weighting scheme would produce a different ranking. The model has no internal validation confirming these weights are optimal.
The spread between top and bottom context scores is relatively narrow given that Cooper Flagg at 73.1 vs Kevin Durant at 62.5 is a 10.6 point gap across the top 15. This is much tighter than Stage 3's 100.0 to 62.5 spread, suggesting situational performance is more uniform across good players than shot difficulty.


### Stage 5 - Team Independence
The previous four stages measure what a player does individually, given that we measured how much they score, how efficiently, on how hard shots, and in what situations. But none of them answer: how much of that scoring is dependent on their team's system and surrounding talent? Stage 5 addresses this by measuring how much better or worse a team performs offensively and overall when a player is on versus off the court.

What we measure
NET_RATING_IMPACT — the difference in team net rating with the player on vs off the court. The single most important signal of individual impact independent of teammates.
OFF_RATING_IMPACT — same calculation but for offensive rating specifically. Isolates scoring contribution from defensive impact.
NET_RATING_ON — absolute team quality when the player is on court. Distinguishes players who elevate bad teams from players who merely contribute to already good ones.

How the Independence Score is built
Three features scaled 0-1 and blended (i.e: we add them all together and re-scale it from 0-100):
NET_RATING_IMPACT  × 0.50
OFF_RATING_IMPACT  × 0.30
NET_RATING_ON      × 0.20

Higher score means the team is meaningfully better with the player on court, particularly offensively, and that the team is genuinely good when they play. Also, a higher independence score correlates to your scoring directly translating to team success, and also gives stronger implications that this NBA player is the offense. In the polar opposite case, a lower score may imply minimal impact and that the scoring is more so a reflection of the system, essentially that the scoring may be replacable.

Key Findings

Wembanyama leads at 100.0 — The spurs posts a NET_RATING of +17.0 with him on court vs +0.6 without him, a swing of 16.4 points per 100 possessions. That is an extraordinary number for a player in his second season. His offensive impact (6.2) is lower than his overall impact, suggesting his defensive presence is a significant part of the swing, but his scoring independence is still elite given SAS' offensive rating jumps dramatically with him on court.

Jokić at 99.3 with an OFF_RATING_IMPACT of 13.4 is the most analytically interesting finding in Stage 5. His offensive impact is the highest of any player in the top 5, meaning Denver's offense is 13.4 points per 100 possessions better with him on court. This directly addresses the Stage 3 limitation where his low shot difficulty score seemed to undervalue him, as Jokić doesn't need to take hard shots because he makes everyone around him more efficient. The on/off data confirms he is the engine of Denver's offense, rather than a weapon within the offense.

SGA at 99.0 with NET_RATING_ON of +16.3 is the strongest absolute team quality finding. OKC is a genuinely elite team when he plays, not just marginally better. Combined with his Stage 1-4 results, SGA's cross-stage consistency is unmatched in the entire dataset.

Kawhi at 96.0 — LA's net rating swings 13.8 points with him on vs off. Given that the Clippers are a below average team without him (NET_RATING_OFF of -6.3), this confirms he is single-handedly keeping them competitive. His scoring independence is real as he is not benefiting from a system or teammate quality.

Giannis at 94.6 with a NET_RATING_OFF of -9.7 is the most dramatic dependency finding. Milwaukee collapses without him to a nearly -10 net rating, one of the largest off-court drops in the dataset. Combined with his Stage 4 clutch finding, Giannis is both the most clutch and the most irreplaceable player on his team. This is pretty consistent as the Bucks looked like a lottery team without him this season, whereas they were a more competitive team in the games he did play.

JJJ at 94.3 averaged across two team stints reflects genuine impact. Memphis is dramatically worse without him regardless of which team context you look at, confirming he is a true franchise cornerstone despite playing for a rebuilding team.

Limitations/Potential Bias
Since this model blends statistics like offensive rating and net rating into an independence score, it may not fully capture true individual impact. Julian Champagnie ranking 7th exposes a key limitation as net rating on/off splits do not account for lineup quality. While his volume and effecient 3pt shooting is valuable on a middle of the pack spacing team like the spurs, it is also important to note that when Champagnie is off the court, other starters including Wembanyama may also be resting. This artificially tanks the team's off-court net rating and inflates Champagnie's apparent impact. This is a known confounding problem with on/off metrics, a player's independence score reflects who else is on or off the court at the same time, not purely their individual contribution.

Another potential bias is team roster quality. For star players on contending teams, net rating impact may actually be understated because their teammates are also high quality. When the star sits, other capable players compensate, minimizing the on/off gap, conversely, stars on rebuilding teams show larger net rating swings because their absence exposes a much weaker supporting cast. This means the independence score may inadvertently penalize players on deep rosters and reward players on talent-thin teams, which is outside of the individual player's control. It makes findings like Wembenyama's and SGA's 13+ point impacts even more impressive given the quality of their surrounding rosters.

Statistical Significance
On/off splits are among the most reliable advanced metrics available because they measure actual outcomes rather than modeled predictions. A 13+ point NET_RATING_IMPACT like Jokić or Kawhi represents thousands of possessions of evidence, making these findings genuinely statistically meaningful.
However, lineup combinations introduce confounding, as a player's on/off numbers are influenced by which teammates they share the court with and which lineups they face. A star who plays exclusively with other stars will have inflated off-court numbers because their absence coincides with weaker lineups taking the floor.
Small market and rebuilding teams systematically produce larger on/off swings because their supporting cast is weaker. This inflates independence scores for players on bad teams and slightly deflates them for players on deep rosters like Boston or Denver.

Final Model Interpretation
As the previous 5 stages measure separate aspects of scoring that show the true value of a specific side of scoring, whether that be volume, efficiency, shot difficulty, situational context, or team independence, the TRUE_SCORING_IMPACT score answers a single question: "If you needed someone to score for your team in the most complete and valuable way possible, who would you pick?" This composite metric blends all 5 stages into a single score, rewarding players who demonstrate sustained scoring value across multiple dimensions rather than excelling in just one.

What we measure
The TRUE_SCORING_IMPACT score is a weighted composite of all 5 stages:
VOLUME_SCORE (Stage 1) — How much scoring burden the player carries. Rewards players who handle high usage, attempt more shots, and play heavy minutes.
EFFICIENCY_SCORE (Stage 2) — How efficiently the player scores relative to what is expected given their role. Rewards players who beat their expected TS% at high usage.
DIFFICULTY_ADJ_EFFICIENCY (Stage 3) — How efficiently the player scores adjusted for how hard their shots actually are. Rewards players who convert on self-created, high difficulty attempts.
CONTEXT_SCORE (Stage 4) — How well the player performs in high pressure situations. Rewards players who elevate in clutch moments, late game situations, and away from home.
INDEPENDENCE_SCORE (Stage 5) — How much the team depends on the player's scoring. Rewards players whose presence meaningfully improves the team's offensive and overall performance.

A player who scores high across all five dimensions is not just a scorer, but they are a complete and irreplaceable offensive weapon. The composite rewards breadth of scoring value over dominance in any single dimension.

How the Total scorimg impact Score is built
Each of the 5 stage scores is already scaled to 0-100 from their respective models. Before combining them, each stage score is independently rescaled to 0-1 using MinMaxScaler. The final composite is computed as a straight weighted sum:
TRUE_SCORING_IMPACT =
    VOLUME_SCORE              × 0.275 +
    DIFFICULTY_ADJ_EFFICIENCY × 0.250 +
    EFFICIENCY_SCORE          × 0.250 +
    CONTEXT_SCORE             × 0.150 +
    INDEPENDENCE_SCORE        × 0.075

A higher score implies that the player is overall more complete across all weighted dimensions of scoring. A lower score does not necessarily mean the player is a poor scorer, but rather that their scoring value is concentrated in fewer dimensions rather than distributed across volume, efficiency, difficulty, context, and team independence simultaneously.

One thing to note is that: The independent rescaling step ensures no single stage dominates the composite due to a wider score distribution (every stage contributes based on relative position within that stage rather than raw magnitude).

Key Findings
SGA at 100.0 — the most complete scorer in the NBA this season. No other player in the dataset combines elite scores across all 5 dimensions the way he does. He ranks top 5 in volume, efficiency, difficulty-adjusted efficiency, and team independence simultaneously. 

Luka at 92.1 with the highest volume score (97.3) but relatively weak efficiency (55.7). This is the most important finding for evaluating Luka. He is the highest volume scorer in the dataset by a significant margin, but his efficiency and difficulty-adjusted efficiency rank lower than peers like SGA, KD, and Kawhi.

Luka at 92.1 with the highest volume score (97.3) but relatively weak efficiency (55.7). This is the most important finding for evaluating Luka. He is the highest volume scorer in the dataset by a significant margin, but his efficiency and difficulty-adjusted efficiency rank lower than peers like SGA, KD, and Kawhi.

Jaylen Brown at 80.3 with the 2nd highest volume score (89.5) but the lowest efficiency in the top 15 (44.6) is the starkest efficiency-volume gap in the dataset. He attempts a massive number of shots but converts at a rate that significantly lags his peers. Combined with a low independence score (68.6), the model suggests his scoring value comes from the Celtics offensive design, as well as tough shot-making ability combined with the volume and scoring reputability.

Cam Spencer at 75.4 is interesting as he only averages 11.1 PPG but ranks 23rd overall elite efficiency + shot difficulty which carrys him, but low volume correctly penalizes him from top 10. 

The bottom 10 consists of mostly young/developing players or inefficient big men like Nurkić, Eason, Plowden. Essentially players who operate on low efficiency, low difficulty, low independence. This makes sense as it is consistent with the scoring impact formula as these guys are not established scorers.

Limations/Potential Bias:
Weight subjectivity. The five stage weights (27.5%, 25%, 25%, 15%, 7.5%) are manually assigned based on basketball intuition, not statistically derived. A different weighting scheme would produce a different ranking. For instance, giving volume a slightly lower weight would elevate Kawhi and KD over Luka. Giving independence a higher weight would elevate Jokić and Wembanyama. The model reflects one defensible weighting philosophy, not the objectively correct one.

One season sample. The entire model reflects 2025-26 only. Players coming off injury, in contract years, or in new systems will look different than their career baseline. Kawhi Leonard's numbers reflect a limited games played sample. Embiid's context score (36.6) is among the lowest in the top 25, partly reflecting missed time and rust rather than genuine situational weakness. Even someone like Cade Cunningham, who has a 73.9 overall score and is right outside the top 25, had dealt with a rib injury so his late season scoring completely tanked his scoring volume and effeciency.

The model measures scoring, not overall value. A player like Jrue Holiday, Draymond Green, or Mikal Bridges may contribute enormous value to winning basketball without ranking highly here. This model deliberately narrows its scope to scoring impact only, so obviously it should not be interpreted as an overall player value metric.

Statistical Significance
The final composite inherits the statistical properties of its components. Stage 1 and Stage 2 are built on 384 players with full season samples, these are the most statistically reliable inputs. Stage 3 uses 102,400 individual shot attempts, making shot-level aggregations highly reliable for players with 200+ attempts. Stage 4 clutch splits remain the weakest input given inherently small sample sizes, and Stage 5 on/off data is reliable for star players with heavy minutes but noisy for players with inconsistent roles.

The top and bottom of the final rankings are the most defensible findings. SGA at 100.0 and players like Daeqwon Plowden at 39.1 reflect genuine, consistent differences across multiple independent data sources. The middle of the distribution may consist of players within statistical noise of each other and should not be interpreted as precise ordinal rankings. In example, The 7.5 point gap between SGA (100.0) and Luka (92.1) is meaningful and consistent with the cross-stage evidence. The 1.0 point gap between Jokić (88.1) and Ant (87.9) is not as those two players are statistically indistinguishable at this level of model precision.

Correlation between stages is an unresolved issue. shot-difficulty and volume are not fully independent as high usage players face tougher defense which affects shot quality. Difficulty and efficiency overlap by design in Stage 3. This means the composite is not a sum of truly independent signals, which inflates confidence in the final rankings somewhat. A future improvement would be to orthogonalize the stage scores using PCA before combining them, removing the overlap between correlated inputs and producing a more statistically independent composite.

