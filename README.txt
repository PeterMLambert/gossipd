This is a python implementation of the encrypted messaging platform gossipd. 


COPYRIGHT INFORMATION:

(C) 2017 Peter Lambert. 

You do not have, nor can you ever acquire the right to use, copy or distribute this software. Should you use this software for any purpose, or copy and distribute it to anyone or in any manner, you are breaking the laws of whatever soi-disant jurisdiction, and you promise to continue doing so for the indefinite future.


# TODO:

Add data encryption to files (keys, messages, etc). The encryption scheme means that the data is secure while going over the wire, but everything is curretly stored as plain text, so if anybody accesses your computer then all the data will be compromised.

Port everyhting into ada using fixed field arithmetic.


DEPENDENCIES:

Python 2.7
Tkinter python module for GUI


INCLUDED FILES:

README.txt      - This file
gossippeers.py  - peer class and functions
rsa.py          - functions for RSA encryption, and key generation
mpfhf.py        - a python implementation of the MP fabulous hash function
gossipconfig.py - configuration settings for gossipd
client.py		- GUI client for the gossipd protocol


SETUP:

Edit the settings in gossipconfig.py - set the desired directory information, user nick, IP address, and port.

Start the rsa script and wait a couple minutes for it to generate some keys, two keys will be used for each peer you add.
> python rsa.py

You can add a peer using the command line
> python gossippeers.py PEER_NICK
where PEER_NICK is the other peer's nickname. A private key will be generated in the RecvPeers directory, and a corresponding "public key" will be generated in the main gossipd directory. I put "public key" in quotes because you should share this only with the intended peer, anybody who has this key file will be able to send you messages as that peer. If you share the public key of another peer with anybody, they will then be able to send messages to that peer that appear to come from you. You must transfer the public key file to that peer, it best to use the most secure method available.

Put public keys received from your peers in the SendPeers directory.


USAGE:

To operate the program, type
> python client.py

Commands:
(all commands start with a '/' character, if you want to send a message starting with a /, use '//')

To add a peer (see note above about keys), in the client window type
/a PEER_NICK

Once you have received the public key from a peer, make sure it is in the form PEER_NICK.MYNICK.pbk and place it in the SendPeers directory. If you do this before starting the program, the key will be imported at startup. If the program is running, to import the peer, in the client window type
/i PEER_NICK

help:
/h 

quit:
/q

send a private message:
/p NICK MESSAGE

add a bogus peer:
/b 

Update the peer data (reloads all peer files):
/u 


NOTES:

If you add a peer with the nick of a key that is already being used, the old key will be erased. This can be useful to periodically update the information for a peer, so the program does not stop it, so be careful.

If you switch IP addresses, peers should still receive messages from you but you will not get any replies. So send a message with your updated IP address. The program does not have an automated way to update the IP address for peers (this might be added in the future). You can manually edit the pubkey file in your RecvPeers directory, the IP address is the second line from the bottom.

The program will count the available keys when it starts. Two keys are used each time you add a peer. Four keys are used every time you add a bogus peer. Run the rsa.py script to generate more keys.

This program is written to be used with python 2.7. If you are using python 3 you are doing it wrong and I will not help you if anything bad happens.