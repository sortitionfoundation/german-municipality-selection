import pandas as pd

from src.path import pwd


def loadMuns(allow_caching: bool = True):
    # load cached if it exists
    pathCache = pwd / 'cached.pkl'
    if allow_caching and pathCache.exists():
        return pd.read_pickle(pathCache)

    # read XSL file
    patchRaw = pwd / 'input' / '31122021_Auszug_GV.xlsx'
    municipalities = pd.read_excel(
        patchRaw.resolve(),
        sheet_name='Onlineprodukt_Gemeinden',
        index_col = None,
        usecols='A,C,H,J,O,P,T',
        names=['Satzart', 'State', 'MunName', 'Population', 'Längengrad', 'Breitengrad', 'Urbanisierung'],
    )

    # drop entries that are not municipalities
    municipalities = municipalities.query("Satzart=='60'")

    # reorder columns and drop Satzart
    municipalities = municipalities[['MunName', 'State', 'Population', 'Urbanisierung', 'Längengrad', 'Breitengrad']]

    # update type of state column
    municipalities = municipalities.astype({'State': int})

    # sort bei GEM
    municipalities = municipalities.sort_values(by=['State', 'Population']).reset_index(drop=True)

    # add size categories
    municipalities.insert(3, 'Größenklasse', 0)
    municipalities = municipalities.astype({'Größenklasse': int})
    categories = {
        1: municipalities['Population'] < 20000,
        2: (municipalities['Population'] >= 20000) & (municipalities['Population'] < 100000),
        3: municipalities['Population'] >= 100000,
    }
    for gk, cond in categories.items():
        municipalities.loc[cond, 'Größenklasse'] = gk

    # check all municiaplities were assigned a category
    assert(municipalities.query("Größenklasse==0").empty)

    # assign a name to the index
    municipalities.index = municipalities.index.set_names(['MunID'])

    # dump cache file
    municipalities.to_pickle(pathCache)

    return municipalities
