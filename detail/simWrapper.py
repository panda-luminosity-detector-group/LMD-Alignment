#!/usr/bin/env python3

"""
LMD Simulation Wrapper

Depends on:
- FairRoot
- PandaRoot
- LuminosityFitFramework
"""

import datetime
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

FIXME:  apparently the lumi fit framework sometimes failes when re-determining the lumi of an already fully processed directory
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
        self.threadNumber = None
        self.__log = ''
        self.__debug = True
        try:
            self.__lumiFitPath = str(Path(os.environ[lmdFitEnv]).parent)
            self.__simDataPath = os.environ[simDirEnv]
            self.__pandaRootDir = os.environ[pndRootDir]
        except:
            self.__log += "can't find LuminosityFit installation, PandaRoot installation or Data_Dir!\n"
            self.__log += f"please set {lmdFitEnv}, {pndRootDir} and {simDirEnv}!\n"
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
            self.__log += f'please set run config first!\n'

        self.__log += f'\n\n========= Running ./doSimulationReconstruction.\n\n'
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
        self.__log += f'DEBUG: changing cwd to {scriptsPath}\n'
        os.chdir(scriptsPath)

        if self.__debug:
            self.__log += f'DEBUG: dumping current runConfig!\n'
            self.__log += self.__config.dump() + '\n'

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

        self.__log += f'\n============ RETURNED:\n{returnVal}\n============ END OF RETURN\n\n'
        self.__log += f'\n\n========= Done!.\n\n'
        print(f'\n\n========= Jobs submitted, waiting for them to finish...\n\n')

        match = re.search(r'Submitted batch job (\d+)', returnVal)
        if match:
            jobID = match.groups()[0]
            self.__log += f'FOUND JOB ID: {jobID}\n'
            self.currentJobID = jobID
        else:
            self.__log += 'can\'t parse job ID from output!\n'

    def waitForJobCompletion(self):
        if self.__config is None:
            self.__log += f'please set run config first!\n'

        if not self.currentJobID:
            self.__log += f'can\'t wait for jobs, this simWrapper doesn\'t know that jobs to wait for!\n'
            return

        self.__log += f'\n\n========= Waiting for jobs...\n\n'
        print(f'\n\n========= Waiting for jobs...\n\n')

        # see https://stackoverflow.com/a/2899055
        user = pwd.getpwuid(os.getuid())[0]
        self.__log += f'you are {user}, waiting on job {self.currentJobID}\n'
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
                print(f'no jobs running, continuing...')
                self.__log += f'all jobs completed after {waitIntervals * waitIntervalTime} minutes!\n'
                self.currentJobID = None
                return

            print(f'Thread {self.threadNumber}: {foundJobsPD} jobs pending, {foundJobsR} running...')

            # wait for 10 minutes
            waitIntervals += 1
            time.sleep(waitIntervalTime)

        print(f'========= Simulation and Reconstruction done, all Jobs finished.')
        self.__log += f'========= Simulation and Reconstruction done, all Jobs finished.\n'

    # the lumi fit scripts are blocking!
    def detLumi(self):
        if self.__config is None:
            self.__log += f'please set run config first!\n'

        absPath = self.__config.pathTrksQA()
        self.__log += f'DEBUG: determining Luminosity of the data set found here:\n{absPath}\n'

        scriptsPath = self.__lumiFitPath / Path('scripts')
        command = scriptsPath / Path('determineLuminosity.py')
        argP = '--base_output_data_dir'
        argPval = absPath

        # see runSimulations()
        # we have to change the directory here since some script paths in LuminosityFit are relative.
        self.__log += f'DEBUG: changing cwd to {scriptsPath}\n'
        os.chdir(scriptsPath)
        self.__log += f'\n\n========= Running ./determineLuminosity.\n\n'
        print(f'Running ./determineLuminosity. This might take a while.\n')

        # don't close file descriptor, this call will block until lumi is determined!
        returnOutput = subprocess.check_output((command, argP, argPval))
        self.__log += '\n\n' + returnOutput.decode(sys.stdout.encoding) + '\n\n'
        print(f'========= Done!')
        self.__log += f'========= Done!\n'

    def extractLumi(self):
        if self.__config is None:
            self.__log += f'please set run config first!\n'

        # TODO: the binary only finds files in [...]/geo_misalignmentmisMat-box-1.00/100000/, NOT the subfolder [...]/1-500_uncut/aligned-alMat-box-1.00 !!!

        print(f'========= Running ./extractLuminosity...')
        self.__log += f'\n\n========= Running ./extractLuminosity...\n\n'

        binPath = self.__lumiFitPath / Path('build') / Path('bin')
        command = binPath / Path('extractLuminosity')
        dataPath = self.__config.pathDataBaseDir()

        if dataPath:
            returnOutput = subprocess.check_output((command, dataPath))
            self.__log += '\n\n' + returnOutput.decode(sys.stdout.encoding) + '\n\n'
            print(f'========= Luminosity extracted!')
            self.__log += f'========= Luminosity extracted!\n'

        else:
            print(f'can\'t determine path!')

    def runAll(self):
        if self.__config is None:
            self.__log += f'please set run config first!\n'
            return

        self.runSimulations()           # non blocking, so we have to wait
        self.waitForJobCompletion()     # blocking
        self.detLumi()                  # blocking
        self.extractLumi()              # blocking
        self.saveLog()                  # this is needed if multiple threads are running concurrently

    def saveLog(self):

        # should include date
        if self.threadNumber is not None:
            timename = datetime.datetime.now().replace(second=0, microsecond=0).isoformat()
        else:
            timename = datetime.datetime.now().isoformat()

        jobname = str(self.threadNumber)
        filename = self.cwd / Path('runLogs') / Path(f'{timename}-{jobname}.log')

        # make dir if not present
        filename.parent.mkdir(exist_ok=True)
        print(f'DEBUG: saving log to {filename}')

        self.__log = f'This is simWrapper {self.threadNumber}:\n\n' + self.__log

        with open(filename, 'w') as file:
            file.write(self.__log)

    # test function

    def idle(self, seconds=3):
        print(f'this thread will idle {seconds} seconds.')
        time.sleep(seconds)
        print(f'done sleeping!')
