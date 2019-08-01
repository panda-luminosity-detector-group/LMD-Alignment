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
from detail.simWrapper import simWrapper


def runAllConfigs(args):
    configs = []
    # read all configs from path
    searchDir = Path(args.configPath)

    # TODO: make recursive
    configs = list(searchDir.glob('*.json'))
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

    # create alignerCorrdiros, run

    # create alignerSensors, run
    pass

def testRunConfigParse():
    print(f'testing parser!')
    path = '/lustre/miifs05/scratch/him-specf/paluma/roklasen/LumiFit/plab_1.5GeV/dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/geo_misalignmentmisMat-box-10.00/100000/1-500_uncut/aligned-alMat-box-10.00'
    config = LMDRunConfig.fromPath(path)
    # config.dump()
    # config.toJSON('runConfigs/box3.json')

    #config = LMDRunConfig.fromJSON('2.json')
    config.dump()


def testMiniRun():
    config = LMDRunConfig()
    config.misalignType = 'box'
    config.misalignFactor = '5.00'
    config.momentum = '1.5'
    config.generateMatrixNames()
    # config.toJSON('runConfigs/box10.json')
    config.dump()


if __name__ == "__main__":
    print('greetings, human')
    parser = argparse.ArgumentParser()

    
    parser.add_argument('-a', metavar='--align', type=str, dest='align', help='try to find all alignment matrices (IP, corridor, sensors) for a single runConfig without running the simulations/fits')
    # TODO: rename this next one, because it will RUN a job, not just ... config
    parser.add_argument('-c', metavar='--config', type=str, dest='configFile', help='LMDRunConfig file (e.g. "runConfigs/box10.json")')
    parser.add_argument('-C', metavar='--configPath', type=str, dest='configPath', help='path to multiple LMDRunConfig files. ALL files in this path will be run as job!')
    parser.add_argument('--debug', action='store_true', help='run single threaded, more verbose output')
    parser.add_argument('-D', action='store_true', dest='makeDefault', help='make a single default LMDRunConfig and save it to runConfigs/identity-1.00.json')
    parser.add_argument('--test', action='store_true', help='internal test function')

    try:
        args = parser.parse_args()
    except:
        parser.exit(1)

    if args.align:
        print('running all aligners')
        runAligners(args)
        print('all done')
        parser.exit(0)

    # run single config
    if args.configFile:

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

    # run multiple configs
    if args.configPath:
        runAllConfigs(args)
        parser.exit(0)

    if args.makeDefault:
        dest = Path('runConfigs/identity-1.00.json')
        print(f'saving default config to {dest}')
        LMDRunConfig.minimalDefault().toJSON(dest)
        parser.exit(0)

    if args.test:
        wrapper = simWrapper.fromRunConfig(LMDRunConfig.minimalDefault())
        wrapper.currentJobID = 4998523
        # wrapper.waitForJobCompletion()
        testMiniRun()

        wrapper.extractLumi()
        parser.exit(0)

        testRunConfigParse()
        LMDRunConfig.minimalDefault().dump()
        parser.exit(0)

    parser.print_help()