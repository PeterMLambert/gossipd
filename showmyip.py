#! /usr/bin/python

import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
	s.connect(("8.8.8.8", 80))
	print 'Local IP: %s' % (s.getsockname()[0])
	s.close()
except SocketError:
	print 'Could not open socket'

from urllib import urlopen
try:
	data = urlopen('http://checkip.dyndns.com/').read()
	print data[data.find('<body>')+6:data.find('</body>')]
except:
	print 'Could not open http://checkip.dyndns.com/'