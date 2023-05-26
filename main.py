#!/usr/bin/env python3
import argparse
from typing import List

from src.caching import readCache
from src.export import exportResults
from src.read import readData
from src.plot import plotLine
from src.probabilities import determineProbabilities
from src.replacements import selectReplacements
from src.selection import selectMuns
from src.groups import defineGroups
from src.seed import setRandomSeed


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
    parser.add_argument('-K', '--iterations', default='5000,10000')
    parser.add_argument('-n', '--no-probs', action='store_true', default=False)
    parser.add_argument('-S', '--seed', default=None)
    parser.add_argument('-p', '--plot-only', action='store_true', default=False)

    # parse args
    args = parser.parse_args()
    iterations = [int(K) for K in args.iterations.split(',')]

    # run
    run(args.ttotinit, args.letters, iterations, args.no_probs, args.seed, args.plot_only)


# calling 'run' will load the database, generate the statistics, and perform the selection
def run(Ttot_init: int, Ltot: int, Ks: List[int], no_probs: bool, seed: int, plot_only: bool):
    # load municipalities data
    states, muns = readData()

    # initialise key parameters
    params = {
        'Ttot_init': Ttot_init, # initial target for number of municipalities to select
        'Ltot': Ltot, # total number of letters to send out
        'Ntot': muns['Nm'].sum(), # total population in Germany
    }

    # get groups and targets
    muns, groups = defineGroups(muns, params)

    if not plot_only:
        # set seed
        setRandomSeed(seed)

        # select municipalities once
        stats = selectMuns(muns, groups, params)
        
        # determine municipalities that can still be selected (those that have not been selected yet)
        munsAvailable = muns[~muns.index.isin(stats.query('Selected==1').index)]

        # replacements 1
        statsReplacements1 = selectReplacements(munsAvailable)

        # determine municipalities that can still be selected (those that have not been selected yet)
        munsAvailable = muns[~(muns.index.isin(stats.query('Selected==1').index) | muns.index.isin(statsReplacements1.query('Selected==1').index))]

        # replacements 2
        statsReplacements2 = selectReplacements(munsAvailable)

        # export results (targets, selection, and stats) to a spreadsheet
        exportResults(muns, groups, states, stats, statsReplacements1, statsReplacements2, params)

        # determine probability of selection for each municipality
        if not no_probs:
            probs = determineProbabilities(muns, groups, params, Ks)
    else:
        print('Plotting only -- loading probs from cache')
        probs = readCache('Probs')
        if probs is None:
            raise Exception('Probs cache file could not be found!')

    # plot line of probabilities
    if not no_probs:
        plotLine(probs, params)


# calling main function
if __name__ == "__main__":
    launch()
