import pandas as pd
from voting import apportionment

from src.path import wd
from src.read import sizeClasses


# export results to spreadsheet
def exportResults(muns: pd.DataFrame, groups: pd.DataFrame, states: pd.DataFrame, stats: pd.DataFrame,
                  statsReplacements1: pd.DataFrame, statsReplacements2: pd.DataFrame, params: dict):
    # list of chosen municipalities
    statsSelected = stats.query("Selected==1")
    munsSelected = muns.loc[statsSelected.index].copy()

    # list of municipality replacements
    munsReplacements1 = muns.loc[statsReplacements1.query("Selected==1").index].copy() \
        .sort_values(by=['StateID', 'Nm']).reset_index(drop=True)
    munsReplacements2 = muns.loc[statsReplacements2.query("Selected==1").index].copy() \
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
    munsReplacements1 = munsReplacements1.merge(states, on=['StateID'])
    munsReplacements2 = munsReplacements2.merge(states, on=['StateID'])
    groupsExport = groupsExport.merge(states, on=['StateID'])

    # stack ClassID in groups for export
    groupsExport = groupsExport.set_index(['StateID', 'ClassID']).unstack('ClassID')

    # sort municipalities
    munsSelected = munsSelected.sort_values(by=['StateID', 'Nm']).reset_index(drop=True)

    # convert shares to percent
    groupsExport['Sg'] *= 100.0

    # start index at 1, not 0
    munsSelected.index += 1
    munsReplacements1.index += 1
    munsReplacements2.index += 1

    # export to spreadsheet
    with pd.ExcelWriter(wd / 'output' / 'results.xlsx') as writer:
        groupsExport.to_excel(writer, sheet_name='Targets')
        munsSelected.to_excel(writer, sheet_name='Selected')
        munsReplacements1.to_excel(writer, sheet_name='Replacements 1')
        munsReplacements2.to_excel(writer, sheet_name='Replacements 2')
