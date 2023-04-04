import pandas as pd
from voting import apportionment

from src.commons import stateNames


def getStats(muns: pd.DataFrame, targetTotal: int):
    # total population
    populationTotal = muns['Population'].sum()

    # share of states
    shareOfStates = muns.groupby('State').agg({'State': 'first', 'Population': 'sum'})
    shareOfStates = shareOfStates \
        .assign(Share=lambda x: x['Population'] / populationTotal) \
        .drop(columns='Population') \
        .set_index('State')

    # share of Größenklassen
    shareOfCategories = muns.groupby('Größenklasse').agg({'Größenklasse': 'first', 'Population': 'sum'})
    shareOfCategories = shareOfCategories \
        .assign(Share=lambda x: x['Population'] / populationTotal) \
        .drop(columns='Population')

    # resulting number of municipalities
    targetInState = pd.DataFrame.from_dict({
        'State': shareOfStates.index.to_list(),
        'Target': apportionment.sainte_lague(shareOfStates['Share'].values, targetTotal),
    }) \
    .set_index('State')

    # share of categories in each state
    records = []
    for stateID in stateNames:
        # initialise records
        r = {'State': stateID}

        # query for relevant municipalities
        munsInState = muns.query(f"State=={stateID}")

        # determine share of category in each state
        populationInState = munsInState['Population'].sum()
        share = {
            cat: munsInState.query(f"Größenklasse=={cat}")['Population'].sum() / populationInState
            for cat in muns['Größenklasse'].unique()
        }

        # determin
        targetInCatInState = dict(zip(
            share.keys(),
            apportionment.sainte_lague(list(share.values()), targetInState.loc[stateID, 'Target'])
        ))

        for c, d in {'Share': share, 'Target': targetInCatInState}.items():
            for cat in share:
                r[f"{c}_Cat{cat}"] = d[cat]

        # append record to list of records
        records.append(r)
    shareOfCategoriesInStates = pd.DataFrame.from_records(records).set_index('State')


    # create combined dataframe
    targets = pd.DataFrame.from_dict({
            'State': list(stateNames.keys()),
            'StateName': list(stateNames.values()),
        }) \
        .set_index('State') \
        .merge(shareOfStates, on='State') \
        .merge(targetInState, on='State') \
        .merge(shareOfCategoriesInStates, on='State')

    return {
        'total': populationTotal,
        'shareOfCategories': shareOfCategories,
        'targets': targets,
    }