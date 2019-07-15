#!/usr/bin/env python3

from pathlib import Path

"""
pathlib wrappr specifically for our LMD case. 

uses pathlib internally and stores some additional values as well:

- alignment matrix used
- misalignment matrix used
- alignment factor
- beam momentum

handles these things implicitly:
- uses json matrices by default
- converts root matrices to json matrices (using ROOT)
"""



class LMDpath:

    def __init__(self, path):
        self._path = Path(path)

        self._alignMat = findAlignMat()
        self._misalignMat = findMisalignMat()
        self._alignFactor = findAlignFactor()
        self._momentum = findMomentum()

    def __init__(self):
        print('no path specified')


if __name__ == "__main__":
    if __name__ == "main":
    print("Sorry, this module can't be run directly")