#!/usr/bin/env python3
from src.adjust import adjustTargets
from src.letters import determineNumbLetters
from src.load import loadMuns
from src.monitor import monitorSelected
from src.path import pwd
from src.plot import plotLine
from src.probabilities import determineProbabilities
from src.select import selectMuns
from src.stats import getStats


# calling 'run' will load the database, generate the statistics, and perform the selection
def run():
    Ti = 80 # initial target for number of municipalities to select
    L = 20000 # number of letters to send out

    # load municipalities data
    muns = loadMuns()
    Ptot = muns['Population'].sum()

    # generate statistics
    stats = getStats(muns, Ti)
    targetsInitial = stats['targets']
    print(targetsInitial)

    # adjust target numbers
    targetsAdjusted, T = adjustTargets(targetsInitial, muns)
    print(T)

    # determine number of letters
    determineNumbLetters(T, L, targetsAdjusted, muns)

    # select municipalities once
    selected = selectMuns(muns, targetsAdjusted)

    # generate monitoring output
    monitor = monitorSelected(muns, selected)
    print(monitor)

    # determine probability of selection for each municipality
    Ns = [100, 1000]
    probabilities = determineProbabilities(muns, targetsAdjusted, Ns)
    pathProbsCached = pwd / 'cachedProbs.pkl'
    probabilities.to_pickle(pathProbsCached)
    print(probabilities)

    # plot line of probabilities
    plotLine(probabilities, L, Ptot)


# calling main function
if __name__ == "__main__":
    run()
