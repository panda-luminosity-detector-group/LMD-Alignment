#!/usr/bin/env python3

"""
this script handles all simulation related abstractions.

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
import os, sys      # to fork

from pathlib import Path

from alignment.alignerIP import alignerIP
from concurrent.futures import ThreadPoolExecutor
from detail.LMDRunConfig import LMDRunConfig
from detail.logger import LMDrunLogger
from detail.simWrapper import simWrapper


def done():
    print(f'\n\n====================================\n')
    print(f'       all tasks completed!           ')
    print(f'\n====================================\n\n')
    # cleanup, probably not neccessary
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    #print(f'\nrunSimulations.py is done!\n')
    parser.exit(0)


# TODO: remove further code duplication in these functions!

# ? =========== functions that can be run by runAllConfigsMT

def runAligners(runConfig, threadID=None):

    print(f'Thread {threadID}: starting!')

    # create logger
    thislogger = LMDrunLogger()

    # create alignerIP, run
    IPaligner = alignerIP.fromRunConfig(runConfig)
    IPaligner.logger = thislogger
    IPaligner.computeAlignmentMatrix()

    # create alignerCorridors, run

    # create alignerSensors, run

    print(f'Thread {threadID} done!')


def runLumifit(runConfig, threadID=None):

    print(f'Thread {threadID}: starting!')

    # create logger
    thislogger = LMDrunLogger()

    # create simWrapper from config
    prealignWrapper = simWrapper.fromRunConfig(runConfig)
    prealignWrapper.threadID = threadID
    prealignWrapper.logger = thislogger

    # run
    prealignWrapper.detLumi()                  # blocking
    prealignWrapper.extractLumi()              # blocking

    # save log, increment log number if log from that day is already present
    i = 0
    while Path(f'./runLogs/runLog-{datetime.date.today()}-nr{i}-i{threadID}.txt').exists():
        i += 1

    logfilename = Path(f'./runLogs/runLog-{datetime.date.today()}-run{i}-thread{threadID}.txt')
    thislogger.save(logfilename)
    print(f'Thread {threadID} done!')


def runSimRecoLumi(runConfig, threadID=None):

    print(f'Thread {threadID}: starting!')

    # create logger
    thislogger = LMDrunLogger()

    # create simWrapper from config
    prealignWrapper = simWrapper.fromRunConfig(runConfig)
    prealignWrapper.threadID = threadID
    prealignWrapper.logger = thislogger

    # run all
    prealignWrapper.runSimulations()           # non blocking, so we have to wait
    prealignWrapper.waitForJobCompletion()     # blocking

    # save log, increment log number if log from that day is already present
    i = 0
    while Path(f'./runLogs/runLog-{datetime.date.today()}-nr{i}-i{threadID}.txt').exists():
        i += 1

    logfilename = Path(f'./runLogs/runLog-{datetime.date.today()}-run{i}-thread{threadID}.txt')
    thislogger.save(logfilename)
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
    thislogger = LMDrunLogger()

    # create simWrapper from config
    prealignWrapper = simWrapper.fromRunConfig(runConfig)
    prealignWrapper.threadID = threadID
    prealignWrapper.logger = thislogger

    # run all
    prealignWrapper.runSimulations()           # non blocking, so we have to wait
    prealignWrapper.waitForJobCompletion()     # blocking
    prealignWrapper.detLumi()                  # blocking
    prealignWrapper.extractLumi()              # blocking

    # then run aligner(s)
    IPaligner = alignerIP.fromRunConfig(runConfig)
    IPaligner.logger = thislogger
    IPaligner.computeAlignmentMatrix()

    # then, set align correction in config true and recreate simWrapper
    runConfig.alignmentCorrection = True

    postalignWrapper = simWrapper.fromRunConfig(runConfig)
    prealignWrapper.threadID = threadID
    postalignWrapper.logger = thislogger

    # re run reco steps and Lumi fit
    postalignWrapper.runSimulations()           # non blocking, so we have to wait
    postalignWrapper.waitForJobCompletion()     # blocking
    postalignWrapper.detLumi()                  # blocking
    postalignWrapper.extractLumi()              # blocking

    # save log, increment log number if log from that day is already present
    i = 0
    while Path(f'./runLogs/runLog-{datetime.date.today()}-nr{i}-i{threadID}.txt').exists():
        i += 1

    logfilename = Path(f'./runLogs/runLog-{datetime.date.today()}-run{i}-thread{threadID}.txt')
    thislogger.save(logfilename)
    print(f'Thread {threadID} done!')

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
        print(f'No runConfig files found in {searchDir}!')

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

# ? =========== main user interface


if __name__ == "__main__":

    if os.fork():
        sys.exit()

    parser = argparse.ArgumentParser()

    parser.add_argument('-a', metavar='--alignConfig', type=str, dest='alignConfig', help='find all alignment matrices (IP, corridor, sensors) for runConfig')
    parser.add_argument('-A', metavar='--alignConfigPath', type=str, dest='alignConfigPath', help='same as -a, but for all Configs in specified path')

    parser.add_argument('-f', metavar='--fullRunConfig', type=str, dest='fullRunConfig', help='Do a full run (simulate mc data, find alignment, determine Luminosity)')
    parser.add_argument('-F', metavar='--fullRunConfigPath', type=str, dest='fullRunConfigPath', help='same as -f, but for all Configs in specified path')

    parser.add_argument('-l', metavar='--lumifitConfig', type=str, dest='lumifitConfig', help='determine Luminosity for runConfig')
    parser.add_argument('-L', metavar='--lumifitConfigPath', type=str, dest='lumifitConfigPath', help='same as -f, but for all Configs in specified path')

    parser.add_argument('-s', metavar='--simulationConfig', type=str, dest='simulationConfig', help='run simulation and reconstruction for runConfig')
    parser.add_argument('-S', metavar='--simulationConfigPath', type=str, dest='simulationConfigPath', help='same as -s, but for all Configs in specified path')

    parser.add_argument('-r', action='store_true', dest='recursive', help='use with any config Path option to scan paths recursively')

    parser.add_argument('-d', action='store_true', dest='makeDefault', help='make a single default LMDRunConfig and save it to runConfigs/identity-1.00.json')
    parser.add_argument('--debug', action='store_true', dest='debug', help='run single threaded, more verbose output, submit jobs to devel queue')
    parser.add_argument('--updateRunConfigs', dest='updateRunConfigs', help='read all configs in ./runConfig, recreate the matrix file paths and store them!')
    parser.add_argument('--test', action='store_true', dest='test', help='internal test function')

    try:
        args = parser.parse_args()
    except:
        parser.exit(1)

    runSimLog = f'runLogs/simulation-{datetime.date.today()}.log'
    runSimLogErr = f'runLogs/simulation-{datetime.date.today()}-stderr.log'

    print(f'+++ starting new run and forking to background! this script will write all output to {runSimLog}\n')
    sys.stdout = open(runSimLog, 'a')
    sys.stderr = open(runSimLogErr, 'a')
    print(f'+++ starting new run at {datetime.datetime.now()}:\n')

    if args.debug:
        print(f'\n\n!!! Running in debug mode !!!\n\n')

    # ? =========== align, single config
    if args.alignConfig:
        config = LMDRunConfig.fromJSON(args.alignConfig)
        if args.debug:
            config.useDebug = True
        runAligners(config, 99)
        done()

    # ? =========== align, multiple configs
    if args.alignConfigPath:
        args.configPath = args.alignConfigPath
        runConfigsMT(args, runAligners)
        done()

    # ? =========== lumiFit, single config
    if args.lumifitConfig:
        config = LMDRunConfig.fromJSON(args.lumifitConfig)
        if args.debug:
            config.useDebug = True
        runLumifit(config, 99)
        done()

    # ? =========== lumiFit, multiple configs
    if args.lumifitConfigPath:
        args.configPath = args.lumifitConfigPath
        runConfigsMT(args, runLumifit)
        done()

    # ? =========== simReco, single config
    if args.simulationConfig:
        config = LMDRunConfig.fromJSON(args.simulationConfig)
        if args.debug:
            config.useDebug = True
        runSimRecoLumi(config, 99)
        done()

    # ? =========== simReco, multiple configs
    if args.simulationConfigPath:
        args.configPath = args.simulationConfigPath
        runConfigsMT(args, runSimRecoLumi)
        done()

    # ? =========== full job, single config
    if args.fullRunConfig:
        config = LMDRunConfig.fromJSON(args.fullRunConfig)
        if args.debug:
            config.useDebug = True
        runSimRecoLumiAlignRecoLumi(config, 99)
        done()

    # ? =========== full job, multiple configs
    if args.fullRunConfigPath:
        args.configPath = args.fullRunConfigPath
        runConfigsMT(args, runSimRecoLumiAlignRecoLumi)
        done()

    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

    # ? =========== helper functions
    if args.makeDefault:
        dest = Path('runConfigs/identity-1.00.json')
        print(f'saving default config to {dest}')
        LMDRunConfig.minimalDefault().toJSON(dest)
        done()

    if args.updateRunConfigs:

        targetDir = Path(args.updateRunConfigs).absolute()
        print(f'reading all files from {targetDir} and regenerating settings...')

        configs = [x for x in targetDir.glob('**/*.json') if x.is_file()]

        for fileName in configs:
            conf = LMDRunConfig.fromJSON(fileName)
            conf.generateMatrixNames()
            conf.toJSON(fileName)
        done()

    if args.test:
        print(f'idlig two by two')
        done()

    parser.print_help()
