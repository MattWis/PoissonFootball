"""This file contains code for use with "Think Bayes",
by Allen B. Downey, available from greenteapress.com

Copyright 2014 Allen B. Downey
License: GNU GPLv3 http://www.gnu.org/licenses/gpl.html
"""

from __future__ import print_function, division

import numpy
import thinkbayes2
import thinkplot
from scrape import scrape_team

class Football():
    """Represents hypotheses about a football team's offense and defense"""

    def __init__(self, hypos, team_name = "None"):
        self.offense = OffenseOrDefense(hypos)
        self.defense = OffenseOrDefense(hypos)
        self.name = team_name

    def UpdateOffense(self, data):
        self.offense.Update(data)

    def UpdateDefense(self, data):
        self.defense.Update(data)

    def PredRemaining(self, rem_time, score, opp_team):
        adjusted = OffenseOrDefense(([0],[0]))
        adjusted.score = self.offense.score.AddPmf(opp_team.defense.score) / 2
        adjusted.TDPercent = self.offense.TDPercent.AddPmf(opp_team.defense.TDPercent) / 2

        return adjusted.PredRemaining(rem_time, score)

class OffenseOrDefense():
    """ Represents hypotheses about a Football teams offense or defense,
    in terms of scores per game, and the probability of a given
    score being a TD.


    For offense, it's the goals scored.
    For defense, it's the goals allowed.
    """

    def __init__(self, hypos):
        self.score = ScoreCount(hypos[0])
        self.TDPercent = BooleanEstimator(hypos[1])

    def Update(self, data):
        """Update the child PMFs based on the data.
        data = (time since last score, boolean flag for the score being a TD)
        """
        self.score.Update(data[0])
        self.TDPercent.Update(data[1])

    def PredRemaining(self, rem_time, points_scored):
        """Plots the predictive distribution for final number of goals.

        rem_time: remaining time in the game in minutes
        points_scored: points already scored
        """
        scorePredict = scorePredRemaining(self.score, rem_time, 0)
        scorePmf = thinkbayes2.Pmf()
        for prob_td, prob_p in self.TDPercent.Items():
            tdProbPmf = thinkbayes2.Pmf()
            for scores, prob_s in scorePredict.Items():
                for num_tds in range(scores + 1):
                    num_fgs = scores - num_tds
                    points = 7 * num_tds + 3 * num_fgs

                    ncr = thinkbayes2.BinomialCoef(scores, num_tds)
                    coef_prob = prob_td**num_tds * (1 - prob_td)**num_fgs
                    tdProbPmf.Incr(points, prob_s * ncr * coef_prob)
            scorePmf.Incr(tdProbPmf, prob_p)

        return thinkbayes2.MakeMixture(scorePmf) + points_scored

class BooleanEstimator(thinkbayes2.Suite):
    """Represents a choice between 2 options"""

    def Likelihood(self, data, hypo):
        """Computes the likelihood of the data under the hypothesis.

        data: boolean indicating if the event happened
        hypo: the probability of the event happening
        """
        if data is True:
            return hypo
        else:
            return 1 - hypo

class ScoreCount(thinkbayes2.Suite):
    """Represents hypotheses about the lambda parameter of a
    Poisson Process to generate scores.
    """

    def Likelihood(self, data, hypo):
        """Computes the likelihood of the data under the hypothesis.

        hypo: hypothetical goal scoring rate in goals per game
        data: time between goals in minutes
        """
        x = data #time between goals in minutes
        lam = hypo/60.0 #goals per minute
        like = thinkbayes2.EvalExponentialPdf(x,lam) #evaluating for every value of lamda
        return like

def scorePredRemaining(pmf, rem_time, score):
    metapmf=thinkbayes2.Pmf()
    for lam, prob in pmf.Items():
        lt = lam*rem_time/60
        pmf=thinkbayes2.MakePoissonPmf(lt,20)
        metapmf[pmf]=prob

    mix = thinkbayes2.MakeMixture(metapmf)
    mix += score
    return mix

def constructPriors():
    """Constructs an even prior for both teams, and then
    uses data from www.covers.com from the 2014 season to
    update the priors
    """

    eagles_url = "/pageLoader/pageLoader.aspx?page=/data/nfl/teams/pastresults/2014-2015/team7.html"
    giants_url = "/pageLoader/pageLoader.aspx?page=/data/nfl/teams/pastresults/2014-2015/team8.html"

    eagles = Football((numpy.linspace(0, 20, 201), numpy.linspace(0, 1, 201)), "Eagles")
    giants = Football((numpy.linspace(0, 20, 201), numpy.linspace(0, 1, 201)), "Giants")

    eagles_data = scrape_team(eagles_url)
    giants_data = scrape_team(giants_url)

    last_time_o = 0
    last_time_d = 0
    for game in eagles_data:
        last_time_o += 60
        last_time_d += 60
        for item in game:
            TD = (item[1] == "TD")
            if item[2] == "Eagles":
                inter_arrival = last_time_o - item[0]
                eagles.UpdateOffense((inter_arrival, TD))
                last_time_o = item[0]
            else:
                inter_arrival = last_time_d - item[0]
                eagles.UpdateDefense((inter_arrival, TD))
                last_time_d = item[0]

    last_time_o = 0
    last_time_d = 0
    for game in giants_data:
        last_time_o += 60
        last_time_d += 60
        for item in game:
            if item[2] == "Giants":
                TD = (item[1] == "TD")
                inter_arrival = last_time_o - item[0]
                giants.UpdateOffense((inter_arrival, TD))
                last_time_o = item[0]
            else:
                inter_arrival = last_time_d - item[0]
                eagles.UpdateDefense((inter_arrival, TD))

    return eagles, giants


def main():
    """Look at the October 12th, 2014 game between the Giants and the Eagles,
    and predict the probabilities of each team winning.
    """

    eagles, giants = constructPriors()

    GoalTotalGiants = giants.PredRemaining(60, 0, eagles)
    GoalTotalEagles = eagles.PredRemaining(60, 0, giants)
    print("Giants win", GoalTotalEagles < GoalTotalGiants)
    print("Eagles win", GoalTotalGiants < GoalTotalEagles)
    print(GoalTotalEagles.MakeCdf().CredibleInterval(80))
    print(GoalTotalGiants.MakeCdf().CredibleInterval(80))

if __name__ == '__main__':
    main()
