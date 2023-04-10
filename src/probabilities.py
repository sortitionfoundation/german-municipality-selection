from typing import List

import numpy as np
import pandas as pd

from src.caching import writeCache
from src.selection import selectMuns


Kbatch = 10000


def determineProbabilities(muns: pd.DataFrame, groups:pd.DataFrame, params: dict, Ks: List[int]):
    # check input parameters
    if any(Ks[i] <= Ks[i-1] for i in range(1,len(Ks))):
        raise Exception(f"The list of iterations has to be strictly increasing.")

    # initialise histogram
    probs = pd.DataFrame(index=muns.index)
    probs['Hist'] = 0
    probs['Hist'] = probs['Hist'].astype(int)

    # loop over iterations
    Klast = 0
    for i, K in enumerate(Ks):
        print(K)
        # choose K-Ktot times
        Kchoose = K-Klast
        while Kchoose > 0:
            print(f"-- {min(Kchoose, Kbatch)}")
            stats = selectMuns(muns, groups, params, min(Kchoose, Kbatch))
            Kchoose -= Kbatch

            # add number of times chosen to histogram
            probs.loc[stats.index, 'Hist'] += stats['Selected'].values

        # add K to total number of times chosen
        Klast = K

        # calculate probabilitiy after iteration
        probs[K] = params['Ltot'] / params['Ttot'] * stats['CFm'] / muns['Nm'] * probs['Hist'] / Klast

    # probs
    probs = probs \
        .reset_index() \
        .drop(columns=['Hist']) \
        .melt(id_vars='MunID', var_name='Iteration', value_name='Prob')

    # write to cache
    writeCache('Probs', probs)

    return probs
