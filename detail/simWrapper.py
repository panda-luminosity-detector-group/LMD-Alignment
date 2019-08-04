#!/usr/bin/env python3

"""
LMD Simulation Wrapper

Depends on:
- FairRoot
- PandaRoot
- LuminosityFitFramework
"""

import datetime
import json
import os
import re
import pwd  # to get current user
import sys
import time
import subprocess

from pathlib import Path
from detail.LMDRunConfig import LMDRunConfig

"""
Simulation Wrapper. This one handles simulations on Hinster2, interfaces with LuminosityFit Framework etc.

FIXME:  apparently the lumi fit framework sometimes fails when re-determining the lumi of an already fully processed directory
"""


class simWrapper:

    # empty constructor
    def __init__(self):
        self.cwd = Path.cwd()
        lmdFitEnv = 'LMDFIT_BUILD_PATH'
        simDirEnv = 'LMDFIT_DATA_DIR'
        pndRootDir = 'VMCWORKDIR'
        self.cwd = str(Path.cwd())
        self.currentJobID = None
        self.threadNumber = None
        self.logger = None
        self.__debug = True
        try:
            self.__lumiFitPath = str(Path(os.environ[lmdFitEnv]).parent)
            self.__simDataPath = os.environ[simDirEnv]
            self.__pandaRootDir = os.environ[pndRootDir]
        except:
            self.logger.log("can't find LuminosityFit installation, PandaRoot installation or Data_Dir!\n")
            self.logger.log(f"please set {lmdFitEnv}, {pndRootDir} and {simDirEnv}!\n")
            sys.exit(1)

    @classmethod
    def fromRunConfig(cls, LMDRunConfig) -> 'simWrapper':
        wrapper = cls()
        wrapper.setRunConfig(LMDRunConfig)
        return wrapper

    def setRunConfig(self, LMDRunConfig):
        self.__config = LMDRunConfig

    def runSimulations(self):
        if self.__config is None:
            self.logger.log(f'please set run config first!')

        self.logger.log(f'\n\n========= Running ./doSimulationReconstruction.\n')
        print(f'\n\n========= Running ./doSimulationReconstruction, please wait.\n')

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
        self.logger.log(f'DEBUG: changing cwd to {scriptsPath}')
        os.chdir(scriptsPath)

        if self.__debug:
            self.logger.log(f'DEBUG: dumping current runConfig!')
            self.logger.log(self.__config.dump() + '')

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

        self.logger.log(f'\n============ RETURNED:\n{returnVal}\n============ END OF RETURN\n')
        self.logger.log(f'\n\n========= Done!.\n')
        print(f'\n\n========= Jobs submitted, waiting for them to finish...\n')

        match = re.search(r'Submitted batch job (\d+)', returnVal)
        if match:
            jobID = match.groups()[0]
            self.logger.log(f'FOUND JOB ID: {jobID}')
            self.currentJobID = jobID
        else:
            self.logger.log('can\'t parse job ID from output!')

    def waitForJobCompletion(self):
        if self.__config is None:
            self.logger.log(f'please set run config first!')

        if not self.currentJobID:
            self.logger.log(f'can\'t wait for jobs, this simWrapper doesn\'t know that jobs to wait for!')
            return

        self.logger.log(f'\n\n========= Waiting for jobs...\n')
        print(f'\n\n========= Waiting for jobs...\n')

        # see https://stackoverflow.com/a/2899055
        user = pwd.getpwuid(os.getuid())[0]
        self.logger.log(f'you are {user}, waiting on job {self.currentJobID}')
        print(f'you are {user}, waiting on job {self.currentJobID}')

        waitIntervals = 0
        waitIntervalTime = 10 * 60

        # actual wait loop
        while True:

            foundJobsPD = 0
            foundJobsR = 0

            # -r: expand job arrays, -h:skip header, -O arrayjobid: show only job array ID
            # find waiting jobs
            squeueOutput = subprocess.check_output(('squeue', '-u', user, '--state=PD', '-r', '-h', '-O', 'arrayjobid')).decode(sys.stdout.encoding)
            outputLines = squeueOutput.splitlines()
            for line in outputLines:
                match = re.search(r'^(\d+)', line)
                if match:
                    found = match.groups()[0]
                    if found == str(self.currentJobID):
                        foundJobsPD += 1

            # find running jobs
            squeueOutput = subprocess.check_output(('squeue', '-u', user, '--state=R', '-h', '-O', 'arrayjobid')).decode(sys.stdout.encoding)
            outputLines = squeueOutput.splitlines()
            for line in outputLines:
                match = re.search(r'^(\d+)', line)
                if match:
                    found = match.groups()[0]
                    if found == str(self.currentJobID):
                        foundJobsR += 1

            # no jobs found? then we can exit
            if foundJobsPD == 0 and foundJobsR == 0:
                print(f'Thread {self.threadNumber}: No more jobs running, continuing...')
                self.logger.log(f'all jobs completed after {waitIntervals * waitIntervalTime / 3600} hours!')
                self.currentJobID = None
                return

            print(f'Thread {self.threadNumber}: {foundJobsPD} jobs pending, {foundJobsR} running...')

            # wait for 10 minutes
            waitIntervals += 1
            time.sleep(waitIntervalTime)

        print(f'========= Simulation and Reconstruction done, all Jobs finished.')
        self.logger.log(f'========= Simulation and Reconstruction done, all Jobs finished.')

    # the lumi fit scripts are blocking!
    def detLumi(self):
        if self.__config is None:
            self.logger.log(f'please set run config first!')

        # FIXME: remove old lumi data directories first, like /bunches/binning/merge_data

        absPath = self.__config.pathTrksQA()
        self.logger.log(f'DEBUG: determining Luminosity of the data set found here:\n{absPath}')

        scriptsPath = self.__lumiFitPath / Path('scripts')
        command = scriptsPath / Path('determineLuminosity.py')
        argP = '--base_output_data_dir'
        argPval = absPath

        # see runSimulations()
        # we have to change the directory here since some script paths in LuminosityFit are relative.
        self.logger.log(f'DEBUG: changing cwd to {scriptsPath}')
        os.chdir(scriptsPath)
        self.logger.log(f'\n========= Running ./determineLuminosity.')
        print(f'Running ./determineLuminosity. This might take a while.')

        # don't close file descriptor, this call will block until lumi is determined!
        returnOutput = subprocess.check_output((command, argP, argPval))
        self.logger.log('\n\n' + returnOutput.decode(sys.stdout.encoding) + '\n')
        print(f'========= Done!')
        self.logger.log(f'========= Done!')

    def extractLumi(self):
        if self.__config is None:
            print(f'please set run config first!')
            self.logger.log(f'please set run config first!')

        print(f'========= Running ./extractLuminosity...')
        self.logger.log(f'\n\n========= Running ./extractLuminosity...\n')

        binPath = self.__lumiFitPath / Path('build') / Path('bin')
        command = binPath / Path('extractLuminosity')
        dataPath = self.__config.pathJobBase()

        if dataPath:
            returnOutput = subprocess.check_output((command, dataPath))
            self.logger.log('\n\n' + returnOutput.decode(sys.stdout.encoding) + '\n')
            print(f'========= Luminosity extracted!')

            if Path(self.__config.pathLumiVals()).exists():
                with open(self.__config.pathLumiVals()) as file:
                    lumiJson = json.load(file)
                self.logger.log(f'========= Luminosity extracted!\nLumi values:\n\n{lumiJson}\n\n')
            else:
                self.logger.log(f'========= Luminosity extracted, but lumi_vals.json could not be found!')

        else:
            print(f'can\'t determine path!')

    # test function

    def idle(self, seconds=3):

        if self.threadNumber > 0:
            sleeptime = seconds * (self.threadNumber+1)
        else:
            sleeptime = seconds
        print(f'this thread will idle {sleeptime} seconds.')
        time.sleep(sleeptime)

        print(f'done sleeping!')
