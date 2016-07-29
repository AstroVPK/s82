import numpy as np
import math as math
import cmath as cmath
import psutil as psutil
import argparse as argparse
import operator as operator
import warnings as warnings
import os as os
import sys as sys
import copy as copy
import time as time
import pdb

try: 
	os.environ['DISPLAY']
except KeyError as Err:
	warnings.warn('No display environment! Using matplotlib backend "Agg"')
	import matplotlib
	matplotlib.use('Agg')
#plt.ion()

import matplotlib.pyplot as plt
from matplotlib import cm as colormap
from matplotlib import gridspec as gridspec

try:
	import libcarma as libcarma
	import util.mcmcviz as mcmcviz
	import s82 as s82
	from util.mpl_settings import set_plot_params
	import util.triangle as triangle
	from util.mpl_settings import set_plot_params
except ImportError:
	print 'libcarma is not setup. Setup libcarma by sourcing bin/setup.sh'
	sys.exit(1)

fhgt = 10
fwid = 16
set_plot_params(useTex = True)

try: 
	os.environ['DISPLAY']
except KeyError as Err:
	warnings.warn('No display environment! Using matplotlib backend "Agg"')
	import matplotlib
	matplotlib.use('Agg')

try:
	import carmcmc as cmcmc
except ImportError:
	carma_pack = False
else:
	carma_pack = True

fhgt = 10
fwid = 16
set_plot_params(useTex = True)

parser = argparse.ArgumentParser()
parser.add_argument('-pwd', '--pwd', type = str, default = os.environ['S82DATADIR'], help = r'Path to working directory')
parser.add_argument('-n', '--name', type = str, default = r'S82wInterceptsSmall.dat', help = r'SDSS Objectlist Filename')
parser.add_argument('-oY', '--outlierDetectionYVal', type = float, default = np.inf, help = r'Maximum deviations away from mean for all y')
parser.add_argument('-oYERR', '--outlierDetectionYERRVal', type = float, default = 5.0, help = r'Maximum deviations away from mean for all yerr')
parser.add_argument('-esc', '--escape', type = str, default = r'#', help = r'Escape character')
parser.add_argument('-b', '--band', type = str, default = r'i', help = r'SDSS filter band to use')
parser.add_argument('-ntries', '--ntries', type = int, default = 5, help = r'Maximum number of times to try fitting a given model')
parser.add_argument('-nthreads', '--nthreads', type = int, default = 25*psutil.cpu_count(logical = True), help = r'Maximum number of threads to use')
parser.add_argument('-nsteps', '--nsteps', type = int, default = 250, help = r'Number of steps per walker')
parser.add_argument('-nwalkers', '--nwalkers', type = int, default = 25*psutil.cpu_count(logical = True), help = r'Number of walkers')
parser.add_argument('-pMax', '--pMax', type = int, default = 1, help = r'Maximum C-AR order')
parser.add_argument('-pMin', '--pMin', type = int, default = 1, help = r'Minimum C-AR order')
parser.add_argument('-qMax', '--qMax', type = int, default = -1, help = r'Maximum C-MA order')
parser.add_argument('-qMin', '--qMin', type = int, default = -1, help = r'Minimum C-MA order')
parser.add_argument('--plot', dest = 'plot', action = 'store_true', help = r'Show plot?')
parser.add_argument('--no-plot', dest = 'plot', action = 'store_false', help = r'Do not show plot?')
parser.set_defaults(plot = False)
parser.add_argument('-minT', '--minTimescale', type = float, default = 2.0, help = r'Minimum allowed timescale = minTimescale*lc.dt')
parser.add_argument('-maxT', '--maxTimescale', type = float, default = 0.5, help = r'Maximum allowed timescale = maxTimescale*lc.T')
parser.add_argument('-maxS', '--maxSigma', type = float, default = 2.0, help = r'Maximum allowed sigma = maxSigma*var(lc)')
parser.add_argument('--stop', dest = 'stop', action = 'store_true', help = r'Stop at end?')
parser.add_argument('--no-stop', dest = 'stop', action = 'store_false', help = r'Do not stop at end?')
parser.set_defaults(stop = False)
parser.add_argument('--save', dest = 'save', action = 'store_true', help = r'Save files?')
parser.add_argument('--no-save', dest = 'save', action = 'store_false', help = r'Do not save files?')
parser.set_defaults(save = False)
parser.add_argument('--log10', dest = 'log10', action = 'store_true', help = r'Compute distances in log space?')
parser.add_argument('--no-log10', dest = 'log10', action = 'store_false', help = r'Do not compute distances in log space?')
parser.set_defaults(log10 = False)
parser.add_argument('--viewer', dest = 'viewer', action = 'store_true', help = r'Visualize MCMC walkers')
parser.add_argument('--no-viewer', dest = 'viewer', action = 'store_false', help = r'Do not visualize MCMC walkers')
parser.set_defaults(viewer = False)
parser.add_argument('--show', dest = 'show', action = 'store_true', help = r'Show figures?')
parser.add_argument('--no-show', dest = 'show', action = 'store_false', help = r'Do not show figures')
parser.set_defaults(show = False)
parser.add_argument('--savefig', dest = 'savefig', action = 'store_true', help = r'Save figures?')
parser.add_argument('--no-savefig', dest = 'savefig', action = 'store_false', help = r'Do not save figures')
parser.set_defaults(savefig = True)
args = parser.parse_args()

if (args.qMax >= args.pMax):
	raise ValueError('pMax must be greater than qMax')
if (args.qMax == -1):
	args.qMax = args.pMax - 1
if (args.qMin == -1):
	args.qMin = 0
if (args.pMin < 1):
	raise ValueError('pMin must be greater than or equal to 1')
if (args.qMin < 0):
	raise ValueError('qMin must be greater than or equal to 0')
if args.savefig:
	dataDir = args.pwd
if args.nsteps%2 == 1:
	args.nsteps += 1

objDict = dict()
with open(os.path.join(args.pwd, args.name), 'rb') as objFile:
	allObjs = objFile.readlines()
for line in allObjs:
	if line[0] == args.escape:
		continue
	line.rstrip('\n')
	words = line.split(' ')
	trialLC = s82.sdssLC(name = words[0], band = args.band, minTimescale = args.minTimescale, maxTimescale = args.maxTimescale, maxSigma = args.maxSigma, outlierDetectionYVal = args.outlierDetectionYVal, outlierDetectionYERRVal = args.outlierDetectionYERRVal)
	if trialLC.mindt == 0.0:
		print 'SDSS %s has atleast two epochs with the same timestamp! Skipping SDSS %s'%(words[0], words[0])
		continue
	objDict[words[0]] = {'lc': trialLC, 'intercept':float(words[1]) }
	taskDict = dict()
	DICDict= dict()
	totalTime = 0.0
	for p in xrange(args.pMin, args.pMax + 1):
		for q in xrange(args.qMin, min(p, args.qMax + 1)):
			nt = libcarma.basicTask(p, q, nthreads = args.nthreads, nwalkers = args.nwalkers, nsteps = args.nsteps)
			DIC = np.nan
			for numTries in xrange(args.ntries):
				print 'Starting trial %d of libcarma fitting for SDSS %s; p = %d and q = %d...'%(numTries, words[0], p, q)
				startLCARMA = time.time()
				nt.fit(objDict[words[0]]['lc'])
				stopLCARMA = time.time()
				timeLCARMA = stopLCARMA - startLCARMA
				print 'libcarma took %4.3f s = %4.3f min = %4.3f hrs'%(timeLCARMA, timeLCARMA/60.0, timeLCARMA/3600.0)
				totalTime += timeLCARMA
				Deviances = copy.copy(nt.LnPosterior[:,args.nsteps/2:]).reshape((-1))
				DIC = 0.5*math.pow(np.nanstd(-2.0*Deviances),2.0) + np.nanmean(-2.0*Deviances)
				print 'C-ARMA(%d,%d) DIC: %+4.3e'%(p, q, DIC)
				if np.isnan(DIC) or (np.isinf(DIC)):
					pass
				else:
					break
			DICDict['%d %d'%(p, q)] = DIC
			taskDict['%d %d'%(p, q)] = nt
	print 'Total time taken by libcarma for SDSS %s is %4.3f s = %4.3f min = %4.3f hrs'%(words[0], totalTime, totalTime/60.0, totalTime/3600.0)
	sortedDICVals = sorted(DICDict.items(), key = operator.itemgetter(1))
	pBest = int(sortedDICVals[0][0].split()[0])
	qBest = int(sortedDICVals[0][0].split()[1])
	print 'Best model is C-ARMA(%d,%d)'%(pBest, qBest)
	objDict[words[0]]['task'] = taskDict['%d %d'%(pBest, qBest)]
	objDict[words[0]]['DIC'] = DICDict['%d %d'%(pBest, qBest)]
	objDict[words[0]]['dt'] = objDict[words[0]]['lc'].dt
	objDict[words[0]]['bestTheta'] = objDict[words[0]]['task'].Chain[:,np.where(objDict[words[0]]['task'].LnPosterior == np.max(objDict[words[0]]['task'].LnPosterior))[0][0],np.where(objDict[words[0]]['task'].LnPosterior == np.max(objDict[words[0]]['task'].LnPosterior))[1][0]]
	objDict[words[0]]['task'].set(objDict[words[0]]['dt'], objDict[words[0]]['bestTheta'])
	objDict[words[0]]['task'].smooth(objDict[words[0]]['lc'])
	fracVar = (np.real(objDict[words[0]]['task'].rootChain[pBest+qBest,:,args.nsteps/2:])/objDict[words[0]]['lc'].mean).flatten(order = 'A')
	longestT = (np.max(-1.0/np.real(objDict[words[0]]['task'].rootChain[:pBest+qBest+1,:,args.nsteps/2:]), axis = 0)).flatten(order = 'A')
	objDict[words[0]]['fracVar'] = fracVar
	objDict[words[0]]['longestT'] = longestT
	del DICDict
	del taskDict
	lcFig = objDict[words[0]]['lc'].plot()
	lcFig.savefig(os.path.join(args.pwd, words[0] + '_LC.jpg'), dpi = 300)
	sfFig = objDict[words[0]]['task'].plotsf(LC = objDict[words[0]]['lc'], newdt = objDict[words[0]]['lc'].mindt/2.0)
	plt.savefig(os.path.join(args.pwd, words[0] + '_SF.jpg'), dpi = 300)

if len(objDict) > 0:
	gs1 = gridspec.GridSpec(1000,1000)
	fig1 = plt.figure(0,figsize=(fwid,fwid))
	ax1 = fig1.add_subplot(gs1[:,:])
	numKeys = len(objDict.keys())
	keyList = objDict.keys()
	numEntries = args.nwalkers*(args.nsteps/2)
	flatFracVar = np.zeros(numKeys*numEntries)
	flatLongestT = np.zeros(numKeys*numEntries)
	flatIntercept = np.zeros(numKeys*numEntries)
	for i in xrange(numKeys):
		for entry in xrange(numEntries):
			flatFracVar[entry + i*numEntries] = objDict[keyList[i]]['fracVar'][entry]
			flatLongestT[entry + i*numEntries] = math.log10(objDict[keyList[i]]['longestT'][entry])
			flatIntercept[entry + i*numEntries] = objDict[keyList[i]]['intercept']
	scatPlot = ax1.scatter(flatFracVar, flatLongestT, c = flatIntercept, marker = '.', edgecolor = 'none', cmap = colormap.PiYG)
	cBar = plt.colorbar(scatPlot, ax = ax1, orientation='vertical')
	ax1.set_xlabel(r'Fractional Variability $A/F$ ')
	ax1.set_ylabel(r'$\log_{10}$ Longest Timescale $\log_{10} \tau_{\mathrm{Longest}}$ ($\log_{10}$ d)')
	cBar.set_label(r'Intercept')
	if args.savefig:
		fig1.savefig(os.path.join(args.pwd, 'InterceptAnalysis.jpg'), dpi = 300)

if args.stop:
	pdb.set_trace()
