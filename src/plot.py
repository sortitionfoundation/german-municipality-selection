import pandas as pd
import plotly.express as px

from src.path import wd


def plotLine(probs: pd.DataFrame, params: dict):
    # plot line without normalisation
    plot = px.line(probs, x='MunID', y='Prob', color='Iteration')
    plot.add_hline(params['Ltot'] / params['Ntot'])

    # write fig to files
    plot.write_image(wd / 'output' / 'plot.png')

