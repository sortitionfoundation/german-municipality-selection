import pandas as pd

from src.commons import stateNames


def adjustTargets(targetsInitial: dict, muns: pd.DataFrame):
    targets = targetsInitial.copy()

    # update targets to avoid zeros
    for stateID, stateName in stateNames.items():
        for cat in muns['Größenklasse'].unique():
            isZero = targets.loc[stateID, f"Target_Cat{cat}"] == 0
            doesExist = not muns.query(f"State=={stateID} & Größenklasse=={cat}").empty

            if isZero and doesExist:
                targets.loc[stateID, f"Target_Cat{cat}"] = 1
                targets.loc[stateID, f"Target"] += 1

    # count total target number
    T = targets['Target'].sum()

    return targets, T