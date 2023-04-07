import random

import pandas as pd


def chooseMuns(muns: pd.DataFrame, groups: pd.DataFrame, K: int = 1):
    choices = []

    # loop over non-zero groups
    for index, Tg in groups.loc[groups['Tg']!=0.0, 'Tg'].items():
        StateID, ClassID = index

        # get all eligible municipalities
        thisMuns = muns.query(f"StateID=={StateID} and ClassID=={ClassID}")

        # choose municipalities randomly weighted by population
        thisChoices = random.choices(thisMuns.index.values, weights=thisMuns['Nm'].values, k=K*Tg)

        # append to list of selected municipalities
        choices.extend(thisChoices)

    return choices
