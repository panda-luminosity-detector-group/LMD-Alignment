#!/usr/bin/env python3

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import rootInterface as ri
import pairFinder as finder
import histogramers as hi
from matplotlib.colors import LogNorm
import os, sys
from matplotlib.backends.backend_pdf import PdfPages

matrices = ri.readJSON("matricesIdeal.json")

def histBinaryPairDistances(pathpre, misalign, pathpost, cutPercent=0, overlap = '0'):
  filename = pathpre + misalign + pathpost
  
  # read binary Pairs
  fileUsable = ri.readBinaryPairFile(filename)
  
  # apply dynmaic cut
  fileUsable = finder.dynamicCut(fileUsable, cutPercent)
  
  # slice to separate vectors
  hit1 = fileUsable[:, :3]
  hit2 = fileUsable[:, 3:6]
  
  # Make C a homogeneous representation of A and B
  hit1H = np.ones((len(fileUsable), 4))
  hit1H[:,0:3] = hit1
  hit2H = np.ones((len(fileUsable), 4))
  hit2H[:,0:3] = hit2
  
  # make numpy matrix from JSON info
  toSen1 = np.array(matrices[overlap]['matrix1']).reshape(4,4)
  
  # invert matrices
  toSen1Inv = np.linalg.inv(toSen1)
  
  # transform hit1 and hit2 to frame of reference of hit1
  hit1T = np.matmul(toSen1Inv, hit1H.T).T
  hit2T = np.matmul(toSen1Inv, hit2H.T).T
  
  # make differnce hit array
  dHit = hit2T[:,:3] - hit1T[:,:3 ]
  
  sigX = np.std(dHit[:,0])*1e4
  sigY = np.std(dHit[:,1])*1e4
  muX = np.average(dHit[:,0])*1e4
  muY = np.average(dHit[:,1])*1e4

  textStr = 'µx={:1.2f}µm, σx={:1.2f}µm\nµy={:1.2f}µm, σy={:1.2f}µm'.format(muX, sigX, muY, sigY)
  

  # plot differnce hit array
  fig = plt.figure(figsize=(8,4))
  fig.suptitle('{}, {}% cut'.format(misalign, cutPercent), fontsize=16)

  histA = fig.add_subplot(1, 2, 1)
  histA.hist(fileUsable[:,6], bins=150)  # this is only the z distance
  #histA.hist(np.linalg.norm(dHit, axis=1), bins=150)  # this is the vector magnitude
  histA.set_title('x-y distance [cm]')

  histB = fig.add_subplot(1, 2, 2)
  histB.hist2d(dHit[:,0], dHit[:,1], bins=150, norm=LogNorm(), range=[[-0.12, 0.12], [-0.12, 0.12]])
  
  histB.text(0.05, 0.95, textStr, transform=histB.transAxes, fontsize=12, verticalalignment='top')
  
  histB.set_title('2d distance')
  histB.set_xlabel('dx [cm]')
  histB.set_ylabel('dy [cm]')

  return fig

def hist2(pathpre, misalign, pathpost, cutPercent=0):
  filename = pathpre + misalign + pathpost
  fileUsable = ri.readBinaryPairFile(filename)
  fileUsable = finder.dynamicCut(fileUsable, cutPercent)
  
  # slice to separate vectors
  hit1 = fileUsable[:, :3]
  hit2 = fileUsable[:, 3:6]
  
  # Make C a homogeneous representation of A and B
  hit1H = np.ones((len(fileUsable), 4))
  hit1H[:,0:3] = hit1
  hit2H = np.ones((len(fileUsable), 4))
  hit2H[:,0:3] = hit2
  
  # make np matrix from JSON info
  toSen1 = np.array(matrices['27']['matrix1']).reshape(4,4)
  
  # invert matrices
  toSen1Inv = np.linalg.inv(toSen1)
  
  # transform hit1 and hit2 to frame of reference of hit1
  hit1T = np.matmul(toSen1Inv, hit1H.T).T
  hit2T = np.matmul(toSen1Inv, hit2H.T).T
  
  fig = plt.figure(figsize=(8,4))
  fig.suptitle('{}, {}% cut'.format(misalign, cutPercent), fontsize=16)

  histA = fig.add_subplot(1, 2, 1)
  histA.hist((hit2T[:,2] - hit1T[:,2]))  # this is only the z distance
  histA.set_title('x-y distance [cm]')

  histB = fig.add_subplot(1, 2, 2)
  histB.hist2d(hit1T[:,0], hit1T[:,1], bins=150, norm=LogNorm(), range=[[-1.2, 1.2], [-1.2, 1.2]])
  #histB.hist2d(hit1T[:,0], hit1T[:,1], bins=150, norm=LogNorm())
  histB.set_title('2d position')
  histB.set_xlabel('dx [cm]')
  histB.set_ylabel('dy [cm]')

def getDXDY(path, overlapID):
  filename = path + 'binaryPairFiles/pairs-' + overlapID + '-cm.bin'
  fileUsable = ri.readBinaryPairFile(filename)
  
  fileUsable = finder.dynamicCut(fileUsable, 1)

  # slice to separate vectors
  hit1 = fileUsable[:, :3]
  hit2 = fileUsable[:, 3:6]
  
  # Make C a homogeneous representation of A and B
  hit1H = np.ones((len(fileUsable), 4))
  hit1H[:,0:3] = hit1
  hit2H = np.ones((len(fileUsable), 4))
  hit2H[:,0:3] = hit2
  
  # make np matrix from JSON info
  toSen1 = np.array(matrices[overlapID]['matrix1']).reshape(4,4)
  
  #print("transforming points! overlap ID:", overlapID)
  #rint("using this matrix:\n", toSen1)

  # invert matrices
  toSen1Inv = np.linalg.inv(toSen1)
  
  # transform hit1 and hit2 to frame of reference of hit1
  hit1T = np.matmul(toSen1Inv, hit1H.T).T
  hit2T = np.matmul(toSen1Inv, hit2H.T).T
  dHit = hit2T - hit1T
  diff = np.average(dHit, axis=0)
  return diff

def histCenters():
  #pathpre = '/home/arbeit/RedPro3TB/simulationData/2018-08-himster2-'
  pathpre = '/mnt/himster2/lmdData/plab_1.5GeV/box_theta_2.0-9.0mrad_recoil_corrected/misalign_geometry/aligned/100000/1-1500_uncut/'
  pathpost = '/'
  misaligns = [
            #'aligned'
            'Pairs'
            #'misalign-10u',
            #'misalign-50u',
            #'misalign-100u',
            #'misalign-150u',
            #'misalign-200u',
            #'misalign-250u'
  ]
  for misalign in misaligns:
    # prepare
    path = pathpre + misalign + pathpost
    resultArray = np.array([])
    
    blob1 = []
    blob2 = []

    for overlapID in matrices:
      # filter array (only check subset of available overlaps)

      # ignore last plane
      if ri.getPlane(overlapID) == 3:
        pass

      tdiff = getDXDY(path, overlapID)
      if tdiff[0] < 0.75*1e-4:
        blob1.append(overlapID)
      else:
        blob2.append(overlapID)

      resultArray = np.append(resultArray, tdiff, axis=0)
    
    # resultArray contains dx and dy values for all overlaps
    resultArray = resultArray.reshape( int(len(resultArray)/4),4) * 1e4
    sigX = np.std(resultArray[:,0])
    sigY = np.std(resultArray[:,1])
    muX = np.average(resultArray[:,0])
    muY = np.average(resultArray[:,1])

    fig, ax = plt.subplots()
    ax.set_title('xy distance for ' + misalign + ' [µm]')
    ax.set_xlabel('dx [µm]')
    ax.set_ylabel('dy [µm]')
    textStr = 'µx={:1.2f}, σx={:1.2f}\nµy={:1.2f}, σy={:1.2f}'.format(muX, sigX, muY, sigY)
    ax.text(0.05, 0.95, textStr, transform=ax.transAxes, fontsize=12, verticalalignment='top')
    ax.margins(0.2)
    ax.axis('equal')
    ax.hist2d(resultArray[:,0], resultArray[:,1], bins=50, norm=LogNorm())
    
    fig.tight_layout()
    plt.savefig('./dx-dy-'+misalign+'.pdf')
    print('saved ' + misalign)
    print('left blob contains IDs:\n', blob1, "\n")
    print('right blob contains IDs:', blob2)

def histMult():
  # for 10, 50, 100, 150, 200, 250
  
  # plot cut 0, 1, 5, 10
  pathpre = '/home/arbeit/RedPro3TB/simulationData/2018-08-himster2-'
  pathpost = '/binaryPairFiles/pairs-27-cm.bin'
  misaligns = [
            'aligned'
            #'misalign-10u',
            #'misalign-50u',
            #'misalign-100u',
            #'misalign-150u',
            #'misalign-200u',
            #'misalign-250u'
  ]
  
  cuts = [0, 0.5, 1, 3]
  #cuts = [0]
  
  for misalign in misaligns:
    if not os.path.isdir(misalign):
      os.mkdir(misalign)
    for cut in cuts:
      hist2(pathpre, misalign, pathpost, cut)
      plt.savefig(misalign+'/'+str(cut)+'.pdf')

def ICPmult():

  # todo: percent bar or something
  pathpre = '/home/arbeit/RedPro3TB/simulationData/2018-08-himster2-'
  pathpost = '/'
  misaligns = [
            'aligned'
            #'misalign-10u'
            #'misalign-50u',
            #'misalign-100u',
            #'misalign-150u',
            #'misalign-200u',
            #'misalign-250u'
  ]
  
  #cuts = [5]
  cuts = [0.4, 0.6, 0.7, 0.8, 0.9]
  
  for misalign in misaligns:
    # prepare
    path = pathpre + misalign + pathpost
    
    for cut in cuts:
      targetDir = path + 'LMDmatrices-python-cut-' + str(cut) + '-2D/'
      # create target dir if need be
      if not os.path.isdir(targetDir):
        os.mkdir(targetDir)
        
      for overlapID in matrices:
        matrix = finder.findMatrix(path, overlapID, cut, matrices)
        np.savetxt('{}m{}cm.mat'.format(targetDir, overlapID), matrix, delimiter = ',')
        #np.savetxt(targetDir + 'm'+overlapID+'cm.mat', matrix, delimiter = ',')
  
  print('done')

def testOID():
  for overlapID in matrices:
    print(overlapID, ' and ', matrices[overlapID]['overlapID'])

def histCvsPythonMatrices():

  prefix = '/home/arbeit/RedPro3TB/simulationData/2018-08-himster2-'

  alignStr = 'aligned'
  #alignStr = 'misalign-10u'
  #alignStr = 'misalign-50u'
  #alignStr = 'misalign-100u'
  #alignStr = 'misalign-150u'
  #alignStr = 'misalign-200u'
  #alignStr = 'misalign-250u'

  #postfix1 = '/LMDmatrices-cut0/'

  other = '3'

  #postfix1 = '/LMDmatrices-python-cut-0-2D/'
  postfix2 = '/LMDmatrices-python-cut-' + other + '-2D/'

  #sourceDir1 = prefix + alignStr + postfix1
  sourceDir2 = prefix + alignStr + postfix2

  values = []

  # read all matrices
  for overlapID in matrices:

    if ri.getPlane(overlapID) == 3:
      #continue
      pass

    #mat1 = np.genfromtxt(sourceDir1 + 'm'+overlapID+'cm.mat', delimiter = ',')
    mat2 = np.genfromtxt(sourceDir2 + 'm'+overlapID+'cm.mat', delimiter = ',')
    #values.append((mat1-mat2)[0][3])
    #values.append((mat1-mat2)[1][3])

    values.append((mat2)[0][3])
    values.append((mat2)[1][3])

  # make numpy array
  npArray = np.array(values).reshape(int(len(values)/2),2)

  # sigX = np.std(npArray[:,0])
  # sigY = np.std(npArray[:,1])
  # muX = np.average(npArray[:,0])
  # muY = np.average(npArray[:,1])

  #print('muX:', muX*1e4, ', muY:', muY*1e4)

  # plot
  fig, ax = plt.subplots()
  ax.set_title('xy distance for ICP matrices (python vs C++) [µm]')
  ax.set_xlabel('dx [µm]')
  ax.set_ylabel('dy [µm]')
  ax.margins(0.2)
  ax.axis('equal')
  ax.hist2d(npArray[:,0]*1e4, npArray[:,1]*1e4, bins=50, norm=LogNorm())
  
  fig.tight_layout()
  plt.savefig('./pythonVsCpp-' + other + '-single.pdf')

def histPairDxDyForOverlap():
  # plot cut 0, 1, 5, 10

  overlap = '0'

  pathpre = '/home/arbeit/RedPro3TB/simulationData/2018-08-himster2-'
  pathpost = '/binaryPairFiles/pairs-' + overlap + '-cm.bin'
  misaligns = [
            #'aligned'
            #'misalign-10u',
            #'misalign-50u',
            #'misalign-100u',
            #'misalign-150u',
            'misalign-200u',
            #'misalign-250u'
  ]
  
  #cuts = [0, 0.5, 1, 3]
  cuts = [0, 2]
  
  for misalign in misaligns:
    if not os.path.isdir(misalign):
      os.mkdir(misalign)
    for cut in cuts:
      histBinaryPairDistances(pathpre, misalign, pathpost, cut, overlap)
      plt.savefig(misalign+'/'+str(cut)+'.pdf')

def histDxDyMisalignByPlane():
  
  # make single image for overlap 0 for all planes
  
  areas = [0,1,2]
  corridors = [0,1]
  halfs = [0]
  cuts = [0,3]

  # /mnt/himster2/lmdData/plab_1.5GeV/box_theta_2.0-9.0mrad_recoil_corrected/misalign_geometry/aligned/100000/1-1500_uncut/Pairs/binaryPairFiles/

  pathPre = '/home/arbeit/RedPro3TB/simulationData/2018-08-himster2-'
  #pathPre = '/mnt/himster2/lmdData/plab_1.5GeV/box_theta_2.0-9.0mrad_recoil_corrected/misalign_geometry/aligned/100000/1-1500_uncut/Pairs/'
  #pathPre = '/mnt/himster2/lmdData/plab_1.5GeV/box_theta_2.0-9.0mrad_recoil_corrected/misalign_geometry/misalignMatrices-SensorsOnly-10/100000/1-1500_uncut/Pairs/'
  
  # misalignMatrices-SensorsOnly-100
  #paths = [ 'aligned-15/']#,
          #  'misalign-100u/',
          #  'misalign-200u/']
  paths = ['misalign-100u/']

  #path = '/home/arbeit/RedPro3TB/simulationData/2018-08-himster2-aligned/'
  pdfPath = 'planePlots/'

  for thisPath in paths:
    for half in halfs:
      for corridor in corridors:
        for area in areas:
          for cut in cuts:
            # create figure with 4 spaces for plots
            fig, axes = plt.subplots(nrows=1, ncols=4, sharex=True, sharey=False, figsize=(16,4.5))
            i = 0
            for plane in range(4):
              ID = '{}'.format(half*1000 + plane*100 + corridor * 10 + area)
              path = pathPre + thisPath
              hist = hi.histogram(matrices)
              hist.histBinaryPairFileSingle_x_dx(path, ID, cut, axes[i])
              axes[i].set_title('Plane ' + str(i+1))
              i += 1
            fig.suptitle('half {}, area {}, corridor {}, cut {}%'.format(half,area,corridor,cut), fontsize=20)
            fig.tight_layout(rect=[0, 0.03, 1, 0.95])
            if not os.path.exists(pdfPath + thisPath):
              os.makedirs(pdfPath + thisPath)
            fig.savefig(pdfPath + thisPath + 'h{}area{}corr{}cut{}.pdf'.format(half,area,corridor,cut))
            plt.close()

def plotEntireCircle():
  hist = hi.histogram(matrices)
  hist.plotAllhitsonCirlce()

if __name__ == "__main__":
  print("Running...")

  #plotEntireCircle()

  #histDxDyMisalignByPlane()
  histPairDxDyForOverlap()

  #histCvsPythonMatrices()
  #histCenters()
  #testOID()
  #histMult()
  #ICPmult()

  print("all done!\n")
