import zmq

addr = "tcp://newton.physics.drexel.edu:5001"
addr = "tcp://76.124.106.126:5001"
addr = "tcp://vish15.physics.upenn.edu:5001"

def getSocket():

	context = zmq.Context()
	socket = context.socket(zmq.REQ)
	socket.connect(addr)
	return socket

def getRandLC():

	socket = getSocket()

	socket.send(b"randLC\n0")
	fname, z, data = socket.recv_pyobj()
	socket.close()
	return fname, z, data

def getLC(ID):

	try:
		socket = getSocket()

		socket.send(b"getLC\n%s" % ID)
		returnObj = socket.recv_pyobj()
	except Exception as e:
		print e
		raise IOError(b'Internal Server Error...')

	if returnObj is not None:
		fname, z, data = returnObj
	else:
		raise IOError(b"%s not found on server!"%(ID))
	socket.close()
	return fname, z, data

def getIDList():

	socket = getSocket()

	socket.send(b"IDList\n0")
	idlist = socket.recv_pyobj()
	socket.close()
	return idlist


if __name__ == '__main__':

	import sys
	if len(sys.argv) == 1:
		print "Test"
	elif sys.argv[1] == '--rand':
		print getRandLC()	
	elif sysargv[1] == '--list':
		print getIDList()

