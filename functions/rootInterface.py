#!/usr/bin/env python3

import json
import numpy as np

if __name__ == "main":
    print("Sorry, this module can't be run directly")

def readJSON(filename):
  with open(filename, 'r') as f:
    return json.load(f)

def misalignMatrices():
    return readJSON('matricesIdeal.json')

def readBinaryPairFile(filename):
  # read file
  f = open(filename, "r")
  fileRaw = np.fromfile(f, dtype=np.double)

  #  TODO: header checks

  # ignore header
  fileUsable =  fileRaw[6:]
  Npairs = int(len(fileUsable)/7)

  # reshape to array with one pair each line
  fileUsable = fileUsable.reshape(Npairs,7)
  return fileUsable

def readNumpyPairFile(filename):
  fileUsable = np.load(filename)
  return fileUsable

def getDigit(number, n):
  return int(number) // 10**n % 10

def getHalf(overlap):
  return getDigit(overlap, 3)

def getPlane(overlap):
  return getDigit(overlap, 2)

def getModule(overlap):
  return getDigit(overlap, 1)

def getSmallOverlap(overlap):
  return getDigit(overlap, 0)
