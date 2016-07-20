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

	socket = getSocket()

	socket.send(b"getLC\n%s" % ID)
	fname, z, data = socket.recv_pyobj()
	socket.close()
	return fname, z, data

def getIDList():

	socket = getSocket()

	socket.send(b"IDList\n0")
	idlist = socket.recv_pyobj()
	socket.close()
	return idlist


if __name__ == '__main__':

	print getRandLC()	

