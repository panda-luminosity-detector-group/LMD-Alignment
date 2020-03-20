#!/usr/bin/env python3

"""
This script reads the current combi runConfigs and makes three sets with different alignment matrices.
Combi needs all alignments, but in different orders.
"""

import sys
sys.path.insert(0, '.')
import json
from detail.LMDRunConfig import LMDRunConfig
from pathlib import Path

alignerStages = [
    [False, True, True],
    [False, False, True],
    [False, True, False],
    [False, False, False]
]

if __name__ == "__main__":
    for i in range(4):
        for mom in ['1.5', '4.06', '8.9', '11.91', '15.0']:
            for fac in ['0.25', '0.50', '0.75', '1.00', '1.25', '1.50', '1.75', '2.00', '2.50', '3.00']:

                # read old combi runConfig file
                fileName = f'runConfigs/corrected/combi/{mom}/factor-{fac}.json'
                config = LMDRunConfig.fromJSON(fileName)
                alMatPath = config.pathAlMatrixPath()
                matFile = str(Path(alMatPath) / Path(f'alMat-combi{i}.json'))
                
                # change alignment matrix
                config.combiMat = matFile
                config.generateMatrixNames()
                config.stages = alignerStages[i]
                
                if i < 3:
                    config.forDisableCut = True
                
                # save to new dir
                destPath = Path(f'runConfigs/special/combi{i}/{mom}/factor-{fac}.json')
                destPath.parent.mkdir(exist_ok=True, parents=True)
                config.toJSON(destPath)