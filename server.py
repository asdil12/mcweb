#!/usr/bin/python2

import os
import re
import sys
import subprocess
import config
import zipfile
from time import sleep

from nbt.nbt import NBTFile

# java -Xms1536M -Xmx1536M -jar minecraft_server.jar nogui 
#        ^ min     ^ max  memory in MB
# min: reserved on startup
# max: maximum allocation (realloc on demand)

class NotRunning(Exception):
	pass

class CommunicationError(Exception):
	pass

class NBT_IO_Exception(Exception):
	pass

def _check_pid(pid):
	""" Check For the existence of a unix pid. """
	try:
		os.kill(pid, 0)
	except OSError:
		return False
	else:
		return True

def _tail(f, n=20):
	stdin,stdout = os.popen2("tail -n %d %s" % (n, f))
	stdin.close()
	lines = stdout.readlines(); stdout.close()
	return ''.join(lines)

class Server:
	player_regex = re.compile(r"There are \d+/\d+ players online:\n.*\[INFO\] (.*)\n")
	start_regex = re.compile(r"For help, type \"help\" or \"\?\"")
	prepare_regex = re.compile(r"Preparing")
	version_regex = re.compile("minecraft server version (\d+\.\d+\.\d+)")
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
		print "Starting minecraft server ... ",
		sys.stdout.flush()
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
		i = 30
		while i > 0:
			if os.path.isfile('mcs/server.log'):
				size = os.path.getsize('mcs/server.log') if os.path.isfile('mcs/server.log') else 0
				if size > lastsize:
					f = open('mcs/server.log')
					f.seek(oldsize)
					log = f.read()
					f.close()
					if Server.start_regex.search(log):
						print "\bDONE"
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
		print "Stopping minecraft server ... ",
		sys.stdout.flush()
		self.cmd('stop')
		sleep(0.5)
		for i in xrange(6):
			if not self.running():
				print "\bDONE"
				return 1
			sleep(0.5)
		Server.process.terminate()
		for i in xrange(6):
			if not self.running():
				print "\bDONE"
				return 5
			sleep(0.5)
		Server.process.kill()
		print "\bDONE"
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
					if _check_pid(pid):
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
			for i in xrange(100):
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
		#old:
		#2012-07-25 16:17:05 [INFO] Connected players: user1, test
		#new:
		#2012-08-25 16:51:54 [INFO] There are 2/20 players online:
		#2012-08-25 16:51:54 [INFO] user1, test
		mclog = self.cmd_out('list')
		try:
			players = Server.player_regex.search(mclog).group(1)
			players = players.split(', ')
			return filter (lambda p: p != '', players)
		except AttributeError:
			raise CommunicationError()

	def known_users(self):
		try:
			dirlist = os.listdir('mcs/world/players')
			userlist = [filename.replace('.dat', '') for filename in dirlist]
			return userlist
		except OSError:
			return []

	def get_version(self):
		try:
			z = zipfile.ZipFile('mcs/minecraft_server.jar', 'r')
			ft = z.read('ft.class')
			version = Server.version_regex.search(ft).group(1)
			return version
		except IOError:
			return 'NONE'

	def info(self):
		info = {}
		info['running'] = self.running()
		info['version'] = self.get_version()
		info['known_users'] = self.known_users()
		if self.running():
			info['connected_users'] = self.connected_users()
		return info

	def log(self, window=None):
		try:
			if isinstance(window, int):
				return _tail('mcs/server.log', window)
			else:
				return open('mcs/server.log').read()
		except IOError:
			return ''

	#
	# NBT based methods
	#
	# thanks to https://github.com/pcsforeducation/PyRedstone/blob/master/pyredstone/pyredstone.py

	def prepare_nbt(self):
		try:
			self.cmd('save-all')
			return True
		except NotRunning:
			return False

	def _get_player_nbt(self, player):
		nbt_file = os.path.join('mcs', 'world', 'players', player + '.dat')
		if not os.path.exists(nbt_file):
			raise NBT_IO_Exception
		return NBTFile(nbt_file)

	def get_player_xp(self, player):
		n = self._get_player_nbt(player)
		return n["XpLevel"].value

	def get_player_health(self, player):
		n = self._get_player_nbt(player)
		return n["Health"].value

	def get_player_location(self, player):
		n = self._get_player_nbt(player)
		loc_list = n["Pos"]
		return (loc_list[0].value, loc_list[1].value, loc_list[2].value)

	def get_time(self):
		""" Gets the current in game time. Returns the time as an int between
		0 and 23999, or None if the time cannot be found.
		"""
		n = NBTFile('mcs/world/level.dat')
		if n == None:
			return None
		else:
			return n[0]["Time"].value % 24000

	def get_spawn(self):
		""" Finds the spawn coordinates. Returns a 3tuple of ints in the format
		(X, Y, Z) or None if the coordinates cannot be found.
		"""
		n = NBTFile('mcs/world/level.dat')
		if n == None:
			return None
		else:
			return {'x': n[0]["SpawnX"].value, 'y': n[0]["SpawnY"].value, 'z': n[0]["SpawnZ"].value}
