import pandas as pd
from samplics import SelectMethod
from samplics.sampling import SampleSelection


def chooseMuns(muns: pd.DataFrame, groups: pd.DataFrame, K: int = 1):
    choices = pd.DataFrame(index=muns.index, dtype=int)
    choices['Selected'] = 0

    # quotas = groups.loc[groups['Tg'] != 0, ['Cg', 'Tg']].min(axis=1).to_dict()
    #
    # pps_sys_sel = SampleSelection(
    #     method=SelectMethod.pps_sys,
    #     strat=True,
    #     wr=False,
    # )
    #
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

    # loop over non-zero groups
    for GroupID in groups.loc[groups['Tg']!=0.0, 'Tg'].index:
        # get all eligible municipalities
        thisMuns = muns.query(f"GroupID=={GroupID}")

        # get target and count for group
        Tg = groups.loc[GroupID, 'Tg']
        Cg = groups.loc[GroupID, 'Cg']

        if Tg < Cg:
            for k in range(K):
                pps_sys_sel = SampleSelection(
                    method=SelectMethod.pps_sys,
                    strat=False,
                    wr=False,
                )

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

                choices.loc[pps_sample['_samp_unit'], 'Selected'] += pps_sample['_sample'].astype(int).values
        else:
            choices.loc[thisMuns.index, 'Selected'] += K

    return choices
