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
TODO: these steps!
- run my aligners
- rerun ./doSimulationReconstruction with correct parameters
- rerun ./determineLuminosity
- rerun ./extractLuminosity


"""

import argparse
import concurrent

from pathlib import Path

from alignment.alignerIP import alignerIP
from concurrent.futures import ThreadPoolExecutor
from detail.LMDRunConfig import LMDRunConfig
from detail.logger import LMDrunLogger
from detail.simWrapper import simWrapper

def runMultipleTasks(wrapper, time):

    # start with a config, not a wrapper
    # config knows all paramters, but set align correction to false
    # then run aligner(s)
    # then, set align correction in config true
    # re run reco steps and Lumi fit

    wrapper.idle(time)
    print('again!')
    wrapper.idle(time)


def idleTwoByTwo():
    # TODO: create two simWrappers and have them both idle two times!
    wrapperOne = simWrapper.fromRunConfig(LMDRunConfig.minimalDefault())
    wrapperTwo = simWrapper.fromRunConfig(LMDRunConfig.minimalDefault())
    wrapperThree = simWrapper.fromRunConfig(LMDRunConfig.minimalDefault())

    simWrappers = [wrapperOne, wrapperTwo, wrapperThree]

    maxThreads = 64

    with concurrent.futures.ProcessPoolExecutor(max_workers=maxThreads) as executor:
        for index, wrapper in enumerate(simWrappers):
            wrapper.threadNumber = index
            executor.submit(runMultipleTasks, wrapper, 1)

def runAllConfigs(args):
    configs = []
    # read all configs from path
    searchDir = Path(args.configPath)

    # TODO: maybe add a recursive flag
    configs = list(searchDir.glob('**/*.json'))
    simWrappers = []

    # loop over all configs, create wrapper and run
    for configFile in configs:
        runConfig = LMDRunConfig.fromJSON(configFile)
        simWrappers.append(simWrapper.fromRunConfig(runConfig))

    maxThreads = min(len(simWrappers), 64)

    if args.debug:
        maxThreads = 1
        print(f'DEBUG: running in {maxThreads} threads!')

    # run concurrently in maximum 64 threads. they mostly wait for compute nodes anyway.
    # we use a process pool instead of a thread pool because the individual interpreters are working on different cwd's.
    with concurrent.futures.ProcessPoolExecutor(max_workers=maxThreads) as executor:
        # Start the load operations and mark each future with its URL
        for index, wrapper in enumerate(simWrappers):
            wrapper.threadNumber = index
            executor.submit(wrapper.runAll)

    print(f'all jobs for config files completed!')
    return

def runAligners(args):
    # create alignerIP, run

    IPaligner = alignerIP.fromRunConfig(LMDRunConfig.fromJSON(args.alignConfig))
    IPaligner.computeAlignmentMatrix()
    
    # create alignerCorrdiros, run

    # create alignerSensors, run
    pass

if __name__ == "__main__":
    print('greetings, human')
    parser = argparse.ArgumentParser()

    
    parser.add_argument('-a', metavar='--alignConfig', type=str, dest='alignConfig', help='try to find all alignment matrices (IP, corridor, sensors) for a single runConfig without running the simulations/fits')
    parser.add_argument('-A', metavar='--alignPath', type=str, dest='alignPath', help='path to multiple LMDRunConfig files. ALL runConfig files in this path will be read and their alignment matrices determined!')
    parser.add_argument('-d', action='store_true', dest='makeDefault', help='make a single default LMDRunConfig and save it to runConfigs/identity-1.00.json')
    
    parser.add_argument('-f', metavar='--fullRunConfig', type=str, dest='fullRunConfig', help='Do a full run (simulate mc data, find alignment, determine Luminosity)')
    #parser.add_argument('-F', metavar='--fullConfigPath', type=str, dest='fullConfigPath', help='path to multiple LMDRunConfig files. ALL files in this path will be run as COMPLETE job, mc data, lumi and alignment!')
    
    parser.add_argument('-r', metavar='--runConfig', type=str, dest='runConfig', help='LMDRunConfig file (e.g. "runConfigs/box10.json")')
    parser.add_argument('-R', metavar='--configPath', type=str, dest='configPath', help='path to multiple LMDRunConfig files. ALL files in this path will be run as COMPLETE job, mc data, lumi and alignment!')
    
    parser.add_argument('--debug', action='store_true', help='run single threaded, more verbose output')
    parser.add_argument('--regenerateMatrixPaths', dest='reGenMatPath', help='read all configs in ./runConfig, recreate the matrix file paths and store them!')
    parser.add_argument('--test', action='store_true', dest='test', help='internal test function')

    try:
        args = parser.parse_args()
    except:
        parser.exit(1)

    #? =========== run align jobs (on frontend) 
    if args.alignConfig:
        print('running all aligners')
        runAligners(args)
        print('all done')
        parser.exit(0)

    #? =========== run single config
    if args.runConfig:

        # TODO: further cases selection, do we want to run simulations, determine Luminosity or find Alignment?
        # TODO: add another flag for these options
        if False:
            wrapper = simWrapper.fromRunConfig(LMDRunConfig.fromJSON(args.configFile))
            wrapper.runSimulations()
            parser.exit(0)
        else:
            aligner = alignerIP.fromRunConfig(LMDRunConfig.fromJSON(args.configFile))
            aligner.computeAlignmentMatrix()
            parser.exit(0)

    #? =========== run multiple configs
    if args.configPath:
        runAllConfigs(args)
        parser.exit(0)

    #? =========== run full chain, simulate mc data, find alignment, determine Luminosity
    if args.fullRunConfig:
        # TODO: implement
        parser.exit(0)


    #? =========== helper functions
    if args.makeDefault:
        dest = Path('runConfigs/identity-1.00.json')
        print(f'saving default config to {dest}')
        LMDRunConfig.minimalDefault().toJSON(dest)
        parser.exit(0)

    if args.reGenMatPath:

        print(f'reading all files from {args.reGenMatPath} and recreating matrix file paths...')

        targetDir = Path('runConfigs')
        configs = [x for x in targetDir.glob('**/*') if x.is_file()]

        for fileName in configs:
            conf = LMDRunConfig.fromJSON(fileName)
            conf.generateMatrixNames()
            conf.toJSON(fileName)
        
        print('all done!')
        parser.exit(0)

    if args.test:
        print(f'idlig two by two')
        idleTwoByTwo()
        parser.exit(0)

    parser.print_help()
