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
            self.logger.add("can't find LuminosityFit installation, PandaRoot installation or Data_Dir!\n")
            self.logger.add(f"please set {lmdFitEnv}, {pndRootDir} and {simDirEnv}!\n")
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
            self.logger.add(f'please set run config first!\n')

        self.logger.add(f'\n\n========= Running ./doSimulationReconstruction.\n\n')
        print(f'\n\n========= Running ./doSimulationReconstruction, please wait.\n\n')

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
        self.logger.add(f'DEBUG: changing cwd to {scriptsPath}\n')
        os.chdir(scriptsPath)

        if self.__debug:
            self.logger.add(f'DEBUG: dumping current runConfig!\n')
            self.logger.add(self.__config.dump() + '\n')

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

        self.logger.add(f'\n============ RETURNED:\n{returnVal}\n============ END OF RETURN\n\n')
        self.logger.add(f'\n\n========= Done!.\n\n')
        print(f'\n\n========= Jobs submitted, waiting for them to finish...\n\n')

        match = re.search(r'Submitted batch job (\d+)', returnVal)
        if match:
            jobID = match.groups()[0]
            self.logger.add(f'FOUND JOB ID: {jobID}\n')
            self.currentJobID = jobID
        else:
            self.logger.add('can\'t parse job ID from output!\n')

    def waitForJobCompletion(self):
        if self.__config is None:
            self.logger.add(f'please set run config first!\n')

        if not self.currentJobID:
            self.logger.add(f'can\'t wait for jobs, this simWrapper doesn\'t know that jobs to wait for!\n')
            return

        self.logger.add(f'\n\n========= Waiting for jobs...\n\n')
        print(f'\n\n========= Waiting for jobs...\n\n')

        # see https://stackoverflow.com/a/2899055
        user = pwd.getpwuid(os.getuid())[0]
        self.logger.add(f'you are {user}, waiting on job {self.currentJobID}\n')
        print(f'you are {user}, waiting on job {self.currentJobID}\n')

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
                self.logger.add(f'all jobs completed after {waitIntervals * waitIntervalTime / 3600} hours!\n')
                self.currentJobID = None
                return

            print(f'Thread {self.threadNumber}: {foundJobsPD} jobs pending, {foundJobsR} running...')

            # wait for 10 minutes
            waitIntervals += 1
            time.sleep(waitIntervalTime)

        print(f'========= Simulation and Reconstruction done, all Jobs finished.')
        self.logger.add(f'========= Simulation and Reconstruction done, all Jobs finished.\n')

    # the lumi fit scripts are blocking!
    def detLumi(self):
        if self.__config is None:
            self.logger.add(f'please set run config first!\n')

        absPath = self.__config.pathTrksQA()
        self.logger.add(f'DEBUG: determining Luminosity of the data set found here:\n{absPath}\n')

        scriptsPath = self.__lumiFitPath / Path('scripts')
        command = scriptsPath / Path('determineLuminosity.py')
        argP = '--base_output_data_dir'
        argPval = absPath

        # see runSimulations()
        # we have to change the directory here since some script paths in LuminosityFit are relative.
        self.logger.add(f'DEBUG: changing cwd to {scriptsPath}\n')
        os.chdir(scriptsPath)
        self.logger.add(f'\n\n========= Running ./determineLuminosity.\n\n')
        print(f'Running ./determineLuminosity. This might take a while.\n')

        # don't close file descriptor, this call will block until lumi is determined!
        returnOutput = subprocess.check_output((command, argP, argPval))
        self.logger.add('\n\n' + returnOutput.decode(sys.stdout.encoding) + '\n\n')
        print(f'========= Done!')
        self.logger.add(f'========= Done!\n')

    def extractLumi(self):
        if self.__config is None:
            self.logger.add(f'please set run config first!\n')

        print(f'========= Running ./extractLuminosity...')
        self.logger.add(f'\n\n========= Running ./extractLuminosity...\n\n')

        binPath = self.__lumiFitPath / Path('build') / Path('bin')
        command = binPath / Path('extractLuminosity')
        dataPath = self.__config.pathJobBase()

        if dataPath:
            returnOutput = subprocess.check_output((command, dataPath))
            self.logger.add('\n\n' + returnOutput.decode(sys.stdout.encoding) + '\n\n')
            print(f'========= Luminosity extracted!')

            with open(self.__config.pathLumiVals()) as file:
                lumiJson = json.load(file)

            print(lumiJson)

            self.logger.add(f'========= Luminosity extracted!\nLumi values: {lumiJson}')

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
