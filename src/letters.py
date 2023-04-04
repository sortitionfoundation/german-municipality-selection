import pandas as pd

from src.commons import stateNames


def determineNumbLetters(T: int, L: int, targets: pd.DataFrame, muns: pd.DataFrame):
    # update targets to avoid zeros
    for stateID, stateName in stateNames.items():
        for cat in muns['Größenklasse'].unique():
            # where to update letter numbers
            cond = (muns['State']==stateID) & (muns['Größenklasse']==cat)

            # add column containing target of group
            muns.loc[cond, 'TargetGroup'] = targets.loc[stateID, f"Target_Cat{cat}"]

            # add column containing population of group
            muns.loc[cond, 'PopulationGroup'] = muns.loc[cond, 'Population'].sum()

    # calculate number of letters to send for municipalities in that group
    populationTotal = muns['Population'].sum()
    muns['Letters'] = L / T * T / muns['TargetGroup'] * muns['PopulationGroup'] / populationTotal / muns['Population'].astype(float)
    muns['LettersWOCorr'] = L / T

    # chances of success
    # muns['ProbMultiplier'] = 1.0 / muns['PopulationGroup'].astype(float)
