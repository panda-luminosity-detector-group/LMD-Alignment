#!/usr/bin/env python3

"""
General alignment script.

Usage:
    python3 runAlignment.py -p <pathToData> <type> [options]

Examples:

Box:
runAlignment.py -p "/mnt/himsterData/roklasen/LumiFit/LMD-15.00-mmHRDIef/data/reco_uncut/no_alignment_correction/" box

Sensors:
runAlignment.py -p "/mnt/himsterData/roklasen/LumiFit/LMD-15.00-dkohUogm/data/reco_uncut/no_alignment_correction/" sensors --externalMatrices "matrices/100u-case-1/externalMatrices-sensors.json"

Modules:
runAlignment.py -p "/mnt/himsterData/roklasen/LumiFit/LMD-15.00-jPzRgtxO/data/reco_uncut/no_alignment_correction" modules --externalMatrices "matrices/100u-case-1/externalMatrices-modules.json" --anchorPoints "config/anchorPoints/anchorPoints-15.00-aligned.json"

"""

import argparse
from pathlib import Path

from src.alignment.boxAlignment import BoxAligner
from src.alignment.moduleAlignment import ModuleAligner
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

    subparsers = parser.add_subparsers(
        dest="type", required=True, help="Type of alignment to run"
    )

    parser_box = subparsers.add_parser(
        "box", help="Box Rotation alignment, specify path to LumiTrksQA files"
    )

    parser_sensors = subparsers.add_parser(
        "sensors", help="Align sensors, requires externalMatrices"
    )
    parser_sensors.add_argument(
        "--externalMatrices",
        type=Path,
        required=True,
        help="External matrices path for sensor alignment",
    )

    parser_modules = subparsers.add_parser(
        "modules", help="Align modules, requires externalMatrices and anchorPoints"
    )
    parser_modules.add_argument(
        "--externalMatrices",
        type=Path,
        required=True,
        help="External matrices path for module alignment",
    )
    parser_modules.add_argument(
        "--anchorPoints",
        type=Path,
        required=True,
        help="Anchor points file path for module alignment",
    )

    args = parser.parse_args()

    # switch case for alignment type
    if args.type == "sensors":
        print("Running sensor alignment")
        aligner = SensorAligner()
        aligner.setExternalMatrices(args.externalMatrices)
        aligner.alignSensors(args.pathToData)

    elif args.type == "modules":
        print("Running module alignment")
        path = "/mnt/himsterData/roklasen/LumiFit/LMD-15.00-jPzRgtxO/data/reco_uncut/no_alignment_correction"
        aligner = ModuleAligner()
        aligner.setExternalMatrices(args.externalMatrices)
        aligner.setAnchorPoints(args.anchorPoints)
        aligner.alignModules(args.pathToData)

    elif args.type == "box":
        print("Running box alignment")
        aligner = BoxAligner()
        aligner.alignBox(args.pathToData)

    else:
        print("Invalid alignment type.")
        exit(1)
