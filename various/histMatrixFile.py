#!/usr/bin/env python3

import json
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
import re
import sys

import matplotlib
matplotlib.use('TkAgg')

def getParamsFromModulePath(modulePath):
    # "/cave_1/lmd_root_0/half_1/plane_0/module_3"
    regex = r"/cave_(\d+)/lmd_root_(\d+)/half_(\d+)/plane_(\d+)/module_(\d+)"
    p = re.compile(regex)
    m = p.match(modulePath)
    if m:
        half = int(m.group(3))
        plane = int(m.group(4))
        module = int(m.group(5))
        sector = (module) + (half)*5;
        return half, plane, module, sector

if __name__ == "__main__":
    
    if len(sys.argv) != 2:
        print('usage: ./histMatrixFile.py matrices.json')
        sys.exit(1)

    filename = str(sys.argv[1])
    with open(filename, 'r') as f:
        matrices = json.load(f)

    values = []

    for m in matrices:
        # _, plane, _ , _ = getParamsFromModulePath(m)
        # if plane == 3:
        values.append([matrices[m][3], matrices[m][7]])

    values = np.array(values)

    plt.switch_backend('TkAgg')

    # plot difference hit array
    fig = plt.figure(figsize=(16/2.54, 16/2.54))

    colors = ['xkcd:pale orange', 'xkcd:teal green', 'xkcd:dark sky blue']
    bucketLabels = ['dx', 'dy', 'rot z']
    kwargs = dict(histtype='stepfilled', alpha=0.75, bins=15, label=bucketLabels, color=colors[:2])

    axis = fig.add_subplot(1,1,1)
    axis.hist(values[...,:2]*1e4, **kwargs)  # this is only the z distance
    axis.set_title(f'{filename}')
    axis.set_xlabel('d [µm]')
    axis.set_ylabel('count')

    plt.rcParams["legend.loc"] = 'upper left'
    plt.legend()

    print(f'Entries total: {len(values)}')
    print(values)
    # fig.show()
    fig.savefig(f'tempHistogram.png')
    print(f'saved!')
    # input()