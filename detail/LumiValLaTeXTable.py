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

        self.corrected = self.configs[0].alignmentCorrection

        for conf in self.configs:
            if conf.alignmentCorrection != self.corrected:
                raise Exception(f'Error! You cannot mix corrected and uncorrected results!')

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

            if not conf.tempDestFile.exists():
                continue

            with open(conf.tempDestFile) as file:
                lumiVals = json.load(file)

            try:
                lumi = lumiVals["relative_deviation_in_percent"][0]
                lumiErr = lumiVals["relative_deviation_error_in_percent"][0]
            except:
                continue

            if float(lumi) > 1e3:
                continue

            # write to np array
            values.append([conf.misalignFactor, lumi, lumiErr])

        # hist das shizzle
        return np.array(values, float)

    def save(self, outFileName, corrected=False):
        values = self.getAllValues()
        if len(values) < 1:
            raise Exception(f'Error! Value array is empty!')
        print(values)

        sizes = [(16/2.54, 8/2.54), (16/2.54, 4/2.54), (6.5/2.54, 4/2.54)]
        titlesCorr = ['Luminosity Fit Error, With Alignment', 'Luminosity Fit Error, With Alignment', 'Luminosity Fit Error']
        titlesUncorr = ['Luminosity Fit Error, Without Alignment', 'Luminosity Fit Error, Without Alignment', 'Luminosity Fit Error']

        import matplotlib.pyplot as plt

        self.latexsigma = r'\textsigma{}'
        self.latexmu = r'\textmu{}'
        self.latexPercent = r'\%'
        plt.rc('font',**{'family':'serif', 'serif':['Palatino'], 'size':10})
        plt.rc('text', usetex=True)
        plt.rc('text.latex', preamble=r'\usepackage[euler]{textgreek}')

        #plt.rcParams['axes.spines.left'] = False
        # plt.rcParams['axes.spines.right'] = False
        # plt.rcParams['axes.spines.top'] = False
        #plt.rcParams['axes.spines.bottom'] = False
        plt.rcParams["legend.loc"] = 'upper left'

        for i in range(len(sizes)):

            # Defining the figure and figure size
            fig, ax = plt.subplots(figsize=sizes[i])

            # Plotting the error bars
            ax.errorbar(values[:,0], values[:,1], yerr=values[:,2], fmt='o', ecolor='orangered', color='steelblue', capsize=2)

            # Adding plotting parameters
            if self.corrected:
                ax.set_title(titlesCorr[i])
            else:
                ax.set_title(titlesUncorr[i])

            ax.set_xlabel(f'Misalign Factor')
            ax.set_ylabel(f'Lumi Deviation [{self.latexPercent}]')
            
            plt.grid(color='lightgrey', which='major', axis='y', linestyle='dotted')
            plt.grid(color='lightgrey', which='major', axis='x', linestyle='dotted')

            plt.savefig(f'{outFileName}-{i}.pdf',
                        #This is simple recomendation for publication plots
                        dpi=1000, 
                        # Plot will be occupy a maximum of available space
                        bbox_inches='tight')
            plt.close()
