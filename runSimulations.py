#!/usr/bin/env python3

# limit openblas's max threads, this must be done BEFORE importing numpy
import os
import subprocess
os.environ.update(
    OMP_NUM_THREADS='8',
    OPENBLAS_NUM_THREADS='8',
    NUMEXPR_NUM_THREADS='8',
    MKL_NUM_THREADS='8',
)

import sys
import random
import json
import datetime
import concurrent
import argparse
from pathlib import Path
from detail.getTrackRecStatus import getTrackEfficiency
from detail.simWrapper import simWrapper
from detail.matrixComparator import *
from detail.LumiValLaTeXTable import LumiValGraph, LumiValLaTeXTable
from detail.logger import LMDrunLogger
from detail.LMDRunConfig import LMDRunConfig
#from concurrent.futures import ThreadPoolExecutor
from alignment.alignerSensors import alignerSensors
from alignment.alignerIP import alignerIP
from alignment.alignerModules import alignerModules
from argparse import RawTextHelpFormatter
from collections import defaultdict  # to concatenate dictionaries
"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de

This script handles all simulation related abstractions.

it:
- browses paths for TrksQA, reco_ip and lumi_vals
- runs simulations (aligned, misaligned)
- runs aligner scripts (alignIP, alignSensors, alignCorridors)
- re-runs simulations with align matrices
- runs ./determineLuminosity
- runs ./extractLuminosity
- compares lumi values before and after alignment
- compares found alignment matrices with actual alignment matrices
- converts JSON to ROOT matrices and vice-versa (with ROOT macros)

---------- steps in ideal geometry sim ----------

- run ./doSimulationReconstruction wit correct parameters (doesn't block)
- run ./determineLuminosity (blocks!)
- run ./extractLuminosity   (blocks!)

---------- steps in misaligned geometry sim ----------

- run ./doSimulationReconstruction wit correct parameters
- run ./determineLuminosity
- run ./extractLuminosity

---------- steps in misaligned geometry with correction ----------
- run ./doSimulationReconstruction with correct parameters
- run ./determineLuminosity
- run ./extractLuminosity
- run my aligners
- rerun ./doSimulationReconstruction with correct parameters
- rerun ./determineLuminosity
- rerun ./extractLuminosity

# TODO: remove combiMat and stages, you don't actually need them. a single runCombi function does this work now.

"""


# to easily copy files, monkey patch
def _copy(self, target):
    import shutil
    try:
        assert self.is_file()
    except:
        print(f'ERROR! {self} is not a file!')
    shutil.copy(self, target)


Path.copy = _copy


def startLogToFile(functionName=None):

    if functionName is None:
        runSimLog = f'runLogs/{datetime.date.today()}/run{runNumber}-main.log'
        runSimLogErr = f'runLogs/{datetime.date.today()}/run{runNumber}-main-stderr.log'

    else:
        runSimLog = f'runLogs/{datetime.date.today()}/run{runNumber}-main-{functionName}.log'
        runSimLogErr = f'runLogs/{datetime.date.today()}/run{runNumber}-main-{functionName}-stderr.log'

    # redirect stdout/stderr to log files
    print(f'+++ starting new run and forking to background! this script will write all output to {runSimLog}\n')
    Path(runSimLog).parent.mkdir(exist_ok=True, parents=True)
    sys.stdout = open(runSimLog, 'a+')
    sys.stderr = open(runSimLogErr, 'a+')
    print(f'+++ starting new run at {datetime.datetime.now()}:\n')


def done():
    print(f'\n\n====================================\n')
    print(f'       all tasks completed!           ')
    print(f'\n====================================\n\n')
    # cleanup, probably not neccessary
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    parser.exit(0)


# TODO: remove further code duplication in these functions!

# ? =========== functions that can be run by runAllConfigsMT


def runAligners(runConfig, threadID=None):

    # stages = runConfig.stages

    print(f'Thread {threadID}: starting!')
    # print(f'Stages:')
    # print(f'Sensor Align: {stages[0]}')
    # print(f'Module Align: {stages[1]}')
    # print(f'Target Align: {stages[2]}')

    # the follwong MUST be unique across all simulations, so set the seedID too!
    sensorAlignerOverlapsResultName = runConfig.pathAlMatrixPath() / Path(f'alMat-sensorOverlaps-seed{config.seedID}-{runConfig.misalignFactor}.json')
    sensorAlignerResultName = runConfig.pathAlMatrixPath() / Path(f'alMat-sensorAlignment-seed{config.seedID}-{runConfig.misalignFactor}.json')
    moduleAlignerResultName = runConfig.pathAlMatrixPath() / Path(f'alMat-moduleAlignment-seed{config.seedID}-{runConfig.misalignFactor}.json')
    IPalignerResultName = runConfig.pathAlMatrixPath() / Path(f'alMat-IPalignment-seed{config.seedID}-{runConfig.misalignFactor}.json')
    mergedAlignerResultName = runConfig.pathAlMatrixPath() / Path(f'alMat-merged-seed{config.seedID}-{runConfig.misalignFactor}.json')
    combi0Name = runConfig.pathAlMatrixPath() / Path(f'alMat-combiSen-seed{config.seedID}-{runConfig.misalignFactor}.json')
    combi1Name = runConfig.pathAlMatrixPath() / Path(f'alMat-combiSenMod-seed{config.seedID}-{runConfig.misalignFactor}.json')
    combi2Name = runConfig.pathAlMatrixPath() / Path(f'alMat-combiSenIP-seed{config.seedID}-{runConfig.misalignFactor}.json')
    combi3Name = runConfig.pathAlMatrixPath() / Path(f'alMat-combiSenModIP-seed{config.seedID}-{runConfig.misalignFactor}.json')

    moduleAlignDataPath = runConfig.pathTrksQA()
    moduleAlignTrackFile = moduleAlignDataPath / Path('processedTracks.json')

    # create logger
    thislogger = LMDrunLogger(f'./runLogs/{datetime.date.today()}/run{runNumber}-worker-Alignment-{runConfig.misalignType}-{runConfig.misalignFactor}-th{threadID}.txt')
    thislogger.log(runConfig.dump())

    #* create alignerSensors, run
    print(f'\n====================================\n')
    print(f'        running sensor aligner')
    print(f'\n====================================\n')
    sensorAligner = alignerSensors.fromRunConfig(runConfig)
    sensorAligner.loadExternalMatrices(runConfig.sensorAlignExternalMatrixPath)  # TODO: do implicitly, aligners always start with a run config
    sensorAligner.sortPairs()
    sensorAligner.findMatrices()
    sensorAligner.saveOverlapMatrices(sensorAlignerOverlapsResultName)
    sensorAligner.combineAlignmentMatrices()
    sensorAligner.saveAlignmentMatrices(sensorAlignerResultName)

    #* create alignerModules, run
    print(f'\n====================================\n')
    print(f'        running module aligner')
    print(f'\n====================================\n')
    moduleAligner = alignerModules.fromRunConfig(runConfig)
    moduleAligner.readAnchorPoints(runConfig.moduleAlignAnchorPointFile)  # TODO: do implicitly, aligners always start with a run config
    moduleAligner.readAverageMisalignments(runConfig.moduleAlignAvgMisalignFile)  # TODO: do implicitly, aligners always start with a run config
    moduleAligner.convertRootTracks(moduleAlignDataPath, moduleAlignTrackFile)
    moduleAligner.readTracks(moduleAlignTrackFile)
    moduleAligner.alignModules()
    moduleAligner.saveMatrices(moduleAlignerResultName)

    #* create alignerIP, run
    print(f'\n====================================\n')
    print(f'        running box rotation aligner')
    print(f'\n====================================\n')
    IPaligner = alignerIP.fromRunConfig(runConfig)
    IPaligner.logger = thislogger
    IPaligner.computeAlignmentMatrix()
    IPaligner.saveAlignmentMatrix(IPalignerResultName)

    #! ignore stages here for now. only if all stages have run all alignment matrices exist, but since all are run initally, that should be okay.
    # TODO: handle case when not all stages have run

    # combine all alignment matrices to one single json File
    with open(sensorAlignerResultName, 'r') as f:
        resSensors = json.load(f)

    with open(moduleAlignerResultName, 'r') as f:
        resModules = json.load(f)

    with open(IPalignerResultName, 'r') as f:
        resIPalign = json.load(f)

    mergedResult = {**resSensors, **resModules, **resIPalign}
    combi0Result = {**resSensors}
    combi1Result = {**resSensors, **resModules}
    combi2Result = {**resSensors, **resIPalign}
    combi3Result = {**resSensors, **resModules, **resIPalign}

    with open(mergedAlignerResultName, 'w') as f:
        json.dump(mergedResult, f, indent=2, sort_keys=True)

    with open(combi0Name, 'w') as f:
        json.dump(combi0Result, f, indent=2, sort_keys=True)

    with open(combi1Name, 'w') as f:
        json.dump(combi1Result, f, indent=2, sort_keys=True)

    with open(combi2Name, 'w') as f:
        json.dump(combi2Result, f, indent=2, sort_keys=True)

    with open(combi3Name, 'w') as f:
        json.dump(combi3Result, f, indent=2, sort_keys=True)

    print(f'Wrote merged alignment matrices to {mergedAlignerResultName}')
    print(f'Thread {threadID} done!')


def runCombi(runConfig, threadID=None):
    """ 
    This function runs the entire simulation chain and perfomrs all three alignments in order. Also fits the luminosity at each intermediate step.

    runConfig: holds MISalign matrix, misalign type and factor
    """

    #* ---------- prepare config (aligner stages, combi mat names etc)
    if runConfig.alignmentCorrection or (runConfig.misalignType != 'combi' and runConfig.misalignType != 'aligned'):
        print(f'Please only use UNcorrected combi runConfigs, this run does the rest')
        return

    print(f'Thread {threadID}: starting!')

    # the follwong MUST be unique across all simulations, so set the seedID too!
    sensorAlignerOverlapsResultName = runConfig.pathAlMatrixPath() / Path(f'alMat-sensorOverlaps-seed{runConfig.seedID}-{runConfig.misalignFactor}.json')
    sensorAlignerResultName = runConfig.pathAlMatrixPath() / Path(f'alMat-sensorAlignment-seed{runConfig.seedID}-{runConfig.misalignFactor}.json')
    moduleAlignerResultName = runConfig.pathAlMatrixPath() / Path(f'alMat-moduleAlignment-seed{runConfig.seedID}-{runConfig.misalignFactor}.json')
    IPalignerResultName = runConfig.pathAlMatrixPath() / Path(f'alMat-IPalignment-seed{runConfig.seedID}-{runConfig.misalignFactor}.json')
    combi0Name = runConfig.pathAlMatrixPath() / Path(f'alMat-combiSen-seed{runConfig.seedID}-{runConfig.misalignFactor}.json')
    combi1Name = runConfig.pathAlMatrixPath() / Path(f'alMat-combiSenMod-seed{runConfig.seedID}-{runConfig.misalignFactor}.json')
    combi3Name = runConfig.pathAlMatrixPath() / Path(f'alMat-combiSenModIP-seed{runConfig.seedID}-{runConfig.misalignFactor}.json')

    # create logger
    thislogger = LMDrunLogger(f'./runLogs/{datetime.date.today()}/run{runNumber}-worker-combi-{runConfig.misalignType}-{runConfig.misalignFactor}-th{threadID}.txt')

    #* ---------- first sim

    # create simWrapper from config
    prealignWrapper = simWrapper.fromRunConfig(runConfig)
    prealignWrapper.threadNumber = threadID
    prealignWrapper.logger = thislogger
    # run all
    prealignWrapper.runSimulations()  # non blocking, so we have to wait
    prealignWrapper.waitForJobCompletion()  # blocking
    # ---------- perform lumi fit
    prealignWrapper.detLumi()  # not blocking
    prealignWrapper.waitForJobCompletion()  # waiting
    prealignWrapper.extractLumi()  # blocking

    #* ---------- align sensors
    # create alignerSensors, run
    print(f'\n====================================\n')
    print(f'        running sensor aligner')
    print(f'\n====================================\n')
    print(runConfig.dump())  # debug output
    sensorAligner = alignerSensors.fromRunConfig(runConfig)
    sensorAligner.loadExternalMatrices(runConfig.sensorAlignExternalMatrixPath)  # TODO: do implicitly, aligners always start with a run config
    sensorAligner.sortPairs()
    sensorAligner.findMatrices()
    sensorAligner.saveOverlapMatrices(sensorAlignerOverlapsResultName)
    sensorAligner.combineAlignmentMatrices()
    sensorAligner.saveAlignmentMatrices(sensorAlignerResultName)
    del sensorAligner

    # make intermediate result 0
    with open(sensorAlignerResultName, 'r') as f:
        resSensors = json.load(f)
    combi0Result = {**resSensors}
    with open(combi0Name, 'w') as f:
        json.dump(combi0Result, f, indent=2, sort_keys=True)
    runConfig.alMatFile = combi0Name

    #! ========== Sensors are now aligned

    #TODO: MAYBE the track, reco and recoMerged files have to be deleted before this step, and again after module alignment. fuck me if I know, but I'll see soon enough.

    #* ---------- half run again, use sensor Align Matrix (combi0)
    # enable correction this time #! this was important because it changed the internal state of the runConfig somehow. check that!
    runConfig.alignmentCorrection = True
    # force cut off, otherwise too many tracks will be discarded
    runConfig.forDisableCut = True

    # create simWrapper from config
    prealignWrapper = simWrapper.fromRunConfig(runConfig)
    prealignWrapper.threadNumber = threadID
    prealignWrapper.logger = thislogger
    # run all
    prealignWrapper.runSimulations()  # non blocking, so we have to wait
    prealignWrapper.waitForJobCompletion()  # blocking

    #* ---------- align modules
    print(f'\n====================================\n')
    print(f'        running module aligner')
    print(f'\n====================================\n')
    print(runConfig.dump())  # debug output
    # prepare paths, don't do this earlier!
    moduleAlignDataPath = runConfig.pathTrksQA()  # TODO: there is an error here! This doesn't go into the proper subfolders! (1-100_uncut/no_alignment_correction)
    moduleAlignTrackFile = moduleAlignDataPath / Path('processedTracks.json')

    moduleAligner = alignerModules.fromRunConfig(runConfig)
    moduleAligner.readAnchorPoints(runConfig.moduleAlignAnchorPointFile)  # TODO: do implicitly, aligners always start with a run config
    moduleAligner.readAverageMisalignments(runConfig.moduleAlignAvgMisalignFile)  # TODO: do implicitly, aligners always start with a run config
    moduleAligner.convertRootTracks(moduleAlignDataPath, moduleAlignTrackFile)
    moduleAligner.readTracks(moduleAlignTrackFile)
    moduleAligner.alignModules()
    moduleAligner.saveMatrices(moduleAlignerResultName)
    del moduleAligner

    # make intermediate result 1
    with open(sensorAlignerResultName, 'r') as f:
        resSensors = json.load(f)
    with open(moduleAlignerResultName, 'r') as f:
        resModules = json.load(f)
    combi1Result = {**resSensors, **resModules}
    with open(combi1Name, 'w') as f:
        json.dump(combi1Result, f, indent=2, sort_keys=True)
    runConfig.alMatFile = combi1Name

    #! ========== Modules are now aligned

    #* ---------- half run again
    # this thime, we need the cut
    runConfig.forDisableCut = False
    # create simWrapper from config
    prealignWrapper = simWrapper.fromRunConfig(runConfig)
    prealignWrapper.threadNumber = threadID
    prealignWrapper.logger = thislogger
    # run all
    prealignWrapper.runSimulations()  # non blocking, so we have to wait
    prealignWrapper.waitForJobCompletion()  # blocking
    # ---------- perform lumi fit, for posterity
    prealignWrapper.detLumi()  # not blocking
    prealignWrapper.waitForJobCompletion()  # waiting
    prealignWrapper.extractLumi()  # blocking

    #* ---------- align IP, last combi result
    print(f'\n============================================\n')
    print(f'        running box rotation aligner        ')
    print(f'\n============================================\n')
    print(runConfig.dump())  # debug output
    IPaligner = alignerIP.fromRunConfig(runConfig)
    IPaligner.logger = thislogger
    IPaligner.computeAlignmentMatrix()
    IPaligner.saveAlignmentMatrix(IPalignerResultName)
    del IPaligner

    # make intermediate result 3
    with open(sensorAlignerResultName, 'r') as f:
        resSensors = json.load(f)
    with open(moduleAlignerResultName, 'r') as f:
        resModules = json.load(f)
    with open(IPalignerResultName, 'r') as f:
        resIPalign = json.load(f)
    combi3Result = {**resSensors, **resModules, **resIPalign}
    with open(combi3Name, 'w') as f:
        json.dump(combi3Result, f, indent=2, sort_keys=True)
    runConfig.alMatFile = combi3Name

    #! ========== ALL is now aligned

    #* ---------- FINAL run and lumi fit
    # this thime, we need the cut
    runConfig.forDisableCut = False
    # create simWrapper from config
    prealignWrapper = simWrapper.fromRunConfig(runConfig)
    prealignWrapper.threadNumber = threadID
    prealignWrapper.logger = thislogger
    # run all
    prealignWrapper.runSimulations()  # non blocking, so we have to wait
    prealignWrapper.waitForJobCompletion()  # blocking
    # ---------- perform lumi fit
    prealignWrapper.detLumi()  # not blocking
    prealignWrapper.waitForJobCompletion()  # waiting
    prealignWrapper.extractLumi()  # blocking
    print(f'=================================')
    print(f'== REJOICE, COMBI RUN IS DONE! ==')
    print(f'=================================')

    # delete temp data
    # delete: Lumi_Track_*.root
    # delete: Lumi_recoMerged_*.root
    # delete: Lumi_Pairs_*.root
    # you save: original: 171G after delete: 58G (doesn't include boxdata)
    #workDir


def runExtractLumi(runConfig, threadID=None):

    print(f'Thread {threadID}: starting!')

    # create logger
    thislogger = LMDrunLogger(f'./runLogs/{datetime.date.today()}/run{runNumber}-worker-ExtractLumi-{runConfig.misalignType}-{runConfig.misalignFactor}-th{threadID}.txt')
    thislogger.log(runConfig.dump())

    # create simWrapper from config
    prealignWrapper = simWrapper.fromRunConfig(runConfig)
    prealignWrapper.threadNumber = threadID
    prealignWrapper.logger = thislogger

    # run
    prealignWrapper.extractLumi()  # blocking

    print(f'Thread {threadID} done!')


def runLumifit(runConfig, threadID=None):

    print(f'Thread {threadID}: starting!')

    # create logger
    thislogger = LMDrunLogger(f'./runLogs/{datetime.date.today()}/run{runNumber}-worker-LumiFit-{runConfig.misalignType}-{runConfig.misalignFactor}-th{threadID}.txt')
    thislogger.log(runConfig.dump())

    # create simWrapper from config
    prealignWrapper = simWrapper.fromRunConfig(runConfig)
    prealignWrapper.threadNumber = threadID
    prealignWrapper.logger = thislogger

    # run
    prealignWrapper.detLumi()  # not blocking!
    prealignWrapper.waitForJobCompletion()  # waiting
    prealignWrapper.extractLumi()  # blocking

    print(f'Thread {threadID} done!')


def runSimRecoLumi(runConfig, threadID=None):

    print(f'Thread {threadID}: starting!')

    # create logger
    thislogger = LMDrunLogger(f'./runLogs/{datetime.date.today()}/run{runNumber}-worker-SimReco-{runConfig.misalignType}-{runConfig.misalignFactor}-th{threadID}.txt')
    thislogger.log(runConfig.dump())

    # create simWrapper from config
    prealignWrapper = simWrapper.fromRunConfig(runConfig)
    prealignWrapper.threadNumber = threadID
    prealignWrapper.logger = thislogger

    # run all
    prealignWrapper.runSimulations()  # non blocking, so we have to wait
    prealignWrapper.waitForJobCompletion()  # blocking

    print(f'Thread {threadID} done!')


def halfRun(runConfig, threadID=None):
    print(f'Thread {threadID}: starting!')

    # create logger
    thislogger = LMDrunLogger(f'./runLogs/{datetime.date.today()}/run{runNumber}-worker-FullRun-{runConfig.misalignType}-{runConfig.misalignFactor}-th{threadID}.txt')

    # create simWrapper from config
    prealignWrapper = simWrapper.fromRunConfig(runConfig)
    prealignWrapper.threadNumber = threadID
    prealignWrapper.logger = thislogger

    # run all
    prealignWrapper.runSimulations()  # non blocking, so we have to wait
    prealignWrapper.waitForJobCompletion()  # blocking
    prealignWrapper.detLumi()  # not blocking
    prealignWrapper.waitForJobCompletion()  # waiting
    prealignWrapper.extractLumi()  # blocking

    # run alignment afterwards
    runAligners(runConfig, threadID)
    print(f'Thread {threadID} done!')


def runSimRecoLumiAlignRecoLumi(runConfig, threadID=None):

    print(f'Thread {threadID}: starting!')

    # start with a config, not a wrapper
    # add a filter, if the config assumes alignment correction, discard

    if runConfig.alignmentCorrection:
        print(f'Thread {threadID}: this runConfig contains a correction, ignoring')
        print(f'Thread {threadID}: done!')
        runConfig.alignmentCorrection = False
        # return

    # create logger
    thislogger = LMDrunLogger(f'./runLogs/{datetime.date.today()}/run{runNumber}-worker-FullRun-{runConfig.misalignType}-{runConfig.misalignFactor}-th{threadID}.txt')

    # create simWrapper from config
    prealignWrapper = simWrapper.fromRunConfig(runConfig)
    prealignWrapper.threadNumber = threadID
    prealignWrapper.logger = thislogger

    # run all
    prealignWrapper.runSimulations()  # non blocking, so we have to wait
    prealignWrapper.waitForJobCompletion()  # blocking
    prealignWrapper.detLumi()  # not blocking
    prealignWrapper.waitForJobCompletion()  # waiting
    prealignWrapper.extractLumi()  # blocking

    # then run aligner(s)
    runAligners(runConfig, threadID)

    # then, set align correction in config true and recreate simWrapper
    runConfig.alignmentCorrection = True

    postalignWrapper = simWrapper.fromRunConfig(runConfig)
    prealignWrapper.threadNumber = threadID
    postalignWrapper.logger = thislogger

    # re run reco steps and Lumi fit
    postalignWrapper.runSimulations()  # non blocking, so we have to wait
    postalignWrapper.waitForJobCompletion()  # blocking
    postalignWrapper.detLumi()  # not blocking
    postalignWrapper.waitForJobCompletion()  # waiting
    postalignWrapper.extractLumi()  # blocking

    print(f'Thread {threadID} done!')


def showLumiFitResults(runConfigPath, threadID=None, saveGraph=False):

    # read all configs from path
    runConfigPath = Path(runConfigPath)
    configFiles = list(runConfigPath.glob('**/factor*.json'))

    configs = []
    for file in configFiles:
        config = LMDRunConfig.fromJSON(file)
        configs.append(config)

    if len(configs) == 0:
        print(f'No runConfig files found in {runConfigPath}!')
    else:
        print(f'found {len(configs)} config files.')

    if saveGraph:
        print(f'saving to graph.')

        if configs[0].alignmentCorrection:
            corrStr = 'corrected'
        else:
            corrStr = 'uncorrected'
        
        fileName = Path(f'output/LumiResults/{configs[0].momentum}/{configs[0].misalignType}/LumiFits-{corrStr}')
        fileName.parent.mkdir(exist_ok=True, parents=True)

        graph = LumiValGraph.fromConfigs(configs)
        
        fileName2 = Path(f'output/LumiResults/All/multi-alMat-combiSenMod-{configs[0].misalignFactor}.json')
        fileName2.parent.mkdir(exist_ok=True, parents=True)
        fileName2 = str(Path(f'output/LumiResults/All/multi-alMat-combiSenMod-{configs[0].misalignFactor}.json'))

        if (configs[0].misalignType == 'combi') and (configs[0].seedID is not None):
            graph.multiSeed(fileName2)
            done()

        else:
            fileName2 = Path(f'output/LumiResults/All/{configs[0].misalignType}-{corrStr}')
            print(f'saving graph to {fileName2}')
            graph.saveAllMomenta(fileName2)
            done()

    else:
        print(f'printing to stdout:')
        table = LumiValLaTeXTable.fromConfigs(configs)
        table.show()


def histogramRunConfig(runConfig, threadId=0):

    # copy matrices from himster to local folder
    oldTargetDir = Path(runConfig.pathAlMatrixPath())

    # remotePrefix = Path('/lustre/miifs05/scratch/him-specf/paluma/roklasen')
    remotePrefix = Path('/media/DataEnc2TBRaid1/Arbeit/VirtualDir')
    targetDir = Path(f'output/temp/alMats/{runConfig.misalignType}-{runConfig.momentum}-{runConfig.misalignFactor}/')
    targetDir.mkdir(exist_ok=True, parents=True)
    # compose remote dir from local dir
    remoteDir = str(remotePrefix / Path(*oldTargetDir.parts[7:]))
    print(f'copying:\n{remoteDir}\nto:\n{targetDir}')

    if True:
        success = subprocess.run(['cp', '-r', remoteDir, targetDir]).returncode

        if success > 0:
            print(f'\n\n')
            print(f'-------------------------------------------------')
            print(f'file could not be copied, skipping this scenario.')
            print(f'-------------------------------------------------')
            print(f'\n\n')
            return

    targetDir = targetDir / Path(f'alignmentMatrices')

    # here be ugly hack
    importantFile = Path(targetDir / Path(f'alMat-merged.json'))
    if not importantFile.exists():
        print(f'you failed')
        if runConfig.misalignFactor == '3.00':
            return
        subprocess.run(['cp', Path(targetDir / Path(f'alMat-combiSenModIP-{runConfig.misalignFactor}.json')), importantFile])

    # box rotation comparator
    comparator = boxComparator(runConfig)
    comparator.loadIdealDetectorMatrices('input/detectorMatricesIdeal.json')
    # comparator.loadDesignMisalignments(runConfig.misMatFile)
    # the design misalignment is so small, just use ideal as comparisond
    comparator.loadDesignMisalignments("/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot-New/macro/detectors/lmd/geo/misMatrices/misMat-aligned-1.00.json")
    comparator.loadAlignerMatrices(targetDir / Path(f'alMat-merged.json'))
    boxResult = comparator.saveHistogram(f'output/comparison/{runConfig.momentum}/misalign-{runConfig.misalignType}/box-{runConfig.misalignFactor}-icp.pdf')

    # overlap comparator
    comparator = overlapComparator(runConfig)
    comparator.loadIdealDetectorMatrices('input/detectorMatricesIdeal.json')
    comparator.loadPerfectDetectorOverlaps('input/detectorOverlapsIdeal.json')
    comparator.loadDesignMisalignments(runConfig.misMatFile)
    comparator.loadSensorAlignerOverlapMatrices(targetDir / Path(f'alMat-sensorOverlaps-{runConfig.misalignFactor}.json'))
    overlapResult = comparator.saveHistogram(f'output/comparison/{runConfig.momentum}/misalign-{runConfig.misalignType}/sensor-overlaps-{runConfig.misalignFactor}-icp.pdf')

    # module comparator
    comparator = moduleComparator(runConfig)
    comparator.loadIdealDetectorMatrices('input/detectorMatricesIdeal.json')
    comparator.loadDesignMisalignments(runConfig.misMatFile)
    comparator.loadAlignerMatrices(targetDir / Path(f'alMat-merged.json'))
    moduleResult = comparator.saveHistogram(f'output/comparison/{runConfig.momentum}/misalign-{runConfig.misalignType}/modules-{runConfig.misalignFactor}.pdf')

    # combined comparator
    comparator = combinedComparator(runConfig)
    comparator.loadIdealDetectorMatrices('input/detectorMatricesIdeal.json')
    comparator.loadDesignMisalignments(runConfig.misMatFile)
    comparator.loadAlignerMatrices(targetDir / Path(f'alMat-merged.json'))
    sensorResult = comparator.saveHistogram(f'output/comparison/{runConfig.momentum}/misalign-{runConfig.misalignType}/sensors-{runConfig.misalignFactor}-misalignments.pdf')

    # refine
    if runConfig.misalignType == 'aligned':
        print(f'This one is aligned, not returning data.')
        return None

    moduleResultMean = np.average(moduleResult, axis=0)
    moduleResultSigma = np.std(moduleResult, axis=0)

    overlapResultMean = np.average(overlapResult, axis=0)
    overlapResultSigma = np.std(overlapResult, axis=0)

    sensorResultMean = np.average(sensorResult, axis=0)
    sensorResultSigma = np.std(sensorResult, axis=0)

    values = {}
    values[runConfig.momentum] = {}
    values[runConfig.momentum][runConfig.misalignFactor] = {
        # 'momentum' : runConfig.momentum,
        'box': np.array(boxResult).tolist(),
        'modules': (np.array(moduleResultMean).tolist(), np.array(moduleResultSigma).tolist()),
        'overlaps': (np.array(overlapResultMean).tolist(), np.array(overlapResultSigma).tolist()),
        'sensors': (np.array(sensorResultMean).tolist(), np.array(sensorResultSigma).tolist())
    }

    # print(values)
    return values


# ? =========== runAllConfigsMT that calls 'function' multithreaded


def runConfigsMT(args, function, threads=8):    # for multiseed, change this back for single scenarios!

    configs = []
    # read all configs from path
    searchDir = Path(args.configPath)

    if args.recursive:
        configs = list(searchDir.glob('**/factor*.json'))
    else:
        configs = list(searchDir.glob('factor*.json'))

    if len(configs) == 0:
        print(f'No runConfig files found in {searchDir}. Exiting!')
        sys.exit(1)

    simConfigs = []

    # loop over all configs, create wrapper and run
    for configFile in configs:
        runConfig = LMDRunConfig.fromJSON(configFile)
        simConfigs.append(runConfig)

    maxThreads = min(len(simConfigs), threads)
    print(f'INFO: running in {maxThreads} threads!')

    futures = {}

    if args.debug:
        maxThreads = 1

        for con in simConfigs:
            con.useDebug = True
            function(con, 0)

    else:
        # run concurrently in maximum 64 threads. they mostly wait for compute nodes anyway.
        # we use a process pool instead of a thread pool because the individual interpreters are working on different cwd's.
        # although I don't think that's actually needed...
        with concurrent.futures.ProcessPoolExecutor(max_workers=maxThreads) as executor:
            # Start the load operations and mark each future with its URL
            for index, config in enumerate(simConfigs):
                futures[index] = executor.submit(function, config, index)

        print('waiting for all jobs...')

        executor.shutdown(wait=True)
        for i in futures:
            print(f'future with index {i} returned:\n')
            print(f'{futures[i].result()}')
            print(f'end of return {i}')
    return


def runConfigsST(args, function):
    configs = []
    # read all configs from path
    searchDir = Path(args.configPath)

    if args.recursive:
        configs = list(searchDir.glob('**/factor*.json'))
    else:
        configs = list(searchDir.glob('factor*.json'))

    if len(configs) == 0:
        print(f'No runConfig files found in {searchDir}. Exiting!')
        sys.exit(1)

    simConfigs = []

    # loop over all configs, create wrapper and run
    for configFile in configs:
        runConfig = LMDRunConfig.fromJSON(configFile)
        simConfigs.append(runConfig)

    for con in simConfigs:
        yield function(con, 0)


def createMultipleDefaultConfigs():
    # for now
    correctedOptions = [False, True]
    # momenta = ['1.5', '15.0']
    momenta = ['1.5', '4.06', '8.9', '11.91', '15.0']
    misFactors = {}
    # misTypes = ['aligned', 'identity', 'sensors', 'box', 'box100', 'boxRotZ', 'modules', 'modulesNoRot', 'modulesOnlyRot', 'combi']
    misTypes = ['aligned', 'identity', 'sensors', 'box100', 'modules', 'combi']

    setOne = ['0.25', '0.50', '0.75', '1.00', '1.25', '1.50', '1.75', '2.00', '2.50', '3.00']
    setTwo = ['0.25', '0.50', '0.75', '1.00', '1.50', '2.00', '3.00', '5.00', '7.50', '10.00']

    misFactors['aligned'] = ['1.00']
    misFactors['identity'] = ['1.00']
    misFactors['sensors'] = setOne
    misFactors['box'] = setOne
    misFactors['box100'] = setOne
    misFactors['boxRotZ'] = setTwo
    misFactors['modules'] = setOne
    misFactors['combi'] = setOne
    misFactors['modulesNoRot'] = ['0.50', '1.00', '2.00']
    misFactors['modulesOnlyRot'] = ['0.50', '1.00', '2.00']

    for misType in misTypes:
        for mom in momenta:
            for fac in misFactors[misType]:
                for corr in correctedOptions:

                    if corr:
                        corrPath = 'corrected'
                    else:
                        corrPath = 'uncorrected'
                    dest = Path('runConfigs') / Path(corrPath) / Path(misType) / Path(mom) / Path(f'factor-{fac}.json')
                    dest.parent.mkdir(parents=True, exist_ok=True)

                    config = LMDRunConfig.minimalDefault()

                    #* set all misalignment matrix file names
                    vmcworkdir = os.environ['VMCWORKDIR']
                    if misType == 'aligned':
                        config.misMatFile = f'{vmcworkdir}/macro/detectors/lmd/geo/misMatrices/misMat-aligned-1.00.json'
                        config.alMatFile = None

                    if misType == 'identity':
                        config.misMatFile = f'{vmcworkdir}/macro/detectors/lmd/geo/misMatrices/misMat-aligned-1.00.json'
                        config.alMatFile = str(Path('input/alMat-identity-all.json'))

                    if misType == 'box100':
                        config.misMatFile = f'{vmcworkdir}/macro/detectors/lmd/geo/misMatrices/misMat-box100-{fac}.json'
                        config.alMatFile = str(config.pathAlMatrixPath() / Path(f'alMat-IPalignment-{fac}.json'))

                    if misType == 'combi':
                        config.misMatFile = f'{vmcworkdir}/macro/detectors/lmd/geo/misMatrices/misMat-combi-{fac}.json'
                        config.alMatFile = str(config.pathAlMatrixPath() / Path(f'alMat-combiSenMod-{fac}.json'))  # this is a placeholder, the actual values are in the special subfolder after makeCombiRunConfigs

                    if misType == 'modules':
                        config.misMatFile = f'{vmcworkdir}/macro/detectors/lmd/geo/misMatrices/misMat-modules-{fac}.json'
                        config.alMatFile = str(config.pathAlMatrixPath() / Path(f'alMat-moduleAlignment-{fac}.json'))

                    if misType == 'sensors':
                        config.misMatFile = f'{vmcworkdir}/macro/detectors/lmd/geo/misMatrices/misMat-sensors-{fac}.json'
                        config.alMatFile = str(config.pathAlMatrixPath() / Path(f'alMat-sensorAlignment-{fac}.json'))

                    config.misalignFactor = fac
                    config.misalignType = misType
                    config.momentum = mom
                    config.alignmentCorrection = corr

                    # identity and aligned don't get factors, only momenta and need fewer pairs
                    if misType == 'aligned' or misType == 'identity':
                        config.useIdentityMisalignment = True
                        config.sensorAlignExternalMatrixPath = f'input/sensorAligner/externalMatrices-sensors-aligned.json'
                        config.moduleAlignAvgMisalignFile = f'input/moduleAlignment/avgMisalign-aligned.json'

                    # supply anchor ppoints to all cases
                    config.moduleAlignAnchorPointFile = f'input/moduleAlignment/anchorPoints.json'

                    # supply external matrices to all cases
                    config.sensorAlignExternalMatrixPath = f'input/sensorAligner/externalMatrices-sensors-{fac}.json'

                    # supply avg misalignments accordingly
                    if misType == 'modulesNoRot':
                        config.moduleAlignAvgMisalignFile = f'input/moduleAlignment/avgMisalign-noRot-{fac}.json'
                    elif misType == 'modulesOnlyRot':
                        config.moduleAlignAvgMisalignFile = f'input/moduleAlignment/avgMisalign-onlyRot-{fac}.json'
                    else:
                        config.moduleAlignAvgMisalignFile = f'input/moduleAlignment/avgMisalign-{fac}.json'

                    # ? ----- special cases here
                    # aligned case has no misalignment
                    if misType == 'aligned':
                        config.misaligned = False

                    # if Path(dest).exists():
                    #     # don;t overwrite, just continue
                    #     pass
                    config.generateJobBaseDir()
                    config.toJSON(dest)


# ? =========== main user interface

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=RawTextHelpFormatter)

    parser.add_argument('-a', metavar='--alignConfig', type=str, dest='alignConfig', help='find all alignment matrices (IP, corridor, sensors) for runConfig')
    parser.add_argument('-A', metavar='--alignConfigPath', type=str, dest='alignConfigPath', help='same as -a, but for all Configs in specified path')

    parser.add_argument('--combi', metavar='--combiRunConfig', type=str, dest='combiRunConfig', help='Do a combi run (all misalignments, all alignments in sequence)')
    parser.add_argument('--COMBI', metavar='--combiRunConfigPath', type=str, dest='combiRunConfigPath', help='same as --combi, but for all Configs in specified path')

    parser.add_argument('--half', metavar='--halfRunConfig', type=str, dest='halfRunConfig', help='Do a half run (simulate/reconstruct data and determine Luminosity)')
    parser.add_argument('--HALF', metavar='--halfRunConfigPath', type=str, dest='halfRunConfigPath', help='same as --half, but for all Configs in specified path')

    parser.add_argument('-f', metavar='--fullRunConfig', type=str, dest='fullRunConfig', help='Do a full run (simulate mc data, find alignment, determine Luminosity)')
    parser.add_argument('-F', metavar='--fullRunConfigPath', type=str, dest='fullRunConfigPath', help='same as -f, but for all Configs in specified path')

    parser.add_argument('-FS', #TODO: deprecate, wasn't really used
                        metavar='--fullRunConfigSequencePath',
                        type=str,
                        dest='fullRunConfigSequencePath',
                        help='run multiple runConfigs sequentially (e.g. for multiple types of alignment)')

    parser.add_argument('-l', metavar='--lumifitConfig', type=str, dest='lumifitConfig', help='determine Luminosity for runConfig')
    parser.add_argument('-L', metavar='--lumifitConfigPath', type=str, dest='lumifitConfigPath', help='same as -l, but for all Configs in specified path')

    parser.add_argument('-el', metavar='--extractLumiConfig', type=str, dest='extractLumiConfig', help='extract Luminosity for runConfig')
    parser.add_argument('-EL', metavar='--extractLumiConfigPath', type=str, dest='extractLumiConfigPath', help='same as -el, but for all Configs in specified path')

    parser.add_argument('-s', metavar='--simulationConfig', type=str, dest='simulationConfig', help='run simulation and reconstruction for runConfig')
    parser.add_argument('-S', metavar='--simulationConfigPath', type=str, dest='simulationConfigPath', help='same as -s, but for all Configs in specified path')

    #parser.add_argument('-v', metavar='--fitValuesConfig', type=str, dest='fitValuesConfig', help='display reco_ip and lumi_vals for select runConfig (if found)')
    parser.add_argument('-V', metavar='--fitValuesConfigPath', type=str, dest='fitValuesConfigPath', help='display reco_ip and lumi_vals for all runConfigs in path')

    parser.add_argument('-r', action='store_true', dest='recursive', help='use with any config Path option to scan paths recursively')

    parser.add_argument('--hist', type=str, dest='histSensorAligner', help='hist matrix deviations for runConfig')
    parser.add_argument('--histPath', type=str, dest='histSensorAlignerPath', help='hist matrix deviations for all runConfigs in Path, recursively')

    parser.add_argument('--histRecPath', type=str, dest='histRecPath', help='hist theta rec for well resonctructed tracks')

    parser.add_argument('-d', action='store_true', dest='makeDefault', help='make a single default LMDRunConfig and save it to runConfigs/identity-1.00.json')
    parser.add_argument('-D', action='store_true', dest='makeMultipleDefaults', help='make multiple example LMDRunConfigs')
    parser.add_argument('--debug', action='store_true', dest='debug', help='run single threaded, more verbose output, submit jobs to devel queue')
    parser.add_argument('--updateRunConfigs', dest='updateRunConfigs', help='read all configs in ./runConfig, recreate the matrix file paths and store them.')
    parser.add_argument('--test', action='store_true', dest='test', help='internal test function')

    try:
        args = parser.parse_args()
    except:
        # parser.print_help()
        parser.exit(1)

    if len(sys.argv) < 2:
        parser.print_help()
        parser.exit(1)

    # random number to identify runs
    global runNumber
    runNumber = random.randint(0, 100)

    if args.makeMultipleDefaults:
        createMultipleDefaultConfigs()
        done()

    if args.updateRunConfigs:

        targetDir = Path(args.updateRunConfigs).absolute()
        print(f'reading all files from {targetDir} and regenerating settings...')

        configs = [x for x in targetDir.glob('**/factor*.json') if x.is_file()]

        for fileName in configs:
            conf = LMDRunConfig.fromJSON(fileName)
            conf.updateEnvPaths()
            conf.generateJobBaseDir()
            conf.toJSON(fileName)
        done()

    if args.test:
        print(f'Testing...')

        # this performs module alignment, stores the matrices to a temp file and runs the matrix comparator against this matrix file
        if True:

            # from good-ish tracks
            # trackFile = Path('input/modulesAlTest/combi0/processedTracks.json')
            # trackFile = Path('input/modulesAlTest/combi0/vgl.json')

            #! these are from 23.03.2020, first real combi run
            # trackFile = Path('input/modulesAlTest/combi0/tracksNoAlignment.json')
            # trackFile = Path('input/modulesAlTest/combi0/tracksAlignedCombi0.json')
            trackFile = Path('input/modulesAlTest/combi0/tracksBroken-2.5.json')

            alignerMod = alignerModules()
            alignerMod.readAnchorPoints('input/moduleAlignment/anchorPoints.json')
            alignerMod.readAverageMisalignments('input/moduleAlignment/avgMisalign-1.00.json')
            alignerMod.readTracks(trackFile)
            alignerMod.alignModules()
            # alignerMod.saveMatrices('input/modulesAlTest/combi0/alMat-noAlign.json')
            # alignerMod.saveMatrices('input/modulesAlTest/combi0/alMat-withCombi0.json')
            alignerMod.saveMatrices('input/modulesAlTest/combi0/alMat-broken.json')

            #! run comparator
            # comp = moduleComparator(LMDRunConfig.fromJSON('runConfigs/uncorrected/modules/15.0/factor-1.00.json'))
            comp = moduleComparator(LMDRunConfig.fromJSON('runConfigs/special/combi0/15.0/factor-1.00.json'))
            comp.loadIdealDetectorMatrices('input/detectorMatricesIdeal.json')
            comp.loadDesignMisalignments('/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot-New/macro/detectors/lmd/geo/misMatrices/misMat-modules-1.00.json')
            # comp.loadDesignMisalignments('/media/DataEnc2TBRaid1/Arbeit/Root/PandaRoot-New/macro/detectors/lmd/geo/misMatrices/misMat-aligned-1.00.json')
            # comp.loadAlignerMatrices('input/modulesAlTest/combi0/alMat-withCombi0.json')
            # comp.loadAlignerMatrices('input/modulesAlTest/combi0/alMat-noAlign.json')
            comp.loadAlignerMatrices('input/modulesAlTest/combi0/almat-broken.json')
            # comp.saveHistogram('input/modulesAlTest/combi0/residuals-modules-2020-03-23-noAlign.pdf')
            comp.saveHistogram('input/modulesAlTest/combi0/residuals-modules-2020-03-23-withCombi0-fromHimster.pdf')

            done()

    if args.debug:
        print(f'\n\n!!! Running in debug mode !!!\n\n')

    # ? =========== histogram Aligner results
    if args.histSensorAligner:
        runConfig = LMDRunConfig.fromJSON(args.histSensorAligner)
        if args.debug:
            runConfig.useDebug = True
        histogramRunConfig(runConfig)
        done()

    if args.histSensorAlignerPath:
        args.configPath = args.histSensorAlignerPath
        allVals = defaultdict(dict)
        for values in runConfigsST(args, histogramRunConfig):

            if values is None:
                continue

            print(f'I got these values: {values}')
            for key, value in values.items():
                mom = key
                theseValues = value
                break  # just in case there is more than one, which shoul never be

            # merge dict to current
            allVals[mom].update(theseValues)

        print(allVals)

        with open(f'{args.configPath}/allMatrixValues.json', 'w') as f:
            json.dump(allVals, f, sort_keys=True, indent=2)
        done()

    # ? =========== hist thetarec
    if args.histRecPath:

        print(f'finding configs!')
        targetDir = Path(args.histRecPath)
        configs = [x for x in targetDir.glob('**/*.json') if x.is_file()]

        runConfs = []
        for fileName in configs:
            runConfs.append(LMDRunConfig.fromJSON(fileName))

        goodFiles = []

        print(f'Running.')
        for con in runConfs:
            print(f'.', end='')
            QAfiles = con.pathDataBaseDir().glob('Lumi_TrksQA_*.root')

            for file in QAfiles:
                goodFiles.append(file)

            if len(goodFiles) > 0:

                iFile = 0

                while True:

                    if iFile == len(goodFiles):
                        print('\n==\nNo more files!\n==')
                        firstQAfile = None
                        break

                    firstQAfile = goodFiles[iFile]
                    size = firstQAfile.stat().st_size
                    if size > 3000:
                        break
                    else:
                        # TODO: iFile must not get larger than len(goodfiles)!
                        print(f'file {firstQAfile} is too small, skipping...')
                        iFile += 1

                if firstQAfile is None:
                    continue

                # plot function here!
                if con.alignmentCorrection:
                    corrStr = 'corr'
                else:
                    corrStr = 'uncorr'
                outfile = f'output/thetaRec-{con.misalignType}-{con.misalignFactor}-{corrStr}.pdf'
                getTrackEfficiency(firstQAfile, outfile)

                goodFiles = []

        done()

    # ? =========== lumi fit results, single config
    # if args.fitValuesConfig:
    #     config = LMDRunConfig.fromJSON(args.fitValuesConfig)
    #     if args.debug:
    #         config.useDebug = True
    #     showLumiFitResults(config, 99)
    #     done()

    # ? =========== lumi fit results, multiple configs
    if args.fitValuesConfigPath:
        #args.configPath = args.fitValuesConfigPath
        print(f'\n\n')
        # I don't think thats valid anymore
        # print(f'======================================')
        # print(f'  Remember to run --histPath before!')
        # print(f'======================================')
        print(f'\n\n')
        print(f'Graphing all Lumi values in {args.fitValuesConfigPath}')
        showLumiFitResults(args.fitValuesConfigPath, 0, True)
        done()

    #! ---------------------- logging goes to file if not in debug mode

    if not args.debug:
        if os.fork():
            sys.exit()

    # ? =========== align, single config
    if args.alignConfig:
        config = LMDRunConfig.fromJSON(args.alignConfig)
        if args.debug:
            config.useDebug = True
        else:
            startLogToFile('Align')
        runAligners(config, 99)
        done()

    # ? =========== align, multiple configs
    if args.alignConfigPath:
        if args.debug:
            pass
        else:
            startLogToFile('AlignMulti')
        args.configPath = args.alignConfigPath
        runConfigsMT(args, runAligners, 8)
        done()

    # ? =========== lumiFit, single config
    if args.lumifitConfig:
        config = LMDRunConfig.fromJSON(args.lumifitConfig)
        if args.debug:
            config.useDebug = True
        else:
            startLogToFile('LumiFit')
        if args.debug:
            config.useDebug = True
        runLumifit(config, 99)
        done()

    # ? =========== lumiFit, multiple configs
    if args.lumifitConfigPath:
        startLogToFile('LumiFitMulti')
        args.configPath = args.lumifitConfigPath
        runConfigsMT(args, runLumifit)
        done()

    # ? =========== extract Lumi, single config
    if args.extractLumiConfig:
        config = LMDRunConfig.fromJSON(args.extractLumiConfig)
        if args.debug:
            config.useDebug = True
        else:
            startLogToFile('ExtractLumi')
        if args.debug:
            config.useDebug = True
        runExtractLumi(config, 99)
        done()

    # ? =========== extract Lumi, multiple configs
    if args.extractLumiConfigPath:
        startLogToFile('ExtractLumi')
        args.configPath = args.extractLumiConfigPath
        runConfigsMT(args, runExtractLumi)
        done()

    # ? =========== simReco, single config
    if args.simulationConfig:
        config = LMDRunConfig.fromJSON(args.simulationConfig)
        if args.debug:
            config.useDebug = True
        else:
            startLogToFile('SimReco')
        if args.debug:
            config.useDebug = True
        runSimRecoLumi(config, 99)
        done()

    # ? =========== simReco, multiple configs
    if args.simulationConfigPath:
        startLogToFile('SimRecoMulti')
        args.configPath = args.simulationConfigPath
        runConfigsMT(args, runSimRecoLumi)
        done()

    # ? =========== combi run, single config
    if args.combiRunConfig:
        config = LMDRunConfig.fromJSON(args.combiRunConfig)
        if args.debug:
            config.useDebug = True
        else:
            startLogToFile('Combi')
        runCombi(config, 99)
        done()

    # ? =========== combi run, multiple configs
    if args.combiRunConfigPath:
        startLogToFile('Combi')
        args.configPath = args.combiRunConfigPath
        runConfigsMT(args, runCombi)
        done()

    # ? =========== half run, single config
    if args.halfRunConfig:
        config = LMDRunConfig.fromJSON(args.halfRunConfig)
        if args.debug:
            config.useDebug = True
        else:
            startLogToFile('FullRun')
        halfRun(config, 99)
        done()

    # ? =========== half run, multiple configs
    if args.halfRunConfigPath:
        startLogToFile('FullRunMulti')
        args.configPath = args.halfRunConfigPath
        runConfigsMT(args, halfRun)
        done()

    # ? =========== full job, single config
    if args.fullRunConfig:
        config = LMDRunConfig.fromJSON(args.fullRunConfig)
        if args.debug:
            config.useDebug = True
        else:
            startLogToFile('FullRun')
        runSimRecoLumiAlignRecoLumi(config, 99)
        done()

    # ? =========== full job, multiple configs
    if args.fullRunConfigPath:
        startLogToFile('FullRunMulti')
        args.configPath = args.fullRunConfigPath
        runConfigsMT(args, runSimRecoLumiAlignRecoLumi)
        done()

    # ? =========== full job sequence, must be directory
    # this one uses sequence files, which contain a list of files and the order in which to run them
    if args.fullRunConfigSequencePath:

        # layer 0: find sequence files

        # layer 1: read sequence files, execute runConfigs from them

        startLogToFile('FullRunSequence')
        args.configPath = args.fullRunConfigPath
        runConfigsMT(args, runSimRecoLumiAlignRecoLumi)
        done()

        # string from command line argument:
        # args.fullRunConfigSequencePath