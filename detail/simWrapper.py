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
        self.config = LMDRunConfig

    def getJobIDfromSubmitOutput(self, output):
        match = re.search(r'Submitted batch job (\d+)', output)
        if match:
            self.currentJobID = []
            for jobID in match.groups():
                self.logger.log(f'FOUND JOB ID: {jobID}\n')
                self.currentJobID.append(jobID)
        else:
            self.logger.log('can\'t parse job ID from output!\n')
            self.currentJobID = None

    def runSimulations(self):
        if self.config is None:
            self.logger.log(f'please set run config first!\n')

        self.logger.log(f'\n\n========= Running ./doSimulationReconstruction.\n')
        print(f'\n\n========= Running ./doSimulationReconstruction, please wait.\n')

        scriptsPath = self.__lumiFitPath / Path('scripts')
        command = scriptsPath / Path('doSimulationReconstruction.py')   # non-blocking!
        nTrks = self.config.trksNum
        nJobs = self.config.jobsNum
        mom = self.config.momentum
        dpm = 'dpm_elastic'

        almatp = '--alignment_matrices_path'
        almatv = str(self.config.pathAlMatrix())

        mismatp = '--misalignment_matrices_path'
        mismatv = str(self.config.pathMisMatrix())

        debugArg = '--debug'
        devQueueArg = '--use_devel_queue'

        if self.config.useDebug:
            self.logger.log(f'DEBUG: dumping current runConfig!')
            self.logger.log(self.config.dump() + '')

        # for debug, use --use_devel_queue

        # a basic run command ALWAYS has these four argumens
        subProcessCommandTuple = (command, nTrks, nJobs, mom, dpm)

        if self.config.useDebug:
            subProcessCommandTuple += (debugArg,)

        if self.config.useDevQueue:
            subProcessCommandTuple += (devQueueArg,)

        # apply misaligned
        if self.config.misaligned:
            subProcessCommandTuple += (mismatp, mismatv)

        # apply correction
        if self.config.alignmentCorrection:
            subProcessCommandTuple += (almatp, almatv)

        if self.config.useDebug:
            self.logger.log(f'DEBUG: run command tuple is {subProcessCommandTuple}')

        returnVal = subprocess.check_output(subProcessCommandTuple, cwd=scriptsPath).decode(sys.stdout.encoding)

        self.logger.log(f'\n============ RETURNED:\n{returnVal}\n============ END OF RETURN\n')
        self.logger.log(f'\n\n========= Done!.\n')
        self.logger.log(f'\n\n========= Jobs submitted, waiting for them to finish...\n')
        self.getJobIDfromSubmitOutput(returnVal)

        self.logger.log(f'Waiting 30 seconds for jobs tu get submitted...')
        time.sleep(30)

    def GetPendingAndRunning(self, jobID):
        foundJobsPD = 0
        foundJobsR = 0

        user = pwd.getpwuid(os.getuid())[0]
        self.logger.log(f'you are {user}, waiting on job {jobID}\n')
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

        self.logger.log(f'Thread {self.threadNumber}, JobID: {jobID}: {foundJobsPD} jobs pending, {foundJobsR} running...\n')
        return (foundJobsPD, foundJobsR)

    def waitForJobCompletion(self):
        if self.config is None:
            self.logger.log(f'please set run config first!')

        if self.currentJobID is None:
            self.logger.log(f'can\'t wait for jobs, this simWrapper doesn\'t know that jobs to wait for!\n')
            return

        self.logger.log(f'\n\n========= Waiting for jobs...\n')
        print(f'\n\n========= Waiting for jobs...\n')

        # see https://stackoverflow.com/a/2899055
        user = pwd.getpwuid(os.getuid())[0]
        self.logger.log(f'you are {user}, waiting on job {self.currentJobID}\n')
        print(f'you are {user}, waiting on job {self.currentJobID}...\n')

        waitIntervals = 0
        waitIntervalTime = 10 * 60

        # actual wait loop
        while True:

            foundJobsPD = 0
            foundJobsR = 0

            for jobID in self.currentJobID:
                self.logger.log(f'Testing for JobID {jobID}...\n')
                pending, running = self.GetPendingAndRunning(jobID)
                foundJobsPD += pending
                foundJobsR += running

            # no jobs found? then we can exit
            if foundJobsPD == 0 and foundJobsR == 0:
                print(f'Thread {self.threadNumber}: No more jobs running, continuing...')
                self.logger.log(f'all jobs completed after {waitIntervals * waitIntervalTime / 3600} hours!')
                self.currentJobID = None
                return

            print(f'Thread {self.threadNumber}: {foundJobsPD} jobs pending, {foundJobsR} running for IDs: {self.currentJobID}...')

            # wait for 10 minutes
            waitIntervals += 1
            time.sleep(waitIntervalTime)

        print(f'========= Simulation and Reconstruction done, all Jobs finished.')
        self.logger.log(f'========= Simulation and Reconstruction done, all Jobs finished.')

    # the lumi fit scripts are not blocking!
    # the first ones are and take about an hour, but the latter ones just submit jobs and return.
    # you have to wait for their jobs to finish!
    def detLumi(self):
        if self.config is None:
            self.logger.log(f'please set run config first!')

        # FIXME: remove old lumi data directories first, like /bunches/binning/merge_data

        absPath = self.config.pathTrksQA()
        self.logger.log(f'DEBUG: determining Luminosity of the data set found here:\n{absPath}')

        scriptsPath = self.__lumiFitPath / Path('scripts')
        command = scriptsPath / Path('determineLuminosity.py')
        argP = '--base_output_data_dir'
        argPval = absPath

        # see runSimulations()
        self.logger.log(f'\n========= Running ./determineLuminosity.')
        print(f'Running ./determineLuminosity. This might take a while.')

        # TODO: this script doesn't have a debug flag, but it can use the devel queue

        returnVal = subprocess.check_output((command, argP, argPval), cwd=scriptsPath).decode(sys.stdout.encoding)
        self.getJobIDfromSubmitOutput(returnVal)

        self.logger.log('\n\n' + returnVal + '\n')
        self.logger.log(f'========= Done!')
        print(f'========= Done!')

    def extractLumi(self):
        if self.config is None:
            print(f'please set run config first!')
            self.logger.log(f'please set run config first!')

        print(f'========= Running ./extractLuminosity...')
        self.logger.log(f'\n\n========= Running ./extractLuminosity...\n')

        binPath = self.__lumiFitPath / Path('build') / Path('bin')
        command = binPath / Path('extractLuminosity')
        dataPath = self.config.pathJobBase()

        if dataPath:
            returnOutput = subprocess.check_output((command, dataPath))
            self.logger.log('\n\n' + returnOutput.decode(sys.stdout.encoding) + '\n')
            print(f'========= Luminosity extracted!')

            if Path(self.config.pathLumiVals()).exists():
                with open(self.config.pathLumiVals()) as file:
                    lumiJson = json.load(file)
                self.logger.log(f'========= Luminosity extracted!\nLumi values:\n\n{lumiJson}\n\n')
            else:
                self.logger.log(f'========= Luminosity extracted, but lumi_vals.json could not be found!\n')

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
