#!/usr/bin/env python3

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de or r.klasen@ep1.rub.de

Reader class to read the csv file containing reco hits and sorts them to numpy files.
"""

import json
from pathlib import Path

import numpy as np


class RecoCSVReader:
    npyOutputDir = Path("temp/sectorRecos")

    # load sensorID -> sectorID mapping
    with open("config/sensorIDtoSectorID.json", "r") as f:
        sensorIDdict = json.load(f)
        sectorIDlut = np.empty(len(sensorIDdict))

        # create a look up table for fast sensorID -> sectorID translation
        for key, value in sensorIDdict.items():
            sectorIDlut[int(key)] = value

    def readRecoHitsFromCSVFile(self, filename: Path) -> np.ndarray:
        """
        Reads reco hits from a csv file and returns them as a numpy array.
        """
        print(f"reading reco hits from {filename}...")

        csvValues = np.genfromtxt(filename, delimiter=",")
        # check if there really are n times 4 elements
        if len(csvValues) % 4 != 0:
            raise ValueError("entries are not a multiple of 4!")

        nEvents = int(len(csvValues) / 4)

        ids = np.array(csvValues[:, 0], dtype=int)
        csvValues[:, 0] = self.sectorIDlut[ids]

        csvValues = csvValues.reshape((nEvents, 4, 4))

        return csvValues

    def sortCSVtoNumpy(self, filename: Path) -> None:
        """
        Sorts reco hits from a csv file to numpy files and saves them to disk.
        """
        print(f"sorting reco hits from {filename} to numpy files...")

        # delete old files
        if self.npyOutputDir.exists():
            for file in self.npyOutputDir.glob("*.npy"):
                file.unlink()

        if not self.npyOutputDir.exists():
            self.npyOutputDir.mkdir(parents=True)

        sortedResultArray = self.readRecoHitsFromCSVFile(filename)

        # sort this to 10 numpy files, one for each sector
        for iSector in range(10):
            sectorMask = sortedResultArray[:, 0, 0] == iSector

            # create new empty array thay has the required structure
            sectorTracksXYZ = sortedResultArray[sectorMask][:, :, 1:4]
            nTrks = len(sectorTracksXYZ)

            # assign recos from input array to new array for this sector
            trackVectorForAligner = np.ones((nTrks, 6, 4))
            trackVectorForAligner[:, 2:6, :3] = sectorTracksXYZ[:, 0:4]

            # read array from disk
            fileName = f"{self.npyOutputDir}/sectorID-{iSector}.npy"

            try:
                oldContent = np.load(fileName)
            # first run, file not already present
            except FileNotFoundError:
                oldContent = np.empty((0, 6, 4))

            # merge
            newContent = np.concatenate((oldContent, trackVectorForAligner))

            # write back to disk
            np.save(file=fileName, arr=newContent, allow_pickle=False)
