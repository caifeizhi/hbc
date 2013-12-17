import socket

class HbcClient(object):
	port = 9531
	
	def __init__(self):
		self.index = -1
		self.clisocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.step = 0

	def __del__(self):
		self.clisocket.close()

	def getServerIP(self):
		return "127.0.0.1"

	def connect(self, ip):
		self.clisocket.connect((ip, self.port))

		self.run()

	def run(self):
		while (self.step <= 7):
			print "step ", self.step
			if (self.step == 0):
				data = self.getindex()

			if (self.step == 1):
				data = self.step1()

			if (self.step == 2):
				data = self.step2()

			if (self.step == 3):
				data = self.step3()

			if (self.step == 4):
				data = self.step4()

			if (self.step == 5):
				data = self.step5()

			if (self.step == 6):
				data = self.step6()

			if (self.step == 7):
				data = self.step7()

			self.step = self.step + 1
		
	def recvmsg(self):
		data = self.clisocket.recv(1024)

		datalist = data.split(':', 1)
		msgheader = datalist[0]
		msgdata = datalist[1]

		return (msgheader, msgdata)

	def getindex():
		(msgheader, msgdata) = self.recvmsg()
		if (msgheader == "index")
			self.index = int(msgdata)

	def step1(self):
		pass

	def step2(self):
		pass

	def step3(self):
		pass

	def step4(self):
		pass

	def step5(self):
		pass

	def step6(self):
		pass

	def step7(self):
		pass

if __name__ == "__main__":
	client = HbcClient()
	client.connect(client.getServerIP())
	print "Hello world!"
