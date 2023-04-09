import pandas as pd


def calcCorrFactors(muns: pd.DataFrame, groups: pd.DataFrame, params: dict):
    # calculate correction factors for all groups
    corrFactorsGroups = pd.DataFrame(index=groups.index, dtype=float)
    corrFactorsGroups['CFg'] = params['Ttot'] / groups['Tg'] * groups['Ng'] / params['Ntot']

    # groups with Tg >= Cg
    groupsToC = groups.loc[(groups['Tg'] >= groups['Cg']) & (groups['Cg'] > 0)].copy()

    # assign correction factors to municipalities
    corrFactorsMuns = muns.filter(['MunName', 'GroupID', 'Nm']) \
        .reset_index() \
        .merge(corrFactorsGroups, on='GroupID') \
        .sort_values(by='MunID') \
        .set_index('MunID') \
        .rename(columns={'CFg': 'CFm'})

    # assign correction factors
    condMunsToC = muns['GroupID'].isin(groupsToC.index)
    corrFactorsMuns.loc[condMunsToC, 'CFm'] = muns['Nm'] / params['Ntot'] * params['Ttot']

    return corrFactorsMuns