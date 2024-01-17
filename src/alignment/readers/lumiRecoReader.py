#!/usr/bin/env python3

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de or r.klasen@ep1.rub.de

Reader class to read the Lumi_recoMerged_*.root files and sorts them to numpy files.
"""

import json
from pathlib import Path

import numpy as np
import uproot


class LumiRecoReader:

    npyOutputDir = Path("temp/sectorRecos")

    # load sensorID -> sectorID mapping
    with open("config/sensorIDtoSectorID.json", "r") as f:
        sensorIDdict = json.load(f)
        sectorIDlut = np.empty(len(sensorIDdict))

        # create a look up table for fast sensorID -> sectorID translation
        for key, value in sensorIDdict.items():
            sectorIDlut[int(key)] = value

    def sortRecoHitsFromRootFilesToNumpy(self, pathToRootFiles: Path, maxNoOfFiles=0):
        """
        Read reco hits from root files.
        """

        print(f"Reading reco hits from {pathToRootFiles}. This may take a while...")
        rootFileWildcard = Path("Lumi_recoMerged_*.root:pndsim")

        # delete old files
        if self.npyOutputDir.exists():
            for file in self.npyOutputDir.glob("*.npy"):
                file.unlink()

        if not self.npyOutputDir.exists():
            self.npyOutputDir.mkdir(parents=True)

        runIndex = 0

        # for some reason, uproot doesn't like Path objects
        files = (pathToRootFiles / rootFileWildcard).__str__()

        for arrayDict in uproot.iterate(
            files,
            [
                "LMDHitsMerged.fSensorID",
                "LMDHitsMerged.fX",
                "LMDHitsMerged.fY",
                "LMDHitsMerged.fZ",
            ],
            library="np",
            allow_missing=True,  # some files may be empty, skip those
        ):
            ids = arrayDict["LMDHitsMerged.fSensorID"]
            recoX = arrayDict["LMDHitsMerged.fX"]
            recoY = arrayDict["LMDHitsMerged.fY"]
            recoZ = arrayDict["LMDHitsMerged.fZ"]

            # create mask for events that have exactly 4 hits
            fourRecoMask = [event.size == 4 for event in ids]

            # make a real 2D array from array[array[ ]]
            eventsWithFourRecos = np.stack(ids[fourRecoMask])

            # calculate module number from sensor IDs
            # use look up table for that
            # thank you TheodrosZelleke for this insanely smart idea
            # https://stackoverflow.com/a/14448935
            sectorIDfromLut = self.sectorIDlut[eventsWithFourRecos]

            # make arrays of arrays to 2d arrays
            xFlat = np.stack(recoX[fourRecoMask])
            yFlat = np.stack(recoY[fourRecoMask])
            zFlat = np.stack(recoZ[fourRecoMask])

            # now, some recos are at -10000 or something in X/Y. Fuck those.
            xMask = np.abs(xFlat) < 100
            yMask = np.abs(yFlat) < 100

            allMaskX = np.array([all(x) for x in xMask])
            allMaskY = np.array([all(x) for x in yMask])

            allMask = allMaskX & allMaskY

            # transpose to assemble and transpose again
            theseTracks = np.array(
                [
                    sectorIDfromLut[allMask].T,
                    xFlat[allMask].T,
                    yFlat[allMask].T,
                    zFlat[allMask].T,
                ]
            ).T
            # theseTracks = np.array([sectorIDfromLut.T, xFlat.T, yFlat.T, zFlat.T]).T

            # sort every 4-hit combo by z value. do this for every event.
            # this is REQUIRED for the aligner
            # I know it looks weird seeing a list comprehension here instead of something
            # more NumPythonic, but this seems to be fastest after all
            # the numpy version would probably look like this:
            # sortedResultArray = theseTracks[:,theseTracks[:,:,3].argsort()]
            # or
            # sortedResultArray = np.einsum('iijk->ijk', theseTracks[:,theseTracks[:,:,0].argsort()])
            # and be 20x slower (and require MUCH more memory)
            sortedResultArray = np.array(
                [subarray[subarray[:, 3].argsort()] for subarray in theseTracks]
            )

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

            runIndex += 1
            if runIndex == maxNoOfFiles:
                break
