#!/usr/bin/env python3

"""
General alignment script.

Usage:
    python3 runAlignment.py -p <pathToData> <type> [options]

Examples:

Box:
./runAlignment.py -p "/mnt/himsterData/roklasen/LumiFit/LMD-15.00-mmHRDIef/data/reco_uncut/no_alignment_correction/" -t box

Sensors:
./runAlignment.py -p "/mnt/himsterData/roklasen/LumiFit/LMD-15.00-dkohUogm/data/reco_uncut/no_alignment_correction/" -t sensors --externalMatrices "matrices/100u-case-1/externalMatrices-sensors.json"

Modules:
./runAlignment.py -p "/mnt/himsterData/roklasen/LumiFit/LMD-15.00-jPzRgtxO/data/reco_uncut/no_alignment_correction" -t modules --externalMatrices "matrices/100u-case-1/externalMatrices-modules.json" --anchorPoints "config/anchorPoints/anchorPoints-15.00-aligned.json"

"""

import argparse
from pathlib import Path

from src.alignment.boxAlignment import BoxAligner
from src.alignment.moduleAlignment import ModuleAligner
from src.alignment.sensorAlignment import SensorAligner


def check_required_args(args):
    if args.type == "sensors" and not args.externalMatrices:
        parser.error("The --externalMatrices argument is required for sensors type.")
    elif args.type == "modules":
        if not args.externalMatrices:
            parser.error(
                "The --externalMatrices argument is required for modules type."
            )
        if not args.anchorPoints:
            parser.error("The --anchorPoints argument is required for modules type.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run alignment")

    # Top level arguments
    parser.add_argument(
        "-p",
        "--pathToData",
        type=Path,
        default=Path(""),
        help="Path to Lumi_*.root files",
        required=True,
    )

    parser.add_argument(
        "-t",
        "--type",
        choices=["box", "sensors", "modules"],
        required=True,
        help="Type of alignment to run",
    )

    # Optional arguments that may be required based on the type chosen
    parser.add_argument(
        "--externalMatrices",
        type=Path,
        help="External matrices path for sensor or module alignment",
    )

    parser.add_argument(
        "--anchorPoints",
        type=Path,
        help="Anchor points file path for module alignment",
    )

    args = parser.parse_args()

    # Run the check to ensure required arguments are provided for specific types
    check_required_args(args)

    # switch case for alignment type
    if args.type == "sensors":
        print("Running sensor alignment")
        aligner = SensorAligner()
        aligner.alignSensors(args.pathToData)
        aligner.setExternalMatrices(args.externalMatrices)

    if args.type == "modules":
        print("Running module alignment")
        aligner = ModuleAligner()
        aligner.alignModules(args.pathToData)
        aligner.setExternalMatrices(args.externalMatrices)
        aligner.setAnchorPoints(args.anchorPoints)

    if args.type == "box":
        print("Running box alignment")
        aligner = BoxAligner()
        aligner.alignBox(args.pathToData)
