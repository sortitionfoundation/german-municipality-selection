import pandas as pd

from voting import apportionment


def getGroups(states: pd.DataFrame, muns: pd.DataFrame, params: dict):
    # define groups, compute population in g, compute share of population
    groups = muns \
        .groupby(['StateID', 'ClassID']) \
        .agg({'Nm': 'sum'}) \
        .rename(columns={'Nm': 'Ng'}) \
        .assign(Sg=lambda x: x['Ng'] / params['Ntot']) \
        .unstack('ClassID') \
        .fillna(0) \
        .stack('ClassID')

    # assign targets via StLague
    groups['Tg_init'] = apportionment.sainte_lague(groups['Ng'].values, params['Ttot_init'])

    # Tg should at least be one for any group with non-zero population
    groups['Tg'] = groups['Tg_init']
    cond = (groups['Tg'] == 0) & (groups['Ng'] > 0)
    groups.loc[cond, 'Tg'] = 1

    # set total target number as new parameter Ttot
    params['Ttot'] = groups['Tg'].sum()

    return groups