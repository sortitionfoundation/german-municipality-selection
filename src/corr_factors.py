import pandas as pd


def calcCorrFactors(groups: pd.DataFrame, muns: pd.DataFrame, params: dict):
    # calculate correction factors for all groups
    corrFactorsGroups = groups \
        .assign(CFm = lambda x: params['Ttot'] / x['Tg'] * x['Ng'] / params['Ntot']) \
        .filter(['CFm'])

    # assign correction factors to municipalities
    corrFactorsMuns = muns.filter(['MunName', 'StateID', 'ClassID', 'Nm']) \
        .reset_index() \
        .merge(corrFactorsGroups, on=['StateID', 'ClassID']) \
        .sort_values(by='MunID') \
        .set_index('MunID')

    return corrFactorsMuns