#!/usr/bin/env python3

import argparse
from pathlib import Path

from src.alignment import boxAlign, moduleAlign, sensorAlign

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run alignment")

    parser.add_argument('-e', '--expConfig', type=Path, default=Path(''), help='Path to the experimentConfig.json file', required=True)
    parser.add_argument('-t', '--type', type=str, default='none', help='Type of alignment to run: [sensors, modules, box]', required=True)

    args = parser.parse_args()

    # switch case for alignment type
    if args.type == 'sensors':
        print('Running sensor alignment')
        # run sensor alignment
    elif args.type == 'modules':
        print('Running module alignment')
        # run module alignment
    elif args.type == 'box':
        print('Running box alignment')
        # run box alignment
    else:
        print('Invalid alignment type.')
        exit(1)