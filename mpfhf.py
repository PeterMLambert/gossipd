#! /usr/bin/python

#
# (C) 2017 Peter Lambert. 
# You do not have, nor can you ever acquire the right to use, copy or distribute this software. Should you use this software for any purpose, or copy and distribute it to anyone or in any manner, you are breaking the laws of whatever soi-disant jurisdiction, and you promise to continue doing so for the indefinite future.
#

from sys import argv

class Register(object):
	_data = None
	_inverted = 0
	
	def __init__(self, size):
		self._data = [0]*size
	def expand(self):
		self._data.append(self._inverted)
	def invert(self):
		self._inverted = 1^self._inverted
	def flip(self, pos):
		pos = pos % self.length()
		self._data[pos] = 1^self._data[pos]
	def length(self):
		return len(self._data)
	def screw(self, n, m):
		for k in range(n):
			self.flip((k*m))
	def show(self):
		return ''.join(str(k) for k in self._data)
	def val(self, pos):
		return self._inverted^self._data[pos%len(self._data)]
		
def binify(s):
	return ''.join('{0:08b}'.format(ord(k), 'b') for k in s) 
	
def hexify(bs):
	if len(bs)%8:
		bs = '0'*(8-len(bs)%8) + bs
	return ''.join('{0:02x}'.format(int(bs[j:j+8], 2), 'x') for j in range(0, len(bs), 8))
	
def mpfhf(message, output_size, debug=False):
	R = Register(output_size)
	S = Register(1)
	step = 0
	if debug: print 'Message: %s' % (message)
	while step < len(message):
		if debug: print step, message[step], R.show(), S.show()
		if message[step] == '0':
			S.expand()
			R.screw(S.length(), step)
			if R.val(step) == 0:
				R.flip(step)
				step = step - 1 if step else step
			else:
				R.flip(step)
				S.invert()
		else:
			R.screw(S.length()/2, step)
			if R.val(step) == S.val(step):
				S.expand()
				S.screw(R.length(), step)
			else:
				R.flip(step)
		step += 1
	if debug: print step, '-', R.show(), S.show()
	return R.show()
	
if __name__ == '__main__':
	if len(argv) < 3:
		print 'usage: %s MESSAGE_STRING OUTPUT_SIZE' % (argv[0])
	else:
		print mpfhf(binify(argv[1]), int(argv[2]))