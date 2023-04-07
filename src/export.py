import pandas as pd

from voting import apportionment

from src.path import wd



# export results to spreadsheet
def exportResults(muns: pd.DataFrame, groups: pd.DataFrame, corrFactorsMuns: pd.DataFrame, choices: pd.DataFrame, params: dict):
    # list of chosen municipalities (with repetition)
    munsChosen = muns.loc[choices]

    # add number of muns selected per group for monitoring purposes
    groupsExport = groups.copy()
    groupsExport['Tg monitor'] = munsChosen.groupby(['StateID', 'ClassID']).size()
    groupsExport['Tg monitor'] = groupsExport['Tg monitor'].fillna(0).astype(int)

    # stack ClassID in groups for export
    groupsExport = groupsExport.unstack('ClassID')

    # list of selected municipalities (without repetition)
    munsSelected = muns \
        .query(f"MunID in @choices") \
        .sort_values('MunID')

    # add correction factors to selected municipalities
    munsSelected['CFm'] = corrFactorsMuns['CFm']

    # add counts to municipalities
    munsSelected['Count'] = munsChosen.index.value_counts()

    # calculate score for municipalities
    munsSelected['Score'] = munsSelected['Count'] * munsSelected['CFm']

    # assign letters via StLague
    munsSelected['Letters'] = apportionment.sainte_lague(munsSelected['Score'].values, params['Ltot'])

    # export to spreadsheet
    with pd.ExcelWriter(wd / 'output' / 'results.xlsx') as writer:
        groupsExport.to_excel(writer, sheet_name='Targets')
        munsSelected.to_excel(writer, sheet_name='Selected')
