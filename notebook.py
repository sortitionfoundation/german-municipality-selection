# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Random selection of municipalities

# %% [markdown]
# ### Initialisation

# %% [markdown]
# Importing general-purpose libraries.

# %%
from pathlib import Path
from urllib.request import urlretrieve
from requests import request
from dateutil import parser
import json

import numpy as np
import pandas as pd
from voting import apportionment
from samplics import SelectMethod
from samplics.sampling import SampleSelection
from samplics.utils import CertaintyError
import plotly.express as px
import plotly.graph_objects as go

from IPython.display import display, HTML, Markdown

# %% [markdown]
# Plot pandas dataframes with plotly by default.

# %%
pd.options.plotting.backend = "plotly"

# %% [markdown]
# Defining input and output directories.

# %%
# base path should be set to the main repo directory but can also be any other working directory
base_path = Path('.')

# input, cache, and output directories should be subdirectories
input_path = base_path / 'input'
cache_path = base_path / 'cache'
output_path = base_path / 'output'

# create subdirectories if not yet present
for p in [input_path, cache_path, output_path]:
    p.mkdir(parents=True, exist_ok=True)

# %% [markdown]
# ### Downloading data file

# %% [markdown]
# Set file name of list of municipalities. This file can be downloaded from the [DESTATIS webpage](https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/Administrativ/Archiv/GVAuszugQ/AuszugGV1QAktuell.html). If it is not present, the code will attempt to download it automatically.

# %%
input_file_path = input_path / 'AuszugGV1QAktuell.xlsx'
input_file_url = 'https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/Administrativ/Archiv/GVAuszugQ/AuszugGV1QAktuell.xlsx?__blob=publicationFile'

if not (input_file_path.exists() and input_file_path.is_file()):
    urlretrieve(input_file_url, input_file_path)


# %% [markdown]
# ### Reading and preprocessing data

# %% [markdown]
# Before reading in the data, we define the size classes.

# %%
def define_classes():
    # define classes
    classes = pd.DataFrame.from_records([
        {'Class-Name': 'Small', 'Threshold': 20000,},
        {'Class-Name': 'Medium', 'Threshold': 100000,},
        {'Class-Name': 'Large', 'Threshold': np.inf,},
    ])
    
    # insure that the threshold is monotonic increasing
    assert classes['Threshold'].is_monotonic_increasing
    
    # update index
    classes.index += 1
    classes.rename_axis('Class-ID', inplace=True)
    
    # add description
    classes['Class-Desc'] = classes \
        .assign(Lower=lambda df: df['Threshold'].shift()) \
        .replace(np.inf, np.nan) \
        .agg(
            lambda row: f"{row['Class-Name']} (" 
                      + (f"≥{row['Lower']}" if not pd.isnull(row['Lower']) else '')
                      + ('; ' if row.notnull().all() else '')
                      + (f"<{row['Threshold']}" if not pd.isnull(row['Threshold']) else '')
                      + ')',
            axis=1,
        )

    return classes


# %% [markdown]
# Municipalities (Gemeinden) and states (Bundeslaender) will be read from input data file.

# %%
# read states and muns from XLSX input file
def read_from_input(classes: pd.DataFrame):
    # list of columns to read from file
    columns = {
        'A': {'name': 'Satzart', 'dtype': 'str'},
        'C': {'name': 'State-ID', 'dtype': 'str'},
        'D': {'name': 'Mun-ID-1', 'dtype': 'str'},
        'E': {'name': 'Mun-ID-2', 'dtype': 'str'},
        'F': {'name': 'Mun-ID-3', 'dtype': 'str'},
        'G': {'name': 'Mun-ID-4', 'dtype': 'str'},
        'H': {'name': 'Name', 'dtype': 'str'},
        'J': {'name': 'Nm', 'dtype': 'float64'},
        'O': {'name': 'LONG', 'dtype': 'float64'},
        'P': {'name': 'LAT', 'dtype': 'float64'},
        'T': {'name': 'Urbanisation', 'dtype': 'str'},
    }

    # read excel to raw dataframe
    raw_dataframe = pd.read_excel(
        input_file_path,
        sheet_name=1,
        index_col=None,
        usecols=','.join(list(columns.keys())),
        names=[col_specs['name'] for col_specs in columns.values()],
        dtype={col_specs['name']: col_specs['dtype'] for col_specs in columns.values()},
        decimal=',',
        skiprows=5,
    )
    
    # obtain states from raw dataframe
    states = raw_dataframe \
        .query("Satzart=='10'") \
        .rename(columns={'Name': 'State-Name'}) \
        .astype({'State-ID': 'int64'}) \
        .filter(['State-ID', 'State-Name']) \
        .set_index('State-ID')

    # obtain municipalities from raw dataframe
    muns = raw_dataframe \
        .query("Satzart=='60'") \
        .rename(columns={'Name': 'Mun-Name'}) \
        .astype({'State-ID': 'int64'}) \
        .assign(**{
            'Mun-ID': lambda df: df.agg("{0[State-ID]}{0[Mun-ID-1]}{0[Mun-ID-2]}{0[Mun-ID-3]}{0[Mun-ID-4]}".format, axis=1),
            'Mun-Shortname': lambda df: df['Mun-Name'].str.split(',').str[0],
        }) \
        .filter(['Mun-ID', 'Mun-Name', 'Mun-Shortname', 'State-ID', 'Nm', 'Urbanisation', 'LONG', 'LAT']) \
        .set_index('Mun-ID')

    # drop municipalities with zero population
    muns = muns.loc[muns['Nm'] > 0]

    # add size classes
    muns['Class-ID'] = muns['Nm'].agg(lambda Nm: (Nm > classes['Threshold']).idxmin())

    # finally, we combine the state and class IDs into groups and compute total pop and share of pop in groups
    groups = muns \
        .groupby(['State-ID', 'Class-ID']) \
        .agg({'Nm': 'sum'}) \
        .rename(columns={'Nm': 'Ng'}) \
        .assign(Sg=lambda x: x['Ng'] / x['Ng'].sum()) \
        .unstack('Class-ID') \
        .fillna(0) \
        .stack('Class-ID')

    # add group ID and set as index
    groups['Group-ID'] = [j + 3*(i-1) for i, j in groups.index.values]
    groups = groups.reset_index().set_index('Group-ID')

    # add group ID to muns
    muns = muns \
        .reset_index() \
        .merge(groups.filter(['State-ID', 'Class-ID']).reset_index(), on=['State-ID', 'Class-ID']) \
        .set_index('Mun-ID')

    # assign count of muns in groups
    groups['Cg'] = 0
    groups_count = muns.groupby('Group-ID')['Group-ID'].count()
    groups.loc[groups_count.index, 'Cg'] = groups_count.values

    # sort muns by population
    muns = muns.sort_values(by=['Nm'], ascending=False)

    return states, muns, groups


# %% [markdown]
# To speed up execution, the processed municipality data will be stored in cached files. Set `allow_caching` to `False` in order to force reprocessing.

# %%
allow_caching: bool = False


# %%
# read dataframe from cache
def read_cache(name: str):
    fpath = cache_path / f"cached_{name}.pkl"
    return pd.read_pickle(fpath) if fpath.exists() else None

# write dataframe from cache
def write_cache(name: str, df: pd.DataFrame):
    fpath = cache_path / f"cached_{name}.pkl"
    df.to_pickle(fpath)


# %%
# read from cache if allowed
classes, states, muns, groups = (
    (read_cache('classes'), read_cache('states'), read_cache('muns'), read_cache('groups'))
    if allow_caching else
    (None, None, None, None)
)

# if either of the two is None, caching was either disabled or the file doesn't exist yet, so read from input file and write cache files
if any(df is None for df in (classes, states, muns, groups)):
    classes = define_classes()
    states, muns, groups = read_from_input(classes)
    write_cache('classes', classes)
    write_cache('muns', muns)
    write_cache('states', states)
    write_cache('groups', groups)

# %%
display(classes)
display(states)
display(muns.sample(10))
display(groups \
    .reset_index() \
    .set_index(['State-ID', 'Class-ID']) \
    .assign(
        Sg=lambda df: df['Sg'] * 100,
        Ng=lambda df: df['Ng'],
    ) \
    .round(2) \
    .unstack('Class-ID'))

# %% [markdown]
# ### Analyse data

# %% [markdown]
# Before we proceed, let's first take a closer look at the data.

# %%
fig = go.Figure(go.Bar(
    x=muns['Nm'].cumsum()-muns['Nm'],
    y=muns['Nm'],
    width=muns['Nm'],
    offset=0.0,
    text=muns.where(lambda d: d['Nm'] > 0.5E+6)['Mun-Shortname'],
    customdata=muns['Mun-Name'],
    hovertemplate='<br>'.join([
        '<b>%{customdata}</b>',
        'Pop: %{y}',
        '<extra></extra>',
    ]),
))
fig.update_traces(
    textfont_size=8,
    textangle=270,
    textposition='outside',
    cliponaxis=True,
)
fig.update_layout(
    xaxis_range=[0, 40E+6],
    yaxis_range=[0, 5E+6],
    uniformtext_minsize=5,
    uniformtext_mode='show',
)

# add horizontal lines to illustrate classes
for class_id, class_row in classes.iterrows():
    x0 = muns.iloc[:(muns['Nm'] < class_row['Threshold']).argmax()]['Nm'].sum()
    fig.add_vline(x=x0)
    fig.add_annotation(x=x0, xanchor='left', y=4.5E+6, text=class_row['Class-Desc'], showarrow=False)

display(fig)
fig.write_image(output_path / 'plot1.png')

# %%
fig = go.Figure(go.Scatter(
    x=muns['Nm'].cumsum(),
    y=muns['Nm'],
    customdata=muns['Mun-Name'],
    mode='markers+lines',
    hovertemplate='<br>'.join([
        '<b>%{customdata}</b>',
        'Pop: %{y}',
        '<extra></extra>',
    ]),
))

display(fig)
fig.write_image(output_path / 'plot2.png')

# %% [markdown]
# ### Defining group targets

# %% [markdown]
# Next, we assign targets to the groups. First, we define some general parameters.

# %%
# initialise key parameters
params = {
    'n*_init': 80,  # initial target for number of municipalities to select
    'L*': 20000,  # total number of letters to send out
    'N*': groups['Ng'].sum(),  # total population in Germany
}

# %% [markdown]
# Then we assign targets to the groups via StLague.

# %%
# assign targets via StLague
groups['ng_init'] = apportionment.sainte_lague(groups['Ng'].values, params['n*_init'])
groups['ng'] = groups['ng_init']

# ng should at least be one for any group with non-zero population
cond = (groups['ng'] == 0) & (groups['Ng'] > 0)
groups.loc[cond, 'ng'] = 1

# Tg should not be greater than Cg
cond = groups['ng'] > groups['Cg']
groups.loc[cond, 'ng'] = groups.loc[cond, 'Cg']

# set total target number as new parameter Ttot
params['n*'] = groups['ng'].sum()

# %% [markdown]
# Display groups in user-friendly format and dump to Excel spreadsheet file.

# %%
d = groups \
    .reset_index() \
    .join(states, on='State-ID') \
    .join(classes, on='Class-ID') \
    .set_index(['State-ID', 'State-Name', 'Class-ID', 'Class-Desc']) \
    .assign(
        Sg=lambda df: df['Sg'] * 100,
    ) \
    .round(2) \
    .unstack(['Class-ID', 'Class-Desc'])

display(d)
d.to_excel(output_path / 'municipality_selection_targets.xlsx')

# %% [markdown]
# Analyse for which groups the initial targets were updated.

# %%
groups \
    .loc[groups['ng'] != groups['ng_init']] \
    .reset_index() \
    .join(states, on='State-ID') \
    .join(classes, on='Class-ID') \
    .loc[:, ['State-Name', 'Class-Desc', 'ng', 'ng_init']] \
    .assign(ng_diff=lambda x: x['ng'] - x['ng_init'])

# %% [markdown]
# ### Set random seed

# %% [markdown]
# The random seed will be set via the randomness beacon.

# %%
# set timestamp
timestr = '30 Apr 2024 08:00:00.000 CEST'
timestamp = int(parser.parse(timestr).timestamp()) * 1000

# request beacon at timestamp
r = request(method="GET", url=f"https://beacon.nist.gov/beacon/2.0/pulse/time/{timestamp}")

# ensure that status code is not 404, otherwise try again with updated timestr
if r.status_code == 404:
    timestr = timestamp = 'LAST'
    r = request(method="GET", url=f"https://beacon.nist.gov/beacon/2.0/pulse/last")

# load json data
json_data = json.loads(r.text)

# get output value in hex format
output_value = json_data['pulse']['outputValue']

# convert to list of ints
l = 8
chunks = [output_value[y-l:y] for y in range(l, len(output_value)+l, l)]
ints = [int(c, 16) for c in chunks]

# random seed
np.random.seed(ints)

# print outputs
display(Markdown(f"""
**Time string:** {timestr}

**Timestamp**: {timestamp}

**Beacon output**: {output_value}

**Ints for seeding**: {ints}
"""))

# %% [markdown]
# ### Random selection of municipalities

# %% [markdown]
# We are using PPS-SYS sampling from the samplics package (probability-proportional-to-size) w/o replacement and w/o stratification. Stratification is done manually by us at the moment.

# %%
# selection method
pps_sys_sel = SampleSelection(
    method=SelectMethod.pps_sys,
    strat=False,
    wr=False,
)

# %% [markdown]
# We will introduce a small correction such that we won't invite more than 10% of population if small municipalities get selected.

# %%
alpha = 0.1
Nmin = params['L*'] / params['n*'] / alpha
muns['Mm'] = muns['Nm'] + Nmin / (1 + (muns['Nm'] / Nmin))


# %% [markdown]
# Define function for running selection $K$ times. This will later allows us to repeat the selection multiple times and experimentally tests whether the chances of receiving a letter converge to $\bar q$.

# %%
def run_selection(K: int = 1):
    # initialise results dataframes
    results = muns.copy()
    results.insert(0, 'Selected', 0)
    results.insert(1, 'Certainty', False)
    
    # loop over groups (with non-zero muns in them)
    for group_id, group_specs in groups.loc[groups['ng'] != 0.0].iterrows():
        # get all eligible municipalities
        this_muns = muns.loc[muns['Group-ID'] == group_id]
    
        # get target and count for group
        this_ng = int(group_specs['ng'])
        this_Cg = int(group_specs['Cg'])
    
        # print for debug
        #print(f"{states.loc[group_specs['State-ID'], 'State-Name']}, {classes.loc[group_specs['Class-ID'], 'Class-Desc']}")
    
        # only select if there are more muns in a group than we want to pick
        # (eg skip Berlin or Hamburg, as they are the only muns in the respective states)
        if this_ng == this_Cg:
            results.loc[this_muns.index, 'Certainty'] = True
        elif this_ng > this_Cg:
            raise Exception(
                f"Cannot select more municipalities than exist in a group. \n\n"
                f"{group_specs.reset_index()}\n\n"
                f"{states.loc[group_specs['State-ID']]}\n\n"
                f"{classes.loc[group_specs['Class-ID']]}"
            )
        else:
            # remove muns with certainty
            this_muns_noncertainty = this_muns
            this_muns_certainty = None
            this_ng_noncertainty = this_ng
    
            while True:
                cond_muns_certainty = (this_muns_noncertainty['Mm'] / this_muns_noncertainty['Mm'].sum() * this_ng_noncertainty) > 1
                if not cond_muns_certainty.any():
                    break
                this_muns_certainty = pd.concat([this_muns_certainty, this_muns_noncertainty.loc[cond_muns_certainty]])
                this_muns_noncertainty = this_muns_noncertainty.loc[~cond_muns_certainty]
                this_ng_noncertainty -= int(cond_muns_certainty.sum())
    
            # for certainty units update results
            if this_muns_certainty is not None:
                results.loc[this_muns_certainty.index, 'Certainty'] = True
    
            # for non-certainty muns run sampling K times (so that we can experimentally test the results)
            for k in range(K):
                # run pps selection algorithm using samplics package
                try:
                    pps_sample = pps_sys_sel.select(
                        samp_unit=this_muns_noncertainty.index.tolist(),
                        samp_size=this_ng_noncertainty,
                        stratum=None,
                        mos=this_muns_noncertainty['Mm'].values,
                        to_dataframe=True,
                        sample_only=False,
                    )
                except CertaintyError:
                    raise Exception(
                        f"A group contains certainty muns.\n\n"
                        f"{group_specs}\n\n"
                        f"{states.loc[group_specs['State-ID']]}\n\n"
                        f"{classes.loc[group_specs['Class-ID']]}"
                    )
    
                # add number of times selected and correction factors for this group
                results.loc[pps_sample['_samp_unit'], 'Selected'] += pps_sample['_sample'].astype(int).values
    
    # certainty muns are selected every time
    results.loc[results['Certainty'], 'Selected'] = K

    return results


# %% [markdown]
# Next, we define a function for computing the share of letters to send for each municipality (ie apportionment factors for deviation from $\bar L = L^*/n^*$). Then we calculate the actual final number of letters $L_m$ to send out.

# %%
def calc_letters(results: pd.DataFrame, check_sum: bool = True):
    # certainty muns
    Nm = results.loc[results['Certainty'], 'Nm']
    results.loc[results['Certainty'], 'AFm'] = Nm / params['N*'] * params['n*']

    # non-certainty muns
    Nm = results.loc[~results['Certainty'], 'Nm']
    Mm = results.loc[~results['Certainty'], 'Mm']
    Mg = results.loc[~results['Certainty']].groupby('Group-ID')['Mm'].transform(sum)
    ng = results.loc[~results['Certainty']].join(groups[['ng']], on='Group-ID')['ng'] - results.groupby('Group-ID')['Certainty'].transform(sum).loc[~results['Certainty']]
    results.loc[~results['Certainty'], 'AFm'] = Nm / params['N*'] * params['n*'] / ng * Mg / Mm

    # calculate final number of letters
    results['Lm'] = params['L*'] / params['n*'] * results['AFm']
    results.loc[results['Selected'] > 0, 'Lm_rounded'] = apportionment.sainte_lague(results.loc[results['Selected'] > 0, 'AFm'], round(results.loc[r['Selected'] > 0, 'Lm'].sum()))

    return results


# %% [markdown]
# We now run the selection once and then calculate the number of letters.

# %%
# run selection once
r = run_selection()

# calculate number of letters
r = calc_letters(r)

# display selected muns and number of letters
r_sel = r.loc[r['Selected'] > 0]
display(r_sel['Lm'].sum())
display(r_sel['Lm_rounded'].sum())
display(r_sel[['Mun-Name', 'Nm', 'Lm', 'Lm_rounded']])

# %%
d = r \
    .loc[r['Selected'] > 0] \
    .drop(columns=['Selected', 'Certainty']) \
    .join(states, on='State-ID') \
    .join(classes, on='Class-ID') \
    .sort_values(by=['State-ID', 'Class-ID'])

display(d['Lm_rounded'].sum())
display(d)
d.to_excel(output_path / 'municipality_selection_results.xlsx')


# %% [markdown]
# Finally, we select replacement municipalities for each group.

# %%
def select_replacements(results: pd.DataFrame, num_repl: int = 5):
    replacements = None
    
    # loop over groups (with non-zero muns in them)
    for group_id, group_specs in groups.loc[groups['ng'] != 0.0].iterrows():
        # get all eligible municipalities
        this_muns = muns.loc[(muns['Group-ID'] == group_id) & (results['Selected'] == 0)]
        #print(f"{states.loc[group_specs['State-ID'], 'State-Name']}, {classes.loc[group_specs['Class-ID'], 'Class-Desc']}")
        #display(this_muns)
    
        # get target and count for group
        this_ng = num_repl
        this_Cg = len(this_muns)
    
        # only perform PPS if there are more muns in the groups left than replacements we plan to select
        if this_ng >= this_Cg:
            new_replacements = this_muns
        else:
            # remove muns with certainty
            this_muns_noncertainty = this_muns
            this_muns_certainty = None
            this_ng_noncertainty = this_ng
    
            while True:
                cond_muns_certainty = (this_muns_noncertainty['Mm'] / this_muns_noncertainty['Mm'].sum() * this_ng_noncertainty) > 1
                if not cond_muns_certainty.any():
                    break
                this_muns_certainty = pd.concat([this_muns_certainty, this_muns_noncertainty.loc[cond_muns_certainty]])
                this_muns_noncertainty = this_muns_noncertainty.loc[~cond_muns_certainty]
                this_ng_noncertainty -= int(cond_muns_certainty.sum())
    
            # for certainty units update results
            new_replacements = this_muns_certainty if this_muns_certainty is not None else None

            # run pps selection algorithm using samplics package
            try:
                pps_sample = pps_sys_sel.select(
                    samp_unit=this_muns_noncertainty.index.tolist(),
                    samp_size=this_ng_noncertainty,
                    stratum=None,
                    mos=this_muns_noncertainty['Mm'].values,
                    to_dataframe=True,
                    sample_only=False,
                )
            except CertaintyError:
                raise Exception(
                    f"A group contains certainty muns.\n\n"
                    f"{group_specs}\n\n"
                    f"{states.loc[group_specs['State-ID']]}\n\n"
                    f"{classes.loc[group_specs['Class-ID']]}"
                )

            new_replacements = pd.concat([
                new_replacements,
                this_muns.loc[pps_sample.loc[pps_sample['_sample'] != 0, '_samp_unit']],
            ])

        replacements = pd.concat([replacements, new_replacements])

    replacements['Lm'] = results.loc[replacements.index, 'Lm']
    replacements['Lm_rounded'] = replacements['Lm'].round()
    
    return replacements


# %%
replacements = select_replacements(r)

# %%
d = replacements \
    .join(states, on='State-ID') \
    .join(classes, on='Class-ID')

display(d)
d.to_excel(output_path / 'municipality_selection_replacements.xlsx')

# %% [markdown]
# ### Checking probabilities experimentally

# %% [markdown]
# We now select muns $K > 1$ times in order to be able to visualise the convergence of the probability.

# %%
# Ks = [100, 1000, 2000]  # uncomment for proper statistics
Ks = [10, 20, 30]

# %%
K_max_batch = 50  # max number of iterations to do in one batch


def calc_stats(Ks: list[int]):
    # check input parameters
    if any(Ks[i] <= Ks[i-1] for i in range(1, len(Ks))):
        raise Exception(f"The list of iterations has to be strictly increasing.")

    # loop over iterations
    stats = pd.DataFrame(index=muns.index)
    K_prev = 0
    for K in Ks:
        print(K)
        
        # initialise column for this iteration
        stats[K] = stats[K_prev] if K_prev else 0
        
        # in this iteration run K-K_prev times
        K_this = K - K_prev
        while K_this > 0:
            K_batch = min(K_this, K_max_batch)
            print(f"-- {K_batch}")
            results = run_selection(K_batch)
            K_this -= K_batch

            # add number of times chosen to histogram
            stats[K] += results['Selected']

        # add K to total number of times chosen
        K_prev = K

    return stats


# %%
stats = calc_stats(Ks)
display(stats)

# %% [markdown]
# Let's calculate and plot the probability of receiving a letter for every citizen in each municipality. This is given by $q_m = \pi_m \times \frac{L_m}{N_m} = \frac{k_m}{K} \times \frac{L_m}{N_m}$, where $k_m$ is the number of times a municipality was selected and $K$ is the number of iterations.

# %%
probs = (stats.apply(lambda col: col * r['Lm'] / r['Nm'])) \
    .melt(ignore_index=False, var_name='Iterations', value_name='Prob') \
    .assign(Prob=lambda df: df['Prob'] / df['Iterations'])
display(probs)

# plot line
fig = px.line(probs.reset_index(), x='Mun-ID', y='Prob', color='Iterations')
fig.add_hline(params['L*'] / params['N*'])
fig.update_layout(xaxis_range=[0, 1000], yaxis_range=[0, 0.0005])

display(fig)
fig.write_image(output_path / 'plot3.png')

# %% [markdown]
# Let's plot the measure of size ($M_m$) along with the population size ($N_m$) such that we can compare the deviation.

# %%
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=muns['Nm'].cumsum(),
    y=muns['Nm'],
    customdata=muns['Mun-Name'],
    name='Real Population',
    mode='markers+lines',
    hovertemplate='<br>'.join([
        '<b>%{customdata}</b>',
        'Pop: %{y}',
        '<extra></extra>',
    ]),
))
fig.add_trace(go.Scatter(
    x=muns['Nm'].cumsum(),
    y=muns['Mm'],
    customdata=muns['Mun-Name'],
    name='Measure of Size',
    mode='markers+lines',
    hovertemplate='<br>'.join([
        '<b>%{customdata}</b>',
        'Pop: %{y}',
        '<extra></extra>',
    ]),
))

fig.update_layout(
    xaxis_range=[60000000.0, 84360000.0],
    yaxis_range=[0.0, 30000.0],
)

display(fig)
fig.write_image(output_path / 'plot4.png')

# %% [markdown]
# Let us also plot the number of letters to send in a municipality.

# %%
fig = px.line(r.assign(Nm_cum=lambda df: df['Nm'].cumsum()), x='Nm_cum', y='Lm')
fig.add_hline(params['L*'] / params['n*'])

fig.update_layout(
    xaxis_range=[0, 84360000.0],
    yaxis_range=[0.0, 800.0],
)

display(fig)
fig.write_image(output_path / 'plot5.png')
