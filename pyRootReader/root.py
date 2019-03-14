#!/usr/bin/env python3

import sys
sys.path.append('../..')
from ROOT import gROOT, TFile, TGraph2DErrors
import matplotlib.pyplot as plt
import matplotlib
from matplotlib import colors
from numpy.random import rand
from matplotlib.colors import LinearSegmentedColormap
import colormaps
import argparse
import copy
import math

font = {'family' : 'sans-serif',
        'serif'  : ['Helvetica'],
        'weight' : 'normal',
        'size'   : 18}
        
matplotlib.rc('font', **font)

plt.register_cmap(name='viridis', cmap=colormaps.viridis)

custom_map = LinearSegmentedColormap.from_list(name='custom_div_cmap', 
                                             colors =['b', 'g', 'r'],
                                             N=50)

class MyHist:
    def __init__(self):
        self.bins_x=0
        self.bins_y=0
        self.x_vals = []
        self.y_vals = []
        self.z_vals = []
        self.widths = []
        self.x_range = []
        self.y_range = []
        self.x_label = ''
        self.y_label = ''
        self.z_label = ''
   
class PlotCollection:
    def __init__(self, filename):
      self.name_dict = dict()
      self.data_dict = dict()
    
      self.name_dict['model'] = 'model'
      self.name_dict['data'] = 'data'
    
      self.extractData(filename)
      self.createRelativeDifference()
    
    def extractData(self, filename):
        #open file
        fdata = TFile(filename, 'READ')
        
        self.lumi_values = fdata.Get('lumi_values')

        for key,value in self.name_dict.items():
          temp=MyHist()
          hist = fdata.Get(value)
          temp.x_label = hist.GetXaxis().GetTitle()
          temp.y_label = hist.GetYaxis().GetTitle()
          temp.z_label = hist.GetZaxis().GetTitle()

          temp.bins_x = hist.GetNbinsX()
          temp.bins_y = hist.GetNbinsY()
          temp.x_range = [hist.GetXaxis().GetBinLowEdge(1), hist.GetXaxis().GetBinUpEdge(hist.GetNbinsX())]
          temp.y_range = [hist.GetYaxis().GetBinLowEdge(1), hist.GetYaxis().GetBinUpEdge(hist.GetNbinsY())]
          for ix in range(1, hist.GetNbinsX()+1):
            for iy in range(1, hist.GetNbinsY()+1):
                #if hist.GetBinContent(ix, iy) != 0.0:
                  #print(hist.GetXaxis().GetBinCenter(ix), hist.GetYaxis().GetBinCenter(iy),hist.GetBinContent(ix, iy))
                temp.x_vals.append(hist.GetXaxis().GetBinCenter(ix))
                temp.y_vals.append(hist.GetYaxis().GetBinCenter(iy))
                temp.z_vals.append(hist.GetBinContent(ix, iy))
                temp.widths.append(hist.GetXaxis().GetBinWidth(ix))

          self.data_dict[key] = temp      
  
    def createRelativeDifference(self):
      print('creating relative difference...')
      reldiff=copy.deepcopy(self.data_dict['data'])
      model=self.data_dict['model']
      counter=0
      for (z, mz) in zip(reldiff.z_vals, model.z_vals):
        if z > 0:
          #found=[mz for mx,my,mz in zip(model.x_vals, model.y_vals, model.z_vals) if mx==x and my==y]
          reldiff.z_vals[counter]=(mz-z)/math.sqrt(z)
        counter=counter+1
      self.data_dict['reldiff'] = reldiff
      print('done!')
      
    def getHist(self, key):
        return self.data_dict[key]

def makePlot(data_hist, output_filename, lumi_values=None, label='rec'):
  plt.clf()
  max_value = sorted([abs(i) for i in data_hist.z_vals])[-1]
  #print max_value

  if lumi_values:
    if max_value > 5.0:
      max_value = 5.0
    H, xedges, yedges, img  = plt.hist2d(data_hist.x_vals, data_hist.y_vals, bins=[data_hist.bins_x, data_hist.bins_y],
                                          norm=None, weights=data_hist.z_vals,
                                           range=[data_hist.x_range,data_hist.y_range], alpha=0.8, cmap=plt.get_cmap('bwr'), vmin=-max_value, vmax=max_value)
    plt.figtext(0.50, 0.81, '$\\frac{\Delta L}{L} = '+'{:.3f}'.format(lumi_values[3]) + '\pm {:.3f}'.format(lumi_values[4])+'\%$' ,
          verticalalignment='bottom', horizontalalignment='left',
          #transform=plt.transAxes,
          color='black', fontsize=18)
  else:   
    H, xedges, yedges, img  = plt.hist2d(data_hist.x_vals, data_hist.y_vals, bins=[data_hist.bins_x, data_hist.bins_y],
                                          norm=None, weights=data_hist.z_vals,
                                           range=[data_hist.x_range,data_hist.y_range], alpha=0.8, cmap=plt.get_cmap('viridis'), cmin=0.000001)
  ax = plt.gca()
  ax.set_xlabel('$\\theta^{\mathrm{'+label+'}}_x\,/\\mathrm{mrad}$')
  ax.set_ylabel('$\\theta^{\mathrm{'+label+'}}_y\,/\\mathrm{mrad}$')
  cbar = plt.colorbar(img, pad=0.0)
  if lumi_values:
    cbar.set_label(r'$\frac{\mathrm{Model}-\mathrm{Data}}{\mathrm{Error_{Data}}}$')
  else:
    cbar.set_label('$\mathrm{\#\,Events}$')

  plt.savefig(output_filename, bbox_inches='tight')


parser = argparse.ArgumentParser(description='', formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument('input_dir', metavar='input_dir', type=str, nargs=1, help='')

args = parser.parse_args()


gROOT.Reset()
#open file

pc = PlotCollection(args.input_dir[0]+'/fit_result_reco_2d.root')

makePlot(pc.getHist('data'), args.input_dir[0]+'/data_2d.png')
makePlot(pc.getHist('model'), args.input_dir[0]+'/model_2d.png')
makePlot(pc.getHist('reldiff'), args.input_dir[0]+'/reldiff_2d.png', pc.lumi_values)

