#!/usr/bin/env python3
import pandas as pd

from src.load import loadMuns
from src.path import pwd
from src.plot import plotLine


# calling 'run' will load the database, generate the statistics, and perform the selection
def run():
    L = 20000

    # load municipalities data
    muns = loadMuns()
    Ptot = muns['Population'].sum()

    # load probabilities
    pathProbsCached = pwd / 'cachedProbs.pkl'
    probabilities = pd.read_pickle(pathProbsCached)

    # plot line of probabilities
    plotLine(probabilities, L, Ptot)


# calling main function
if __name__ == "__main__":
    run()
