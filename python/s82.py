import math as math, re
import numpy as np
import astropy.io.fits as astfits
import os as os
import zmq
import pdb
from JacksTools import jools
from pylab import *
import time
import copy
import operator
import math

import libcarma as libcarma
import util.mcmcviz as mcmcviz

class Args(object):

	pass

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

	def fit(self):

		self.taskDict = dict()
		self.DICDict = dict()
		totalTime = 0.0
		args = Args()
		args.viewer = True
		args.pMin = 1
		args.pMax = 2
		args.qMin = 0 
		args.qMax = 1
		args.nsteps = 1000
		args.nwalkers = 200

		for p in xrange(args.pMin, args.pMax + 1):
			for q in xrange(args.qMin, min(p, args.qMax + 1)):
				nt = libcarma.basicTask(p, q, nwalkers = args.nwalkers, nsteps = args.nsteps, xTol = 0.001, maxEvals = 10000)

				print 'Starting libcarma fitting for p = %d and q = %d...'%(p, q)
				startLCARMA = time.time()
				nt.fit(self)
				stopLCARMA = time.time()
				timeLCARMA = stopLCARMA - startLCARMA
				print 'libcarma took %4.3f s = %4.3f min = %4.3f hrs'%(timeLCARMA, timeLCARMA/60.0, timeLCARMA/3600.0)
				totalTime += timeLCARMA

				Deviances = copy.copy(nt.LnPosterior[:,args.nsteps/2:]).reshape((-1))
				DIC = 0.5*math.pow(np.nanstd(-2.0*Deviances),2.0) + np.nanmean(-2.0*Deviances)
				print 'C-ARMA(%d,%d) DIC: %+4.3e'%(p, q, DIC)
				self.DICDict['%d %d'%(p, q)] = DIC
				self.taskDict['%d %d'%(p, q)] = nt
		print 'Total time taken by libcarma is %4.3f s = %4.3f min = %4.3f hrs'%(totalTime, totalTime/60.0, totalTime/3600.0)

		sortedDICVals = sorted(self.DICDict.items(), key = operator.itemgetter(1))
		self.pBest = int(sortedDICVals[0][0].split()[0])
		self.qBest = int(sortedDICVals[0][0].split()[1])
		print 'Best model is C-ARMA(%d,%d)'%(self.pBest, self.qBest)

		self.bestTask = self.taskDict['%d %d'%(self.pBest, self.qBest)]

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
					res = mcmcviz.vizWalkers(self.taskDict['%d %d'%(pView, qView)].Chain, self.taskDict['%d %d'%(pView, qView)].LnPosterior, dim1, dim1Name, dim2, dim2Name)

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
					res = mcmcviz.vizWalkers(self.taskDict['%d %d'%(pView, qView)].rootChain, self.taskDict['%d %d'%(pView, qView)].LnPosterior, dim1, dim1Name, dim2, dim2Name)

				else:
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


	@staticmethod
	def query():
		pass

	@classmethod
	def newRandLC(self, band):

		return sdssLC(name = '', band = band)

	def plot(self):

		plt.errorbar(self.t, self.y, self.yerr, ls = ' ', marker = '.', markeredgecolor = 'none')
		plt.show()
	

	def read(self, name, band, pwd = None, **kwargs):
		self._computedCadenceNum = -1
		self._tolIR = 1.0e-3
		self._fracIntrinsicVar = 0.0
		self._fracNoiseToSignal = 0.0
		self._maxSigma = 2.0
		self._minTimescale = 2.0
		self._maxTimescale = 0.5
		self._p = 0
		self._q = 0
		self.XSim = np.require(np.zeros(self._p), requirements=['F', 'A', 'W', 'O', 'E']) ## State of light curve at last timestamp
		self.PSim = np.require(np.zeros(self._p*self._p), requirements=['F', 'A', 'W', 'O', 'E']) ## Uncertainty in state of light curve at last timestamp.
		self.XComp = np.require(np.zeros(self._p), requirements=['F', 'A', 'W', 'O', 'E']) ## State of light curve at last timestamp
		self.PComp = np.require(np.zeros(self._p*self._p), requirements=['F', 'A', 'W', 'O', 'E']) ## Uncertainty in state of light curve at last timestamp.
		#pdb.set_trace()
		self._name, self.z, data = self._getRandLC()
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
		self._name = re.findall('LC_(\w+)_*',self._name)[0]
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

	def write(self):
		pass


def test():


	newLC = sdssLC(band = 'g', name = '')
	newLC.plot()
	newLC.fit()
	pdb.set_trace()


if __name__ == '__main__':
		test()

