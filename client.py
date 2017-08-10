#! /usr/bin/python

# This is a GUI client for gossipd.

#
# (C) 2017 Peter Lambert. 
# You do not have, nor can you ever acquire the right to use, copy or distribute this software. Should you use this software for any purpose, or copy and distribute it to anyone or in any manner, you are breaking the laws of whatever soi-disant jurisdiction, and you promise to continue doing so for the indefinite future.
#

import Tkinter as T
import os, random, socket, threading, time
from Queue import Queue
from binascii import crc32

import rsa
import gossippeers as g
import gossipconfig as conf

MAXUDPSIZE = 512 # maximum size of UDP-gram
MAXMESSAGE = MAXUDPSIZE / 2 - 17 - len(conf.nick) # leaving room for encryption, checksum of 4 bytes, time, and nick

def cs(s):
	return rsa.n_to_s(crc32(s))

class Listener(threading.Thread):
	def __init__(self, master=None):
		threading.Thread.__init__(self)
		self.master = master
		self.cont = True
		self.master.printm("Loading receiving peer information ...")
		self.peers = g.loadpeers(conf.RecvPeers, self.master.printm)
		
	def run(self):
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
		sock.bind(("", conf.port))
		sock.settimeout(conf.sockettimeout)
		messages = []
		
		while self.cont:
			try:
				data, addr = sock.recvfrom(MAXUDPSIZE) # buffer size
				# self.master.printm(rsa.hexify(data))
				for peer in self.peers:
					message = rsa.unpad(data, peer.A, peer.B).strip('\x00')
					if cs(message) == message[:4]:
						if message not in messages:
							messages.append(message)
							logfile = open('messagelog', 'a')
							logfile.write(message[4:]+'\n')
							logfile.close()
							if message.split(' ')[1]!='PRIVMSG:':
								self.master.relay.mq.put(message)
							self.master.printm("%d %s: %s" % (int(time.time()), peer.nick, message[4:]))
						break
			except socket.timeout:
				pass
		sock.close()
		
	def add_peer(self, newpeer):
		filename = os.path.join(conf.RecvPeers, newpeer)
		if os.path.isfile(filename):
			self.peers.append(g.import_peer(filename))
	
class Relay(threading.Thread):
	def __init__(self, master=None):
		threading.Thread.__init__(self)
		self.cont = True
		self.mq = Queue()
		self.newpeer = False
		self.master = master
		self.master.printm("Loading sending peer information ...")
		self.peers = g.loadpeers(conf.SendPeers, self.master.printm)
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
	def run(self):
		while self.cont:
			m = self.mq.get()
			if m:
				for peer in self.peers:
					self.sock.sendto(rsa.padencrypt(m, peer.A, peer.B), (peer.IP, peer.port))	
			if self.newpeer:
				filename = os.path.join(conf.SendPeers, self.newpeer+'.'+conf.nick+'.pbk')
				if os.path.isfile(filename):
					self.peers.append(g.import_peer(filename))
				self.newpeer = False

class App(T.Frame):
	def __init__(self, master=None):
		T.Frame.__init__(self, master)
		self.pack()
		self.create_widgets()
		
		f = open(os.path.join(conf.GossipDir, 'available'), 'r')
		self.printm('There are %d keys currently available' % (len(f.readlines())))
		f.close()
	
		self.listener = Listener(self)
		self.listener.start()
		self.relay = Relay(self)
		self.relay.start()
	
	def quit(self):
		self.printm('Exiting ...')
		self.listener.cont = False
		self.relay.cont = False
		self.relay.mq.put('')
		self.listener.join()
		self.relay.join()
		T.Frame.quit(self)
	
	def create_widgets(self):
		if conf.showbuttons:
			self.bbox = T.Frame(self)
			self.bbox.pack({'side': 'top'})
			
			self.UPDATE = T.Button(self.bbox, text='Update Peers', command=self.update_peers)
			self.UPDATE.pack({"side": "left"})
			
			self.QUIT = T.Button(self.bbox, text='Quit', command=self.quit)
			self.QUIT.pack({"side": "left"})
			
		self.scrollbox = T.Frame(self, width=700, height=600)
		self.scrollbox.pack(fill='both', expand=True)
		self.scrollbox.grid_propagate(False)
		self.scrollbox.grid_rowconfigure(0, weight=1)
		self.scrollbox.grid_columnconfigure(0, weight=1)
		self.textbox = T.Text(self.scrollbox, borderwidth=1, wrap='word')
		self.textbox.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
		self.scroller = T.Scrollbar(self.scrollbox, command=self.textbox.yview)
		self.scroller.grid(row=0, column=1, sticky='nsew')
		self.textbox['yscrollcommand'] = self.scroller.set
		
		self.entrybox = T.Entry(width=116)
		self.entrybox.pack({"side": "bottom", 'expand': 'True'})
		self.entrybox.focus_set()
		self.user_entry = T.StringVar()
		self.entrybox["textvariable"] = self.user_entry
		self.entrybox.bind('<Key-Return>', self.user_input)
		
	def update_peers(self):
		self.listener.peers = g.loadpeers(conf.RecvPeers, self.printm)
		self.relay.peers = g.loadpeers(conf.SendPeers, self.printm)
		
	def user_input(self, event):
		m = self.user_entry.get()
		datedm = '%s%d %s: %s' % (cs(m), time.time(), conf.nick, m)
		self.user_entry.set('')
		if m.startswith('/'):
			self.printm(m)
			if m.startswith('/q'): # quit
				self.quit()
			elif m.startswith('/h'): # help
				self.printm('\nCommands: \n'
						'//REST_OF_MESSAGE : start a message with /\n'
						'/a NICK : add a peer with name NICK \n'
						'/h : this list of commands \n'
						'/i NICK : import pubkey for NICK \n'
						'/p NICK MESSAGE : send a private message to NICK \n'
						'/u : Update peers \n'
						'/q : quit')
			elif m.startswith('//'): # send a message starting with /
				datedm = '%s%d %s: %s' % (cs(m), time.time(), conf.nick, m[1:])
				self.listener.messages.append(datedm)
				self.relay.mq.put(datedm)
			elif m.startswith('/p'): # send a direct message
				try:
					topeer, m = m.split(' ', 2)[1:]
					for peer in self.relay.peers:
						if topeer == peer.nick:
							self.relay.sock.sendto(
									rsa.padencrypt(peer.cs+conf.nick+' PRIVMSG: '+m, peer.A, peer.B), 
									(peer.IP, peer.port))
							break
					else:
						self.printm('Could not find peer %s' % (topeer))
				except ValueError:
					self.printm('usage: /p NICK MESSAGE')
			elif m.startswith('/a'): # add a new peer to receive from, create pubkey for them
				newpeernick = m.split(' ')[1]
				f = open(os.path.join(conf.GossipDir, 'available'), 'r+')
				avail = f.readlines()
				keys = [rsa.import_key(avail.pop(random.randint(0, len(avail))).strip()) for k in [0, 1]]
				f.seek(0)
				f.writelines(avail)
				f.truncate()
				f.close()
				
				newpeer = g.Peer(keys[0], keys[1], newpeernick, conf.myIP, conf.port)
				g.export_peer(newpeer, os.path.join(conf.RecvPeers, newpeernick))
				
				myinfo = g.Peer(keys[0], keys[1], conf.nick, conf.myIP, conf.port)
				pubkey = os.path.join(conf.GossipDir, conf.nick+'.'+newpeernick+'.pbk')
				g.export_peer(myinfo, pubkey, private=False)
				self.printm('Public key information written to %s, transfer this file securely to %s.' % 
						(pubkey, newpeernick))
				self.listener.add_peer(newpeernick)
			elif m.startswith('/i'): # import pubkey to send to
				newnick = m.split(' ')[1]
				filename = os.path.join(conf.SendPeers, newnick+'.'+conf.nick+'.pbk')
				if os.path.isfile(filename):
					relay.peers.append(g.import_peer(filename))
				else:
					self.printm("Could not find file %s" % (filename))
			elif m.startswith('/u'):
				self.update_peers()
			else:
				self.printm("Unknown command: %s" % (m))
		else:
			self.printm(datedm)
			self.listener.messages.append(datedm)
			self.relay.mq.put(datedm)
		
	def printm(self, message):
		self.textbox.insert('end', message+'\n')
		self.textbox.see('end')
		
root = T.Tk()
root.wm_title("GossipD")
app = App(master=root)
app.mainloop()
root.destroy()
