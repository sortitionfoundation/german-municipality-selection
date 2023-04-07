#!/usr/bin/env python3
import pandas as pd

from src.read import readData
from src.path import wd
from src.plot import plotLine


# calling 'run' will load the database, generate the statistics, and perform the selection
def run():
    L = 20000

    # load municipalities data
    muns = readData()
    Ptot = muns['Population'].sum()

    # load probabilities
    pathProbsCached = wd / 'cachedProbs.pkl'
    probabilities = pd.read_pickle(pathProbsCached)

    # plot line of probabilities
    plotLine(probabilities, L, Ptot)


# calling main function
if __name__ == "__main__":
    run()
