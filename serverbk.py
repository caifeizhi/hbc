import socket
import pickle
import sys
import time
import thread
import random
import paillier

_KEY = '0123456789abcdef'
_PAILLIER = paillier.Paillier(_KEY)

def changekey(key):
    _PAILLIER = paillier.Paillier(key)

class PlainPoly(object):
    def __init__(self, s = None):
        self.f = {}
        if (s == None or len(s) <= 0):
            self.f[0] = 0
            return

        #f = (x - s0) * (x - s1) * ... * (x - sn)
        self.f[0] = -s[0]
        self.f[1] = 1
        for i in range(1, len(s)):
            self.f[i + 1] = 1
            for j in range(i, 0, -1):
                self.f[j] = self.f[j - 1] - self.f[j] * s[i]
            self.f[0] = self.f[0] * -s[i]

    def __mul__(self, other):
        if (type(other) == CipherPoly):
            return other * self

    def __add__(self, other):
        if (type(other) == CipherPoly):
            return other + self

    def __str__(self):
        return str(self.f)

    def encrypt(self):
        cp = CipherPoly()
        for i in range(len(self.f)):
            print self.f[i]
            cp.f[i] = _PAILLIER.EncryptInt64(self.f[i])
        return cp

    @staticmethod
    def random(n):
        p = PlainPoly()
        for i in range(n):
            p.f[i] = random.randint(0, 2 ** 32 -1)
        return p

class CipherPoly(object):
    def __init__(self):
        self.f = {}

    def __add__(self, other):
        if (type(other) == CipherPoly):
            cp = CipherPoly()
            for i in range(0, max(len(self.f), len(other.f))):
                if (i >= len(self.f)):
                    cp.f[i] = other.f[i]
                    continue
                if (i >= len(other.f)):
                    cp.f[i] = self.f[i]
                    continue
                cp.f[i] = _PAILLIER.Add(self.f[i], other.f[i])
            return cp

        return self

    def __mul__(self, other):
        if (type(other) != PlainPoly):
            return

        cp = CipherPoly()
        upper = len(other.f) + len(self.f) - 2
        for i in range(upper, -1, -1):
            cp.f[i] = _PAILLIER.EncryptInt64(0)
            for j in range(len(self.f) - 1, -1, -1):
                if (i - j < 0 or i - j > len(other.f) - 1):
                    continue
                mul = _PAILLIER.Affine(self.f[j] , other.f[i - j])
                cp.f[i] = _PAILLIER.Add(mul, cp.f[i])

        return cp

    def decrypt(self):
        pp = PlainPoly()
        for i in range(len(self.f)):
            pp.f[i] = _PAILLIER.DecryptInt64(self.f[i])
        return pp

class HbcAgent(object):
    PORT = 9531
    DATALEN = 1024
    splitter = "#"

    def __init__(self):
        self.debug = True

    def debug(self, message):
        if (self.debug):
            print message

    #send data without length limit
    def send(self, sock, data):
        maxseq = len(data) / self.DATALEN
        seq = 0
        while (seq <= maxseq):
            senddata = str(seq) + self.splitter + str(maxseq) + self.splitter + data[seq * self.DATALEN:(seq + 1)* self.DATALEN - 1]
            self.debug("sendding data:" + senddata)
            sock.send(senddata)
            seq = seq + 1

    #recv data withtou length limit
    def recv(self, sock):
        realdatalist = {}
        while True:
            data = sock.recv(self.DATALEN + 16)
            datalist = data.split(self.splitter, 2)
            self.debug("recv debug:" + data)
            seq = int(datalist[0])
            maxseq = int(datalist[1])
            realdata = datalist[2]
            realdatalist[seq] = realdata
            self.debug("debug:" + str(maxseq) + ":" + str(realdatalist))
            if (len(realdatalist) > maxseq):
                break

        wholedata = ""
        for i in range(len(realdatalist)):
            wholedata = wholedata + realdatalist[i]

        self.debug("the whole data is :" + wholedata)
        return wholedata

    def recvmsg(self, sock, msgheader):
        data = self.recv(sock)
        datalist = data.split(self.splitter, 1)

        if (msgheader == datalist[0]):
            return pickle.loads(datalist[1])
        else:
            return None

    def sendmsg(self, sock, msgheader, data):
        msgdata = pickle.dumps(data)
        senddata = msgheader + self.splitter + msgdata
        self.debug("sendding data:" + msgheader + str(data))
        self.send(sock, senddata)

class HbcServer(HbcAgent):
    def __init__(self, c, n):
        self.srvsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.c = c
        self.n = n
        self.addrlist = {}

    def __del__(self):
        self.srvsock.close()

    def run(self):
        #bind address
        addr = ("localhost", self.PORT)
        self.srvsock.bind(addr)
        self.srvsock.listen(self.n)

        #common info
        info = {}
        info["c"] = self.c
        info["n"] = self.n

        #wait for connection
        clisocklist = {}
        i = 0
        while (i < self.n):
            clisock, addr = self.srvsock.accept()
            clisocklist[i] = clisock
            info["index"] = i
            self.sendmsg(clisock, "info", info)
            cliaddr = self.recvmsg(clisock, "addr") # client listen addr
            self.addrlist[i] = cliaddr
            i = i + 1

        #send addrlist infomation

        for i in range(len(clisocklist)):
            self.debug(str(self.addrlist))
            self.sendmsg(clisocklist[i], "addrlist", self.addrlist)
            clisocklist[i].close()

class HbcClient(HbcAgent):
    def __init__(self):
        self.srvsock = None
        self.step = -1
        self.theta = None

    def __del__(self):
        if (self.srvsock != None):
            self.srvsock.close()

    def connect(self, ip):
        clisock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clisock.connect((ip, self.PORT))
        info = self.recvmsg(clisock, "info")
        self.c = info["c"]
        self.n = info["n"]
        self.index = info["index"]

        #search for a point to bind
        point = self.index
        flag = True
        while True:
            try:
                flag = True
                self.srvsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                addr = ("localhost", self.PORT + point)
                print self.srvsock.bind(addr)
            except socket.error:
                point = point + 1
                flag = False
            if (flag):
                break

        self.srvsock.listen(self.n)
        self.sendmsg(clisock, "addr", addr)

        #info update commplete
        self.addrlist = self.recvmsg(clisock, "addrlist")
        self.step = 0

        clisock.close()

    def recvthread(self):
        while (self.step < 7):
            clisock, addr = self.srvsock.accept()

            if (self.step <= 1):
                i = 0
                while (i < self.c):
                    cp = self.recvmsg(clisock, "f")
                    self.theta = self.theta + cp * PlainPoly.random(len(self.s))
                    i = i + 1

                self.step = 2
                print self.theta
            clisock.close()


    def sendbyindex(self, index, msgheader, data):
        clisock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clisock.connect(self.addrlist[index])
        self.sendmsg(clisock, msgheader, data)
        clisock.close()
        pass

    def getinputset(self,filename = "", splitter = ' '):
        if (filename == ""):
            filename = str(self.index) + ".dat"

        filehd = open(filename, "r+")
        data = filehd.read()
        datalist = data.split(splitter)
        self.s = {}
        for i in range(len(datalist)):
            self.s[i] = int(datalist[i])

        self.f = PlainPoly(self.s)

    def run(self):
        self.theta = self.f.encrypt() * PlainPoly.random(len(self.s))
        thread.start_new_thread(self.recvthread, ())

        for i in range(1, self.c + 1):
            cp = self.f.encrypt()
            self.sendbyindex((self.index + i) % self.n, "f", cp)

        time.sleep(30)

if __name__ == "__main__":
    if (len(sys.argv) > 1 and sys.argv[1] == "server"):
        server = HbcServer(1, 2)
        server.run()
    if (len(sys.argv) > 1 and sys.argv[1] == "client"):
        client = HbcClient()
        client.connect("localhost")
        client.getinputset()
        client.run()
    if (len(sys.argv) > 1 and sys.argv[1] == "test"):
        a = {}
        a[0] = 1
        a[1] = 3
        #a[2] = 5
        p = PlainPoly(a)
        c = p.encrypt()
        b = {}
        b[0] = 0
        b[1] = 0
        b[2] = 0
        p = PlainPoly(b)
        print c.decrypt()
        c2 = c * p
        print c2.decrypt()
        c3 = c + c2
        print c3.decrypt()



