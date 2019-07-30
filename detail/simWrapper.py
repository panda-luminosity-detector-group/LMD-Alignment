#!/usr/bin/env python3

"""
LMD Simulation Wrapper

Depends on:
- FairRoot
- PandaRoot
- LuminosityFitFramework
"""

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
        self.__debug = True
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
        print(f'DEBUG: changing cwd to {scriptsPath}')
        os.chdir(scriptsPath)

        if self.__debug:
            print(f'DEBUG: dumping current runConfig!\n')
            self.__config.dump()

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

        print(f'\n============ RETURNED:\n{returnVal}\n============ END OF RETURN\n\n')

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

        if not self.currentJobID:
            print(f'can\'t wait for jobs, this simWrapper doesn\'t know that jobs to wait for!')
            return

        # see https://stackoverflow.com/a/2899055
        user = pwd.getpwuid(os.getuid())[0]
        print(f'you are {user}, waiting on job {self.currentJobID}')
        while True:
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

            # TODO: check for stuck jobs here, sometimes a single job will get stuck and timeout.

            # wait until next iteration
            time.sleep(10*60)

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
        print(f'DEBUG: changing cwd to {scriptsPath}')
        os.chdir(scriptsPath)
        print(f'Running ./determineLuminosity . This might take a while.')
        # don't close file desciptor, this call will block until lumi is determined!
        subprocess.call((command, argP, argPval))
        print(f'done!')

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
            subprocess.call((command, dataPath))
            print(f'Luminosity extracted!')

        else:
            print(f'can\'t determine path!')

    def runAll(self):
        if self.__config is None:
            print(f'please set run config first!')
            return

        self.runSimulations()           # non blocking, so we have to wait
        self.waitForJobCompletion()     # blocking
        self.detLumi()                  # blocking
        self.extractLumi()              # blocking

    # test function
    def idle(self, seconds=3):
        print(f'this thread will idle {seconds} seconds.')
        time.sleep(seconds)
        print(f'done sleeping!')
