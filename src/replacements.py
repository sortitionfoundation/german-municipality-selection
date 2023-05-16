import pandas as pd
from samplics import SelectMethod
from samplics.sampling import SampleSelection


def selectReplacements(muns: pd.DataFrame, stats: pd.DataFrame):
    # determine municipalities that can still be selected (those that have not been selected yet)
    munsAvailable = muns[~muns.index.isin(stats.query('Selected==1').index)]

    # create new stats table
    statsReplacements = stats.copy()
    statsReplacements['Selected'] = 0

    # selection method
    pps_sys_sel = SampleSelection(
        method=SelectMethod.pps_sys,
        strat=False,
        wr=False,
    )

    # select one municipality for every group
    for GroupID in munsAvailable['GroupID'].unique():
        thisMunsAvailable = munsAvailable.query(f"GroupID=={GroupID}")

        if thisMunsAvailable.empty:
            continue
        elif len(thisMunsAvailable) == 1:
            statsReplacements.loc[thisMunsAvailable.index, 'Selected'] = 1
            continue

        samp_size = 1
        pps_sample = pps_sys_sel.select(
            samp_unit=thisMunsAvailable.index,
            samp_size=samp_size,
            stratum=None,
            mos=thisMunsAvailable['Nm'].values,
            to_dataframe=True,
            sample_only=False,
        )

        statsReplacements.loc[pps_sample['_samp_unit'], 'Selected'] += pps_sample['_sample'].astype(int).values

    return statsReplacements
