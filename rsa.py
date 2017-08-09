#! /usr/bin/python

#
# (C) 2017 Peter Lambert. 
# You do not have, nor can you ever acquire the right to use, copy or distribute this software ; Should you use this software for any purpose, or copy and distribute it to anyone or in any manner, you are breaking the laws of whatever soi-disant jurisdiction, and you promise to continue doing so for the indefinite future.
#

import random
from os import urandom

class Key(object):
	def __init__(self, e, n, d=0):
		self.e = e
		self.n = n
		self.d = d
		self.private = bool(d)
		self.l = len(n_to_s(self.n))

def padencrypt(m, keya, keyb):
	'''Takes a string, splits it into chunks and xor's them with random bytes, then encrypts to two keys.
	Returns an array of arrays holding the random string and the xor'ed result string.'''
	padlen = min(keya.l, keyb.l) - 1 # make sure that the strings will not overflow the key mods
	cutmessage = []
	while len(m) > padlen:
		cutmessage.append(m[:padlen])
		m = m[padlen:]
	if len(m) > 0:
		cutmessage.append(m + '\x00'*(padlen-len(m)))
	for k in range(len(cutmessage)):
		r = urandom(len(cutmessage[k]))
		cutmessage[k] = encrypt(r, keya) + encrypt(xor(r, cutmessage[k]), keyb)
	return ''.join(cutmessage)
	
def unpack(pm, keya, keyb):
	'''Takes a string (the result of padding, encrypting, and joining) and breaks it into pieces ready for decrypting.
	Returns an array of arrays holding the encrypted random string and xor'ed message.'''
	res = []
	seclen = keya.l+keyb.l
	while len(pm) > 0:
		res.append([pm[:keya.l], pm[keya.l:seclen]])
		pm = pm[seclen:]
	return res

def unpad(xorpair, keya, keyb):	
	padlen = min(keya.l, keyb.l) - 1
	return xor(decrypt(xorpair[0], keya, padlen), decrypt(xorpair[1], keyb, padlen))

def fermat_test(n):
	''' Use the fermat test to check if n is prime. '''
	primes = [2, 3, 5, 7, 11, 13]
	if n in primes:
		return True
	for a in primes:
		if n % a == 0:
			return False
		elif pow(a, n-1, n) != 1:
			return False
	return True

small_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31] # etc.

def miller_rabin(n, strength=10):
    """Return True if n passes strength rounds of the Miller-Rabin primality
    test (and is probably prime). Return False if n is proved to be
    composite.

    """
    for p in small_primes:
        if n % p == 0: return False
    r, s = 0, n - 1
    while s % 2 == 0:
        r += 1
        s //= 2
    for _ in range(strength):
        a = random.randint(2, n - 2)
        x = pow(a, s, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True
	
def genkey(nbits, e):
	''' Generate an RSA key with modulus of length about nbits and exponent e.
	Returns Key object'''
	found = False
	p = [0]*2
	while not found:
		for k in [0, 1]:
			p[k] = random.randint(2**(nbits/2-1), 2**(nbits/2))
			if p[k] % 2 == 0:
				p[k] += 1
			while not miller_rabin(p[k]):
				p[k] += 2
		m = (p[0]-1)*(p[1]-1)
		found = bool(m % e)
	d = find_inverse(e, m)
	n = p[0]*p[1]
	return Key(e, n, d)
	
def xor(m1, m2):
	''' produces the xor of the strings m1 and m2. Output length is set by length of m1.'''
	return ''.join(chr(ord(m1[k]) ^ ord(m2[k % len(m2)])) for k in range(len(m1)))

def s_to_n(s):
	'''Convert string s into a number.'''
	resn = 0
	for k in s:
		resn *= 256
		resn += ord(k)
	return resn
		
def n_to_s(n):
	'''Convert number n to a string.'''
	s = ''
	while n > 0:
		s = chr(n % 256) + s
		n = n / 256
	return s
	
# Part of find_inverse below
# See: http://en.wikipedia.org/wiki/Extended_Euclidean_algorithm
def eea(a,b):
	if b==0:return (1,0)
	(q,r) = (a//b,a%b)
	(s,t) = eea(b,r)
	return (t, s-(q*t) )

# Find the multiplicative inverse of x (mod y) (this is used in key generation for RSA)
# see: http://en.wikipedia.org/wiki/Modular_multiplicative_inverse
def find_inverse(x,y):
	''' Find the inverse of x (mod y). '''
	inv = eea(x,y)[0]
	if inv < 1: inv += y #we only want positive values
	return inv

def encrypt(message, key):
	mess = n_to_s(pow(s_to_n(message), key.e, key.n))
	mess = '\x00'*(key.l - len(mess)) + mess
	return mess
	
def decrypt(encrypted, key, reslen):
	decrypted = n_to_s(pow(s_to_n(encrypted), key.d, key.n))
	if reslen > len(decrypted):
		decrypted = '\x00'*(reslen-len(decrypted))+decrypted
	return decrypted
	
def hexify(s):
	return ''.join('{0:02x}'.format(ord(k), 'x') for k in s) 
	
def unhexify(h):
	if len(h)%2:
		h = '0'+h
	return ''.join(chr(int(h[k:k+2], 16)) for k in range(0, len(h), 2)) 
	
def export_key(key, filename, private=True):
	f = open(filename, 'w')
	f.write('%d %d %d\n' % (key.e, key.n, key.d if private else 0))
	f.close()
	
def import_key(filename):
	f = open(filename, 'r')
	e, n, d = map(int, f.readline().split(' '))
	f.close()
	return Key(e, n, d)

if __name__=='__main__':
	import os
	import mpfhf
	from gossipconfig import GossipDir, KeyDir
	from time import asctime
	
	print "Generating RSA keys, this will take a couple minutes. Use Ctrl-C to exit."
		
	try:
		while True:
			newkey = genkey(4096, 35567)
			khash = mpfhf.hexify(mpfhf.mpfhf(format(newkey.n, 'b'), 64))
			print '%s Found key with hash %s' % (asctime(), khash)
			hpath = os.path.join(KeyDir, khash[0], khash[1])
			if not os.path.isdir(hpath):
				os.makedirs(hpath)
			filename = os.path.join(hpath, khash)
			if os.path.isfile(filename): # check for hash collisions
				ext = 1
				while os.path.isfile(filename+format(ext, 'x')):
					ext += 1
				filename = filename+format(ext, 'x')
			export_key(newkey, filename)
			f = open(os.path.join(GossipDir, 'available'), 'a')
			f.write('%s\n' % (filename))
			f.close()
	except KeyboardInterrupt:
		print "Exiting."
	