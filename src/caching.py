import pandas as pd

from src.path import wd


# read dataframe from cache
def readCache(name: str):
    pathCache = wd / 'output' / f"cached{name}.pkl"
    return pd.read_pickle(pathCache) if pathCache.exists() else None


# write dataframe from cache
def writeCache(name: str, df: pd.DataFrame):
    pathCache = wd / 'output' / f"cached{name}.pkl"
    df.to_pickle(pathCache)
