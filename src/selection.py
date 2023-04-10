import pandas as pd
from samplics import SelectMethod
from samplics.sampling import SampleSelection


def selectMuns(muns: pd.DataFrame, groups: pd.DataFrame, params: dict, K: int = 1):
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
            for k in range(K):
                # run pps selection algorithm
                pps_sample = pps_sys_sel.select(
                    samp_unit=thisMuns.index,
                    samp_size=int(Tg),
                    stratum=None,
                    mos=thisMuns['Nm'].values,
                    to_dataframe=True,
                    sample_only=False,
                )

                # choose municipalities randomly weighted by population
                # choice = pd.Series(pps.ppss(robjects.IntVector(thisMuns['Nm']), Tg)).astype(int) - 1
                # choiceIndices = thisMuns.iloc[choice.values.tolist()].index.to_list()

                # add number of times selected
                stats.loc[pps_sample['_samp_unit'], 'Selected'] += pps_sample['_sample'].astype(int).values

                # add to certainty
                stats.loc[pps_sample.query('_probs>1.0')['_samp_unit'], 'Certainty'] = True
        else:
            stats.loc[thisMuns.index, 'Certainty'] = True

    stats.loc[stats['Certainty'], 'Selected'] = K

    # calculate correction factors for all groups
    corrFactorsGroups = pd.DataFrame(index=groups.index, dtype=float)
    corrFactorsGroups['CFg'] = params['Ttot'] / groups['Tg'] * groups['Ng'] / params['Ntot']

    # assign correction factors for non-certainty
    stats = stats \
        .reset_index() \
        .merge(corrFactorsGroups, on='GroupID') \
        .sort_values(by='MunID') \
        .set_index('MunID') \
        .rename(columns={'CFg': 'CFm'})

    # assign correction factors for certainty
    stats.loc[stats['Certainty'], 'CFm'] = muns['Nm'] / params['Ntot'] * params['Ttot']

    return stats
