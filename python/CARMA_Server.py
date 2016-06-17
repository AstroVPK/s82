import zmq, sys, os, time, cPickle, StringIO, numpy as np, re, random
import carmcmc as cm
import multiprocessing as mp
from JacksTools import jio


class Server:

	def __init__(self):

		self.context = zmq.Context()

		self.socket = self.context.socket(zmq.REP)
		self.socket.bind('tcp://*:5001')

		self.commands = {'getLC':self.getLC, 'randLC':self.randLC}
	
		print "Server Started"

	def getLC(self, *args):

		ID = args[0]
		fname = os.path.join(FileManager.LCDir, FileManager.getFileName(ID))
		data = jio.load(fname, delimiter = ',', headed = True)
		z = FileManager.getRedshift(ID)
		package = (fname, z, data)	
		self.socket.send_pyobj(package)
		print "Sent %s" % FileManager.getFileName(ID)

	def getIDList(self, *args):

		pass	

	def randLC(self, *args):

		ID = random.choice(FileManager.IDList(FileManager.getLCList()))
		self.getLC(ID)

	def start(self):

		while True:
			try:
				message = self.socket.recv().split('\n')
				command = message[0]
				args = message[1].split()
				print "GOT:",command
				print "   ARGS:", args
				self.commands[command](*args)
			except Exception as e:
				print "Failed"
				print e

class FileManager:

	Pattern = r"LC_(.*)_Calibrated\.csv"	
	LCDir = "/home/rodot/KeplerS82/Data/LC/Calibrated"
	PickleDir = "/home/rodot/KeplerS82/Pickles"
	RedshiftFile = "/home/rodot/KeplerS82/Data/Stripe82ObjectList.dat"
	zList = []
	regex = re.compile(Pattern)
	with open(RedshiftFile,'rb') as f:
		zList = [line.split() for line in f]

	def __init__(self):
		pass
	
	@classmethod
	def getzList(self):

		return self.zList

	@classmethod
	def getLCList(self):

		return os.listdir(self.LCDir)

	@classmethod
	def getPickleList(self):

		return os.listdir(self.PickleDir)

	@classmethod
	def IDList(self, List):

		return self.regex.findall('\n'.join(List))

	@classmethod
	def getProcessed(self):

		return self.IDList(self.getPickleList())

	@classmethod
	def getUnprocessed(self):

		return list(set(self.IDList(self.getLCList())) - set(self.getProcessed()))

	@classmethod
	def getFileName(self, ID):

		return self.getLCList()[self.IDList(self.getLCList()).index(ID)]

	@classmethod
	def getRedshift(self, ID):

		index = [i[0] for i in self.zList].index(ID) #1 is the index for the ID number
		return self.zList[index][3] #3 is the index for redshift



if __name__ == '__main__':

	S = Server()
	S.start()

