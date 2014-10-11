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

    def __init__(self, hypos):
        self.TD = ScoreType(hypos[0])
        self.FG = ScoreType(hypos[1])

    def Update(self, data):
        self.TD.Update(data[0])
        self.FG.Update(data[1])

    def UpdateFG(self, delta_time):
        self.FG.Update(delta_time)

    def UpdateTD(self, delta_time):
        self.TD.Update(delta_time)

    def PredRemaining(self, rem_time, scores):
        FGpredict = self.FG.PredRemaining(60,0)
        TDpredict = self.TD.PredRemaining(60,0)
        GoalTotal = FGpredict * 3 + TDpredict * 7
        return GoalTotal

class ScoreType(thinkbayes2.Suite):
    """Represents hypotheses about."""

    def Likelihood(self, data, hypo):
        """Computes the likelihood of the data under the hypothesis.

        hypo: hypothetical goal scoring rate in goals per game
        data: time between goals in minutes

        x=quantity where evaluating print_function
        lam=parameter determining rate in events/unit time
        """
        x = data #time between goals in minutes
        lam = hypo/60.0 #goals per minute
        like = thinkbayes2.EvalExponentialPdf(x,lam) #evaluating for every value of lamda
        return like

    def PredRemaining(self, rem_time, score):
        """Plots the predictive distribution for final number of goals.

        rem_time: remaining time in the game in minutes
        score: number of goals already scored
        """
        metapmf=thinkbayes2.Pmf() #PMF about PMFS. probabilities of pmf values
        for lam, prob in self.Items(): #loop through probabilities of lamdas
            #print(lam,prob)
            lt = lam*rem_time/60
            pmf=thinkbayes2.MakePoissonPmf(lt,20)
            #thinkplot.Pdf(pmf,linewidth=1,alpha=0.2,color='purple')
            metapmf[pmf]=prob

        mix = thinkbayes2.MakeMixture(metapmf)
        mix += score #shift by 2 because we've already seen 2
        return mix

def score_to_TD_FG(score):
    """
    Assume that the score was created by the smaller number of TD+FG
    Also, assume that >8 scores per quarter doesn't happen
    So, 21 points is (3,0), not (0,7)
    """
    points = {3: (0,1), 7: (1,0)}
    two_scores = add_dicts(points, points)
    four_scores = add_dicts(two_scores, two_scores)
    eight_scores = add_dicts(four_scores, four_scores)

    if score == 0:
        return (0,0)
    if score in eight_scores:
        return eight_scores[score]
    else:
        raise ValueError("Score can't be that!")


def add_dicts(d1, d2):
    d3 = {}
    for k1, i1 in d1.items():
        for k2, i2 in d2.items():
            d3[k1 + k2] = (i1[0] + i2[0], i1[1] + i2[1])
            d3[k2] = i2
        d3[k1] = i1
    return d3


def constructPriors():

    eagles_url = "/pageLoader/pageLoader.aspx?page=/data/nfl/teams/pastresults/2014-2015/team7.html"
    giants_url = "/pageLoader/pageLoader.aspx?page=/data/nfl/teams/pastresults/2014-2015/team8.html"

    eagles = Football((numpy.linspace(0, 20, 201), numpy.linspace(0, 20, 201)))
    giants = Football((numpy.linspace(0, 20, 201), numpy.linspace(0, 20, 201)))

    eagles_data = scrape_team(eagles_url)
    giants_data = scrape_team(giants_url)

    last_time_FG_eagles = 0
    last_time_TD_eagles = 0
    for game in eagles_data:
        last_time_FG_eagles += 60.0
        last_time_TD_eagles += 60.0
        for item in game:
            if item[2] == "Eagles":
                if item[1] == "FG":
                    rem_time = item[0]
                    inter_arrival = last_time_FG_eagles - rem_time
                    last_time_FG_eagles = rem_time

                    eagles.UpdateFG(inter_arrival)
                if item[1] == "TD":
                    rem_time = item[0]
                    inter_arrival = last_time_TD_eagles - rem_time
                    last_time_TD_eagles = rem_time

                    eagles.UpdateTD(inter_arrival)

    last_time_FG_giants = 0
    last_time_TD_giants = 0
    for game in giants_data:
        last_time_FG_giants += 60.0
        last_time_TD_giants += 60.0
        for item in game:
            if item[2] == "Giants":
                if item[1] == "FG":
                    rem_time = item[0]
                    inter_arrival = last_time_FG_giants - rem_time
                    last_time_FG_giants = rem_time

                    giants.UpdateFG(inter_arrival)
                if item[1] == "TD":
                    rem_time = item[0]
                    inter_arrival = last_time_TD_giants - rem_time
                    last_time_TD_giants = rem_time

                    giants.UpdateTD(inter_arrival)


    #thinkplot.Pdf(suite.FG, label='priorFG')
    #print('Field Goal prior mean', suite.FG.Mean())
    #thinkplot.Pdf(suite.TD, label='priorTD')
    #print('Touchdown prior mean', suite.TD.Mean())

    ###construct priors using pseudo-observations
    #for (FGlam, TDlam) in zip(FG_per_game2014, TD_per_game2014):
        #suite.Update((60.0 / TDlam, 60.0 / FGlam))

    #thinkplot.Pdf(suite.FG, label='prior 2: FG pseudo-observation')
    #print('pseudo-observation', suite.FG.Mean())
    #thinkplot.Pdf(suite.TD, label='prior 2: TD pseudo-observation')
    #print('pseudo-observation', suite.TD.Mean())

    #thinkplot.Show()

    return eagles, giants


def main():

    eagles, giants = constructPriors()

    #if we know what lamda is, we know the goals left in the game.
    GoalTotal_giants = giants.PredRemaining(60, (0, 0))
    GoalTotal_eagles = eagles.PredRemaining(60, (0, 0))
    print("Giants win", GoalTotal_eagles.ProbLess(GoalTotal_giants))
    print("Eagles win", GoalTotal_giants.ProbLess(GoalTotal_eagles))
    #print(GoalTotal.MakeCdf().CredibleInterval(75))
    #thinkplot.Hist(GoalTotal_giants)
    #thinkplot.Show()

if __name__ == '__main__':
    main()
