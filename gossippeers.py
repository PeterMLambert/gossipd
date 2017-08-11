#! /usr/bin/python

#
# (C) 2017 Peter Lambert. 
# You do not have, nor can you ever acquire the right to use, copy or distribute this software. Should you use this software for any purpose, or copy and distribute it to anyone or in any manner, you are breaking the laws of whatever soi-disant jurisdiction, and you promise to continue doing so for the indefinite future.
#

import os, random
from sys import argv

import rsa
import gossipconfig as conf

# make sure directories are in place
for d in (conf.GossipDir, conf.SendPeers, conf.RecvPeers, conf.KeyDir):
	if not os.path.isdir(d):
		os.makedirs(d)
if not os.path.isfile(os.path.join(conf.GossipDir, 'available')):
	open(os.path.join(conf.GossipDir, 'available'), 'a').close()

class Peer(object):
	def __init__(self, keyA, keyB, nick='', IP='127.0.0.1', port=13000):
		self.nick = nick
		self.IP = IP
		self.port = port
		self.A = keyA
		self.B = keyB

def import_peer(filename):
	f = open(filename, 'r')
	tmp = map(int, f.readline().split(' '))
	A = rsa.Key(tmp[0], tmp[1], tmp[2])
	tmp = map(int, f.readline().split(' '))
	B = rsa.Key(tmp[0], tmp[1], tmp[2])
	nick = f.readline().strip()
	IP = f.readline().strip()
	port = int(f.readline().strip())
	f.close()
	return Peer(A, B, nick, IP, port)
	
def export_peer(peer, filename, private=True):
	f = open(filename, 'w')
	f.write('%d %d %d\n%d %d %d\n%s\n%s\n%s\n' % (
			peer.A.e, peer.A.n, peer.A.d if private else 0,
			peer.B.e, peer.B.n, peer.B.d if private else 0,
			peer.nick,
			peer.IP,
			peer.port))
	f.close()

def _prnt(s):
	print s
	
def loadpeers(directory, pf=_prnt):
	peers = []
	for peer in os.listdir(directory):
		try:
			peers.append(import_peer(os.path.join(directory, peer)))
		except:
			pf('Could not open file %s' % os.path.join(directory, peer))
	pf("Loaded %d peers from %s." % (len(peers), directory))
	return peers
	
def addbogus(pf=_prnt):
	f = open(os.path.join(conf.GossipDir, 'available'), 'r+')
	avail = f.readlines()
	if len(avail) >= 4:
		keys = [rsa.import_key(avail.pop(random.randint(0, len(avail)-1)).strip()) for _ in range(4)]
		f.seek(0)
		f.writelines(avail)
		f.truncate()
		f.close()
	else:
		f.close()
		pf('Not enough keys available.')
		return
	current = loadpeers(conf.SendPeers, pf)
	names = [p.nick.lower() for p in current]
	while True:
		newnick = ''.join(chr(random.randint(97, 122)) for _ in range(random.randint(3, 12)))
		if newnick in names:
			continue
		sfile = os.path.join(conf.SendPeers, '%s.%s.pbk' % (newnick, conf.nick))
		rfile = os.path.join(conf.RecvPeers, newnick)
		if os.path.isfile(sfile) or os.path.isfile(rfile):
			continue
		ip = '%d.%d.%d.%d' % (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
		export_peer(Peer(keys[0], keys[1], newnick, ip, random.randint(10001, 63355)), sfile, private=False)
		export_peer(Peer(keys[2], keys[3], newnick, conf.myIP, conf.port), rfile)
		pf('Added bogus peer %s.' % (newnick))
		break
		

def addpeer(newpeernick):
	f = open(os.path.join(conf.GossipDir, 'available'), 'r+')
	avail = f.readlines()
	if len(avail) >= 2:
		keys = [rsa.import_key(avail.pop(random.randint(0, len(avail)-1)).strip()) for _ in range(2)]
		f.seek(0)
		f.writelines(avail)
		f.truncate()
		
		newpeer = Peer(keys[0], keys[1], newpeernick, conf.myIP, conf.port)
		export_peer(newpeer, os.path.join(conf.RecvPeers, newpeernick))
		pubkey = os.path.join(conf.GossipDir, conf.nick+'.'+newpeernick+'.pbk')
		myinfo = Peer(keys[0], keys[1], conf.nick, conf.myIP, conf.port)
		export_peer(myinfo, pubkey, private=False)
		print 'Public key information written to %s\n transfer this file securely to %s.' % (pubkey, newpeernick)
	else:
		print 'not enough keys available.'
	f.close()

if __name__=='__main__':
	if len(argv) > 1 :
		addpeer(argv[2])
	else:
		print 'Usage: python %s PEER_NICK' % (argv[0])