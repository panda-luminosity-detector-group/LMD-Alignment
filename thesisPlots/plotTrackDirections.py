#!/usr/bin/env python3

import matplotlib.pyplot as plt
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import uproot
import sys

latexmu = r'\textmu{}'
latexsigma = r'\textsigma{}'
latexPercent = r'\%'
plt.rc('font', **{'family': 'serif', 'serif': ['Palatino'], 'size': 10})
plt.rc('text', usetex=True)
plt.rc('text.latex', preamble=r'\usepackage[euler]{textgreek}')


def plot(inputFile, outputFile, title):

    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm

    plt.rc('font', **{'family': 'serif', 'serif': ['Palatino'], 'size': 10})
    plt.rc('text', usetex=True)
    plt.rc('text.latex', preamble=r'\usepackage[euler]{textgreek}')

    # plot difference hit array
    fig = plt.figure(figsize=(6 / 2.54, 6 / 2.54))
    newTracks = np.load(inputFile)

    axis = fig.add_subplot(1, 1, 1)
    axis.hist2d(newTracks[:, 1, 0] * 1e4 - 425, newTracks[:, 1, 1] * 1e4, bins=50, norm=LogNorm(), label='Count (log)')  #, range=((-300,300), (-300,300)))
    fig.suptitle(title)
    axis.yaxis.tick_left()
    axis.set_xlabel(r'$\vec{p}_x$ [µm]')
    axis.set_ylabel(r'$\vec{p}_y$ [µm]')
    axis.tick_params(direction='out')
    axis.yaxis.set_label_position("left")

    # axis2 = fig.add_subplot(1,2,2)
    # axis2.hist(newTracks[:, 1, 2]*1e4, bins=50)#, range=((-300,300), (-300,300)))
    # axis2.set_title(f'pz')
    # axis2.yaxis.tick_right()
    # axis2.set_xlabel('pz [µm]')
    # axis2.set_ylabel('count')
    # axis2.yaxis.set_label_position("right")

    fig.tight_layout()
    fig.savefig(outputFile, dpi=1000, bbox_inches='tight')
    plt.close(fig)


def TriplePlot(in1, in2, in3, outF):
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm

    plt.rc('font', **{'family': 'serif', 'serif': ['Palatino'], 'size': 10})
    plt.rc('text', usetex=True)
    plt.rc('text.latex', preamble=r'\usepackage[euler]{textgreek}')

    # plot difference hit array
    fig = plt.figure(figsize=(16 / 2.54, 7 / 2.54))
    newTracks = np.load(in1)

    axis = fig.add_subplot(1, 3, 1)
    axis.hist2d(newTracks[:, 1, 0] * 1e4 - 425, newTracks[:, 1, 1] * 1e4, bins=50, norm=LogNorm(), label='Count (log)')  #, range=((-300,300), (-300,300)))
    axis.set_title('Before Alignment')
    axis.yaxis.tick_left()
    axis.set_xlabel(r'$\vec{p}_x$ [µm]')
    axis.set_ylabel(r'$\vec{p}_y$ [µm]')
    axis.tick_params(direction='in')
    axis.yaxis.set_label_position("left")

    xmin, xmax = axis.get_xlim()
    ymin, ymax = axis.get_ylim()

    thisrange = [[xmin, xmax], [ymin, ymax]]

    newTracks2 = np.load(in2)
    axis2 = fig.add_subplot(1, 3, 2, sharey=axis)
    axis2.hist2d(newTracks2[:, 1, 0] * 1e4 - 425, newTracks2[:, 1, 1] * 1e4, bins=50, norm=LogNorm(), label='Count (log)', range=thisrange)
    axis2.set_title('After Direction Cut')
    axis2.set_xlabel(r'$\vec{p}_x$ [µm]')
    axis2.set_yticklabels([])
    axis2.tick_params(direction='in')
    # axis2.yaxis.set_label_position("left")

    newTracks3 = np.load(in3)
    axis3 = fig.add_subplot(1, 3, 3, sharey=axis)
    axis3.hist2d(newTracks3[:, 1, 0] * 1e4 - 425, newTracks3[:, 1, 1] * 1e4, bins=50, norm=LogNorm(), label='Count (log)', range=thisrange)
    axis3.set_title('After Residual Cut')
    axis3.set_xlabel(r'$\vec{p}_x$ [µm]')
    axis3.set_yticklabels([])
    axis3.tick_params(direction='in')
    # axis3.yaxis.set_label_position("left")

    fig.tight_layout()
    fig.savefig(outF)
    plt.close(fig)


if __name__ == '__main__':
    inF0 = 'output/alignmentModules/trackDirections/newTracks-BeforeFirstCut.npy'
    inF1 = 'output/alignmentModules/trackDirections/newTracks-AfterFirstCut.npy'

    outD = 'output/alignmentModules/test/trackDirections/'

    plot(inF0, outD + 'noCuts.pdf', 'No Cuts')
    plot(inF1, outD + 'initialDirCut.pdf', 'After Direction Cut')

    for it in [0, 1, 2]:

        inFit1 = f'output/alignmentModules/trackDirections/newTracks-it{it}-step1-noRecoCut.npy'
        inFit2 = f'output/alignmentModules/trackDirections/newTracks-it{it}-step2-afterRecoCut.npy'
        inFit3 = f'output/alignmentModules/trackDirections/newTracks-it{it}-step3-afterFit.npy'
        inFit4 = f'output/alignmentModules/trackDirections/newTracks-it{it}-step4-afterDirectionCut.npy'
        inFit5 = f'output/alignmentModules/trackDirections/newTracks-it{it}-step5-afterTrackFit.npy'

        plot(inFit1, outD + f'it{it}s1.pdf', f'Before Residual Cut')
        plot(inFit2, outD + f'it{it}s2.pdf', f'After Residual Cut')
        plot(inFit3, outD + f'it{it}s3.pdf', f'After Hit Transformation')
        plot(inFit4, outD + f'it{it}s4.pdf', f'After Direction Cut')
        plot(inFit5, outD + f'it{it}s5.pdf', f'After Track Fit')

    # TriplePlot(inF0, inF1, inF3, outD + 'trackDirections.pdf')

    # inTrip1 =
    # inTrip2 =
    # inTrip3 =

    # TriplePlot(inF0, inF1, inF3, outD + 'trackDirections.pdf')