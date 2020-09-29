#!/usr/bin/env python3
"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de

"""

from pathlib import Path

import json
import numpy as np
import subprocess
import sys
import glob  # to resolve wildcards in lumi values path name


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

    def getAllValues(self, copy=True, reallyAll=False):

        values = []

        # remotePrefix = Path('m22:/lustre/miifs05/scratch/him-specf/paluma/roklasen/LumiFit/backup_beamTiltEnabled/') # used to be roklasen here too, what was that about?
        # remotePrefix = Path('m22:/lustre/miifs05/scratch/him-specf/paluma/roklasen/LumiFit/') #! this is the usual path directly after simulations have run
        # remotePrefix = Path('m22:/lustre/miifs05/scratch/him-specf/paluma/roklasen/LumiFit/FINAL')  #! this is the hand-picked path (results from different run sets)
        # remotePrefix = Path('himster:/lustre/miifs05/scratch/him-specf/paluma/roklasen/LumiFit/FINAL')  #! after himster hack, but now with 2FA, thats not working anymore either

        #* all the above are now irrelevant, the himster was hacked and every access requires 2FA. you cannot copy files from here anymore and have to prepare them by hand.
        remotePrefix = Path('/media/DataEnc2TBRaid1/Arbeit/VirtualDir')

        self.corrected = self.configs[0].alignmentCorrection
        self.misalignType = self.configs[0].misalignType

        for conf in self.configs:

            if (conf.alignmentCorrection != self.corrected) and (conf.misalignType != 'aligned'):
                raise Exception(f'Error! You cannot mix corrected and uncorrected results!')
            if (conf.misalignType != self.misalignType) and (conf.misalignType != 'aligned'):
                raise Exception(f'Please plot misalign types individually.')

            if conf.misalignType == 'aligned':
                conf.misalignFactor = 0.0
                conf.alignmentCorrection = False

            if reallyAll and conf.seedID is not None:

                # workaround for alignment matrix name which is not included in runConfig files
                # if you want UNcorrected, leave this off
                conf.alignmentCorrection = True
                
                conf.alMatFile = f'alMat-combiSenMod-seed{conf.seedID}-{conf.misalignFactor}.json'

                conf.tempDestPath = Path(f'output/temp/LumiVals/multi/{conf.misalignType}-{conf.momentum}-{conf.misalignFactor}-seed{conf.seedID}-{conf.alignmentCorrection}')
            else:
                conf.tempDestPath = Path(f'output/temp/LumiVals/{conf.misalignType}-{conf.momentum}-{conf.misalignFactor}-{conf.alignmentCorrection}')
            
            conf.tempDestFile = conf.tempDestPath / Path(conf.pathLumiVals().name)
            conf.tempDestPath.mkdir(exist_ok=True, parents=True)
            conf.tempSourcePath = remotePrefix / Path(*conf.pathLumiVals().parts[7:])

            # print(f'debug:')
            # print(f'conf.tempSourcePath: {conf.tempSourcePath}')
            # print(f'conf.alignmentCorrection is {conf.alignmentCorrection}')
            # print(f'conf.tempDestPath: {conf.tempDestPath}')

            # changed thus to use local directory, since rsyncing from python doesn't work anymore from himster
            if copy:
                # first, find the actual file, use bash auto completetion for wildcards:
                resolved = glob.glob(str(conf.tempSourcePath))
                if len(resolved) > 0:
                    resolved = resolved[0]
                else:
                    continue

                # print(f'copying:\n{resolved}\nto:\n{conf.tempDestPath}')
                success = subprocess.run(['cp', resolved, conf.tempDestPath]).returncode  #! use cp instead of scp for copies from local dirs

                if success > 0:
                    print(f'\n\n')
                    print(f'-------------------------------------------------')
                    print(f'file could not be copied, skipping this scenario.')
                    print(f'-------------------------------------------------')
                    print(f'\n\n')
                    continue

            if not conf.tempDestFile.exists():
                print(f'error! cannot find {conf.tempDestFile}')
                continue

            with open(conf.tempDestFile) as file:
                lumiVals = json.load(file)
                # print(f'reading data from {conf.tempDestFile}')

            try:
                lumi = lumiVals["relative_deviation_in_percent"][0]
                lumiErr = lumiVals["relative_deviation_error_in_percent"][0]
            except:
                continue

            if abs(float(lumi)) > 1e3:
                continue

            seedID = conf.seedID

            # write to np array
            if reallyAll:
                values.append([conf.momentum, conf.misalignFactor, lumi, lumiErr, seedID])
            else:
                values.append([conf.misalignFactor, lumi, lumiErr])

        # hist das shizzle
        return np.array(values, float)

    """
    TODO: Further encapsulate so that the graphs can be saved individually AND all momenta in a single graph! For that, they should be sorted by misalignType
    """

    def save(self, outFileName, corrected=False):

        values = self.getAllValues()
        if len(values) < 1:
            raise Exception(f'Error! Value array is empty!')
        # print(values)

        sizes = [(15 / 2.54, 9 / 2.54), (15 / 2.54, 4 / 2.54), (6.5 / 2.54, 4 / 2.54)]
        titlesCorr = ['Luminosity Fit Error, With Alignment', 'Luminosity Fit Error, With Alignment', 'Luminosity Fit Error']
        titlesUncorr = ['Luminosity Fit Error, Without Alignment', 'Luminosity Fit Error, Without Alignment', 'Luminosity Fit Error']

        import matplotlib.pyplot as plt

        self.latexsigma = r'\textsigma{}'
        self.latexmu = r'\textmu{}'
        self.latexPercent = r'\%'
        plt.rc('font', **{'family': 'serif', 'serif': ['Palatino'], 'size': 10})
        plt.rc('text', usetex=True)
        plt.rc('text.latex', preamble=r'\usepackage[euler]{textgreek}')

        plt.rcParams["legend.loc"] = 'best'

        for i in range(len(sizes)):

            # Defining the figure and figure size
            fig, ax = plt.subplots(figsize=sizes[i])

            # Plotting the error bars
            # ax.errorbar(values[:,0], values[:,1], yerr=values[:,2], fmt='.', ecolor='grey', color='steelblue', capsize=2)
            ax.errorbar(values[:, 0], values[:, 1], yerr=values[:, 2], fmt='d', ecolor='black', capsize=2, elinewidth=0.6)

            # Adding plotting parameters
            # no titles anymore
            if False:
                if self.corrected:
                    ax.set_title(titlesCorr[i])
                else:
                    ax.set_title(titlesUncorr[i])

            ax.set_xlabel(f'Misalign Factor')
            # ax.set_ylabel(f'Luminosity Error [{self.latexPercent}]')
            ax.set_ylabel(f'$\Delta L$ [{self.latexPercent}]')

            plt.grid(color='lightgrey', which='major', axis='y', linestyle='dotted')
            plt.grid(color='lightgrey', which='major', axis='x', linestyle='dotted')

            plt.savefig(
                f'{outFileName}-{i}.pdf',
                #This is simple recomendation for publication plots
                dpi=1000,
                # Plot will be occupy a maximum of available space
                bbox_inches='tight')
            plt.close()

    def saveAllMomenta(self, outFileName):
        values = self.getAllValues(reallyAll=True, copy=True)
        if len(values) < 1:
            raise Exception(f'Error! Value array is empty!')
        # print(values)

        # we're guranteed to only have one single misalign type, therefore we're looping over beam momenta
        momenta = []
        print('gathering momenta')

        for i in values:
            momenta.append(i[0])

        # we only want unique entries
        momenta = np.array(momenta)
        momenta = np.sort(momenta)
        momenta = np.unique(momenta, axis=0)

        sizes = [(15 / 2.54, 9 / 2.54), (15 / 2.54, 4 / 2.54), (6.5 / 2.54, 4 / 2.54)]
        titlesCorr = ['Luminosity Fit Error, With Alignment', 'Luminosity Fit Error, With Alignment', 'Luminosity Fit Error']
        titlesUncorr = ['Luminosity Fit Error, Without Alignment', 'Luminosity Fit Error, Without Alignment', 'Luminosity Fit Error']

        import matplotlib.pyplot as plt

        self.latexsigma = r'\textsigma{}'
        self.latexmu = r'\textmu{}'
        self.latexPercent = r'\%'
        plt.rc('font', **{'family': 'serif', 'serif': ['Palatino'], 'size': 10})
        plt.rc('text', usetex=True)
        plt.rc('text.latex', preamble=r'\usepackage[euler]{textgreek}')

        # plt.rcParams["legend.loc"] = 'upper left'
        plt.rcParams["legend.loc"] = 'upper right'

        # Defining the figure and figure size

        offsetscale = 1.0
        offsets = np.arange(-0.02, 0.03, 0.01)

        for i in range(len(sizes)):

            fig, ax = plt.subplots(figsize=sizes[i])
            colorI = 0

            # colors = ['steelblue', 'red', 'green']
            # these are the default colors, why change them
            colors = [u'#1f77b4', u'#ff7f0e', u'#2ca02c', u'#d62728', u'#9467bd', u'#8c564b', u'#e377c2', u'#7f7f7f', u'#bcbd22', u'#17becf']

            for mom in momenta:
                # print(f'for momentum {mom}, we find:')
                mask = (values[:, 0] == mom)  # & (values[:, 2] > -0.3)
                thseVals = values[mask]

                # sort 2D array by second column
                thseVals = thseVals[thseVals[:, 1].argsort()]

                # Plotting the error bars
                ax.errorbar(thseVals[:, 1] + offsets[colorI] * offsetscale,
                            thseVals[:, 2],
                            yerr=thseVals[:, 3],
                            fmt='d',
                            ecolor='black',
                            color=colors[colorI],
                            capsize=2,
                            elinewidth=0.6,
                            label=f'{mom} GeV',
                            ls='dashed',
                            linewidth=0.4)
                colorI += 1

            # Adding plotting parameters
            # no titles anymore
            if False:
                if self.corrected:
                    ax.set_title(titlesCorr[i])
                else:
                    ax.set_title(titlesUncorr[i])

            ax.set_xlabel(f'Misalign Factor')
            # ax.set_ylabel(f'Luminosity Error [{self.latexPercent}]')

            # set ticks exactly to the misalign factors
            start, end = ax.get_xlim()
            # ax.xaxis.set_ticks(np.arange(0.0, end, 0.25))

            #! change for sensors, they don't have 3.0
            ax.xaxis.set_ticks([0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0])
            ax.xaxis.set_view_interval(start, end)

            ax.set_ylabel(f'$\Delta L$ [{self.latexPercent}]')

            # get handles
            handles, labels = ax.get_legend_handles_labels()
            # remove the errorbars
            handles = [h[0] for h in handles]
            # use them in the legend
            # ax.legend(handles, labels, loc='upper left',numpoints=1)
            # ax.legend(handles, labels, loc='upper right',numpoints=1)
            ax.legend(handles, labels, loc='best', numpoints=1)

            # draw vertical line to separate aligned and misaligned cases
            plt.axvline(x=0.125, color=r'#aa0000', linestyle='-', linewidth=0.5)

            plt.tight_layout()

            plt.grid(color='grey', which='major', axis='y', linestyle=':', linewidth=0.5)
            plt.grid(color='grey', which='major', axis='x', linestyle=':', linewidth=0.5)
            # plt.legend()

            plt.savefig(
                f'{outFileName}-{i}.pdf',
                #This is simple recomendation for publication plots
                dpi=1000,
                # Plot will be occupy a maximum of available space
                bbox_inches='tight')
            plt.close()

    # this is the grand final, plots all factors for all momenta, averages over all seeds and calcs std errors
    def multiSeed(self, fileName):
        print(f'Yes. I am multiseeding.')

        values = self.getAllValues(reallyAll=True, copy=True)
        if len(values) < 1:
            raise Exception(f'Error! Value array is empty!')
        # print(values)

        # we're guranteed to only have one single misalign type, therefore we're looping over beam momenta
        momenta = []
        print('gathering momenta')

        for i in values:
            momenta.append(i[0])

        # we only want unique entries
        momenta = np.array(momenta)
        momenta = np.sort(momenta)
        momenta = np.unique(momenta, axis=0)

        print(f'Momenta: {momenta}')

        sizes = [(15 / 2.54, 9 / 2.54), (15 / 2.54, 4 / 2.54), (6.5 / 2.54, 4 / 2.54)]
        titlesCorr = ['Luminosity Fit Error, With Alignment', 'Luminosity Fit Error, With Alignment', 'Luminosity Fit Error']
        titlesUncorr = ['Luminosity Fit Error, Without Alignment', 'Luminosity Fit Error, Without Alignment', 'Luminosity Fit Error']

        import matplotlib.pyplot as plt

        self.latexsigma = r'\textsigma{}'
        self.latexmu = r'\textmu{}'
        self.latexPercent = r'\%'
        plt.rc('font', **{'family': 'serif', 'serif': ['Palatino'], 'size': 10})
        plt.rc('text', usetex=True)
        plt.rc('text.latex', preamble=r'\usepackage[euler]{textgreek}')

        # plt.rcParams["legend.loc"] = 'upper left'
        plt.rcParams["legend.loc"] = 'upper right'

        # Defining the figure and figure size

        offsetscale = 2.0
        offsets = np.arange(-0.02, 0.03, 0.01)

        for i in range(len(sizes)):

            fig, ax = plt.subplots(figsize=sizes[i])
            colorI = 0

            # colors = ['steelblue', 'red', 'green']
            # these are the default colors, why change them
            colors = [u'#1f77b4', u'#ff7f0e', u'#2ca02c', u'#d62728', u'#9467bd', u'#8c564b', u'#e377c2', u'#7f7f7f', u'#bcbd22', u'#17becf']

            for mom in momenta:
                # print(f'for momentum {mom}, we find:')
                mask = (values[:, 0] == mom)  # & (values[:, 2] > -0.3)
                thseVals = values[mask]

                # sort 2D array by second column
                thseVals = thseVals[thseVals[:, 1].argsort()]

                newArray = []
                # ideally, get the factors from the array, but at this point I don't really care anymore
                for fac in ['0.0', '0.25', '0.50', '0.75', '1.00', '1.25', '1.50', '1.75', '2.00', '2.50', '3.00']:
                # for fac in ['0.0', '0.25', '0.50', '0.75', '1.00', '1.25', '1.50']:
                # for fac in ['1.00']:
                    facMask = (thseVals[:, 1] == float(fac))
                    maskedArray = thseVals[facMask]

                    if len(maskedArray) < 1:
                        continue

                    # print(f'for factor {fac} at {mom}GeV, this is the masked array BEFORE outlier rejection:\n{maskedArray}')
                    # outlier rejection, sort 2D array by second column
                    # maskedArray = maskedArray[np.abs(maskedArray[:, 2]).argsort()]
                    # maskedArray = maskedArray[:-2]
                    # print(f'for factor {fac} at {mom}GeV, this is the masked array AFTER outlier rejection:\n{maskedArray}')
                    #! NOPE! We use data thats not available at the real experiment, the reference luminosity!
                    #! NO OUTLIER REJECTION! Keep this comment so you don't forget that.

                    mean = np.mean(maskedArray[:, 2], axis=0)
                    std = np.std(maskedArray[:, 2], axis=0)

                    if not np.isnan(mean) and not np.isnan(std):
                        newLine = [mom, float(fac), mean, std]
                        newArray.append(newLine)
                        # print(f'I will add this line: {newLine}')

                newArray = np.array(newArray)
                # print(f'newArray: {newArray}')

                ax.errorbar(newArray[:, 1] + offsets[colorI] * offsetscale,
                            newArray[:, 2],
                            yerr=newArray[:, 3],
                            fmt='d',
                            ecolor=colors[colorI],
                            color=colors[colorI],
                            capsize=2,
                            elinewidth=0.6,
                            label=f'{mom} GeV',
                            ls='dashed',
                            linewidth=0.4)
                colorI += 1

            # Adding plotting parameters
            # no titles anymore
            if False:
                if self.corrected:
                    ax.set_title(titlesCorr[i])
                else:
                    ax.set_title(titlesUncorr[i])

            ax.set_xlabel(f'Misalign Factor')
            # ax.set_xticks(np.arange(-0.25, 2, step=0.25))
            
            # set ticks exactly to the misalign factors
            start, end = ax.get_xlim()
            # ax.xaxis.set_ticks(np.arange(0.0, end, 0.25))
            ax.xaxis.set_ticks([0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5])
            ax.xaxis.set_view_interval(start, end)

            # ax.set_ylabel(f'Luminosity Error [{self.latexPercent}]')
            ax.set_ylabel(f'$\Delta L$ [{self.latexPercent}]')

            # get handles
            handles, labels = ax.get_legend_handles_labels()
            # remove the errorbars
            handles = [h[0] for h in handles]
            # use them in the legend
            # ax.legend(handles, labels, loc='upper left',numpoints=1)
            # ax.legend(handles, labels, loc='upper right',numpoints=1)
            ax.legend(handles, labels, loc='best', numpoints=1)

            # draw vertical line to separate aligned and misaligned cases
            plt.axvline(x=0.125, color=r'#aa0000', linestyle='-', linewidth=0.5)

            plt.tight_layout()

            plt.grid(color='grey', which='major', axis='y', linestyle=':', linewidth=0.5)
            plt.grid(color='grey', which='major', axis='x', linestyle=':', linewidth=0.5)
            # plt.legend()

            plt.savefig(
                # f'{fileName}-{i}.pdf',      # normal case
                f'{fileName}-{i}-uncorrected.pdf',      # for the lumi from UNcorrected UNcut data
                # f'{fileName}-{i}-subset.pdf',     # for the smaller misalign factor subset
                #This is simple recomendation for publication plots
                dpi=1000,
                # Plot will be occupy a maximum of available space
                bbox_inches='tight')
            plt.close()