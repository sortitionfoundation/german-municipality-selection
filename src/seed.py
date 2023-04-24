import json
from requests import request
import numpy as np


def setRandomSeed(seed: int):
    if seed is not None:
        np.random.seed(seed)

    # set timestamp
    t = 1682362800000

    # request beacon at timestamp
    r = request(method="GET", url=f"https://beacon.nist.gov/beacon/2.0/pulse/time/{t}")

    # load json data
    jsonData = json.loads(r.text)

    # get output value in hex format
    outputValueHex = jsonData['pulse']['outputValue']

    # convert to list of ints
    l = 8
    chunks = [outputValueHex[y-l:y] for y in range(l, len(outputValueHex)+l, l)]
    ints = [int(c, 16) for c in chunks]

    # random seed
    np.random.seed(ints)
