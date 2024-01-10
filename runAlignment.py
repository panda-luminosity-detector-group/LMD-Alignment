#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

from src.alignment.boxAlignment import BoxAligner
from src.alignment.sensorAlignment import SensorAligner

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run alignment")

    parser.add_argument(
        "-e",
        "--expConfig",
        type=Path,
        default=Path(""),
        help="Path to the experimentConfig.json file",
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

    # load experiment config
    with open(args.expConfig) as f:
        expConfig = json.load(f)

    # switch case for alignment type
    if args.type == "sensors":
        print("Running sensor alignment")
        path = "/mnt/himsterData/roklasen/LumiFit/LMD-15.00-dkohUogm/data/reco_uncut/aligned-alignment-matrices/"
        aligner = SensorAligner()
        aligner.alignSensors(path)


    elif args.type == "modules":
        print("Running module alignment")
        # run module alignment

    elif args.type == "box":
        print("Running box alignment")
        path = "/mnt/himsterData/roklasen/LumiFit/LMD-15.00-mmHRDIef/data/reco_uncut/aligned-alignment-matrices/"
        aligner = BoxAligner()
        aligner.alignBox(path)

    else:
        print("Invalid alignment type.")
        exit(1)
