import pandas as pd


def calcCorrFactors(groups: pd.DataFrame, muns: pd.DataFrame, params: dict):
    # calculate correction factors for all groups
    corrFactorsGroups = groups \
        .assign(CFm = lambda x: params['Ttot'] / x['Tg'] * x['Ng'] / params['Ntot']) \
        .filter(['CFm'])

    # assign correction factors to municipalities
    corrFactorsMuns = muns.filter(['MunName', 'StateID', 'ClassID']) \
        .merge(corrFactorsGroups, on=['StateID', 'ClassID'])
    corrFactorsMuns.index.set_names('MunID', inplace=True)

    return corrFactorsMuns