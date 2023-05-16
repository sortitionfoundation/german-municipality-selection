import pandas as pd

from voting import apportionment

from src.path import wd
from src.read import sizeClasses


# export results to spreadsheet
def exportResults(muns: pd.DataFrame, groups: pd.DataFrame, states: pd.DataFrame, stats: pd.DataFrame,
                  statsReplacements: pd.DataFrame, params: dict):
    # list of chosen municipalities
    statsSelected = stats.query("Selected==1")
    munsSelected = muns.loc[statsSelected.index].copy()

    # list of municipality replacements
    munsReplacements = muns.loc[statsReplacements.query("Selected==1").index].copy() \
        .sort_values(by=['StateID', 'Nm']).reset_index(drop=True)

    # add correction factors
    munsSelected.loc[statsSelected.index, 'CFm'] = statsSelected['CFm']

    # assign letters via StLague
    munsSelected['Letters'] = apportionment.sainte_lague(munsSelected['CFm'].values, params['Ltot'])

    # add number of muns selected per group for monitoring purposes
    groupsExport = groups.copy()
    groupsExport['Tg monitor'] = munsSelected.groupby('GroupID').size()
    groupsExport['Tg monitor'] = groupsExport['Tg monitor'].fillna(0).astype(int)

    # add number of letters in each group
    groupsExport['Letters'] = munsSelected.groupby('GroupID')['Letters'].sum()
    groupsExport['Letters rel'] = groupsExport['Letters'] / params['Ltot'] * 100.0

    # add names of size classes
    classNameMapping = {
        ClassID: ClassSpecs['name']
        for ClassID, ClassSpecs in sizeClasses.items()
    }
    munsSelected['ClassName'] = munsSelected['ClassID'].map(classNameMapping)

    # add state names
    munsSelected = munsSelected.merge(states, on=['StateID'])
    groupsExport = groupsExport.merge(states, on=['StateID'])

    # stack ClassID in groups for export
    groupsExport = groupsExport.set_index(['StateID', 'ClassID']).unstack('ClassID')

    # sort municipalities
    munsSelected = munsSelected.sort_values(by=['StateID', 'Nm']).reset_index(drop=True)

    # convert shares to percent
    groupsExport['Sg'] *= 100.0

    # export to spreadsheet
    with pd.ExcelWriter(wd / 'output' / 'results.xlsx') as writer:
        groupsExport.to_excel(writer, sheet_name='Targets')
        munsSelected.to_excel(writer, sheet_name='Selected')
        munsReplacements.to_excel(writer, sheet_name='Replacements')

    print(munsSelected.head(15))
