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

# TODO: express homogenization and de-homogenization with 4x4 matrices! it's pretty easy!
def makeHomogenous(matrix):
    shape = np.shape(matrix)
    if np.shape(matrix) == (3,):
        matrix = matrix[np.newaxis]
    shape = np.shape(matrix)
    if shape == (3,3):
        result = np.identity(4)
        result[:3,:3] = matrix
        return result
    elif shape == (1,3):
        result = np.ones((1,4))
        result[0, :3] = matrix[0,:]
        return result
    elif shape == (3,1):
        result = np.ones((4,1))
        result[:3, 0] = matrix[:,0]
        return result
    elif shape == (4,4):
        # dehomogenize, sue me
        result = np.identity(3)
        result = matrix[:3, :3]
        return result
    else:
        print('ERROR! can only cast 3x3 matrices or 3x1 vectors to homogenous form')
        print('(or de-homogenize the other way round)')

if __name__ == "__main__":
    print('this module is not intended to be run independently.')