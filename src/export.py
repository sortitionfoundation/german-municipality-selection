import pandas as pd

from voting import apportionment

from src.path import wd


# export results to spreadsheet
def exportResults(muns: pd.DataFrame, groups: pd.DataFrame, corrFactorsMuns: pd.DataFrame, choices: pd.DataFrame, params: dict):
    # list of chosen municipalities (with repetition)
    munsSelected = muns.loc[choices.query("Selected==1").index].copy()

    # add number of muns selected per group for monitoring purposes
    groupsExport = groups.copy()
    groupsExport['Tg monitor'] = munsSelected.groupby('GroupID').size()
    groupsExport['Tg monitor'] = groupsExport['Tg monitor'].fillna(0).astype(int)

    # stack ClassID in groups for export
    groupsExport = groupsExport.reset_index().set_index(['StateID', 'ClassID']).unstack('ClassID')

    # assign letters via StLague
    munsSelected['Letters'] = apportionment.sainte_lague(corrFactorsMuns.loc[munsSelected.index, 'CFm'].values, params['Ltot'])

    # export to spreadsheet
    with pd.ExcelWriter(wd / 'output' / 'results.xlsx') as writer:
        groupsExport.to_excel(writer, sheet_name='Targets')
        munsSelected.to_excel(writer, sheet_name='Selected')
