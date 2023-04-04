from typing import List

import pandas as pd

from src.select import selectMuns


def determineProbabilities(muns: pd.DataFrame, targetsAdjusted: pd.DataFrame, Ns: List[int]):
    ret = None

    # initialise hits dict
    muns['Hist'] = 0

    # loop over iterations
    Ntot = 0
    for i, N in enumerate(Ns):
        selected = selectMuns(muns, targetsAdjusted, N)
        Ntot += N

        for munID in selected:
            muns.loc[munID, 'Hist'] += 1

        # add to dataframe returned
        muns['FinalProb'] = muns['Letters'] * muns['Hist'] / Ntot
        muns['FinalProbWOCorr'] = muns['LettersWOCorr'] * muns['Hist'] / Ntot

        # append round
        append = muns.query(f"Population!=0")[['FinalProb', 'FinalProbWOCorr']].copy()
        append['Round'] = i
        if ret is None:
            ret = append
        else:
            ret = pd.concat([ret, append])

    return ret