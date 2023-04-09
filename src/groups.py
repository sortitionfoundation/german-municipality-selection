import pandas as pd

from voting import apportionment


def defineGroups(muns: pd.DataFrame, params: dict):
    # define groups, compute population in g, compute share of population
    groups = muns \
        .groupby(['StateID', 'ClassID']) \
        .agg({'Nm': 'sum'}) \
        .rename(columns={'Nm': 'Ng'}) \
        .assign(Sg=lambda x: x['Ng'] / params['Ntot']) \
        .unstack('ClassID') \
        .fillna(0) \
        .stack('ClassID')

    # add GroupID and set as index
    groups['GroupID'] = [j + 3*(i-1) for i, j in groups.index.values]
    groups = groups.reset_index().set_index('GroupID')

    # add GroupID to muns
    muns = muns \
        .reset_index() \
        .merge(groups.filter(['StateID', 'ClassID']).reset_index(), on=['StateID', 'ClassID']) \
        .set_index('MunID') \
        .sort_index()

    # assign targets via StLague
    groups['Tg_init'] = apportionment.sainte_lague(groups['Ng'].values, params['Ttot_init'])

    # Tg should at least be one for any group with non-zero population
    groups['Tg'] = groups['Tg_init']
    cond = (groups['Tg'] == 0) & (groups['Ng'] > 0)
    groups.loc[cond, 'Tg'] = 1

    # assign count of muns in groups
    groups['Cg'] = 0
    groupsCount = muns.groupby('GroupID')['GroupID'].count()
    groups.loc[groupsCount.index, 'Cg'] = groupsCount.values

    # set total target number as new parameter Ttot
    params['Ttot'] = groups['Tg'].sum()

    return muns, groups