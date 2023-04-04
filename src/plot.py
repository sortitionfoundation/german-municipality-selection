import pandas as pd
import plotly.express as px

from src.path import pwd


def plotLine(probabilities: pd.DataFrame, L: int, popTot: int):
    # plot line without normalisation
    plot = px.line(probabilities.reset_index(), x='MunID', y='FinalProb', color='Round')
    plot.add_hline(L / popTot)

    # write figs to files
    plot.write_image(pwd / 'output' / 'plot.png')

    # plot line without normalisation
    plot = px.line(probabilities.reset_index(), x='MunID', y='FinalProbWOCorr', color='Round')
    plot.add_hline(L / popTot)

    # write figs to files
    plot.write_image(pwd / 'output' / 'plotWOCorr.png')


