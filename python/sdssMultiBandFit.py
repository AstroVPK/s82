import numpy as np
import math as math
import cmath as cmath
import psutil as psutil
import matplotlib.pyplot as plt
from matplotlib import cm as cm
from matplotlib import gridspec as gridspec
import argparse as argparse
import operator as operator
import warnings as warnings
import copy as copy
import time as time
import pdb
import os as os

import libcarma as libcarma
import util.mcmcviz as mcmcviz
import s82 as s82
from util.mpl_settings import set_plot_params
import util.triangle as triangle

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
parser.add_argument('-pwd', '--pwd', type = str, default = '/home/vpk24/Documents', help = r'Path to working directory')
parser.add_argument('-n', '--name', type = str, default = 'random', help = r'SDSS Filename')
parser.add_argument('-libcarmaChain', '--lC', type = str, default = 'libcarmaChain', help = r'libcarma Chain Filename')
parser.add_argument('-cmcmcChain', '--cC', type = str, default = 'cmcmcChain', help = r'carma_pack Chain Filename')
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
	dataDir = os.environ['S82DATADIR']

bandSeq = 'gri'#'uzgri'
sdssLC = {}
sdssLC['g'] = s82.sdssLC(name = args.name, band = 'g')
sdssLC['i'] = s82.sdssLC(name = sdssLC['g'].name, band = 'i')
sdssLC['r'] = s82.sdssLC(name = sdssLC['g'].name, band = 'r')
#sdssLC['u'] = s82.sdssLC(name = sdssLC['g'].name, band = 'u')
#sdssLC['z'] = s82.sdssLC(name = sdssLC['g'].name, band = 'z')
for band in bandSeq:
	lc = sdssLC[band]
	lc.minTimescale = args.minTimescale
	lc.maxTimescale = args.maxTimescale
	lc.maxSigma = args.maxSigma

if args.savefig or args.show:
	print 'Plotting light curve for %s'%(lc.name)
	figName = os.path.join(dataDir,'%s_AllBands_LC.jpg'%(lc.name))
	if not os.path.isfile(figName):
		for band in bandSeq:
			lc = sdssLC[band]
			lc.plot()
		if args.savefig:
			plt.savefig(figName)
		if args.show:
			plt.show()
		plt.clf()

	print 'Plotting structure function for %s'%(lc.name)
	figName = os.path.join(dataDir,'%s_AllBands_SF.jpg'%(lc.name))
	if not os.path.isfile(figName):
		for band in bandSeq:
			lc = sdssLC[band]
			lc.plotsf()
		if args.savefig:
			plt.savefig(figName)
		if args.show:
			plt.show()
		plt.clf()

taskDict = dict()
DICDict= dict()
totalTime = 0.0

for band in bandSeq:
	lc = sdssLC[band]
	print '\nBand: %s\n'%(band)
	for p in xrange(args.pMin, args.pMax + 1):
		for q in xrange(args.qMin, min(p, args.qMax + 1)):
			nt = libcarma.basicTask(p, q, nwalkers = args.nwalkers, nsteps = args.nsteps)
	
			print 'Starting libcarma fitting for p = %d and q = %d...'%(p, q)
			startLCARMA = time.time()
			nt.fit(sdssLC[band])
			stopLCARMA = time.time()
			timeLCARMA = stopLCARMA - startLCARMA
			print 'libcarma took %4.3f s = %4.3f min = %4.3f hrs'%(timeLCARMA, timeLCARMA/60.0, timeLCARMA/3600.0)
			totalTime += timeLCARMA
	
			Deviances = copy.copy(nt.LnPosterior[:,args.nsteps/2:]).reshape((-1))
			DIC = 0.5*math.pow(np.nanstd(-2.0*Deviances),2.0) + np.nanmean(-2.0*Deviances)
			print 'C-ARMA(%d,%d) DIC: %+4.3e'%(p, q, DIC)
			DICDict['%d %d'%(p, q)] = DIC
			taskDict['%d %d'%(p, q)] = nt
	print 'Total time taken by libcarma is %4.3f s = %4.3f min = %4.3f hrs'%(totalTime, totalTime/60.0, totalTime/3600.0)

	sortedDICVals = sorted(DICDict.items(), key = operator.itemgetter(1))
	pBest = int(sortedDICVals[0][0].split()[0])
	qBest = int(sortedDICVals[0][0].split()[1])
	print 'Best model is C-ARMA(%d,%d)'%(pBest, qBest)

	bestTask = taskDict['%d %d'%(pBest, qBest)]

	if args.viewer:
		notDone = True
		while notDone:
			whatToView = -1
			while whatToView < 0 or whatToView > 3:
				whatToView = int(raw_input('View walkers in C-ARMA coefficients (0) or C-ARMA roots (1) or C-ARMA timescales (2):'))
			pView = -1
			while pView < 1 or pView > args.pMax:
				pView = int(raw_input('C-AR model order:'))
			qView = -1
			while qView < 0 or qView >= pView:
				qView = int(raw_input('C-MA model order:'))

			dim1 = -1
			while dim1 < 0 or dim1 > pView + qView + 1:
				dim1 = int(raw_input('1st Dimension to view:'))
			dim2 = -1
			while dim2 < 0 or dim2 > pView + qView + 1 or dim2 == dim1:
				dim2 = int(raw_input('2nd Dimension to view:'))

			if whatToView == 0:
				if dim1 < pView:
					dim1Name = r'$a_{%d}$'%(dim1)
				if dim1 >= pView and dim1 < pView + qView + 1:
					dim1Name = r'$b_{%d}$'%(dim1 - pView)
				if dim2 < pView:
					dim2Name = r'$a_{%d}$'%(dim2)
				if dim2 >= pView and dim2 < pView + qView + 1:
					dim2Name = r'$b_{%d}$'%(dim2 - pView)
				res = mcmcviz.vizWalkers(taskDict['%d %d'%(pView, qView)].Chain, taskDict['%d %d'%(pView, qView)].LnPosterior, dim1, dim1Name, dim2, dim2Name)

			elif whatToView == 1:
				if dim1 < pView:
					dim1Name = r'$r_{%d}$'%(dim1)
				if dim1 >= pView and dim1 < pView + qView:
					dim1Name = r'$m_{%d}$'%(dim1 - pView)
				if dim1 == pView + qView:
					dim1Name = r'$\mathrm{Amp.}$'
				if dim2 < pView:
					dim2Name = r'$r_{%d}$'%(dim2)
				if dim2 >= pView and dim2 < pView + qView:
					dim2Name = r'$m_{%d}$'%(dim2 - pView)
				if dim2 == pView + qView:
					dim2Name = r'$\mathrm{Amp.}$'
				res = mcmcviz.vizWalkers(taskDict['%d %d'%(pView, qView)].rootChain, taskDict['%d %d'%(pView, qView)].LnPosterior, dim1, dim1Name, dim2, dim2Name)

			else:
				if dim1 < pView + qView:
					dim1Name = r'$\tau_{%d}$'%(dim1)
				if dim1 == pView + qView:
					dim1Name = r'$\mathrm{Amp.}$'
				if dim2 < pView + qView:
					dim2Name = r'$\tau_{%d}$'%(dim2)
				if dim2 == pView + qView:
					dim2Name = r'$\mathrm{Amp.}$'
				res = mcmcviz.vizWalkers(taskDict['%d %d'%(pView, qView)].timescaleChain, taskDict['%d %d'%(pView, qView)].LnPosterior, dim1, dim1Name, dim2, dim2Name)

			var = str(raw_input('Do you wish to view any more MCMC walkers? (y/n):')).lower()
			if var == 'n':
				notDone = False

	loc0 = np.where(bestTask.LnPosterior == np.max(bestTask.LnPosterior))[0][0]
	loc1 = np.where(bestTask.LnPosterior == np.max(bestTask.LnPosterior))[1][0]

	if args.savefig or args.show:
		lblsTau = list()
		for i in xrange(pBest):
			lblsTau.append(r'$\tau_{AR, %d}$ ($d$)'%(i + 1))
		for i in xrange(qBest):
			lblsTau.append(r'$\tau_{MA, %d}$ ($d$)'%(i))
		lblsTau.append(r'Amp. ($Jy$ $d^{%2.1f}$)'%(qBest + 0.5 - pBest))
		try:
			mcmcviz.vizTriangle(pBest, qBest, bestTask.timescaleChain, labelList = lblsTau, figTitle = r'SDSS S82 %s-band LC %s'%(lc.name, lc.band))
		except ValueError as err:
			print str(err)
		else:
			print 'Plotting triangle plot of timescales for the %s-band light curve of %s'%(lc.band, lc.name)
			figName = os.path.join(dataDir,'%s_%s_Tau.jpg'%(lc.name, lc.band))
			if not os.path.isfile(figName):
				if args.savefig:
					plt.savefig(figName)
				if args.show:
					plt.show()
				plt.clf()

		lblsTheta = list()
		for i in xrange(pBest):
			lblsTheta.append(r'$\alpha_{%d}$'%(i + 1))
		for i in xrange(qBest + 1):
			lblsTheta.append(r'$\beta_{%d}$'%(i))
		try:
			mcmcviz.vizTriangle(pBest, qBest, bestTask.Chain, labelList = lblsTheta, figTitle = r'SDSS S82 %s-band LC %s'%(lc.name, lc.band))
		except ValueError as err:
			print str(err)
		else:
			print 'Plotting triangle plot of parameters for the %s-band light curve of %s'%(lc.band, lc.name)
			figName = os.path.join(dataDir,'%s_%s_Theta.jpg'%(lc.name, lc.band))
			if not os.path.isfile(figName):
				if args.savefig:
					plt.savefig(figName)
				if args.show:
					plt.show()
				plt.clf()

	if args.savefig or args.show:
		figName = os.path.join(dataDir,'%s_%s_LC.jpg'%(lc.name, lc.band))
		if not os.path.isfile(figName):
			Theta = bestTask.Chain[:, loc0, loc1]
			nt = libcarma.basicTask(pBest, qBest)
			nt.set(lc.dt, Theta)
			nt.smooth(lc)
			lc.plot()
			if args.savefig:
				plt.savefig(figName)
			if args.show:
				plt.show()
			plt.clf()

		figName = os.path.join(dataDir,'%s_%s_SF.jpg'%(lc.name, lc.band))
		if not os.path.isfile(figName):
			bestTask.plotsf(lc)
			if args.savefig:
				plt.savefig(figName)
			if args.show:
				plt.show()
			plt.clf()

if args.stop:
	pdb.set_trace()
