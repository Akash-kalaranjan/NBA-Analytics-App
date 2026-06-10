### Who Am I?

At 9 years old, there was a scrawny and delusional kid who was tired of running around the soccer field and instead picked up a medium-sized bouncy white and light blue ball. In front of that ball, there was a 10-foot pole attached to a backboard and a double rim called a basketball net. He decided to throw the ball into the hoop Rick Barry style, not because he studied Barry's game, but because he did not know how to play this game called basketball.

Even though he was not very good at this game, he decided to try to get better, watch YouTube videos on how to shoot a basketball, and spend hours after school just to improve. Eventually, he fell in love with the game of basketball more than he could ever have dreamed of loving soccer. He fell in love with basketball so much that after making his elementary school's basketball team, he was fully determined to make it to the NBA. He would study players like Steph Curry, James Harden, and Kyle Lowry's games specifically, thinking he could shoot half-court shots just like them. To all the critics, he would always mention that players like Embiid, Siakam, and Giannis all started basketball later than he did, and that was reason enough to believe he would make it to the NBA. However, years later when he tried out for the high school basketball team, he did not come close despite what he felt was an amazing performance in tryouts. That is when reality hit and he was not going to make it to the NBA.

While the hopes of making it to the league at the age of 13 were destroyed, what was not destroyed was his ambition and confidence, it just shifted elsewhere. He could still find a career related to basketball, but it does not have to be on the court as a player. Math and basketball were his two favourite hobbies, and he used that to eventually get better at and study statistics.

Now, over a decade later, he is still finding his footing into a career he desires, and this personal project is a great way to do so.

My name is Akash Kalaranjan, and I built this web app out of my love for basketball. I am currently a student at the University of Toronto, entering my fourth year in the coming fall. I specialize in applied mathematics with a concentration in statistics, so I used a lot of the linear regression skills and Python knowledge I have gained from relevant courses to put into practice and showcase my skill set to the best of my abilities.

### Why I built the web app

When playing the game of basketball, the primary objective is to get the most effecient look possible in order to put the ball into the basket (and prevent the opposing team from doing so). In other words, scoring the basketball is the desired end goal of a possesion and in the bigger picture to use playmaking, defense and scoring to end up with more points than the opposing team. So on the highest stage of basketball in the world, that being the NBA, it is very important to understand what the most quality shot is. Now, I found that measuring the highest quality and most valuable scorers in the NBA is crucial to understanding what role in the offense a player should recieve. 

Moreover, Traditional scoring metrics like PPG and true shooting treat all points equally. In example, a wide open corner three counts the same as a pull-up fadeaway over a defender with 2 seconds on the shot clock. This makes it difficult to separate players who manufacture their own offense from those who benefit from system advantages, and it obscures who the truly elite scorers are. On the other hand, there are players who deserve far more shot attempts and offensive opportunities. These are players whose efficiency and impact suggest they should have a bigger role. That's why the Underrated Players tab was created: to identify which NBA players are being underutilized and what they could bring to their team's offense with an expanded role.

All in all, I wanted to build a metric that captures the full picture of a scorer's value: how much volume they carry, how efficiently they convert, how difficult their shots are, how they perform in high-stakes moments, and how much of their production is independent of their team. That's what True Scoring Impact measures.

### What this Project demonstrates

This project showcases a full end-to-end data science workflow, as instead of taking a CSV and analyzing it, I built the entire process from collecting data to building the true scoring impact model and showing results. That is, this project started from raw API ingestion and ended up into a deployed interactive web application. Some of the many key skills demonstrated include building automated data pipelines, feature engineering across multiple analytical stages, regression modelling, and data visualization with Streamlit and Plotly.

* **Data Pipeline**: Automated daily data ingestion from the NBA Stats API, processing through a 5-stage feature engineering pipeline
* **Feature Engineering**: Shot difficulty scoring, game context analysis, team independence modelling, and efficiency adjustment
* **Regression Modelling**: OLS regression to estimate expected scoring efficiency and isolate above-expectation performance
* **Web Development**: Interactive Streamlit dashboard with player profiles, leaderboards, comparison tools, and daily debate features

[View the full technical report](#) | [GitHub Repository](https://github.com/Akash-kalaranjan/NBA-Analytics-App)