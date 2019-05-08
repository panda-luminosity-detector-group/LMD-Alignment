#!/usr/bin/env python3

import json, os, sys

"""
This script iterates over lumi fit paths, collects IP poisitions and prints them to a LaTeX table.

example path:
plab_1.5GeV/dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/geo_misalignmentmisMat-modules-1.00/100000/1-500_uncut/bunches_10/binning_300/merge_data/reco_ip.json 

env:
$LMDFIT_DATA_DIR

"""

def test():
    print('hi!')

if __name__ == "__main__":
    test()

    try:
        os.environ["LMDFIT_DATA_DIR"]
        path0 = os.environ["LMDFIT_DATA_DIR"]
    except:
        print('Error: environment variable "LMDFIT_DATA_DIR" not set!')
        sys.exit()

    path1 = {   "plab_1.5GeV/", "plab_15.0GeV/"   }
    path2 = "dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/"

    # iterate over dirs
    misalignDirs = {    "no_geo_misalignment/",
                        "geo_misalignmentmisMat-modules-0.25/",
                        "geo_misalignmentmisMat-modules-0.50/",
                        "geo_misalignmentmisMat-modules-0.75/",
                        "geo_misalignmentmisMat-modules-1.00/",
                        "geo_misalignmentmisMat-modules-1.50/",
                        "geo_misalignmentmisMat-modules-2.00/",
                        "geo_misalignmentmisMat-modules-3.00/",
                        "geo_misalignmentmisalignMatrices-SensorsOnly-10/",
                        "geo_misalignmentmisalignMatrices-SensorsOnly-50/",
                        "geo_misalignmentmisalignMatrices-SensorsOnly-100/",
                        "geo_misalignmentmisalignMatrices-SensorsOnly-150/",
                        "geo_misalignmentmisalignMatrices-SensorsOnly-200/",
                        "geo_misalignmentmisalignMatrices-SensorsOnly-250/"
    }

    path3 = "100000/1-500_uncut/bunches_10/binning_300/merge_data/reco_ip.json"

    print('iterating over dirs...')
    dirs=0
    # read reco_ip.json
    for mom in path1:
        for misalign in misalignDirs:
            filename = path0 + mom + path2 + misalign + path3
            print('trying ', filename, '...')
            if os.path.isfile(filename):
                dirs += 1
                with open(filename) as json_file:  
                    data = json.load(json_file)
                    print('x: {}, y:{}, z:{}'.format(data['ip_x'],data['ip_y'], data['ip_z']))
    if dirs < 1:
        print('no valid files found!')

    # put to LaTeX table