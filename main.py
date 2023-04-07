#!/usr/bin/env python3
from src.corr_factors import calcCorrFactors
from src.export import exportResults
from src.read import readData
from src.path import wd
from src.plot import plotLine
from src.probabilities import determineProbabilities
from src.choose import chooseMuns
from src.groups import getGroups


# calling 'run' will load the database, generate the statistics, and perform the selection
def run():
    # load municipalities data
    states, muns = readData()
    print(states)

    # initialise key parameters
    params = {
        'Ttot_init': 80, # initial target for number of municipalities to select
        'Ltot': 20000, # total number of letters to send out
        'Ntot': muns['Nm'].sum(), # total population in Germany
    }

    # get groups and targets
    groups = getGroups(states, muns, params)

    # determine correction factors
    corrFactorsMuns = calcCorrFactors(groups, muns, params)

    # select municipalities once
    choices = chooseMuns(muns, groups)

    # export results (targets, selection, and stats) to a spreadsheet
    exportResults(muns, groups, corrFactorsMuns, choices, params)

    # determine probability of selection for each municipality
    Ks = [20000, 50000, 200000]
    probs = determineProbabilities(muns, groups, corrFactorsMuns, params, Ks)

    # plot line of probabilities
    plotLine(probs, params)


# calling main function
if __name__ == "__main__":
    run()
