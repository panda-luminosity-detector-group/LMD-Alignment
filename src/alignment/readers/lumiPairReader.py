#!/usr/bin/env python3

"""
Author: R. Klasen, roklasen@uni-mainz.de or r.klasen@gsi.de or r.klasen@ep1.rub.de

Reader class to read the Lumi_Pairs_*.root files and sorts them to numpy files.
"""

from pathlib import Path

import awkward as ak
import numpy as np
import uproot


class LumiPairReader:

    npyOutputDir = Path("temp/npPairs")
    availableModuleIDs = range(40)

    def sortPairs(self, rootFilePath: Path, maxNoOfFiles=0) -> None:
        """
        Sorts the pairs from root files to numpy files and saves them to disk.
        """
        print("Sorting pairs from root files to numpy files. This may take a while.")
        rootFileWildcard = Path("Lumi_Pairs_*.root:pndsim")

        runIndex = 0

        # delete old files
        if self.npyOutputDir.exists():
            for file in self.npyOutputDir.glob("*.npy"):
                file.unlink()

        if not self.npyOutputDir.exists():
            Path(self.npyOutputDir).mkdir(parents=True)

        for arrays in uproot.iterate(
            (rootFilePath / rootFileWildcard).__str__(),
            [
                "PndLmdHitPair._moduleID",
                "PndLmdHitPair._overlapID",
                "PndLmdHitPair._hit1",
                "PndLmdHitPair._hit2",
            ],
            # library="np", # DONT use numpy yet, we need the awkward array for the TVector3
            allow_missing=True,  # some files may be empty, skip those):
        ):
            runIndex += 1

            # some evvents have no hits, but thats not a problem
            # after the arrays are flattened, those empty events
            # simply disappear
            moduleIDs = np.array(ak.flatten(arrays["PndLmdHitPair._moduleID"]))
            overlapIDs = np.array(ak.flatten(arrays["PndLmdHitPair._overlapID"]))
            hit1x = ak.flatten(arrays["PndLmdHitPair._hit1"].fX)
            hit1y = ak.flatten(arrays["PndLmdHitPair._hit1"].fY)
            hit1z = ak.flatten(arrays["PndLmdHitPair._hit1"].fZ)
            hit2x = ak.flatten(arrays["PndLmdHitPair._hit2"].fX)
            hit2y = ak.flatten(arrays["PndLmdHitPair._hit2"].fY)
            hit2z = ak.flatten(arrays["PndLmdHitPair._hit2"].fZ)

            arr = np.array(
                (moduleIDs, hit1x, hit1y, hit1z, hit2x, hit2y, hit2z, overlapIDs)
            ).T

            for moduleID in self.availableModuleIDs:
                mask = arr[:, 0] == moduleID
                thisOverlapsArray = arr[mask][:, 1:]

                # read array from disk
                fileName = f"{self.npyOutputDir}/pairs-modID-{moduleID}.npy"

                try:
                    oldContent = np.load(fileName)
                # first run, file not already present
                except FileNotFoundError:
                    oldContent = np.empty((0, 7))

                # merge
                newContent = np.concatenate((oldContent, thisOverlapsArray))

                # write back to disk
                np.save(file=fileName, arr=newContent, allow_pickle=False)

            if runIndex == maxNoOfFiles:
                break
