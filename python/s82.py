import math as math
import numpy as np
import astropy.io.fits as astfits
import os as os
import zmq
import pdb

import libcarma as libcarma

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

	@staticmethod
	def query():
		pass

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
		pdb.set_trace()
		'''if path is None:
			path = os.environ['PWD']
		filePath = os.path.join(path, name)
		with open(filePath) as sdssFile:
			allLines = sdssFile.readlines()
		self._numCadences = len(allLines) - 1
		self.objId = np.require(np.zeros(self.numCadences, dtype = long), requirements=['F', 'A', 'W', 'O', 'E'])
		self.t = np.require(np.zeros(self.numCadences), requirements=['F', 'A', 'W', 'O', 'E'])
		self.x = np.require(np.zeros(self.numCadences), requirements=['F', 'A', 'W', 'O', 'E'])
		self.y = np.require(np.zeros(self.numCadences), requirements=['F', 'A', 'W', 'O', 'E'])
		self.yerr = np.require(np.zeros(self.numCadences), requirements=['F', 'A', 'W', 'O', 'E'])
		self.mask = np.require(np.zeros(self.numCadences), requirements=['F', 'A', 'W', 'O', 'E'])
		words = allLines[1].split(',')
		self._name = words[1] ## The name of the light curve (usually the object's name).
		self.startT = float(words[12])
		self._band = str('sdss_g') ## The name of the photometric band (eg. HSC-I or SDSS-g etc..).
		self._xunit = r'$d$ (MJD)' ## Unit in which time is measured (eg. s, sec, seconds etc...).
		self._yunit = r'$F$ (Jy)' ## Unit in which the flux is measured (eg Wm^{-2} etc...).
		for lineNum, line in enumerate(allLines[1:]):
			words = line.split(',')
			self.objId[lineNum] = long(words[2])
			self.t[lineNum] = float(words[12]) - self.startT
			self.y[lineNum] = float(words[27])
			self.yerr[lineNum] = float(words[28])
			self.mask[lineNum] = 1.0'''
		self._mean = np.mean(self.y)
		self._std = np.std(self.y)
		self._meanerr = np.mean(self.yerr)
		self._stderr = np.std(self.yerr)
		self._T = float(self.t[-1] - self.t[0])
		self._dt = float(np.nanmin(self.t[1:] - self.t[:-1]))

	def write(self):
		pass