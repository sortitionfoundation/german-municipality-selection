import pandas as pd

from voting import apportionment

from src.path import wd


# export results to spreadsheet
def exportResults(muns: pd.DataFrame, groups: pd.DataFrame, stats: pd.DataFrame, params: dict):
    # list of chosen municipalities (with repetition)
    statsSelected = stats.query("Selected==1")
    munsSelected = muns.loc[statsSelected.index].copy()

    # add correction factors
    munsSelected.loc[statsSelected.index, 'CFm'] = statsSelected['CFm']

    # add number of muns selected per group for monitoring purposes
    groupsExport = groups.copy()
    groupsExport['Tg monitor'] = munsSelected.groupby('GroupID').size()
    groupsExport['Tg monitor'] = groupsExport['Tg monitor'].fillna(0).astype(int)

    # stack ClassID in groups for export
    groupsExport = groupsExport.reset_index().set_index(['StateID', 'ClassID']).unstack('ClassID')

    # assign letters via StLague
    munsSelected['Letters'] = apportionment.sainte_lague(munsSelected['CFm'].values, params['Ltot'])

    # export to spreadsheet
    with pd.ExcelWriter(wd / 'output' / 'results.xlsx') as writer:
        groupsExport.to_excel(writer, sheet_name='Targets')
        munsSelected.to_excel(writer, sheet_name='Selected')
