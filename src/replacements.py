import pandas as pd
from samplics import SelectMethod
from samplics.sampling import SampleSelection


def selectReplacements(muns: pd.DataFrame):
    # initialise stats dataframe
    stats = muns[['GroupID']].copy()
    stats['Selected'] = 0
    stats['Certainty'] = False

    # selection method
    pps_sys_sel = SampleSelection(
        method=SelectMethod.pps_sys,
        strat=False,
        wr=False,
    )

    # select one municipality for every group
    for GroupID in muns['GroupID'].unique():
        thisMunsAvailable = muns.query(f"GroupID=={GroupID}")

        if thisMunsAvailable.empty:
            continue
        elif len(thisMunsAvailable) == 1:
            stats.loc[thisMunsAvailable.index, 'Selected'] = 1
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

        stats.loc[pps_sample['_samp_unit'], 'Selected'] += pps_sample['_sample'].astype(int).values

    return stats
