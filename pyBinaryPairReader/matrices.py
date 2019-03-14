#!/usr/bin/env python3

import subprocess, sys, os
from queue import Queue
from threading import Thread

"""

full path data misalignment:
/lustre/miifs05/scratch/him-specf/paluma/roklasen/LumiFit/plab_1.5GeV/dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/100000/1-1500_uncut_misalignMatrices-SensorsOnly-100/Pairs

full path no data misalignment:
/lustre/miifs05/scratch/him-specf/paluma/roklasen/LumiFit/plab_1.5GeV/dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/100000/1-1500_uncut_no_data_misalignment/Pairs

full path no geo misalignment:
/lustre/miifs05/scratch/him-specf/paluma/roklasen/LumiFit/plab_1.5GeV/dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/no_geo_misalignment/100000/1-1500_uncut/Pairs

full path with geo misalignment:
/lustre/miifs05/scratch/him-specf/paluma/roklasen/LumiFit/plab_1.5GeV/dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/geo_misalignmentmisalignMatrices-SensorsOnly-100/100000/1-1500_uncut/Pairs

hint: use * for some paths like 10000 and 1-1500

copy (if not there):
cp ../../mc_data/Lumi_MC_1000000.root ../../mc_data/Lumi_Params_1000000.root .

NAY. don't copy, change the macros for that.
"""

"""
Minimal Thread Pool implementation from https://www.metachris.com/2016/04/python-threadpool/
"""
class Worker(Thread):
	""" Thread executing tasks from a given tasks queue """
	def __init__(self, tasks):
		Thread.__init__(self)
		self.tasks = tasks
		self.daemon = True
		self.start()

	def run(self):
		while True:
			func, args, kargs = self.tasks.get()
			try:
				func(*args, **kargs)
			except Exception as e:
				# An exception happened in this thread
				print(e)
			finally:
				# Mark this task as done, whether an exception happened or not
				self.tasks.task_done()

class ThreadPool:
	""" Pool of threads consuming tasks from a queue """
	def __init__(self, num_threads):
		self.tasks = Queue(num_threads)
		for _ in range(num_threads):
			Worker(self.tasks)

	def addTask(self, func, *args, **kargs):
		""" Add a task to the queue """
		self.tasks.put((func, args, kargs))

	def join(self):
		""" Wait for completion of all the tasks in the queue """
		self.tasks.join()


def generatePath(preset = None):

	auto = False

	if preset is None:
		preset = (1,1,1,1)
	else:
		auto = True

	mom = menuSelect(['Select Momentum:','1.5GeV', '15.0GeV'], preset[0], auto)
	thetaRange = menuSelect(['Select Theta Range:','2.7-13.0mrad', '2.0-9.0mrad', '2.0-12.0mrad'], preset[1], auto)
	misalignType = menuSelect(['Shift geometry or data?','geometry', 'data'], preset[2], auto)

	if misalignType == 'geometry':
		misalign = menuSelect([	'Select Misalignment:', 
								'no_geo_misalignment/', 
								'geo_misalignmentmisalignMatrices-SensorsOnly-10/', 
								'geo_misalignmentmisalignMatrices-SensorsOnly-50/', 
								'geo_misalignmentmisalignMatrices-SensorsOnly-100/', 
								'geo_misalignmentmisalignMatrices-SensorsOnly-200/'], 
								preset[3], auto)
		misalign += '100000/1-1500_uncut/Pairs/'	# note: maybe change 100000 and 1-1500 to * later

	elif misalignType == 'data':
		misalign = menuSelect([	'Select Misalignment:', 
								'1-1500_uncut_no_data_misalignment/', 
								'1-1500_uncut_misalignMatrices-SensorsOnly-10/', 
								'1-1500_uncut_misalignMatrices-SensorsOnly-50/', 
								'1-1500_uncut_misalignMatrices-SensorsOnly-100/', 
								'1-1500_uncut_misalignMatrices-SensorsOnly-200/'], 
								preset[3], auto)
		misalign = '100000/' + misalign + 'Pairs/'	# note: maybe change 100000 and 1-1500 to * later
	
	# testing should succeed on non-himster:
	try:
		p0 = os.environ['LMDFIT_DATA_DIR'] 
	except:
		p0 = ':TEST'
	
	p1 = '/plab_'
	p2 = '/dpm_elastic_theta_'
	p3 = '_recoil_corrected/'
	pathTotal = p0 + p1 + mom + p2 + thetaRange + p3 + misalign
	return pathTotal

def findMatrices():

	all = menuSelect(['Find all Pairs or one specifig config?', 'All', 'Just one config'], 2)

	if all == 'All':
		print('Warning! This will take a LONG time.')
		pairPaths = [	generatePath((1,1,1,1)),	# 1.5 geo align
						generatePath((1,1,1,4)),	# 1.5 geo 100u
						generatePath((1,1,1,5)),	# 1.5 geo 200u
						generatePath((1,1,2,1)),	# 1.5 data align
						generatePath((1,1,2,4)),	# 1.5 data 100u
						generatePath((1,1,2,5)),	# 1.5 data 100u
						generatePath((2,1,1,1)),	# 15 geo align
						generatePath((2,1,1,4)),	# 15 geo 100u
						generatePath((2,1,1,5)),	# 15 geo 100u
						generatePath((2,1,2,1)),	# 15 data align
						generatePath((2,1,2,4)),	# 15 data 100u
						generatePath((2,1,2,5))		# 15 data 100u
		]
	
	else:
		pairPaths = [generatePath()]
	# spawn multiple at once, maybe 4 to 6
	pool = ThreadPool(4)

	for path in pairPaths:
		print(path)
		pool.addTask(runRootMacro, path)

	pool.join()

def runRootMacro(pairPath=None):
	if pairPath is None:
		print('ERROR! Please specify pair path!')
		sys.exit(1)

	pathTotal = pairPath
	rootMacroDir = "/home/roklasen/PandaRoot/macro/detectors/lmd/"
	binaryPath = pathTotal+'binaryPairFiles/'
	matrixPath = pathTotal+'LMDmatrices/'

	# copy mc and param files
	subprocess.call(['rsync', pathTotal + '../../mc_data/Lumi_MC_1000000.root', pathTotal + '../../mc_data/Lumi_Params_1000000.root', pathTotal])
	macroArg = rootMacroDir+'runLumiPixel2fMatrixFinder.C("' + pairPath + '","' + binaryPath + '","' + matrixPath + '",true,0)'
	
	# run root
	subprocess.call(['root','-q','-l',macroArg])
	

def test():
	
	#all = input('enter "all" to start all matrix finders (1.5 / 15 GeV, all misalignments), [enter] for individual selection:')
	testPaths = [	generatePath((1,1,1,1)),
					generatePath((1,1,1,4)),
					generatePath((1,1,2,1)),
					generatePath((1,1,2,4))
	]

	# compare with known paths for testing
	pathEx = (	':TEST/plab_1.5GeV/dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/100000/1-1500_uncut_no_data_misalignment/Pairs/',
				':TEST/plab_1.5GeV/dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/no_geo_misalignment/100000/1-1500_uncut/Pairs/',
				':TEST/plab_1.5GeV/dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/geo_misalignmentmisalignMatrices-SensorsOnly-100/100000/1-1500_uncut/Pairs/',
				':TEST/plab_1.5GeV/dpm_elastic_theta_2.7-13.0mrad_recoil_corrected/100000/1-1500_uncut_misalignMatrices-SensorsOnly-100/Pairs/'
	)
	
	for path in testPaths:
		if path not in pathEx:
			print('path comparison error!')
			#print('0:', path)
			#for p in pathEx:
			#	print('-:', p)
		else:
			print('path comparison ok!')

def menuSelect(options, default=0, auto=False):
	
	if auto:
		if default < 0 or default > len(options)-1:
			print('invalid default option and auto!')
			sys.exit()
		else:
			#print(options[0], options[default], ' (auto selected)')
			return options[default]
	
	print(options[0])
	print('[0]: exit')

	# print menu
	for i in range(1, len(options)):
		print('[{}]:'.format(i), options[i], end='')
		if default == i:
			print(' <-default->')
		else:
			print('')
	
	# get user input
	try:
		choice = input('Selection: ')
		if choice == '' and default != 0:
			return options[default]
		else:
			choice = int(choice)
	except:
		print('invalid entry, somehow!')
		sys.exit()

	# return user selection
	if choice == 0:
		print('exiting!')
		sys.exit()
	if choice < 0 or choice > len(options)-1:
		print('invalid entry!')
		sys.exit()
	return options[choice]

if __name__ == '__main__':
	
	#test()

	findMatrices()

	print('all done!')
