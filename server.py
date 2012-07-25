#!/usr/bin/python2

import os
import re
import subprocess
import config
from time import sleep

# java -Xms1536M -Xmx1536M -jar minecraft_server.jar nogui 
#        ^ min     ^ max  memory in MB
# min: reserved on startup
# max: maximum allocation (realloc on demand)

class NotRunning(Exception):
	pass

class CommunicationError(Exception):
	pass

player_regex = re.compile(r"Connected players: (.*)\n")

process = None

def start():
	global process
	#FIXME: check port (report old pid)
	mem = config.get('server_memory')
	cmd = ['java', '-Xms%dM' % mem, '-Xmx%dM' % mem, '-jar', 'minecraft_server.jar', 'nogui']
	process = subprocess.Popen(cmd, cwd='mcs',
		stderr=subprocess.STDOUT,
		stdout=open('/dev/null', 'w'),
		stdin=subprocess.PIPE
	)

def stop():
	global process
	cmd('stop')
	for i in xrange(3):
		if not process.poll() == None: return 0
		sleep(1)
	process.terminate()
	for i in xrange(3):
		if not process.poll() == None: return 5
		sleep(1)
	process.kill()
	return 9


def running():
	try:
		return (process.poll() == None)
	except:
		return False

def cmd(command):
	if running():
		process.stdin.write(command+"\n")
		sleep(0.1)
	else:
		raise NotRunning()

def cmd_out(command):
	if running():
		oldsize = os.path.getsize('mcs/server.log')
		cmd(command)
		for i in xrange(3):
			if os.path.getsize('mcs/server.log') > oldsize: break
			sleep(0.1)
		mclogf = open('mcs/server.log')
		mclogf.seek(oldsize)
		mclog = mclogf.read()
		mclogf.close()
		return mclog
	else:
		raise NotRunning()

def connected_users():
	#2012-07-25 16:17:05 [INFO] Connected players: user1, test
	mclog = cmd_out('list')
	try:
		players = player_regex.search(mclog).group(1)
		players = players.split(', ')
		return players
	except AttributeError:
		raise CommunicationError()

def info():
	info = {}
	info['running'] = running()
	if running():
		info['connected_users'] = connected_users()
	return info
