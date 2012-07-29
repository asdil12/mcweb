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

def check_pid(pid):
	""" Check For the existence of a unix pid. """
	try:
		os.kill(pid, 0)
	except OSError:
		return False
	else:
		return True

class Server:
	player_regex = re.compile(r"Connected players: (.*)\n")
	start_regex = re.compile(r"For help, type \"help\" or \"\?\"")
	prepare_regex = re.compile(r"Preparing")
	process = None

	def __init__(self):
		pass

	def __del__(self):
		try:
			self.stop()
		except:
			pass

	def start(self):
		if self.running():
			return False
		print "Starting minecraft server"
		mem = config.get('server_memory')
		cmd = ['java', '-Xms%dM' % mem, '-Xmx%dM' % mem, '-jar', 'minecraft_server.jar', 'nogui']
		Server.process = subprocess.Popen(cmd, cwd='mcs',
			stderr=subprocess.STDOUT,
			stdout=open('/dev/null', 'w'),
			stdin=subprocess.PIPE
		)
		open('mcs/pid.lock', 'w').write(str(int(Server.process.pid)))

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
					if Server.start_regex.search(log):
						return True
					else:
						f = open('mcs/server.log')
						f.seek(lastsize)
						log = f.read()
						f.close()
						if Server.prepare_regex.search(log):
							i += 2
					lastsize = size
			i -= 1
			sleep(0.5)
		raise NotRunning()

	def stop(self):
		if not self.running():
			return False
		print "Stopping minecraft server"
		self.cmd('stop')
		sleep(0.5)
		for i in xrange(6):
			if not self.running():
				return 1
			sleep(0.5)
		Server.process.terminate()
		for i in xrange(6):
			if not self.running():
				return 5
			sleep(0.5)
		Server.process.kill()
		return 9

	def running(self):
		try:
			if not os.path.isfile('mcs/server.log'):
				return False
			if Server.process.poll() == None:
				return True
			else:
				try:
					pid = int(open('mcs/pid.lock').read())
					if check_pid(pid):
						print "got running pid %d" % pid
						return True
				except:
					pass
				return False
		except:
			return False

	def cmd(self, command):
		if self.running():
			Server.process.stdin.write(command+"\n")
			sleep(0.1)
		else:
			raise NotRunning()

	def cmd_out(self, command):
		if self.running():
			oldsize = os.path.getsize('mcs/server.log')
			self.cmd(command)
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

	def connected_users(self):
		#2012-07-25 16:17:05 [INFO] Connected players: user1, test
		mclog = self.cmd_out('list')
		try:
			players = Server.player_regex.search(mclog).group(1)
			players = players.split(', ')
			return filter (lambda p: p != '', players)
		except AttributeError:
			raise CommunicationError()

	def info(self):
		info = {}
		info['running'] = self.running()
		if self.running():
			info['connected_users'] = self.connected_users()
		return info
