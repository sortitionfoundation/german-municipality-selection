import random

import pandas as pd


def selectMuns(muns: pd.DataFrame, targets: pd.DataFrame, N: int = 1):
    selected = []

    for stateID in targets.index:
        for cat in muns['Größenklasse'].unique():
            # get the target to select for this state and category
            targetGroup = targets.loc[stateID, f"Target_Cat{cat}"]
            if not targetGroup: continue

            # get the list of eligible municipalities
            thisMuns = muns.query(f"State=={stateID} and Größenklasse=={cat}")

            # get their weights based on population size
            weights = (thisMuns['Population'] / thisMuns['Population'].sum()).values.tolist()

            # choose municipalities randomly
            choices = random.choices(thisMuns.index, weights=weights, k=targetGroup*N)

            # append to list of selected municipalities
            selected.extend(choices)

    return selected
