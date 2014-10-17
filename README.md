Poisson Football - Computational Bayesian Project

This repository contains two models to attempt to predict football games, both of which are centered on Poisson Processes, and relatively limited in what they can do. The model ignores the uncommon ways to score, focusing instead on 7 point touchdowns and 3 point field goals. The model assumes that every touchdown would come with a one point extra point, and that safeties never happen. We also assumed that scoring happens in a Poisson manner, so that it is equally likely to score at any point in time. We did not incorporate overtime modeling. We found the probabilities of the first team winning, the second team winning, and the game going into OT.

The first model, in football1.py, is based upon two independent Poisson Processes, the first of which is for touchdowns, and the second of which is for field goals. These get updated independently, and then combined in order to predict a game.

The second model, in football2.py, is based on one Poisson Process to model scoring, and a second Suite of probabilities to capture the likelihood of the score being a TD or an FG. To compute the likelihood of scoring a certain number of points, we use the binomial distribution.


TODO:
Defense wins championships. How to incorporate that in. It can be modelled in the same way as the offense, but the question is, (assume the second model) given a lambda for scoring and a p_TD for the offense, and a lambda for scoring and a p_TD for the defense, how should the probability of scoring get determined? One thought is to use the current method with the average of the lambdas and the p_TDs, but that doesn't seem rigorous...

The spread (90% credible interval of points scored) of both models is wider than realistic. What's a good way to incorporate historical data in a way that brings each team's spread down, but still highlights the differences between teams as they currently are. (As opposed to being dominated by historical statistics.)
