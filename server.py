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
start_regex = re.compile(r"For help, type \"help\" or \"\?\"")
prepare_regex = re.compile(r"Preparing")

process = None

def start():
	global process
	#FIXME: check port (report old pid)
	if running():
		return False
	mem = config.get('server_memory')
	cmd = ['java', '-Xms%dM' % mem, '-Xmx%dM' % mem, '-jar', 'minecraft_server.jar', 'nogui']
	process = subprocess.Popen(cmd, cwd='mcs',
		stderr=subprocess.STDOUT,
		stdout=open('/dev/null', 'w'),
		stdin=subprocess.PIPE
	)
	oldsize = os.path.getsize('mcs/server.log') if os.path.isfile('mcs/server.log') else 0
	lastsize = oldsize
	i = 10
	while i > 0:
		if os.path.isfile('mcs/server.log'):
			size = os.path.getsize('mcs/server.log') if os.path.isfile('mcs/server.log') else 0
			if size > lastsize:
				f = open('mcs/server.log')
				f.seek(oldsize)
				log = f.read()
				f.close()
				if start_regex.search(log):
					return True
				else:
					f = open('mcs/server.log')
					f.seek(lastsize)
					log = f.read()
					f.close()
					if prepare_regex.search(log):
						i += 2
				lastsize = size
		i -= 1
		sleep(0.5)
	raise NotRunning()


def stop():
	global process
	if not running():
		return False
	cmd('stop')
	for i in xrange(3):
		if not process.poll() == None: return 1
		sleep(1)
	process.terminate()
	for i in xrange(3):
		if not process.poll() == None: return 5
		sleep(1)
	process.kill()
	return 9


def running():
	try:
		if not os.path.isfile('mcs/server.log'):
			return False
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
		return filter (lambda p: p != '', players)
	except AttributeError:
		raise CommunicationError()

def info():
	info = {}
	info['running'] = running()
	if running():
		info['connected_users'] = connected_users()
	return info
