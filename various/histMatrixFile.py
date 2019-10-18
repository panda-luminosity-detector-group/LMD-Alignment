#!/usr/bin/env python3

import json
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
import sys

if __name__ == "__main__":
    
    if len(sys.argv) != 2:
        print('usage: ./histMatrixFile.py matrices.json')
        sys.exit(1)

    filename = str(sys.argv[1])
    with open(filename, 'r') as f:
        matrices = json.load(f)

    values = []

    for m in matrices:
        values.append([matrices[m][3], matrices[m][7]])

    values = np.array(values)

    # plot difference hit array
    fig = plt.figure(figsize=(16/2.54, 16/2.54))

    colors = ['xkcd:pale orange', 'xkcd:teal green', 'xkcd:dark sky blue']
    bucketLabels = ['dx', 'dy', 'rot z']
    kwargs = dict(histtype='stepfilled', alpha=0.75, bins=15, label=bucketLabels, color=colors[:2])

    histB = fig.add_subplot()
    histB.hist(values[...,:2]*1e4, **kwargs)  # this is only the z distance
    histB.set_title(f'{filename}')
    histB.set_xlabel('d [µm]')
    histB.set_ylabel('count')

    plt.rcParams["legend.loc"] = 'upper left'
    plt.legend()

    print(f'Entries total: {len(values)}')
    fig.show()
    input()