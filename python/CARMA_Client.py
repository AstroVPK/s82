import zmq

addr = "tcp://newton.physics.drexel.edu:5001"

def getRandLC():

	context = zmq.Context()
	socket = context.socket(zmq.REQ)
	socket.connect(addr)

	socket.send(b"randLC\n0")
	fname, z, data = socket.recv_pyobj()
	socket.close()
	return fname, z, data

def getLC(ID):

	context = zmq.Context()
	socket = context.socket(zmq.REQ)
	socket.connect(addr)

	socket.send(b"getLC\n%s" % ID)
	fname, z, data = socket.recv_pyobj()
	socket.close()
	return fname, z, data

def getIDList():

	context = zmq.Context()
	socket = context.socket(zmq.REQ)
	socket.connect(addr)

	socket.send(b"IDList\n0")
	idlist = socket.recv_pyobj()
	socket.close()
	return idlist


if __name__ == '__main__':

	print getRandLC()	

