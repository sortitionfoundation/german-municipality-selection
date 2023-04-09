from typing import List

import pandas as pd

from src.caching import writeCache
from src.choose import chooseMuns


Kbatch = 10000


def determineProbabilities(muns: pd.DataFrame, groups:pd.DataFrame, corrFactorsMuns:pd.DataFrame, params: dict, Ks: List[int]):
    # check input parameters
    if any(Ks[i] <= Ks[i-1] for i in range(1,len(Ks))):
        raise Exception(f"The list of iterations has to be strictly increasing.")

    # initialise histogram
    probs = corrFactorsMuns.copy().filter(['CFm'])
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
            choices = chooseMuns(muns, groups, min(Kchoose, Kbatch))
            Kchoose -= Kbatch

            # add number of times chosen to histogram
            probs.loc[choices.index, 'Hist'] += choices['Selected'].values

        # add K to total number of times chosen
        Klast = K

        # calculate probabilitiy after iteration
        probs[K] = params['Ltot'] / params['Ttot'] * probs['CFm'] / muns['Nm'] * probs['Hist'] / Klast

    probs = probs \
        .reset_index() \
        .drop(columns=['Hist', 'CFm']) \
        .melt(id_vars='MunID', var_name='Iteration', value_name='Prob')

    # write to cache
    writeCache('Probs', probs)

    return probs
