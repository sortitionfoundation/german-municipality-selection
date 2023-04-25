from dateutil import parser

import json
from requests import request
import numpy as np


def setRandomSeed(seed: int):
    if seed is not None:
        np.random.seed(seed)
        return

    # set timestamp
    timeString = "25 Apr 2023 16:00:00.000 CEST"
    timeStamp = int(parser.parse(timeString).timestamp()) * 1000
    print(f"Timestamp: {timeStamp}")

    # request beacon at timestamp
    r = request(method="GET", url=f"https://beacon.nist.gov/beacon/2.0/pulse/time/{timeStamp}")

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
