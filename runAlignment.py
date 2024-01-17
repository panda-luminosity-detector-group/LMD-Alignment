#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

from src.alignment.boxAlignment import BoxAligner
from src.alignment.moduleAlign import ModuleAligner
from src.alignment.sensorAlignment import SensorAligner

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run alignment")

    parser.add_argument(
        "-p",
        "--pathToData",
        type=Path,
        default=Path(""),
        help="Path to the Lumi_*.root files (Lumi_Reco_* for module alignment, Lumi_Pairs_* for sensor alignment, Lumi_TrksQA_* for box alignment)",
        required=True,
    )
    parser.add_argument(
        "-t",
        "--type",
        type=str,
        default="none",
        help="Type of alignment to run: [sensors, modules, box]",
        required=True,
    )

    args = parser.parse_args()

    # switch case for alignment type
    if args.type == "sensors":
        print("Running sensor alignment")
        path = "/mnt/himsterData/roklasen/LumiFit/LMD-15.00-dkohUogm/data/reco_uncut/aligned-alignment-matrices/"
        aligner = SensorAligner()
        aligner.setExternalMatrices(
            "matrices/100u-case-1/externalMatrices-sensors.json"
        )
        aligner.alignSensors(path)

    elif args.type == "modules":
        print("Running module alignment")
        path = "src/util/lmd-1.5-Vf.csv"  # TODO: change for root files, not csv
        aligner = ModuleAligner()
        aligner.setExternalMatrices(
            "matrices/100u-case-1/externalMatrices-modules.json"
        )
        aligner.setAnchorPoints("config/anchorPoints/anchorPoints-1.5-aligned.json")
        aligner.alignModules(path)

    elif args.type == "box":
        print("Running box alignment")
        path = "/mnt/himsterData/roklasen/LumiFit/LMD-15.00-mmHRDIef/data/reco_uncut/aligned-alignment-matrices/"
        aligner = BoxAligner()
        aligner.alignBox(path)

    else:
        print("Invalid alignment type.")
        exit(1)
