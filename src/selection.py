import pandas as pd
from samplics import SelectMethod
from samplics.sampling import SampleSelection


def selectMuns(muns: pd.DataFrame, groups: pd.DataFrame, params: dict, K: int = 1):
    # initialise stats dataframe
    stats = muns[['GroupID']].copy()
    stats['Selected'] = 0
    stats['Certainty'] = False

    # create dataframe for correction factors for all groups
    corrFactorsGroups = pd.DataFrame(index=groups.index, dtype=float)

    # selection method
    pps_sys_sel = SampleSelection(
        method=SelectMethod.pps_sys,
        strat=False,
        wr=False,
    )

    # quotas = groups.loc[groups['Tg'] != 0, ['Cg', 'Tg']].min(axis=1).to_dict()
    # pps_sample = pps_sys_sel.select(
    #     muns.index,
    #     quotas,
    #     muns['GroupID'],
    #     muns['Nm'],
    #     to_dataframe=True,
    #     sample_only=False,
    # )
    #
    # print(pps_sample)

    # loop over groups (with non-zero muns in them)
    for GroupID in groups.loc[groups['Tg']!=0.0, 'Tg'].index:
        # get all eligible municipalities
        thisMuns = muns.query(f"GroupID=={GroupID}")

        # get target and count for group
        Tg = groups.loc[GroupID, 'Tg']
        Cg = groups.loc[GroupID, 'Cg']

        if Tg < Cg:
            thisMunsSampling = thisMuns
            thisMunsCertainty = None

            for k in range(K):
                # run pps selection algorithm
                while True:
                    samp_size = int(Tg) if thisMunsCertainty is None else int(Tg) - len(thisMunsCertainty)
                    pps_sample = pps_sys_sel.select(
                        samp_unit=thisMunsSampling.index,
                        samp_size=samp_size,
                        stratum=None,
                        mos=thisMunsSampling['Nm'].values,
                        to_dataframe=True,
                        sample_only=False,
                    )

                    thisMunsCertaintyNew = thisMunsSampling.loc[pps_sample.query('_probs>=1.0')['_samp_unit']]

                    if thisMunsCertaintyNew.empty:
                        break

                    thisMunsCertainty = thisMunsCertaintyNew if thisMunsCertainty is None else pd.concat([thisMunsCertainty, thisMunsCertaintyNew])
                    thisMunsSampling = thisMunsSampling[~thisMunsSampling.index.isin(thisMunsCertainty.index)]

                # add number of times selected and correction factors for this group
                stats.loc[pps_sample['_samp_unit'], 'Selected'] += pps_sample['_sample'].astype(int).values
                corrFactorsGroups.loc[GroupID, 'CFg'] = thisMunsSampling['Nm'].sum() / params['Ntot'] / samp_size * params['Ttot']

            # add certainty information
            if thisMunsCertainty is not None:
                stats.loc[thisMunsCertainty.index, 'Certainty'] = True
        else:
            stats.loc[thisMuns.index, 'Certainty'] = True

    # assign correction factors from groups to muns
    stats = stats \
        .reset_index() \
        .merge(corrFactorsGroups, on='GroupID') \
        .sort_values(by='MunID') \
        .set_index('MunID') \
        .rename(columns={'CFg': 'CFm'})

    # assign correction factors and number of samplings for certainty muns
    stats.loc[stats['Certainty'], 'Selected'] = K
    stats.loc[stats['Certainty'], 'CFm'] = muns['Nm'] / params['Ntot'] * params['Ttot']

    return stats
