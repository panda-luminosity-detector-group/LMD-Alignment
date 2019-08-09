#!/usr/bin/env python3

"""
Note: of course this will somehow be line based since every line corresponds to a runConfig.

But later I want it column based, so that I can just add or remove a column to a Table, 
set it's header and specify which values from the runConfig go into the column.
Then, I want to be able to quickly assemble a complete LaTeX table with arbitrary
columns.
"""

import json

class LumiValLaTeXTable:
    def __init__(self):
        self.cols = []

    @classmethod
    def fromConfigs(cls, configs):
        temp = cls()
        temp.configs = configs
        return temp

    def show(self):
        for conf in self.configs:
            print(conf.dump())

            with open(conf.pathLumiVals()) as file:
                lumiVals = json.load(file)

            print(f'{conf.momentum} & {conf.misalignType} & {conf.misalignFactor} & {conf.alignmentCorrection} & {lumiVals["relative_deviation_in_percent"]}')

