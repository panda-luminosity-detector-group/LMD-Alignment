#!/usr/bin/env python3

import json, os, sys

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
    path4 = "100000/1-100_xy_m_cut_real/bunches_10/binning_300/merge_data/lumi-values.json"

    print('iterating over dirs...')
    dirs=0

    resultTable = 'Momentum & Misalign & $IP_x$ & $IP_y$ & $IP_z$ & Lumi Error'
    x, y, z = ('ERR', 'ERR', 'ERR')
    LumiError = 'FIT FAILED' 

    # read reco_ip.json
    for mom in path1:
        for misalign in misalignDirs:
            filename = path0 + mom + path2 + misalign + path3
            #print('trying ', filename, '...')
            if os.path.isfile(filename):
                dirs += 1
                with open(filename) as json_file:  
                    data = json.load(json_file)
                    x, y, z = (data['ip_x'],data['ip_y'], data['ip_z'])
                    print('x: {}, y:{}, z:{}'.format(x, y, z))
            else:
                print('no reco IP values found')
                x, y, z = ('ERR', 'ERR', 'ERR')

            filename2 = path0 + mom + path2 + misalign + path4
            if os.path.isfile(filename2):
                with open(filename2) as json_file2:  
                    data2 = json.load(json_file2)
                    LumiError = str(data2['relative_deviation_in_percent'])
                    print('error:{}'.format(LumiError))
            else:
                print('no lumi values found')
                LumiError = 'FIT FAILED'
            
            resultTable += mom + ' & ' + misalign + ' & ' + x + ' & ' + y + ' & ' + z + ' & ' + LumiError + '\n'

    if dirs < 1:
        print('no valid files found!')
    else:
        print('here comes the table:\n\n', resultTable)

    # put to LaTeX table