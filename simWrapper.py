#!/usr/bin/env python3

import argparse
import re
import os
import pwd  # to get current user
import sys
import time
import subprocess
from pathlib import Path
from detail.LMDRunConfig import LMDRunConfig

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

TODO:
- remember to delete everything after mc generation for new run

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


class simWrapper():

    # empty constructor
    def __init__(self):
        self.cwd = Path.cwd()
        lmdFitEnv = 'LMDFIT_BUILD_PATH'
        simDirEnv = 'LMDFIT_DATA_DIR'
        pndRootDir = 'VMCWORKDIR'
        self.cwd = str(Path.cwd())
        self.currentJobID = None
        try:
            self.__lumiFitPath = str(Path(os.environ[lmdFitEnv]).parent)
            self.__simDataPath = os.environ[simDirEnv]
            self.__pandaRootDir = os.environ[pndRootDir]
        except:
            print("can't find LuminosityFit installation, PandaRoot installation or Data_Dir!")
            print(f"please set {lmdFitEnv}, {pndRootDir} and {simDirEnv}!")
            sys.exit(1)

    @classmethod
    def fromRunConfig(cls, LMDRunConfig) -> 'simWrapper':
        wrapper = cls()
        wrapper.setRunConfig(LMDRunConfig)
        return wrapper

    def dump(self):
        print(f'\n\n')
        print(f'------------------------------')
        print(f'DEBUG OUTPUT for SimWrapper:\n')
        print(f'CWD: {self.cwd}')
        print(f'------------------------------')
        print(f'\n\n')

    def setRunConfig(self, LMDRunConfig):
        self.__config = LMDRunConfig

    def runSimulations(self):
        if self.__config is None:
            print(f'please set run config first!')

        scriptsPath = self.__lumiFitPath / Path('scripts')
        command = scriptsPath / Path('doSimulationReconstruction.py')   # non-blocking!
        nTrks = self.__config.trksNum
        nJobs = self.__config.jobsNum
        mom = self.__config.momentum
        dpm = 'dpm_elastic'

        almatp = '--alignment_matrices_path'
        almatv = str(self.__config.pathAlMatrix())

        mismatp = '--misalignment_matrices_path'
        mismatv = str(self.__config.pathMisMatrix())

        # we have to change the directory here since some script paths in LuminosityFit are relative.
        print(f'DEBUG: chaning cwd to {scriptsPath}')
        os.chdir(scriptsPath)

        # no misalignment nor correction
        if not self.__config.misaligned and not self.__config.alignmentCorrection:
            returnVal = subprocess.check_output((command, nTrks, nJobs, mom, dpm))

        # run only misaligned, no correction
        if self.__config.misaligned and not self.__config.alignmentCorrection:
            returnVal = subprocess.check_output((command, nTrks, nJobs, mom, dpm, mismatp, mismatv))

        # run only correction
        if not self.__config.misaligned and self.__config.alignmentCorrection:
            returnVal = subprocess.check_output((command, nTrks, nJobs, mom, dpm, almatp, almatv))

        # both misalignment and correction:
        if self.__config.misaligned and self.__config.alignmentCorrection:
            returnVal = subprocess.check_output((command, nTrks, nJobs, mom, dpm, mismatp, mismatv, almatp, almatv))

        returnVal = returnVal.decode(sys.stdout.encoding)

        print(f'RETURNED:\n{returnVal}')

        match = re.search(r'Submitted batch job (\d+)', returnVal)
        if match:
            jobID = match.groups()[0]
            print(f'FOUND JOB ID: {jobID}')
            self.currentJobID = jobID
        else:
            print('can\'t parse job ID from output!')

    def waitForJobCompletion(self):
        if self.__config is None:
            print(f'please set run config first!')

        while True:
            # see https://stackoverflow.com/a/2899055
            user = pwd.getpwuid(os.getuid())[0]
            print(f'you are {user}, waiting on job {self.currentJobID}')

            squeueOutput = subprocess.check_output(('squeue', '-u', user)).decode(sys.stdout.encoding)
            outputLines = squeueOutput.splitlines()
            foundJobs = 0
            for line in outputLines:
                match = re.search(r'^\s+(\d+)', line)
                if match:
                    found = match.groups()[0]
                    if found == str(self.currentJobID):
                        foundJobs += 1

            # no jobs found? then we can exit
            if foundJobs == 0:
                print(f'no jobs running, continuing...')
                self.currentJobID = None
                return

            print(f'{foundJobs} jobs  running...')
            time.sleep(60)

    def extractLumi(self):
        if self.__config is None:
            print(f'please set run config first!')

        #absPath = self.__config.__path
        #print(f'path: {absPath}')
        print(f'Running ./extractLuminosity...')
        binPath = self.__lumiFitPath / Path('build') / Path('bin')
        command = binPath / Path('extractLuminosity')
        dataPath = self.__config.pathTrksQA()

        if dataPath:
            subprocess.check_output((command, dataPath))

        else:
            print(f'can\'t determine path!')

    # the lumi fit scripts are blocking!
    def detLumi(self):
        if self.__config is None:
            print(f'please set run config first!')

        absPath = self.__config.pathTrksQA()
        print(f'DEBUG: determining Luminosity of the data set found here:\n{absPath}')

        scriptsPath = self.__lumiFitPath / Path('scripts')
        command = scriptsPath / Path('determineLuminosity.py')
        argP = '--base_output_data_dir'
        argPval = absPath

        # see runSimulations()
        # we have to change the directory here since some script paths in LuminosityFit are relative.
        print(f'DEBUG: chaning cwd to {scriptsPath}')
        os.chdir(scriptsPath)

        # don't close file desciptor, this call will block until lumi is determined!
        subprocess.check_output((command, argP, argPval))

        # returnVal = returnVal.decode(sys.stdout.encoding)

        # print(f'RETURNED:\n{returnVal}')
        # match = re.search(r'Submitted batch job (\d+)', returnVal)
        # if match:
        #     jobID = match.groups()[0]
        #     print(f'FOUND JOB ID: {jobID}')
        #     self.currentJobID = jobID
        # else:
        #     print('can\'t parse job ID from output!')


def runAllConfigs(args):
    configs = []
    # read all configs from path
    searchDir = Path(args.configPath)
    configs = list(searchDir.glob('*.json'))
    simWrappers = []

    # loop over all configs, create wrapper and run
    for configFile in configs:
        runConfig = LMDRunConfig.fromJSON(configFile)
        simWrappers.append(simWrapper.fromRunConfig(runConfig))

    # TODO: thread pool for wrappers so they can:
    # run concurrently. they mostly wait for compute nodes anyway.

    # for now, use single thread:
    for wrapper in simWrappers:
        wrapper.runSimulations()
        wrapper.waitForJobCompletion()
        wrapper.detLumi()
        wrapper.waitForJobCompletion()
        wrapper.extractLumi()

        # TODO: add alignment here and rerun simulations! use the runSteps values from the runConfig


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

    parser.add_argument('--test', action='store_true', help='internal test function')
    parser.add_argument('-c', metavar='--config', type=str, dest='configFile', help='LMDRunConfig file (e.g. "runConfigs/box10.json")')
    parser.add_argument('-D', action='store_true', help='make a single default LMDRunConfig and save it to runConfigs/identity-1.00.json')
    # this is the real magic:
    parser.add_argument('-C', metavar='--configPath', type=str, dest='configPath', help='path to multiple LMDRunConfig files. ALL files in this path will be run as job!')

    try:
        args = parser.parse_args()
    except:
        parser.exit(1)

    # run single config
    if args.configFile:
        wrapper = simWrapper.fromRunConfig(LMDRunConfig.fromJSON(args.configFile))
        wrapper.runSimulations()
        sys.exit(0)

    # run multiple configs
    if args.configPath:
        runAllConfigs(args)
        sys.exit(0)

    if args.test:
        wrapper = simWrapper.fromRunConfig(LMDRunConfig.minimalDefault())
        wrapper.currentJobID = 4998523
        # wrapper.waitForJobCompletion()
        testMiniRun()

        wrapper.extractLumi()
        sys.exit(0)

        testRunConfigParse()
        LMDRunConfig.minimalDefault().dump()
        sys.exit(0)

    if args.D:
        dest = Path('runConfigs/identity-1.00.json')
        print(f'saving default config to {dest}')
        LMDRunConfig.minimalDefault().toJSON(dest)
