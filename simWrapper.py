#!/usr/bin/env python3

import os
import sys
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
- remember to delete everything after mc genereation for new run

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
        self.__cwd = Path.cwd()

    @classmethod
    def fromRunConfig(cls, LMDRunConfig) -> 'simWrapper':
        print('I wanna go home (;-;) ')

    def dump(self):
        print(f'\n\n')
        print(f'------------------------------')
        print(f'DEBUG OUTPUT for SimWrapper:\n')
        print(f'CWD: {self.__cwd}')
        print(f'------------------------------')
        print(f'\n\n')

    def setRunConfig(self, LMDRunConfig):
        self.__config = LMDRunConfig

    # the lumi fit scripts are blocking!
    def detLumi(self):
        if self.__config is None:
            print(f'please set run config first!')

        absPath = self.__config.__path
        print(f'path: {absPath}')

        scriptsPath = self.__lumiFitPath / Path('scripts')
        command = scriptsPath / Path('determineLuminosity.py')
        argP = '--base_output_data_dir'
        argPval = absPath

        # close file desciptor to run command in different process and return
        subprocess.Popen((command, argP, argPval), close_fds=True)  # works!


def run():
    path = '/lustre/miifs05/scratch/him-specf/paluma/roklasen/LumiFit/plab_1.5GeV/dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/geo_misalignmentmisMat-box-3.00/100000/1-500_uncut_aligned'
    config = LMDRunConfig.fromPath(path)

    wrapper = simWrapper()
    wrapper.setRunConfig(config)
    wrapper.detLumi()


def testRunConfigs():
    path = '/lustre/miifs05/scratch/him-specf/paluma/roklasen/LumiFit/plab_1.5GeV/dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/geo_misalignmentmisMat-box-3.00/100000/1-500_uncut_aligned'
    config = LMDRunConfig.fromPath(path)
    config.dump()

    config.toJSON('1.json')


if __name__ == "__main__":
    print('greetings, human')
    testRunConfigs()
