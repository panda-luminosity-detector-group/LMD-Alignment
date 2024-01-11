#!/usr/bin/env python3
"""
This script reads the current combi runConfigs and makes three sets with different alignment matrices.
Combi needs all alignments, but in different orders.
"""

import os
import sys
sys.path.insert(0, '.')
import json
from detail.LMDRunConfig import LMDRunConfig
from pathlib import Path

# TODO: remove combiMat and stages, you don't actually need them. a single runCombi function does this work now.

def copyCombiToSpecial():
    # alignerStages = [[False, True, True], [False, False, True], [False, True, False], [False, False, False]]
    combiName = ['combiSen', 'combiSenMod', 'combiSenIP', 'combiSenModIP']
    
    for i in range(4):
        for mom in ['1.5', '4.06', '8.9', '11.91', '15.0']:
            for fac in ['0.25', '0.50', '0.75', '1.00', '1.25', '1.50', '1.75', '2.00', '2.50']:  #, '3.00']:

                # read old combi runConfig file
                fileName = f'runConfigs/corrected/combi/{mom}/factor-{fac}.json'
                config = LMDRunConfig.fromJSON(fileName)
                alMatPath = config.pathAlMatrixPath()
                config.alMatFile = str(Path(f'alMat-{combiName[i]}-{fac}.json'))
                config.alMatPath = str(Path(alMatPath) / Path(f'alMat-{combiName[i]}-{fac}.json'))
                # change alignment matrix
                # config.combiMat = matFile
                # config.stages = alignerStages[i]

                if i < 3:
                    config.forDisableCut = True

                # save to new dir
                destPath = Path(f'runConfigs/special/{combiName[i]}/{mom}/factor-{fac}.json')
                destPath.parent.mkdir(exist_ok=True, parents=True)
                config.toJSON(destPath)


def copyCombiToMultiSeed():
    for mom in ['1.5', '4.06', '8.9', '11.91', '15.0']:
        for fac in ['0.25', '0.50', '0.75', '1.00', '1.25', '1.50', '1.75', '2.00', '2.50']:

            for seedID in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']:

                # read original combi file for mom and fac (not seed obvs)
                # do this each time so you don't reuse settings on accident

                fileName = f'runConfigs/corrected/combi/{mom}/factor-{fac}.json'
                config = LMDRunConfig.fromJSON(fileName)

                # change misMat, extMat, avgMat names
                vmcworkdir = os.environ['VMCWORKDIR'] # points to PandaRoot base dir
                config.sensorAlignExternalMatrixPath = f'input/sensorAligner/multi/externalMatrices-sensors-seed{seedID}-{fac}.json'
                config.moduleAlignAvgMisalignFile = f'input/moduleAlignment/multi/avgMisalign-seed{seedID}-{fac}.json'
                config.misMatFile = f'{vmcworkdir}/macro/detectors/lmd/geo/misMatrices/multi/misMat-combiSeed{seedID}-{fac}.json'
                config.alignmentCorrection = False
                # set more events per job
                config.trksNum = '200000'
                config.seedID = seedID
                config.generateJobBaseDir()

                # save to new runConfig
                destPath = Path(f'runConfigs/special/multiSeed/{mom}/{fac}/factor-{fac}-seed{seedID}.json')
                destPath.parent.mkdir(exist_ok=True, parents=True)
                config.toJSON(destPath)

                # you should now have 10 for each fac and seedID (100 total per momentum)
                pass

# This generates three NON-misaligned cases
def copyCombiToMultiSeedAligned():
    for mom in ['1.5', '4.06', '8.9', '11.91', '15.0']:
        for fac in ['0.0']:

            for seedID in ['1', '2', '3']:

                # read original combi file for mom and fac (not seed obvs)
                # do this each time so you don't reuse settings on accident

                fileName = f'runConfigs/corrected/aligned/{mom}/factor-1.00.json'
                config = LMDRunConfig.fromJSON(fileName)

                # change misMat, extMat, avgMat names
                vmcworkdir = os.environ['VMCWORKDIR'] # points to PandaRoot base dir
                config.sensorAlignExternalMatrixPath = f'input/sensorAligner/externalMatrices-sensors-aligned.json'
                config.moduleAlignAvgMisalignFile = f'input/moduleAlignment/avgMisalign-aligned.json'
                config.misMatFile = f'{vmcworkdir}/macro/detectors/lmd/geo/misMatrices/misMat-aligned-1.00.json'
                config.alignmentCorrection = False
                # set more events per job
                config.trksNum = '200000'
                config.seedID = seedID
                config.generateJobBaseDir()

                # save to new runConfig
                destPath = Path(f'runConfigs/special/multiSeed/{mom}/{fac}/factor-{fac}-seed{seedID}.json')
                destPath.parent.mkdir(exist_ok=True, parents=True)
                config.toJSON(destPath)

                # you should now have 10 for each fac and seedID (100 total per momentum)
                pass

if __name__ == "__main__":
    copyCombiToSpecial()
    copyCombiToMultiSeed()
    #copyCombiToMultiSeedAligned()      # don't do that for now