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

def saveMatrixToJSON(matrix):
    pass

def makeHomogenous(matrix):
    shape = np.shape(matrix)
    if shape == (3,3):
        result = np.identity(4)
        result[:3,:3] = matrix
        return result
    elif shape == (3,1):
        return np.array(matrix, 1)
    elif shape == (1,3):
        return np.array(matrix, 1)
    else:
        print('ERROR! can only cast 3x3 matrices or 3x1 vectors to homogenous form')

if __name__ == "__main__":
    print('this module is not intended to be run independently.')