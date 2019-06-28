#!/usr/bin/env python3
import json, os, sys, glob

"""
This script iterates over lumi fit paths, collects IP poisitions and prints them to a LaTeX table.

example path:
plab_1.5GeV/dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/geo_misalignmentmisMat-modules-1.00/100000/1-500_uncut/bunches_10/binning_300/merge_data/reco_ip.json 

new example:
plab_1.5GeV/dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/geo_misalignmentmisMat-identity-1.00/100000/1-100_xy_m_cut_real/bunches_10/binning_300/merge_data

env:
$LMDFIT_DATA_DIR

"""

"""
TODO: 
- cleanup functions
- better latex table generation
"""

class table:
    def __init__(self, dir_path_):
        pass

def test():
    
    try:
        os.environ["LMDFIT_DATA_DIR"]
        # should be /lustre/miifs05/scratch/him-specf/paluma/roklasen/LumiFit
        path0 = os.environ["LMDFIT_DATA_DIR"] + '/'
    except:
        print('INFO: environment variable "LMDFIT_DATA_DIR" not set! Assuming test environment.')
        path0 = os.getcwd() + '/input/lustre/miifs05/scratch/him-specf/paluma/roklasen/LumiFit/'
        #sys.exit()

    path1 = [   "plab_1.5GeV/" ]#, "plab_4.06GeV/", "plab_8.9GeV/", "plab_15.0GeV/"   ]
    path2 = "dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/"

    # iterate over misalign dirs
    misalignDirs = [    "no_geo_misalignment/",
                        # "geo_misalignmentmisMat-box-0.25/",
                        # "geo_misalignmentmisMat-box-0.50/",
                        # "geo_misalignmentmisMat-box-1.00/",
                        # "geo_misalignmentmisMat-box-2.00/",
                        # "geo_misalignmentmisMat-box-3.00/",
                        # "geo_misalignmentmisMat-box-5.00/",
                        # "geo_misalignmentmisMat-box-10.00/",
                        # "geo_misalignmentmisMat-combi-0.50/",
                        # "geo_misalignmentmisMat-combi-1.00/",
                        # "geo_misalignmentmisMat-combi-2.00/",
                        "geo_misalignmentmisMat-identity-1.00/"
                        # "geo_misalignmentmisMat-modules-0.01/",
                        # "geo_misalignmentmisMat-modules-0.05/",
                        # "geo_misalignmentmisMat-modules-0.10/",
                        # "geo_misalignmentmisMat-modules-0.15/",
                        # "geo_misalignmentmisMat-modules-0.25/",
                        # "geo_misalignmentmisMat-modules-0.50/",
                        # "geo_misalignmentmisMat-modules-0.75/",
                        # "geo_misalignmentmisMat-modules-1.00/",
                        # "geo_misalignmentmisMat-modules-1.50/",
                        # "geo_misalignmentmisMat-modules-2.00/",
                        # "geo_misalignmentmisMat-modules-3.00/",
                        # "geo_misalignmentmisalignMatrices-SensorsOnly-10/",
                        # "geo_misalignmentmisalignMatrices-SensorsOnly-50/",
                        # "geo_misalignmentmisalignMatrices-SensorsOnly-100/",
                        # "geo_misalignmentmisalignMatrices-SensorsOnly-150/",
                        # "geo_misalignmentmisalignMatrices-SensorsOnly-200/",
                        # "geo_misalignmentmisalignMatrices-SensorsOnly-250/"
    ]

    # this comes in aligned and non-aligned
    path3 = "*/*_uncut*/bunches_*/binning_*/merge_data/reco_ip.json"
    
    # this comes in aligned and non-aligned
    path4 = "*/*_xy_m_cut_real*/bunches_*/binning_*/merge_data/lumi-values.json"

    print('iterating over dirs...')
    dirs=0

    resultTable = 'Momentum & Misalign & $IP_x$ [mm] & $IP_y$ [mm] & $IP_z$ [mm] & Lumi Dev. [\\%] & Lumi Dev. Err [\\%] \\\\ \\hline \n'
    x, y, z = ('no data', 'no data', 'no data')
    LumiError = 'no data' 
    LumiErrorError = 'no data'

    check1, check2 = 0, 0

    # TODO: reorder nested for loops, loop over align path first, then grab and loop over all aligned/nonaligned paths, then grab reco_ip and lumi_values

    # read reco_ip.json
    for mom in path1:
        for misalign in misalignDirs:
            
            #! ------------ new part
            # construct align path
            alignPath = path0 + mom + path2 + misalign

            # print(alignPath)

            # match all reco ips
            for matchReco in glob.glob(alignPath + path3):
                
                # is this an aligned case?
                aligned = '_aligned/' in matchReco

                # print(f'match 1: {matchReco}')

                # extract values
                with open(matchReco) as json_file:  
                    dataReco = json.load(json_file)
                    x, y, z = (str(round(float(dataReco['ip_x']) * 1e1, 2)), str(round(float(dataReco['ip_y']) * 1e1, 2)), str(round(float(dataReco['ip_z']) * 1e1, 2)))


                # then, match all lumi values but filter by aligned or not
                for matchLumi in glob.glob(alignPath + path4):

                    #filter by current aligned-flag
                    if ('_aligned/' in matchLumi) == aligned:
                        
                        # print(f'match 2: {matchLumi}')

                        # extract values
                        with open(matchLumi) as json_file2:  
                            dataLumi = json.load(json_file2)
                            LumiError = str(round(float(dataLumi['relative_deviation_in_percent']),3))
                            LumiErrorError = str(round(float(dataLumi['relative_deviation_error_in_percent']),3))

                        # clean and store data. if something fails, the combination is simply skipped
                        # TODO: put in separate function
                        dirs += 1
                        mom2 = mom.replace('plab_', '')
                        mom2 = mom2.replace('_', '\_')
                        mom2 = mom2.replace('GeV/', ' GeV')
                        misalign2 = misalign.replace('geo_misalignment', '')
                        misalign2 = misalign2.replace('/', '')
                        # misalign2 = misalign2.replace('misalignMatrices-SensorsOnly', 'misMat-sensors')
                        misalign2 = misalign2.replace('no_', 'aligned')
                        if aligned:
                            misalign2 += ', corrected'
                        misalign2 = misalign2.replace('_', '\_')
                        resultTable += mom2 + ' & ' + misalign2 + ' & ' + x + ' & ' + y + ' & ' + z + ' & ' + LumiError  + ' & ' + LumiErrorError + ' \\\\ \n'

                    # wrong aligned / non-aligned combination
                    # else:
                    #     print('no match')

    print('here comes the table:\n\n')
    print(resultTable)

            #! ------------ old part
            
            # # reset check counter
            # check1, check2 = 0, 0

            # # prep filename1
            # filename = path0 + mom + path2 + misalign + path3
            # print(f'file path: {filename}')

            # for match in glob.glob(filename):
            #     check1 += 1
            #     with open(match) as json_file:  
            #         data = json.load(json_file)
            #         x, y, z = (str(round(float(data['ip_x']) * 1e1, 2)), str(round(float(data['ip_y']) * 1e1, 2)), str(round(float(data['ip_z']) * 1e1, 2)))
        
            # # prep filename1
            # filename2 = path0 + mom + path2 + misalign + path4
            # for match2 in glob.glob(filename2):
            #     check2 += 1
            #     with open(match2) as json_file2:  
            #         data2 = json.load(json_file2)
            #         LumiError = str(round(float(data2['relative_deviation_in_percent']),3))
            #         LumiErrorError = str(round(float(data2['relative_deviation_error_in_percent']),3))

            # if check1 == 1:
            #     if check2 < 1:
            #         LumiError = 'no data'
            #         LumiErrorError = 'no data'
            #     elif check2 > 1:
            #         print('second path is ambigous.')
            #         continue

            #     dirs += 1
            #     mom2 = mom.replace('plab_', '')
            #     mom2 = mom2.replace('_', '\_')
            #     mom2 = mom2.replace('GeV/', ' GeV')
            #     misalign2 = misalign.replace('geo_misalignment', '')
            #     misalign2 = misalign2.replace('misalignMatrices-SensorsOnly', 'misMat-sensors')
            #     misalign2 = misalign2.replace('no_', 'aligned')
            #     misalign2 = misalign2.replace('_', '\_')
            #     resultTable += mom2 + ' & ' + misalign2 + ' & ' + x + ' & ' + y + ' & ' + z + ' & ' + LumiError  + ' & ' + LumiErrorError + ' \\\\ \n'
            # elif check1 > 1:
            #   print('first path is ambigous!')

            # else:
            #     print('wait wat')
            #     continue

    # if dirs < 1:
    #     print('no valid files found!')
    # else:
    #     print('here comes the table:\n\n')
    #     print(resultTable)

    # put to LaTeX table


if __name__ == "__main__":
    
    print('hi there!')
    test()
    print('all done.')
    
