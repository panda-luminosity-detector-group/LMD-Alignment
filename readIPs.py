#!/usr/bin/env python3

import json, os, sys, glob

"""
This script iterates over lumi fit paths, collects IP poisitions and prints them to a LaTeX table.

example path:
plab_1.5GeV/dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/geo_misalignmentmisMat-modules-1.00/100000/1-500_uncut/bunches_10/binning_300/merge_data/reco_ip.json 

env:
$LMDFIT_DATA_DIR

"""

class table:
    def __init__(self, dir_path_):
        pass

def test():
    print('hi!')

if __name__ == "__main__":
    test()

    try:
        os.environ["LMDFIT_DATA_DIR"]
        path0 = os.environ["LMDFIT_DATA_DIR"] + '/'
    except:
        print('Error: environment variable "LMDFIT_DATA_DIR" not set!')
        sys.exit()

    path1 = [   "plab_1.5GeV/", "plab_15.0GeV/"   ]
    path2 = "dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/"

    # iterate over dirs
    misalignDirs = [    "no_geo_misalignment/",
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
    ]

    path3 = "*/*_uncut/bunches_*/binning_*/merge_data/reco_ip.json"
    path4 = "*/*_xy_m_cut_real/bunches_*/binning_*/merge_data/lumi-values.json"

    print('iterating over dirs...')
    dirs=0

    resultTable = 'Momentum & Misalign & $IP_x$ [mm] & $IP_y$ [mm] & $IP_z$ [mm] & Lumi Deviation [\\%] & Lumi Deviation Error [\\%] \\\\ \\hline \n'
    x, y, z = ('no data', 'no data', 'no data')
    LumiError = 'no data' 
    LumiErrorError = 'no data'

    check1, check2 = 0, 0

    # read reco_ip.json
    for mom in path1:
        for misalign in misalignDirs:

            # reset check counter
            check1, check2 = 0, 0

            # prep filename1
            filename = path0 + mom + path2 + misalign + path3

            for match in glob.glob(filename):
                check1 += 1
                with open(match) as json_file:  
                    data = json.load(json_file)
                    x, y, z = (str(round(float(data['ip_x']) * 1e1, 2)), str(round(float(data['ip_y']) * 1e1, 2)), str(round(float(data['ip_z']) * 1e1, 2)))
        
            # prep filename1
            filename2 = path0 + mom + path2 + misalign + path4
            for match2 in glob.glob(filename2):
                check2 += 1
                with open(match2) as json_file2:  
                    data2 = json.load(json_file2)
                    LumiError = str(round(float(data2['relative_deviation_in_percent']),3))
                    LumiErrorError = str(round(float(data2['relative_deviation_error_in_percent']),3))

            if check1 == 1:
                if check2 < 1:
                    LumiError = 'no data'
                elif check2 > 1:
                    continue

                dirs += 1
                mom2 = mom.replace('plab_', '')
                mom2 = mom2.replace('_', '\_')
                mom2 = mom2.replace('GeV/', ' GeV')
                misalign2 = misalign.replace('geo_misalignment', '')
                misalign2 = misalign2.replace('misalignMatrices-SensorsOnly', 'misMat-sensors')
                misalign2 = misalign2.replace('no_', 'aligned')
                misalign2 = misalign2.replace('_', '\_')
                resultTable += mom2 + ' & ' + misalign2 + ' & ' + x + ' & ' + y + ' & ' + z + ' & ' + LumiError  + ' & ' + LumiErrorError + ' \\\\ \n'
            else:
                continue

    if dirs < 1:
        print('no valid files found!')
    else:
        print('here comes the table:\n\n')
        print(resultTable)

    # put to LaTeX table