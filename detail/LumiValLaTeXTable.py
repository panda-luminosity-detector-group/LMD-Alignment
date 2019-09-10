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
import sys


class LumiValLaTeXTable:
    def __init__(self):
        self.cols = []

    @classmethod
    def fromConfigs(cls, configs):
        temp = cls()
        temp.configs = configs
        return temp

    def show(self):

        self.configs.sort()

        print('Beam Momentum [GeV] & Misalign Type & Misalign Factor & Corrected & Lumi Deviation [\%]')
        for conf in self.configs:

            if Path(conf.pathLumiVals()).exists():

                with open(conf.pathLumiVals()) as file:
                    lumiVals = json.load(file)

                lumi = np.round(lumiVals["relative_deviation_in_percent"][0], 3)
            else:
                lumi = 'no data!'

            print(f'{conf.momentum} & {conf.misalignType} & {conf.misalignFactor} & {conf.alignmentCorrection} & {lumi}')
