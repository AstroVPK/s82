import math as math
import cmath as cmath
import re
import numpy as np
import astropy.io.fits as astfits
import os as os
import zmq
import pdb
from pylab import *
import time
import copy
import operator
import argparse
import psutil
import warnings
import sys

try:
	import libcarma as libcarma
	from util.mpl_settings import set_plot_params
	import util.mcmcviz as mcmcviz
	import util.triangle as triangle
except ImportError:
	print 'libcarma not found! Try setting up libcarma if you have it installed. Unable to proceed!!'
	sys.exit(0)

try:
	from JacksTools import jools
except ImportError:
	print 'JacksTools not found! Try pip installing JacksTools. Unable to proceed!!'
	sys.exit(0)

try:
	import carmcmc as cmcmc
except ImportError:
	carma_pack = False
	warnings.warn('carma_pack not found. Not using carma_pack!!')
else:
	carma_pack = True

try: 
	os.environ['DISPLAY']
except KeyError as Err:
	warnings.warn('No display environment! Using matplotlib backend "Agg"')
	import matplotlib
	matplotlib.use('Agg')

fhgt = 10
fwid = 16
set_plot_params(useTex = True)

class sdssLC(libcarma.basicLC):

	def _getRandLC(self):
		context = zmq.Context()
		socket = context.socket(zmq.REQ)
		socket.connect('tcp://76.124.106.126:5001')
		socket.send(b"randLC\n0")
		fname, z, data = socket.recv_pyobj()
		socket.close()
		return fname, z, data

	def _getLC(self, ID):
		context = zmq.Context()
		socket = context.socket(zmq.REQ)
		socket.connect('tcp://76.124.106.126:5001')
	
		socket.send(b"getLC\n%s" % ID)
		fname, z, data = socket.recv_pyobj()
		socket.close()
		return fname, z, data

	def fit(self, pMin = 1, pMax = 1, qMin = -1, qMax = -1, nwalkers = 200, nsteps = 1000, xTol = 0.001, maxEvals = 10000):
		self.taskDict = dict()
		self.DICDict = dict()
		self.totalTime = 0.0
		if (qMax >= pMax):
			raise ValueError('pMax must be greater than qMax')
		if (qMax == -1):
			qMax = pMax - 1
		if (qMin == -1):
			qMin = 0
		if (pMin < 1):
			raise ValueError('pMin must be greater than or equal to 1')
		if (qMin < 0):
			raise ValueError('qMin must be greater than or equal to 0')
		self.pMax = pMax
		self.pMin = pMin
		self.qMax = qMax
		self.qMin = qMin

		for p in xrange(pMin, pMax + 1):
			for q in xrange(qMin, min(p, qMax + 1)):
				nt = libcarma.basicTask(p, q, nwalkers = nwalkers, nsteps = nsteps, xTol = xTol, maxEvals = maxEvals)

				print 'Starting libcarma fitting for p = %d and q = %d...'%(p, q)
				startLCARMA = time.time()
				nt.fit(self)
				stopLCARMA = time.time()
				timeLCARMA = stopLCARMA - startLCARMA
				print 'libcarma took %4.3f s = %4.3f min = %4.3f hrs'%(timeLCARMA, timeLCARMA/60.0, timeLCARMA/3600.0)
				self.totalTime += timeLCARMA

				Deviances = copy.copy(nt.LnPosterior[:,nsteps/2:]).reshape((-1))
				DIC = 0.5*math.pow(np.nanstd(-2.0*Deviances),2.0) + np.nanmean(-2.0*Deviances)
				print 'C-ARMA(%d,%d) DIC: %+4.3e'%(p, q, DIC)
				self.DICDict['%d %d'%(p, q)] = DIC
				self.taskDict['%d %d'%(p, q)] = nt
		print 'Total time taken by libcarma is %4.3f s = %4.3f min = %4.3f hrs'%(self.totalTime, self.totalTime/60.0, self.totalTime/3600.0)

		sortedDICVals = sorted(self.DICDict.items(), key = operator.itemgetter(1))
		self.pBest = int(sortedDICVals[0][0].split()[0])
		self.qBest = int(sortedDICVals[0][0].split()[1])
		print 'Best model is C-ARMA(%d,%d)'%(self.pBest, self.qBest)

		self.bestTask = self.taskDict['%d %d'%(self.pBest, self.qBest)]
		self.bestFigTitle = 'Best Model: CARMA(%d,%d); DIC: %+4.3e'%(self.pBest, self.qBest,self.DICDict['%d %d'%(self.pBest, self.qBest)])
		self.bestLabelList = list()
		for i in range(self.pBest):
			self.bestLabelList.append("$a_{%d}$"%(i + 1))
		for i in range(self.qBest + 1):
			self.bestLabelList.append("$b_{%d}$"%(i))
		mcmcviz.vizTriangle(self.pBest, self.qBest, self.bestTask.Chain, labelList = self.bestLabelList, figTitle = self.bestFigTitle)

	def view(self):
		notDone = True
		while notDone:
			whatToView = -1
			while whatToView < 0 or whatToView > 3:
				try:
					whatToView = int(raw_input('View walkers in C-ARMA coefficients (0) or C-ARMA roots (1) or C-ARMA timescales (2):'))
				except ValueError:
					print 'Bad input: integer required!'
			pView = -1
			while pView < 1 or pView > self.pMax:
				try:
					pView = int(raw_input('C-AR model order:'))
				except ValueError:
					print 'Bad input: integer required!'
			qView = -1
			while qView < 0 or qView >= pView:
				try:
					qView = int(raw_input('C-MA model order:'))
				except ValueError:
					print 'Bad input: integer required!'

			if whatToView == 0:
				figTitle = 'CARMA(%d,%d); DIC: %+4.3e'%(pView, qView,self.DICDict['%d %d'%(pView, qView)])
				labelList = list()
				dimCtr = 0
				for i in range(pView):
					labelList.append(r'$a_{%d}$: $\mathrm{dim}%d$'%(i + 1, dimCtr))
					dimCtr += 1
				for i in range(qView + 1):
					labelList.append(r'$b_{%d}$: $\mathrm{dim}%d$'%(i, dimCtr))
					dimCtr += 1
				mcmcviz.vizTriangle(pView, qView, self.taskDict['%d %d'%(pView, qView)].Chain, labelList = labelList, figTitle = figTitle)
				dim1 = -1
				while dim1 < 0 or dim1 > pView + qView + 1:
					try:
						dim1 = int(raw_input('1st Dimension to view:'))
					except ValueError:
						print 'Bad input: integer required!'
				dim2 = -1
				while dim2 < 0 or dim2 > pView + qView + 1 or dim2 == dim1:
					try:
						dim2 = int(raw_input('2nd Dimension to view:'))
					except ValueError:
						print 'Bad input: integer required!'
				if dim1 < pView:
					dim1Name = r'$a_{%d}$'%(dim1)
				if dim1 >= pView and dim1 < pView + qView + 1:
					dim1Name = r'$b_{%d}$'%(dim1 - pView)
				if dim2 < pView:
					dim2Name = r'$a_{%d}$'%(dim2)
				if dim2 >= pView and dim2 < pView + qView + 1:
					dim2Name = r'$b_{%d}$'%(dim2 - pView)
				res = mcmcviz.vizWalkers(self.taskDict['%d %d'%(pView, qView)].Chain, self.taskDict['%d %d'%(pView, qView)].LnPosterior, dim1, dim1Name, dim2, dim2Name)

			elif whatToView == 1:
				figTitle = 'CARMA(%d,%d); DIC: %+4.3e'%(pView, qView,self.DICDict['%d %d'%(pView, qView)])
				labelList = list()
				dimCtr = 0
				for i in range(pView):
					labelList.append(r'$r_{%d}$: $\mathrm{dim}%d$'%(i, dimCtr))
					dimCtr += 1
				for i in range(qView):
					labelList.append(r'$m_{%d}$: $\mathrm{dim}%d$'%(i, dimCtr))
					dimCtr += 1
				labelList.append(r'$\mathrm{Amp.}$: $\mathrm{dim}%d$'%(dimCtr))
				dimCtr += 1
				mcmcviz.vizTriangle(pView, qView, self.taskDict['%d %d'%(pView, qView)].rootChain, labelList = labelList, figTitle = figTitle)
				dim1 = -1
				while dim1 < 0 or dim1 > pView + qView + 1:
					try:
						dim1 = int(raw_input('1st Dimension to view:'))
					except ValueError:
						print 'Bad input: integer required!'
				dim2 = -1
				while dim2 < 0 or dim2 > pView + qView + 1 or dim2 == dim1:
					try:
						dim2 = int(raw_input('2nd Dimension to view:'))
					except ValueError:
						print 'Bad input: integer required!'
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
				res = mcmcviz.vizWalkers(self.taskDict['%d %d'%(pView, qView)].rootChain, self.taskDict['%d %d'%(pView, qView)].LnPosterior, dim1, dim1Name, dim2, dim2Name)

			else:
				figTitle = 'CARMA(%d,%d); DIC: %+4.3e'%(pView, qView,self.DICDict['%d %d'%(pView, qView)])
				labelList = list()
				dimCtr = 0
				for i in range(pView + qView):
					labelList.append(r'$\tau_{%d}$: $\mathrm{dim}%d$'%(i, dimCtr))
					dimCtr += 1
				labelList.append(r'$\mathrm{Amp.}$: $\mathrm{dim}%d$'%(dimCtr))
				dimCtr += 1
				mcmcviz.vizTriangle(pView, qView, self.taskDict['%d %d'%(pView, qView)].timescaleChain, labelList = labelList, figTitle = figTitle)
				dim1 = -1
				while dim1 < 0 or dim1 > pView + qView + 1:
					try:
						dim1 = int(raw_input('1st Dimension to view:'))
					except ValueError:
						print 'Bad input: integer required!'
				dim2 = -1
				while dim2 < 0 or dim2 > pView + qView + 1 or dim2 == dim1:
					try:
						dim2 = int(raw_input('2nd Dimension to view:'))
					except ValueError:
						print 'Bad input: integer required!'
				if dim1 < pView + qView:
					dim1Name = r'$\tau_{%d}$'%(dim1)
				if dim1 == pView + qView:
					dim1Name = r'$\mathrm{Amp.}$'
				if dim2 < pView + qView:
					dim2Name = r'$\tau_{%d}$'%(dim2)
				if dim2 == pView + qView:
					dim2Name = r'$\mathrm{Amp.}$'
				res = mcmcviz.vizWalkers(self.taskDict['%d %d'%(pView, qView)].timescaleChain, self.taskDict['%d %d'%(pView, qView)].LnPosterior, dim1, dim1Name, dim2, dim2Name)

			var = str(raw_input('Do you wish to view any more MCMC walkers? (y/n):')).lower()
			if var == 'n':
				notDone = False

	@classmethod
	def newRandLC(self, band):
		return sdssLC(name = '', band = band)

	def plot(self, doShow = False):
		plt.figure(-1, figsize = (fwid, fhgt))
		if np.sum(self.x) != 0.0:
			plt.plot(self.t, self.x - np.mean(self.x) + np.mean(self.y[np.where(self.mask == 1.0)[0]]), color = '#000000', zorder = 0)
			plt.plot(self.t, self.x - np.mean(self.x) + np.mean(self.y[np.where(self.mask == 1.0)[0]]), color = '#000000', marker = 'o', markeredgecolor = 'none', zorder = 0)
		if np.sum(self.y) != 0.0:
			plt.errorbar(self.t[np.where(self.mask == 1.0)[0]], self.y[np.where(self.mask == 1.0)[0]], self.yerr[np.where(self.mask == 1.0)[0]], label = r'%s (SDSS %s-band)'%(self.name, self.band), fmt = 'o', capsize = 0, color = self.colorDict[self.band], markeredgecolor = 'none', zorder = 10)
		if self.isSmoothed:
			plt.plot(self.tSmooth, self.xSmooth - np.mean(self.xSmooth) + np.mean(self.y[np.where(self.mask == 1.0)[0]]), color = self.smoothColorDict[self.band], marker = 'o', markeredgecolor = 'none', zorder = -5)
			plt.plot(self.tSmooth, self.xSmooth - np.mean(self.xSmooth) + np.mean(self.y[np.where(self.mask == 1.0)[0]]), color = self.smoothColorDict[self.band], zorder = -5)
			plt.fill_between(self.tSmooth, self.xSmooth - np.mean(self.xSmooth) + np.mean(self.y[np.where(self.mask == 1.0)[0]]) - self.xerrSmooth, self.xSmooth - np.mean(self.xSmooth) + np.mean(self.y[np.where(self.mask == 1.0)[0]]) + self.xerrSmooth, facecolor = self.smoothErrColorDict[self.band], zorder = -10)
		plt.xlabel(self.xunit)
		plt.ylabel(self.yunit)
		plt.title(r'Light curve')
		plt.legend()
		if doShow:
			plt.show(False)

	def plotacvf(self, doShow = False):
		plt.figure(-2, figsize = (fwid, fhgt))
		plt.plot(0.0, 0.0)
		if np.sum(self.y) != 0.0:
			lagsE, acvfE, acvferrE = self.acvf()
			if np.sum(acvfE) != 0.0:
				plt.errorbar(lagsE[1:], acvfE[1:], acvferrE[1:], label = r'%s (SDSS %s-band) obs. Autocovariance Function'%(self.name, self.band), fmt = 'o', capsize = 0, color = self.colorDict[self.band], markeredgecolor = 'none', zorder = 10)
		plt.xlabel(r'$\delta t$')
		plt.ylabel(r'$ACVF$')
		plt.title(r'AutoCovariance Function')
		plt.legend(loc = 3)
		if doShow:
			plt.show(False)

	def plotacf(self, doShow = False):
		plt.figure(-3, figsize = (fwid, fhgt))
		plt.plot(0.0, 0.0)
		if np.sum(self.y) != 0.0:
			lagsE, acfE, acferrE = self.acf()
			if np.sum(acfE) != 0.0:
				plt.errorbar(lagsE[1:], acfE[1:], acferrE[1:], label = r'%s (SDSS %s-band) obs. Autocorrelation Function'%(self.name, self.band), fmt = 'o', capsize = 0, color = self.colorDict[self.band], markeredgecolor = 'none', zorder = 10)
		plt.xlabel(r'$\delta t$')
		plt.ylabel(r'$ACF$')
		plt.title(r'AutoCorrelation Function')
		plt.legend(loc = 3)
		plt.ylim(-1.0, 1.0)
		if doShow:
			plt.show(False)

	def plotsf(self, doShow = False):
		plt.figure(-4, figsize = (fwid, fhgt))
		plt.loglog(1.0, 1.0)
		if np.sum(self.y) != 0.0:
			lagsE, sfE, sferrE = self.sf()
			if np.sum(sfE) != 0.0:
				plt.errorbar(lagsE[1:], sfE[1:], sferrE[1:], label = r'%s (SDSS %s-band) obs. Structure Function'%(self.name, self.band), fmt = 'o', capsize = 0, color = self.colorDict[self.band], markeredgecolor = 'none', zorder = 10)
		plt.xlabel(r'$\delta t$')
		plt.ylabel(r'$\log SF$')
		plt.title(r'Structure Function')
		plt.legend(loc = 2)
		if doShow:
			plt.show(False)

	def read(self, name, band, pwd = None, **kwargs):
		self._computedCadenceNum = -1
		self._tolIR = 1.0e-3
		self._fracIntrinsicVar = 0.0
		self._fracNoiseToSignal = 0.0
		self._maxSigma = 2.0
		self._minTimescale = 2.0
		self._maxTimescale = 0.5
		self._pSim = 0
		self._qSim = 0
		self._pComp = 0
		self._qComp = 0
		self.XSim = np.require(np.zeros(self._pSim), requirements=['F', 'A', 'W', 'O', 'E']) ## State of light curve at last timestamp
		self.PSim = np.require(np.zeros(self._pSim*self._pSim), requirements=['F', 'A', 'W', 'O', 'E']) ## Uncertainty in state of light curve at last timestamp.
		self.XComp = np.require(np.zeros(self._pComp), requirements=['F', 'A', 'W', 'O', 'E']) ## State of light curve at last timestamp
		self.PComp = np.require(np.zeros(self._pComp*self._pComp), requirements=['F', 'A', 'W', 'O', 'E']) ## Uncertainty in state of light curve at last timestamp.
		if name.lower() in ['random', 'rand', 'r', 'rnd', 'any', 'none', '']:
			self._name, self.z, data = self._getRandLC()
		else:
			self._name, self.z, data = self._getLC(name)
		t = data['mjd_%s' % band]
		y = data['calMag_%s' % band]
		yerr = data['calMagErr_%s' % band]
		y, yerr = jools.luptitude_to_flux(y, yerr, band)
		t = jools.time_to_restFrame(t, float(self.z))
		self._numCadences = len(t)
		self.t = np.require(np.zeros(self.numCadences), requirements=['F', 'A', 'W', 'O', 'E'])
		self.x = np.require(np.zeros(self.numCadences), requirements=['F', 'A', 'W', 'O', 'E'])
		self.y = np.require(np.zeros(self.numCadences), requirements=['F', 'A', 'W', 'O', 'E'])
		self.yerr = np.require(np.zeros(self.numCadences), requirements=['F', 'A', 'W', 'O', 'E'])
		self.mask = np.require(np.zeros(self.numCadences), requirements=['F', 'A', 'W', 'O', 'E'])
		self._name = self.name.split('/')[-1].split('_')[1]
		self._band = band
		self.objID = data['objID']
		self.t[:] = t - t[0]
		self.y[:] = y
		self.yerr[:] = yerr
		self.mask[:] += 1
		self.startT = t[0]
		self._band = band
		self._xunit = r'$d$ (MJD)' ## Unit in which time is measured (eg. s, sec, seconds etc...).
		self._yunit = r'$F$ (Jy)' ## Unit in which the flux is measured (eg Wm^{-2} etc...).
		self._mean = np.mean(self.y)
		self._std = np.std(self.y)
		self._meanerr = np.mean(self.yerr)
		self._stderr = np.std(self.yerr)
		self._T = float(self.t[-1] - self.t[0])
		self._dt = float(np.nanmin(self.t[1:] - self.t[:-1]))
		self._isSmoothed = False
		self._dtSmooth = 0.0
		self._isRegular = False
		self.colorDict = {'u': '#756bb1', 'g': '#3182bd', 'r': '#31a354', 'i': '#de2d26', 'z': '#636363'}
		self.smoothColorDict = {'u': '#bcbddc', 'g': '#9ecae1', 'r': '#a1d99b', 'i': '#fc9272', 'z': '#bdbdbd'}
		self.smoothErrColorDict = {'u': '#efedf5', 'g': '#deebf7', 'r': '#e5f5e0', 'i': '#fee0d2', 'z': '#f0f0f0'}

	def write(self):
		pass


def test(band = 'r', nsteps = 1000, nwalkers = 200, pMax = 1, pMin = 1, qMax = -1, qMin = -1, minT = 2.0, maxT = 0.5, maxS = 2.0, xTol = 0.001, maxE = 10000, plot = True, stop = False, fit = True, viewer = True):

	argDict = {'band': band, 'nsteps': nsteps, 'nwalkers': nwalkers, 'pMax': pMax, 'pMin': pMin, 'qMax': qMax, 'qMin': qMin, 'minT': minT, 'maxT': maxT, 'maxS': maxS, 'xTol': xTol, 'maxE': maxE, 'plot': plot, 'stop': stop, 'fit': fit, 'viewer': viewer}

	Another = 'y'
	Same = 'y'
	while Another == 'y' or Same == 'y':
		if Another == 'y':
			newLC = sdssLC(band = argDict['band'], name = '')
		newLC.minTimescale = argDict['minT']
		newLC.maxTimescale = argDict['maxT']
		newLC.maxSigma = argDict['maxS']
		if argDict['plot']:
			newLC.plot()
		if argDict['fit']:
			newLC.fit(pMin = argDict['pMin'], pMax = argDict['pMax'], qMin = argDict['qMin'], qMax = argDict['qMax'], nwalkers = argDict['nwalkers'], nsteps = argDict['nsteps'], xTol = argDict['xTol'], maxEvals = argDict['maxE'])
			if argDict['viewer']:
				newLC.view()
		if argDict['stop']:
			pdb.set_trace()
		Same = str(raw_input('Redo same LC (possibly with different fitting parameters)? (y/n):')).lower()
		if Same == 'n':
			Another = str(raw_input('Do another LC? (y/n):')).lower()
		if Same == 'y' or Another == 'y':
			Change = str(raw_input('Change any fitting parameters? (y/n):')).lower()
			if Change == 'y':
				changeAnother = 'y'
				while changeAnother == 'y':
					whichParam = str(raw_input('Which parameter do you wish to change? (band/nsteps/nwalkers/pMin,pMax/qMin/qMax/minT/maxT/maxS/xTol/maxE/plot/stop/fit/viewer):'))
					whatValue = str(raw_input('What would you like to set the value to?:'))
					if whichParam in ['band']:
						argDict[whichParam] = whatValue
					elif whichParam in ['nsteps', 'nwalkers', 'pMax', 'pMin', 'qMax', 'qMin', 'maxE']:
						argDict[whichParam] = int(whatValue)
					elif whichParam in ['minT', 'maxT', 'maxS', 'xTol']:
						argDict[whichParam] = float(whatValue)
					elif whichParam in ['plot', 'stop', 'fit', 'viewer']:
						argDict[whichParam] = bool(whatValue)
					else:
						print 'Unrecognized fit parameter!'
					changeAnother = str(raw_input('Would you like to change any other parameters? (y/n):'))

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-b', '--band', type = str, default = 'r', help = r'SDSS band')
	parser.add_argument('-nsteps', '--nsteps', type = int, default = 1000, help = r'Number of steps per walker')
	parser.add_argument('-nwalkers', '--nwalkers', type = int, default = 25*psutil.cpu_count(logical = True), help = r'Number of walkers')
	parser.add_argument('-pMax', '--pMax', type = int, default = 1, help = r'Maximum C-AR order')
	parser.add_argument('-pMin', '--pMin', type = int, default = 1, help = r'Minimum C-AR order')
	parser.add_argument('-qMax', '--qMax', type = int, default = -1, help = r'Maximum C-MA order')
	parser.add_argument('-qMin', '--qMin', type = int, default = -1, help = r'Minimum C-MA order')
	parser.add_argument('--plot', dest = 'plot', action = 'store_true', help = r'Show plot?')
	parser.add_argument('--no-plot', dest = 'plot', action = 'store_false', help = r'Do not show plot?')
	parser.set_defaults(plot = True)
	parser.add_argument('-minT', '--minTimescale', type = float, default = 2.0, help = r'Minimum allowed timescale = minTimescale*lc.dt')
	parser.add_argument('-maxT', '--maxTimescale', type = float, default = 0.5, help = r'Maximum allowed timescale = maxTimescale*lc.T')
	parser.add_argument('-maxS', '--maxSigma', type = float, default = 2.0, help = r'Maximum allowed sigma = maxSigma*var(lc)')
	parser.add_argument('-xTol', '--xTol', type = float, default = 0.001, help = r'Relative tolerance on parameters during optimization phase')
	parser.add_argument('-maxE', '--maxEvals', type = int, default = 10000, help = r'Maximum number of evaluations per walker during optimization phase')
	parser.add_argument('--stop', dest = 'stop', action = 'store_true', help = r'Stop at end?')
	parser.add_argument('--no-stop', dest = 'stop', action = 'store_false', help = r'Do not stop at end?')
	parser.set_defaults(stop = False)
	parser.add_argument('--save', dest = 'save', action = 'store_true', help = r'Save files?')
	parser.add_argument('--no-save', dest = 'save', action = 'store_false', help = r'Do not save files?')
	parser.set_defaults(save = False)
	parser.add_argument('--fit', dest = 'fit', action = 'store_true', help = r'Fit CARMA model')
	parser.add_argument('--no-fit', dest = 'fit', action = 'store_false', help = r'Do not fit CARMA model')
	parser.set_defaults(fit = True)
	parser.add_argument('--viewer', dest = 'viewer', action = 'store_true', help = r'Visualize MCMC walkers')
	parser.add_argument('--no-viewer', dest = 'viewer', action = 'store_false', help = r'Do not visualize MCMC walkers')
	parser.set_defaults(viewer = True)
	args = parser.parse_args()
	test(band = args.band, nsteps = args.nsteps, nwalkers = args.nwalkers, pMax = args.pMax, pMin = args.pMin, qMax = args.qMax, qMin = args.qMin, minT = args.minTimescale, maxT = args.maxTimescale, maxS = args.maxSigma, xTol = args.xTol, maxE = args.maxEvals, plot = args.plot, stop = args.stop, fit = args.fit, viewer = args.viewer)

