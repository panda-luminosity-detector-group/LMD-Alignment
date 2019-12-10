#!/usr/bin/env python3

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de

Note: of course this will somehow be line based since every line corresponds to a runConfig.

But later I want it column based, so that I can just add or remove a column to a Table, 
set it's header and specify which values from the runConfig go into the column.
Then, I want to be able to quickly assemble a complete LaTeX table with arbitrary
columns. But time is critical right now.
"""

from pathlib import Path

import json
import numpy as np
import subprocess
import sys

class LumiValDisplay:
    def __init__(self):
        self.cols = []

    @classmethod
    def fromConfigs(cls, configs):
        temp = cls()
        temp.configs = configs
        return temp

    def show(self):
        raise NotImplementedError

class LumiValLaTeXTable(LumiValDisplay):
    
    def show(self):

        self.configs.sort()

        print('Beam Momentum [GeV] & Misalign Type & Misalign Factor & Corrected & Lumi Deviation [\%] \\\\ \\hline')
        for conf in self.configs:

            if Path(conf.pathLumiVals()).exists():

                with open(conf.pathLumiVals()) as file:
                    lumiVals = json.load(file)

                try:
                    lumi = np.round(float(lumiVals["relative_deviation_in_percent"][0]), 3)
                except:
                    lumi = 'malformed data!'
            else:
                lumi = 'no data!'

            print(f'{conf.momentum} & {conf.misalignType} & {conf.misalignFactor} & {conf.alignmentCorrection} & {lumi} \\\\')

class LumiValGraph(LumiValDisplay):
    def show(self):
        print(f'Not applicable, try save(outFileName)!')
        raise NotImplementedError

    def getAllValues(self, copy=True):

        values = []

        remotePrefix = Path('m22:/lustre/miifs05/scratch/him-specf/paluma/roklasen')
        for conf in self.configs:
            
            # conf.tempDestPath = conf.pathLumiVals().parent
            conf.tempDestPath = Path(f'output/temp/{conf.misalignType}-{conf.misalignFactor}-{conf.alignmentCorrection}')
            conf.tempDestFile = conf.tempDestPath / Path(conf.pathLumiVals().name)
            conf.tempDestPath.mkdir(exist_ok=True, parents=True)
            conf.tempSourcePath = remotePrefix / Path(*conf.pathLumiVals().parts[6:])

            if copy:
                print(f'copying:\n{conf.tempSourcePath}\nto:\n{conf.tempDestPath}')
                success = subprocess.run(['scp', conf.tempSourcePath, conf.tempDestPath]).returncode

                if success > 0:
                    print(f'\n\n')
                    print(f'-------------------------------------------------')
                    print(f'file could not be copied, skipping this scenario.')
                    print(f'-------------------------------------------------')
                    print(f'\n\n')
                    continue

            with open(conf.tempDestFile) as file:
                lumiVals = json.load(file)

            lumi = lumiVals["relative_deviation_in_percent"][0]
            lumiErr = lumiVals["relative_deviation_error_in_percent"][0]


            # write to np array
            values.append([conf.misalignFactor, lumi, lumiErr])

        # hist das shizzle
        return np.array(values, float)

    def save(self, outFileName):
        values = self.getAllValues()
        print(values)

        import matplotlib.pyplot as plt
        #import seaborn; seaborn.set_style('whitegrid')

        self.latexsigma = r'\textsigma{}'
        self.latexmu = r'\textmu{}'
        plt.rc('font',**{'family':'serif', 'serif':['Palatino'], 'size':10})
        plt.rc('text', usetex=True)
        plt.rc('text.latex', preamble=r'\usepackage[euler]{textgreek}')

        #plt.rcParams['axes.spines.left'] = False
        # plt.rcParams['axes.spines.right'] = False
        # plt.rcParams['axes.spines.top'] = False
        #plt.rcParams['axes.spines.bottom'] = False
        plt.rcParams["legend.loc"] = 'upper left'




        # Defining the figure and figure size
        fig, ax = plt.subplots(figsize=(16/2.54, 10/2.54))

        # Plotting the error bars
        ax.errorbar(values[:,0], values[:,1], yerr=values[:,2], fmt='o', ecolor='orangered', color='steelblue', capsize=2)

        # Adding plotting parameters
        ax.set_title('Luminosity Fit Error by Misalignment Factor')
        ax.set_xlabel('Misalign Factor')
        ax.set_ylabel('Lumi Deviation [\%]')
        
        
        
        plt.grid(color='lightgrey', which='major', axis='y', linestyle='dotted')

        plt.savefig(outFileName,
                    #This is simple recomendation for publication plots
                    dpi=1000, 
                    # Plot will be occupy a maximum of available space
                    bbox_inches='tight')
        plt.close()

        pass
