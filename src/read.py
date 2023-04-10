import pandas as pd

from src.caching import readCache, writeCache
from src.path import wd


# path to raw XLSX input file
patchRaw = wd / 'input' / '31122021_Auszug_GV.xlsx'


# definition of size classes
sizeClasses = {
    1: {
        'name': 'Small (<20.000)',
        'cond': lambda muns: muns['Nm'] < 20000,
    },
    2: {
        'name': 'Medium (≥20.000; <100.000)',
        'cond': lambda muns: (muns['Nm'] >= 20000) & (muns['Nm'] < 100000),
    },
    3: {
        'name': 'Large (≥100.000)',
        'cond': lambda muns: muns['Nm'] >= 100000,
    },
}


# read all data
def readData(allow_caching: bool = True):
    states = (readCache('States') if allow_caching else None)
    muns = (readCache('Muns') if allow_caching else None)

    if states is None:
        states = __readStates()
        writeCache('States', states)

    if muns is None:
        muns = __readMuns()
        writeCache('Muns', muns)

    return states, muns


# read states from XLSX input file
def __readStates():
    states = pd.read_excel(
        patchRaw,
        sheet_name='Inhalt',
        index_col=None,
        usecols='A',
        names=['Combined'],
        skiprows=17,
        nrows=16,
    )

    # split column into IDs and names of states
    states[['StateID', 'StateName']] = states['Combined'].str.split(expand=True)

    # make ID an integer column, make it the index, and drop obsolete column Combined
    states = states \
        .astype({'StateID': int}) \
        .set_index('StateID') \
        .drop(columns=['Combined'])

    return states


# read municipalities from XLSX file
def __readMuns():
    muns = pd.read_excel(
        patchRaw,
        sheet_name='Onlineprodukt_Gemeinden',
        index_col=None,
        usecols='A,C,H,J,O,P,T',
        names=['Satzart', 'StateID', 'MunName', 'Nm', 'LONG', 'LAT', 'Urbanisation'],
        decimal=',',
    )

    # drop entries that are not municipalities
    muns = muns.query("Satzart=='60'")

    # reorder columns and drop Satzart
    muns = muns[['MunName', 'StateID', 'Nm', 'Urbanisation', 'LONG', 'LAT']]

    # update type of state column
    muns = muns.astype({'StateID': int, 'Nm': int})

    # drop municipalities with zero population
    muns = muns.query(f"Nm!=0")

    # sort by population and then by state
    muns = muns.sort_values(by=['Nm'], ascending=False).reset_index(drop=True)

    # add size classes
    muns.insert(3, 'ClassID', 0)
    muns = muns.astype({'ClassID': int})
    for ClassID, ClassSpecs in sizeClasses.items():
        muns.loc[ClassSpecs['cond'](muns), 'ClassID'] = ClassID

    # check all municiaplities were assigned a category
    assert (muns.query("ClassID==0").empty)

    # assign a name to the index
    muns.index = muns.index.set_names(['MunID'])

    return muns