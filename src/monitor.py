import pandas as pd

from src.commons import stateNames


def monitorSelected(muns: pd.DataFrame, selected: list):
    munsSelected = muns.loc[selected]

    # share of categories in each state
    records = []
    for stateID, stateName in stateNames.items():
        # initialise records
        r = {'State': stateID, 'StateName': stateName}

        # get final selected for each state
        munsInState = munsSelected.query(f"State=={stateID}")
        r['Final'] = len(munsInState)

        # get final selected for each category in each state
        for cat in muns['Größenklasse'].unique():
            munsInCatInState = munsInState.query(f"Größenklasse=={cat}")
            r[f"Final_Cat{cat}"] = len(munsInCatInState)

        # append record to list of records
        records.append(r)
    monitor = pd.DataFrame.from_records(records).set_index('State')

    return monitor