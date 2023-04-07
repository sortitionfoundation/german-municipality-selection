from typing import List

import pandas as pd

from src.caching import writeCache
from src.choose import chooseMuns


def determineProbabilities(muns: pd.DataFrame, groups:pd.DataFrame, corrFactorsMuns:pd.DataFrame, params: dict, Ks: List[int]):
    # check input parameters
    if any(Ks[i] <= Ks[i-1] for i in range(1,len(Ks))):
        raise Exception(f"The list of iterations has to be strictly increasing.")

    # initialise histogram
    probs = corrFactorsMuns.copy().filter(['CFm'])
    probs['Hist'] = 0

    # loop over iterations
    Ktot = 0
    for i, K in enumerate(Ks):
        # choose K times
        choices = chooseMuns(muns, groups, K-Ktot)

        # add K to total number of times chosen
        Ktot = K

        # add number of times chosen to histogram
        probs['Hist'] += pd.Series(choices).value_counts()

        # calculate probabilitiy after iteration
        probs[K] = params['Ltot'] / params['Ttot'] / muns['Nm'] * probs['Hist'] / Ktot

    probs = probs \
        .reset_index() \
        .drop(columns=['Hist', 'CFm']) \
        .melt(id_vars='MunID', var_name='Iteration', value_name='Prob')

    # write to cache
    writeCache('Probs', probs)

    return probs
