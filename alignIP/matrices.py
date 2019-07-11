#!/usr/bin/env python3

import json
import numpy as np

def readJSON(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def getMatrixFromJSON(jsonFile, path):
    json = readJSON(jsonFile)
    data = json[path]
    matrix = np.array(data)
    matrix = np.reshape(matrix, (4,4))
    return matrix

def makeHomogenous(matrix):
    shape = np.shape(matrix)
    if shape != (3,3):
        print('ERROR! can only cast 3x3 matrices to homogenous form')
    result = np.identity(4)
    result[:3,:3] = matrix
    return result

if __name__ == "__main__":
    print('this module is not intended to be run independently.')