#!/usr/bin/python2

import os
import sys
import urllib2
import zipfile

pathname = os.path.dirname(sys.argv[0])
scriptdir = os.path.abspath(pathname)
mcwebdir = os.path.abspath(os.path.join(scriptdir, '../'))

mcjar = os.path.join(scriptdir, 'minecraft_client.jar')
mcterrain = os.path.join(mcwebdir, 'static', 'images', 'terrain.png')

def update_client_binary():
	u = urllib2.urlopen('http://s3.amazonaws.com/MinecraftDownload/minecraft.jar')
	f = open(mcjar, 'w')
	f.write(u.read())
	f.close()

if __name__ == '__main__':
	print "Downloading minecraft_client.jar ... ",
	sys.stdout.flush()
	update_client_binary()
	print "\bDONE"
	z = zipfile.ZipFile(mcjar, 'r')
	print "Extracting terrain.png ... ",
	sys.stdout.flush()
	f = open(mcterrain, 'w')
	f.write(z.read('terrain.png'))
	f.close()
	print "\bDONE"
	os.unlink(mcjar)
