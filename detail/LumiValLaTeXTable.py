#!/usr/bin/env python3

"""
Note: of course this will somehow be line based since every line corresponds to a runConfig.

But I want it column based, so that I can just add or remove a column to a Table, 
set it's header and specify which values from the runConfig go into the column.
Then, I want to be able to quickly assemble a complete LaTeX table with arbitrary
columns.
"""

import json

class LumiValLaTeXTable:
    def __init__(self):
        self.cols = []
        print(f'much LaTeX!')

    @classmethod
    def fromConfigs(cls, configs):
        print(f'yay! from configs!')
        temp = cls()
        temp.configs = configs
        return temp

    def addColumn(self, column):
        self.cols.append(column)
        pass

    def show(self):
        for conf in self.configs:
            print(conf.dump())
            print(f'nothing more to show!')

            with open(conf.pathLumiVals()) as file:
                lumiVals = json.load(file)

            print(f'{conf.momentum} & {conf.misalignType} & {conf.misalignFactor} & {conf.alignmentCorrection} & {lumiVals["relative_deviation_in_percent"]}')

        # TODO: main assembly loop: loop over columns, THEN runConfigs
        for col in self.cols:
            print(f'I am a column! Header: {col.header}')

class column:
    def __init__(self, valueInRunConfig):
        print(f'empty column')
        self.header = 'Header!'
    def val(self):
        pass


class colLumiDev(column):
    def __init__(self):
        pass
    pass


# TODO: inherit from column here and implement manually ffs