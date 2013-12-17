import socket

class HbcServer(object):
	port = 9531

	def __init__ (self, size):
		self.size = size 		
		self.clilist = []
		self.srvsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	def __del__(self):
		for element in self.clilist:
			element[1].close()
		self.srvsock.close()

	def wait(self):
		self.srvsock.bind(('', self.port))
		self.srvsock.listen(self.size)

		index = 0
		while (index < self.size):
			clisock, (clientIP, clientPort) = self.srvsock.accept()
			self.clilist.append((index, clisock))
			self.sendmsg(index, "index", "")
			index = index + 1

	def sendmsg(self, index, msgtype, msg):
		if (msgtype == "index"):
			data = "index:" + str(index)
			self.clilist[index][1].send(data)

	def run(self):
		while True:
			data = self.srvsock.recv(1024)
			self.handle(data)

	def handle(self, data):
		datalist = data.split(':', 1)	
		msgheader = datalist[0]
		msgdata = datalist[1]

		if (msgheader == "all"):
			return False
		
		if (msgheader == "die"):
			return True
			
		index = int(msgheader)
		print str(index + 1)
		
if __name__ == "__main__":
	server = HbcServer(2)
	server.wait()
