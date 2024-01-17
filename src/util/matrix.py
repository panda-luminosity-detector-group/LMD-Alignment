import json
from pathlib import Path

import numpy as np


def baseTransform(mat: np.ndarray, matFromAtoB: np.ndarray) -> np.ndarray:
    """
    Reminder: the way this works is that the matrix pointing from pnd to sen0 transforms a matrix IN sen0 back to Pnd
    If you want to transform a matrix from Pnd to sen0, and you have the matrix to sen0, then you need to give
    this function inv(matTo0). I know it's confusing, but that's the way this works.

    Example: matrixInPanda = baseTransform(matrixInSensor, matrixPandaToSensor)
    """
    return matFromAtoB @ mat @ np.linalg.inv(matFromAtoB)


def loadMatrices(filename: Path):
    with open(filename) as f:
        result = json.load(f)
    for key, value in result.items():
        result[key] = np.array(value).reshape(4, 4)
    return result


def saveMatrices(matrices: dict, fileName: Path):
    # create path if needed
    if not Path(fileName).parent.exists():
        Path(fileName).parent.mkdir()

    # warn if overwriting
    if Path(fileName).exists():
        print(f"WARNING. Replacing file: {fileName}!\n")
        Path(fileName).unlink()

    # flatten matrices, make a copy (pass-by-reference!)
    saveMatrices = {}
    for p in matrices:
        saveMatrices[p] = np.ndarray.tolist(np.ndarray.flatten(matrices[p]))

    with open(fileName, "w") as f:
        json.dump(saveMatrices, f, indent=2, sort_keys=True)
