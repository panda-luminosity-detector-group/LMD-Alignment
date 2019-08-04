#!/usr/bin/env python3

"""
Minimum Logger object that can be passed to other objects
"""

class LMDrunLogger():
    def __init__(self):
        self.__contents__ = ''

    def log(self, item):
        self.__contents__ += item + '\n'

    def print(self):
        print(self.__contents__)

    def save(self, filename):
        with open(filename, 'w') as file:
            file.write(self.__contents__)
        print(f'Log successfully saved to {filename}!')

if __name__ == "__main__":
    print("Sorry, this module can't be run directly")
