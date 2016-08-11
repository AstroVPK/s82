import zmq, sys, os, time, cPickle, StringIO, numpy as np, re, random
import carmcmc as cm
import multiprocessing as mp
from JacksTools import jio


class Server:

	def __init__(self):

		self.context = zmq.Context(io_threads = 4)

		self.socket = self.context.socket(zmq.REP)
		self.socket.bind('tcp://*:5001')
		self.running = True

		self.commands = {
		'getLC':self.getLC, 
		'randLC':self.randLC,
		'IDList':self.getIDList,
		'isValid':self.isValidCommand,
		'argCount':self.getArgCount,
		'ping': self.respond}
	
		print "Server Started"

	def respond(self): #respond to arbitrary request

		self.socket.send_pyobj(1)
		print "Server has been pinged"

	def getArgCount(self, command):

		result = self.commands[command].func_code.co_argcount
		self.socket.send_pyobj(result)
		print "Sent arg count for %s" % command

	def isValidCommand(self, server_func):

		isValid = False
		if server_func in self.commands:
			isValid = True
		self.socket.send_pyobj(isValid)
		print "Sent %s" % str(isValid)

	def getLC(self, ID):

		fname = os.path.join(FileManager.LCDir, FileManager.getFileName(ID))
		data = jio.load(fname, delimiter = ',', headed = True)
		z = FileManager.getRedshift(ID)
		package = (fname, z, data)	
		self.socket.send_pyobj(package)
		print "Sent %s" % FileManager.getFileName(ID)

	def getIDList(self):

		idlist = FileManager.IDList(FileManager.getLCList())
		self.socket.send_pyobj(idlist)
		print "Sent %s" % "id list"

	def randLC(self):

		ID = random.choice(FileManager.IDList(FileManager.getLCList()))
		self.getLC(ID)

	#below here are server specific (sort of private) functions

	def ErrorMsg(self, *args):
		
		error = Exception(*args)
		self.socket.send_pyobj(error)
		print "Sent Exception %s" % args[0]

	def isRunning(self):

		return self.running

	def stop(self):

		self.running = False

	def quit(self):

		self.running = False
		self.socket.close()
		sys.exit(0)

	def processCMD(self, cmd): # process a command input from keyboard

		if cmd.lower() in ['exit','quit']:
			print "Quitting"
			self.quit()
		elif cmd.lower() in ['stop']:
			if self.isRunning():
				print "Stopping Server"
				self.stop()
				return True
			else:
				print "The server is already stopped"
				return True
		elif cmd.lower() in ['start']:
			if self.isRunning():
				print "The server is already running"
				return True
			else:
				print "Starting Server"
				self.start()
				return False

	def start(self):

		self.running = True
		while self.isRunning():
			try:
				message = self.socket.recv().split('\n')
				command = message[0]
				args = message[1].split()
				print "GOT:",command
				print "   ARGS:", args
				self.commands[command](*args)

			except KeyboardInterrupt as k:
				print "KeyboadInterrupt detected, would you like to do something?"
				cmd = raw_input("=> ")
				self.processCMD(cmd)
				
			except Exception as e:
				print "Failed"
				print e
				self.ErrorMsg(*e.args)

		cmd = raw_input("=> ")
		while self.processCMD(cmd):
			cmd = raw_input("=> ")

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

