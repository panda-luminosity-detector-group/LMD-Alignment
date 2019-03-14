#!/usr/bin/env python2

from ROOT import gROOT, TFile
import argparse, subprocess, os, re

def alt1():

	parser = argparse.ArgumentParser(description='Hi there.', formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('input_dir', metavar='input_dir', type=str, nargs=1, help='')
	args = parser.parse_args()

	misaligns = [
							"/plots-0/",
							"/plots-10/",
							"/plots-50/",
							"/plots-100/",
							"/plots-200/"
							]

	for mis in misaligns:
		gROOT.Reset()
		filename = args.input_dir[0]+mis+'plab_1.5/test/fit_result_reco_2d.root'
		fdata = TFile(filename, 'READ')
		lumi_values = fdata.Get('lumi_values')
		print(mis, lumi_values[3])



"""
python plotMultipleLumiFitResults.py 
/lustre/miifs05/scratch/him-specf/paluma/roklasen/LumiFit/plab_1.5GeV/dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/no_geo_misalignment/100000/1-100_xy_m_cut_real/bunches_10/binning_300/merge_data/ 
/home/roklasen/plots-0
"""

def readLumi(fileName):
	gROOT.Reset()
	fdata = TFile(fileName, 'READ')
	lumi_values = fdata.Get('lumi_values')
	return lumi_values[3]

def fitAndPrintLumi():

	# prepare
	fitLumi = True
	PrintLumi = True

	# for momenta
	path0 = '/lustre/miifs05/scratch/him-specf/paluma/roklasen/LumiFit/'
	path1 = 'dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/'
	path2 = '/100000/1-100_xy_m_cut_real/bunches_10/binning_300/merge_data/'
	out0 = '/home/roklasen/lumiPlots/'

	scriptPath = '/home/roklasen/LuminosityFit/scripts/'
	scriptName = scriptPath + 'plotMultipleLumiFitResults.py'

	momenta = [	
		'plab_1.5GeV/',
		'plab_4.09GeV/',
		'plab_15.0GeV/'
				]

	plotMomenta = [
		'plab_1.5/',
		'plab_4.09/',
		'plab_15/'
	] 
	# for misaligns
	misaligns = [	
		'no_geo_misalignment/',
		'geo_misalignmentmisalignMatrices-SensorsOnly-10/',
		'geo_misalignmentmisalignMatrices-SensorsOnly-50/',
		'geo_misalignmentmisalignMatrices-SensorsOnly-100/',
		'geo_misalignmentmisalignMatrices-SensorsOnly-150/',
		'geo_misalignmentmisalignMatrices-SensorsOnly-200/',
		'geo_misalignmentmisalignMatrices-SensorsOnly-250/'
	]
	if fitLumi:
		for mom in momenta:
			for mis in misaligns:
				inputData = path0+mom+path1+mis+path2
				outputPath = out0+mom+mis
				# make output directories
				if not os.path.exists(outputPath):
					os.makedirs(outputPath)

				# call plot.py script, specify input dir and output
				#print(path0+mom+path1+mis+path2)
				subprocess.call(['python', scriptName, inputData, outputPath])

	if PrintLumi:
		# for misaligns in output
		for i in range(len(momenta)):
			print('---------------- ' + momenta[i] + ', ' + plotMomenta[i] + ' ----------------')
			for mis in misaligns:
				outputPath = out0+momenta[i-1] + mis + plotMomenta[i-1] + '/test/'
				fileName = outputPath + 'fit_result_reco_2d.root'
				# check if file is present
				misalignValue = '0'

				m = re.search('[0-9]{2,3}', mis)
				if m is None:
					misalignValue = '0'
				else:
					misalignValue = m.group(0)

				if not os.path.isfile(fileName):
					#print('file not found:' + fileName + '!')
					print(misalignValue + '\t&\t\\text{job error} \\\\')
					continue
				# read lumi from root file
				print(misalignValue + '\t&\t' + str(readLumi(fileName)) + '\\\\')

if __name__ == "__main__":
	print('now, with flavour!')
	fitAndPrintLumi()