#!/usr/bin/env python3

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

"""

import argparse
import concurrent
import datetime
import json
import os
import random
import sys

from argparse import RawTextHelpFormatter
from pathlib import Path

from alignment.alignerIP import alignerIP
from alignment.alignerSensors import alignerSensors
from concurrent.futures import ThreadPoolExecutor
from detail.LMDRunConfig import LMDRunConfig
from detail.LumiValLaTeXTable import LumiValLaTeXTable
from detail.logger import LMDrunLogger
from detail.simWrapper import simWrapper


def startLogToFile(functionName=None):

    if functionName is None:
        runSimLog = f'runLogs/runSim-{datetime.date.today()}-run{runNumber}.log'
        runSimLogErr = f'runLogs/runSim-{datetime.date.today()}-run{runNumber}-stderr.log'

    else:
        runSimLog = f'runLogs/runSim-{datetime.date.today()}-run{runNumber}-{functionName}.log'
        runSimLogErr = f'runLogs/runSim-{datetime.date.today()}-run{runNumber}-{functionName}-stderr.log'

    # redirect stdout/stderr to log files
    print(f'+++ starting new run and forking to background! this script will write all output to {runSimLog}\n')
    Path(runSimLog).parent.mkdir(exist_ok=True)
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
    # print(f'\nrunSimulations.py is done!\n')
    parser.exit(0)


# TODO: remove further code duplication in these functions!

# ? =========== functions that can be run by runAllConfigsMT

def runAligners(runConfig, threadID=None):

    print(f'Thread {threadID}: starting!')

    # create logger
    thislogger = LMDrunLogger(f'./runLogs/runLog-{datetime.date.today()}-run{runNumber}-Alignment-{runConfig.misalignType}-{runConfig.misalignFactor}-th{threadID}.txt')
    thislogger.log(runConfig.dump())

    # create alignerSensors, run

    # create alignerIP, run
    IPaligner = alignerIP.fromRunConfig(runConfig)
    IPaligner.logger = thislogger
    IPaligner.computeAlignmentMatrix()

    # create alignerCorridors, run

    print(f'Thread {threadID} done!')


def runExtractLumi(runConfig, threadID=None):

    print(f'Thread {threadID}: starting!')

    # create logger
    thislogger = LMDrunLogger(f'./runLogs/runLog-{datetime.date.today()}-run{runNumber}-ExtractLumi-{runConfig.misalignType}-{runConfig.misalignFactor}-th{threadID}.txt')
    thislogger.log(runConfig.dump())

    # create simWrapper from config
    prealignWrapper = simWrapper.fromRunConfig(runConfig)
    prealignWrapper.threadNumber = threadID
    prealignWrapper.logger = thislogger

    # run
    prealignWrapper.extractLumi()              # blocking

    print(f'Thread {threadID} done!')


def runLumifit(runConfig, threadID=None):

    print(f'Thread {threadID}: starting!')

    # create logger
    thislogger = LMDrunLogger(f'./runLogs/runLog-{datetime.date.today()}-run{runNumber}-LumiFit-{runConfig.misalignType}-{runConfig.misalignFactor}-th{threadID}.txt')
    thislogger.log(runConfig.dump())

    # create simWrapper from config
    prealignWrapper = simWrapper.fromRunConfig(runConfig)
    prealignWrapper.threadNumber = threadID
    prealignWrapper.logger = thislogger

    # run
    prealignWrapper.detLumi()                  # not blocking!
    prealignWrapper.waitForJobCompletion()     # waiting
    prealignWrapper.extractLumi()              # blocking

    print(f'Thread {threadID} done!')


def runSimRecoLumi(runConfig, threadID=None):

    print(f'Thread {threadID}: starting!')

    # create logger
    thislogger = LMDrunLogger(f'./runLogs/runLog-{datetime.date.today()}-run{runNumber}-SimReco-{runConfig.misalignType}-{runConfig.misalignFactor}-th{threadID}.txt')
    thislogger.log(runConfig.dump())

    # create simWrapper from config
    prealignWrapper = simWrapper.fromRunConfig(runConfig)
    prealignWrapper.threadNumber = threadID
    prealignWrapper.logger = thislogger

    # run all
    prealignWrapper.runSimulations()           # non blocking, so we have to wait
    prealignWrapper.waitForJobCompletion()     # blocking

    print(f'Thread {threadID} done!')


def runSimRecoLumiAlignRecoLumi(runConfig, threadID=None):

    print(f'Thread {threadID}: starting!')

    # start with a config, not a wrapper
    # add a filter, if the config assumes alignment correction, discard

    if runConfig.alignmentCorrection:
        print(f'Thread {threadID}: this runConfig contains a correction, ignoring')
        print(f'Thread {threadID}: done!')
        return

    # create logger
    thislogger = LMDrunLogger(f'./runLogs/runLog-{datetime.date.today()}-run{runNumber}-FullRun-{runConfig.misalignType}-{runConfig.misalignFactor}-th{threadID}.txt')

    # create simWrapper from config
    prealignWrapper = simWrapper.fromRunConfig(runConfig)
    prealignWrapper.threadNumber = threadID
    prealignWrapper.logger = thislogger

    # run all
    prealignWrapper.runSimulations()           # non blocking, so we have to wait
    prealignWrapper.waitForJobCompletion()     # blocking
    prealignWrapper.detLumi()                  # not blocking
    prealignWrapper.waitForJobCompletion()     # waiting
    prealignWrapper.extractLumi()              # blocking

    # then run aligner(s)
    IPaligner = alignerIP.fromRunConfig(runConfig)
    IPaligner.logger = thislogger
    IPaligner.computeAlignmentMatrix()

    # then, set align correction in config true and recreate simWrapper
    runConfig.alignmentCorrection = True

    postalignWrapper = simWrapper.fromRunConfig(runConfig)
    prealignWrapper.threadNumber = threadID
    postalignWrapper.logger = thislogger

    # re run reco steps and Lumi fit
    postalignWrapper.runSimulations()           # non blocking, so we have to wait
    postalignWrapper.waitForJobCompletion()     # blocking
    postalignWrapper.detLumi()                  # not blocking
    postalignWrapper.waitForJobCompletion()     # waiting
    postalignWrapper.extractLumi()              # blocking

    print(f'Thread {threadID} done!')


def showLumiFitResults(runConfigPath, threadID=None):

    # read all configs from path
    runConfigPath = Path(runConfigPath)
    configFiles = list(runConfigPath.glob('**/*.json'))

    configs = []
    for file in configFiles:
        configs.append(LMDRunConfig.fromJSON(file))

    if len(configs) == 0:
        print(f'No runConfig files found in {runConfigPath}!')

    table = LumiValLaTeXTable.fromConfigs(configs)
    # TODO: add a function to evaluate the config here somehow
    #table.addColumn('Header name', )
    table.show()

# ? =========== runAllConfigsMT that calls 'function' multithreaded


def runConfigsMT(args, function):

    configs = []
    # read all configs from path
    searchDir = Path(args.configPath)

    if args.recursive:
        configs = list(searchDir.glob('**/*.json'))
    else:
        configs = list(searchDir.glob('*.json'))

    if len(configs) == 0:
        print(f'No runConfig files found in {searchDir}. Exiting!')
        sys.exit(1)

    simConfigs = []

    # loop over all configs, create wrapper and run
    for configFile in configs:
        runConfig = LMDRunConfig.fromJSON(configFile)
        simConfigs.append(runConfig)

    maxThreads = min(len(simConfigs), 64)

    if args.debug:
        maxThreads = 1
        print(f'DEBUG: running in {maxThreads} threads!')

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
                executor.submit(function, config, index)

        print('waiting for all jobs...')
        executor.shutdown(wait=True)
    return


def createMultipleDefaultConfigs():
    # for now
    smallBatch = True

    if smallBatch:
        momenta = ['1.5', '15.0']
        misFactors = ['0.50', '1.00', '2.00']
        misTypes = ['sensors', 'box', 'identity']
    else:
        momenta = ['1.5', '4.06', '8.9', '11.91', '15.0']
        misFactors = ['0.01', '0.05', '0.10', '0.15', '0.20', '0.25', '0.50', '1.00', '2.00', '3.00', '5.00', '10.00']
        misTypes = ['aligned', 'sensors', 'box', 'combi', 'modules', 'identity', 'all']

    for misType in misTypes:
        for mom in momenta:
            for fac in misFactors:
                dest = Path('runConfigs') / Path(misType) / Path(mom) / Path(f'factor-{fac}.json')
                dest.parent.mkdir(parents=True, exist_ok=True)

                config = LMDRunConfig.minimalDefault()

                config.misalignFactor = fac
                config.misalignType = misType
                config.momentum = mom

                if Path(dest).exists():
                    print(f'ERROR! Config {dest} already exists, skipping!')
                    continue

                config.toJSON(dest)

    # regenerate missing fields
    targetDir = Path('runConfigs')
    configs = [x for x in targetDir.glob('**/*.json') if x.is_file()]
    for fileName in configs:
        conf = LMDRunConfig.fromJSON(fileName)
        conf.generateMatrixNames()
        conf.toJSON(fileName)


# ? =========== main user interface

if __name__ == "__main__":

    # if os.fork():
    #     sys.exit()

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=RawTextHelpFormatter)

    parser.add_argument('-a', metavar='--alignConfig', type=str, dest='alignConfig', help='find all alignment matrices (IP, corridor, sensors) for runConfig')
    parser.add_argument('-A', metavar='--alignConfigPath', type=str, dest='alignConfigPath', help='same as -a, but for all Configs in specified path')

    parser.add_argument('-f', metavar='--fullRunConfig', type=str, dest='fullRunConfig', help='Do a full run (simulate mc data, find alignment, determine Luminosity)')
    parser.add_argument('-F', metavar='--fullRunConfigPath', type=str, dest='fullRunConfigPath', help='same as -f, but for all Configs in specified path')

    parser.add_argument('-l', metavar='--lumifitConfig', type=str, dest='lumifitConfig', help='determine Luminosity for runConfig')
    parser.add_argument('-L', metavar='--lumifitConfigPath', type=str, dest='lumifitConfigPath', help='same as -l, but for all Configs in specified path')

    parser.add_argument('-el', metavar='--extractLumiConfig', type=str, dest='extractLumiConfig', help='extract Luminosity for runConfig')
    parser.add_argument('-EL', metavar='--extractLumiConfigPath', type=str, dest='extractLumiConfigPath', help='same as -el, but for all Configs in specified path')

    parser.add_argument('-s', metavar='--simulationConfig', type=str, dest='simulationConfig', help='run simulation and reconstruction for runConfig')
    parser.add_argument('-S', metavar='--simulationConfigPath', type=str, dest='simulationConfigPath', help='same as -s, but for all Configs in specified path')

    #parser.add_argument('-v', metavar='--fitValuesConfig', type=str, dest='fitValuesConfig', help='display reco_ip and lumi_vals for select runConfig (if found)')
    parser.add_argument('-V', metavar='--fitValuesConfigPath', type=str, dest='fitValuesConfigPath', help='display reco_ip and lumi_vals for all runConfigs in path')

    parser.add_argument('-r', action='store_true', dest='recursive', help='use with any config Path option to scan paths recursively')

    parser.add_argument('-d', action='store_true', dest='makeDefault', help='make a single default LMDRunConfig and save it to runConfigs/identity-1.00.json')
    parser.add_argument('-D', action='store_true', dest='makeMultipleDefaults', help='make multiple example LMDRunConfigs')
    parser.add_argument('--debug', action='store_true', dest='debug', help='run single threaded, more verbose output, submit jobs to devel queue')
    parser.add_argument('--updateRunConfigs', dest='updateRunConfigs', help='read all configs in ./runConfig, recreate the matrix file paths and store them.')
    parser.add_argument('--test', action='store_true', dest='test', help='internal test function')

    try:
        args = parser.parse_args()
    except:
        parser.print_help()
        parser.exit(1)

    if len(sys.argv) < 2:
        parser.print_help()
        parser.exit(1)

    # random number to identify runs
    global runNumber
    runNumber = random.randint(0, 1000000)

    # ? =========== helper functions
    if args.makeDefault:
        dest = Path('runConfigs/identity-1.00.json')
        print(f'saving default config to {dest}')
        LMDRunConfig.minimalDefault().toJSON(dest)
        done()

    # ? =========== helper functions
    if args.makeMultipleDefaults:
        createMultipleDefaultConfigs()
        done()

    if args.updateRunConfigs:

        targetDir = Path(args.updateRunConfigs).absolute()
        print(f'reading all files from {targetDir} and regenerating settings...')

        configs = [x for x in targetDir.glob('**/*.json') if x.is_file()]

        for fileName in configs:
            conf = LMDRunConfig.fromJSON(fileName)
            conf.updateEnvPaths()
            conf.generateMatrixNames()
            conf.toJSON(fileName)
        done()

    if args.test:
        print(f'Testing...')
        runConfig = LMDRunConfig.fromJSON('runConfigs/sensors/1.5/factor-1.00.json')
        if args.debug:
            print(f'\n\n!!! Running in debug mode !!!\n\n')
            runConfig.useDebug=True

        sensorAligner = alignerSensors.fromRunConfig(runConfig)
        sensorAligner.sortPairs()
        sensorAligner.findMatrices()
        # TODO: save matrices to disk
        sensorAligner.histCompareResults()
        sensorAligner.combineAlignmentMatrices()
        done()

    if args.debug:
        print(f'\n\n!!! Running in debug mode !!!\n\n')

    # # ? =========== lumi fit results, single config
    # if args.fitValuesConfig:
    #     config = LMDRunConfig.fromJSON(args.fitValuesConfig)
    #     if args.debug:
    #         config.useDebug = True
    #     showLumiFitResults(config, 99)
    #     done()

    # ? =========== lumi fit results, multiple configs
    if args.fitValuesConfigPath:
        #args.configPath = args.fitValuesConfigPath
        showLumiFitResults(args.fitValuesConfigPath)
        done()

    #! ---------------------- logging goes to file

    if os.fork():
        sys.exit()

    # ? =========== align, single config
    if args.alignConfig:
        startLogToFile('Align')
        config = LMDRunConfig.fromJSON(args.alignConfig)
        if args.debug:
            config.useDebug = True
        runAligners(config, 99)
        done()

    # ? =========== align, multiple configs
    if args.alignConfigPath:
        startLogToFile('AlignMulti')
        args.configPath = args.alignConfigPath
        runConfigsMT(args, runAligners)
        done()

    # ? =========== lumiFit, single config
    if args.lumifitConfig:
        startLogToFile('LumiFit')
        config = LMDRunConfig.fromJSON(args.lumifitConfig)
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
        startLogToFile('ExtractLumi')
        config = LMDRunConfig.fromJSON(args.extractLumiConfig)
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
        startLogToFile('SimReco')
        config = LMDRunConfig.fromJSON(args.simulationConfig)
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

    # ? =========== full job, single config
    if args.fullRunConfig:
        startLogToFile('FullRun')
        config = LMDRunConfig.fromJSON(args.fullRunConfig)
        if args.debug:
            config.useDebug = True
        runSimRecoLumiAlignRecoLumi(config, 99)
        done()

    # ? =========== full job, multiple configs
    if args.fullRunConfigPath:
        startLogToFile('FullRunMulti')
        args.configPath = args.fullRunConfigPath
        runConfigsMT(args, runSimRecoLumiAlignRecoLumi)
        done()
