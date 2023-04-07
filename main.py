#!/usr/bin/env python3
import argparse
from typing import List

from src.caching import readCache
from src.corr_factors import calcCorrFactors
from src.export import exportResults
from src.read import readData
from src.path import wd
from src.plot import plotLine
from src.probabilities import determineProbabilities
from src.choose import chooseMuns
from src.groups import getGroups


# the launch function handles command-line parameters
def launch():
    # create parser
    parser = argparse.ArgumentParser(
        prog='German Municipality Selection',
        description='Randomly selecting municipalities from the German municipality register.',
        epilog='For further help, please refer to the code on GitHub.',
    )
    parser.add_argument('-L', '--letters', default=20000)
    parser.add_argument('-T', '--ttotinit', default=80)
    parser.add_argument('-K', '--iterations', default='500,5000')
    parser.add_argument('-p', '--plot-only', action='store_true', default=False)

    # parse args
    args = parser.parse_args()
    iterations = [int(K) for K in args.iterations.split(',')]

    # run
    run(args.ttotinit, args.letters, iterations, args.plot_only)


# calling 'run' will load the database, generate the statistics, and perform the selection
def run(Ttot_init: int, Ltot: int, Ks: List[int], plot_only: bool):
    # load municipalities data
    states, muns = readData()
    print(states)

    # initialise key parameters
    params = {
        'Ttot_init': Ttot_init, # initial target for number of municipalities to select
        'Ltot': Ltot, # total number of letters to send out
        'Ntot': muns['Nm'].sum(), # total population in Germany
    }

    if not plot_only:
        # get groups and targets
        groups = getGroups(states, muns, params)

        # determine correction factors
        corrFactorsMuns = calcCorrFactors(groups, muns, params)

        # select municipalities once
        choices = chooseMuns(muns, groups)

        # export results (targets, selection, and stats) to a spreadsheet
        exportResults(muns, groups, corrFactorsMuns, choices, params)

        # determine probability of selection for each municipality
        probs = determineProbabilities(muns, groups, corrFactorsMuns, params, Ks)
    else:
        print('Plotting only -- loading probs from cache')
        probs = readCache('Probs')
        if probs is None:
            raise Exception('Probs cache file could not be found!')

    # plot line of probabilities
    plotLine(probs, params)


# calling main function
if __name__ == "__main__":
    launch()
